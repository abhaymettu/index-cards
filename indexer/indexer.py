#!/usr/bin/env python3
"""index-cards: one card per person, project, harness, area and topic in an Obsidian vault.

Every run rebuilds each card's Timeline from the current sources (vault notes, an optional
folder of markdown reports, optional session digests) and merges it with what the card holds:
  - an entry is keyed by (entity, source, block); the same key is never written twice
  - an entry whose source file disappeared is kept and marked, never dropped
  - an entry whose source still exists but no longer mentions the entity is dropped
  - everything in a card outside the Timeline markers is left exactly as found
Cards are written only when their content changed, atomically.

Entities come from notes the vault already has (the folders the instance config names for
people, projects, areas, topics and archives) plus index-cards/_registry.md for things with no
note. Session digests (digest.py's JSONL for Claude Code transcripts) put one entry per session
on each project card the session names in its title, working directory or a prompt; the entry
points at the digest and at the transcript span. Runs under /usr/bin/python3 (3.9) from cron:
stdlib only.

  indexer.py               sweep and write
  indexer.py --if-changed  sweep only if an input changed since the last sweep (cron)
  indexer.py --unsourced   list agent-written bullets that lack [source: ...; added: YYYY-MM-DD] (specs/015)

Instance config: JSON at $INDEX_CONFIG (default ~/.config/index-cards/config.json). Keys, all
optional: vault, audit, session_digests, lock, cards (paths); skip_dirs, skip_files, block_dirs,
block_files, person_dirs, project_dirs, root_project_dirs, area_dirs, topic_dirs, archive_dirs
(vault-relative names); not_entities (globs of notes or folders that are read but define no
entity); catalog_note (a line added to the catalog intro).
"""
import argparse
import fcntl
import fnmatch
import glob
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone

HOME = os.path.expanduser("~")
CONFIG = os.path.expanduser(os.environ.get("INDEX_CONFIG", "~/.config/index-cards/config.json"))
KINDS = ["person", "project", "harness", "area", "topic"]
START, END = "<!-- index:start -->", "<!-- index:end -->"


def configure(cfg):
    """Set the module's paths and vault layout from an instance config dict."""
    global VAULT, AUDIT, EXTRA, DIGESTS, LOCK, STAMP, CARDS, REGISTRY, CATALOG, CATALOG_NOTE, NOT_ENTITIES
    global SKIP_DIRS, SKIP_FILES, BLOCK_DIRS, BLOCK_FILES, PERSON_DIRS, PROJECT_DIRS, ROOT_PROJECT_DIRS
    global AREA_DIRS, TOPIC_DIRS, ARCHIVE_DIRS
    path = lambda k, d="": os.path.expanduser(cfg.get(k, d))
    VAULT, AUDIT, DIGESTS = path("vault"), path("audit"), path("session_digests")
    LOCK = path("lock", "~/.cache/index-cards/index-cards.lock")
    STAMP = LOCK[:-len(".lock")] + ".stamp"
    CARDS = path("cards", os.path.join(VAULT, "index-cards"))     # elsewhere only for a scratch sweep
    REGISTRY = os.path.join(CARDS, "_registry.md")
    CATALOG = os.path.join(CARDS, "_catalog.md")
    CATALOG_NOTE = cfg.get("catalog_note", "")
    EXTRA = cfg.get("extra_files", [])                # globs of lane logs outside the vault and audit
    # Never read: machine traffic, known secret stores, templates, generated or churning files.
    SKIP_DIRS = {".obsidian", ".trash", ".git"} | set(cfg.get("skip_dirs", []))
    SKIP_FILES = set(cfg.get("skip_files", []))
    # Files that are logs of many dated events: one entry per block, not per file.
    BLOCK_DIRS = tuple(cfg.get("block_dirs", []))
    BLOCK_FILES = set(cfg.get("block_files", []))
    PERSON_DIRS = cfg.get("person_dirs", [])
    PROJECT_DIRS = cfg.get("project_dirs", [])        # notes and subfolders are projects
    ROOT_PROJECT_DIRS = cfg.get("root_project_dirs", [])
    AREA_DIRS = cfg.get("area_dirs", [])
    TOPIC_DIRS = cfg.get("topic_dirs", [])            # frontmatter type: project makes a project
    ARCHIVE_DIRS = cfg.get("archive_dirs", [])        # notes are (finished) projects
    NOT_ENTITIES = cfg.get("not_entities", [])


