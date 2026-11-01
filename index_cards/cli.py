"""index-cards: one command for every layer.

  index-cards demo [DIR]               copy the bundled demo vault to DIR, build its cards, show one
  index-cards init VAULT               write a config for your vault (~/.config/index-cards/config.json)
  index-cards sweep [indexer args]     build or refresh the cards
  index-cards context "QUESTION"       print the context an agent should read, within --budget tokens
  index-cards eval ...                 memeval: score retrievers on your own frozen question set
  index-cards nightly ...              the nightly lint loop (report, or --apply behind the eval gate)
  index-cards digest ... / consolidate ...

Every subcommand but demo and init runs the script of the same layer with the remaining arguments,
so `index-cards sweep --help` shows the indexer's own options.
"""
import json
import os
import runpy
import shutil
import sys

PKG = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.expanduser("~/.config/index-cards/config.json")
SCRIPTS = {"sweep": "indexer/indexer.py", "context": "search/context.py", "eval": "eval/memeval.py",
           "nightly": "nightly/nightly.py", "digest": "digest/digest.py", "consolidate": "consolidate/consolidate.py"}
DEMO_Q = "What is the current deadline for Kestrel-Sync?"


def run(script, args, config=None):
    if config:
        os.environ["INDEX_CONFIG"] = config
    sys.argv = [script] + args
    runpy.run_path(os.path.join(PKG, script), run_name="__main__")


def layout(vault):
    """Guess folder roles from what exists; the defaults are the PARA layout in docs/VAULT-LAYOUT.md."""
    has = lambda *p: [x for x in p if os.path.isdir(os.path.join(vault, x))]
    return {"vault": vault, "lock": os.path.expanduser("~/.cache/index-cards/index-cards.lock"),
            "person_dirs": has("People", "people", "02-Areas/Relationships") or ["People"],
            "project_dirs": has("01-Projects", "Projects", "projects") or ["01-Projects"],
            "area_dirs": has("02-Areas", "Areas"), "topic_dirs": has("Wiki", "Topics"),
            "archive_dirs": has("04-Archives", "Archive"),
            "block_dirs": [d + "/" for d in has("00-Inbox/Daily", "Daily", "Journal", "daily")],
            "skip_dirs": [".obsidian", ".trash", "Templates", "03-Resources/Credentials"]}


def demo(args):
    dst = os.path.abspath(args[0] if args else "index-cards-demo")
    if os.path.exists(dst):
        sys.exit(f"{dst} exists; pass another directory")
    shutil.copytree(os.path.join(PKG, "demo", "vault"), dst)
    cfg = layout(dst)
    cfg["lock"] = os.path.join(dst, ".index-cards.lock")
    path = os.path.join(dst, ".index-cards.json")
    json.dump(cfg, open(path, "w"), indent=1)
    print(f"Demo vault: {dst} (fictional: 36 people, 12 projects, six months of daily notes)\n")
    run(SCRIPTS["sweep"], [], path)
    card = os.path.join(dst, "index-cards", "project", "kestrel-sync.md")
    print(f"\nCatalog: {dst}/index-cards/_catalog.md\nOne card, {card}:\n")
    text = open(card).read()
    print(text[text.index("## Timeline"):][:1400].rstrip() + "\n...\n")
    print(f'Context for "{DEMO_Q}" (budget 600 tokens):\n')
    run(SCRIPTS["context"], [DEMO_Q, "--budget", "600", "--vault", dst], path)
    print(f"\nNext: index-cards init <your vault>, then index-cards sweep. Config used here: {path}")


def init(args):
    if not args:
        sys.exit("usage: index-cards init VAULT")
    vault = os.path.abspath(os.path.expanduser(args[0]))
    if os.path.exists(CONFIG) and "--force" not in args:
        sys.exit(f"{CONFIG} exists; pass --force to overwrite")
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    json.dump(layout(vault), open(CONFIG, "w"), indent=1)
    print(f"Wrote {CONFIG}. Check the folder lists, then run: index-cards sweep")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "demo":
        return demo(args)
    if cmd == "init":
        return init(args)
    if cmd not in SCRIPTS:
        sys.exit(f"unknown command {cmd}; see index-cards --help")
    run(SCRIPTS[cmd], args)


if __name__ == "__main__":
    main()
