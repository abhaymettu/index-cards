# rate limiter designs

Quick ref for the main algos + what actually bites in prod. Not exhaustive.

## token bucket
- bucket cap = burst size, refill rate = sustained rate
- store `tokens` + `last_refill_ts`, compute refill lazily on each request (no timer needed)
- allows bursts up to cap, which is usually what I want for user-facing APIs
- easy to explain to API consumers: "100 req/min, burst 20"
- gotcha: float drift if refilling with fractional tokens, use integer microtokens or just ms math

## fixed window counter
- `INCR key` + `EXPIRE` per window, dead simple
- boundary problem: 2x the limit possible across the edge of two windows (end of window N + start of N+1)
- fine for coarse abuse protection, bad for anything billing-adjacent
- set the expiry atomically with the incr or a crash between them leaves an immortal key

## sliding window log
- sorted set of timestamps per key, trim old, count
- exact, but memory is O(requests), so painful at high limits
- only use for low limits (like login attempts, 5/hr)

## sliding window counter
- weighted blend of current + previous window counts
- `est = prev * (1 - elapsed_frac) + curr`
- approximate but close enough, tiny memory (two ints per key)
- my default when token bucket feels like overkill

## distributed concerns
- do the read-modify-write in a single Lua script on Redis, otherwise races undercount
- local in-memory limiter per node + periodic sync is cheaper but allows overshoot by roughly N nodes x local burst
- clock skew: use the Redis server time (`TIME`) not app node clocks
- hot keys: one abusive client can melt a single shard, consider key hashing with a suffix and summing, or a local pre-filter
- decide fail-open vs fail-closed when the limiter store is down. fail-open for most things, fail-closed for auth endpoints

## response behavior
- return 429 with `Retry-After`, plus `X-RateLimit-Remaining` style headers
- add jitter to suggested retry so clients don't stampede back at the same second
- log rejections with the key and rule name, otherwise debugging "why was I limited" is miserable
- separate limits per endpoint class (read vs write vs expensive), one global number is too blunt

## todo / open q
- check whether cost-weighted tokens (expensive calls consume more) are worth the added complexity
- load test the Lua script under contention before trusting it
