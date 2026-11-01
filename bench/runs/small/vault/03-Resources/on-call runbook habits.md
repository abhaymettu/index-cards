# on-call runbook habits

## before the shift

- skim last week's handoff notes first. 5 min, saves an hour of "wait, is this known?"
- check that pager actually fires. test page to my phone, confirm DND exceptions are still on (os updates reset this more than once)
- laptop charged, hotspot tested, vpn creds not expiring mid-shift
- bookmark the dashboards I always end up opening: error rate, queue depth, db connections, deploy history. one folder, same order every time
- look at what's scheduled to deploy or migrate during the window. if something risky is landing Friday afternoon, say so early

## when the page hits

- ack fast, then read the alert twice. half the time the alert text already says what to check
- first question is always "what changed?" deploys, config flips, flag rollouts, cert expiry, traffic spikes
- open an incident doc/thread immediately and timestamp as I go. future me at 3am is not going to remember the order
- rollback > forward fix when unsure. can debug calmly after bleeding stops
- don't restart things before grabbing logs/heap dump/state. restart destroys evidence
- if stuck >20 min, escalate. not a failure, it's the point of having a secondary

## writing runbooks

- every step is a command I can paste, not a paragraph of vibes
- include expected output so I know if it worked
- put the "how to tell this is NOT the problem" section up top, kills a lot of wild goose chases
- link the runbook from the alert itself. if I have to search for it, it's already broken
- date + owner at the bottom. stale runbooks are worse than none
- add the dumb stuff: which region, which account, which kubectl context. wrong-context mistakes are the scariest

## after

- fix the runbook while it's fresh, same day. even one line
- if I did a manual step more than twice, it's a script ticket
- noisy alert that woke me up and needed no action → tune or delete it, don't just sigh
- write the handoff note before logging off: what fired, what I did, what's still smoldering
- sleep. seriously. don't be a hero the day after a bad night

## misc

- keep a "weird things I've seen" list. patterns show up over months
- communicate status on a schedule even if status is "still investigating"
- never run a destructive command from shell history without reading it first
