# eval design for LLM apps

## start from failures, not metrics
- read ~50-100 real outputs before building anything. write down what's actually wrong in plain words
- failure categories come from the data, not from a generic rubric ("helpfulness", "coherence" tell me nothing)
- every bug I find in prod becomes a test case. the set grows from incidents
- keep a "weird inputs" bucket: empty strings, huge pastes, wrong language, prompt-injection-looking text

## dataset
- 30 good cases beats 1000 scraped ones nobody looked at
- tag each case (category, difficulty, source) so I can slice results later
- split: small fast set (<2 min, runs on every prompt change) and a bigger nightly set
- freeze a held-out chunk. don't tune prompts against it or it stops meaning anything
- store inputs + expected behavior, not just exact expected strings. often the "expected" is a property ("cites the source", "refuses", "valid json")

## scoring
- prefer deterministic checks first: schema validity, regex, tool-call args, exact match on extracted fields
- code-based assertions are cheap and don't drift. use them for anything checkable
- LLM-as-judge only for fuzzy stuff. binary pass/fail per criterion, one criterion per judge call. 1-10 scales are noise
- judge prompt gets a short rubric + 2-3 labeled examples
- **validate the judge**: hand-label ~40 cases, compute agreement with the judge. if it's under ~85% fix the judge before trusting any number
- judge model ≠ the model being tested if possible (self-preference bias)

## running evals
- pin model version, temperature, prompt hash in every run record
- run flaky cases N times (3-5), report pass rate not a single pass/fail
- log full traces (inputs, retrieved context, tool calls, output) so a failure is debuggable without rerunning
- diff against the last run per case, not just the aggregate. aggregate hides regressions that cancel out

## interpreting
- a score going up 2 points with a small set is probably noise. check variance first
- look at the failures every time. numbers tell me where, reading tells me why
- separate retrieval failures from generation failures in RAG, otherwise I fix the wrong thing
- track cost and latency next to quality, a +3% win that doubles tokens may not be a win

## gotchas
- eval set leaks into few-shot examples in the prompt. check overlap
- judge rewards length. add a length-controlled check
- metrics that never fail are useless, prune them
- when the product changes, the eval set goes stale. review it monthly

## todo
- [ ] set up the fast/nightly split
- [ ] label the judge calibration set
- [ ] add the trace diff view
