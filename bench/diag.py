"""Answer-in-context rate: does the context contain every key of the answer? No model calls."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from systems import ROOT as HERE, SYSTEMS, load_chunks
from score import has, person_keys
world = json.load(open(os.path.join(HERE, "data", "world.json")))
everyone = {p["name"] for p in world["people"]}
qs = [json.loads(l) for l in open(os.path.join(HERE, "data", "questions.jsonl"))]
split = sys.argv[1] if len(sys.argv) > 1 else "dev"
budget = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
names = sys.argv[3].split(",") if len(sys.argv) > 3 else ["grep", "bm25", "rag", "cards", "oracle"]
qs = [q for q in qs if q["category"] != "abstention" and (split == "all" or q["split"] == split)]
chunks = load_chunks(os.path.join(HERE, "vault"))
for n in names:
    s = SYSTEMS[n](chunks, vault=os.path.join(HERE, "vault"), data=os.path.join(HERE, "data"))
    cat = collections.defaultdict(list)
    for q in qs:
        ctx = s(q, budget)
        cat[q["category"]].append(all(has(ctx, person_keys(k) if k in everyone else k) for k in q["keys"]))
    allv = [v for vs in cat.values() for v in vs]
    print(f"{n:7} {sum(allv)/len(allv):6.1%} " + " ".join(f"{c}={sum(v)/len(v):.0%}" for c, v in sorted(cat.items())))
