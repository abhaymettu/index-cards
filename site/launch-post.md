# Launch post drafts (for Abhay to send; nothing has been posted)

## X

agent memory benchmarks mostly measure chat logs. i measured memory over a markdown vault: same model, same
4k-token budget, grep vs bm25 vs embeddings vs a claude-code-style memory file vs a deterministic entity index.
index 89.5%, embeddings 82.1%. but let the agent grep on its own and the index stops helping.
github.com/abhaymettu/index-cards

## Hacker News (Show HN)

Title: Show HN: Index-cards, a measured memory layer for coding agents over a markdown vault

Text: index-cards keeps one markdown card per person and project in your notes vault, listing every dated mention,
built by code with no model calls. I benchmarked it on fictional vaults with known answers, against grep, BM25,
embedding RAG, hybrid retrieval and a Claude Code style memory file, all at the same 4,000-token budget and with the
same answering model. On a world generated after the retriever was frozen, cards answer 89.5% and embeddings 82.1%.
Most of the gap is questions that need two notes. Two results surprised me. Stale facts were rarely the failure once
chunks carry dates. And in an unbudgeted agent loop, where the model greps the vault itself, the cards didn't help
Sonnet and hurt Haiku. Cached answers are committed, so every table rescores without model calls.
