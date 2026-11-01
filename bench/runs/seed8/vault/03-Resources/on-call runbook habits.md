# on-call runbook habits

## before the shift

- skim the last 2 handoff notes + any open incidents. don't start cold.
- check pager actually fires. test page to my phone, confirm DND override works. burned by this once, never again
- laptop charged, hotspot tested, VPN creds not expiring mid-week
- know who the escalation is for each tier BEFORE needing them. save numbers in phone, not just the wiki
- glance at deploy calendar. anything big landing during my shift = read the rollback steps now

## when the page hits

- ack first, think second. stops the re-page spam and tells others someone's on it
- open an incident doc/thread immediately, even if it's just "looking, 02:14". timestamps save me later
- check the boring stuff first:
  - recent deploys / config changes
  - disk, memory, cert expiry
  - upstream dependency status pages
  - did traffic spike or drop?
- mitigate before root-causing. rollback, flip the flag, scale up, restart. *then* dig
- if 15 min in and no progress → escalate. no ego. pulling someone in early is cheaper than a long outage

## writing runbooks (for future me at 3am)

- assume the reader is groggy and stressed. short steps, copy-pasteable commands
- every alert links straight to its runbook. if it doesn't, that's a bug
- put "how to tell it's fixed" at the end of each one. easy to forget
- include the *why* in one line so I can judge when the steps don't apply
- date + "last verified" at top. stale runbooks are worse than none
- dead-end sections: list what I already tried and ruled out

## after

- write handoff while it's fresh, not the next morning
- if I touched something manually, note it exactly (command, host, time)
- any alert that fired and needed no action → ticket to tune or delete it
- any step I had to figure out live → goes into the runbook same day
- sleep. seriously. take the comp time

## things I keep relearning

- don't run a fix I don't understand just because it's in an old thread
- read-only commands first, always
- say what I'm about to do in the incident channel before doing it
- most pages are one of 4 or 5 causes. keep a short "usual suspects" list at the top of the doc
