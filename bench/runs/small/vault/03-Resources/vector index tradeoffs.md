# vector index tradeoffs

Quick reference for picking an ANN index. Not exhaustive, just what I keep re-deriving.

## flat (brute force)

- exact results, zero build time, no tuning
- fine up to ~100k vectors, maybe 1M if latency budget is loose and I have SIMD/GPU
- always use it as the ground truth when measuring recall of anything else
- cost scales linearly with corpus, so p99 gets ugly fast

## HNSW

- best default for recall vs latency when everything fits in RAM
- memory heavy: raw vectors + graph links (roughly M * 2 * 4 bytes per node on top)
- knobs: `M` (graph degree, 16 is a sane start), `efConstruction` (build quality, 100-200), `efSearch` (query-time recall/latency dial)
- raising efSearch is the cheapest fix for bad recall, try that before rebuilding
- deletes are awkward. Usually tombstones, and the graph degrades until a rebuild
- build is slow and mostly single-threaded-ish, so budget for it on big loads
- filtered search hurts: heavy metadata filters can disconnect the traversal and recall drops off a cliff

## IVF (flat / PQ)

- cluster into `nlist` cells, search `nprobe` of them
- nlist rule of thumb: ~sqrt(N) to 4*sqrt(N)
- needs a training step, and stale centroids hurt if the data distribution drifts
- much cheaper memory than HNSW, especially IVF-PQ
- recall is capped by nprobe, so latency climbs as I push it
- good fit when data is mostly static and rebuilds are cheap

## quantization

- PQ: 8-32x smaller, recall loss is real, rerank top-k with full vectors to recover most of it
- scalar (int8): ~4x smaller, usually barely noticeable loss, easy win
- binary: huge savings, only worth it for high-dim embeddings with a rerank stage
- always measure recall on my own queries, not a public benchmark

## disk-based graphs

- when the corpus doesn't fit in RAM but SSD is fast
- keeps compressed vectors in memory, full ones on disk
- latency is dominated by IO, so check IOPS before committing

## checklist before deciding

1. corpus size now vs in 12 months
2. update/delete rate
3. filter usage (hybrid queries change the answer)
4. recall target and p99 budget
5. RAM budget per node

If unsure: HNSW + int8 quantization + rerank. Revisit when memory becomes the problem.
