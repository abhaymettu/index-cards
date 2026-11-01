# WebAssembly component model

Mental model: core wasm = flat linear memory + ints/floats only. Component model = a layer on top that lets modules talk with rich types (strings, lists, records, variants, resources) without everyone hand-rolling pointer/length ABIs.

## Core pieces

- **Component** = wrapped core module(s) + typed imports/exports. Not the same binary as a plain `.wasm` module, different header/layer.
- **WIT** = the interface definition language. Describes `interface`s (groups of funcs/types) and `world`s (what a component imports + exports). Think IDL / protobuf-ish but for in-process calls.
- **Canonical ABI** = the fixed rules for lowering/lifting high-level types to core wasm values. This is what makes strings cross boundaries safely (copy, not shared pointers).
- **Resources** = opaque handles with ownership, `own<T>` vs `borrow<T>`. Used for things like file handles, streams. Drop = destructor runs.

## Workflow I keep repeating

1. Write the `.wit` first. Resist the urge to start from the code.
2. Generate guest bindings for the language (Rust, JS, Python, Go all have different maturity, Rust is smoothest).
3. Compile to core module, then "componentize" it (adapter step for WASI preview2 imports).
4. Run in a host runtime that supports components. Check the runtime version, support varies a lot.
5. Compose multiple components into one with a link/compose tool if they need to call each other directly.

## Gotchas

- Strings are UTF-8 by default in the canonical ABI, but copies happen on every call. Chatty fine-grained calls are slow, batch things.
- No shared memory between components. That's the point, but it surprises me every time I try to pass a big buffer. Use streams or pass the bytes once.
- Async story is still unsettled / evolving. Don't design around it yet, use polling or stream types where available.
- Error handling: use `result<T, E>` in WIT, not traps. Traps kill the whole instance.
- Worlds matter more than I expected. Wrong world = missing imports at instantiate time with unhelpful errors.
- Debugging: stack traces across component boundaries are poor. Log at the boundary.

## Where it fits

- Plugin systems where I don't trust the plugin (sandbox + typed contract).
- Polyglot libs: one implementation, bindings for many langs.
- Probably overkill for a single-language app that just wants wasm speed. Plain core module is fine there.

## TODO

- Try a toy plugin host with two guest langs against one world.
- Measure per-call overhead for a string-heavy interface vs a batched one.
