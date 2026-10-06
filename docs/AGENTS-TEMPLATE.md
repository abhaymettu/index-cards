# AGENTS.md template for a vault that agents operate

The instruction file is the layer that makes the vault agent-operable: a short standing contract
that loads into context at the start of every session, so conventions survive handoffs and fresh
sessions. Put one at the vault root. Claude Code reads `CLAUDE.md`, other agents read `AGENTS.md`:
keep one file and link the other (`ln -s AGENTS.md CLAUDE.md`, or `@AGENTS.md` inside `CLAUDE.md`).

Keep it to 5-15 lines of contract plus the layout. Copy the block below and edit the names.

```markdown
# <Vault name>: agent contract

## Layers
1. Raw: <inbox folder>. Sources land here untouched. Agents read, never rewrite.
2. Cards: <vault>/index-cards/. One card per entity; the indexer keeps the Timeline section,
   agents own the bullets outside the Timeline markers.
3. This file: the schema. Layout, naming, linking, workflows.

## Conventions
- Every bullet an agent writes carries `[source; added]` metadata. No source, no bullet.
- Link entities with [[wikilinks]]. Names are the card file names.
- One index file (the vault entry file) and one append-only log. Update both on every write.
- Folders listed in `skip_dirs` (credentials, private archives) are never read or indexed.

## Workflows
- Ingest: read the new source, update the cards it touches, append to the log.
- Query: search cards first, open sources only to verify a claim.
- Lint (nightly): the deterministic pass proposes a diff; a change set that lowers the eval
  score is rejected by the gate. Never apply a proposal by hand without reading the diff.

## Verify ritual
Run the indexer sweep and the eval check; both must report zero errors before you stop.
```

For repos that agents work in (not the vault), the same shape applies: what the repo is, its
invariants, its verify ritual, plus a link to one shared conventions file.
