# Brain Memory Layer Constitution

## Core Principles

### I. Sources Are Immutable

- The indexer MUST NOT modify, move, rename or add frontmatter to any source note or `~/audit`
  artifact. It writes only inside `<vault>/index-cards/` and its own log and lock under
  its own cache folder.
- `Raw/` stays read-only.

Rationale: the vault has more writers than readers (UPGRADE-PLAN 3.2). A layer that edits sources
competes with brain-route, reconcile and every capture lane.

### II. Update In Place, Never Duplicate

- One card per entity, at a stable path. A run rewrites a card only when its content changed.
- Every Timeline entry carries a stable key; the same key is never written twice.
- An entry whose source file disappeared is kept and marked, not dropped.
- Text outside a card's Timeline markers belongs to agents and the human, and the indexer MUST
  leave it byte-identical.

### III. Deterministic and Free to Run

- Indexing MUST NOT call a model. It runs every few minutes, forever, and costs nothing per run.
- The same inputs MUST produce byte-identical cards; a second sweep with no source change writes
  nothing.
- LLM synthesis, if added later, is a separate optional pass that writes only the Summary section.

### IV. No Secrets Leave Their Folder

- `03-Resources/Credentials/`, `04-Archives/Fragments/` and `05-Bridge/exec/` are never read.
- Any excerpt line containing a key-shaped token (32+ key characters) is dropped, not truncated.

### V. Quiet Machine Citizen

- Runs from cron under `/usr/bin/python3` with the stdlib only. `/usr/sbin/cron` holds Full
  Disk Access; a LaunchAgent running python is denied the iCloud vault by TCC (measured on one Mac, 2026-10-03).
- Its change detection MUST NOT stat anything it writes (F4 lane-safety rule).
- It sends no notifications and adds no surface he has to open; the vault keeps its one entry file.

## Constraints

- Plain markdown readable in Obsidian on the phone and by agents grepping the git mirror.
- No em dashes in generated text.
- Open-source first: a baseline that met these principles would have been adopted (see
  `specs/001-memory-layer/research.md`; none did).

## Governance

This constitution outranks the spec and plan. Amending it needs a dated line here saying what
changed and why.

- 2026-10-03 1.0.1: Principle V moved from launchd to cron after the first LaunchAgent run was
  denied the vault by TCC.

**Version**: 1.0.1 | **Ratified**: 2026-10-03 | **Last Amended**: 2026-10-03
