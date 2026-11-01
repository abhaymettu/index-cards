#!/usr/bin/env python3
"""Generate the benchmark's fictional world: people, projects, a six-month event log, the note
plans a writer turns into a vault, and the questions with their answers.

  world.py [--seed 7] [--out bench/data]

Writes world.json (the ground truth), plans.json (what each note must say) and questions.jsonl.
Everything is fictional and derived from the seed; rerunning with the same seed gives the same
files byte for byte. The vault itself is written from plans.json by render.py.
"""
import argparse
import hashlib
import datetime as dt
import json
import os
import random
import re

FIRST = """Ana Bilal Chioma Dmitri Elif Farah Gideon Hana Ivo Jun Kavya Lior Mateo Nadia Oskar Priya
Quentin Rosa Sven Tamsin Umar Vera Wendell Ximena Yusuf Zara Anika Bruno Celeste Dario Esme Felix
Greta Hugo Ines Joaquin""".split()
LAST = """Abara Lindqvist Moreau Okonkwo Petrov Quiroga Rahman Sato Tanaka Varga Whitfield Yilmaz
Zielinski Castellano Delacroix Eriksen Fontaine Galloway Haddad Iwasaki Jaramillo Kowalczyk
Laurent Mbeki Nakamura Oyelaran Pacheco Rasmussen Szabo Trevino Ulloa Vasquez Wexler Ashdown
Brennan Calloway""".split()
NICK = {"Dmitri": "Dima", "Quentin": "Q", "Wendell": "Dell", "Ximena": "Xime", "Joaquin": "Quino",
        "Celeste": "Cece", "Gideon": "Gid", "Tamsin": "Tam"}
ROLES = ["data engineer", "product designer", "ML researcher", "backend engineer", "engineering manager",
         "founder", "security engineer", "technical writer", "SRE", "frontend engineer", "PhD student",
         "developer advocate"]
COMPANIES = ["Northwind Labs", "Quillfeather", "Brightwater AI", "Cobalt Harbor", "Tessellate",
             "Juniper Systems", "Halcyon Bio", "Marrow & Finch", "Ostrander Robotics", "Pinecrest Data",
             "Saltmarsh Studio", "Verdant Grid", "Kiteline", "Embergate", "Lumen Fold"]
CITIES = ["Porto", "Tallinn", "Montreal", "Osaka", "Nairobi", "Valparaiso", "Ljubljana", "Tbilisi",
          "Madison", "Leipzig", "Hobart", "Cordoba", "Bergen", "Kraków", "Austin"]
EVENTS = ["the RustConf meetup", "the Halloween hackathon", "a climbing gym session", "PyData Porto",
          "a friend's dinner party", "the local AI reading group", "a startup demo night",
          "the open-source sprint", "a conference hallway track", "the board game cafe"]
HOBBIES = ["bouldering", "sourdough baking", "competitive chess", "trail running", "film photography",
           "beekeeping", "salsa dancing", "woodworking", "birdwatching", "fencing", "pottery",
           "open-water swimming"]
PETS = ["Biscuit", "Pixel", "Mochi", "Juniper", "Turnip", "Waffles", "Ziggy", "Pepper", "Noodle",
        "Comet", "Olive", "Basil"]
SCHOOLS = ["Carnegie Mellon", "ETH Zurich", "the University of Waterloo", "Imperial College",
           "KAIST", "the University of Cape Town", "TU Delft", "McGill", "Sciences Po"]
PROJECTS = ["Kestrel-Sync", "Orchard-Maps", "Lantern-CI", "Bramble-DB", "Quarry-Vision", "Tidewater-API",
            "Saffron-Notes", "Gullwing-Auth", "Mosaic-Ledger", "Cinder-Queue", "Heron-Eval", "Pebble-Shell"]
LANGS = ["Rust", "Go", "Elixir", "TypeScript", "Python", "Kotlin", "Zig", "OCaml", "Swift", "Clojure"]
HOSTS = ["GitHub", "GitLab", "Codeberg", "SourceHut"]
STATUSES = ["paused", "shipped", "in beta", "cancelled"]
TOPICS = ["hiring plans", "a conference talk", "remote work", "a book they are reading", "pricing",
          "on-call rotations", "a side project idea", "travel plans", "the job market", "eval design"]
