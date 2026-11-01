#!/usr/bin/env python3
"""nightly: the measured self-betterment loop over index cards (specs/016).

  nightly.py [--config CFG] [--apply] [--llm] [--model M]

Deterministic passes over the agent-owned part of every card (the bullets outside the Timeline
markers): unsourced bullets, exact and near duplicates, contradiction candidates between bullets
with the same label and different numbers, stale sourced bullets whose source is gone, broken
wikilinks. They produce a PROPOSED change set: a unified diff over the cards (applies with
`patch -p1` from the cards folder) and a report. No card is edited unless --apply is given, and
then only through the gate: the proposals go into a scratch copy, memeval scores the configured
question set before and after (ripgrep, no model), the indexer sweeps the scratch copy, and a
change set that lowers the score or does not survive the sweep is rejected. Every run appends one
line to a JSONL ledger. --llm adds one model call over all sourced bullets for contradictions code
cannot see (consolidate.py's lint prompt); it is off by default and the input size and price are
printed before the call. Stdlib only, /usr/bin/python3 (3.9).

Config: JSON at --config or $NIGHTLY_CONFIG (default ~/.config/index-cards/nightly.json):
  indexer_config   the indexer's instance config (vault, cards, lock)         required
  questions        memeval question set (JSONL)                                required for --apply
  corpora          memeval corpora config (JSON); its "vault" corpus holds index-cards/   required for --apply
  split, k         memeval split (default "frozen") and cutoff (default 5)
  out              folder for the patch, the report and ledger.jsonl (default ~/.cache/index-cards/nightly)
  stale_days       default 90
  log              base path of the cron log and err files named in the report's schedule line
  price_usd_per_mtok   input price used for the --llm estimate; unset prints tokens only
"""
import argparse
import difflib
import fcntl
import glob
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", d) for d in ("indexer", "eval", "consolidate")]
import consolidate  # noqa: E402
import indexer  # noqa: E402
import memeval  # noqa: E402

PASSES = ("unsourced", "exact_dup", "near_dup", "contradiction", "stale", "broken_link")
NEAR, CONTRA = 0.8, 0.5                 # Jaccard thresholds over content words
NUM_RE = re.compile(r"\d[\d.,:/-]*\d|\d")
CRON = ("40 3 * * * PATH=/opt/homebrew/bin:/usr/bin:/bin NIGHTLY_CONFIG={cfg} /usr/bin/python3 {script} "
        "< /dev/null >> {log}.log 2>> {log}.err")


def content(line):
    """A bullet's claim: no marker, no label, no metadata."""
    m = indexer.BULLET_RE.match(line)
    return indexer.SINCE_RE.sub("", indexer.META_RE.sub("", m.group(2) if m else line)).strip()


def label(line):
    m = indexer.BULLET_RE.match(line)
    return m.group(1) if m else None


def norm(line):
    return (label(line) or "") + ": " + re.sub(r"\s+", " ", content(line).lower()).strip(" .;:")


def words(line):
    return set(memeval.terms(content(line)))


def jaccard(a, b):
    return len(a & b) / float(len(a | b)) if a or b else 0.0


def resolves(ref, keys, vault):
    """Does a source ref still point at something: a Timeline key on this card, a file, a URL."""
    if ref.startswith("k:"):
        return ref[2:] in keys
    if ref.startswith(("http://", "https://")):
        return True
    if ref.startswith(("~", "/")):
        return os.path.exists(os.path.expanduser(ref))
    return os.path.exists(os.path.join(vault, ref)) or os.path.exists(os.path.join(vault, ref + ".md"))


def note_names(vault):
    names = set()
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in indexer.SKIP_DIRS]
        names |= {f[:-3].lower() for f in files if f.endswith(".md")}
    return names


def link_ok(target, vault, names):
    t = target.strip()
    return os.path.exists(os.path.join(vault, t + ".md")) or os.path.exists(os.path.join(vault, t)) \
        or os.path.basename(t).lower() in names


