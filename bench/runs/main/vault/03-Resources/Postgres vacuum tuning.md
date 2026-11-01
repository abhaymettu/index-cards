# Postgres vacuum tuning

Quick ref for when tables bloat or autovacuum falls behind. Not exhaustive, just what I keep having to look up.

## Defaults that bite

- `autovacuum_vacuum_scale_factor` = 0.2 → vacuum fires after 20% of rows are dead. Fine for small tables, awful for big ones. 100M rows means 20M dead tuples before anything happens.
- `autovacuum_naptime` = 1min, rarely worth touching.
- `autovacuum_max_workers` = 3. Workers share the cost budget, so adding more without raising the limit just slows each one down.
- `autovacuum_vacuum_cost_limit` = 200 (via `vacuum_cost_limit`). Way too low on modern SSDs. Bump to 1000–2000 and see.

## Per-table overrides

Better than global changes for the hot tables:

```
ALTER TABLE events SET (
  autovacuum_vacuum_scale_factor = 0.01,
  autovacuum_vacuum_threshold = 5000,
  autovacuum_analyze_scale_factor = 0.02
);
```

Rule of thumb: big append/update-heavy tables get scale_factor 0.01–0.05. Keep the threshold as a floor so tiny tables don't thrash.

## Checking what's going on

- `pg_stat_user_tables`: look at `n_dead_tup`, `last_autovacuum`, `last_autoanalyze`.
- Dead ratio = `n_dead_tup / (n_live_tup + n_dead_tup)`. Over ~10–20% on a busy table means autovacuum isn't keeping up.
- `pg_stat_progress_vacuum` for live runs. If it's stuck in "index vacuuming" repeatedly, too many indexes or `maintenance_work_mem` too small.
- Set `log_autovacuum_min_duration = 0` temporarily to see every run in logs.

## Things that block cleanup

- Long-running transactions hold back the xmin horizon, so dead rows can't be removed. Check `pg_stat_activity` for old `xact_start`.
- Idle in transaction sessions, same problem. Set `idle_in_transaction_session_timeout`.
- Stale replication slots pin xmin too. Check `pg_replication_slots`.
- Prepared transactions left lying around.

## Misc notes

- `maintenance_work_mem` bigger (512MB–1GB) means fewer index passes. Autovacuum uses `autovacuum_work_mem` if set.
- Plain `VACUUM` doesn't shrink files, it just makes space reusable. `VACUUM FULL` rewrites and takes an exclusive lock, so avoid in prod. Use `pg_repack` instead.
- Watch for wraparound: `age(datfrozenxid)` per DB. Anything past ~1B and I start worrying. Aggressive anti-wraparound vacuums can't be cancelled.
- Lower `fillfactor` (e.g. 85) on update-heavy tables to enable HOT updates and reduce vacuum load.
