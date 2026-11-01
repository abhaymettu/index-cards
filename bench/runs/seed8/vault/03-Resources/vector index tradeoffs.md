# vector index tradeoffs

Quick reference for picking an ANN index. Not exhaustive, just what I keep having to re-derive.

## flat (brute force)

- exact results, no build step, no tuning
- fine up to ~100k vectors, maybe 1M if latency budget is loose and SIMD is on
- always use it as the ground truth when measuring recall of anything else
- cost scales linearly with corpus, so it stops being fun fast

## HNSW

- best default for recall/latency when everything fits in RAM
- memory is the catch: raw vectors + graph links. roughly 1.3–2x the vector data depending on M
- knobs: `M` (connectivity), `efConstruction` (build quality), `efSearch` (query-time recall vs speed)
- raising efSearch is the cheap fix for low recall, try that before rebuilding
- inserts are fine, deletes are ugly (tombstones, graph degrades). periodic rebuild if churn is high
- build time is slow on big corpora, parallelism helps but not linearly

## IVF (+ PQ)

- cluster into `nlist` cells, probe `nprobe` of them at query time
- much smaller memory than HNSW, especially with PQ compression
- recall drops noticeably with PQ, rerank top-k with full vectors to recover most of it
- needs a training step on representative data. bad training sample = bad clusters
- rule of thumb: nlist ~ sqrt(N) to 4*sqrt(N)
- data drift hurts, retrain if distribution shifts a lot

## disk-based graph indexes

- for corpora that don't fit in RAM, keep compressed vectors in memory and full ones on SSD
- latency is dominated by random reads, so NVMe matters a lot
- more operational complexity, only worth it past a few hundred million vectors or when RAM cost is the blocker

## things to check before choosing

- how much recall is actually needed? 0.95 vs 0.99 changes the cost a lot
- filter-heavy queries? post-filtering kills recall, pre-filtering can be slow. test with real filter selectivity
- write rate and delete rate, not just corpus size
- p99 latency, not just average
- embedding dimension: higher dim means more memory and slower distance calcs, consider truncating or quantizing

## gotchas

- benchmark on your own data, public datasets lie about your distribution
- normalize vectors if using cosine via inner product, easy to forget
- index params that look great at 1M can fall apart at 50M
- always log recall against a flat sample in prod, otherwise regressions go unnoticed
