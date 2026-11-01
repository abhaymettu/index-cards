# writing better RFCs

## before writing anything
- if I can't state the problem in 2 sentences, I'm not ready to write. do that first, then see if it still needs an RFC at all
- half the time a short design doc or a Slack thread is enough. RFC = decision that's expensive to reverse or touches multiple teams
- figure out who actually has to say yes. name the approvers up front, not after 2 weeks of comments
- talk to the 2-3 most skeptical reviewers *before* publishing. no surprises in the doc

## structure that works
- **TL;DR** at the top, 3-5 lines max. most readers stop here
- **Context / problem**: what hurts today, with real numbers if I have them (latency, incident count, hours lost)
- **Goals and non-goals**: non-goals do more work than goals. they kill scope creep in review
- **Proposal**: the boring concrete version. diagrams only if they replace a paragraph
- **Alternatives considered**: at least 2 real ones, plus "do nothing". say why each lost, fairly
- **Risks / open questions**: put them in, don't hide them. reviewers trust the doc more
- **Rollout + rollback**: how do we ship it in steps, how do we back out

## writing style
- short sentences. active voice. no "we might potentially consider"
- define terms once, use them the same way everywhere
- one decision per section so comments don't tangle
- put examples right next to abstract claims (sample request, sample schema, before/after)
- cut anything that doesn't change someone's vote

## review process
- set a deadline for comments (a week is usually fine) and a date for the decision
- mark open questions explicitly so people know what feedback I actually need
- resolve comments in the doc, don't let decisions live in side chats
- if debate goes past ~2 rounds, get on a call, then write the outcome back into the doc
- silence ≠ agreement. ping specific people

## after it's approved
- update status at the top (draft / accepted / superseded)
- link the implementation tickets back to the RFC
- when reality diverges, edit the RFC or add a short addendum. stale RFCs are worse than none
- revisit a few months later: did it solve the problem stated at the top?

## common failure modes
- solution looking for a problem
- too long, nobody reads past page 2
- alternatives are strawmen
- no owner after approval, so it just sits
