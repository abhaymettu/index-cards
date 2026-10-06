# Vault layout template

The indexer does not impose a layout; it reads one from the instance config. The layout below is
the one the code was built against (PARA plus a few conventions) and is what
`config/indexer.example.json` describes.

```
Vault/
  00-Inbox/Daily/YYYY-MM-DD.md     captures; one Timeline entry per **HH:MM Title** block
  01-Projects/<Name>.md            a project note, or a folder whose first note defines it
  02-Areas/<Name>.md               ongoing areas; 02-Areas/Relationships/ holds people too
  03-Resources/                    reference; Credentials/ is never read
  04-Archives/<Name>.md            finished projects
  People/<Name>.md                 one note per person; frontmatter name: and context:
  Wiki/<Topic>.md                  topics; frontmatter type: project makes a project
  Journal/, Decisions.md, log.md   dated logs; one entry per block
  index-cards/                     written by the indexer, read by agents
    _catalog.md                    every card: kind, entry count, last seen
    _registry.md                   ## kind headings, "- Name: alias, alias" lines
    person/ project/ harness/ area/ topic/
```

## Entities

- A note in a person, project, area, topic or archive folder defines an entity of that kind.
- A registry line (`- Name: alias, alias` under a `## kind` heading) defines one with no note and
  overrides guessed aliases. An alias with a capital letter matches case-sensitively; an
  all-lowercase one matches any case. A common English word gets no automatic alias: it matches
  only by wikilink or by a registry alias.
- Bibliography mentions ("Okafor Y,", "Okafor et al.") do not count as mentions of a person.

## Cards

- Frontmatter (indexer-owned): `type`, `kind`, `entity`, `aliases`, `entries`, `last_seen`, `updated`.
- `## Summary` and anything else outside the markers: yours. The indexer seeds it once and never
  rewrites it. The optional Summary pass rewrites only this section, with cited facts.
- `## Timeline` between `<!-- index:start -->` and `<!-- index:end -->`: indexer-owned. One line per
  (entity, source, block), newest first: date, time when known, a link, a one-line excerpt, and a
  hidden stable key `<!--k:xxxxxxxxxx-->`. An entry whose source disappeared stays, marked
  `(source gone)`. An excerpt line that contains a key-shaped token is dropped, not truncated.

## The bullet contract

Every bullet you or an agent writes on a card outside the markers ends with per-bullet metadata:

```
- <one fact, one line> [source: <ref>[, <ref>...]; added: YYYY-MM-DD]
```

- `source`: a `k:` Timeline key on the same card (preferred: it survives a note moving), a
  vault-relative note path, a `~/` path, or a URL.
- `added`: the day the bullet was written.
- Other keys are allowed (`[key: value; ...]`); `source` and `added` make a bullet count as sourced.
- A bullet the Summary pass wrote, `- Kind: text (since YYYY-MM-DD; k:...)`, already carries both.
- Placeholders and housekeeping lines (`Defining notes`, `Links`, `Summary as of`, `Tags`) need none.

`indexer.py --unsourced` lists the bullets that break the contract; the nightly report counts them.

## What runs

- Per minute: `indexer.py --if-changed` (cron). Sweeps only when an input file or folder is newer
  than the last sweep; never stats its own output.
- Nightly, your call: `nightly.py` (propose) then `nightly.py --apply` (gated).
- Optional, your call: `consolidate.py run --commit` nightly and `consolidate.py lint` weekly.
