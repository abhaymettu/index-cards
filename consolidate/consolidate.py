#!/usr/bin/python3
"""Consolidation pass over index cards: a headless model writes each card's ## Summary, code checks it.

  consolidate.py run CARDS --vault VAULT --state STATE [--lock LOCK] [--jobs 6] [--model sonnet]
                           [--only GLOB] [--dry-run] [--commit]
  consolidate.py lint CARDS --state STATE --out REPORT [--stale-days 30] [--llm] [--model sonnet]

`run` picks the cards whose Timeline changed since the state file's last pass and makes one isolated
`claude -p` call per card. The model sees the card's facts as F0..Fm and its Timeline as integer IDs
with the sources cloned to src/<id>, and returns facts that cite those IDs. Code rejects any fact
without a valid, supported citation, maps IDs to the entries' stable keys, applies supersession
from the cited dates, keeps every fact the model left out, and archives instead of deleting.
Only the ## Summary section is rewritten. `lint` reports and edits nothing. Spec:
specs/005-consolidation/spec.md. Stdlib only.
"""
import argparse, concurrent.futures as cf, difflib, fcntl, fnmatch, glob, hashlib, json, os, re, \
    shutil, subprocess, sys, tempfile
from datetime import date, timedelta

START, END = "<!-- index:start -->", "<!-- index:end -->"
ENTRY_RE = re.compile(r"<!--k:([0-9a-f]{10})-->")
KINDS = ["Overview", "Decision", "State", "Open", "Fact"]
FACT_RE = re.compile(r"^- (" + "|".join(KINDS) + r"): (.+) \(since (\d{4}-\d{2}-\d{2}); "
                     r"(k:[0-9a-f]{10}(?:, k:[0-9a-f]{10})*)\)$")
MARKER = ("<!-- consolidated by consolidate.py: each bullet cites Timeline keys (k:...); "
          "a bullet without one is archived on the next pass -->")
SUPERSEDED, ARCHIVED = "### Superseded", "### Archived as written"
STOP = set("this that with from have been were will what when which their there about into than then "
           "they them also only more most some such each other over after before same very just".split())
CLAUDE = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")

SCHEMA = {"type": "object", "required": ["facts"], "properties": {"facts": {"type": "array", "items": {
    "type": "object", "required": ["kind", "text", "cite"], "properties": {
        "kind": {"enum": KINDS}, "text": {"type": "string"},
        "cite": {"type": "array", "items": {"type": "integer"}},
        "replaces": {"type": "array", "items": {"type": "string"}}}}}}}

PROMPT = """You write the Summary of one index card in a personal knowledge vault. The card is
about the {kind} "{entity}". Its Timeline below lists every dated note, report and session that
mentions it, newest first, under integer IDs. The vault belongs to one person; "I" in sources is him.

Follow these steps in order.
1. Read. Start from the current facts and the Timeline. If a Timeline line is too short to show what
   happened, open the source file it names (under src/) with Read or Grep, and open nothing more
   than you need.
2. Select. Keep what a newcomer would need a month from now: what the thing is, decisions with their
   dates, where it stands, what is still open, and corrections. Leave out passing mentions, chatter
   and one-off details. If sources conflict, trust the most recent.
3. Propose changes. Return only facts that differ from what is stored: new facts, and replacements
   for stored facts the Timeline shows are out of date or wrong. A replacement or merge is a new fact
   whose "replaces" lists the old IDs (e.g. ["F2"]). Stored facts you do not mention stay as they
   are, and nothing can be deleted. Never repeat a stored fact unchanged.
4. Cite. Each fact lists in "cite" the Timeline IDs that support it and no others; code drops any
   fact without a valid citation. Use absolute dates. One sentence per fact, under 40 words, no em
   dashes, at most 10 facts. If nothing needs to change, return an empty list.

Kinds: Overview (what this is; at most one), Decision, State, Open (unresolved item or next step),
Fact.

Current facts:
{facts}

Timeline (ID, date, line, source):
{timeline}
"""

