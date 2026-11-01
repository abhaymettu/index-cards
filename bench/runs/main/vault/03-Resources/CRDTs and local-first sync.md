# CRDTs and local-first sync

## Mental model
- CRDT = data type where concurrent edits merge deterministically w/o a central arbiter. Any order of delivery, same end state.
- Two flavors: state-based (ship whole state, merge = join) and op-based (ship ops, need causal delivery + dedupe). Most libs are a hybrid, ship deltas.
- Merge must be commutative, associative, idempotent. If I can't argue all three, it's not a CRDT, it's a bug.
- Not magic: converges, but doesn't guarantee the result *makes sense* to a user. Intent preservation is the hard part.

## Types I actually reach for
- LWW register: simplest, loses concurrent writes silently. Fine for settings, bad for anything the user cares about.
- OR-set (add-wins): remove only kills the adds it saw. Good default for tags/membership.
- Counter (PN): per-replica increments, sum on read.
- Map of registers: most app state ends up here. Nested maps get messy when one side deletes a parent and the other edits a child.
- Sequence/text: RGA or tree-based. Heavy metadata, interleaving anomalies on concurrent inserts at the same spot.

## Practical gotchas
- Tombstones grow forever unless I do GC, and GC needs knowledge of what all peers have seen. Plan for snapshot + compaction early.
- Clocks: don't trust wall time for LWW. Use hybrid logical clocks or Lamport + replica id as tiebreak.
- Replica IDs: never reuse after restoring from backup/cloned disk, or two devices emit the same op IDs. Generate fresh on first launch, and on restore.
- Schema migrations are painful, old ops replay against new code. Version the ops, not just the snapshot.
- Undo/redo is per-user-intent, not a global log rewind. Needs its own design.
- Permissions/validation: a CRDT will happily merge a malicious op. Validate at the edges, sign ops if peers aren't trusted.

## Sync layer notes
- Transport is the boring part: dumb server that stores and relays opaque blobs is enough. Server can be E2E-encrypted-ignorant.
- Sync by version vector / "give me everything after X". Cheap to compute diffs this way.
- Persist locally first (SQLite or IndexedDB), UI reads from local, network is background.
- Batch and debounce ops, per-keystroke ops will wreck storage.
- Offline for days is the real test case, test with long-diverged replicas, not just two tabs.

## When NOT to use
- Strong invariants (unique usernames, balances, inventory). Needs coordination or a server-side check.
- Small data, one writer at a time: plain last-write-wins plus a version number is enough.

## TODO
- Try snapshot + delta compaction on a toy doc and measure size growth after 100k ops.
- Write a fuzz test: random op order across 3 replicas, assert same final state.