def load_config(path):
    return json.load(open(path)) if os.path.exists(path) else {}


configure(load_config(CONFIG))

DATE_RE = re.compile(r"(20\d\d-\d\d-\d\d)")
CAPTURE_RE = re.compile(r"^\*\*(\d{1,2}:\d\d)\s+(.+?)\*\*")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
SECRET_RE = re.compile(r"[A-Za-z0-9_/+=-]{32,}")
CITATION_RE = re.compile(r"\s+et al\b|,?\s[A-Z]{1,2}[.,]|,\s[A-Z]\.")
ENTRY_RE = re.compile(r"<!--k:([0-9a-f]{10})-->")
# Per-bullet metadata on the agent-owned part of a card (specs/015): "- fact [source: ref, ref; added: date]".
META_RE = re.compile(r"\s\[([a-z_]+:\s*[^;\]]+(?:;\s*[a-z_]+:\s*[^;\]]+)*)\](?:\s*·.*)?$")
SINCE_RE = re.compile(r"\(since (20\d\d-\d\d-\d\d); (k:[0-9a-f]{10}(?:, k:[0-9a-f]{10})*)\)")   # consolidate.py's form
BULLET_RE = re.compile(r"^\s*[-*] (?:\[[ x]\] )?(?:([A-Za-z][A-Za-z /]{0,30}): ?)?(.*)$")
NO_SOURCE_NEEDED = ("Defining notes", "Links", "Summary as of", "Tags")     # housekeeping lines, not facts
SEP = r"[-_ ]+"


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("'\"")
    rest = text[end + 4:]
    return fm, rest[1:] if rest.startswith("\n") else rest


