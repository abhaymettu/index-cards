# flaky test triage

## first 5 min
- don't just rerun and move on. rerun once to confirm it's actually flaky vs just broken on main
- check: does it fail on the same line every time? same error msg? if yes probably deterministic w/ a rare trigger
- look at when it started. `git log` on the test file + whatever it touches, last ~2 weeks
- grab the failing CI log before it rotates out. paste the relevant bit into the ticket

## common causes (roughly by how often I see them)
1. **time** – `sleep` instead of waiting on a condition, tests relying on wall clock, timezone/DST edges, midnight rollover
2. **shared state** – leftover rows in db, global singletons, env vars, temp files w/ fixed names, cached modules
3. **ordering** – passes alone, fails in suite (or reverse). run with random seed / shuffle to expose
4. **async races** – unawaited promise, callback firing after teardown, event not yet flushed
5. **resource limits** – port already in use, CI box low on mem/cpu, parallel workers fighting over one fixture
6. **external stuff** – real network calls, third party sandbox being slow, DNS

## repro tricks
- loop it: run 50-200x in a tight loop, note failure rate. rate matters for judging a fix later
- run under CPU stress or with fewer cores to widen race windows
- pin the seed from the failing run, replay it
- run the test in isolation vs. with its neighbors (bisect the suite if order-dependent)
- add temp logging w/ timestamps, not a debugger. debugger changes the timing

## fix vs quarantine
- if fix is < ~1hr, just fix it
- otherwise quarantine: tag it, keep it running but non-blocking, open a ticket w/ owner and a deadline
- never quarantine without the ticket. quarantine w/o a ticket = deleted test
- never "fix" by bumping timeouts unless the thing is truly slow by design. usually hides the race

## after the fix
- rerun the loop, want 0 failures in at least 10x the original failure rate window
- note root cause category in the ticket so patterns show up later
- if same cause hits 3+ times, fix the helper/fixture, not the tests

## things to remember
- a flaky test is often a real bug in prod code, not only a test problem
- retries in CI are a smell, fine as a stopgap but track retry count somewhere
