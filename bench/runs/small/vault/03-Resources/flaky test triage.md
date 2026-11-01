# flaky test triage

## first 5 min
- don't just rerun and move on. rerun once to confirm it's flaky vs actually broken, note result
- check if it fails on main too or only on a branch. branch-only = probably my change
- look at the failure message before the stack. timeouts, "element not found", and "connection refused" each point different directions
- grab the seed / random order if the runner prints it. without it, can't reproduce

## repro
- loop it: `for i in {1..50}; do npm test -- -t "name" || break; done` (swap in whatever runner). stops on first fail
- if it passes alone but fails in suite → shared state or order dependence
- run with parallelism off. if it vanishes, it's a race or shared resource (port, temp file, db row)
- run under CPU throttle or in a container with fewer cores. surfaces timing bugs that a fast laptop hides

## usual suspects
- **time**: real clocks, `sleep`, tz differences, tests that cross midnight or a month boundary
- **async**: missing await, assertion before the promise settles, fire-and-forget callbacks
- **shared state**: globals, singletons, cached modules, leftover db rows, env vars not restored
- **ordering**: relying on map/set iteration, unsorted query results, `ls` order
- **network**: real calls sneaking in, hardcoded ports, dns slowness
- **randomness**: unseeded rng, uuid collisions in fixtures (rare but happens)
- **resource limits**: file handles, memory on CI runners, disk full on shared agents

## fixes (preference order)
1. make the test deterministic: inject the clock, seed rng, isolate data per test
2. wait on a condition, not a duration. poll with a timeout instead of `sleep(2)`
3. fix the real bug if the test is exposing a race in prod code (happens more than I want)
4. tighten teardown so state can't leak
5. last resort: retry annotation, but only with a ticket and a note saying why

## quarantine rules
- quarantine if it fails >~2% of runs and I can't fix it same day
- quarantined tests still run, just non-blocking, so I keep the data
- every quarantine gets an owner and a date to revisit. otherwise they rot
- delete the test if it's been quarantined a month and nobody missed it

## after
- write one line in the commit about root cause category (time / async / state / etc). helps spot patterns later
- if same category keeps showing up, fix the helper or fixture, not the individual tests
