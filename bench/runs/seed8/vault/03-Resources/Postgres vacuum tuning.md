# Postgres vacuum tuning

## Why bother
Default autovacuum is tuned for small tables. On big, write-heavy ones it falls behind, bloat creeps up, and then wraparound anxiety shows up. Fix per table, not globally, unless the whole db is hot.

## Thresholds
- Default trigger: `autovacuum_vacuum_scale_factor = 0.2` → 20% of rows dead. On a 500M row table that's 100M dead tuples. Way too late.
- Per-table override is the move:
  `ALTER TABLE events SET (autovacuum_vacuum_scale_factor = 0.01, autovacuum_vacuum_threshold = 5000);`
- Same idea for analyze: `autovacuum_analyze_scale_factor = 0.02` or so.
- For insert-only tables, PG13+ has `autovacuum_vacuum_insert_scale_factor`, helps set visibility map bits so index-only scans actually work.

## Speed / throttling
- `autovacuum_vacuum_cost_limit` default (200 via vacuum_cost_limit) is stingy. Bump to 1000-2000 on modern SSDs.
- `autovacuum_vacuum_cost_delay` is 2ms by default now. Can go lower, 0 if IO is fine.
- Cost limit is shared across workers, so adding workers alone doesn't speed things up. Raise `autovacuum_max_workers` AND the cost limit together.
- `maintenance_work_mem` / `autovacuum_work_mem`: bigger = fewer index passes. Check the vacuum log for "index scans: N", want 1.

## Monitoring
- `pg_stat_user_tables`: `n_dead_tup`, `last_autovacuum`, `autovacuum_count`.
- `log_autovacuum_min_duration = 0` (or 1s) to see what it's actually doing.
- Long-running transactions and idle-in-transaction sessions block cleanup. Check `pg_stat_activity` ordered by `xact_start` first, before touching any settings.
- Stale replication slots and prepared transactions also hold back xmin. Easy to forget.
- Wraparound check: `SELECT datname, age(datfrozen_xid) FROM pg_database;` should be well under `autovacuum_freeze_max_age` (200M default).

## Gotchas
- Plain `VACUUM` doesn't shrink files, just marks space reusable. `VACUUM FULL` takes an exclusive lock, rewrites the table. Use `pg_repack` instead if downtime is a problem.
- Lots of HOT updates reduce bloat. Lower `fillfactor` (e.g. 85-90) on update-heavy tables to leave room.
- Don't kill an anti-wraparound autovacuum. It will just restart, and it won't be cancelled by lock conflicts like normal ones.
- Tuning order: kill long txns → per-table scale factors → cost limit → memory → workers.

## TODO
- Dashboard for dead tuple ratio per table
- Alert on oldest xmin age
