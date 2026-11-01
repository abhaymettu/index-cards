# writing better RFCs

## start with the problem, not the solution
- first paragraph = what hurts, who it hurts, how I know (numbers if I have them)
- if a reader can't restate the problem in one sentence after the intro, rewrite the intro
- the solution section should feel obvious *because* the problem section was sharp
- I keep jumping to design because that's the fun part. force myself to write the "why now" first

## scope
- explicit **non-goals** list. most useful section, cheapest to write
- say what I'm NOT deciding in this doc (naming, rollout dates, etc.) so review doesn't derail
- one RFC = one decision. if there are three decisions, split it into three docs
- TL;DR at top, 3-4 lines max. what I'm proposing + what I need from reviewers

## alternatives
- always list at least 2 real alternatives, plus "do nothing"
- "do nothing" needs actual cost: what happens in 6 months if we skip this?
- be fair to the options I didn't pick. if I can't steelman it, I haven't understood it
- table works well: option / pros / cons / cost / reversibility
- reversibility is underrated. one-way doors need way more scrutiny than two-way ones

## design detail
- diagrams only if they replace a paragraph. otherwise skip
- show one concrete example end to end (request in, state change, response out) before abstract description
- call out the ugly parts myself: migration, failure modes, data backfill, on-call burden
- put open questions in their own section with an owner each, not buried in prose

## getting useful review
- say what kind of feedback I want: "poke holes in the failure handling" beats "thoughts?"
- set a review deadline up front, ~1 week. silence past that = soft approval, say so in the doc
- comments in the doc, decisions recorded back in the doc. no decisions living only in chat
- keep a "changes since v1" log at the bottom so people don't re-read everything
- don't get defensive in comments; if the same question comes up 3 times the doc is unclear, fix the doc

## after approval
- link the RFC from the code/tickets it spawns
- mark status clearly: draft / in review / accepted / superseded
- revisit after ship: what did we get wrong? add a short postmortem paragraph at the end
- old RFCs are a decent onboarding reading list, so keep them findable

## checklist before sending
- [ ] problem + why now
- [ ] non-goals
- [ ] alternatives incl. do nothing
- [ ] rollout + rollback
- [ ] open questions w/ owners
- [ ] review deadline
