# reading notes on Designing Data-Intensive Applications

Not a cover-to-cover summary. Just the stuff I keep going back to when making design calls at work.

## data models and storage

- Pick the model by access pattern, not hype. Lots of joins / many-to-many → relational. Self-contained documents loaded whole → document store. Heavily connected data → graph.
- LSM trees: fast writes, compaction cost shows up later as read/write amplification. B-trees: predictable reads, in-place updates, WAL needed for crash safety.
- Rule of thumb I wrote on the whiteboard: LSM if write-heavy and can tolerate compaction stalls, B-tree if read latency matters more.
- Column stores for analytics only. Don't try to force OLTP onto them.
- Schema-on-read isn't "no schema", it's the schema living in app code. Still have to deal with migrations, just later.

## replication

- Single-leader is the default unless there's a real reason. Multi-leader and leaderless buy availability and cost conflict handling.
- Async replication means replica lag. Symptoms to watch for: user writes then reads and doesn't see it. Fixes: read-your-writes (route to leader for recently written data), monotonic reads (pin a user to a replica).
- Last-write-wins silently drops data. Only OK when losing writes is fine.
- Quorum (w + r > n) is not a strong guarantee. Sloppy quorums and clock issues break it in edge cases.

## partitioning

- Key-range: good for range scans, risks hot spots (timestamps as key = all writes to one shard).
- Hash: spreads load evenly, kills range queries.
- Secondary indexes: local (scatter/gather reads) vs global (slower, more complex writes). Know which one I'm getting.
- Hot keys still need app-level handling, e.g. salting the key.

## transactions and consistency

- ACID "isolation" varies a lot. Default level on most DBs is weaker than I assume. Check what it actually prevents (write skew, phantoms).
- Write skew is the one that bites: two transactions read the same condition, each writes something different, invariant breaks. Fix with serializable or explicit locking.
- Linearizability is expensive. Ask whether I need it or just causal ordering.
- Distributed transactions (2PC) work but the coordinator is a blocking failure point.

## things to remember in reviews

- Timeouts can't tell slow from dead. Design for that.
- Wall clocks drift. Don't order events with them unless there's a bounded-error source.
- Idempotency keys on anything retried.
- Derived data (caches, search indexes) should be rebuildable from a log of record.
- Ask "what happens on partial failure?" every single time.

## to reread

- Stream processing chapter, esp. exactly-once semantics and where it's really just idempotence.
- Consensus section, I skimmed it.
