# writing better RFCs

Notes to self after writing too many that nobody finished reading.

## before writing

- if I can't state the problem in 2 sentences, I'm not ready to write. do that first, then close the doc and go for a walk
- talk to the 2-3 people most affected *before* drafting. an RFC should never be the first time someone hears about it
- decide what decision is actually needed. "approve this design" vs "pick between A and B" vs "FYI, objecting window open till Friday" are three different docs
- check if a short Slack thread or 1-pager would do. not everything needs the full template

## structure that works

1. **Problem / context**: why now, what's broken, who feels it
2. **Goals and non-goals**: non-goals matter more than I think. kills half the scope arguments early
3. **Proposal**: the actual thing, with a diagram if it has more than 3 moving parts
4. **Alternatives considered**: real ones, with why they lost. not strawmen
5. **Risks / open questions**: put the shaky parts up front, don't bury them
6. **Rollout + rollback**: how do we get there, how do we back out

Put a TL;DR at the top. Reviewers decide in the first 30 seconds whether to engage.

## writing tips

- concrete numbers over adjectives. "p99 is 800ms, target 200ms" not "too slow"
- one example walkthrough beats three paragraphs of abstraction
- define terms once, use them consistently. don't rename things halfway
- cut anything that doesn't change a reader's vote
- length: if it's over ~5 pages the real design is probably fuzzy

## getting useful review

- name specific reviewers and say what I want from each ("sanity check the migration plan")
- set a deadline. open-ended review = no review
- list open questions explicitly so people can answer them directly instead of vibing
- comments I get most often: "what about X?" where X was in non-goals but I didn't say why. add one line of reasoning

## after

- record the decision and date at the top, even if it's "rejected"
- link the RFC from the code / ADR so future me finds it
- revisit 3 months later: did the risks I listed actually happen? feeds back into the next one

## anti-patterns I keep doing

- writing the solution first and backfilling the problem
- alternatives section written last, at 11pm, shows
- hiding the controversial bit in section 7
- asking for "thoughts?" with no question attached
