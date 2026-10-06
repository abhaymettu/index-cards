#!/usr/bin/env python3
"""digest: deterministic, no-model compaction of session transcripts and notes.

  digest.py build CORPORA OUT_ROOT [--corpus NAME ...]

For every file a corpus in CORPORA covers (the same config and globs memeval uses), writes
OUT_ROOT/<corpus>/<path relative to the corpus root>: JSONL, one small record per line, each with
`kind, text, ts, src`. `src` is `<corpus>:<path>#L<a>[-<b>]`, the span the record came from. The digest
keeps the source's relative path, so `<corpus>:<path>` refs (and memeval gold sets) are unchanged when
a corpora config points its root at OUT_ROOT/<corpus>.

*.jsonl files are read as Claude Code transcripts: user prompts and assistant text are kept, tool
results, thinking and reminders are dropped. Other files are read as markdown notes, one record per
section. Nothing is ever deleted: a digest outlives its source, and a rewrite that would lose records
first copies the old digest to OUT_ROOT/archive/. Stdlib only.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

CAP = 2000                                    # chars per prompt (clipped) or per record (split)
BUDGET = 16000                                # bytes of ranked session digest, about a long note (p90 note digest 12KB)
PRIORITY = ("prompt", "reply", "step", "file", "url", "cmd")   # what was said before what was run
NO_INDEX = "DO NOT INDEX THIS CHAT"
PRIVATE_RE = re.compile(r"<private>.*?</private>", re.S)
NOISE_RE = re.compile(r"<(system-reminder|local-command-\w+|command-\w+|task-notification)>.*?</\1>", re.S)
TOKEN_RE = re.compile(r"[A-Za-z0-9_/+=.-]{32,}")
KNOWN_KEY_RE = re.compile(r"\b(?:sk-|ghp_|gho_|github_pat_|xox[abpr]-|AKIA|AIza|eyJ)[A-Za-z0-9_.-]{16,}")
UUID_RE = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$")
URL_RE = re.compile(r"https?://[^\s)\"'<>\]]+")
FILE_TOOLS = ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit")


def scrub(text):
    """Redact key-shaped tokens. Paths, slugs and UUIDs survive; a long segment mixing upper, lower and
    digits, or long hex, does not."""
    def seg_ok(s):
        s = UUID_RE.sub("", s)
        return len(s) < 32 or not (re.search(r"[A-Z]", s) and re.search(r"[a-z]", s) and re.search(r"\d", s)
                                   or re.fullmatch(r"[0-9a-fA-F]{32,}", s))
    text = KNOWN_KEY_RE.sub("[redacted]", text)
    return TOKEN_RE.sub(lambda m: m.group() if all(seg_ok(s) for s in m.group().split("/")) else "[redacted]",
                        text)


def clip(text):
    text = re.sub(r"[ \t]*\n\s*\n+", "\n", text.strip())
    return text if len(text) <= CAP else text[:CAP] + " [...]"


def chunks(pairs):
    """Group (line number, line) pairs at line ends into runs of at most CAP chars, so nothing is cut."""
    out, size = [[]], 0
    for n, line in pairs:
        if out[-1] and size + len(line) > CAP:
            out.append([])
            size = 0
        out[-1].append((n, line))
        size += len(line) + 1
    return out


def pieces(text):
    lines = re.sub(r"[ \t]*\n\s*\n+", "\n", text.strip()).split("\n")
    return ["\n".join(x for _, x in c) for c in chunks(enumerate(lines))]


def blocks(content, kind):
    if isinstance(content, str):
        return [content] if kind == "text" else []
    return [b for b in content or [] if isinstance(b, dict) and b.get("type") == kind]


def digest_session(path, ref):
    head = {"kind": "session", "text": "", "ts": "", "src": ref, "id": "", "cwd": "", "branch": "",
            "title": "", "start": "", "end": ""}
    out, seen, pending = [], set(), []
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if any(NO_INDEX in line for line in lines):
        head["text"] = "not indexed (marker)"
        return [head]

    def add(kind, text, ts, n, **extra):
        text = scrub(text)
        if text and (kind, text) not in seen:
            seen.add((kind, text))
            out.append(dict({"kind": kind, "text": text, "ts": ts, "src": "%s#L%d" % (ref, n)}, **extra))

    def settle(final):
        """A turn's last reply is its conclusion; earlier assistant text in the turn is a step."""
        if pending:
            text, ts, n = pending.pop()
            for piece in pieces(text):
                add("reply" if final else "step", piece, ts, n)

    for n, line in enumerate(lines, 1):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        ts = r.get("timestamp", "")
        if r.get("type") == "ai-title":
            head["title"] = scrub(r.get("aiTitle", ""))
        if r.get("type") not in ("user", "assistant") or r.get("isMeta"):
            continue
        head["start"] = head["start"] or ts
        head["end"] = ts or head["end"]
        for k in ("cwd", "branch"):
            head[k] = head[k] or r.get("gitBranch" if k == "branch" else k, "")
        head["id"] = head["id"] or r.get("sessionId", "")
        content = (r.get("message") or {}).get("content")
        for b in blocks(content, "text"):
            text = b if isinstance(b, str) else b.get("text", "")
            text = NOISE_RE.sub("", PRIVATE_RE.sub("", text)).strip()
            if not text:
                continue
            settle(r["type"] == "user")
            if r["type"] == "user":
                add("prompt", clip(text), ts, n)
            else:
                pending.append((text, ts, n))
        for b in blocks(content, "tool_use"):
            inp = b.get("input") or {}
            name = b.get("name", "")
            if name in FILE_TOOLS and inp.get("file_path"):
                add("file", inp["file_path"], ts, n, op=name)
            elif name == "Bash" and inp.get("command"):      # the stated intent, not the heredoc
                add("cmd", (inp.get("description") or inp["command"].strip().split("\n")[0])[:160], ts, n)
            for u in URL_RE.findall(json.dumps(inp)):
                add("url", u.rstrip(".,;\\"), ts, n)
    settle(True)
    head["ts"] = head["start"]
    head["text"] = head["title"]
    return [head] + out


