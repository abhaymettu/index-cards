# WebAssembly component model

## What it actually is
- Layer on top of core wasm. Core modules only know i32/i64/f32/f64 + linear memory. Components add typed interfaces so two modules can talk w/o sharing memory
- A component = wrapped core module(s) + canonical ABI glue + declared imports/exports
- Goal: language-agnostic composition. Rust component calls a Python or JS one via typed function calls, no hand-rolled FFI

## WIT (interface definition)
- `.wit` files describe types and functions. Worlds = what a component imports and exports
- Types: string, list<T>, option<T>, result<T,E>, record, variant, enum, flags, resource
- `resource` = handle w/ methods, owned vs borrowed. Handles are just ints under the hood, host tracks lifetime
- Keep interfaces small. Big worlds make bindings gen slow and ugly
- Versioning goes in the package name (`pkg:name@1.2.0`), bump on breaking changes

## Canonical ABI
- Strings/lists get copied across the boundary (lift/lower). Cost shows up with big payloads
- Strings are UTF-8 by default but can be configured, mismatch = silent perf hit from transcoding
- For hot paths, pass fewer bigger calls instead of many tiny ones
- Don't pass giant buffers repeatedly. Use a resource or stream if available

## Tooling notes
- `wasm-tools component new` turns a core module into a component. Needs an adapter if the module uses WASI preview1
- `wasm-tools component wit` to dump the interface of a built component, good for sanity checks
- Binding generators exist per language. Regenerate on every WIT change, don't hand edit the output
- Composition: link one component's exports to another's imports with a compose step, result is a single component

## WASI tie-in
- WASI preview2 is defined as WIT worlds (filesystem, sockets, clocks, cli, http)
- Component targets a world, host must supply those imports or it fails to instantiate
- Capabilities model: nothing available unless granted. Good for sandboxing plugins

## Gotchas
- Async story still rough, lots of polling/pollable workarounds. Check what the runtime actually supports before designing around it
- Debugging across component boundaries is painful, stack traces stop at the edge
- Runtime support is uneven, test on the exact host I'll deploy to
- Binary size grows w/ bundled stdlib per component, strip and opt (`wasm-opt -Oz`)

## TODO
- Try a plugin system where host loads user components against one narrow world
- Benchmark list<u8> copy overhead vs a resource handle approach
