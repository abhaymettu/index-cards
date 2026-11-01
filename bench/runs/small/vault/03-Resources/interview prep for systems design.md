# interview prep for systems design

## framework i keep coming back to

1. clarify requirements first. functional vs non-functional. ask about scale (DAU, read/write ratio, data size, latency target). don't skip, even if nervous
2. back-of-envelope numbers. QPS, storage per year, bandwidth. round aggressively, 86400 s/day ≈ 10^5
3. API sketch. 3-5 endpoints max, write the shapes out
4. data model + storage choice, justify it
5. high-level diagram, then pick ONE or two areas to go deep
6. bottlenecks, failure modes, tradeoffs at the end

time split for 45 min: ~5 reqs, ~5 estimates, ~10 hld, ~20 deep dive, ~5 wrap

## numbers to have memorized

- single Postgres box: ~5-10k simple QPS before it hurts
- redis: 100k+ ops/s per node
- SSD random read ~100 µs, network round trip in-DC ~0.5 ms, cross-region ~50-150 ms
- 1M req/day ≈ 12 QPS avg, peak maybe 3-5x
- 1 KB * 1M rows = 1 GB. easy to scale up from there
- kafka partition handles roughly 10 MB/s, plan partitions by throughput and consumer parallelism

## building blocks checklist

- load balancer (L4 vs L7)
- cache: write-through vs cache-aside, eviction, stampede protection
- queue/stream for async work, idempotent consumers
- sharding: pick key carefully, watch hot keys, consistent hashing
- replication: leader/follower, lag, read-your-writes problem
- CDN for static/media
- rate limiting (token bucket is the default answer)
- search index separate from primary store

## things that trip me up

- jumping to microservices too early. start with a boring monolith + DB and split only when numbers justify
- forgetting to say WHY a choice. "I'd use Cassandra" means nothing without the access pattern
- ignoring consistency. say out loud where eventual is fine and where it isn't (payments, inventory)
- not talking while thinking. narrate
- over-drawing. a messy diagram with clear labels beats a pretty one

## practice plan

- one design per day, 30 min timed, then compare to a reference and note gaps
- rotation: URL shortener, feed, chat, rate limiter, notification system, file storage, ride matching, metrics pipeline
- redo the ones where my deep dive was weak after a week
- do at least two mock sessions out loud with someone before the real thing

## todo

- [ ] write one-page cheat sheet of numbers above
- [ ] re-read notes on consistency models (quorum, CRDT basics)
- [ ] practice explaining sharding tradeoffs in under 2 minutes
