# eval design for LLM apps

## start from failures, not metrics
- read ~50-100 real outputs before writing any eval. tag what's actually wrong. the tags become the test categories
- generic scores (helpfulness, "quality 1-5") hide everything. want narrow checks tied to a failure I've actually seen
- every prod bug -> new eval case. cheapest way to build a regression set that matters
- keep a "known bad" bucket separate from the "should always pass" bucket. different purpose, different alert thresholds

## dataset
- 30 good cases beats 1000 scraped ones nobody looked at
- mix: happy path, edge inputs (empty, huge, wrong language, injection attempts), and adversarial stuff users really do
- version the dataset like code. a score change means nothing if the cases changed under it
- hold out a slice I never tune prompts against, otherwise I'm just overfitting by hand
- sample from real traffic monthly, drift is real

## graders
- order of preference: exact/programmatic check > structured-output check (schema, regex, field compare) > LLM judge > human
- if it can be asserted in code, assert it in code
- LLM judge: binary pass/fail with a written rubric, not a 1-10 scale. one criterion per judge call
- have the judge give reasoning first, then verdict. log both
- spot check judge against ~30 human labels, track agreement. recheck when judge model changes
- watch for judge bias: prefers longer answers, prefers its own model family's style, position bias in pairwise
- pairwise comparison good for "is B better than A", bad for absolute thresholds

## running them
- run each case multiple times (3-5) when temp > 0, look at pass rate not single result
- fast tier on every PR (small, mostly programmatic, under ~2 min). big tier nightly
- pin model version + prompt hash + dataset version in every result row
- store full traces, not just scores. debugging a fail without the trace is miserable
- cost tracking per run, otherwise the nightly quietly gets expensive

## reading results
- look at per-category breakdown, the aggregate lies
- a flat score after a change doesn't mean nothing changed, diff the individual cases that flipped
- set thresholds from baseline variance, not vibes. if noise is ±3% a 2% drop is nothing
- eval passing != good product. still need online signals (thumbs, retries, edits, abandon rate)

## todo
- [ ] write the rubric template for judge prompts
- [ ] script to turn a flagged prod trace into an eval case in one command
- [ ] measure run-to-run variance on current suite before setting any gate