def frontmatter_dates(text):
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    return DATE_RE.findall(text[:end]) if end > 0 else []


def digest_note(path, ref):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    mtime = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))
    dates = frontmatter_dates(text)
    note_ts = dates[0] if dates else mtime
    title = os.path.splitext(os.path.basename(path))[0]
    out = [{"kind": "note", "text": scrub(title), "ts": note_ts, "src": ref, "dates": dates, "mtime": mtime}]
    lines = PRIVATE_RE.sub("", text).split("\n")
    trail, body, fence = [], [], False

    def flush():
        """One record per section; a long section becomes several records, never a truncated one."""
        for chunk in chunks(body):
            if not chunk and not trail:
                continue
            t = scrub("\n".join(x for _, x in chunk))
            d = DATE_RE.search(" ".join(trail) + " " + t)
            a, b = (chunk[0][0], chunk[-1][0]) if chunk else (head_line, head_line)
            out.append({"kind": "section", "text": t, "ts": d.group() if d else note_ts,
                        "src": "%s#L%d-L%d" % (ref, a, b), "heading": scrub(" > ".join(trail))})

    head_line = 1
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEADING_RE.match(line)
        if m:
            flush()
            trail = trail[:len(m.group(1)) - 1] + [m.group(2)]
            head_line, body = n, []
        elif not fence and line.strip() and line.strip() != "---":
            body.append((n, line))
    flush()
    return out


def corpus_files(c):
    root = os.path.expanduser(c["root"])
    os.listdir(root)
    args = [a for p in c.get("include", []) for a in ("--glob", p)]
    args += [a for p in c.get("exclude", []) for a in ("--glob", "!" + p)]
    return subprocess.run(["rg", "--files", "--no-ignore"] + args, cwd=root, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL).stdout.splitlines()


def dumps(r):
    # U+2028/9 would split a line for str.splitlines readers
    return json.dumps(r, ensure_ascii=False, sort_keys=True).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def bound(records):
    """Keep the session record and the highest-priority records that fit in BUDGET, in source order.
    The rest is overflow: kept on disk, not ranked."""
    order = sorted(range(1, len(records)), key=lambda i: (PRIORITY.index(records[i]["kind"]), i))
    keep, used = {0}, len(dumps(records[0]))
    for i in order:
        size = len(dumps(records[i])) + 1
        if used + size <= BUDGET:
            keep.add(i)
            used += size
    return [r for i, r in enumerate(records) if i in keep], [r for i, r in enumerate(records) if i not in keep]


def write(files, archive):
    """files: [(path, records)], the digest (header record first) then its overflow, if any. If the old
    files hold body records the new ones lack, the old files are archived first."""
    new, old = set(), set()
    for k, (path, recs) in enumerate(files):
        new.update(dumps(r) for r in recs[k == 0:])
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old.update(line.rstrip("\n") for line in f.readlines()[k == 0:])
    if old - new:
        for path, _ in files:
            if os.path.exists(path):
                dest = os.path.join(archive, os.path.relpath(path, os.path.dirname(archive)))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(path, dest + time.strftime(".%Y%m%dT%H%M%S"))
    for path, recs in files:
        if not recs and not os.path.exists(path):
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            f.writelines(dumps(r) + "\n" for r in recs)
        os.replace(path + ".tmp", path)


def build(corpora, out_root, names=None):
    counts = {}
    for name, c in sorted(corpora.items()):
        if names and name not in names:
            continue
        root = os.path.expanduser(c["root"])
        done = 0
        for rel in corpus_files(c):
            src = os.path.join(root, rel)
            dest = os.path.join(out_root, name, rel)
            try:
                if os.path.exists(dest) and os.path.getmtime(dest) >= os.path.getmtime(src):
                    continue
                if rel.endswith(".jsonl"):
                    keep, over = bound(digest_session(src, name + ":" + rel))
                    files = [(dest, keep), (os.path.join(out_root, "overflow", name, rel), over)]
                else:
                    files = [(dest, digest_note(src, name + ":" + rel))]
                write(files, os.path.join(out_root, "archive"))
                done += 1
            except OSError as e:
                print("skip %s:%s (%s)" % (name, rel, e), file=sys.stderr)
        counts[name] = done
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("corpora")
    b.add_argument("out_root")
    b.add_argument("--corpus", action="append", help="only this corpus (repeatable)")
    args = ap.parse_args()
    with open(args.corpora) as f:
        corpora = json.load(f)
    for name, n in build(corpora, os.path.expanduser(args.out_root), args.corpus).items():
        print("%s: %d digests written" % (name, n))


if __name__ == "__main__":
    main()
