"""Cumulin (KYOO-myoo-lin), candidate B: the puff-folk who carry their own cloud.

Short, round and cheerful, named after cumulus, the big heaped fair-weather clouds. From a Cumulin's
upper back grows its billow: a living cloud of warm gas, heaped in soft lumps above its head. A
Cumulin swells its billow to rise and lets breath out of it to sink (little puffs of cloud trail
behind), and bobs through the sky like a balloon, paddling its boots and rowing with its mittens.
Two sandbags of ballast swing from its belt.

Sky-farmers and rain-makers: they herd wild clouds over thirsty land and wring the rain out of them.
They dress like balloon sailors: patched canvas coats, a knitted cap with brass goggles pushed up, a
long knitted scarf, chunky boots. About 1.5 blocks of person under about a block of cloud.
"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "people"))  # noqa: E401
from common import glow_as, gradient, mix, painter, ring_u, shade, tone
from mobkit import Model, Pack, faces

NAME = "Cumulin"

SKIN = ["#f1c9a5", "#eec3a0", "#f4cfac"]
SKIN_SHADE = "#d4a37f"
CHEEK = "#ec8f86"
HAIR = ["#c9692f", "#d17436", "#bd612b"]          # ginger tufts under the cap
EYE = "#2a2230"
EYE_HI = "#ffffff"
MOUTH = "#8c3a3a"
MOUTH_DARK = "#6a2a2e"
CANVAS = ["#c99a4a", "#c3944a", "#cfa253"]        # sail-canvas coat
CANVAS_DARK = "#93692d"
PATCH_TEAL = ["#3f8f8a", "#3a8782"]
PATCH_RED = ["#b4513e", "#aa4b3a"]
STITCH = "#5a3d1c"
BRASS = "#d39b3c"
BRASS_LIGHT = "#f4cf7a"
BRASS_DARK = "#8e6220"
GLASS = "#8fd6f0"
GLASS_HI = "#e6fbff"
KNIT_TEAL = ["#3e8d88", "#43948f", "#38837e"]
KNIT_RED = ["#c2463b", "#b84036", "#c94e42"]
CREAM = "#f3e7cf"
TROUSER = ["#5b6a7a", "#566475", "#617080"]
LEATHER = ["#7a4e2c", "#734828", "#815431"]
LEATHER_DARK = "#4c2f19"
ROPE = ["#d8c08a", "#ccb27b"]
BURLAP = ["#bfa275", "#b59869", "#c7ab7f"]
CLOUD_TOP = ["#ffffff", "#fdfcff", "#fffaf0"]
CLOUD_SIDE = ["#fbfbff", "#eeeef7", "#d9d8e8", "#c2c0d6"]   # top of a side face -> its bottom
CLOUD_UNDER = ["#aeacc4", "#a7a5be", "#b5b3ca"]
SUN = "#fff1cf"


# -- the billow ------------------------------------------------------------------------------------
def cloud(c):
    """A heap of cloud: sunlit top, sides that grey toward the bottom in soft bulges, a lilac underside."""
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CLOUD_TOP)
                if c.rng.random() < 0.08:
                    col = SUN
                c.set(x, y, col)
        return
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CLOUD_UNDER)
                edge = min(x, y, c.w - 1 - x, c.h - 1 - y)
                if edge == 0:
                    col = mix(col, CLOUD_SIDE[3], 0.5)
                c.set(x, y, col)
        return
    # sides: rounded bulges, each lit on top and shaded underneath
    bumps = [(c.rng.uniform(0, c.w), c.rng.uniform(c.h * 0.25, c.h * 0.9), c.rng.uniform(2.0, 3.6))
             for _ in range(max(2, c.w // 3))]
    for y in range(c.h):
        for x in range(c.w):
            t = y / max(1, c.h - 1)
            col = gradient(CLOUD_SIDE, t * 0.85)
            for (bx, by, r) in bumps:
                d = ((x - bx) ** 2 + (y - by) ** 2) ** 0.5
                if r - 1.1 < d <= r and y > by:
                    col = shade(col, 0.93)               # the shadowed underside of a bulge
                elif d <= r * 0.55 and y < by:
                    col = mix(col, "#ffffff", 0.45)       # its sunlit crown
            if y == 0:
                col = mix(col, "#ffffff", 0.6)
            c.set(x, y, col)


def stalk(c, x, y):
    """Where the billow grows from the back: cloud at the top, a soft pale root below."""
    t = y / max(1, c.h - 1)
    if c.face == "top":
        return CLOUD_SIDE[1]
    if c.face == "bottom":
        return mix(SKIN_SHADE, CLOUD_UNDER[0], 0.5)
    return mix(gradient(CLOUD_SIDE, 0.3 + t * 0.6), SKIN[0], max(0.0, t - 0.55) * 1.6)


# -- head ------------------------------------------------------------------------------------------
def front_dist(c, x):
    return c.w - 1 - x if c.face == "right" else x


def head(c):
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, c.pick(SKIN), 0.06))
        for x in (0, 1, 7, 8):
            c.set(x, 1, c.pick(HAIR))                     # tufts escaping the cap
        c.set(0, 2, HAIR[2])
        c.set(8, 2, HAIR[2])
        for x in (2, 3, 5, 6):
            c.set(x, 2, shade(HAIR[0], 0.8))              # ginger brows
        for ex in (2, 5):                                 # big round eyes with a shine
            c.set(ex, 3, EYE_HI)
            c.set(ex + 1, 3, EYE)
            c.set(ex, 4, EYE)
            c.set(ex + 1, 4, EYE)
        c.set(4, 4, SKIN_SHADE)                           # button nose
        c.set(4, 5, mix(SKIN[0], CHEEK, 0.5))
        for x in (1, 7):
            c.set(x, 5, CHEEK)
        c.set(1, 4, mix(SKIN[0], CHEEK, 0.4))
        c.set(7, 4, mix(SKIN[0], CHEEK, 0.4))
        c.set(3, 6, MOUTH_DARK)                           # a wide grin
        c.set(4, 6, MOUTH)
        c.set(5, 6, MOUTH_DARK)
        c.set(2, 5, shade(SKIN[0], 0.92))
        c.set(6, 5, shade(SKIN[0], 0.92))
        return
    if c.face in ("right", "left"):
        for y in range(c.h):
            for x in range(c.w):
                d = front_dist(c, x)
                hair = (d >= 4 and y <= 5) or (d >= 2 and y <= 1)
                c.set(x, y, c.pick(HAIR) if hair else tone(c, y, c.pick(SKIN), 0.08))
        ear = c.w - 1 - 3 if c.face == "right" else 3
        c.set(ear, 3, SKIN_SHADE)
        c.set(ear, 4, mix(SKIN[0], CHEEK, 0.35))
        return
    if c.face == "back":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(HAIR) if y <= 5 else tone(c, y, c.pick(SKIN), 0.1))
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(HAIR) if c.face == "top" else SKIN_SHADE)


def cap(c):
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "bottom":
                c.clear(x, y)
                continue
            col = c.pick(KNIT_TEAL)
            if c.face == "top":
                if (x + y) % 3 == 0:
                    col = shade(col, 0.9)
            else:
                if y == c.h - 1:
                    col = CREAM if (x + ring_u(c, 9, 8)) % 2 else shade(CREAM, 0.9)   # turned-up brim
                elif x % 2 == 0:
                    col = shade(col, 0.88)                # knit ribs
            c.set(x, y, col)


def goggles(c):
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "front":
                if x in (1, 2) or x in (5, 6):
                    col = GLASS_HI if (x in (1, 5) and y == 0) else GLASS
                elif x in (3, 4):
                    col = BRASS_LIGHT if y == 0 else BRASS
                else:
                    col = LEATHER_DARK
                c.set(x, y, col)
            elif c.face in ("top", "bottom"):
                c.set(x, y, BRASS_DARK)
            else:
                c.set(x, y, LEATHER_DARK)
    if c.face == "front":
        for x in (0, 3, 4, 7):
            c.set(x, 1, BRASS_DARK)


# -- coat and kit ----------------------------------------------------------------------------------
def patchwork(w, d, belt_row=None, buttons=False, hem=False):
    def run(c):
        if c.face in ("top", "bottom"):
            c.fill(CANVAS_DARK)
            return
        patches = []
        rng = c.rng
        for _ in range(1 if c.w < 6 else 2):
            pw, ph = rng.randint(2, 3), rng.randint(2, 3)
            patches.append((rng.randint(0, max(0, c.w - pw)), rng.randint(0, max(0, c.h - ph - 1)), pw, ph,
                            rng.choice((PATCH_TEAL, PATCH_RED))))
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CANVAS)
                if (x + ring_u(c, w, d) + y) % 4 == 0:
                    col = shade(col, 0.94)
                for (px, py, pw, ph, pal) in patches:
                    if px <= x < px + pw and py <= y < py + ph:
                        edge = x in (px, px + pw - 1) or y in (py, py + ph - 1)
                        col = shade(pal[0], 0.85) if edge and (x + y) % 2 else rng.choice(pal)
                if belt_row is not None and belt_row <= y <= belt_row + 1:
                    col = ROPE[0] if (x + y) % 2 else ROPE[1]
                if hem and y == c.h - 1:
                    col = CANVAS_DARK
                c.set(x, y, tone(c, y, col, 0.12))
        if buttons and c.face == "front":
            mid = c.w // 2
            for y in range(1, c.h - 1, 2):
                if belt_row is None or not belt_row <= y <= belt_row + 1:
                    c.set(mid, y, BRASS_LIGHT if y == 1 else BRASS)
        if belt_row is not None and c.face == "front":
            k = c.w // 2 - 1
            c.set(k, belt_row, STITCH)
            c.set(k, belt_row + 1, ROPE[1])
    return run


def scarf(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(KNIT_RED)
            if c.face in ("top", "bottom"):
                col = shade(col, 0.9 if c.face == "top" else 0.75)
            elif (x + ring_u(c, 9, 9)) % 4 == 0:
                col = CREAM
            c.set(x, y, col)


def scarf_tail(c):
    for y in range(c.h):
        for x in range(c.w):
            if y >= c.h - 1 and x % 2 == 1:
                c.clear(x, y)                             # fringe
                continue
            col = CREAM if y % 3 == 1 else c.pick(KNIT_RED)
            c.set(x, y, col if c.face == "front" else shade(col, 0.88))


def sleeve(c, x, y):
    if c.face == "top":
        return CANVAS_DARK
    if c.face == "bottom":
        return KNIT_RED[0]
    if y == c.h - 1:
        return PATCH_TEAL[0] if (x + ring_u(c, 3, 3)) % 2 else PATCH_TEAL[1]
    col = c.pick(CANVAS)
    if c.face == "right" and y == 1 and x == 1:
        col = PATCH_RED[0]                                 # an elbow patch
    return tone(c, y, col, 0.12)


def mitten(c, x, y):
    if c.face == "top":
        return CREAM
    col = c.pick(KNIT_RED)
    if y == 0:
        col = CREAM if (x + ring_u(c, 4, 4)) % 2 else shade(CREAM, 0.9)
    elif (x + y) % 3 == 0:
        col = shade(col, 0.9)
    return tone(c, y, col, 0.12)


def trouser(c, x, y):
    if c.face in ("top", "bottom"):
        return shade(TROUSER[0], 0.8)
    col = c.pick(TROUSER)
    if (x + ring_u(c, 4, 4)) % 4 == 0:
        col = shade(col, 0.9)
    return tone(c, y, col, 0.1)


def boot(c, x, y):
    if c.face == "bottom":
        return LEATHER_DARK
    if c.face == "top":
        return shade(LEATHER[0], 0.85) if 1 <= x <= c.w - 2 and 1 <= y <= c.h - 2 else LEATHER[0]
    if y == c.h - 1:
        return LEATHER_DARK                                # sole
    col = c.pick(LEATHER)
    if y == 0:
        col = shade(col, 1.12)                             # the turned-down cuff
    if c.face == "front" and y in (1, 2) and x in (1, 3):
        col = CREAM                                        # laces
    if c.face in ("left", "right") and y == 1:
        col = BRASS if x == c.w // 2 else LEATHER_DARK     # buckle strap
    return tone(c, y, col, 0.1)


def cord(c, x, y):
    return ROPE[(x + y) % 2]


def sandbag(c, x, y):
    if c.face == "top":
        return shade(BURLAP[0], 0.85) if x == 1 and y == 1 else BURLAP[1]
    col = c.pick(BURLAP)
    if c.face in ("front", "back", "left", "right") and (x == y or x == c.w - 1 - y):
        col = STITCH if c.face == "front" else shade(col, 0.85)      # stitched X
    return tone(c, y, col, 0.15)


def build():
    m = Model("cumulin", 128, 128, seed=33)
    m.scale = 0.82                                   # a short, round people
    m.preview = {"right_arm": [0, 0, 0.35], "left_arm": [0, 0, -0.35]}
    P = Pack(m)

    body = m.part("body", (0, 15, 0))
    P.add(body, (-5, -10, -4), (10, 10, 8), faces(patchwork(10, 8, belt_row=7, buttons=True)))
    P.add(body, (-4, -8, -5), (8, 6, 1), faces(patchwork(8, 1, buttons=True)))
    P.add(body, (-5.5, -1, -4.5), (11, 3, 9), faces(patchwork(11, 9, hem=True)))
    P.add(body, (-4.5, -11, -4.5), (9, 2, 9), faces(scarf))
    tail = body.part("scarf_tail", (2.5, -9.5, -4.6), (0.05, 0, -0.1))
    P.add(tail, (-1, 0, 0), (2, 7, 0), faces(scarf_tail))

    head_part = body.part("head", (0, -10, 0))
    P.add(head_part, (-4.5, -8, -4), (9, 8, 8), faces(head))
    P.add(head_part, (-4.5, -9.5, -4), (9, 2.5, 8), faces(cap), inflate=0.35)
    P.add(head_part, (-4, -8.6, -4.9), (8, 2, 1), faces(goggles))

    billow = body.part("billow", (0, -9, 5.5))
    P.add(billow, (-1.5, -12, -1.5), (3, 12, 3), faces(painter(stalk)))
    for origin, size in (((-7, -25, -8.5), (14, 10, 12)),      # the heart of the heap
                         ((5, -22, -7), (6, 7, 9)),            # left shoulder of cloud
                         ((-11, -21, -6), (5, 6, 8)),          # right shoulder
                         ((-4, -30, -6), (8, 5, 8)),           # crown
                         ((2, -28, -4), (5, 3, 5)),            # a little crown puff
                         ((-5, -21, 2.5), (10, 6, 4)),         # trailing back
                         ((-4, -20, -10.5), (8, 4, 2))):       # brow, out over the face
        P.add(billow, origin, size, faces(cloud))

    for side, sx in (("right", -1), ("left", 1)):
        mirror = side == "left"
        arm = body.part(f"{side}_arm", (6 * sx, -8, 0), (0, 0, -0.12 * sx))
        P.add(arm, (-1.5, -1, -1.5), (3, 5, 3), faces(painter(sleeve)), mirror, "sleeve")
        P.add(arm, (-2, 4, -2), (4, 3, 4), faces(painter(mitten)), mirror, "mitten")

        leg = body.part(f"{side}_leg", (2.5 * sx, 2, 0))
        P.add(leg, (-2, 0, -2), (4, 3, 4), faces(painter(trouser)), mirror, "trouser")
        P.add(leg, (-2.5, 3, -3), (5, 4, 5), faces(painter(boot)), mirror, "boot")

        bag = body.part(f"{side}_sandbag", (5.3 * sx, -2, 0))
        P.add(bag, (-0.5, 0, -0.5), (1, 3, 1), faces(painter(cord)), mirror, "cord")
        P.add(bag, (-1.5, 3, -1.5), (3, 3, 3), faces(painter(sandbag)), mirror, "bag")

    P.apply()
    m.save()


if __name__ == "__main__":
    build()
