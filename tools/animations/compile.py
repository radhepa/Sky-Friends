"""Compiles and checks the peoples' animation packs (docs/ANIMATIONS.md).

    python tools/animations/compile.py                 compile tools/animations/<people>/*.py for every people
    python tools/animations/compile.py cirri            one people
    python tools/animations/compile.py --check         validate, and confirm the JSON in the mod is current
    python tools/animations/compile.py --list cirri     every clip: trigger, length, requirements
    python tools/animations/compile.py --parts cirri    the model parts each look of the people has

Each people's clips are authored in tools/animations/<people>/*.py with kit.py and compiled to
src/main/resources/assets/<mod>/folk_animations/<people>.json (never hand-edit that). A pack names its waist: the
hip height and the parts that bend with the upper body, worked out from the people's main model.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402
from species import MOD_ID, SPECIES, GEOMETRY_DIRS, TAGS, MIN_CLIPS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "src", "main", "resources", "assets", MOD_ID, "animations")
MAX_ROT, MAX_POS, MAX_LEN = 400, 16, 30


def geometry(look):
    for d in GEOMETRY_DIRS:
        path = os.path.join(ROOT, d, look + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(f"no geometry for {look}")


def parts_of(look):
    return [p["name"] for p in geometry(look)["parts"]]


def waist(species, look=None):
    """The hips (where legs hang from, or the bottom of the body) and the top-level parts above them. The pack
    keeps the main look's; the game (and sheet.py) bends every model at its own legs, when it has any."""
    geo = geometry(look or SPECIES[species]["looks"][0])
    top = [p for p in geo["parts"] if not p["parent"]]
    legs = [p for p in top if "leg" in p["name"]]
    if legs:
        hip = min(p["pivot"][1] for p in legs)
    else:
        body = next(p for p in top if p["name"] == "body")
        hip = body["pivot"][1] + max(c["from"][1] + c["size"][1] for c in body["cubes"])
    return {"hip": round(hip, 3), "upper": [p["name"] for p in top if p not in legs]}


def load_clips(species):
    folder = os.path.join(HERE, species)
    clips = []
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not name.endswith(".py") or name.startswith("_"):
            continue
        kit.CLIPS.clear()
        spec = importlib.util.spec_from_file_location(f"{species}_{name[:-3]}", os.path.join(folder, name))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for c in kit.CLIPS:
            c.module = name
        clips += kit.CLIPS
        kit.CLIPS.clear()
    return clips


def tag_ok(species, tag):
    return tag in TAGS["common"] or tag in TAGS.get(species, ()) or any(
        tag.startswith(p) and tag[len(p):] in vals for p, vals in TAGS.get(species + ":prefixed", {}).items())


def check(species, clips):
    problems = []
    known = set()
    for look in SPECIES[species]["looks"]:
        known |= set(parts_of(look))
    known |= {"waist", "root"}
    seen = set()
    motions = set()
    for c in clips:
        where = f"{species}/{getattr(c, 'module', '?')}: {c.id}"
        if c.id in seen:
            problems.append(f"{where}: duplicate clip id")
        seen.add(c.id)
        if not c.id.replace("_", "").isalnum() or c.id != c.id.lower():
            problems.append(f"{where}: ids are lowercase words with underscores")
        if not 0 < c.length <= MAX_LEN:
            problems.append(f"{where}: length must be 0..{MAX_LEN}")
        if sum(c.blend) > c.length:
            problems.append(f"{where}: blends longer than the clip")
        if not c.channels:
            problems.append(f"{where}: no keys")
        for part in c.parts():
            if part not in known:
                problems.append(f"{where}: no part {part!r} in any {species} model (see --parts)")
        for (part, kind), keys in c.channels.items():
            for t, v in keys.items():
                limit = MAX_ROT if kind == "rot" else MAX_POS
                if any(abs(x) > limit for x in v):
                    problems.append(f"{where}: {part}.{kind} at {t}: {v} beyond +-{limit}")
        for group in c.require:
            for tag in group.split("|"):
                if not tag_ok(species, tag):
                    problems.append(f"{where}: unknown tag {tag!r} in require")
        for tag in list(c.avoid) + list(c.boost):
            if not tag_ok(species, tag):
                problems.append(f"{where}: unknown tag {tag!r}")
        motions.add(json.dumps(sorted((f"{p}.{k}", sorted(v.items())) for (p, k), v in c.channels.items())))
    return problems, len(motions)


