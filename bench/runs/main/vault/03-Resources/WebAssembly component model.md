# WebAssembly component model

Notes to self so I stop re-reading the spec every time.

## What it actually is

- Layer on top of core wasm. Core modules only know i32/i64/f32/f64 + linear memory. Components add typed interfaces so two modules can talk without me hand-rolling pointer/length passing.
- A component = one or more core modules + glue (adapters, canonical ABI) + declared imports/exports.
- Interfaces described in WIT (wasm interface types). Think IDL: records, variants, enums, lists, options, results, resources, flags.
- Worlds = the full set of imports + exports a component expects. Target a world, not just an interface.

## WIT cheat sheet

- `interface` = named bag of types + funcs. `world` = what the component imports/exports.
- `result<T, E>` for errors, not exceptions. Map to the language's native Result where bindings allow.
- `resource` = opaque handle with methods, owned or borrowed. Drop it explicitly or let the binding generator do it. Leaks here show up as handle table growth.
- Strings are UTF-8 in the canonical ABI by default. Watch out if the source language uses UTF-16 internally, copies add up.
- No shared-memory objects across components. Everything crosses by copy (lists, strings) or by handle (resources).

## Workflow that works

1. Write the `.wit` first, even if it's rough.
2. Run binding generator for the guest language, implement the exports.
3. Build to a core module, then wrap it into a component with the componentize/adapt step.
4. Validate and inspect with the tooling's `print` / `wit` extract command. Confirms the world matches what I think I built.
5. Compose components by plugging one's exports into another's imports. Result is a new component.

## Gotchas

- WASI preview 2 is built on this. If a guest needs filesystem/sockets/clocks, it imports WASI interfaces, and the host has to provide them. "Works locally, fails on the runtime" is usually a missing import.
- Old preview 1 modules need an adapter to become components.
- Async story is still unfinished. Don't design APIs assuming streaming or futures are cheap yet; poll-based workarounds are clunky.
- Large payloads: copying across the boundary is the real cost, not the call. Batch calls, pass fewer bigger lists.
- Debugging is rough. Stack traces lose source names unless debug info is kept in the build.
- Version the WIT package names. Breaking a world breaks every consumer silently at link time.

## Open questions

- Best way to test composed components in CI without a full runtime matrix?
- How much overhead do resource handles add in a hot loop? Benchmark before committing.
- Is it worth replacing a plain C-ABI plugin boundary with this for the small stuff?