def clean(s, n=140):
    s = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"[*`>#]+|^\s*[-+] ", "", s)
    s = s.replace(" — ", ", ").replace("—", "-").replace("–", "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 3].rstrip() + "..."


def load_dictionary():
    try:
        with open("/usr/share/dict/words") as f:
            return {w.strip().lower() for w in f}
    except OSError:
        return set()


class Entity(object):
    def __init__(self, name, kind):
        self.name, self.kind, self.slug = name, kind, slugify(name)
        self.aliases = []       # (text, case_sensitive)
        self.notes = []         # vault-relative paths of notes that define it


def discover(dictionary):
    ents = {}

    def add(name, kind, note=None, aliases=None):
        e = ents.get(slugify(name))
        if e is None:
            e = ents[slugify(name)] = Entity(name, kind)
        if note and note not in e.notes:
            e.notes.append(note)
        for a in aliases or []:
            if a not in e.aliases:
                e.aliases.append(a)
        return e

    def auto_aliases(name, kind):
        words = re.split(SEP, name)
        if kind == "person":
            return [(" ".join(w[:1].upper() + w[1:] for w in words), True)]
        if len(words) == 1 and (name.lower() in dictionary or name.lower().rstrip("s") in dictionary):
            return []           # common word: wikilinks and registry aliases only
        return [(name, False)]

    def notes_in(rel):
        d = os.path.join(VAULT, rel)
        return sorted(f for f in os.listdir(d) if f.endswith(".md")
                      and not defines_nothing(rel + "/" + f)) if os.path.isdir(d) else []

    # People first, so a person never loses its kind to a same-named project.
    for rel in PERSON_DIRS:
        for f in notes_in(rel):
            path = rel + "/" + f
            if path in SKIP_FILES:
                continue
            fm, _ = frontmatter(read(os.path.join(VAULT, path)))
            name = fm.get("name") or f[:-3]
            name = re.sub(r"\s+\d+$", "", name)            # "Lucy 1" is a Lucy
            e = add(f[:-3], "person", path, auto_aliases(name, "person"))
            e.display = name
    firsts = {}
    for e in ents.values():
        if e.kind == "person" and " " in e.name:
            firsts.setdefault(e.name.split()[0].capitalize(), []).append(e)
    for first, es in firsts.items():
        if len(es) == 1 and slugify(first) not in ents:
            es[0].aliases.append((first, True))

    for rel in PROJECT_DIRS:
        projects = [f[:-3] for f in notes_in(rel)]
        for p in projects:
            parent = next((q for q in projects if p != q and p.lower().startswith(q.lower() + "-")), None)
            add(parent or p, "project", rel + "/" + p + ".md", auto_aliases(parent or p, "project"))
        pdir = os.path.join(VAULT, rel)
        for d in sorted(os.listdir(pdir)):
            if os.path.isdir(os.path.join(pdir, d)) and not defines_nothing(rel + "/" + d) \
                    and not d.startswith("."):
                e = add(d, "project", None, auto_aliases(d, "project"))
                for f in notes_in(rel + "/" + d)[:1]:
                    e.notes.append(rel + "/" + d + "/" + f)
    for d in ROOT_PROJECT_DIRS:
        e = add(d, "project", None, auto_aliases(d, "project"))
        for f in notes_in(d)[:1]:
            e.notes.append(d + "/" + f)
    for rel in AREA_DIRS:
        for f in notes_in(rel):
            add(f[:-3], "area", rel + "/" + f, auto_aliases(f[:-3], "area"))
    for rel in TOPIC_DIRS:
        for f in notes_in(rel):
            fm, _ = frontmatter(read(os.path.join(VAULT, rel, f)))
            kind = "project" if fm.get("type") == "project" else "topic"
            add(f[:-3], kind, rel + "/" + f, auto_aliases(f[:-3], kind))
    for rel in ARCHIVE_DIRS:
        for f in notes_in(rel):
            add(f[:-3], "project", rel + "/" + f, auto_aliases(f[:-3], "project"))

    # Registry last: its kind and aliases win, since a person wrote them on purpose.
    kind = None
    for line in read(REGISTRY).splitlines():
        m = re.match(r"^##\s+(\w+)", line)
        if m:
            kind = m.group(1).lower() if m.group(1).lower() in KINDS else None
            continue
        m = re.match(r"^-\s+([^:]+):\s*(.*)$", line)
        if kind and m:
            name = m.group(1).strip()
            aliases = [a.strip() for a in m.group(2).split(",") if a.strip()]
            e = ents.get(slugify(name)) or add(name, kind)
            e.kind = kind
            e.aliases = [(a, a != a.lower()) for a in aliases] or [(name, name != name.lower())]
    return ents


def defines_nothing(rel):
    return any(fnmatch.fnmatchcase(rel, g) for g in NOT_ENTITIES)


def tilde(path):
    return "~" + path[len(HOME):] if path.startswith(HOME + "/") else path


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def build_matchers(ents):
    """Two alternations (case-sensitive, case-insensitive) mapping matched text to entities."""
    table = {True: {}, False: {}}
    for e in ents.values():
        for text, cs in e.aliases:
            key = re.sub(SEP, " ", text if cs else text.lower())
            table[cs].setdefault(key, set()).add(e.slug)
    rx = {}
    for cs, keys in table.items():
        if keys:
            alts = sorted((SEP.join(re.escape(w) for w in k.split(" ")) for k in keys), key=len, reverse=True)
            rx[cs] = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(alts) + r")(?![A-Za-z0-9])",
                                0 if cs else re.IGNORECASE)
    notes = {}
    for e in ents.values():
        for n in e.notes:
            notes.setdefault(os.path.basename(n)[:-3].lower(), set()).add(e.slug)
            notes.setdefault(n[:-3].lower(), set()).add(e.slug)
    return table, rx, notes


def alias_hits(text, rx, table):
    """Entity slugs named in text. A capitalized name followed by initials or "et al" is a
    citation author ("Okafor Y,", "Okafor, Y.", "Okafor et al."), not a mention."""
    hits = set()
    for cs, r in rx.items():
        for m in r.finditer(text):
            if cs and CITATION_RE.match(text, m.end()):
                continue
            hits |= table[cs].get(re.sub(SEP, " ", m.group(1) if cs else m.group(1).lower()), set())
    return hits


def find(text, table, rx, notes):
    hits = alias_hits(text, rx, table)
    for m in WIKILINK_RE.finditer(text):
        t = m.group(1).strip().lower()
        hits |= notes.get(t, set()) | notes.get(os.path.basename(t), set())
    return hits


def raise_(err):
    raise err


