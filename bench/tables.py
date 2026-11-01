#!/usr/bin/env python3
"""Write the paper's tables from score.py JSON.

  tables.py SEED8.json SEED7.json SEED8-HAIKU.json AGENT-SONNET.json AGENT-HAIKU.json OUTDIR
"""
import json
import os
import sys

NAMES = {"none": "No memory", "grep": "grep", "memory": "Memory file", "bm25": "BM25", "hybrid": "Hybrid",
         "rag": "Embedding RAG", "cards-v1": "index-cards v1", "cards": "\\textbf{index-cards}", "oracle": "Oracle"}
ORDER = ["none", "grep", "memory", "bm25", "hybrid", "rag", "cards-v1", "cards", "oracle"]
CATS = ["single", "multihop", "update", "aggregate", "temporal"]


def main_table(s8, s7, hk):
    rows = []
    for s in ORDER:
        r = s8.get(f"{s}@4000")
        if not r:
            continue
        r7, rh = s7.get(f"{s}@4000"), hk.get(f"{s}@4000")
        cells = [NAMES[s], f"{100 * r['acc']:.1f}", f"{100 * r['ci'][0]:.0f}--{100 * r['ci'][1]:.0f}"]
        cells += [f"{100 * r['by_category'][c]:.0f}" for c in CATS]
        cells += [f"{100 * r['abstain_rate']:.1f}", f"{100 * r['stale_rate']:.1f}",
                  f"{100 * r7['acc']:.1f}" if r7 else "", f"{100 * rh['acc']:.1f}" if rh else ""]
        rows.append(" & ".join(cells) + " \\\\")
    n = s8["cards@4000"]["n"]
    return ("\\begin{table*}[t]\\centering\\small\n\\caption{Accuracy at a 4{,}000-token budget. Columns up to Stale: seed 8, "
            f"the fresh held-out world, {n} test questions, Sonnet answering. Abst.\\ is the share of answerable "
            "questions answered ``unknown''; Stale is the share of changed-fact questions answered with a superseded "
            "value. Seed 7 is the first world (development data for the final retriever; v1 was frozen before its "
            "test run). Haiku is seed 8 with Haiku answering.}\\label{tab:main}\n"
            "\\begin{tabular}{lrrrrrrrrrrr}\\toprule\n"
            "System & Acc. & 95\\% CI & Single & Multihop & Update & Aggr. & Temporal & Abst. & Stale & Seed 7 & Haiku \\\\\n"
            "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table*}\n")


def agent_table(ags, agh):
    rows = []
    for setup, label in [("plain", "Vault only"), ("memory", "Vault + memory file"), ("cards", "Vault + index-cards")]:
        a, h = ags[setup], agh[setup]
        rows.append(f"{label} & {100 * a['acc']:.1f} & {a['input_tokens']:,.0f} & {a['turns']:.1f} & "
                    f"{100 * h['acc']:.1f} & {h['input_tokens']:,.0f} & {h['turns']:.1f} \\\\".replace(",", "{,}"))
    n = ags["plain"]["n"]
    return ("\\begin{table}[t]\\centering\\small\n\\caption{The agent loop: Claude Code with Read, Grep and Glob in the "
            f"seed-7 vault, no budget, {n} test questions. Tokens are input tokens per question.}}\\label{{tab:agent}}\n"
            "\\begin{tabular}{lrrrrrr}\\toprule\n& \\multicolumn{3}{c}{Sonnet} & \\multicolumn{3}{c}{Haiku} \\\\\n"
            "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\nSetup & Acc. & Tokens & Turns & Acc. & Tokens & Turns \\\\\n"
            "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table}\n")


def main():
    s8, s7, hk, ags, agh = (json.load(open(p)) for p in sys.argv[1:6])
    out = sys.argv[6]
    open(os.path.join(out, "table-main.tex"), "w").write(main_table(s8, s7, hk))
    open(os.path.join(out, "table-agent.tex"), "w").write(agent_table(ags, agh))


if __name__ == "__main__":
    main()