def merge_meta(keep, drop):
    """The kept near-duplicate takes the union of both source lists and the earlier added date.
    A consolidate.py line keeps its own form."""
    mk, md = indexer.bullet_meta(keep), indexer.bullet_meta(drop)
    if md is None or (mk and not indexer.META_RE.search(keep)):
        return keep
    sources = (mk["source"] if mk else []) + [s for s in md["source"] if not mk or s not in mk["source"]]
    added = min(mk["added"], md["added"]) if mk else md["added"]
    return indexer.META_RE.sub("", keep).rstrip() + " [source: %s; added: %s]" % (", ".join(sources), added)


def add_superseded(text, lines):
    """Append history lines to the card's ### Superseded list, creating it after the Summary bullets."""
    span = consolidate.summary_span(text)
    if span is None:
        return text.rstrip("\n") + "\n\n## Summary\n\n" + consolidate.SUPERSEDED + "\n\n" + "\n".join(lines) + "\n"
    a, b = span
    body = text[a:b]
    if consolidate.SUPERSEDED in body:
        head, _, rest = body.partition(consolidate.SUPERSEDED)
        m = re.search(r"\n### ", rest)
        block, tail = (rest[:m.start()], rest[m.start():]) if m else (rest, "")
        body = head + consolidate.SUPERSEDED + block.rstrip("\n") + "\n" + "\n".join(lines) + "\n\n" + tail
    else:
        body = body.rstrip("\n") + "\n\n" + consolidate.SUPERSEDED + "\n\n" + "\n".join(lines) + "\n\n"
    return text[:a] + body + text[b:]


def analyse(cards_dir, vault, stale_days, today):
    """The deterministic passes. Returns (findings {pass: [line]}, proposed {rel: (old, new)}, card count)."""
    names, cutoff = note_names(vault), (date.fromisoformat(today) - timedelta(days=stale_days)).isoformat()
    findings, proposed = {p: [] for p in PASSES}, {}
    paths = sorted(glob.glob(os.path.join(cards_dir, "*", "*.md")))
    for path in paths:
        rel, text = os.path.relpath(path, cards_dir), indexer.read(path)
        keys = set(indexer.ENTRY_RE.findall(text))
        bullets = indexer.fact_bullets(text)
        cur, dead, sup = dict(enumerate(text.split("\n"))), set(), []

        def say(p, msg):
            findings[p].append(rel + ": " + msg)

        for u in indexer.unsourced(text):                                   # 1 unsourced: report
            say("unsourced", u)
        seen = {}
        for i, line in bullets:                                             # 2 exact duplicates
            n = norm(line)
            if n not in seen:
                seen[n] = i
                continue
            j = seen[n]
            keep, drop = (i, j) if indexer.bullet_meta(line) and not indexer.bullet_meta(cur[j]) else (j, i)
            dead.add(drop)
            seen[n] = keep
            say("exact_dup", "drop line %d, same as line %d: %s" % (drop + 1, keep + 1, cur[drop].strip()))
        live = [(i, line) for i, line in bullets if i not in dead]
        for x in range(len(live)):                                          # 3 near duplicates
            for y in range(x + 1, len(live)):
                (ia, la), (ib, lb) = live[x], live[y]
                if ia in dead or ib in dead or jaccard(words(cur[ia]), words(cur[ib])) < NEAR \
                        or set(NUM_RE.findall(content(la))) != set(NUM_RE.findall(content(lb))):
                    continue        # same words but different numbers is a contradiction, not a duplicate
                keep, drop = (ia, ib) if len(content(cur[ia])) >= len(content(cur[ib])) else (ib, ia)
                cur[keep] = merge_meta(cur[keep], cur[drop])
                dead.add(drop)
                say("near_dup", "drop line %d into line %d: %s" % (drop + 1, keep + 1, cur[drop].strip()))
        tagged = [(i, l) for i, l in bullets if i not in dead and label(l)]
        for x in range(len(tagged)):                                        # 4 contradiction candidates
            for y in range(x + 1, len(tagged)):
                (ia, la), (ib, lb) = tagged[x], tagged[y]
                if ia in dead or ib in dead or label(la) != label(lb):
                    continue
                na, nb = set(NUM_RE.findall(content(la))), set(NUM_RE.findall(content(lb)))
                wa, wb = {w for w in words(la) if not w[0].isdigit()}, {w for w in words(lb) if not w[0].isdigit()}
                if na == nb or not (na or nb) or jaccard(wa, wb) < CONTRA:
                    continue
                ma, mb = indexer.bullet_meta(la), indexer.bullet_meta(lb)
                if ma and mb and ma["added"] != mb["added"]:
                    (ni, nl, nm), (oi, ol, om) = sorted([(ia, la, ma), (ib, lb, mb)], key=lambda t: t[2]["added"],
                                                        reverse=True)
                    if all(resolves(r, keys, vault) for r in nm["source"]):
                        dead.add(oi)
                        sup.append(ol.strip() + " · superseded %s by %s" % (nm["added"], content(nl)))
                        say("contradiction", "line %d superseded by line %d: %s -> %s" % (
                            oi + 1, ni + 1, content(ol), content(nl)))
                        continue
                say("contradiction", "candidate, lines %d and %d: %s | %s" % (ia + 1, ib + 1, content(la), content(lb)))
        for i, line in bullets:                                             # 5 stale sourced bullets
            m = indexer.bullet_meta(line)
            if i in dead or m is None:
                continue
            gone = [r for r in m["source"] if not resolves(r, keys, vault)]
            if gone and m["added"] < cutoff:
                dead.add(i)
                sup.append(line.strip() + " · retired %s: source gone (%s)" % (today, ", ".join(gone)))
                say("stale", "retire line %d, added %s, source gone: %s" % (i + 1, m["added"], content(line)))
            elif gone:
                say("stale", "source gone but added %s (kept): %s" % (m["added"], content(line)))
            elif m["added"] < cutoff:
                say("stale", "aging, added %s, sources intact (kept): %s" % (m["added"], content(line)))
        for t in indexer.WIKILINK_RE.findall(indexer.owned(text)):         # 6 broken wikilinks: report
            if not link_ok(t, vault, names):
                say("broken_link", "[[" + t.strip() + "]]")
        new = "\n".join(cur[i] for i in range(len(cur)) if i not in dead)
        if sup:
            new = add_superseded(new, sup)
        if new != text:
            proposed[rel] = (text, new)
    return findings, proposed, len(paths)


