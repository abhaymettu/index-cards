# on-call runbook habits

## before the shift

- skim last week's handoff notes first. most pages repeat, so the answer is usually already written down
- check that pager actually rings on silent/DND. test it, don't assume
- laptop charged, VPN works, 2FA device within reach. sounds dumb, has bitten me at 3am
- confirm I have access to prod dashboards, logs, and the deploy tool. permissions rot quietly
- know who the secondary is and how to reach them without a chat app

## when a page fires

- ack immediately, even before understanding. stops the escalation timer and tells others someone's on it
- open an incident note/thread right away and timestamp everything. memory is garbage after the fact
- first question: what changed? deploys, flags, config, cron, upstream deps. most incidents are a change
- second question: is it getting worse, stable, or recovering?
- mitigate before root-causing. rollback > hotfix > "let me just understand this"
- if stuck 15 min with no progress, escalate. no heroics

## writing runbooks

- start with symptom, not system. "p99 latency spikes" not "the cache service"
- every step should be copy-pasteable. commands with real flags, no "check the logs"
- include what *good* output looks like so I can tell when it worked
- put the rollback step next to the risky step, not in a separate section
- link dashboards by direct URL, not "see the metrics page"
- date + owner at the top. a stale runbook is worse than none, since it gets trusted
- if I had to improvise during an incident, update the doc the same day

## communication

- status update every 20-30 min even if it's "no change". silence makes people ping
- say what's known, what's unknown, next step. three lines max
- don't speculate about cause in public channels until confirmed
- keep customer-facing wording plain, no internal jargon

## after

- handoff note before closing the laptop: what happened, what's still flaky, what I'd watch
- small fixes (alert thresholds, missing doc steps) get done immediately, bigger ones become tickets
- delete or tune any alert that paged but needed no action. noisy alerts train me to ignore real ones
- sleep. seriously. a tired follow-up causes the next incident
