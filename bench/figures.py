#!/usr/bin/env python3
"""Draw the result figures as SVG from score.py's JSON output. Stdlib only.

  score.py --json results/main.json && figures.py results/main.json OUTDIR
"""
import json
import os
import sys

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
HIGHLIGHT, BASE = "#2a78d6", "#a8a7a1"
SERIES = {"cards": "#2a78d6", "bm25": "#eb6834", "rag": "#1baf7a", "hybrid": "#eda100", "grep": "#e87ba4",
          "memory": "#6250d6"}
LABEL = {"none": "No memory", "grep": "grep", "bm25": "BM25", "rag": "Embedding RAG", "hybrid": "Hybrid (BM25 + RAG)",
         "memory": "Memory file (Claude Code style)", "cards": "index-cards", "cards-v1": "index-cards v1", "oracle": "Oracle (gold notes)"}
FONT = "font-family='Inter, -apple-system, Segoe UI, Helvetica, Arial, sans-serif'"


def svg(w, h, body, title):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' {FONT}>"
            f"<title>{title}</title><rect width='{w}' height='{h}' fill='{SURFACE}'/>{body}</svg>\n")


def bars(res, budget, path, sub):
    rows = [(s, res[f"{s}@{budget}"]) for s in ["none", "grep", "memory", "bm25", "hybrid", "rag", "cards", "oracle"]
            if f"{s}@{budget}" in res]
    w, top, rowh, left, right = 760, 86, 40, 250, 70
    h = top + rowh * len(rows) + 46
    x = lambda v: left + v * (w - left - right)
    out = [f"<text x='24' y='36' font-size='19' font-weight='600' fill='{INK}'>Accuracy at a {budget:,}-token context budget</text>",
           f"<text x='24' y='60' font-size='13' fill='{MUTED}'>{sub}</text>"]
    for t in range(0, 101, 20):
        out.append(f"<line x1='{x(t/100):.1f}' x2='{x(t/100):.1f}' y1='{top-8}' y2='{h-40}' stroke='{GRID}'/>")
        out.append(f"<text x='{x(t/100):.1f}' y='{h-20}' font-size='11' fill='{MUTED}' text-anchor='middle'>{t}%</text>")
    for i, (s, r) in enumerate(rows):
        y = top + i * rowh
        col = HIGHLIGHT if s == "cards" else BASE
        weight = "600" if s == "cards" else "400"
        out.append(f"<text x='{left-12}' y='{y+19}' font-size='13' fill='{INK}' text-anchor='end' font-weight='{weight}'>{LABEL[s]}</text>")
        fade = " fill-opacity='0.55'" if s == "oracle" else ""
        out.append(f"<rect x='{left}' y='{y+6}' width='{max(x(r['acc'])-left, 2):.1f}' height='18' rx='4' fill='{col}'{fade}/>")
        lo, hi = r["ci"]
        out.append(f"<line x1='{x(lo):.1f}' x2='{x(hi):.1f}' y1='{y+15}' y2='{y+15}' stroke='{INK}' stroke-width='1.5' opacity='0.55'/>")
        out.append(f"<text x='{x(hi)+8:.1f}' y='{y+19}' font-size='12.5' fill='{INK}' font-weight='{weight}'>{r['acc']:.1%}</text>")
    open(path, "w").write(svg(w, h, "".join(out), f"Accuracy at {budget} tokens"))


def sweep(res, systems, path, sub):
    budgets = sorted({int(k.split("@")[1]) for k in res if "@" in k and k.split("@")[0] in systems})
    w, h, l, r, t, b = 760, 420, 64, 190, 80, 56
    xs = {bd: l + i * (w - l - r) / max(1, len(budgets) - 1) for i, bd in enumerate(budgets)}
    vals = [res[f"{s}@{bd}"]["acc"] for s in systems for bd in budgets if f"{s}@{bd}" in res]
    lo = max(0, (min(vals) * 100 // 10) * 10 / 100)
    y = lambda v: t + (1 - (v - lo) / (1 - lo)) * (h - t - b)
    out = [f"<text x='24' y='36' font-size='19' font-weight='600' fill='{INK}'>Accuracy as the context budget grows</text>",
           f"<text x='24' y='60' font-size='13' fill='{MUTED}'>{sub}</text>"]
    tick = lo
    while tick <= 1.0001:
        out.append(f"<line x1='{l}' x2='{w-r}' y1='{y(tick):.1f}' y2='{y(tick):.1f}' stroke='{GRID}'/>")
        out.append(f"<text x='{l-10}' y='{y(tick)+4:.1f}' font-size='11' fill='{MUTED}' text-anchor='end'>{tick:.0%}</text>")
        tick += 0.1
    for bd in budgets:
        out.append(f"<text x='{xs[bd]:.1f}' y='{h-30}' font-size='11' fill='{MUTED}' text-anchor='middle'>{bd:,}</text>")
    out.append(f"<text x='{(l+w-r)/2:.0f}' y='{h-10}' font-size='11.5' fill='{MUTED}' text-anchor='middle'>context budget (tokens)</text>")
    ends = []
    for s in systems:
        pts = [(xs[bd], y(res[f"{s}@{bd}"]["acc"])) for bd in budgets if f"{s}@{bd}" in res]
        if not pts:
            continue
        sw = 2.5 if s == "cards" else 2
        out.append(f"<polyline points='{' '.join(f'{a:.1f},{c:.1f}' for a, c in pts)}' fill='none' stroke='{SERIES[s]}' "
                   f"stroke-width='{sw}' stroke-linejoin='round' stroke-linecap='round'/>")
        for a, c in pts:
            out.append(f"<circle cx='{a:.1f}' cy='{c:.1f}' r='4.5' fill='{SERIES[s]}' stroke='{SURFACE}' stroke-width='2'/>")
        ends.append([pts[-1][1], s, res[f"{s}@{budgets[-1]}"]["acc"]])
    ends.sort()
    for i in range(1, len(ends)):                       # keep end labels from colliding
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 16)
    for yy, s, v in ends:
        out.append(f"<text x='{w-r+12}' y='{yy+4:.1f}' font-size='12.5' fill='{INK}' "
                   f"font-weight='{'600' if s == 'cards' else '400'}'>{LABEL[s]} {v:.0%}</text>")
    open(path, "w").write(svg(w, h, "".join(out), "Accuracy by context budget"))


def main():
    res = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    n = res.get("cards@4000", {}).get("n", 0)
    bars(res, 4000, os.path.join(out, "accuracy-4000.svg"),
         f"Held-out test split, {n} questions over a 114k-token synthetic vault (seed 8). Same answering model and prompt; 95% CIs.")
    if sum(1 for k in res if k.startswith("cards@")) > 1:
        sweep(res, ["cards", "rag", "bm25"], os.path.join(out, "budget-sweep.svg"),
              f"Held-out test split, {n} questions. Each line is one retriever; same answering model throughout.")


if __name__ == "__main__":
    main()
