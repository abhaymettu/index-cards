#!/usr/bin/env python3
"""Write paper/numbers.tex and site numbers from score.py JSON, so no number is typed by hand.

  texnums.py SEED8.json SEED7.json SEED8-HAIKU.json AGENT-SONNET.json AGENT-HAIKU.json > paper/numbers.tex
"""
import json
import sys

NAMES = {"none": "None", "grep": "Grep", "bm25": "Bm", "rag": "Rag", "hybrid": "Hybrid", "memory": "Memory",
         "cards": "Cards", "cards-v1": "CardsVone", "oracle": "Oracle"}
WORDS = {1000: "One", 2000: "Two", 4000: "Four", 8000: "Eight"}


def pct(x):
    return f"{100 * x:.1f}"


def emit(prefix, res):
    for key, r in res.items():
        if "@" not in key:
            continue
        s, b = key.split("@")
        if s not in NAMES or int(b) not in WORDS:
            continue
        m = f"{prefix}{NAMES[s]}{WORDS[int(b)]}"
        print(f"\\newcommand{{\\{m}Acc}}{{{pct(r['acc'])}}}")
        print(f"\\newcommand{{\\{m}Lo}}{{{pct(r['ci'][0])}}}")
        print(f"\\newcommand{{\\{m}Hi}}{{{pct(r['ci'][1])}}}")
        print(f"\\newcommand{{\\{m}Stale}}{{{pct(r['stale_rate'])}}}")
        print(f"\\newcommand{{\\{m}Abst}}{{{pct(r['abstain_rate'])}}}")
        print(f"\\newcommand{{\\{m}Ctx}}{{{r['ctx_tokens']:.0f}}}")
        print(f"\\newcommand{{\\{m}Ms}}{{{r['retrieve_ms']:.1f}}}")
        for c, v in r["by_category"].items():
            print(f"\\newcommand{{\\{m}{c.capitalize()}}}{{{100 * v:.0f}}}")
        if s == "cards" and b == "4000":
            print(f"\\newcommand{{\\{prefix}N}}{{{r['n']}}}")
    for k, p in res.get("bootstrap", {}).items():
        a, b = k.split("@")
        print(f"\\newcommand{{\\{prefix}P{NAMES[a.split('>')[1]]}{WORDS[int(b)]}}}{{{p:.4f}}}")


def agent(prefix, path):
    for setup, r in json.load(open(path)).items():
        if setup == "bootstrap":
            continue
        n = prefix + setup.capitalize()
        print(f"\\newcommand{{\\{n}Acc}}{{{pct(r['acc'])}}}")
        print(f"\\newcommand{{\\{n}Tok}}{{{r['input_tokens']:,.0f}}}".replace(",", "{,}"))
        print(f"\\newcommand{{\\{n}Turns}}{{{r['turns']:.1f}}}")
        print(f"\\newcommand{{\\{n}Secs}}{{{r['wall_s']:.1f}}}")
        print(f"\\newcommand{{\\{n}N}}{{{r['n']}}}")


def main():
    """texnums.py SEED8.json SEED7.json SEED8-HAIKU.json AGENT-SONNET.json AGENT-HAIKU.json"""
    emit("Main", json.load(open(sys.argv[1])))
    emit("Seven", json.load(open(sys.argv[2])))
    emit("Haiku", json.load(open(sys.argv[3])))
    agent("AgS", sys.argv[4])
    agent("AgH", sys.argv[5])


if __name__ == "__main__":
    main()