MORE_FIRST = """Aiko Benedikt Caio Daria Emeka Freya Goran Ilse Jonas Kenji Leila Marisol Noor Otto Paloma Rafael
Signe Teodor Uma Valentin Wren Yara Zoltan Amara""".split()
MORE_LAST = """Aldana Bachmann Cervantes Dimitriou Ekwueme Ferreira Grünewald Halvorsen Ibarra Jovanovic Kaminski
Lindgren Marchetti Novak Ortega Pellegrino Quintero Rinaldi Sandoval Thorsen Uchida Valverde Wainwright
Xiong Yamada Zamora Achterberg Bergqvist Carvalho Dragomir Esposito Falk Gutierrez Holloway Ivanova
Jansen Kuznetsov Lombardi Moretti Nikolaidis Olsen Pires Ramires Sorensen Takahashi Underwood Vogel
Weissman Yildiz Zubiri Aguilar Brandt Coelho Dunmore Engel Fitzroy""".split()
MORE_NICK = {"Benedikt": "Ben", "Valentin": "Val", "Teodor": "Teo", "Marisol": "Mari", "Zoltan": "Zoli",
             "Emeka": "Meks"}
NAME_A = """Kestrel Orchard Lantern Bramble Quarry Tidewater Saffron Gullwing Mosaic Cinder Heron Pebble Falcon
Granite Willow Tundra Sparrow Coral Ember Fjord Hollow Iris Kelp Lichen Marten Nimbus Otter Prism Quill
Rook Sable Thistle Umber Vesper Wisp""".split()
NAME_B = "Sync Maps CI DB Vision API Notes Auth Ledger Queue Eval Shell Index Relay Forge Lens Graph Cache".split()
START = dt.date(2026, 3, 2)
WEEKS = 26
TODAY = START + dt.timedelta(weeks=WEEKS) + dt.timedelta(days=1)


def d(day):
    return (START + dt.timedelta(days=day)).isoformat()


def human(iso):
    x = dt.date.fromisoformat(iso)
    return x.strftime("%B ") + str(x.day)


def date_keys(iso):
    x = dt.date.fromisoformat(iso)
    return "|".join([iso, x.strftime("%B ") + str(x.day), x.strftime("%b ") + str(x.day),
                     str(x.day) + x.strftime(" %B"), f"{x.month}/{x.day}"])


def weekday(rng, lo, hi):
    while True:
        day = rng.randint(lo, hi)
        if (START + dt.timedelta(days=day)).weekday() < 5:
            return day


SCALES = {   # people, projects, touchpoints per person, job changes, moves, corrections
    "small": dict(people=36, projects=12, touch=(1, 6), jobs=9, moves=6, fixes=6, singles=50, temporal=16, abstain=10, pulse=False),
    "main": dict(people=90, projects=30, touch=(2, 9), jobs=22, moves=14, fixes=12, singles=70, temporal=24, abstain=16, pulse=True),
}
S = dict(SCALES["small"])
AMBIG = set()       # first names more than one person has: notes never use them alone


