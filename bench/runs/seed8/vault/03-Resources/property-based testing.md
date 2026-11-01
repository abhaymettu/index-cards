# property-based testing

Reminder to self on how I actually use this, not the theory.

## When it's worth it

- Anything with a round trip: serialize/deserialize, encode/decode, parse/print. Cheapest win, nearly always finds something.
- Pure functions with a clear invariant (sorting, dedup, merge, normalize).
- Stateful stuff like caches or queues: model-based testing against a dumb reference impl (plain list/dict).
- Not worth it for glue code, thin CRUD, or anything where the "property" is just restating the implementation.

## Properties I reach for

- **Round trip**: `decode(encode(x)) == x`
- **Idempotence**: `normalize(normalize(x)) == normalize(x)`
- **Invariants preserved**: output length equals input length, output is sorted, no dupes, etc.
- **Oracle**: compare fast version against slow obvious version
- **Commutativity / associativity** where it should hold (merges, set ops). Failing here is usually a real bug.
- **Doesn't crash**: weakest one, but still catches a lot on parsers fed garbage.

## Generators

- Start with built-in strategies, compose up. Don't hand-roll random.
- Constrain at generation time, not with filters. Heavy `assume`/filter use makes the run slow and health checks start complaining.
- Build domain objects from smaller strategies (`builds`/`map`/`flatmap`).
- Bias toward edge cases: empty strings, zero, negative, max int, unicode, NaN for floats. Decide explicitly whether NaN is allowed, otherwise equality props fail in confusing ways.
- Keep sizes small. 100 examples of small inputs beats 10 giant ones for finding minimal repros.

## Debugging failures

- Trust the shrunk example. Copy it into a plain regular test as a regression case before fixing.
- Save the failing seed or use the example database so it replays in CI.
- If shrinking gives something weird, the generator is probably too loose or the code is nondeterministic.
- Flaky property = hidden state (time, global, ordering of dict/set). Fix the code or pin it, don't bump retries.

## CI / practical

- Fewer examples locally for speed, more in a nightly job.
- Set a deadline per example, but loosen it for slow CI boxes so it doesn't flake.
- Log the seed on failure. Always.
- Don't replace example tests. Keep a few readable ones as documentation and let properties cover the weird corners.

## Mistakes I've made

- Writing a property that reimplements the function. Proves nothing.
- Generating inputs that are almost always valid, so the error paths never run.
- Forgetting that float equality needs a tolerance, or `isclose`.