def sources():
    """Yield (relpath, abs_path, in_vault). A walk error aborts the run: under a TCC denial
    os.walk would otherwise look empty and every entry would be marked source-gone."""
    for root, dirs, files in os.walk(VAULT, onerror=raise_):
        rel_root = os.path.relpath(root, VAULT)
        rel_root = "" if rel_root == "." else rel_root + "/"
        dirs[:] = [d for d in dirs if (rel_root + d) not in SKIP_DIRS and d not in SKIP_DIRS
                   and not (rel_root == "index-cards/")]
        for f in files:
            rel = rel_root + f
            if not f.endswith(".md") or rel in SKIP_FILES or rel.startswith("index-cards/_"):
                continue
            yield rel, os.path.join(root, f), True
    if os.path.isdir(AUDIT):
        for f in sorted(os.listdir(AUDIT)):
            if f.endswith(".md"):
                yield tilde(AUDIT) + "/" + f, os.path.join(AUDIT, f), False
    for pattern in EXTRA:
        for path in sorted(glob.glob(os.path.expanduser(pattern))):
            yield tilde(path), path, False


def session_digests():
    """Yield (ref, abs_path) for each session digest. Digests outlive their transcripts, so an
    entry stays valid after the transcript is deleted."""
    if not os.path.isdir(DIGESTS):
        return
    for root, dirs, files in os.walk(DIGESTS, onerror=raise_):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(".jsonl"):
                path = os.path.join(root, f)
                yield tilde(path), path


def local_time(ts):
    """'2026-10-03T21:05:09.123Z' (UTC) as local 'YYYY-MM-DD HH:MM', or None."""
    try:
        t = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return t.astimezone().strftime("%Y-%m-%d %H:%M")


def note_date(rel, fm, path):
    m = DATE_RE.search(os.path.basename(rel))
    if m:
        return m.group(1)
    for k in ("date", "modified", "created"):
        m = DATE_RE.search(fm.get(k, ""))
        if m:
            return m.group(1)
    try:
        return date.fromtimestamp(os.path.getmtime(path)).isoformat()
    except OSError:
        return date.today().isoformat()


def blocks(body):
    """Split into (heading, time, lines). The text before the first header has heading None."""
    out, cur = [], [None, None, []]
    fence = False
    for line in body.splitlines():
        if line.startswith("```"):
            fence = not fence
        c = None if fence else CAPTURE_RE.match(line)
        h = None if fence or c else HEADING_RE.match(line)
        if c or h:
            out.append(cur)
            cur = [c.group(2) if c else h.group(1), c.group(1) if c else None, []]
        cur[2].append(line)
    out.append(cur)
    return [b for b in out if b[2]]


def snippet(lines, rx, table, slug):
    for line in lines:
        if line.strip() and not SECRET_RE.search(line) and slug in alias_hits(line, rx, table):
            return clean(line)
    return ""


def link(rel, in_vault):
    if not in_vault:
        return "`" + rel + "`"
    return "[[" + rel[:-3] + "|" + os.path.basename(rel)[:-3] + "]]"


def key(slug, rel, block):
    return hashlib.sha1((slug + "\0" + rel + "\0" + (block or "")).encode()).hexdigest()[:10]


def collect(ents, table, rx, notes):
    """Return {slug: {key: (sort_key, line)}} and the set of source paths seen."""
    out = {s: {} for s in ents}
    seen = set()
    for rel, path, in_vault in sources():
        text = read(path)
        if not text:
            continue
        seen.add(rel)
        fm, body = frontmatter(text)
        fdate = note_date(rel, fm, path)
        title = fm.get("title") or next((b[0] for b in blocks(body) if b[0]), None) or os.path.basename(rel)[:-3]
        title = clean(title, 90)
        per_block = rel.startswith(BLOCK_DIRS) or rel in BLOCK_FILES
        if per_block:
            for heading, hhmm, lines in blocks(body):
                chunk = "\n".join(lines)
                if "(synced via audit-to-vault)" in chunk:
                    continue        # ~/audit is indexed directly; skip its daily-note echo
                hits = find(chunk, table, rx, notes)
                if not hits:
                    continue
                m = DATE_RE.search(heading or "")
                d = m.group(1) if (m and not rel.startswith(BLOCK_DIRS)) else fdate
                label = clean(heading or title, 90)
                for slug in hits:
                    sn = snippet(lines[1:], rx, table, slug) if heading else snippet(lines, rx, table, slug)
                    text_ = label if not sn or slug in alias_hits(label, rx, table) else label + ": " + sn
                    put(out, slug, rel, heading or "", d, hhmm, in_vault, text_)
        else:
            hits = find(body if in_vault else text, table, rx, notes)
            for e in ents.values():
                if rel in e.notes:
                    hits.add(e.slug)
            for slug in hits:
                own = rel in ents[slug].notes
                sn = "" if own else snippet(body.splitlines(), rx, table, slug)
                text_ = title + (" (defining note)" if own else "") + (": " + sn if sn and slug not in alias_hits(title, rx, table) else "")
                put(out, slug, rel, "", fdate, None, in_vault, text_)
    collect_sessions(ents, table, rx, notes, out, seen)
    return out, seen


