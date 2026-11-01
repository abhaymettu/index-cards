# GPU memory math

Quick back-of-envelope rules so I stop opening a calculator every time.

## Weights

- params × bytes/param. fp32 = 4, fp16/bf16 = 2, int8 = 1, int4 = 0.5
- 7B in bf16 ≈ 14 GB. 13B ≈ 26 GB. 70B ≈ 140 GB (so multi-GPU or quantized)
- 1B params ≈ 2 GB in bf16, easy to remember
- quantized weights also carry scales/zero-points, add ~5-10% on top of the naive number

## Training (full finetune, Adam)

Per param, mixed precision:
- bf16 weights: 2
- bf16 grads: 2
- fp32 master weights: 4
- Adam m + v in fp32: 8
- total ≈ 16 bytes/param, **before activations**

So 7B full finetune ≈ 112 GB just for state. Doesn't fit on one 80 GB card. Options: ZeRO/FSDP sharding, 8-bit optimizer, or LoRA.

LoRA: frozen base in bf16 (2 B/param) + tiny trainable adapters. 7B LoRA fits in ~16-20 GB with small batch + grad checkpointing.

## Activations

- scale linearly with batch size and (roughly) sequence length; attention scores scale with seq² unless using flash attention
- grad checkpointing trades ~30% extra compute for a big cut in activation memory, usually worth it
- if OOM only happens at larger batch, it's activations, not weights. Halve the batch first, then use grad accumulation

## Inference / KV cache

KV cache per token = 2 × layers × kv_heads × head_dim × bytes

- the 2 is K and V
- GQA/MQA shrinks kv_heads a lot, check the config before estimating
- total = per-token × seq_len × batch
- long context + big batch can make the KV cache bigger than the weights. Always compute it separately.

## Overheads / gotchas

- CUDA context + framework: ~0.5-1 GB gone before anything loads
- allocator fragmentation: budget 10-20% headroom
- `nvidia-smi` shows reserved, not used. Use `torch.cuda.memory_summary()` or `max_memory_allocated()` for the real peak
- peak usually happens in the first backward pass or at optimizer step, not forward
- empty_cache() doesn't fix real OOMs, only frees cached blocks for other processes

## Sanity formula

needed ≈ (weights + grads + optimizer state) + activations + KV cache + ~15% slack

If it's within 10% of card capacity, assume it won't fit.
