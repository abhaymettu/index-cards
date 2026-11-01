# SQLite in production

Mostly notes to self so I stop re-googling the same pragmas.

## Setup I always apply

- `PRAGMA journal_mode=WAL;` first thing. Persists in the db file, so only needs setting once, but harmless to repeat.
- `PRAGMA synchronous=NORMAL;` with WAL. Safe against app crash, tiny risk of losing last txn on power loss. Fine for most stuff.
- `PRAGMA foreign_keys=ON;` is per-connection. Easy to forget, set it in the connection init hook.
- `PRAGMA busy_timeout=5000;` otherwise you get SQLITE_BUSY instantly under contention.
- `PRAGMA cache_size=-64000;` (negative = KiB, so ~64MB).
- `PRAGMA temp_store=MEMORY;` helps with big sorts.

## Concurrency

- WAL = many readers, one writer. Readers don't block the writer and vice versa.
- Keep write txns short. Never hold one open across a network call.
- Use `BEGIN IMMEDIATE` for write txns. Plain `BEGIN` then upgrading to write can fail with BUSY and busy_timeout doesn't help in that case.
- Separate connection pools: small number of readers, exactly one writer connection (or a mutex around writes). Way fewer lock errors than a single shared pool.
- Long-running read txns pin the WAL and stop checkpoints, so the `-wal` file grows. Watch for that.

## Backups

- Do NOT just `cp` the db file while it's live. Use `.backup` in the CLI, the online backup API, or `VACUUM INTO 'file'`.
- If copying files by hand, you need the `-wal` and `-shm` too, and it's still racy. Avoid.
- Streaming replication tools exist, worth it if RPO matters. Otherwise periodic `VACUUM INTO` to object storage is enough.
- Test the restore. Actually open the restored file and run `PRAGMA integrity_check;`.

## Gotchas

- Not on network filesystems (NFS etc). Locking is unreliable and WAL needs shared memory on the same host.
- Type affinity is loose. Use `STRICT` tables so a string doesn't silently land in an int column.
- `ALTER TABLE` is limited. For big changes: create new table, copy, drop old, rename, all in one txn.
- Autovacuum is off by default, so deleted space isn't returned. Occasional `VACUUM` or set `auto_vacuum=INCREMENTAL` at creation.
- Run `PRAGMA optimize;` before closing connections, and `ANALYZE` after big loads.

## When to move on

- Need multiple app servers writing at once.
- Write throughput gets saturated by the single writer.
- Need row-level access control or heavy role management.

Until then, one box + SQLite + good backups is plenty.
