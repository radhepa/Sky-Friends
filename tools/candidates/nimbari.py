"""Nimbari (nim-BAR-ee), candidate C: the storm-tails.

Named after nimbus, the dark rain cloud. Human from the waist up; below the waist, a long finned tail
of storm-slate scales, longer than they are tall. They swim through the sky the way eels swim through
water: a wave runs down the tail and pushes them along, mane and whiskers streaming back. Hovering,
the torso stands upright and the tail hangs in a slow S beneath. Lightning lives in their fins: the
veins glow white-blue and flare before a strike.

Proud wardens of the high air who hunt Phantoms and follow thunderstorms. Swept-back dark horns ringed
with copper, a pale storm-grey mane, long whisker-barbels, glowing storm-gold eyes, copper gorget and
bracers greening with age, a rain-blue sash. About 2 blocks of torso and head over 2.3 blocks of tail.
"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "people"))  # noqa: E401
from common import glow_as, gradient, mix, painter, ring_u, shade, tone
from mobkit import Model, Pack, faces

NAME = "Nimbari"

SCALE = ["#5b6f86", "#566a80", "#61758c"]
SCALE_LIGHT = "#8195ab"
SCALE_DARK = "#3c4b5f"
BELLY = ["#a9b6c4", "#a3b0be", "#b0bcc9"]
BELLY_LINE = "#8592a3"
SKIN = ["#8d9cae", "#8797a9", "#93a2b3"]       # the face and hands: smoother, paler slate
SKIN_SHADE = "#6c7b8d"
MANE = ["#d9e0e8", "#cfd7e0", "#e3e8ee"]
MANE_SHADE = "#9aa6b5"
HORN = ["#2b2f3a", "#262a34", "#30353f"]
HORN_TIP = "#4b5161"
EYE = "#ffd35a"
EYE_HOT = "#fff3b8"
EYE_DEEP = "#b5851f"
COPPER = ["#c4733f", "#bd6c3a", "#cb7a45"]
COPPER_LIGHT = "#e8a06b"
COPPER_DARK = "#8a4a26"
VERDIGRIS = ["#4fa58a", "#5bb197", "#46997f"]
SASH = ["#2c3e66", "#2a3a60", "#30446d"]
SASH_LIGHT = "#4c6496"
CLAW = "#20232b"
FIN = ["#7a8ea6", "#71859d", "#8297ae"]
FIN_DARK = "#4a5a70"
BOLT = "#bff3ff"
BOLT_DIM = "#5fb7d9"


def front_dist(c, x):
    return c.w - 1 - x if c.face == "right" else x


def scales(c, x, y, w, d, belly=False):
    """Overlapping scale rows on the back and sides; pale ridged plates down the front."""
    if belly and c.face == "front" and 0 < x < c.w - 1:
        col = c.pick(BELLY)
        if y % 3 == 2:
            col = BELLY_LINE
        return col
    u = x + ring_u(c, w, d)
    col = c.pick(SCALE)
    if (u + (y // 2) * 2) % 4 == 0 and y % 2 == 0:
        col = SCALE_LIGHT                                # each scale's lit edge
    elif y % 2 == 1 and u % 2 == 0:
        col = SCALE_DARK
    return tone(c, y, col, 0.08)


# -- head ------------------------------------------------------------------------------------------
def head(c):
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, c.pick(SKIN), 0.05))
        for x in range(8):
            c.set(x, 0, c.pick(MANE))                     # mane at the brow
        c.set(0, 1, MANE[0])
        c.set(7, 1, MANE[0])
        for x in (1, 2, 5, 6):                            # heavy brow ridge
            c.set(x, 2, SCALE_DARK)
        c.set(3, 2, SKIN_SHADE)
        c.set(4, 2, SKIN_SHADE)
        for ex, inner in ((1, 2), (5, 5)):                # narrow glowing eyes
            c.set(ex, 3, EYE_DEEP)
            c.set(ex + 1, 3, EYE_DEEP)
        glow_as(c, 2, 3, EYE_DEEP, EYE_HOT)
        glow_as(c, 1, 3, EYE_DEEP, EYE)
        glow_as(c, 5, 3, EYE_DEEP, EYE_HOT)
        glow_as(c, 6, 3, EYE_DEEP, EYE)
        c.set(3, 4, SKIN_SHADE)                           # a long straight nose
        c.set(3, 5, SKIN_SHADE)
        c.set(4, 5, SCALE_DARK)
        for x in (0, 7):                                  # scale marks on the cheekbones
            c.set(x, 4, SCALE[0])
            c.set(x, 5, SCALE_LIGHT)
        c.set(2, 6, SCALE_DARK)                           # a stern mouth
        c.set(3, 6, SCALE_DARK)
        c.set(4, 6, SCALE_DARK)
        c.set(5, 6, SKIN_SHADE)
        for x in range(2, 6):
            c.set(x, 7, SKIN_SHADE)                       # strong jaw
        return
    if c.face in ("right", "left"):
        for y in range(c.h):
            for x in range(c.w):
                d = front_dist(c, x)
                if d >= 4 or y == 0:
                    col = c.pick(MANE) if (x + y) % 4 else MANE_SHADE
                else:
                    col = tone(c, y, c.pick(SKIN), 0.06)
                    if d >= 2 and y >= 4:
                        col = SCALE[0] if (x + y) % 2 else SCALE_LIGHT    # scaled jaw and neck
                c.set(x, y, col)
        fin = c.w - 1 - 3 if c.face == "right" else 3
        c.set(fin, 3, FIN_DARK)                           # a small fin-ear
        c.set(fin, 4, FIN[0])
        return
    if c.face == "back":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, MANE_SHADE if (x + y) % 3 == 0 else c.pick(MANE))
        return
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(MANE) if y >= 2 or x in (0, 7) else MANE_SHADE)
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, SKIN_SHADE if y < 5 else MANE_SHADE)


def horn(c, x, y):
    if y == 0 and c.face != "bottom":
        return HORN_TIP
    col = c.pick(HORN)
    if c.face in ("front", "left") and (y % 3 == 1):
        col = shade(col, 1.25)                            # growth rings
    return col


def horn_ring(c, x, y):
    return COPPER_LIGHT if (x + y) % 2 == 0 else c.pick(COPPER)


def mane(c, x, y):
    col = c.pick(MANE)
    if c.face in ("back", "front") and x % 2 == 1:
        col = MANE_SHADE if c.face == "back" else shade(col, 0.92)
    if y >= c.h - 2 and x % 2 == 0 and c.face in ("back", "front"):
        col = mix(col, "#ffffff", 0.4)
    return tone(c, y, col, 0.1)


def whisker(c, x, y):
    return MANE[0] if y % 2 == 0 else MANE_SHADE


# -- torso -----------------------------------------------------------------------------------------
def chest(c):
    w, d = 9, 6
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top":
                c.set(x, y, SCALE_DARK)
                continue
            if c.face == "bottom":
                c.set(x, y, SCALE_DARK)
                continue
            col = scales(c, x, y, w, d, belly=True)
            if c.face == "front" and x in (0, c.w - 1):
                col = SCALE[1]
            c.set(x, y, col)
    if c.face == "front":                                 # the sash across the chest, right shoulder to left hip
        for y in range(c.h):
            x0 = int(y * 1.3)
            for x in (x0, x0 + 1):
                if 0 <= x < c.w:
                    c.set(x, y, SASH_LIGHT if x == x0 else c.pick(SASH))
    if c.face == "back":                                  # lightning running down the spine
        mid = c.w // 2
        for y, dx in ((1, 0), (2, 1), (3, 0), (4, -1), (5, 0), (6, 1)):
            if y < c.h:
                glow_as(c, mid + dx, y, BOLT_DIM, BOLT)


def abdomen(c, x, y):
    if c.face in ("top", "bottom"):
        return SCALE_DARK
    return scales(c, x, y, 7, 5, belly=True)


def gorget(c, x, y):
    if c.face == "bottom":
        return COPPER_DARK
    if c.face == "top":
        edge = min(x, y, c.w - 1 - x, c.h - 1 - y)
        return COPPER_LIGHT if edge == 0 else c.pick(COPPER)
    col = c.pick(COPPER)
    if y == 0:
        col = COPPER_LIGHT
    if (x * 7 + y * 3 + ring_u(c, 10, 7)) % 5 == 0:
        col = c.pick(VERDIGRIS)                           # green where the rain has got at it
    return col


def gorget_stone(c):
    painter(gorget)(c)
    if c.face == "front":
        glow_as(c, 4, 1, BOLT_DIM, BOLT)
        glow_as(c, 5, 1, BOLT_DIM, BOLT)


def ridge_fin(c, x, y):
    """Thin back fin: dark membrane between pale spines."""
    col = FIN[0] if y % 3 else FIN_DARK
    if x == 0:
        col = SCALE_LIGHT
    return col


# -- arms ------------------------------------------------------------------------------------------
def upper_arm(c, x, y):
    if c.face in ("top", "bottom"):
        return SCALE_DARK
    return scales(c, x, y, 3, 3)


def pauldron(c, x, y):
    if c.face == "bottom":
        return COPPER_DARK
    col = c.pick(COPPER)
    if c.face == "top":
        return COPPER_LIGHT if (x + y) % 3 == 0 else col
    if y == c.h - 1:
        col = COPPER_DARK
    elif (x + y) % 4 == 0:
        col = c.pick(VERDIGRIS)
    return col


def forearm(c, x, y):
    if c.face in ("top", "bottom"):
        return SKIN_SHADE
    return tone(c, y, c.pick(SKIN), 0.1)


def bracer(c, x, y):
    if c.face in ("top", "bottom"):
        return COPPER_DARK
    col = c.pick(COPPER)
    if y == 1:
        col = COPPER_LIGHT if (x + ring_u(c, 4, 4)) % 2 else COPPER_DARK
    elif (x + y * 2) % 5 == 0:
        col = c.pick(VERDIGRIS)
    return col


def hand(c, x, y):
    if y == c.h - 1 and c.face in ("front", "left", "right"):
        return CLAW if x % 2 == 0 else SKIN_SHADE
    if c.face == "bottom":
        return CLAW
    return tone(c, y, c.pick(SKIN), 0.1)


# -- tail ------------------------------------------------------------------------------------------
TAIL = ((7, 5, 7), (6, 5, 7), (5, 4, 6), (4, 4, 6), (3, 3, 5), (2, 2, 5))   # width, depth, length per segment
TAIL_LEN = sum(s[2] for s in TAIL)


def tail_seg(index, sash=False):
    w, d, length = TAIL[index]
    start = sum(s[2] for s in TAIL[:index])

    def run(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    c.set(x, y, SCALE_DARK)
                    continue
                if c.face == "bottom":
                    c.set(x, y, SCALE[0] if index < len(TAIL) - 1 else FIN_DARK)
                    continue
                col = scales(c, x, y, w, d, belly=True)
                t = (start + y) / TAIL_LEN
                col = mix(col, SCALE_DARK, t * 0.35) if c.face != "front" else col
                if sash and y <= 1:
                    col = SASH_LIGHT if y == 0 else c.pick(SASH)
                c.set(x, y, col)
        if c.face in ("left", "right") and index % 2 == 0:  # a glowing vein along the flank
            yy = min(c.h - 1, 2 + index % 3)
            glow_as(c, c.w // 2, yy, BOLT_DIM, BOLT)
    return run


def dorsal(index):
    """The dorsal fin along each tail segment (a plane facing sideways), veined with lightning."""
    def run(c):
        for y in range(c.h):
            for x in range(c.w):
                # x: 0 at the root of the fin (against the back) on one side; the planes are mirrored
                d = front_dist(c, x)
                edge = d == c.w - 1
                if edge and (y + index) % 3 == 2:
                    c.clear(x, y)                         # notched trailing edge
                    continue
                col = FIN[(x + y) % 3] if not edge else FIN_DARK
                if y % 3 == 0:
                    col = SCALE_LIGHT                     # spines
                c.set(x, y, col)
        # the lightning vein zig-zags through the fin
        for y in range(c.h):
            d = 1 if (y + index) % 4 < 2 else 0
            x = (c.w - 1 - d) if c.face == "right" else d
            if c.inside(x, y):
                glow_as(c, x, y, BOLT_DIM, BOLT)
    return run


def tuft(c, x, y):
    """The storm-hair tuft at the tail's tip, lightning flickering in it."""
    col = c.pick(MANE) if (x + y) % 3 else MANE_SHADE
    if c.face == "top":
        return MANE_SHADE
    if y >= c.h - 2 and c.face != "bottom" and (x + y) % 2 == 0:
        return None                                        # wispy ends
    return tone(c, y, col, 0.15)


