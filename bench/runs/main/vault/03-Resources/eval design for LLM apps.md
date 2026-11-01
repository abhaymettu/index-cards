# eval design for LLM apps

## start from failures, not metrics
- read ~50-100 real outputs before building anything. tag what's actually wrong. the tags become the eval categories
- don't start with a generic "quality" score. it hides everything
- every prod bug that slips through → new test case. the set should grow from pain
- keep a "known bad" bucket separate from the "regression" bucket. different purpose

## dataset notes
- 30 good cases beats 1000 scraped ones nobody looked at
- mix: happy path, edge inputs (empty, huge, wrong language, junk), adversarial/injection, and "should refuse"
- store input + expected behavior, not always an exact expected string. often a rubric is better than a gold answer
- version the dataset like code. when scores jump, first check whether the data changed
- sample from real traffic regularly or it drifts away from what users do

## scoring
- prefer deterministic checks first: schema valid, required fields present, regex, tool call correct, length bounds, no banned strings
- code-checkable stuff should never go to an LLM judge
- LLM-as-judge for fuzzy things only (tone, helpfulness, faithfulness to source)
  - binary or 3-point scale, not 1-10. 1-10 is noise
  - one criterion per judge prompt
  - make it explain before it scores
  - judge with a different/stronger model than the one being tested if possible
- spot-check judge against my own labels. aim for agreement I'd actually trust (~85%+), else fix the prompt
- watch for position bias and verbosity bias in pairwise comparisons. randomize order

## running them
- temp 0 where possible, but still run n>1 on flaky cases and look at pass rate
- split: fast suite (~minutes, runs on every prompt change) vs full suite (nightly or pre-release)
- log full traces with each run so a failure can be debugged without rerunning
- track cost and latency next to quality. a +2% win that doubles tokens usually isn't a win

## reading results
- look at diffs per case, not just the aggregate. averages hide regressions in small slices
- slice by category/input type
- small deltas on small sets = noise. don't ship decisions on a 1-point change over 40 cases
- when an eval saturates (~100%), it's done teaching me anything. add harder cases

## gotchas
- eval set leaking into few-shot examples or prompt tweaks → overfit. hold out a set I never tune against
- model/provider updates silently change behavior. rerun the full suite on a schedule even with no code changes
- end-to-end evals for the whole pipeline, plus component evals (retrieval, tool selection) so I know where it broke
- human review is still the ground truth. budget a small weekly pass
