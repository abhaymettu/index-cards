# SQLite in production

## Pragmas I always set
Per connection, on open. Forgetting these is the #1 source of weirdness.

- `journal_mode=WAL` — readers don't block the writer. Persistent on the db file, but set it anyway.
- `synchronous=NORMAL` — safe with WAL, much faster than FULL. Can lose last txn on power loss, not corrupt.
- `busy_timeout=5000` — otherwise you get `SQLITE_BUSY` instantly under contention.
- `foreign_keys=ON` — off by default, per connection. Easy to forget with pools.
- `temp_store=MEMORY`, `cache_size=-64000` (negative = KiB, so ~64MB).

## Concurrency
- One writer at a time, period. Many readers fine in WAL.
- Keep write txns short. No network calls or slow work inside a txn.
- Use `BEGIN IMMEDIATE` for any txn that will write. Plain `BEGIN` then upgrading to a write lock can fail with BUSY immediately and busy_timeout doesn't help in that case.
- Separate pools: one write connection (max 1), N read connections. Cuts lock errors a lot.
- Long-running read txns block WAL checkpointing, so the `-wal` file grows. Watch for it.

## Backups
- Never `cp` the db file while it's live. With WAL you'd miss the `-wal` contents.
- Use `.backup` in the CLI or `VACUUM INTO 'file.db'`. Both give a consistent snapshot.
- Streaming replication to object storage is worth it if the data matters. Test the restore, not just the backup.
- Run `PRAGMA integrity_check` on a restored copy occasionally.

## Gotchas
- Types are loose. Use `STRICT` tables to get real type enforcement.
- `ALTER TABLE` is limited. Dropping or changing columns often means the create-new, copy, drop, rename dance inside a txn.
- Don't put the db on NFS or other network filesystems. Locking is unreliable and it will bite eventually.
- In containers, mount a real volume. Keep the db, `-wal`, and `-shm` on the same filesystem.
- Run `PRAGMA optimize` before closing connections, or periodically on long-lived ones.
- `VACUUM` needs roughly 2x free disk and takes a write lock. Schedule it.

## When to leave
- Need multiple app servers writing to the same data.
- Write throughput is consistently pegged on the single writer.
- Need fine-grained access control or online schema changes on big tables.

Otherwise it's fine. A single box with SQLite goes a lot further than people assume.
