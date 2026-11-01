# interview prep for systems design

## the 45 min skeleton
- 5 min: clarify reqs. functional first, then non-functional (latency, availability, consistency, scale)
- 5 min: back-of-envelope. QPS, storage/yr, read:write ratio, peak vs avg (peak ~2-3x)
- 10 min: high-level boxes. client → LB → stateless app → cache → DB, plus queue if async
- 15 min: deep dive on 1-2 hot spots. let interviewer steer
- 5 min: failure modes, bottlenecks, what I'd monitor
- don't spend 20 min on schema. I always do this.

## numbers worth memorizing
- 1 day ≈ 86k sec, so 1M req/day ≈ 12 QPS
- 1M users x 1KB = 1GB. scale from there
- memory read ~100ns, SSD ~100µs, same-DC network RTT ~0.5ms, cross-region ~100ms+
- single Postgres box handles several thousand simple QPS fine. don't shard by reflex
- Redis ~100k ops/sec per node, rough

## building blocks checklist
- **cache**: aside vs write-through vs write-back. say what happens on invalidation, stampede (locking, jittered TTL)
- **queue**: decouples spikes, need idempotent consumers, DLQ, ordering only per partition
- **sharding**: pick key by access pattern, watch hot keys, resharding pain → consistent hashing
- **replication**: leader/follower, replica lag breaks read-your-writes. mention sticky reads or read from leader after write
- **CDN** for static + cacheable API responses
- **rate limiting**: token bucket, per-user + per-IP, where it lives (gateway vs service)

## tradeoffs to state out loud
- CAP is only interesting during partitions. otherwise it's latency vs consistency
- SQL vs NoSQL: justify with access patterns, not hype
- push vs pull (fan-out on write vs read) — classic feed question, hybrid for high-follower accounts
- sync vs async: what can the user not wait on?

## practice list
- URL shortener (warm-up, ID generation, redirects)
- news feed
- chat / presence
- rate limiter
- notification service
- distributed job scheduler
- file sync / blob storage
- typeahead search

## habits to fix
- narrate reasoning, silence reads as stuck
- write numbers on the board, not just say them
- ask "is it ok if I go deeper on X?" instead of guessing
- end with what I'd do with another month
- mock out loud at least 2x a week, timed
