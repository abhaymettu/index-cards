# rate limiter designs

Quick reference for the main algorithms + what actually bites in practice.

## fixed window counter
- key = `client:window_start`, INCR + EXPIRE. Dead simple.
- problem: boundary burst. 100/min limit lets through 200 in a couple seconds straddling the minute edge.
- fine for coarse abuse protection, not for protecting a fragile downstream.
- cheap: one key per client per window, one round trip.

## sliding window log
- store timestamp of every request in a sorted set, trim old, count what's left.
- exact, no boundary burst.
- memory is O(requests) per client. Gets ugly at high limits (10k/min x many clients).
- ok for low limits, like login attempts or password resets.

## sliding window counter
- weighted blend of current + previous fixed window: `prev * (1 - elapsed_frac) + curr`.
- approximate but usually within a few % of the real thing. Two keys per client.
- my default pick when I want something better than fixed but don't want the log cost.

## token bucket
- bucket of capacity B, refill at rate R/sec. Request costs 1 token (or N for weighted endpoints).
- allows bursts up to B, then settles to R. Matches how people actually want to think about limits.
- store just `tokens` + `last_refill_ts`. Compute refill lazily on each request, no background timer.
- gotcha: use server time (or Redis `TIME`), not client time, or clock skew gives free tokens.

## leaky bucket
- queue drained at constant rate. Smooths output, good when downstream needs steady load.
- adds latency since requests wait in the queue. Decide up front: drop on full or block?
- as a meter (no queue) it's basically token bucket with different framing.

## distributed notes
- Redis + Lua script for atomic read-modify-write. Without atomicity, two nodes both see "1 token left".
- local in-memory limiter in front of Redis cuts load a lot. Accept some overshoot (N nodes x local slack).
- decide fail-open vs fail-closed when Redis is down. Mine: fail-open for general API, fail-closed for auth endpoints.
- shard keys by client id, watch for hot keys (one noisy client hammering one shard).

## response behavior
- return 429 + `Retry-After`. Add `RateLimit-Remaining` / reset headers so clients can back off sanely.
- add jitter to suggested retry or everyone retries on the same second.
- log rejects with client id + rule name, otherwise tuning limits is guesswork.

## todo
- load test sliding window counter vs token bucket on same traffic replay
- check how limits behave when a client rotates IPs but keeps the same API key
