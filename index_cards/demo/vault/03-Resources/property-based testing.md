# property-based testing

Reference for myself. Idea: instead of hand-picking inputs, state an invariant and let the framework generate hundreds of inputs trying to break it. When it fails it shrinks to a minimal counterexample.

## When it's worth it

- Parsers / serializers: `decode(encode(x)) == x` (roundtrip). Best ROI by far.
- Anything with an inverse (compress/decompress, encrypt/decrypt, to_json/from_json).
- Idempotent ops: `normalize(normalize(x)) == normalize(x)`. Good for dedupe, sorting, path cleanup, formatting.
- Comparing a fast impl against a slow obvious one (oracle testing). Great for refactors/optimizations.
- Invariants on data structures: size never negative, tree stays balanced, no duplicate keys after merge.
- Not great for: UI glue, thin wrappers over IO, stuff where the "property" is just re-implementing the function.

## Writing properties

- Hard part is thinking of the property, not the tooling. Checklist I keep coming back to:
  - roundtrip
  - idempotence
  - commutativity / associativity (merge, union, money math)
  - "output is subset of input" / length preserved
  - monotonicity (more input => not less output)
  - no crash on any input (weakest but still catches stuff)
- Don't copy the implementation into the assertion. If the test mirrors the code it proves nothing.
- Start with the "doesn't throw" property, then tighten.

## Generators

- Build small strategies and compose them. Custom generators for domain objects are where the real value lives.
- Constrain at generation time rather than filtering. Heavy `assume`/filter = most cases discarded, test slow and flaky health checks.
- Bias toward edge cases: empty, one element, duplicates, unicode, huge ints, negative zero, NaN for floats.
- Dates and timezones: generate them deliberately, they find bugs every time.

## Shrinking and reproducing

- Always save the failing seed / example. Pin it as a normal regression test once fixed.
- Shrinking is only as good as the generator; if built via flat-map chains it shrinks badly. Prefer simple composition.
- Keep a failure database enabled in local runs, disable or fix the seed in CI if flakiness bothers people.

## Practical settings

- Local: ~100 examples default is fine. Nightly/CI-extended: crank to thousands.
- Set a deadline so slow cases surface as failures, not hangs.
- Keep each property fast (ms). If setup is heavy, build it once outside the test.
- Mix with example-based tests; examples document intent, properties hunt for surprises.

## Todo

- Add roundtrip property for the config loader.
- Try stateful testing (model-based) on the cache layer.
