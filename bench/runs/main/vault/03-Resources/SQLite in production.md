# SQLite in production

Notes to self. SQLite is fine for way more than I used to assume, as long as the setup is right.

## When it fits

- Single-writer workloads, read-heavy. Most internal tools and small SaaS fall here.
- One app server (or one primary + read replicas via a replication tool). Multiple app servers writing to the same file over NFS = no. Don't.
- Data size under a few hundred GB is comfortable. Past that, backups and vacuum get painful.
- Doesn't fit: high write concurrency, multi-node writes, needing row-level perms.

## Pragmas I always set

Set per connection, not per DB (except journal_mode, which persists):

- `PRAGMA journal_mode = WAL;` readers don't block the writer
- `PRAGMA synchronous = NORMAL;` safe enough with WAL, big speedup
- `PRAGMA busy_timeout = 5000;` otherwise get SQLITE_BUSY instantly
- `PRAGMA foreign_keys = ON;` off by default, easy to forget
- `PRAGMA cache_size = -20000;` ~20MB page cache
- `PRAGMA temp_store = MEMORY;`

Forgetting busy_timeout caused most of my "database is locked" errors.

## Concurrency gotchas

- WAL still allows only one writer at a time. Keep write transactions short.
- Use `BEGIN IMMEDIATE` for transactions that will write. A deferred txn that upgrades from read to write can fail with BUSY even with a timeout.
- Separate pools: one writer connection (or a small serialized queue), many reader connections.
- Don't hold a read txn open for a long time, it blocks WAL checkpointing and the -wal file grows.
- Long-running checkpoints: watch the size of the `-wal` file. If it keeps growing, something is holding a reader.

## Backups

- Never `cp` the db file while it's live. Misses the WAL, can be corrupt.
- Use `sqlite3 db ".backup 'out.db'"` or `VACUUM INTO 'out.db'`.
- Continuous streaming replication to object storage is worth it if losing a few minutes of data matters.
- Test the restore. Actually do it, with `PRAGMA integrity_check` after.

## Migrations and schema

- `ALTER TABLE` is limited. Dropping/changing columns often means create new table, copy, drop, rename. Wrap in a txn.
- Types are loose by default. Use `STRICT` tables on new schemas.
- Keep `PRAGMA user_version` as the schema version marker if no migration tool.

## Misc

- Run `PRAGMA optimize;` before closing connections or periodically.
- Docker: put the db on a volume, and make sure the `-wal` and `-shm` files live on the same filesystem.
- Check the SQLite version in the runtime. Some features (STRICT, RETURNING, JSON improvements) need recent builds.