def tuft_bolts(c):
    painter(tuft)(c)
    if c.face in ("front", "back"):
        for y, x in ((1, 1), (2, 2), (3, 1), (4, 0)):
            if c.inside(x, y):
                glow_as(c, x, y, BOLT_DIM, BOLT)


def build():
    m = Model("nimbari", 128, 64, seed=44)
    m.preview = {"right_arm": [0, 0, 0.25], "left_arm": [-0.3, 0, -0.3], "left_forearm": [-0.6, 0, 0],
                 "tail1": [0.2, 0, 0], "tail2": [0.35, 0, 0], "tail3": [-0.45, 0, 0], "tail4": [-0.55, 0, 0],
                 "tail5": [0.4, 0, 0], "tail6": [0.6, 0, 0]}
    P = Pack(m)

    body = m.part("body", (0, 8, 0))
    P.add(body, (-4.5, -12, -3), (9, 7, 6), faces(chest))
    P.add(body, (-3.5, -5, -2.5), (7, 5, 5), faces(painter(abdomen)))
    P.add(body, (-5, -13, -3.5), (10, 2, 7), faces(gorget_stone))
    spine = body.part("spine_fin", (0, -11, 3))
    P.add(spine, (0, 0, 0), (0, 10, 3), faces(painter(ridge_fin)))

    head_part = body.part("head", (0, -13, 0))
    P.add(head_part, (-4, -8, -4), (8, 8, 8), faces(head))
    for side, sx in (("right", -1), ("left", 1)):
        horn_part = head_part.part(f"{side}_horn", (2.5 * sx, -7.5, 0.5), (-1.15, 0.2 * sx, 0.28 * sx))
        P.add(horn_part, (-1, -5, -1), (2, 5, 2), faces(painter(horn)), side == "left", "horn")
        P.add(horn_part, (-1.25, -3, -1.25), (2.5, 1, 2.5), faces(painter(horn_ring)), side == "left", "horn_ring")
        upper = horn_part.part(f"{side}_horn_tip", (0, -5, 0), (-0.45, 0, 0))
        P.add(upper, (-0.5, -5, -0.5), (1, 5, 1), faces(painter(horn)), side == "left", "horn_tip")
        tine = horn_part.part(f"{side}_tine", (0, -3.5, -0.5), (0.9, 0, 0.35 * sx))
        P.add(tine, (-0.5, -3, -0.5), (1, 3, 1), faces(painter(horn)), side == "left", "tine")
        wh = head_part.part(f"{side}_whisker", (2.6 * sx, -2.5, -4), (0.7, 0.5 * sx, 0.35 * sx))
        P.add(wh, (-0.5, 0, -0.5), (1, 5, 1), faces(painter(whisker)), side == "left", "whisker")
        wh2 = wh.part(f"{side}_whisker2", (0, 5, 0), (0.4, 0, 0))
        P.add(wh2, (-0.5, 0, -0.5), (1, 5, 1), faces(painter(whisker)), side == "left", "whisker")
    mane_part = head_part.part("mane", (0, -7, 4), (0.25, 0, 0))
    P.add(mane_part, (-3.5, 0, -1), (7, 8, 2), faces(painter(mane)))
    mane2 = mane_part.part("mane2", (0, 8, 0), (0.15, 0, 0))
    P.add(mane2, (-2.5, 0, -1), (5, 6, 2), faces(painter(mane)))

    for side, sx in (("right", -1), ("left", 1)):
        mirror = side == "left"
        arm = body.part(f"{side}_arm", (6 * sx, -11, 0), (0, 0, -0.1 * sx))
        P.add(arm, (-1.5, -1, -1.5), (3, 6, 3), faces(painter(upper_arm)), mirror, "upper_arm")
        P.add(arm, (-2, -2, -2), (4, 3, 4), faces(painter(pauldron)), mirror, "pauldron")
        fore = arm.part(f"{side}_forearm", (0, 5, 0))
        P.add(fore, (-1.5, 0, -1.5), (3, 5, 3), faces(painter(forearm)), mirror, "forearm")
        P.add(fore, (-2, 0.5, -2), (4, 3, 4), faces(painter(bracer)), mirror, "bracer")
        P.add(fore, (-1.5, 5, -1.5), (3, 2, 3), faces(painter(hand)), mirror, "hand")

    parent, pivot = body, (0, 0, 0)
    for i, (w, d, length) in enumerate(TAIL):
        seg = parent.part(f"tail{i + 1}", pivot)
        P.add(seg, (-w / 2, 0, -d / 2), (w, length, d), faces(tail_seg(i, sash=i == 0)))
        fin_h = 3 if i < 4 else 2
        fin = seg.part(f"fin{i + 1}", (0, 0, d / 2))
        P.add(fin, (0, 0, 0), (0, length, fin_h), faces(dorsal(i)))
        parent, pivot = seg, (0, length, 0)
    tip = parent.part("tuft", (0, TAIL[-1][2], 0))
    P.add(tip, (-1.5, -1, -1.5), (3, 7, 3), faces(tuft_bolts))

    P.apply()
    m.save()


if __name__ == "__main__":
    build()