LINT_PROMPT = """Below are the current facts from every index card in a personal knowledge vault, one
per line as "<card>#F<n> <kind>: <text> (since <date>)". List pairs of facts from different cards
that contradict each other (both cannot be true at the same time). Ignore facts that merely differ
in date or detail. Use the exact "<card>#F<n>" IDs. Return an empty list if there are none.

{facts}
"""
LINT_SCHEMA = {"type": "object", "required": ["pairs"], "properties": {"pairs": {"type": "array", "items": {
    "type": "object", "required": ["a", "b", "why"], "properties": {
        "a": {"type": "string"}, "b": {"type": "string"}, "why": {"type": "string"}}}}}}


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, IsADirectoryError):
        return ""


def timeline(text):
    return text.split(START, 1)[1].split(END, 1)[0] if START in text and END in text else None


def entries(text, vault):
    """Timeline entries in card order: [(key, when, source path or None, line)]."""
    out = []
    for line in timeline(text).splitlines():
        m = ENTRY_RE.search(line)
        if not m:
            continue
        wiki = re.search(r"\[\[([^|\]]+)\|", line)
        tick = re.search(r"`([~/][^`]+)`", line)
        src = os.path.join(vault, wiki.group(1) + ".md") if wiki else \
            os.path.expanduser(tick.group(1)) if tick else None
        out.append((m.group(1), line[2:].split(" · ", 1)[0], src, line))
    return out


def summary_span(text):
    """(start, end) of the ## Summary section body, ending at the next ## heading."""
    m = re.search(r"^## Summary\n", text, re.M)
    if not m:
        return None
    n = re.search(r"^## ", text[m.end():], re.M)
    return m.end(), m.end() + (n.start() if n else len(text) - m.end())


def parse_summary(body):
    """(facts, superseded lines, archived block, uncited active lines)."""
    if MARKER not in body:
        return [], [], "", [body.strip()] if body.strip() else []
    active, _, rest = body.partition(SUPERSEDED) if SUPERSEDED in body else body.partition(ARCHIVED)
    sup, _, arch = rest.partition(ARCHIVED) if SUPERSEDED in body else ("", "", rest)
    facts, loose = [], []
    for line in active.replace(MARKER, "").splitlines():
        m = FACT_RE.match(line.strip())
        if m:
            facts.append({"kind": m.group(1), "text": m.group(2), "since": m.group(3),
                          "keys": [k[2:] for k in m.group(4).split(", ")]})
        elif line.strip():
            loose.append(line.strip())
    return facts, [l for l in sup.splitlines() if l.strip()], arch.strip("\n"), loose


def fact_line(f):
    return "- %s: %s (since %s; %s)" % (f["kind"], f["text"], f["since"], ", ".join("k:" + k for k in f["keys"]))


def render_summary(facts, superseded, archived):
    order = {k: i for i, k in enumerate(KINDS)}
    out = "\n" + MARKER + "\n" + "".join(fact_line(f) + "\n" for f in sorted(facts, key=lambda f: order[f["kind"]]))
    if superseded:
        out += "\n" + SUPERSEDED + "\n\n" + "".join(l + "\n" for l in superseded)
    if archived:
        out += "\n" + ARCHIVED + "\n\n" + archived + "\n"
    return out + "\n"


def words(s):
    return {w for w in re.findall(r"[a-z0-9]{4,}", s.lower()) if w not in STOP}


def call(prompt, schema, cwd, model):
    """One isolated headless call; returns structured_output or raises."""
    cmd = [CLAUDE, "-p", "--safe-mode", "--restricted", "--strict-mcp-config", "--tools", "Read,Grep,Glob",
           "--no-session-persistence", "--model", model, "--permission-mode", "dontAsk",
           "--output-format", "json", "--json-schema", json.dumps(schema)]
    p = subprocess.run(cmd, cwd=cwd, input=prompt, capture_output=True, text=True, timeout=900)
    out = json.loads(p.stdout) if p.stdout.strip() else {}
    if out.get("is_error") or "structured_output" not in out:
        raise RuntimeError((out.get("result") or p.stderr or "no output")[-300:])
    return out["structured_output"], out.get("total_cost_usd", 0)