def build(seed):
    rng = random.Random(seed)
    if S["people"] == 36:
        last = rng.sample(LAST, len(FIRST))
        firsts = FIRST[:]
        firsts[firsts.index("Anika")] = "Ana"       # two Anas: a first name alone is ambiguous
        firsts[firsts.index("Esme")] = "Hugo"       # two Hugos
        project_names = PROJECTS
    else:
        last = rng.sample(LAST + MORE_LAST, S["people"])
        firsts = [rng.choice(FIRST + MORE_FIRST) for _ in range(S["people"])]
        heads = rng.sample(NAME_A, S["projects"])
        project_names = [h + "-" + rng.choice(NAME_B) for h in heads]
        NICK.update(MORE_NICK)
    AMBIG.clear()
    AMBIG.update(f for f in firsts if firsts.count(f) > 1)
    people = []
    for i, (f, l) in enumerate(zip(firsts, last)):
        p = {"name": f + " " + l, "first": f, "nick": NICK.get(f), "role": rng.choice(ROLES),
             "employer": rng.choice(COMPANIES), "city": rng.choice(CITIES), "met_at": rng.choice(EVENTS),
             "met_day": weekday(rng, 0, 140), "has_note": i % 3 != 2, "introduced_by": None,
             "hobby": rng.choice(HOBBIES), "pet": rng.choice(PETS) if i % 2 == 0 else None,
             "school": rng.choice(SCHOOLS) if i % 4 == 1 else None}
        people.append(p)
    people.sort(key=lambda p: p["met_day"])
    for i, p in enumerate(people):
        if i >= 4 and rng.random() < 0.5:
            p["introduced_by"] = rng.choice(people[:i])["name"]
    byname = {p["name"]: p for p in people}

    log = []        # (day, kind, payload); the plans and the questions are both derived from it

    def ev(day, kind, **kw):
        log.append({"day": day, "kind": kind, **kw})

    for p in people:
        ev(p["met_day"], "meet", person=p["name"])
    projects = []
    for i, name in enumerate(project_names):
        start = weekday(rng, 3, 80)
        known = [p for p in people if p["met_day"] < start]
        if not known:               # a project needs an owner already met
            start = people[2]["met_day"] + 1
            known = people[:3]
        owner = rng.choice(known)
        collab = rng.sample([p for p in known if p is not owner], min(2, len(known) - 1))
        pr = {"name": name, "start_day": start, "owner": owner["name"], "lang": rng.choice(LANGS),
              "host": rng.choice(HOSTS), "deadline": d(start + rng.randint(40, 90)),
              "collaborators": [c["name"] for c in collab], "status": "active",
              "note_updated": i % 3 == 0}
        projects.append(pr)
        ev(start, "kickoff", project=name)

    history = []    # (field, entity, old, new, day) for every fact that changed
    for pr in projects:
        day = pr["start_day"]
        for _ in range(rng.choice([0, 1, 1, 2])):          # deadline slips
            day = weekday(rng, day + 7, min(day + 50, 7 * WEEKS - 2))
            new = d(dt.date.fromisoformat(pr["deadline"]).toordinal() - START.toordinal() + rng.randint(10, 35))
            history.append(("deadline", pr["name"], pr["deadline"], new, day))
            ev(day, "deadline", project=pr["name"], old=pr["deadline"], new=new)
            pr["deadline"] = new
        if rng.random() < 0.35:                            # language migration
            day2 = weekday(rng, pr["start_day"] + 10, 7 * WEEKS - 2)
            new = rng.choice([l for l in LANGS if l != pr["lang"]])
            history.append(("lang", pr["name"], pr["lang"], new, day2))
            ev(day2, "lang", project=pr["name"], old=pr["lang"], new=new)
            pr["lang"] = new
        if rng.random() < 0.35:                            # owner handoff
            day3 = weekday(rng, pr["start_day"] + 10, 7 * WEEKS - 2)
            cands = [p for p in people if p["met_day"] < day3 and p["name"] != pr["owner"]]
            new = rng.choice(cands)["name"]
            history.append(("owner", pr["name"], pr["owner"], new, day3))
            ev(day3, "owner", project=pr["name"], old=pr["owner"], new=new)
            pr["owner"] = new
        if rng.random() < 0.5:                             # status change late in the log
            day4 = weekday(rng, max(pr["start_day"] + 20, 110), 7 * WEEKS - 2)
            new = rng.choice(STATUSES)
            history.append(("status", pr["name"], "active", new, day4))
            ev(day4, "status", project=pr["name"], old="active", new=new)
            pr["status"] = new
        if rng.random() < 0.6:                             # a collaborator joins
            day5 = weekday(rng, pr["start_day"] + 5, 7 * WEEKS - 2)
            cands = [p for p in people if p["met_day"] < day5 and p["name"] not in pr["collaborators"]
                     and p["name"] != pr["owner"]]
            if cands:
                c = rng.choice(cands)["name"]
                pr["collaborators"].append(c)
                ev(day5, "join", project=pr["name"], person=c)

    for p in rng.sample(people, S["jobs"]):                # job changes
        day = weekday(rng, p["met_day"] + 14, 7 * WEEKS - 2) if p["met_day"] + 14 < 7 * WEEKS - 2 else None
        if day is None:
            continue
        new = rng.choice([c for c in COMPANIES if c != p["employer"]])
        history.append(("employer", p["name"], p["employer"], new, day))
        ev(day, "employer", person=p["name"], old=p["employer"], new=new)
        p["employer"] = new
    for p in rng.sample(people, S["moves"]):               # moves
        if p["met_day"] + 14 >= 7 * WEEKS - 2:
            continue
        day = weekday(rng, p["met_day"] + 14, 7 * WEEKS - 2)
        new = rng.choice([c for c in CITIES if c != p["city"]])
        history.append(("city", p["name"], p["city"], new, day))
        ev(day, "city", person=p["name"], old=p["city"], new=new)
        p["city"] = new
    for p in rng.sample([p for p in people if p["met_day"] < 120], S["fixes"]):   # an error, corrected later
        wrong = rng.choice([h for h in HOBBIES if h != p["hobby"]])
        day = weekday(rng, p["met_day"], p["met_day"] + 20)
        fix = weekday(rng, day + 10, 7 * WEEKS - 2)
        history.append(("hobby", p["name"], wrong, p["hobby"], fix))
        ev(day, "hobby_wrong", person=p["name"], value=wrong)
        ev(fix, "hobby_fix", person=p["name"], old=wrong, new=p["hobby"])
        p["hobby_corrected"] = True
    for p in people:                                       # touchpoints: noise and recency
        mine = [pr for pr in projects if p["name"] in pr["collaborators"] or p["name"] == pr["owner"]]
        for _ in range(rng.randint(*S["touch"])):
            if p["met_day"] + 3 >= 7 * WEEKS - 2:
                break
            day = weekday(rng, p["met_day"] + 3, 7 * WEEKS - 2)
            topic = rng.choice(mine)["name"] if mine and rng.random() < 0.4 else rng.choice(TOPICS)
            ev(day, "touch", person=p["name"], topic=topic, mode=rng.choice(["coffee", "call", "lunch", "walk"]))
        if not p.get("hobby_corrected"):
            ev(weekday(rng, p["met_day"], min(p["met_day"] + 30, 7 * WEEKS - 2)), "hobby", person=p["name"])
        if p["pet"]:
            ev(weekday(rng, p["met_day"], 7 * WEEKS - 2), "pet", person=p["name"])
        if p["school"]:
            ev(weekday(rng, p["met_day"], 7 * WEEKS - 2), "school", person=p["name"])
    if S["pulse"]:          # status mentions that repeat whatever value held on the day
        def value_at(ent, field, day, current):
            v = current
            for (f, e, old, new, dd) in sorted(history, key=lambda h: h[4], reverse=True):
                if e == ent and f == field and dd > day:
                    v = old
            return v
        for pr in projects:
            day = pr["start_day"] + rng.randint(3, 9)
            while day < 7 * WEEKS - 2:
                if (START + dt.timedelta(days=day)).weekday() < 5:
                    field = rng.choice(["deadline", "deadline", "lang", "owner"])
                    ev(day, "pulse", project=pr["name"], field=field, value=value_at(pr["name"], field, day, pr[field]))
                day += rng.randint(5, 12)
    log.sort(key=lambda e: (e["day"], e["kind"], json.dumps(e, sort_keys=True)))
    return {"seed": seed, "start": START.isoformat(), "today": TODAY.isoformat(), "people": people,
            "projects": projects, "history": history, "log": log}, rng, byname