def collect_sessions(ents, table, rx, notes, out, seen):
    """One entry per (project, session) when the session's title, working directory or a user
    prompt names the project. Assistant text is not matched: it names projects in passing.
    A subagent's transcript counts toward its parent session (one entry, keyed on the parent);
    the entry links the digest whose prompt matched."""
    projects = {s for s, e in ents.items() if e.kind == "project"}
    titles = {}
    for ref, path in session_digests():         # a parent digest comes before its subagents/
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        seen.add(ref)
        try:
            head = json.loads(lines[0])
            recs = [(head, head.get("title", "") + "\n" + head.get("cwd", ""))] + [
                (r, r.get("text", "")) for r in (json.loads(l) for l in lines[1:] if '"kind": "prompt"' in l)
                if r.get("kind") == "prompt"]
        except (IndexError, ValueError):
            continue
        parent = path.split("/subagents/")[0] + ".jsonl" if "/subagents/" in path else path
        if parent == path:          # untitled: the first prompt line stands in
            first = next((l for _, t in recs[1:] for l in t.splitlines() if l.strip() and not SECRET_RE.search(l)), "")
            titles[path] = clean(head.get("title") or first or "untitled session", 90)
        title = titles.get(parent, "untitled session") + (" (subagent)" if parent != path else "")
        for r, text in recs:
            for slug in find(text, table, rx, notes) & projects:
                if key(slug, tilde(parent), "") in out[slug]:
                    continue
                when = local_time(r.get("ts", "")) or local_time(head.get("ts", "")) \
                    or date.fromtimestamp(os.path.getmtime(path)).isoformat()
                sn = "" if r is head else snippet(text.splitlines(), rx, table, slug)
                text_ = title + (": " + sn if sn and slug not in alias_hits(title, rx, table) else "")
                put(out, slug, ref, "", when[:10], when[11:], False, text_, span=r.get("src"),
                    group=tilde(parent))


def put(out, slug, rel, block, d, hhmm, in_vault, text, span=None, group=None):
    k = key(slug, group or rel, block)
    when = d + (" " + hhmm if hhmm else "")
    line = "- " + when + " · " + link(rel, in_vault) + " · " + clean(text, 220) \
        + (" · from `" + span + "`" if span else "") + " <!--k:" + k + "-->"
    out[slug][k] = (when, rel, line)


def existing_entries(card_text):
    """Entries already on a card: {key: (sort_key, source_rel, line)}."""
    out = {}
    if START not in card_text:
        return out
    for line in card_text.split(START, 1)[1].split(END, 1)[0].splitlines():
        m = ENTRY_RE.search(line)
        if not m:
            continue
        when = line[2:].split(" · ", 1)[0]
        src = re.search(r"\[\[([^|\]]+)\|", line)
        src = src.group(1) + ".md" if src else (re.search(r"`([~/][^`]+)`", line) or [None, None])[1]
        out[m.group(1)] = (when, src, line)
    return out


def bullet_meta(line):
    """{"source": [refs], "added": "YYYY-MM-DD", ...} for a bullet ending in [source: ...; added: ...],
    or one consolidate.py wrote as (since DATE; k:...). None when either field is missing."""
    m = META_RE.search(line)
    if m:
        meta = dict((k.strip(), v.strip()) for k, _, v in (p.partition(":") for p in m.group(1).split(";")))
        if not meta.get("source") or not re.fullmatch(r"20\d\d-\d\d-\d\d", meta.get("added", "")):
            return None
        meta["source"] = [s.strip() for s in meta["source"].split(",") if s.strip()]
        return meta
    m = SINCE_RE.search(line)
    return {"source": m.group(2).split(", "), "added": m.group(1)} if m else None


def owned(card_text):
    """The agent-owned text of a card: everything outside the frontmatter and the Timeline markers."""
    _, body = frontmatter(card_text)
    if START in body:
        head, rest = body.split(START, 1)
        body = head + (rest.split(END, 1)[1] if END in rest else "")
    return body


