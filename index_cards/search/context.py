"""Build the context an agent reads for a question, from index cards, within a token budget.

  context.py "QUESTION" [--budget 4000] [--vault VAULT]

The cards whose names or aliases appear in the question come first: a header, then Timeline lines.
Then the source blocks those lines point at, taken round-robin across cards: blocks sharing the most
of the question's other words first, then the defining note, then newest and oldest alternating.
Cards reached by the one-hop step skip the word ranking: the question's words describe the card it
names, not the one it leads to. Then up to three cards named most often in what was already taken (one hop), with their
blocks. A question that names no card falls back to BM25 over the vault's blocks. Every block is
printed with its note path and date. This is the retriever the benchmark in bench/ measures.
"""
import argparse
import collections
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "indexer"))
import indexer  # noqa: E402

STOP = set("""a about after again all also an and any are as at be been before being both but by can could
did do does doing done for from had has have having he her here him his how i if in into is it its just me
more most my no nor not now of off on once only or other our out over own same she should so some such than
that the their them then there these they this those through to too under until up us very was we were what
when where which while who whom why will with would you your current currently date daily notes note person
people project""".split())
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]*")


def tokens(text):
    return (len(text) + 3) // 4


class Chunk:
    __slots__ = ("path", "date", "heading", "text", "rendered", "words")

    def __init__(self, path, date, heading, text):
        self.path, self.date, self.heading, self.text = path, date, heading, text.strip()
        self.rendered = f"[{path} | {date}]\n{self.text}"
        self.words = [w.lower() for w in WORD.findall(self.text)]


def load_chunks(vault):
    """Blocks: a daily note splits at **HH:MM Title** lines, any other note at ## headings."""
    out = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if d != "index-cards" and not d.startswith("."))
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            path = os.path.relpath(os.path.join(root, f), vault)
            text = open(os.path.join(root, f)).read()
            fm, body = indexer.frontmatter(text)
            date = indexer.note_date(path, fm, os.path.join(root, f))
            daily = path.startswith(indexer.BLOCK_DIRS)
            cur, head = [], None
            if not daily and fm:                # frontmatter (aliases, type) stays with the first block
                cur = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---"]
            for line in body.splitlines():
                c = indexer.CAPTURE_RE.match(line)
                h = re.match(r"^##\s+(.+)", line)
                if (daily and c) or (not daily and h):
                    if "".join(cur).strip():
                        out.append(Chunk(path, date, head, "\n".join(cur)))
                    cur, head = [], (c.group(2) if c else h.group(1))
                cur.append(line)
            if "".join(cur).strip():
                out.append(Chunk(path, date, head, "\n".join(cur)))
    return out


def fill(chunks, budget):
    picked, used, seen = [], 0, set()
    for c in chunks:
        if id(c) in seen:
            continue
        t = tokens(c.rendered) + 1
        if used + t <= budget:
            picked.append(c.rendered)
            used += t
            seen.add(id(c))
    return "\n\n".join(picked)


def terms(question):
    return sorted({w.lower() for w in WORD.findall(question) if w.lower() not in STOP and len(w) > 1})


class BM25:
    name = "bm25"

    def __init__(self, chunks, k1=1.2, b=0.75, **_):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.df = collections.Counter(w for c in chunks for w in set(c.words))
        self.tf = [collections.Counter(c.words) for c in chunks]
        self.avg = sum(len(c.words) for c in chunks) / len(chunks)

    def __call__(self, q, budget):
        return fill([self.chunks[i] for i in self.rank(q)], budget)

    def rank(self, q):
        ts, n = terms(q["question"]), len(self.chunks)
        scores = []
        for i, c in enumerate(self.chunks):
            s = 0.0
            for t in ts:
                f = self.tf[i].get(t)
                if f:
                    idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(c.words) / self.avg))
            if s:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [i for _, i in scores]


class Card:
    __slots__ = ("slug", "entity", "kind", "aliases", "notes", "entries", "path")


def load_cards(vault):
    cards = {}
    for kind in sorted(os.listdir(os.path.join(vault, "index-cards"))):
        d = os.path.join(vault, "index-cards", kind)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            text = open(os.path.join(d, f)).read()
            fm, body = indexer.frontmatter(text)
            c = Card()
            c.slug, c.kind, c.entity, c.notes = f[:-3], kind, fm.get("entity", "").strip('"'), []
            c.path = f"index-cards/{kind}/{f}"
            al = re.findall(r'"([^"]+)"', fm.get("aliases", ""))
            c.aliases = [(a, a != a.lower()) for a in al] or [(c.entity, True)]
            c.entries = []
            for line in body.split(indexer.START, 1)[-1].split(indexer.END, 1)[0].splitlines():
                m = re.match(r"^- (20\d\d-\d\d-\d\d)(?: (\d\d:\d\d))? · (?:\[\[([^|\]]+)\|[^\]]*\]\]|`([^`]+)`) · (.*?) ?<!--k:", line)
                if m:
                    c.entries.append({"date": m.group(1), "path": (m.group(3) or m.group(4)) + ".md"
                                      if m.group(3) else m.group(4), "label": m.group(5),
                                      "line": f"- {m.group(1)}{' ' + m.group(2) if m.group(2) else ''} · "
                                              f"{(m.group(3) or m.group(4))} · {m.group(5)}"})
            cards[c.slug] = c
    return cards


