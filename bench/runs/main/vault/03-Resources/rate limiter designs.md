# rate limiter designs

Quick reference for when I need to pick one. Mostly bites me on the "which one is least surprising for clients" question.

## fixed window

- counter per key per window (e.g. `key:1699000000`), INCR + EXPIRE
- dead simple, one Redis op
- problem: burst at boundary. 100/min limit lets 200 through in ~2s if client times it right
- fine for internal stuff or coarse abuse protection, not for anything billing-related
- gotcha: set EXPIRE only when INCR returns 1, otherwise you keep resetting TTL (did this once, limits never cleared)

## sliding window log

- sorted set of timestamps per key, trim old ones, count what's left
- exact, no boundary burst
- memory is O(requests) per key, hurts at high limits. 10k/min limit = 10k entries per user
- needs a Lua script or MULTI so trim+count+add is atomic

## sliding window counter

- keep current + previous window counts, weight previous by how much of it overlaps
- `est = prev * (1 - elapsed/window) + curr`
- approximate but close enough, O(1) memory
- my default for API limits. error is small unless traffic is very spiky

## token bucket

- store tokens + last refill ts, refill lazily on each request
- allows bursts up to bucket size, then steady rate
- two params to explain to users (rate and burst), which is the annoying part
- good fit when bursty clients are legit (batch uploads, page loads firing many calls)
- do the refill math in Lua so it's atomic, use server time not client time

## leaky bucket

- queue drains at constant rate, overflow gets dropped
- smooths output, good for protecting a downstream that hates spikes
- as a meter it's basically token bucket with different framing; as a queue it adds latency

## practical stuff

- always return `429` plus `Retry-After`. Add `X-RateLimit-Remaining` style headers if clients are third party
- decide fail-open vs fail-closed when Redis is down. I lean fail-open for general APIs, fail-closed for auth/login endpoints
- key choice matters more than algorithm: user id > api key > IP. IP alone punishes shared NATs
- local in-process limiter in front of the distributed one cuts Redis load a lot, accept some looseness
- clock skew between nodes breaks timestamp-based schemes, centralize time in the Redis script
- test with a burst at the window edge, and with concurrent requests on the same key to check atomicity

## todo

- try a cell-based approach (GCRA), supposedly one timestamp per key and handles burst cleanly
- add per-endpoint cost weights instead of flat 1 per request
