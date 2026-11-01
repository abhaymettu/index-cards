# vector index tradeoffs

Quick ref for picking an ANN index. Not exhaustive, just what I keep forgetting.

## flat (brute force)
- exact results, no build step, no tuning
- fine up to ~100k vectors, maybe 1M if latency budget is loose and SIMD is on
- always use it as the ground truth when measuring recall of anything else
- cost scales linearly with corpus size, so it falls over fast

## HNSW
- best default for most things under ~50M vectors
- recall/latency is great, queries are fast even at high recall
- memory hungry: graph links + full vectors in RAM. rough rule: vectors * (dim*4 bytes) + ~M*2*4 bytes per node for links
- knobs: `M` (connectivity, 16 is sane), `efConstruction` (build quality, 200ish), `efSearch` (query-time recall vs speed)
- raise efSearch before touching anything else when recall is low
- deletes are ugly. tombstones pile up, need periodic rebuild
- inserts are online-friendly, which is the big win over IVF

## IVF (+ PQ)
- cluster into `nlist` cells, probe `nprobe` at query time
- nlist ~ sqrt(N) as a starting point
- needs a training pass, and if the data distribution drifts the clusters go stale
- IVF-PQ compresses hard (8–32x), so it's the option when RAM is the constraint
- PQ costs recall. rerank top-k with full vectors to claw it back
- nprobe is the main recall dial, linear-ish latency hit

## disk-based graph indexes
- for when it won't fit in RAM even compressed
- keep compressed vectors in memory, full vectors + graph on SSD
- latency is dominated by random reads, so NVMe is not optional
- slower to build, painful to update

## things that bit me
- recall numbers meaningless without a fixed query set and ground truth. save one
- normalize vectors if using cosine, then inner product is the same and faster
- filtered search (metadata predicates) tanks recall on graph indexes when the filter is very selective. pre-filter vs post-filter matters a lot
- benchmark at p95/p99, not mean
- quantizing to int8 or binary is often a cheap win before reaching for fancier indexes

## rough decision
- <1M: flat or HNSW, don't overthink
- 1M–50M, RAM ok: HNSW
- RAM tight: IVF-PQ with rerank
- huge + SSD: disk graph
- heavy filtering: test it explicitly, don't assume