def fact_bullets(card_text):
    """(line number, line) of every fact-stating bullet in the agent-owned text: outside the
    frontmatter and the markers, and not in a history list (### Superseded, ### Archived ...)."""
    lines, out, inside, history = card_text.split("\n"), [], False, False
    start = next((j for j in range(1, len(lines)) if lines[j] == "---"), -1) + 1 if lines[:1] == ["---"] else 0
    for j in range(start, len(lines)):
        line = lines[j]
        if line.startswith((START, END)):
            inside = line.startswith(START)
            continue
        if line.startswith("## "):
            history = False
        elif line.startswith(("### Superseded", "### Archived")):
            history = True
        m = None if inside or history else BULLET_RE.match(line)
        if m and m.group(2).strip() and (m.group(1) or "") not in NO_SOURCE_NEEDED:
            out.append((j, line))
    return out


def unsourced(card_text):
    """Fact-stating bullets outside the markers that carry no [source: ...; added: YYYY-MM-DD]."""
    return [line.strip() for _, line in fact_bullets(card_text) if bullet_meta(line) is None]


def seed_summary(e):
    """Written once when a card is created; agents own this section afterwards."""
    one = ""
    for n in e.notes:
        fm, body = frontmatter(read(os.path.join(VAULT, n)))
        one = fm.get("description") or fm.get("context") or ""
        if not one:
            for line in body.splitlines():
                s = line.strip()
                if s and not s.startswith(("#", "|", "---", "```", "!", "<")) and len(clean(s)) > 20:
                    one = s
                    break
        if one:
            break               # n is the note that supplied the line
    notes = ", ".join("[[" + n[:-3] + "|" + os.path.basename(n)[:-3] + "]]" for n in e.notes) or "none yet"
    return ("\n## Summary\n\n"
            "- One line: " + (clean(one, 240) + " [source: " + n + "; added: " + date.today().isoformat() + "]"
                              if one else "") + "\n"
            "- Defining notes: " + notes + "\n"
            "- Decisions/gates: \n- Open: \n- Links: \n"
            "- Summary as of: " + date.today().isoformat() + " (seeded by the indexer; rewrite freely, "
            "the indexer never touches this section)\n\n")


def render(e, entries, old_text):
    aliases = sorted({a for a, _ in e.aliases})
    lines = sorted(entries.values(), key=lambda v: (v[0], v[2]), reverse=True)
    last = lines[0][0][:10] if lines else ""
    fm = ("---\ntype: index-card\nkind: " + e.kind + "\nentity: \"" + getattr(e, "display", e.name) + "\"\n"
          "aliases: [" + ", ".join('"' + a.replace('"', "") + '"' for a in aliases) + "]\n"
          "entries: " + str(len(lines)) + "\nlast_seen: " + (last or "never") + "\n"
          "updated: {UPDATED}\n---\n")
    if old_text and START in old_text:
        _, rest = frontmatter(old_text)
        head, tail = rest.split(START, 1)
        tail = tail.split(END, 1)[1] if END in tail else ""
    else:
        head = "\n# " + getattr(e, "display", e.name) + "\n" + seed_summary(e) + "## Timeline\n\n" \
               "Newest first. Maintained by the indexer; edits between " \
               "the markers are overwritten.\n\n"
        tail = "\n"
    body = START + "\n" + "\n".join(v[2] for v in lines) + ("\n" if lines else "") + END
    return fm + head + body + tail


def write_if_changed(path, new):
    old = read(path)
    old_upd = re.search(r"^updated: (.*)$", old, re.M)
    probe = new.replace("{UPDATED}", old_upd.group(1) if old_upd else "")
    if probe == old:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), "." + os.path.basename(path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new.replace("{UPDATED}", datetime.now().strftime("%Y-%m-%d %H:%M")))
    os.replace(tmp, path)
    return True


def card_path(e):
    return os.path.join(CARDS, e.kind, e.slug + ".md")


def relocate(e):
    """A card whose kind changed moves with its content instead of being duplicated."""
    want = card_path(e)
    if os.path.exists(want):
        return
    for k in KINDS:
        p = os.path.join(CARDS, k, e.slug + ".md")
        if p != want and os.path.exists(p):
            os.makedirs(os.path.dirname(want), exist_ok=True)
            os.replace(p, want)
            return


