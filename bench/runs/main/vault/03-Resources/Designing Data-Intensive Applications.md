# reading notes on Designing Data-Intensive Applications

Re-reading parts of this for work, not cover to cover. Keeping what I actually use when reviewing designs.

## replication

- single-leader is the default unless there's a real reason. Easiest to reason about, failover is still the painful part
- async replication = replicas lag. Read-your-writes breaks first. Fix: route a user's reads to leader for a short window after they write, or track last-write timestamp/position
- monotonic reads: pin a user to one replica (hash user id) so they don't see time go backwards
- multi-leader only makes sense for multi-datacenter or offline clients. Conflict resolution is where it hurts. LWW silently drops writes, don't use it for anything that matters
- quorum: w + r > n gives overlap but not real linearizability. Sloppy quorums and clock skew break the guarantees people assume

## partitioning

- key-range = good range scans, hot spots on sequential keys (timestamps). Hash = even spread, range queries gone
- compound key trick: hash first part, sort on the rest. Good fit for "all events for user X in order"
- secondary indexes: local (scatter/gather on reads) vs global (writes touch multiple partitions). Pick based on read/write ratio
- celebrity/hot key problem: hashing doesn't save you. Need app-level splitting (append random suffix to key, merge on read)
- rebalancing: fixed number of partitions >> nodes is simpler than dynamic. Don't do hash mod N

## transactions

- "serializable" and "snapshot isolation" are not the same. Snapshot isolation still allows write skew (the on-call doctor example)
- write skew checklist: read something, decide, write something *else* based on it. If yes, need explicit locking (`SELECT ... FOR UPDATE`) or real serializable
- check what the DB calls "repeatable read," it varies by vendor
- 2PC works but the coordinator is a single point of failure. In-doubt transactions hold locks until resolved

## streams and logs

- log-based broker for ordering within a partition, consumers track offsets, replay is cheap
- CDC beats dual writes. Dual writes will diverge eventually, no matter how careful
- make consumers idempotent. Exactly-once is really at-least-once + dedupe
- event sourcing is neat but schema evolution of old events is a real cost

## things to remember in reviews

- ask "what happens when this node is slow, not dead?" Slow is worse than dead
- ask what the consistency expectation is *in words* before picking a tech
- timeouts are a guess, and clocks lie. Don't use wall-clock time for ordering
- derived data (caches, search indexes) should be rebuildable from the source of truth
