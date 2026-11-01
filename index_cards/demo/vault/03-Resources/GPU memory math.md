# GPU memory math

Quick back-of-envelope for "will this fit" before I waste an hour on OOMs.

## Weights

- bytes = params × bytes per param
- fp32 = 4, fp16/bf16 = 2, int8 = 1, int4 = 0.5
- 7B in bf16 → ~14 GB. 13B → ~26 GB. 70B → ~140 GB
- quantized int4 70B → ~35 GB + overhead, so realistically 40ish
- rule of thumb: GB ≈ params (in B) × 2 for bf16. Easy to do in head

## Training (full finetune, Adam)

Per param, mixed precision:
- weights bf16: 2
- grads bf16: 2
- fp32 master copy: 4
- Adam m + v in fp32: 8
- total ≈ 16 bytes/param, before activations

So 7B full finetune ≈ 112 GB just for states. Doesn't fit on one 80 GB card. Need sharding (ZeRO/FSDP) or go LoRA.

LoRA / QLoRA: base frozen so no grads/optimizer for it. Only adapter states are tiny. QLoRA 7B ≈ 4-5 GB base + activations, fits on a 12-16 GB card if seq len is sane.

## Activations

- scale with batch × seq len × hidden × layers
- gradient checkpointing trades ~30% extra compute for big memory savings. Almost always worth it when tight
- halving batch size is the fastest knob, then use grad accumulation to keep effective batch
- attention without flash kernels is O(seq²), long context blows up fast

## Inference / KV cache

KV cache per token = 2 × layers × kv_heads × head_dim × bytes

- grows linearly with seq len AND batch size
- GQA/MQA shrinks it a lot (fewer kv_heads), check the config not just the param count
- example: 32 layers, 8 kv heads, 128 head dim, bf16 → 2×32×8×128×2 = 131 KB/token. 8k ctx ≈ 1 GB per sequence
- batch of 32 at 8k ≈ 32 GB of cache alone. This is what kills serving, not weights

## Overhead / gotchas

- reserve 10-20% for CUDA context, allocator fragmentation, workspace buffers
- `nvidia-smi` shows reserved, not used. Use `torch.cuda.memory_summary()` or `max_memory_allocated()` for the real peak
- peak often happens at the first backward pass or during optimizer step, not forward
- OOM only after N steps → usually a long-seq batch or a leak holding tensors (logging losses without `.item()`)
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` helps with fragmentation

## Checklist when OOM

1. drop batch size
2. enable grad checkpointing
3. lower precision / quantize
4. shorter seq len
5. shard or offload
6. only then buy more GPU