def patch_text(proposed):
    out = []
    for rel in sorted(proposed):
        old, new = proposed[rel]
        out += difflib.unified_diff(old.splitlines(True), new.splitlines(True), "a/" + rel, "b/" + rel)
    return "".join(out)


def questions_for(cfg):
    qs = memeval.load(os.path.expanduser(cfg["questions"]))
    split = cfg.get("split", "frozen")
    return [q for q in qs if not split or q.get("split") == split]


def score(cfg, cards_dir, questions):
    """memeval's retrieval score with the index-cards corpus pointed at cards_dir. No model."""
    with open(os.path.expanduser(cfg["corpora"])) as f:
        corpora = json.load(f)
    corpora["vault"] = dict(corpora["vault"], exclude=corpora["vault"].get("exclude", []) + ["index-cards/**"])
    corpora["cards"] = {"root": cards_dir, "include": ["*.md"]}
    pre = "vault:index-cards/"
    qs = [dict(q, gold=["cards:" + g[len(pre):] if g.startswith(pre) else g for g in q["gold"]]) for q in questions]
    memeval._sizes.clear()
    rows = memeval.run(qs, corpora, None, cfg.get("k", 5))
    scored = [r for r in rows if r["hit"] is not None]
    mrr = sum(1.0 / r["rank"] for r in scored if r["rank"]) / max(len(scored), 1)
    return {"n": len(scored), "hits": sum(1 for r in scored if r["hit"]), "mrr": round(mrr, 4)}


def sweep(icfg, scratch, proposed):
    """Sweep the scratch cards with the indexer (live sources) and check the proposals survived."""
    indexer.configure(dict(icfg, cards=scratch, lock=os.path.join(os.path.dirname(scratch), "sweep.lock")))
    out = io.StringIO()
    with redirect_stdout(out):
        indexer.run()
    lost = [rel for rel, (_, new) in proposed.items()
            if indexer.owned(indexer.read(os.path.join(scratch, rel))) != indexer.owned(new)]
    return {"line": out.getvalue().strip(), "lost": lost}