def ref(p, rng, day_salt):
    """How a daily note names a person: full name, first name, or nickname."""
    r = random.Random(hashlib.sha1(f"{p['name']}|{day_salt}".encode()).hexdigest())
    opts = [p["name"], p["name"], p["first"]] + ([p["nick"]] * 2 if p["nick"] else [])
    if p["first"] in AMBIG:
        opts = [p["name"]]
    return r.choice(opts)


def plans(world, byname):
    """What each note must say. A fact is a sentence for the writer plus strings that must appear."""
    rng = random.Random(world["seed"] + 1)
    prj = {p["name"]: p for p in world["projects"]}
    daily = {}
    first_state = {}        # entity -> fields as first written in its note
    for e in world["log"]:
        day, k = e["day"], e["kind"]
        p = byname.get(e.get("person"))
        who = ref(p, rng, day) if p else None
        f = None
        if k == "meet":
            intro = f" {p['introduced_by']} introduced us." if p["introduced_by"] else ""
            f = (f"Met {p['name']} at {p['met_at']}. {p['first']} is a {p['role']} at {p['employer']}, "
                 f"based in {p['city']}.{intro}", [p["name"], p["met_at"], p["employer"], p["city"]]
                 + ([p["introduced_by"]] if p["introduced_by"] else []))
        elif k == "kickoff":
            pr = prj[e["project"]]
            f0 = first_state[pr["name"]] = _initial(world, pr)
            f = (f"Kicked off {pr['name']} today. {f0['owner']} owns it; it is written in {f0['lang']}, "
                 f"hosted on {pr['host']}; target date {human(f0['deadline'])}.",
                 [pr["name"], f0["owner"], f0["lang"], pr["host"], human(f0["deadline"])])
        elif k == "deadline":
            f = (f"{e['project']} deadline moved from {human(e['old'])} to {human(e['new'])}.",
                 [e["project"], human(e["new"])])
        elif k == "lang":
            f = (f"{e['project']} is being rewritten from {e['old']} in {e['new']}; the {e['old']} version is retired.",
                 [e["project"], e["new"]])
        elif k == "owner":
            f = (f"{e['old']} handed {e['project']} over to {e['new']}, who owns it from now on.",
                 [e["project"], e["new"]])
        elif k == "status":
            f = (f"{e['project']} is now {e['new']}.", [e["project"], e["new"]])
        elif k == "join":
            f = (f"{who} joined {e['project']} as a collaborator.", [who, e["project"]])
        elif k == "employer":
            f = (f"{who} left {e['old']} and now works at {e['new']}.", [who, e["new"]])
        elif k == "city":
            f = (f"{who} moved from {e['old']} to {e['new']}.", [who, e["new"]])
        elif k == "hobby_wrong":
            f = (f"{who} is really into {e['value']}.", [who, e["value"]])
        elif k == "hobby_fix":
            f = (f"Correction: {who} is into {e['new']}, not {e['old']}; I had that wrong.", [who, e["new"]])
        elif k == "hobby":
            f = (f"{who} spends weekends on {p['hobby']}.", [who, p["hobby"]])
        elif k == "pet":
            f = (f"{who}'s dog is called {p['pet']}.", [who, p["pet"]])
        elif k == "school":
            f = (f"{who} studied at {p['school']}.", [who, p["school"]])
        elif k == "pulse" and e["field"] == "deadline":
            f = (f"{e['project']}: still aiming for {human(e['value'])}.", [e["project"], human(e["value"])])
        elif k == "pulse" and e["field"] == "lang":
            f = (f"{e['project']}: an hour in the {e['value']} codebase.", [e["project"], e["value"]])
        elif k == "pulse":
            o = ref(byname[e["value"]], rng, day)
            f = (f"Checked in with {o} about {e['project']}.", [e["project"], o])
        elif k == "touch":
            f = (f"{e['mode'].capitalize()} with {who}; we talked about {e['topic']}.", [who])
        involved = [n for n in (e.get("person"), e.get("old"), e.get("new"), e.get("value"), p and p["introduced_by"] if k == "meet" else None,
                                first_state.get(e.get("project"), {}).get("owner") if k == "kickoff" else None)
                    if n in byname]
        daily.setdefault(d(day), []).append({"kind": k, "text": f[0], "must": f[1], "people": involved,
                                             "entity": e.get("person") or e.get("project")})
    people_notes = {}
    for p in world["people"]:
        if not p["has_note"]:
            continue
        intro = f"Introduced by [[{p['introduced_by']}]]." if p["introduced_by"] else ""
        init = _person_initial(world, p)
        people_notes[p["name"]] = {"created": d(p["met_day"]), "aliases": [a for a in [p["first"], p["nick"]] if a and p["first"] not in AMBIG],
                                   "text": f"{p['name']}: {p['role']} at {init['employer']}, lives in {init['city']}. "
                                           f"Met at {p['met_at']} on {human(d(p['met_day']))}. {intro}",
                                   "must": [init["employer"], init["city"], p["met_at"]]}
    project_notes = {}
    for pr in world["projects"]:
        f0 = first_state.get(pr["name"]) or _initial(world, pr)
        collab0 = [c for c in pr["collaborators"]
                   if not any(e["kind"] == "join" and e["person"] == c and e["project"] == pr["name"] for e in world["log"])]
        upd = []
        if pr["note_updated"]:
            for (field, ent, old, new, day) in world["history"]:
                if ent == pr["name"]:
                    upd.append(f"Update {d(day)}: {field} changed from {old} to {new}.")
        project_notes[pr["name"]] = {"created": d(pr["start_day"]),
                                     "text": f"{pr['name']}. Owner: {f0['owner']}. Language: {f0['lang']}. Repo on {pr['host']}. "
                                             f"Target date: {f0['deadline']}. Collaborators: {', '.join(collab0)}.",
                                     "updates": upd, "must": [f0["owner"], f0["lang"], pr["host"]] + collab0}
    return {"daily": daily, "people": people_notes, "projects": project_notes}