def coverage(species, clips):
    """Every moment needs something to play, for grown-ups and (where the people has them) children."""
    problems = []
    ages = ["adult", "child"] if SPECIES[species].get("children", True) else ["adult"]
    def fits(tag, age):
        if tag in ("adult", "child"):
            return tag == age
        if age == "child":
            return not (tag.startswith("job:") and tag != "job:child" or tag.startswith("rank:") or tag == "working")
        return tag != "job:child"

    for trigger in sorted(kit.TRIGGERS):
        for age in ages:
            ok = [c for c in clips if c.trigger == trigger and age not in c.avoid
                  and all(any(fits(t, age) for t in group.split("|")) for group in c.require)]
            if not ok:
                problems.append(f"{species}: nothing for {age}s to play on {trigger!r}")
    return problems


def pack(species, clips):
    return {"format": 1, "species": species, "name": SPECIES[species]["name"], "waist": waist(species),
            "clips": [c.compile() for c in clips]}


def dump(data):
    """One clip per block, tracks one per line: diffs stay readable."""
    head = {k: v for k, v in data.items() if k != "clips"}
    lines = ["{"] + [f"  {json.dumps(k)}: {json.dumps(v)}," for k, v in head.items()] + ['  "clips": [']
    for i, c in enumerate(data["clips"]):
        meta = {k: v for k, v in c.items() if k != "tracks"}
        lines.append("    " + json.dumps(meta)[:-1] + ', "tracks": {')
        tracks = list(c["tracks"].items())
        for j, (k, v) in enumerate(tracks):
            lines.append(f"      {json.dumps(k)}: {json.dumps(v)}" + ("," if j < len(tracks) - 1 else ""))
        lines.append("    }}" + ("," if i < len(data["clips"]) - 1 else ""))
    lines += ["  ]", "}"]
    return "\n".join(lines) + "\n"


def main(argv):
    flags = {a for a in argv if a.startswith("--")}
    names = [a for a in argv if not a.startswith("--")] or list(SPECIES)
    if "--parts" in flags:
        for s in names:
            for look in SPECIES[s]["looks"]:
                print(f"{s} / {look}: {' '.join(parts_of(look))}")
            print(f"{s} waist: {waist(s)}")
        return 0
    bad = 0
    for s in names:
        if s not in SPECIES:
            print(f"unknown people {s}")
            return 2
        clips = load_clips(s)
        problems, motions = check(s, clips)
        problems += coverage(s, clips) if clips else []
        if "--list" in flags:
            for c in clips:
                req = f" require={c.require}" if c.require else ""
                print(f"  {c.id:32} {c.trigger:12} {c.length:5.2f}s w{c.weight}{req}  {c.name}")
        by_trigger = {}
        for c in clips:
            by_trigger[c.trigger] = by_trigger.get(c.trigger, 0) + 1
        summary = ", ".join(f"{t} {n}" for t, n in sorted(by_trigger.items()))
        short = motions < MIN_CLIPS
        print(f"{s}: {len(clips)} clips, {motions} distinct motions" + (f" (want {MIN_CLIPS})" if short else "")
              + (f", {len(problems)} problems" if problems else ", ok") + (f"  [{summary}]" if summary else ""))
        for p in problems[:60]:
            print("   ", p)
        bad += len(problems)
        path = os.path.join(OUT, s + ".json")
        text = dump(pack(s, clips))
        if "--check" in flags:
            current = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if clips and current != text:
                print(f"    {os.path.relpath(path, ROOT)} is out of date: run compile.py {s}")
                bad += 1
            if short:
                bad += 1
        elif not problems and clips:
            os.makedirs(OUT, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