def ask(card_rel, text, ents, facts, model, base):
    """Build the scratch dir, call the model, return its raw facts."""
    d = tempfile.mkdtemp(prefix="card-", dir=base)
    os.mkdir(os.path.join(d, "src"))
    seen, rows = {}, []
    for i, (k, when, src, line) in enumerate(ents):
        name = seen.get(src)
        if name is None and src and os.path.isfile(src):
            name = "src/%d%s" % (i, os.path.splitext(src)[1])
            if subprocess.run(["cp", "-c", src, os.path.join(d, name)]).returncode:
                name = None             # no clone, so do not point the model at a missing file
            else:
                seen[src] = name
        body = ENTRY_RE.sub("", line[2:]).strip()
        rows.append("[%d] %s%s" % (i, body, " (" + name + ")" if name else ""))
    id_of = {k: i for i, (k, _, _, _) in enumerate(ents)}
    shown = ["F%d %s: %s (since %s; cites %s)" % (j, f["kind"], f["text"], f["since"],
             ", ".join(str(id_of[k]) for k in f["keys"] if k in id_of)) for j, f in enumerate(facts)]
    kind, entity = card_rel.split("/")[0], re.search(r"^entity: \"(.*)\"$", text, re.M)
    prompt = PROMPT.format(kind=kind, entity=entity.group(1) if entity else card_rel,
                           facts="\n".join(shown) or "(none yet)", timeline="\n".join(rows))
    try:
        return call(prompt, SCHEMA, d, model)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def consolidate(text, ents, returned, today):
    """Apply the provenance check and supersession to one card. Returns (new card text, stats)."""
    a, b = summary_span(text)
    facts, superseded, archived, loose = parse_summary(text[a:b])
    if loose:
        archived = (archived + "\n\n" if archived else "") + "Archived %s (no Timeline key):\n\n%s" % (
            today, "\n".join(loose))
    when = {k: w for k, w, _, _ in ents}
    stats = {"returned": len(returned), "accepted": 0, "no_cite": 0, "bad_cite": 0, "unsupported": 0,
             "bad_replaces": 0, "superseded": 0, "orphaned": 0, "duplicate": 0}
    live = []
    for f in facts:
        if any(k in when for k in f["keys"]):
            live.append(f)
        else:
            superseded.append(fact_line(f) + " · retired %s: cited entries gone" % today)
            stats["orphaned"] += 1
    current, support = list(live), {}
    for r in returned:
        cite = sorted(set(r.get("cite") or []))
        if not cite:
            stats["no_cite"] += 1
            continue
        if any(not 0 <= i < len(ents) for i in cite):
            stats["bad_cite"] += 1
            continue
        txt = re.sub(r"\s+", " ", r["text"].replace("—", "-")).strip()
        for i in cite:
            if i not in support:
                support[i] = words(ents[i][3]) | words(read(ents[i][2])[:200000] if ents[i][2] else "")
        if not words(txt) & set().union(*(support[i] for i in cite)):
            stats["unsupported"] += 1
            continue
        new = {"kind": r["kind"], "text": txt, "keys": [ents[i][0] for i in cite],
               "since": min(ents[i][1] for i in cite)[:10]}
        newest = max(ents[i][1] for i in cite)
        if any(f["text"].lower() == txt.lower() for f in current):
            stats["duplicate"] += 1
            continue
        refs = list(r.get("replaces") or [])
        if new["kind"] == "Overview":   # at most one: a new Overview replaces the current one
            refs += ["F%d" % j for j, f in enumerate(live) if f["kind"] == "Overview" and f in current
                     and "F%d" % j not in refs]
        olds, loser = [], None          # check every ref first, then apply in one step
        for ref in refs:
            j = int(ref[1:]) if re.fullmatch(r"F\d+", ref) else -1
            if not 0 <= j < len(live) or live[j] not in current or live[j] in olds:
                stats["bad_replaces"] += 1
                continue
            old_key = max((k for k in live[j]["keys"] if k in when), key=when.get)
            if newest < when[old_key]:  # dates decide, not the model: the "update" is older
                loser = (live[j], old_key)
                break
            olds.append(live[j])
        if loser:
            superseded.append(fact_line(new) + " · superseded %s by %s (k:%s)" % (
                when[loser[1]][:10], loser[0]["text"], loser[1]))
            continue
        for old in olds:
            current.remove(old)
            superseded.append(fact_line(old) + " · superseded %s by %s (k:%s)" % (
                newest[:10], txt, max(new["keys"], key=when.get)))
            stats["superseded"] += 1
        current.append(new)
        stats["accepted"] += 1
    return text[:a] + render_summary(current, superseded, archived) + text[b:], stats


