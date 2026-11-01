# property-based testing

Quick ref for myself. PBT = state an invariant, let the framework generate hundreds of inputs, shrink any failure to a minimal case.

## When it pays off

- Parsers/serializers: `decode(encode(x)) == x` is the easiest win, find it first.
- Anything with a "slow but obviously correct" reference impl. Compare the optimized one against the naive one.
- Idempotence: `normalize(normalize(x)) == normalize(x)`. Catches a surprising number of bugs in cleanup/canonicalization code.
- Sorting, dedup, merging, diffing: output length, ordering, and membership properties.
- State machines / stateful APIs: generate sequences of ops, check model vs real.

Not worth it for: glue code, thin CRUD wrappers, UI layout. Example tests are fine there.

## Properties I keep reaching for

1. Round trip (encode/decode, serialize/parse)
2. Idempotence
3. Invariants preserved (sum unchanged after transfer, set of items unchanged after sort)
4. Oracle / reference comparison
5. "Doesn't crash" for arbitrary input, weak but cheap, good for fuzzing-adjacent stuff
6. Commutativity/associativity where it should hold (merge, union, CRDT-ish logic)

## Generators

- Start with built-in primitives, compose up. Don't hand-roll random.
- Constrain at generation time, not with filters. Heavy `assume`/filter = most cases discarded, slow and weak coverage.
- Bias toward edge values: empty, zero, negative, max int, unicode, very long strings, duplicates.
- Build domain objects with a `builds`/map style combinator so shrinking still works through it.
- Keep a shared generators module so tests don't each reinvent the same user/order/etc.

## Shrinking and reproducing

- Always log/keep the seed on failure. CI failures that can't be replayed are useless.
- When a failure is found, copy the shrunk case into a plain example-based regression test. Don't rely on random to re-find it.
- Many frameworks have a failure database; commit it or at least cache it in CI.
- If shrinking gives a weird huge case, the generator is probably not composed in a shrink-friendly way.

## Practical settings

- Local: default ~100 examples, fast feedback.
- CI nightly: crank to thousands.
- Set a deadline per example; flaky timing failures are usually a real perf bug or a slow generator.
- Keep properties pure and deterministic. Hidden time/randomness/network breaks shrinking.

## Gotchas

- Property that restates the implementation proves nothing. Test a *different* angle.
- Floats: NaN and inf will wreck equality checks. Decide up front whether to exclude them.
- Passing 100 runs isn't proof. Treat as a bug-finder, not a verifier.
- Writing the property is the hard part, and that's the value: it forces me to spell out the spec.
