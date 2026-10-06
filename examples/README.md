# Examples (synthetic data only)

`vault/` is a five-note vault with one person, one project, one daily note with three captures, a
resources note with a bibliography mention, and a credentials folder the indexer must never read.
`questions.jsonl` is a three-question eval set over it, in `eval/memeval.py`'s format.

```sh
cd examples
printf '{"vault": "%s/vault", "lock": "/tmp/example.lock", "person_dirs": ["People"], "project_dirs": ["01-Projects"], "block_dirs": ["00-Inbox/Daily/"], "skip_dirs": ["03-Resources/Credentials"]}\n' "$PWD" > /tmp/example-config.json
INDEX_CONFIG=/tmp/example-config.json python3 ../indexer/indexer.py      # writes vault/index-cards/
python3 ../eval/memeval.py check questions.jsonl corpora.json            # 0 errors
python3 ../eval/memeval.py run questions.jsonl corpora.json              # ripgrep floor, hit@5 and MRR
```

Expected after the sweep: `vault/index-cards/_catalog.md`, `person/ann-lee.md` (links the person
note and the 09:15 capture), `project/alpha-engine.md`, `person/okafor.md` (the resources note,
not the bibliography line), and nothing from `03-Resources/Credentials/`.