def cards(root, only=None):
    out = []
    for p in sorted(glob.glob(os.path.join(root, "*", "*.md"))):
        rel = os.path.relpath(p, root)
        if (only is None or fnmatch.fnmatch(rel, only)) and timeline(read(p)) is not None:
            out.append(rel)
    return out


def sha(text):
    return hashlib.sha256(timeline(text).encode()).hexdigest()


def write_card(path, text, lock):
    """Splice under the indexer's lock: re-read, swap only ## Summary, atomic replace."""
    with open(lock or os.devnull, "a") as lk:
        if lock:
            fcntl.flock(lk, fcntl.LOCK_EX)
        cur = read(path)
        a, b = summary_span(text)
        ca, cb = summary_span(cur)
        new = cur[:ca] + text[a:b] + cur[cb:]
        tmp = os.path.join(os.path.dirname(path), "." + os.path.basename(path) + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(new)
        os.replace(tmp, path)


def run(args, model_call=ask):
    state = json.loads(read(args.state) or '{"cards": {}}')
    todo = [rel for rel in cards(args.cards, args.only)
            if state["cards"].get(rel) != sha(read(os.path.join(args.cards, rel)))]
    totals, written = {}, []
    with tempfile.TemporaryDirectory(prefix="consolidate-") as base, cf.ThreadPoolExecutor(args.jobs) as ex:
        futs = {}
        for rel in todo:
            text = read(os.path.join(args.cards, rel))
            ents = entries(text, args.vault)
            span, keys = summary_span(text), {e[0] for e in ents}
            if span is None:
                print(json.dumps({"card": rel, "error": "no ## Summary"}))
                totals["errors"] = totals.get("errors", 0) + 1
                continue
            facts = [f for f in parse_summary(text[slice(*span)])[0] if any(k in keys for k in f["keys"])]
            futs[ex.submit(model_call, rel, text, ents, facts, args.model, base)] = (rel, text, ents)
        for fut in cf.as_completed(futs):
            rel, text, ents = futs[fut]
            try:
                out, cost = fut.result()
            except Exception as e:
                print(json.dumps({"card": rel, "error": str(e)[-300:]}), flush=True)
                totals["errors"] = totals.get("errors", 0) + 1
                continue
            new, stats = consolidate(text, ents, out.get("facts", []), date.today().isoformat())
            stats["cost_usd"] = round(cost, 4)
            for k, v in stats.items():
                totals[k] = round(totals.get(k, 0) + v, 4)
            path = os.path.join(args.cards, rel)
            if args.dry_run:
                a, b = summary_span(text)
                na, nb = summary_span(new)
                sys.stdout.writelines(difflib.unified_diff(text[a:b].splitlines(True), new[na:nb].splitlines(True),
                                                           rel, rel + " (proposed)"))
            elif new != text:
                write_card(path, new, args.lock)
                written.append(path)
            if not args.dry_run:
                state["cards"][rel] = sha(text)
            print(json.dumps(dict(card=rel, **stats)), flush=True)
    if not args.dry_run:
        tmp = args.state + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=1, sort_keys=True)
        os.replace(tmp, args.state)
    if args.commit and written:
        top = subprocess.run(["git", "-C", args.cards, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "-C", top, "add", "--"] + written, check=True)
        subprocess.run(["git", "-C", top, "commit", "-q", "-m", "consolidate: %d cards, %s" % (
            len(written), ", ".join("%s %s" % (k, v) for k, v in sorted(totals.items())))] + ["--"] + written,
            check=True)
    print(json.dumps(dict(cards=len(todo), written=len(written), **totals)))
    return totals