def write_live(cards_dir, lock, proposed):
    """Write accepted cards under the indexer's lock; a card that changed since analysis is skipped."""
    written, skipped = [], []
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    with open(lock, "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        for rel, (old, new) in sorted(proposed.items()):
            path = os.path.join(cards_dir, rel)
            if indexer.read(path) != old:
                skipped.append(rel)
                continue
            tmp = os.path.join(os.path.dirname(path), "." + os.path.basename(path) + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new)
            os.replace(tmp, path)
            written.append(rel)
    return written, skipped


def llm_listing(cards_dir):
    """Every sourced bullet across cards as "<card>#B<n> <label>: <text> (since <added>)" for the lint prompt."""
    rows = {}
    for path in sorted(glob.glob(os.path.join(cards_dir, "*", "*.md"))):
        rel = os.path.relpath(path, cards_dir)
        for n, (i, line) in enumerate(indexer.fact_bullets(indexer.read(path))):
            m = indexer.bullet_meta(line)
            if m:
                rows["%s#B%d" % (rel, n)] = "%s %s: %s (since %s)" % ("%s#B%d" % (rel, n), label(line) or "Fact",
                                                                      content(line), m["added"])
    return rows


def llm_pass(cards_dir, cfg, run_it, model):
    """The optional model pass: estimate first, call only when asked."""
    rows = llm_listing(cards_dir)
    prompt = consolidate.LINT_PROMPT.format(facts="\n".join(rows.values()))
    tokens = len(prompt) // 4
    price = cfg.get("price_usd_per_mtok")
    est = "%d sourced bullets, about %d input tokens" % (len(rows), tokens) + (
        ", about $%.4f at $%s per million input tokens (config price_usd_per_mtok)" % (tokens / 1e6 * price, price)
        if price else "; set price_usd_per_mtok in the config for a dollar figure")
    print("llm pass: " + est + ("; calling " + model if run_it else "; not run (no --llm)"))
    if not run_it or not rows:
        return {"estimate": est, "run": False, "pairs": []}
    with tempfile.TemporaryDirectory(prefix="nightly-lint-") as d:
        out, cost = consolidate.call(prompt, consolidate.LINT_SCHEMA, d, model)
    pairs = [p for p in out.get("pairs", []) if p["a"] in rows and p["b"] in rows
             and p["a"].split("#")[0] != p["b"].split("#")[0]]
    return {"estimate": est, "run": True, "cost_usd": cost, "pairs": pairs}


def report_text(entry, findings, llm, cfg, cfg_path, cards_dir):
    sec = lambda title, rows: "## %s (%d)\n\n%s\n" % (title, len(rows), "\n".join("- " + r for r in rows) or "none")
    out = ["# Nightly %s (%s)" % (entry["date"], entry["mode"]), "",
           "Cards: %d. Proposed changes on %d: `%s`." % (entry["cards"], entry["proposed_cards"], entry["patch"]),
           "Apply by hand with `cd '%s' && patch -p1 < '%s'`, or let the gate decide with `--apply`." % (
               cards_dir, entry["patch"]), ""]
    if entry["mode"] == "apply":
        out += ["## Gate", "", "- score before: %s" % json.dumps(entry["score_before"]),
                "- score after: %s" % json.dumps(entry["score_after"]),
                "- sweep: %s" % json.dumps(entry["sweep"]), "- decision: %s" % entry["decision"],
                "- written: %s; skipped (changed since analysis): %s" % (entry["written"], entry["skipped"]), ""]
    out += ["| pass | findings |", "|---|---|"] + ["| %s | %d |" % (p, len(findings[p])) for p in PASSES] + [""]
    for p in PASSES:
        out.append(sec(p, findings[p]))
    out += ["## LLM contradiction pass", "", "- " + llm["estimate"] + (
        "; ran, cost $%.4f, %d pairs" % (llm.get("cost_usd", 0), len(llm["pairs"])) if llm["run"] else "; not run (--llm)")]
    out += ["- %s vs %s: %s" % (p["a"], p["b"], p["why"]) for p in llm["pairs"]]
    line = CRON.format(cfg=cfg_path, script=os.path.abspath(__file__), log=os.path.expanduser(cfg.get("log", "~/.cache/index-cards/nightly")))
    out += ["", "## Schedule (not installed)", "", "```", line, "```", "",
            "Install: `(crontab -l; echo '%s') | crontab -`" % line.replace("'", "'\\''"),
            "Remove: `crontab -l | grep -v nightly/nightly.py | crontab -`", "",
            "The retrieval score is the free part of the question-set eval (ripgrep, no model). The agent-level "
            "grade is the paid part and is not run by this loop.", ""]
    return "\n".join(out)


def run(cfg, cfg_path, apply=False, llm=False, model="sonnet"):
    t0 = time.time()
    icfg = indexer.load_config(os.path.expanduser(cfg["indexer_config"]))
    vault = os.path.expanduser(icfg["vault"])
    cards_dir = os.path.expanduser(icfg.get("cards") or os.path.join(vault, "index-cards"))
    lock = os.path.expanduser(icfg.get("lock", "~/.cache/index-cards/index-cards.lock"))
    out_dir = os.path.expanduser(cfg.get("out", "~/.cache/index-cards/nightly"))
    ledger = os.path.join(out_dir, "ledger.jsonl")
    today = date.today().isoformat()
    os.makedirs(out_dir, exist_ok=True)
    findings, proposed, n = analyse(cards_dir, vault, cfg.get("stale_days", 90), today)
    patch = os.path.join(out_dir, "nightly-%s.patch" % today)
    with open(patch, "w", encoding="utf-8") as f:
        f.write(patch_text(proposed))
    entry = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "date": today, "mode": "apply" if apply else "propose",
             "cards": n, "findings": {p: len(findings[p]) for p in PASSES}, "proposed_cards": len(proposed),
             "patch": patch, "report": os.path.join(out_dir, "nightly-%s.md" % today), "score_before": None,
             "score_after": None, "sweep": None, "decision": "proposed", "written": [], "skipped": []}
    if apply:
        questions = questions_for(cfg)
        entry["score_before"] = score(cfg, cards_dir, questions)
        if not proposed:
            entry["decision"] = "nothing to apply"
        else:
            with tempfile.TemporaryDirectory(prefix="nightly-") as d:
                scratch = os.path.join(d, "index-cards")
                shutil.copytree(cards_dir, scratch)
                for rel, (_, new) in proposed.items():
                    with open(os.path.join(scratch, rel), "w", encoding="utf-8") as f:
                        f.write(new)
                entry["score_after"] = score(cfg, scratch, questions)
                entry["sweep"] = sweep(icfg, scratch, proposed)
            b, a = entry["score_before"], entry["score_after"]
            if a["hits"] < b["hits"] or a["mrr"] < b["mrr"]:
                entry["decision"] = "rejected: score"
            elif entry["sweep"]["lost"]:
                entry["decision"] = "rejected: sweep"
            else:
                entry["written"], entry["skipped"] = write_live(cards_dir, lock, proposed)
                entry["decision"] = "applied"
    llm_out = llm_pass(cards_dir, cfg, llm, model)
    entry["llm"] = {k: v for k, v in llm_out.items() if k != "pairs"}
    entry["llm"]["pairs"] = len(llm_out["pairs"])
    entry["seconds"] = round(time.time() - t0, 1)
    with open(entry["report"], "w", encoding="utf-8") as f:
        f.write(report_text(entry, findings, llm_out, cfg, cfg_path, cards_dir))
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    print("%s %s cards=%d proposed=%d %s decision=%r -> %s" % (
        entry["ts"], entry["mode"], n, len(proposed), " ".join("%s=%d" % (p, len(findings[p])) for p in PASSES),
        entry["decision"], entry["report"]))
    return entry


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.environ.get("NIGHTLY_CONFIG", "~/.config/index-cards/nightly.json"))
    ap.add_argument("--apply", action="store_true", help="apply the change set if it passes the gate")
    ap.add_argument("--llm", action="store_true", help="one model call for contradictions across cards (paid)")
    ap.add_argument("--model", default="sonnet")
    args = ap.parse_args()
    cfg_path = os.path.expanduser(args.config)
    with open(cfg_path) as f:
        cfg = json.load(f)
    run(cfg, cfg_path, args.apply, args.llm, args.model)


if __name__ == "__main__":
    main()
