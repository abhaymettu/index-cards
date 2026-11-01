#!/usr/bin/env python3
"""Write the benchmark vault from plans.json with a model, one note per call.

  render.py [--data bench/data] [--vault bench/vault] [--jobs 8] [--model sonnet]

A model writes the prose so that notes read like notes rather than templates; code checks that
every planted fact's required strings appear in the note and retries up to three times. Notes
that already exist and pass the check are kept, so a rerun only fills gaps. The finished vault is
committed; nothing else in the benchmark calls a model to build it.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from llm import ask  # noqa: E402

ROOT = os.path.abspath(os.environ.get("BENCH_ROOT", os.path.join(os.path.dirname(__file__), "runs", "main")))

SYSTEM = ("You write realistic personal markdown notes for a fictional software engineer who keeps an "
          "Obsidian vault. Terse, first person, shorthand, varied phrasing. Output only the note, no code fences.")
TOPICS = """CRDTs and local-first sync; Postgres vacuum tuning; reading notes on Designing Data-Intensive
Applications; property-based testing; WebAssembly component model; tokenizer quirks; on-call runbook
habits; home network setup; sourdough schedule; marathon training plan; Kubernetes cost notes; eval
design for LLM apps; vector index tradeoffs; SQLite in production; keyboard shortcuts I keep forgetting;
interview prep for systems design; espresso dial-in notes; tax paperwork checklist; reading list 2026;
garden planting calendar; GPU memory math; rate limiter designs; git tricks; writing better RFCs;
meditation log; bike maintenance; flaky test triage; observability stack comparison; book notes on
Thinking in Systems; apartment move checklist""".replace("\n", " ").split("; ")


def check(text, must):
    low = text.lower()
    return [m for m in must if m.lower() not in low]


def daily_prompt(date, facts, rng):
    wd = dt.date.fromisoformat(date).strftime("%A")
    filler = rng.randint(2, 4) if facts else rng.randint(3, 5)
    lines = [f"Write the daily note for {date} ({wd}).",
             f"First line exactly: # {date} {wd}",
             "Then blocks. Each block starts with a line **HH:MM Short title** (24h time, ascending, 07:00 to 22:30) "
             "followed by one to four lines of prose or bullets.",
             f"Write {filler} filler blocks about work tasks, errands, reading, health or ideas. Filler must not "
             "name any person or project.", ""]
    if facts:
        lines.append("Also put each of these facts in its own block, rephrased in your own words:")
        for f in facts:
            lines.append(f"- {f['text']}  (must contain verbatim: {'; '.join(f['must'])})")
        lines += ["", "Name people exactly as the fact names them: never expand a first name or nickname into a full name."]
    return "\n".join(lines)


def person_prompt(name, n):
    fm = "---\nname: " + name + "\naliases: [" + ", ".join(n["aliases"]) + "]\ncreated: " + n["created"] + "\n---\n"
    return (f"Write a short person note (60 to 120 words) about {name}. Start with exactly this frontmatter:\n{fm}\n"
            f"Then '# {name}', a '## Context' section and a '## Notes' section. Facts to include: {n['text']}\n"
            f"Must contain verbatim: {'; '.join(n['must'])}. Invent nothing about other people or projects.")


def project_prompt(name, n):
    fm = "---\ntype: project\ncreated: " + n["created"] + "\n---\n"
    return (f"Write a project note (100 to 180 words) for {name}. Start with exactly this frontmatter:\n{fm}\n"
            f"Then '# {name}', an '## Overview' section (invent a plausible one-paragraph purpose), and a '## Setup' "
            f"section listing these facts: {n['text']}\nMust contain verbatim: {'; '.join(n['must'])}. "
            "Name no other people or projects.")


def resource_prompt(topic):
    return (f"Write a reference note (250 to 450 words) titled '# {topic}' with a few '##' sections of practical "
            "notes. Name no people or projects. No frontmatter.")


def job(path, prompt, must, model, tail=""):
    if os.path.exists(path) and not check(open(path).read(), must):
        return path, "kept"
    for attempt in range(3):
        text = ask(prompt, system=SYSTEM, model=model)["result"].strip()
        text = re.sub(r"^```\w*\n|\n```$", "", text)
        missing = check(text, must)
        if not missing:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(text.rstrip() + "\n" + tail)
            return path, f"ok after {attempt + 1}"
        prompt += f"\n\nYour last draft was missing: {'; '.join(missing)}. Include them verbatim."
    return path, "FAILED " + "; ".join(missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--vault", default=os.path.join(ROOT, "vault"))
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    plans = json.load(open(os.path.join(a.data, "plans.json")))
    world = json.load(open(os.path.join(a.data, "world.json")))
    rng = random.Random(world["seed"] + 3)
    jobs = []
    start, end = dt.date.fromisoformat(world["start"]), dt.date.fromisoformat(world["today"])
    day = start
    while day < end:
        iso = day.isoformat()
        facts = plans["daily"].get(iso, [])
        if day.weekday() < 5 or facts:
            must = [m for f in facts for m in f["must"]]
            jobs.append((os.path.join(a.vault, "00-Inbox/Daily", iso + ".md"), daily_prompt(iso, facts, rng), must, ""))
        day += dt.timedelta(days=1)
    for name, n in plans["people"].items():
        jobs.append((os.path.join(a.vault, "People", name + ".md"), person_prompt(name, n), n["must"], ""))
    for name, n in plans["projects"].items():
        tail = ("\n## Log\n\n" + "\n".join("- " + u for u in n["updates"]) + "\n") if n["updates"] else ""
        jobs.append((os.path.join(a.vault, "01-Projects", name + ".md"), project_prompt(name, n), n["must"], tail))
    for t in TOPICS:
        jobs.append((os.path.join(a.vault, "03-Resources", t.split(" on ")[-1].replace("/", "-")[:60] + ".md"),
                     resource_prompt(t), [], ""))
    reg = ["# Registry", "", "## person", ""]
    for name, n in sorted(plans["people"].items()):
        if any(x for x in n["aliases"] if x != name.split()[0]):
            reg.append(f"- {name}: {', '.join([name] + n['aliases'])}")
    os.makedirs(os.path.join(a.vault, "index-cards"), exist_ok=True)
    with open(os.path.join(a.vault, "index-cards", "_registry.md"), "w") as f:
        f.write("\n".join(reg) + "\n")
    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for path, status in ex.map(lambda j: job(j[0], j[1], j[2], a.model, j[3]), jobs):
            if status.startswith("FAILED"):
                bad += 1
                print(os.path.relpath(path, a.vault), status, flush=True)
    print(f"{len(jobs)} notes, {bad} failed")


if __name__ == "__main__":
    main()
