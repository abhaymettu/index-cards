# interview prep for systems design

## the frame i keep using

45 min goes fast. rough split so i don't ramble:
- 5 min: requirements + scope (functional, then non-functional)
- 5 min: back-of-envelope numbers
- 10 min: high-level boxes and arrows
- 15 min: deep dive on 1-2 parts the interviewer cares about
- 10 min: bottlenecks, failure modes, wrap

always ask "what's the read/write ratio" and "how stale can data be" early. those two questions steer like half the design.

## numbers worth memorizing

- 1 day ≈ 86k sec, so ~100k for easy math
- 1M req/day ≈ 12 req/sec
- 100M DAU * 10 actions = 1B/day ≈ 12k QPS avg, peak 2-3x
- single Postgres box: few thousand writes/sec fine, ~10k+ simple reads
- redis: ~100k ops/sec per node
- SSD read ~100us, network round trip in-DC ~0.5ms, cross-region ~100ms+
- 1 char = 1 byte, a tweet-ish record ~1KB with metadata, image ~200KB-2MB

round aggressively. nobody cares about 11.57 vs 12.

## building blocks checklist

- load balancer (L4 vs L7, why)
- cache: where (client, CDN, app, DB), eviction, invalidation strategy
- queue/stream for async work, decouples spikes
- sharding key choice, hot key problem
- replication: leader/follower, what happens on failover
- blob storage + CDN for media
- rate limiting, idempotency keys on writes
- search index as a separate system, not the primary DB

## deep dive habits

- pick the part with the real tradeoff, don't spread thin
- say the tradeoff out loud: "fan-out on write is fast to read but celebrity accounts blow it up"
- name the failure mode before they ask. what if the cache dies, what if the queue backs up
- consistency: say which parts need strong, which can be eventual, and why

## mistakes i've made in mocks

- jumped to microservices before understanding the problem
- forgot to state assumptions, then got confused by my own numbers
- spent 20 min on the schema and never reached scaling
- said "just use Kafka" without saying what it buys me
- didn't talk about monitoring/alerting at all

## practice list

- URL shortener (warm up)
- news feed
- chat / messaging
- rate limiter
- notification system
- distributed file storage
- ride matching / geo lookup

do one out loud, timed, every other day. record it and listen back, painful but works.