def catalog(ents, counts):
    out = ["---\ntype: index-card-catalog\n---\n", "# Index cards",
           "",
           "One card per person, project, harness, area and topic, each with a dated Timeline of every "
           "note, report and (on project cards) session that mentions it. Rebuilt by the indexer. "
           "To add a thing that has no note, or fix a noisy match, edit "
           "[[index-cards/_registry|_registry]]. A bullet you write on a card ends with "
           "`[source: <ref>; added: YYYY-MM-DD]` (a `k:` Timeline key, a note path or a URL); "
           "`indexer.py --unsourced` lists the ones that do not."
           + (" " + CATALOG_NOTE if CATALOG_NOTE else ""), ""]
    for k in KINDS:
        es = sorted((e for e in ents.values() if e.kind == k and e.slug in counts),
                    key=lambda e: (-counts[e.slug][0], e.slug))
        if not es:
            continue
        out.append("## " + k + " (" + str(len(es)) + ")\n")
        for e in es:
            n, last = counts[e.slug]
            out.append("- [[index-cards/" + k + "/" + e.slug + "|" + getattr(e, "display", e.name) + "]] · "
                       + str(n) + " entries · last " + last)
        out.append("")
    return "\n".join(out)


def run():
    t0 = time.time()
    ents = discover(load_dictionary())
    table, rx, notes = build_matchers(ents)
    found, seen = collect(ents, table, rx, notes)
    changed, counts, kept, missing = 0, {}, 0, 0
    for slug, e in ents.items():
        relocate(e)
        path = card_path(e)
        old_text = read(path)
        merged = dict(found[slug])
        for k, (when, src, line) in existing_entries(old_text).items():
            if k in merged or src is None:
                continue
            gone = src not in seen and not os.path.exists(os.path.join(VAULT, src)) \
                and not os.path.exists(os.path.expanduser(src))
            if gone:            # source moved or deleted: keep the history, say so
                kept += 1
                merged[k] = (when, src, line if "(source gone)" in line
                             else line.replace(" <!--k:", " (source gone) <!--k:"))
        if not merged and not old_text:
            continue            # registry entity with no mention yet: no empty card
        last = max(v[0] for v in merged.values())[:10] if merged else "never"
        counts[slug] = (len(merged), last)
        new = render(e, merged, old_text)
        missing += len(unsourced(new))
        if write_if_changed(path, new):
            changed += 1
    cat_changed = write_if_changed(CATALOG, catalog(ents, counts))
    print("%s entities=%d cards=%d changed=%d kept_gone=%d sources=%d unsourced=%d catalog_changed=%s %.1fs" % (
        datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), len(ents), len(counts), changed, kept,
        len(seen), missing, cat_changed, time.time() - t0))
    return changed


def newest_input():
    """Latest mtime over every input file and its folder (folders catch deletions). Never
    stats index-cards/ itself or a card, so the indexer's own writes cannot re-trigger it."""
    newest, dirs = os.path.getmtime(REGISTRY) if os.path.exists(REGISTRY) else 0, set()
    for path in [p for _, p, _ in sources()] + [p for _, p in session_digests()]:
        newest = max(newest, os.path.getmtime(path))
        dirs.add(os.path.dirname(path))
    dirs.discard(CARDS)
    return max([newest] + [os.path.getmtime(d) for d in dirs])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--if-changed", action="store_true",
                    help="sweep only if an input changed since the last sweep (cron polls this)")
    ap.add_argument("--unsourced", action="store_true",
                    help="list agent-written bullets with no [source: ...; added: ...] and sweep nothing")
    args = ap.parse_args()
    if not os.path.isdir(VAULT):
        sys.exit("vault not found: " + VAULT)
    if args.unsourced:
        for p in sorted(glob.glob(os.path.join(CARDS, "*", "*.md"))):
            for line in unsourced(read(p)):
                print(os.path.relpath(p, CARDS) + ": " + line)
        return
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    with open(LOCK, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("another run holds the lock; skipping")
            return
        started = time.time()
        if args.if_changed:
            try:
                last = float(read(STAMP) or 0)
            except ValueError:
                last = 0
            if newest_input() <= last:
                return
        run()
        with open(STAMP, "w") as f:
            f.write(repr(started))


if __name__ == "__main__":
    main()
