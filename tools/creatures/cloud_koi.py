"""Cloud Koi: little koi that swim through the air in schools round the Cirri's gardens, long wispy fins
trailing. Three colourings share one model: kohaku (white with red-orange patches and a red crown),
yamabuki (gold) and sora (sky blue under white cloud patches, the Cirri's own breed).

    python tools/creatures/cloud_koi.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "people"))
sys.path.insert(0, os.path.dirname(HERE))

from common import mix, painter, shade, tone  # noqa: E402
from mobkit import Model, Pack, faces, spawn_egg  # noqa: E402

NAME = "Cloud Koi"
EYE, GLINT = "#1d1a24", "#ffffff"

COATS = {
    "kohaku": dict(base=["#f6f3ee", "#f1ede6", "#faf8f4"], patch=["#e2553c", "#d84a33", "#e86245"], belly="#ffffff",
                   fin=["#fbe9e2", "#f7ddd2"], fin_edge="#f2b9a8", crown=True),
    "yamabuki": dict(base=["#f2c24f", "#eeba44", "#f6ca5c"], patch=["#f8d97a", "#fbe18d"], belly="#fbe7a9",
                     fin=["#f9e3a0", "#f6da8c"], fin_edge="#e3b54a", crown=False),
    "sora": dict(base=["#b9dcf3", "#b1d6ef", "#c2e2f6"], patch=["#ffffff", "#f3f8fd", "#eaf3fb"], belly="#eef6fc",
                 fin=["#eef7fd", "#e3f1fb"], fin_edge="#a9d2ee", crown=False),
}
C = COATS["kohaku"]


def scales(c, x, y):
    """The coat: scale rows, with the coat's patches (seeded per face so each colouring keeps one pattern)."""
    if c.face == "bottom":
        return C["belly"]
    col = c.pick(C["base"])
    rng = c.rng
    if rng.random() < 0.45 and C["patch"] and (x * 3 + y * 5 + c.w) % 7 < 4:
        col = c.pick(C["patch"])
    if (x + (y % 2)) % 2 == 0:
        col = shade(col, 0.95)                      # scale rows
    if c.face == "top" and C["crown"] and 1 <= x <= c.w - 2 and y <= 1:
        col = C["patch"][0]
    return tone(c, y, col, 0.12) if c.face != "top" else col


def head(c):
    painter(scales)(c)
    if c.face in ("right", "left"):
        ex = c.w - 2 if c.face == "right" else 1     # eyes toward the front
        c.set(ex, 1, EYE)
        c.set(ex, 0, GLINT if C is not COATS["sora"] else EYE)
    if c.face == "top" and C["crown"]:
        for x in range(1, c.w - 1):
            for y in range(1, c.h - 1):
                c.set(x, y, C["patch"][0])           # the tancho crown


def mouth(c, x, y):
    return shade(C["base"][0], 0.85) if c.face != "front" else mix(C["base"][0], "#d98a8a", 0.4)


def fin(c, x, y):
    """A wispy fin plane: pale, its far edge frayed away."""
    col = c.pick(C["fin"])
    if y % 3 == 0:
        col = shade(col, 0.93)                       # rays
    far = c.h - 1 - y
    if far <= 1:
        col = C["fin_edge"]
        if (x + far) % 2 == 0 and far == 0:
            return None
    return col


def tail_fin(c, x, y):
    col = c.pick(C["fin"])
    if x % 2 == 0:
        col = shade(col, 0.94)
    far = c.w - 1 - x if c.face == "right" else x
    if far >= c.w - 2:
        col = C["fin_edge"]
        if (y + far) % 3 == 0:
            return None
    return col


def build(coat, geometry=True):
    global C
    C = COATS[coat]
    m = Model("cloud_koi", 64, 32, seed=5, texture_id=f"cloud_koi_{coat}")
    m.scale = 1.0
    P = Pack(m)
    body = m.part("body", (0, 19, 0))
    P.add(body, (-2.5, -2.5, -1), (5, 5, 6), faces(painter(scales)))
    head_part = body.part("head", (0, 0, -1))
    P.add(head_part, (-2, -2, -3), (4, 4, 3), faces(head))
    P.add(head_part, (-1, -0.5, -4), (2, 1.5, 1), faces(painter(mouth)))
    dorsal = body.part("dorsal", (0, -2.5, 0))
    P.add(dorsal, (0, -3, 0), (0, 3, 5), faces(painter(tail_fin)))
    tail = body.part("tail", (0, 0, 5))
    P.add(tail, (-1.5, -1.5, 0), (3, 3, 4), faces(painter(scales)))
    tail2 = tail.part("tail2", (0, 0, 4))
    P.add(tail2, (-1, -1, 0), (2, 2, 3), faces(painter(scales)))
    fluke = tail2.part("fluke", (0, 0, 3))
    P.add(fluke, (0, -4, 0), (0, 8, 7), faces(painter(tail_fin)))
    for side, sx in (("right", -1), ("left", 1)):
        f = body.part(f"{side}_fin", (2.5 * sx, 1.5, 0), (0, 0, 0.35 * -sx))
        P.add(f, (-5, 0, -1) if sx < 0 else (0, 0, -1), (5, 0, 4), faces(painter(fin)), side == "left", "fin")
    P.apply()
    m.save(geometry=geometry)


if __name__ == "__main__":
    first = True
    for coat in COATS:
        build(coat, geometry=first)
        first = False
    spawn_egg("cloud_koi", "#f6f3ee", "#e2553c", "#b9dcf3")
    print("cloud koi:", ", ".join(COATS))
