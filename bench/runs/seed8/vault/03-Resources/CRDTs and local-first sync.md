# CRDTs and local-first sync

## Core mental model
- CRDT = data type where concurrent edits merge deterministically w/o a central arbiter. Any replica can apply ops in any order and converge.
- Two flavors: state-based (ship whole state, merge = join/lattice) and op-based (ship ops, need causal delivery + idempotence). Delta-state is the practical middle: ship only the diff of state.
- Convergence != intent preserved. Merge is always *a* result, not necessarily the one the user wanted. Design UI around that.

## Picking a type
- Counter: PN-counter, easy. Don't use a plain LWW register for counters, lose increments.
- Single value: LWW register. Fine for settings, bad for anything users type into concurrently.
- Set: OR-set (add wins over concurrent remove). Remove-wins variants exist, pick based on what feels less surprising.
- Map/object: per-key LWW or nested CRDTs. Per-field merge beats whole-object LWW almost always.
- Text/lists: sequence CRDT (RGA / Fugue-style / tree-based). Interleaving of concurrent inserts is the classic gotcha, check how the lib handles it.
- Ordering of items in a list: fractional indexing is cheap, but duplicates can happen with concurrent inserts at same spot. Add a tiebreaker (replica id).

## Practical gotchas
- Tombstones grow forever. Need GC strategy, usually requires knowing all peers have seen the delete. Or periodic snapshot + compaction.
- Metadata overhead can be 10x+ the payload for char-level text. Measure before committing.
- Clocks: use hybrid logical clocks, not wall time. Wall clock skew will silently break LWW.
- Schema migrations are painful. Version the doc format from day one, and keep old clients in mind (they'll write old shapes).
- Deleting + re-creating same id: avoid reusing ids, use fresh uuids.
- Undo/redo needs to be scoped to local user's ops, not global history.

## Sync layer
- Sync is separate from the CRDT. Transport can be websocket, HTTP polling, even files.
- Need: per-peer version vector (or similar) so you only send what's missing.
- Persist locally first (IndexedDB / SQLite), then sync in background. Treat network as optional.
- Auth/permissions are NOT solved by CRDTs. A malicious peer can write garbage that merges fine. Validate server-side or sign ops.
- Server can just be another peer, plus relay and backup. Keep it dumb where possible.

## When not to use
- Strong invariants (unique usernames, inventory, balances). Need a coordinator or reservation scheme.
- Small data, rare conflicts: plain versioned rows + "last write wins + show conflict" is simpler.

## TODO
- Benchmark doc size growth after 100k edits, w/ and w/o compaction.
- Test offline for a few days then reconnect, see merge cost.