def _initial(world, pr):
    out = {"owner": pr["owner"], "lang": pr["lang"], "deadline": pr["deadline"]}
    for (field, ent, old, new, day) in reversed(world["history"]):
        if ent == pr["name"] and field in out:
            out[field] = old
    return out


def _person_initial(world, p):
    out = {"employer": p["employer"], "city": p["city"]}
    for (field, ent, old, new, day) in reversed(world["history"]):
        if ent == p["name"] and field in out:
            out[field] = old
    return out


def questions(world, byname, plan):
    rng = random.Random(world["seed"] + 2)
    prj = {p["name"]: p for p in world["projects"]}
    changed = {(f, e) for (f, e, *_r) in world["history"]}
    stale = {}
    for (f, e, old, new, day) in world["history"]:
        stale.setdefault((f, e), []).append(old)
    qs = []

    def q(cat, text, answer, keys, gold, stale_keys=(), mode="all"):
        qs.append({"category": cat, "question": text, "answer": answer, "keys": keys, "stale": list(stale_keys),
                   "gold": gold, "mode": mode})

    people = world["people"]
    for p in people:                                       # single: stated once, never changed
        if not p.get("hobby_corrected"):
            q("single", f"What does {p['name']} spend weekends doing?", p["hobby"], [p["hobby"]], [("hobby", p["name"])])
        if p["pet"]:
            q("single", f"What is the name of {p['name']}'s dog?", p["pet"], [p["pet"]], [("pet", p["name"])])
        if p["school"]:
            q("single", f"Where did {p['name']} study?", p["school"], [p["school"].replace("the ", "")], [("school", p["name"])])
        q("single", f"Where did I first meet {p['name']}?", p["met_at"], [_core(p["met_at"])], [("meet", p["name"])])
        if ("employer", p["name"]) not in changed and rng.random() < 0.3:
            q("single", f"What is {p['name']}'s job title?", p["role"], [p["role"]], [("meet", p["name"])])
    for pr in world["projects"]:
        q("single", f"Where is the {pr['name']} repository hosted?", pr["host"], [pr["host"]], [("kickoff", pr["name"])])
    for (f, e) in sorted(changed):                         # update: the current value after a change
        if f == "deadline":
            v = prj[e]["deadline"]
            q("update", f"What is the current deadline for {e}?", v, [date_keys(v)], [("deadline", e)],
              [date_keys(o) for o in stale[(f, e)]])
        elif f == "lang":
            q("update", f"What language is {e} written in now?", prj[e]["lang"], [prj[e]["lang"]], [("lang", e)], stale[(f, e)])
        elif f == "owner":
            q("update", f"Who owns {e} now?", prj[e]["owner"], [prj[e]["owner"]], [("owner", e)], stale[(f, e)])
        elif f == "status":
            st = prj[e]["status"]
            q("update", f"What is the current status of {e}?", st, [st + ("|" + st[3:] if st.startswith("in ") else "")],
              [("status", e)], ["active"])
        elif f == "employer":
            q("update", f"Which company does {e} work for now?", byname[e]["employer"], [byname[e]["employer"]],
              [("employer", e)], stale[(f, e)])
        elif f == "city":
            q("update", f"Which city does {e} live in now?", byname[e]["city"], [byname[e]["city"]], [("city", e)], stale[(f, e)])
        elif f == "hobby":
            q("update", f"What does {e} spend weekends doing?", byname[e]["hobby"], [byname[e]["hobby"]],
              [("hobby_fix", e)], stale[(f, e)])
    for pr in world["projects"]:                           # multihop: two facts in two notes
        o = byname[pr["owner"]]
        q("multihop", f"Which company does the current owner of {pr['name']} work for?", o["employer"], [o["employer"]],
          [("owner", pr["name"]), ("employer", o["name"])],
          stale.get(("employer", o["name"]), []))
        q("multihop", f"Which city does the current owner of {pr['name']} live in?", o["city"], [o["city"]],
          [("owner", pr["name"]), ("city", o["name"])], stale.get(("city", o["name"]), []))
    for p in people:
        if p["introduced_by"] and rng.random() < 0.6:
            i = byname[p["introduced_by"]]
            q("multihop", f"Where did I first meet the person who introduced me to {p['name']}?", i["met_at"],
              [_core(i["met_at"])], [("meet", p["name"]), ("meet", i["name"])])
    for pr in world["projects"]:                           # aggregate: every member of a set
        members = sorted(set(pr["collaborators"]))
        q("aggregate", f"Who are the collaborators on {pr['name']} (not counting the owner)?", ", ".join(members),
          members, [("kickoff", pr["name"])] + [("join", pr["name"])])
        qs[-1]["owner"] = pr["owner"]       # naming the owner as the owner is not an extra member
    for ev in sorted({p["met_at"] for p in people}):
        met = sorted(p["name"] for p in people if p["met_at"] == ev)
        if 2 <= len(met) <= 5:
            q("aggregate", f"Which people did I first meet at {ev}?", ", ".join(met), met, [("meet", m) for m in met])
    lastday = {}
    for day, facts in sorted(plan["daily"].items()):
        for f in facts:
            for n in f["people"]:
                lastday[n] = day
    for p in rng.sample(people, S["temporal"]):            # temporal: first and last contact
        if rng.random() < 0.5:
            q("temporal", f"On what date did I first meet {p['name']}?", d(p["met_day"]), [date_keys(d(p["met_day"]))], [("meet", p["name"])])
        else:
            q("temporal", f"What is the most recent date my daily notes mention {p['name']}?", lastday[p["name"]],
              [date_keys(lastday[p["name"]])], [("last", p["name"])])
    for p in rng.sample(people, S["abstain"]):             # abstention: never stated
        what = rng.choice(["phone number", "birthday", "favourite band"])
        q("abstention", f"What is {p['name']}'s {what}?", "unknown", [], [])
    for name in ["Zephyr-Lens", "Marlin-Forge", "Aspen-Relay", "Quokka-Graph", "Thistle-Cache"]:
        q("abstention", f"Who owns the {name} project?", "unknown", [], [])
    for p in people:
        if not p["school"] and rng.random() < 0.12:
            q("abstention", f"Where did {p['name']} study?", "unknown", [], [])
    singles = [x for x in qs if x["category"] == "single"]
    drop = {id(x) for x in singles} - {id(x) for x in rng.sample(singles, S["singles"])}
    qs = [x for x in qs if id(x) not in drop]
    for i, x in enumerate(qs):
        x["id"] = f"q{i:03d}"
        x["split"] = "dev" if random.Random(x["id"] + str(world["seed"])).random() < 0.3 else "test"
    return qs


def _core(event):
    return re.sub(r"^(the|a) ", "", event).replace("friend's ", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--scale", choices=sorted(SCALES), default="main")
    ap.add_argument("--out", default=os.path.join(os.environ.get("BENCH_ROOT", os.path.join(os.path.dirname(__file__), "runs", "main")), "data"))
    a = ap.parse_args()
    S.clear()
    S.update(SCALES[a.scale])
    world, rng, byname = build(a.seed)
    world["scale"] = a.scale
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "world.json"), "w") as f:
        json.dump(world, f, indent=1, sort_keys=True)
    with open(os.path.join(a.out, "plans.json"), "w") as f:
        plan = plans(world, byname)
        json.dump(plan, f, indent=1, sort_keys=True)
    qs = questions(world, byname, plan)
    with open(os.path.join(a.out, "questions.jsonl"), "w") as f:
        for x in qs:
            f.write(json.dumps(x, sort_keys=True) + "\n")
    cats = {}
    for x in qs:
        cats[x["category"]] = cats.get(x["category"], 0) + 1
    print(len(qs), "questions", cats, "events", len(world["log"]), "changes", len(world["history"]))


if __name__ == "__main__":
    main()
