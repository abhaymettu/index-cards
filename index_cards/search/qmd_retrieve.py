#!/usr/bin/python3
"""memeval --cmd adapter for qmd: question on stdin, ranked `<corpus>:<path>` refs on stdout.

  qmd_retrieve.py MODE [--index NAME]      MODE: query | vsearch | search

Each qmd collection must be named after its memeval corpus, so `qmd://<c>/<p>` becomes `<c>:<p>`.
qmd's config dir (QMD_CONFIG_DIR) and model cache come from the environment.
"""
import argparse
import json
import subprocess
import sys


def refs(results):
    out = []
    for r in results:
        name, _, path = r["file"].split("://", 1)[1].partition("/")
        ref = name + ":" + path.split("?index=", 1)[0]
        if ref not in out:
            out.append(ref)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("query", "vsearch", "search"))
    ap.add_argument("--index", default="index")
    args = ap.parse_args()
    question = " ".join(sys.stdin.read().split())
    p = subprocess.run(["qmd", "--index", args.index, args.mode, question, "--format", "json",
                        "-n", "10"], stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, check=True)
    print("\n".join(refs(json.loads(p.stdout or "[]"))))


if __name__ == "__main__":
    main()