def ends(xs):
    """Indexes newest, oldest, second newest, second oldest, ... of a newest-first list."""
    lo, hi, out = 0, len(xs) - 1, []
    while lo <= hi:
        out.append(lo)
        if hi != lo:
            out.append(hi)
        lo, hi = lo + 1, hi - 1
    return out


class Cards:
    name = "cards"

    def __init__(self, chunks, vault=None, hop_share=0.4, match=True, **_):
        self.cards = load_cards(vault)
        self.table, self.rx, _ = indexer.build_matchers(self.cards)
        self.by_path = collections.defaultdict(list)
        for c in chunks:
            self.by_path[c.path].append(c)
        self.hop_share, self.match = hop_share, match

    def blocks(self, card, entry):
        """The source blocks a Timeline entry points at: the block whose heading starts the label,
        or every block of a whole-note entry."""
        cs = self.by_path.get(entry["path"], [])
        if entry["path"].startswith(indexer.BLOCK_DIRS):
            hit = [c for c in cs if c.heading and entry["label"].startswith(indexer.clean(c.heading, 90))]
            return hit[:1]
        return cs

    def section(self, card, budget, seen, words=()):
        """A card's header and Timeline lines, plus its blocks in reading order: blocks that share the
        most words with the question, then the defining note, then newest and oldest alternating, so
        both where it stands now and how it started fit."""
        own = {i for i, e in enumerate(card.entries) if e["label"].endswith("(defining note)")}
        pos = {i: n for n, i in enumerate(ends(card.entries))}
        hits = {i: sum(1 for w in words if any(w in c.text.lower() for c in self.blocks(card, e)))
                for i, e in enumerate(card.entries)} if words else {}
        order = sorted(pos, key=lambda i: (-hits.get(i, 0), i not in own, pos[i]))
        head = f"[{card.path}] {card.entity} ({card.kind}), {len(card.entries)} entries, newest first"
        lines, used, keep = [head], tokens(head), set()
        for i in order:
            if used + tokens(card.entries[i]["line"]) > budget * 0.35:
                break
            keep.add(i)
            used += tokens(card.entries[i]["line"]) + 1
        lines += [e["line"] for i, e in enumerate(card.entries) if i in keep]
        blocks = []
        for i in order:
            for c in self.blocks(card, card.entries[i]):
                if id(c) not in seen:
                    blocks.append(c)
        return "\n".join(lines), blocks

    def __call__(self, q, budget):
        seeds = sorted(indexer.alias_hits(q["question"], self.rx, self.table))
        if not seeds:
            return BM25Fallback.get(self)(q, budget)
        named = {w.lower() for s in seeds for a, _ in self.cards[s].aliases for w in WORD.findall(a)}
        words = [w for w in terms(q["question"]) if w not in named] if self.match else ()
        out, used, seen = [], 0, set()
        per = (budget * (1 - self.hop_share if self.hop_share else 1)) / len(seeds)
        queues = []
        for s in seeds:
            text, blocks = self.section(self.cards[s], per, seen, words)
            out.append(text)
            used += tokens(text) + 1
            queues.append(blocks)
        limit = budget * (1 - self.hop_share)
        used = self._drain(queues, out, used, limit, seen)
        hops = collections.Counter()
        for text in out:
            for slug in sorted(indexer.alias_hits(text, self.rx, self.table)):
                if slug not in seeds:
                    hops[slug] += 1
        seed_queues, queues = queues, []
        for slug in sorted(hops, key=lambda k: (-hops[k], k))[:3]:      # ties by name, never by hash order
            text, blocks = self.section(self.cards[slug], (budget - used) / 3, seen)
            if used + tokens(text) <= budget:
                out.append(text)
                used += tokens(text) + 1
                queues.append(blocks)
        self._drain(queues + seed_queues, out, used, budget, seen)
        return "\n\n".join(out)

    @staticmethod
    def _drain(queues, out, used, limit, seen):
        progress = True
        while progress:
            progress = False
            for qu in queues:
                while qu:
                    c = qu.pop(0)
                    if id(c) in seen:
                        continue
                    t = tokens(c.rendered) + 1
                    if used + t <= limit:
                        out.append(c.rendered)
                        used += t
                        seen.add(id(c))
                        progress = True
                        break
        return used


class BM25Fallback:
    _bm = {}

    @classmethod
    def get(cls, cards):
        if id(cards) not in cls._bm:
            cls._bm[id(cards)] = BM25([c for cs in cards.by_path.values() for c in cs])
        return cls._bm[id(cards)]



def main():
    ap = argparse.ArgumentParser(description="Print the index-card context for a question.")
    ap.add_argument("question")
    ap.add_argument("--budget", type=int, default=4000, help="context budget in tokens (chars / 4)")
    ap.add_argument("--vault", default=indexer.VAULT)
    a = ap.parse_args()
    chunks = load_chunks(a.vault)
    print(Cards(chunks, vault=a.vault)({"question": a.question}, a.budget))


if __name__ == "__main__":
    main()
