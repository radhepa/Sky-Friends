"""Cloud Whale: a huge, gentle whale that swims slowly across the high sky. Sky-blue-grey above, a pale
pleated belly below, little clouds resting on its back, and faint star-like spots glowing along its
flanks after dark. It sings.

    python tools/creatures/cloud_whale.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "people"))
sys.path.insert(0, os.path.dirname(HERE))

from common import glow_as, gradient, mix, painter, ring_u, shade, tone  # noqa: E402
from mobkit import Model, Pack, faces, spawn_egg  # noqa: E402

NAME = "Cloud Whale"
BACK = ["#6f8fb5", "#6a8ab0", "#7596bb"]
FLANK = ["#8eb0d4", "#89abcf", "#94b6d9"]
BELLY = ["#eef2f7", "#e8eef5", "#f3f6fa"]
PLEAT = "#c9d5e4"
CLOUD = ["#ffffff", "#f4f7fc", "#e6edf7"]
CLOUD_SHADE = "#cdd7e8"
STAR, STAR_DIM = "#fff6c8", "#c9c39a"
EYE = "#1d2433"


def skin(depth_rows):
    """Back colour on top, shading down the flanks to the pale pleated belly; a few glowing star spots."""
    def run(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = c.pick(BACK)
                    if c.rng.random() < 0.05:
                        col = shade(col, 1.1)
                elif c.face == "bottom":
                    col = c.pick(BELLY) if x % 3 else PLEAT          # ventral pleats
                else:
                    t = y / max(1, c.h - 1)
                    col = gradient([BACK[0], FLANK[0], FLANK[1], BELLY[0]], min(1.0, t * 1.15))
                    if t > 0.72 and x % 3 == 0:
                        col = PLEAT
                    if c.rng.random() < 0.07:
                        col = shade(col, 1.06)
                c.set(x, y, col)
        if c.face in ("left", "right"):
            for _ in range(max(1, c.w // 5)):
                x, y = c.rng.randrange(c.w), c.rng.randrange(max(1, c.h // 3), max(2, c.h * 2 // 3))
                glow_as(c, x, y, STAR_DIM, STAR)
    return run


def head(c):
    skin(0)(c)
    if c.face in ("right", "left"):
        ex = 3 if c.face == "right" else c.w - 4          # eyes toward the front (front edge: right face's high x)
        ex = c.w - 4 if c.face == "right" else 3
        ey = c.h // 2 + 1
        c.set(ex, ey, EYE)
        c.set(ex + (1 if c.face == "right" else -1), ey, EYE)
        c.set(ex, ey - 1, "#ffffff")
        for x in range(c.w):                               # the long mouth line
            if (c.face == "right" and x > c.w // 3) or (c.face == "left" and x < c.w * 2 // 3):
                c.set(x, ey + 2, shade(FLANK[0], 0.75))
    if c.face == "front":
        for x in range(2, c.w - 2):
            c.set(x, c.h // 2 + 3, shade(FLANK[0], 0.75))


def cloud(c, x, y):
    if c.face == "bottom":
        return CLOUD_SHADE
    col = c.pick(CLOUD)
    if c.face != "top" and y >= c.h - 1:
        col = CLOUD_SHADE
    return col


def flipper(c, x, y):
    col = c.pick(FLANK) if c.face != "bottom" else c.pick(BELLY)
    edge = min(x, c.w - 1 - x)
    if edge == 0:
        col = shade(col, 0.85)
    return col


def fluke(c, x, y):
    col = c.pick(BACK) if c.face == "top" else c.pick(BELLY)
    if c.face in ("top", "bottom") and y >= c.h - 2 and abs(x - (c.w - 1) / 2) < 1.5:
        return None                                        # the notch
    if c.face in ("top", "bottom") and y == c.h - 1 and x % 3 == 0:
        return None
    return col


def build():
    m = Model("cloud_whale", 256, 128, seed=9)
    m.scale = 2.4
    P = Pack(m)
    body = m.part("body", (0, 8, 0))
    P.add(body, (-8, -8, -6), (16, 15, 14), faces(skin(0)))
    head_part = body.part("head", (0, 0, -6))
    P.add(head_part, (-7.5, -7.5, -13), (15, 14, 13), faces(head))
    P.add(head_part, (-6, -8.5, -10), (12, 1, 8), faces(painter(cloud)))     # a little cloud riding on its brow
    tail = body.part("tail", (0, -1, 8))
    P.add(tail, (-6.5, -6, 0), (13, 12, 11), faces(skin(0)))
    tail2 = tail.part("tail2", (0, 0, 11))
    P.add(tail2, (-4.5, -4, 0), (9, 8, 9), faces(skin(0)))
    tail3 = tail2.part("tail3", (0, 0, 9))
    P.add(tail3, (-2.5, -2.5, 0), (5, 5, 7), faces(skin(0)))
    fl = tail3.part("fluke", (0, 0, 7))
    P.add(fl, (-11, -0.5, -1), (22, 1, 9), faces(painter(fluke)))
    # clouds resting on its back
    for i, (ox, oz, w, d, h) in enumerate(((-6, -4, 9, 8, 3), (1, -1, 6, 6, 2), (-3, 3, 7, 6, 2))):
        P.add(body, (ox, -8 - h, oz), (w, h, d), faces(painter(cloud)))
    P.add(tail, (-4, -6 - 2, 2), (7, 2, 6), faces(painter(cloud)))
    for side, sx in (("right", -1), ("left", 1)):
        f = body.part(f"{side}_flipper", (7.5 * sx, 4, -2), (0.2, 0, 0.5 * -sx))
        P.add(f, (-14, -0.75, -2) if sx < 0 else (0, -0.75, -2), (14, 1.5, 6), faces(painter(flipper)), side == "left", "flipper")
    P.apply()
    m.save()


if __name__ == "__main__":
    build()
    spawn_egg("cloud_whale", "#7596bb", "#eef2f7", "#fff6c8")
    print("cloud whale")
