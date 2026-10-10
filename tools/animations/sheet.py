"""Renders animation clips as a sheet of frames on the real models, offline (headless Edge, like tools/preview).

    python tools/animations/sheet.py cirri --clips stretch,weave_air          rows = clips, columns = frames
    python tools/animations/sheet.py cirri --clips stretch --frames 8 --view 90 --look cirri_male
    python tools/animations/sheet.py cirri --module everyday.py               every clip in one module
    python tools/animations/sheet.py cirri --clips stretch --mirror           as a left-hander plays it

Frames are evenly spaced from the start to the end of each clip (the first and last are the rest pose, so the
default 7 frames show 5 poses in between). The picture is the model's rest pose plus the clip, exactly as the
game adds it (the game adds the look, walk and breathing on top). Output: tools/animations/out/<people>.png
(or --out). Children: pass --look <people>_child (and clips that suit them).
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, "preview"))
sys.path.insert(0, TOOLS)
import compile as packer  # noqa: E402
import preview  # noqa: E402
from species import SPECIES, TEXTURES  # noqa: E402

OUT = os.path.join(HERE, "out")


# -- sampling: a straight port of the mod's anim.Track (monotone cubic, Fritsch-Carlson) ---------------------------
def sample(keys, t):
    times = [k[0] for k in keys]
    vals = [k[1:] for k in keys]
    n = len(times)
    if n == 1 or t <= times[0]:
        return list(vals[0])
    if t >= times[-1]:
        return list(vals[-1])
    out = []
    for c in range(3):
        sec = [(vals[k + 1][c] - vals[k][c]) / (times[k + 1] - times[k]) for k in range(n - 1)]
        m = [0.0] * n
        for k in range(1, n - 1):
            m[k] = 0.0 if sec[k - 1] * sec[k] <= 0 else (sec[k - 1] + sec[k]) / 2
        for k in range(n - 1):
            d = sec[k]
            if d == 0:
                m[k] = m[k + 1] = 0.0
                continue
            a, b = m[k] / d, m[k + 1] / d
            s = a * a + b * b
            if s > 9:
                f = 3 / math.sqrt(s)
                m[k], m[k + 1] = f * a * d, f * b * d
        k = 0
        while k < n - 2 and t >= times[k + 1]:
            k += 1
        h = times[k + 1] - times[k]
        s = (t - times[k]) / h
        s2, s3 = s * s, s * s * s
        out.append((2 * s3 - 3 * s2 + 1) * vals[k][c] + (s3 - 2 * s2 + s) * h * m[k]
                   + (-2 * s3 + 3 * s2) * vals[k + 1][c] + (s3 - s2) * h * m[k + 1])
    return out


# -- rotation maths, as ModelPart and JOML do it: R = Rz * Ry * Rx ---------------------------------------------------
def mat(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return mul(rz, mul(ry, rx))


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def euler(r):
    y = math.asin(max(-1.0, min(1.0, -r[2][0])))
    return [math.atan2(r[2][1], r[2][2]), y, math.atan2(r[1][0], r[0][0])]


def turn(part, rot_deg, pivot):
    t = mat(*(math.radians(v) for v in rot_deg))
    p = [part["pivot"][i] - pivot[i] for i in range(3)]
    p = [sum(t[i][k] * p[k] for k in range(3)) for i in range(3)]
    part["pivot"] = [p[i] + pivot[i] for i in range(3)]
    part["rotation"] = euler(mul(t, mat(*part["rotation"])))


def mirror_name(n):
    if n.startswith("right_"):
        return "left_" + n[6:]
    if n.startswith("left_"):
        return "right_" + n[5:]
    return n


def posed(geo, waist, clip, t, mirrored=False):
    geo = copy.deepcopy(geo)
    geo.pop("preview", None)   # the design previews' display pose: clips start from the model's own rest pose
    parts = {p["name"]: p for p in geo["parts"]}
    side = -1 if mirrored else 1
    w_rot, r_rot, r_pos = [0, 0, 0], [0, 0, 0], [0, 0, 0]
    for key, keys in clip["tracks"].items():
        bone, kind = key.rsplit(".", 1)
        if mirrored:
            bone = mirror_name(bone)
        x, y, z = sample(keys, t)
        if bone in ("waist", "root"):
            if kind == "rot":
                acc = w_rot if bone == "waist" else r_rot
                acc[0] += x
                acc[1] += y * side
                acc[2] += z * side
            else:
                r_pos[0] += x * side
                r_pos[1] += y
                r_pos[2] += z
            continue
        p = parts.get(bone)
        if p is None:
            continue
        if kind == "rot":
            p["rotation"] = [p["rotation"][0] + math.radians(x), p["rotation"][1] + math.radians(y * side),
                             p["rotation"][2] + math.radians(z * side)]
        else:
            p["pivot"] = [p["pivot"][0] + x * side, p["pivot"][1] + y, p["pivot"][2] + z]
    if any(w_rot):
        for name in waist["upper"]:
            if name in parts:
                turn(parts[name], w_rot, (0, waist["hip"], 0))
    top = [p for p in geo["parts"] if not p["parent"]]
    if any(r_rot):
        for p in top:
            turn(p, r_rot, (0, waist["hip"], 0))   # a Cirri turns about its hips, as the game does (it is in the air)
    for p in top:
        p["pivot"] = [p["pivot"][i] + r_pos[i] for i in range(3)]
    return geo


def page(cols):
    html = preview.PAGE
    old_cols = "const cols = Math.ceil(Math.sqrt(cells.length * W / H * 0.9)) || 1;"
    old_box = "const {obj, box} = buildMob(c.m);"
    assert old_cols in html and old_box in html, "preview.PAGE changed: update sheet.py"
    html = html.replace(old_cols, f"const cols = {cols};")
    # frame every cell on the rest pose so the model doesn't jump about between frames
    html = html.replace(old_box, "const {obj} = buildMob(c.m); const box = buildMob(Object.assign({}, c.m, {geo: c.m.rest})).box;"
                                 " box.expandByScalar(3);")
    return html


def render(payloads, cols, out_png, size):
    os.makedirs(OUT, exist_ok=True)
    html_text = (page(cols).replace("__THREE__", preview.THREE).replace("__MOBS__", json.dumps(payloads))
                 .replace("__VIEWS__", json.dumps([payloads[0].get("view", 35)])).replace("__POSES__", "{}"))
    tag = str(os.getpid())
    html = os.path.join(OUT, f"_sheet_{tag}.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(html_text)
    profile = os.path.join(OUT, f"_edge_{tag}")
    if os.path.exists(out_png):
        os.remove(out_png)
    subprocess.run([preview.EDGE, "--headless=new", "--enable-unsafe-swiftshader", "--use-angle=swiftshader",
                    "--hide-scrollbars", f"--window-size={size[0]},{size[1]}", "--virtual-time-budget=8000",
                    f"--user-data-dir={profile}", f"--screenshot={out_png}", "file:///" + html.replace("\\", "/")],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    for _ in range(300):
        if os.path.exists(out_png) and os.path.getsize(out_png) > 0:
            time.sleep(0.5)
            break
        time.sleep(0.5)
    else:
        sys.exit("sheet failed: no screenshot written")
    try:
        os.remove(html)
    except OSError:
        pass
    shutil.rmtree(profile, ignore_errors=True)
    return out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("people", choices=list(SPECIES))
    ap.add_argument("--clips", help="comma-separated clip ids")
    ap.add_argument("--module", help="every clip in this module (e.g. everyday.py)")
    ap.add_argument("--frames", type=int, default=7)
    ap.add_argument("--look", help="which model (default: the people's first look)")
    ap.add_argument("--view", type=int, default=35, help="0 front, 35 three-quarter, 90 side, 180 back")
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--cell", type=int, default=170, help="pixels per frame")
    ap.add_argument("--out")
    a = ap.parse_args()

    clips = packer.load_clips(a.people)
    if a.clips:
        wanted = a.clips.split(",")
        chosen = [c for w in wanted for c in clips if c.id == w]
        missing = set(wanted) - {c.id for c in chosen}
        if missing:
            sys.exit(f"no such clips: {', '.join(sorted(missing))}")
    elif a.module:
        chosen = [c for c in clips if getattr(c, "module", None) == a.module]
    else:
        sys.exit("pick clips with --clips or --module")
    if not chosen:
        sys.exit("no clips to draw")
    if len(chosen) * a.frames > 120:
        sys.exit(f"{len(chosen)} clips x {a.frames} frames is too many for one sheet (max 120 cells): split it up")
    look = a.look or SPECIES[a.people]["looks"][0]
    base = preview.mob_payload(look, TEXTURES.get(look))
    waist = packer.waist(a.people)
    own = packer.waist(a.people, look)
    if any("leg" in n for n in [p["name"] for p in base["geo"]["parts"] if not p["parent"]]):
        waist = dict(waist, hip=own["hip"])
    payloads = []
    for c in chosen:
        data = c.compile()
        for i in range(a.frames):
            t = data["length"] * i / (a.frames - 1)
            p = dict(base)
            p["geo"] = posed(base["geo"], waist, data, t, a.mirror)
            p["rest"] = {k: v for k, v in base["geo"].items() if k != "preview"}
            p["id"] = f"{c.id} {t:.2f}s"
            payloads.append(p)
    # the page takes one view for every cell
    preview_views = [a.view]
    payloads[0]["view"] = a.view
    out = os.path.abspath(a.out) if a.out else os.path.join(OUT, f"{a.people}.png")
    size = (a.frames * a.cell, len(chosen) * int(a.cell * 1.15))
    print(render(payloads, a.frames, out, size))
    del preview_views


if __name__ == "__main__":
    main()
