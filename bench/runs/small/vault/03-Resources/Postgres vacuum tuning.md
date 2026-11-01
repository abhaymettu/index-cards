# Postgres vacuum tuning

Quick ref for when tables bloat or autovacuum falls behind. Not exhaustive, just what I keep looking up.

## Why it matters

- Dead tuples pile up after UPDATE/DELETE. Vacuum reclaims space for reuse (not returned to OS, except trailing pages).
- Also freezes old xids, so no wraparound shutdown. This one is non-negotiable.
- Bloat -> slower seq scans, bigger indexes, worse cache hit ratio.

## Default triggers (usually too lazy)

- `autovacuum_vacuum_scale_factor = 0.2` -> waits for 20% of table dead. Fine for small tables, awful for 100M+ row ones.
- `autovacuum_vacuum_threshold = 50` base added on top.
- Analyze scale factor default 0.1.

Fix per table, not globally:

```sql
ALTER TABLE events SET (
  autovacuum_vacuum_scale_factor = 0.01,
  autovacuum_vacuum_threshold = 1000,
  autovacuum_analyze_scale_factor = 0.02
);
```

For insert-only tables, `autovacuum_vacuum_insert_scale_factor` matters (PG13+) so visibility map gets set and index-only scans work.

## Throttling / speed

- `autovacuum_vacuum_cost_limit` default effectively 200 -> very slow on modern SSDs. Bumping to 1000-2000 is common.
- `autovacuum_vacuum_cost_delay` 2ms default now. Lower it for faster runs.
- `autovacuum_max_workers` = 3. More workers don't help if cost limit is shared across them (it is, budget is split). Raise limit alongside.
- `maintenance_work_mem` / `autovacuum_work_mem`: bigger means fewer index scan passes. 1GB is a reasonable ceiling to try.

## Checking what's going on

```sql
SELECT relname, n_live_tup, n_dead_tup,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 20;
```

- `pg_stat_progress_vacuum` for running jobs.
- `log_autovacuum_min_duration = 0` temporarily to see what each run does.
- Age check: `SELECT datname, age(datfrozenxid) FROM pg_database;` Worry past ~1B, panic near 2B.

## Things that block vacuum

- Long-running transactions (check `pg_stat_activity` by `xact_start`).
- Idle in transaction sessions. Set `idle_in_transaction_session_timeout`.
- Abandoned replication slots holding back xmin.
- Orphaned prepared transactions.

If dead tuples won't go away after vacuum, it's almost always one of these.

## When to go heavier

- `VACUUM FULL` takes an exclusive lock and rewrites the table. Avoid on prod.
- `pg_repack` for online reclaim instead.
- Better long-term fix is usually lower fillfactor + HOT updates, or fewer updates to hot rows in the first place.
