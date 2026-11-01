# GPU memory math

Quick reference for back-of-envelope VRAM estimates. Not exact, but gets within ~20% which is usually enough to decide if something fits.

## Weights

- params × bytes per param
- fp32 = 4, fp16/bf16 = 2, int8 = 1, int4 = 0.5
- 7B in bf16 → ~14 GB. 13B → ~26 GB. 70B → ~140 GB
- 4-bit quant of 70B → ~35 GB + overhead for scales/zero points, call it 38-40
- Rule of thumb: 1B params ≈ 2 GB at half precision. Easy to remember.

## Training (full finetune, Adam)

Per param, mixed precision:
- weights bf16: 2
- grads bf16: 2
- fp32 master weights: 4
- Adam m + v in fp32: 8
- total ≈ 16 bytes/param, before activations

So 7B full finetune ≈ 112 GB just for states. Won't fit on a single 80 GB card. Need ZeRO/FSDP sharding or go LoRA.

LoRA: base weights frozen (2 bytes/param) + tiny adapter states. 7B LoRA fits in ~16-20 GB with grad checkpointing on.

## Activations

- Scale roughly linearly with batch size × seq len × layers × hidden
- Attention scores scale with seq² unless using flash attention. Always use flash attn, otherwise 8k context gets ugly fast.
- Gradient checkpointing trades ~30% extra compute for big activation savings. Usually worth it.
- If OOM at step 1, halve the micro-batch and bump grad accumulation. Don't touch the effective batch size.

## Inference / KV cache

KV cache per token = 2 × layers × kv_heads × head_dim × bytes

- The 2 is for K and V
- GQA cuts kv_heads a lot, so models with GQA have far smaller caches
- Multiply by seq len × concurrent sequences
- Example: 32 layers, 8 kv heads, 128 head dim, fp16 → 2×32×8×128×2 = 131 KB/token. At 8k ctx that's ~1 GB per sequence. 32 concurrent seqs = 32 GB. This is what actually kills throughput, not the weights.

## Overhead / gotchas

- CUDA context + framework: ~0.5-1 GB gone before anything loads
- Fragmentation can eat 5-10%. Setting expandable segments in the allocator config helps.
- Leave ~10% headroom, never plan to 100%
- `nvidia-smi` shows reserved, not used. Use the framework's own memory stats to see real allocation.
- Peak memory often hits during the optimizer step or at the first backward, not steady state.