def lint(args, model_call=call):
    state = json.loads(read(args.state) or '{"cards": {}}')
    cutoff = (date.today() - timedelta(days=args.stale_days)).isoformat()
    uncited, stale, orphans, pending, ids = [], [], [], [], {}
    for rel in cards(args.cards):
        text = read(os.path.join(args.cards, rel))
        ents = entries(text, "")
        when = {k: w for k, w, _, _ in ents}
        if not ents or all("(source gone)" in e[3] for e in ents):
            orphans.append(rel)
        if state["cards"].get(rel) != sha(text):
            pending.append(rel)
        span = summary_span(text)
        body = text[span[0]:span[1]] if span else ""
        if MARKER not in body:
            continue
        facts, _, _, loose = parse_summary(body)
        uncited += ["%s: %s" % (rel, l) for l in loose]
        for j, f in enumerate(facts):
            ids["%s#F%d" % (rel, j)] = f
            known = [when[k] for k in f["keys"] if k in when]
            if not known:
                uncited.append("%s: %s (cited keys gone)" % (rel, fact_line(f)))
            elif f["kind"] == "Open" and max(known)[:10] < cutoff:
                stale.append("%s: %s" % (rel, fact_line(f)))
    pairs, dropped = [], 0
    if args.llm and ids:
        listing = "\n".join("%s %s: %s (since %s)" % (i, f["kind"], f["text"], f["since"]) for i, f in ids.items())
        with tempfile.TemporaryDirectory(prefix="lint-") as d:
            out, _ = model_call(LINT_PROMPT.format(facts=listing), LINT_SCHEMA, d, args.model)
        for p in out.get("pairs", []):
            if p["a"] in ids and p["b"] in ids and p["a"].split("#")[0] != p["b"].split("#")[0]:
                pairs.append(p)
            else:
                dropped += 1
    sec = lambda title, rows: "## %s (%d)\n\n%s\n" % (title, len(rows), "\n".join("- " + r for r in rows) or "none")
    report = "# Index card lint, %s\n\nReport only; no card was edited.\n\n" % date.today().isoformat() \
        + sec("Uncited active bullets", uncited) + "\n" \
        + sec("Open items with no citation newer than %s" % cutoff, stale) + "\n" \
        + sec("Orphans (no entries, or every source gone)", orphans) + "\n" \
        + sec("Pending a consolidation pass", pending) + "\n" \
        + (sec("Contradictions across cards" + (" (%d dropped: unknown IDs)" % dropped if dropped else ""),
               ["%s vs %s: %s" % (p["a"], p["b"], p["why"]) for p in pairs]) if args.llm else "")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print("lint: uncited=%d stale_open=%d orphans=%d pending=%d contradictions=%d -> %s" % (
        len(uncited), len(stale), len(orphans), len(pending), len(pairs), args.out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("cards")
    r.add_argument("--vault", required=True, help="root that [[wikilinks]] in entries resolve against")
    r.add_argument("--state", required=True)
    r.add_argument("--lock", help="the indexer's lock file; held only while a card is written")
    r.add_argument("--jobs", type=int, default=6)
    r.add_argument("--model", default="sonnet")
    r.add_argument("--only", help="glob over card paths, e.g. 'project/*'")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--commit", action="store_true")
    l = sub.add_parser("lint")
    l.add_argument("cards")
    l.add_argument("--state", required=True)
    l.add_argument("--out", required=True)
    l.add_argument("--stale-days", type=int, default=30)
    l.add_argument("--llm", action="store_true")
    l.add_argument("--model", default="sonnet")
    args = ap.parse_args()
    (run if args.cmd == "run" else lint)(args)


if __name__ == "__main__":
    main()
