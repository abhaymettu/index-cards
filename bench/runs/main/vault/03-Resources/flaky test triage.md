# flaky test triage

First rule: don't just rerun and move on. A retry that goes green hides the bug and trains me to ignore red. Spend 10 min classifying before touching anything.

## first pass

- Does it fail locally with the same seed/order? If yes, not really flaky, just order-dependent.
- Check the last ~20 CI runs for this test. Fails on one runner type only? Suspect env, not code.
- Look at the failure message, not just "failed". Timeout vs assertion vs connection refused point at different causes.
- Did anything land near the first failure? `git log` on the test file and the code under it.

## usual suspects

- **Shared state**: leftover rows, global singletons, env vars set in one test and not reset. Run the test alone, then with the suite. If alone passes and suite fails, it's this.
- **Time**: `sleep(n)` waiting on async work, tests that assume "now" doesn't tick, midnight/DST/timezone edges. Replace sleeps with polling on a condition + timeout. Freeze the clock where possible.
- **Ordering**: assuming a map/set/query result comes back in insertion order. Add explicit sort or compare unordered.
- **Concurrency**: races between test setup and a background worker. Ports already in use when tests run in parallel. Use port 0 / random free port.
- **Network / external**: anything hitting a real service. Mock it or move it to a separate nightly job.
- **Resource limits**: CI box is slower and has fewer cores. A 100ms timeout that's fine on my laptop dies there.

## reproducing

- Loop it: run 200x in a shell loop, stop on first failure, keep output.
- Add CPU stress in the background to shake out timing bugs.
- Randomize order, log the seed so a failure is replayable.
- If it only fails in parallel, drop worker count to 1 and bump up to find the threshold.

## when to quarantine

- If I can't fix it in the timebox (~1 hr), tag it as quarantined so it stops blocking merges, but still runs and reports.
- Open a ticket with the failure message, frequency, and what I already ruled out. A quarantine with no ticket is just deleting the test slowly.
- Set a review date. Quarantined tests older than 2 weeks get fixed or deleted.

## after the fix

- Run the loop again to confirm, not just one green.
- Note root cause category in the commit message so patterns show up later.
- If same category keeps appearing, fix the helper or fixture, not each test.
