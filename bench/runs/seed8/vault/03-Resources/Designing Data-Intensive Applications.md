# reading notes on Designing Data-Intensive Applications

Reference for myself. Not a summary, just the stuff I keep coming back to at work.

## storage and indexing

- LSM trees: fast writes (append to memtable, flush to sorted files), reads pay for checking multiple levels. Bloom filters cut the cost of misses. Compaction is where the pain lives: write amplification, latency spikes when it falls behind.
- B-trees: in-place updates, predictable reads, WAL needed for crash safety. Page splits are the thing to remember.
- Rule of thumb I use: write-heavy and append-ish -> LSM. Read-heavy with range scans and strong transactional needs -> B-tree.
- Column stores for analytics. Compression + vectorized scans is why they're so much faster for aggregates. Don't use them for point lookups on single rows.

## replication

- Single leader is the default answer. Async replication means a failover can lose acked writes. Know which one you have.
- Read-your-writes problem: user writes, reads from a lagging follower, sees old data. Fixes: read from leader for recent writes, or track a timestamp/LSN per session.
- Multi-leader only if I really need multi-region writes. Conflict resolution is the cost. LWW silently drops data, so avoid unless loss is fine.
- Quorum (w + r > n) is not a guarantee of linearizability. Sloppy quorums and clock skew break the intuition.

## partitioning

- Key range: good for scans, hot spots on monotonic keys (timestamps). Hash: even spread, kills range queries.
- Secondary indexes: local (scatter/gather reads) vs global (slower, more complex writes). Pick based on which side hurts more.
- Rebalancing: fixed number of partitions up front is the least painful. Avoid hash mod N.

## transactions and consistency

- Isolation levels are muddier than the names suggest. Read committed lets through read skew. Snapshot isolation lets through write skew (the on-call doctors example).
- Serializable options: actual serial execution, 2PL, SSI. Most systems I touch default to something weaker, so check the docs.
- Distributed transactions (2PC) are a blocking mess if the coordinator dies. Prefer idempotent operations + retries where possible.
- Linearizability costs latency and availability. Only pay for it for things like uniqueness constraints and leader election.

## streams and derived data

- Log-based messaging gives ordering per partition and replay. Consumer offsets are the state to monitor.
- Change data capture beats dual writes. Dual writes will diverge eventually.
- Idempotency keys everywhere, since exactly-once is really at-least-once plus dedup.
- Treat caches, search indexes, and views as derived data that can be rebuilt from the log.

## to revisit

- Chapter on clocks and unreliable networks, especially fencing tokens.
- Write down how our current setup maps to these tradeoffs.
