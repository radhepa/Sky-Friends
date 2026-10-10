"""Cirri (SEER-eye), candidate A: the ribbon-flyers of the high wind.

Wingless sky-dancers named after cirrus, the thin streaky clouds at the top of the sky. They fly on their
veils: two long scarves of woven cirrus that grow from a stole over their shoulders and catch the high
wind. A Cirri never flaps; it swims through the air in long arcs, body stretched out, one knee bent,
the veils rippling two blocks behind it. Hovering, it stands upright on nothing while the veils float
round it like weed in a slow current.

About two blocks tall and slender: warm skin, dark hair in a high bun with a long tail, a gold circlet
with a sky-blue stone, a cream silk wrap, loose sky-blue trousers, bare feet with gold anklets, gold
armlets, and silk ribbons at the wrists. Inspired by the flying musicians painted on old temple and
cave walls across Asia.
"""
from common import glow_as, gradient, mix, painter, ring_u, shade, tone
from living_eyes import bake as bake_face
from mobkit import Model, Pack, faces

NAME = "Cirri"

SKIN = ["#d6a47c", "#d19e76", "#dbaa83"]
SKIN_SHADE = "#b4825d"
SKIN_LIGHT = "#e6bd97"
HAIR = ["#2b1d33", "#30213a", "#271a2e"]
HAIR_HI = "#4d3a5a"
GOLD = "#e6c15a"
GOLD_LIGHT = "#f8e29a"
GOLD_DARK = "#a77a2b"
JEWEL = "#5cc8ff"
JEWEL_DIM = "#2f7fb8"
SILK = ["#f4ecdc", "#efe5d1", "#f7f0e2"]
SILK_SHADE = "#d6c8ac"
ROSE = ["#e3a1af", "#dd98a7", "#e8abb8"]
ROSE_DARK = "#b9707f"
SKY = ["#8fc4e8", "#89bee3", "#97cbec"]
SKY_LIGHT = "#c3e2f5"
SKY_DARK = "#5f93bd"
IRIS = "#4f7896"          # a high-sky blue-grey (the living eyes sample it)
VEIL = ["#a9d9f2", "#e9f6fc", "#ffffff", "#f6d3c8", "#f0b8a4"]   # root -> tip: sky, cloud-white, dawn rose


def front_dist(c, x):
    """How far a side-face column is from the front edge (0 = the front corner)."""
    return c.w - 1 - x if c.face == "right" else x


# -- head ------------------------------------------------------------------------------------------
def head(c):
    if c.face == "front":
        # A clean face, like a Village Friends resident's: the living eyes, brows, mouth and blush are
        # planes drawn in front of it by the client. Hair keeps clear of the eye rows.
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, c.pick(SKIN), 0.06))
        for x in range(8):                                   # hairline, parted in the middle
            c.set(x, 0, c.pick(HAIR))
        for x in (0, 1, 2, 5, 6, 7):
            c.set(x, 1, c.pick(HAIR))
        c.set(2, 1, HAIR_HI)
        c.set(5, 1, HAIR_HI)
        c.set(0, 2, c.pick(HAIR))                            # temple locks
        c.set(7, 2, c.pick(HAIR))
        return
    if c.face in ("right", "left"):
        for y in range(c.h):
            for x in range(c.w):
                d = front_dist(c, x)
                hair = y <= 2 or d >= 3 or (d == 0 and y <= 6)
                c.set(x, y, c.pick(HAIR) if hair else tone(c, y, c.pick(SKIN), 0.08))
        ear = c.w - 1 - 3 if c.face == "right" else 3
        c.set(ear, 4, SKIN_SHADE)
        c.set(ear, 5, SKIN[0])
        c.set(ear, 6, GOLD)                                   # a gold drop earring
        c.glow(ear, 7, GOLD_LIGHT)
        for y in range(3, 8):                                 # a highlight running back
            if (y + 1) % 3 == 0:
                c.set(ear + (1 if c.face == "left" else -1) * 2, y, HAIR_HI)
        return
    if c.face == "back":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(HAIR)
                if (x + y) % 5 == 0:
                    col = HAIR_HI
                c.set(x, y, col)
        return
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, HAIR_HI if x in (3, 4) and y > 3 else c.pick(HAIR))
        return
    for y in range(c.h):                                     # underside: jaw in front, hair behind
        for x in range(c.w):
            c.set(x, y, c.pick(HAIR) if y < 4 else SKIN_SHADE)


def circlet(c):
    if c.face in ("top", "bottom"):
        return                                                # just a band: no lid, no floor
    for x in range(c.w):
        c.set(x, 0, GOLD_DARK if (x + ring_u(c, 8, 8)) % 4 == 0 else GOLD)
    if c.face == "front":
        c.set(3, 0, GOLD_LIGHT)
        c.glow(4, 0, JEWEL)                                   # the sky-stone
        c.set(4, 0, JEWEL)
        glow_as(c, 4, 0, JEWEL, JEWEL)


def bun(c, x, y):
    if c.face == "top":
        return HAIR_HI if (x + y) % 3 == 0 else HAIR[0]
    return HAIR_HI if (x + ring_u(c, 4, 4) + y) % 4 == 0 else tone(c, y, HAIR[1], 0.15)


def pin(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, GOLD if (x + y) % 2 else GOLD_LIGHT)
    if c.face in ("right", "left"):
        glow_as(c, 0, 0, JEWEL_DIM, JEWEL)


def hair_tail(taper):
    def run(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(HAIR)
                if c.face in ("back", "front") and x == c.w // 2 and y % 2 == 0:
                    col = HAIR_HI
                if taper and y >= c.h - 2 and c.face in ("back", "front") and x in (0, c.w - 1):
                    c.clear(x, y)                             # the tail thins to a point
                    continue
                c.set(x, y, col)
        if not taper and c.face in ("back", "front"):
            for x in range(c.w):                              # a gold ring holding the tail
                c.set(x, 0, GOLD)
    return run


# -- body ------------------------------------------------------------------------------------------
def silk_wrap(c):
    w, d = 8, 5
    for y in range(c.h):
        for x in range(c.w):
            if c.face in ("top", "bottom"):
                c.set(x, y, SILK_SHADE)
                continue
            col = c.pick(SILK)
            u = x + ring_u(c, w, d)
            if c.face == "front" and abs((x - 0.5) - y * 1.2) < 0.7:
                col = SILK_SHADE                              # the fold where the wrap crosses
            elif u % 4 == 3:
                col = shade(col, 0.95)
            if y == c.h - 1:
                col = GOLD if u % 2 else GOLD_DARK
            c.set(x, y, tone(c, y, col, 0.08))
    if c.face == "front":
        c.set(3, 1, GOLD)
        glow_as(c, 4, 1, JEWEL_DIM, JEWEL)                    # brooch
        c.set(4, 2, GOLD_DARK)


def midriff(c, x, y):
    """The wrap's lower fold, tucked into the sash."""
    if c.face in ("top", "bottom"):
        return SILK_SHADE
    col = c.pick(SILK)
    if y == 0:
        col = SILK_SHADE                                      # shadow under the upper wrap
    elif (x + ring_u(c, 7, 4)) % 3 == 0:
        col = shade(col, 0.94)
    return tone(c, y, col, 0.1)


def waistband(c):
    w, d = 9, 6
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top":
                c.set(x, y, GOLD_DARK)
                continue
            if c.face == "bottom":
                c.set(x, y, SKY_DARK)
                continue
            u = x + ring_u(c, w, d)
            if y == 0:
                col = GOLD if u % 3 else GOLD_LIGHT
            elif y == 1:
                col = ROSE[0] if u % 2 else ROSE_DARK            # rose sash knotted round the hips
            else:
                col = c.pick(SKY) if u % 2 else shade(SKY[0], 0.9)
            c.set(x, y, tone(c, y, col, 0.1))
    if c.face == "front":
        glow_as(c, 4, 0, JEWEL_DIM, JEWEL)


def stole(c):
    w, d = 10, 6
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top":
                col = c.pick(ROSE)
                if y in (0, c.h - 1):
                    col = GOLD
                c.set(x, y, col)
                continue
            if c.face == "bottom":
                c.set(x, y, ROSE_DARK)
                continue
            col = GOLD if y == c.h - 1 else c.pick(ROSE)
            if y == 0 and (x + ring_u(c, w, d)) % 2 == 0:
                col = shade(ROSE[0], 1.08)
            c.set(x, y, col)


def sash_panel(c, x, y):
    """The sash's long front fold, rose silk with a gold hem."""
    if y >= c.h - 1:
        return GOLD
    if y == c.h - 2:
        return GOLD_DARK if x == 1 else ROSE_DARK
    col = c.pick(ROSE)
    if x == 1 and y % 3 == 1:
        col = shade(col, 1.08)
    return tone(c, y, col, 0.12)


# -- limbs -----------------------------------------------------------------------------------------
def upper_arm(c, x, y):
    if c.face == "top":
        return ROSE_DARK
    col = tone(c, y, c.pick(SKIN), 0.08)
    if y == 2:
        col = GOLD
    elif y == 3:
        col = GOLD_DARK if (x + ring_u(c, 3, 3)) % 2 else GOLD
    return col


def forearm(c, x, y):
    if c.face in ("top", "bottom"):
        return SKIN_SHADE
    col = tone(c, y, c.pick(SKIN), 0.08)
    if y in (3, 4):
        col = GOLD if (x + y + ring_u(c, 3, 3)) % 2 else GOLD_LIGHT    # stacked bangles
    return col


def hand(c, x, y):
    if c.face == "bottom":
        return SKIN_SHADE
    if c.face == "front" and y == c.h - 1:
        return SKIN_LIGHT
    return tone(c, y, c.pick(SKIN), 0.1)


def trousers(top, bottom):
    """Loose sky-silk trousers in long pleats, paling toward the ankle (t = top..bottom of the leg)."""
    def run(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    c.set(x, y, SKY_DARK)
                    continue
                if c.face == "bottom":
                    c.set(x, y, SKY_DARK)
                    continue
                t = top + (bottom - top) * (y / max(1, c.h - 1))
                col = mix(c.pick(SKY), SKY_LIGHT, t * 0.6)
                u = x + ring_u(c, 4, 4)
                if u % 2 == 1:
                    col = shade(col, 0.9)                         # pleat shadow
                if bottom >= 1.0 and y == c.h - 1:
                    col = GOLD if u % 2 else GOLD_DARK            # gold-bordered cuff
                c.set(x, y, col)
    return run


def anklet(c, x, y):
    if c.face in ("top", "bottom"):
        return SKIN_SHADE
    return GOLD_LIGHT if (x + ring_u(c, 3, 3)) % 2 else GOLD


def foot(c, x, y):
    if c.face == "top" and y == c.h - 1:
        return SKIN_LIGHT if x % 2 == 0 else SKIN[0]                 # toes (on a top face the last row is the front)
    if c.face == "bottom":
        return SKIN_SHADE
    return c.pick(SKIN)


# -- veils -----------------------------------------------------------------------------------------
VEIL_SEGMENTS = (7, 7, 7, 6)


def veil(index, last=False, segments=VEIL_SEGMENTS):
    """One plane of a veil: a woven-cloud gradient along the whole veil, gold-threaded edges, frayed tip."""
    start, total = sum(segments[:index]), sum(segments)

    def run(c):
        for y in range(c.h):
            t = (start + y) / (total - 1)
            for x in range(c.w):
                col = gradient(VEIL, t)
                if x in (0, c.w - 1):
                    col = mix(col, GOLD, 0.55) if (start + y) % 2 == 0 else mix(col, GOLD_DARK, 0.3)
                elif c.rng.random() < 0.18:
                    col = shade(col, 1.06)
                if c.face == "back":
                    col = shade(col, 0.92)                        # the outer side is a touch deeper
                if last:
                    fray = y - (c.h - 3)
                    if fray >= 0 and (x != c.w // 2 or fray == 2) and c.rng.random() < 0.45 + fray * 0.25:
                        c.clear(x, y)
                        continue
                c.set(x, y, col)
        if c.face == "front" and index == 1:                     # a woven star where the veil turns
            glow_as(c, 1, min(3, c.h - 1), mix(VEIL[1], GOLD, 0.6), GOLD_LIGHT)
    return run


def ribbon(index):
    def run(c):
        for y in range(c.h):
            t = (index * 5 + y) / 9
            for x in range(c.w):
                col = mix(ROSE[0], GOLD_LIGHT, t * 0.7)
                if x == 0:
                    col = shade(col, 0.9)
                if index == 1 and y >= c.h - 1 and x == 1:
                    c.clear(x, y)
                    continue
                c.set(x, y, col)
    return run


# -- men -------------------------------------------------------------------------------------------
def head_male(c):
    """Short hair swept back to a small topknot; the face is clean like everyone's (living eyes)."""
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, c.pick(SKIN), 0.06))
        for x in range(8):
            c.set(x, 0, c.pick(HAIR))
        for x in (0, 1, 6, 7):
            c.set(x, 1, c.pick(HAIR))
        c.set(0, 2, c.pick(HAIR))
        c.set(7, 2, c.pick(HAIR))
        return
    if c.face in ("right", "left"):
        for y in range(c.h):
            for x in range(c.w):
                d = front_dist(c, x)
                hair = y <= 1 or d >= 4 or (d >= 2 and y <= 3) or (d == 1 and y <= 4)   # with a sideburn
                c.set(x, y, c.pick(HAIR) if hair else tone(c, y, c.pick(SKIN), 0.08))
        ear = c.w - 1 - 3 if c.face == "right" else 3
        c.set(ear, 4, SKIN_SHADE)
        c.set(ear, 5, GOLD)                                   # a gold stud
        return
    if c.face == "back":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(HAIR) if y <= 5 else tone(c, y, c.pick(SKIN), 0.1)
                if y <= 5 and (x + y) % 5 == 0:
                    col = HAIR_HI
                c.set(x, y, col)
        return
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, HAIR_HI if (x + y) % 4 == 0 else c.pick(HAIR))
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(HAIR) if y < 3 else SKIN_SHADE)


def tunic(c):
    """A sleeveless silk tunic with a V at the neck and the stole colour crossing it as a sash."""
    w, d = 9, 5
    for y in range(c.h):
        for x in range(c.w):
            if c.face in ("top", "bottom"):
                c.set(x, y, SILK_SHADE)
                continue
            col = c.pick(SILK)
            u = x + ring_u(c, w, d)
            if u % 4 == 3:
                col = shade(col, 0.95)
            if c.face == "front":
                mid = (c.w - 1) / 2
                if y <= 1 and abs(x - mid) <= 1 - y * 0.5 + 0.1:
                    col = tone(c, y, c.pick(SKIN), 0.05)      # the V at the neck
                if abs((c.w - 1 - x) - y * 1.4 - 1) < 0.9:
                    col = ROSE[0] if (x + y) % 2 else ROSE_DARK   # sash over the left shoulder
            if c.face == "back" and abs(x - y * 1.4 - 1) < 0.9:
                col = ROSE[0]
            if y == c.h - 1:
                col = GOLD if u % 2 else GOLD_DARK
            c.set(x, y, tone(c, y, col, 0.08))


def bracer_forearm(c, x, y):
    if c.face in ("top", "bottom"):
        return SKIN_SHADE
    col = tone(c, y, c.pick(SKIN), 0.08)
    if y in (2, 3, 4):
        col = GOLD_DARK if y == 2 else (GOLD if (x + ring_u(c, 3, 3)) % 2 else GOLD_LIGHT)   # a gold bracer
    return col


# -- looks -----------------------------------------------------------------------------------------
# skin (3 shades), its shadow and light, hair (3) and its highlight, eyes. The living eyes take the
# skin, the iris and the hair colour from here.
COMPLEXIONS = [
    dict(SKIN=["#e9c6a6", "#e4bf9f", "#eecdae"], SKIN_SHADE="#c99d7a", SKIN_LIGHT="#f5dcc4",
         HAIR=["#5b3a26", "#634029", "#523422"], HAIR_HI="#80583b", IRIS="#4f7896"),
    dict(SKIN=["#d6a47c", "#d19e76", "#dbaa83"], SKIN_SHADE="#b4825d", SKIN_LIGHT="#e6bd97",
         HAIR=["#2b1d33", "#30213a", "#271a2e"], HAIR_HI="#4d3a5a", IRIS="#62703f"),
    dict(SKIN=["#8f5c3f", "#89573b", "#966244"], SKIN_SHADE="#6c4431", SKIN_LIGHT="#a77253",
         HAIR=["#1c1418", "#211719", "#181114"], HAIR_HI="#3b2c31", IRIS="#6b4423"),
]
# the clothes: silk, the stole/sash colour, the trousers, and the veils from root to tip
PALETTES = {
    'dawn': dict(SILK=["#f4ecdc", "#efe5d1", "#f7f0e2"], SILK_SHADE="#d6c8ac", ROSE=["#e3a1af", "#dd98a7", "#e8abb8"],
                 ROSE_DARK="#b9707f", SKY=["#8fc4e8", "#89bee3", "#97cbec"], SKY_LIGHT="#c3e2f5", SKY_DARK="#5f93bd",
                 VEIL=["#a9d9f2", "#e9f6fc", "#ffffff", "#f6d3c8", "#f0b8a4"]),
    'dusk': dict(SILK=["#ece6f2", "#e5def0", "#f1ebf6"], SILK_SHADE="#c8bcd8", ROSE=["#eaa65e", "#e39d55", "#efb06a"],
                 ROSE_DARK="#b8773a", SKY=["#6f6cb0", "#6865a8", "#7774b8"], SKY_LIGHT="#a7a3d8", SKY_DARK="#4a4785",
                 VEIL=["#8f86c9", "#cfc6ee", "#f6eefc", "#f7cfa6", "#eeb06e"]),
    'noon': dict(SILK=["#fbf8f0", "#f6f2e8", "#fffcf5"], SILK_SHADE="#dcd6c6", ROSE=["#7dbde6", "#74b5e0", "#88c5ea"],
                 ROSE_DARK="#4f8fbf", SKY=["#efe0b4", "#eadaa9", "#f3e6bf"], SKY_LIGHT="#fbf3dc", SKY_DARK="#c9b37a",
                 VEIL=["#ffffff", "#e8f4fc", "#bfe2f6", "#e8f4fc", "#ffffff"]),
    'storm': dict(SILK=["#dfe5ec", "#d8dfe7", "#e6ebf1"], SILK_SHADE="#b6c0cc", ROSE=["#3f4f86", "#3a4a7f", "#46578e"],
                  ROSE_DARK="#2a3560", SKY=["#5b8791", "#557f89", "#628f99"], SKY_LIGHT="#93bcc3", SKY_DARK="#3d6169",
                  VEIL=["#c9d4e2", "#9fb2c8", "#7f97b2", "#6fa3ad", "#4f8a96"]),
}
PALETTE_ORDER = ('dawn', 'dusk', 'noon', 'storm')


def use(complexion, palette):
    """Dress the painters in a look: a complexion (0-2) and a palette name."""
    globals().update(COMPLEXIONS[complexion])
    globals().update(PALETTES[palette])


def texture_id(gender, complexion, palette):
    return f"cirri_{gender}_{complexion}_{palette}"


def child_texture_id(gender, complexion):
    return f"cirri_child_{gender}_{complexion}"


# -- the models ------------------------------------------------------------------------------------
def adult(gender, complexion, palette, geometry):
    use(complexion, palette)
    male = gender == "m"
    m = Model("cirri_male" if male else "cirri", 128, 64, seed=21, texture_id=texture_id(gender, complexion, palette))
    bake_face(m, 112, 63, SKIN[0], IRIS, HAIR[0])            # the living eyes' colours, on the bottom row
    m.preview = {"right_arm": [-0.2, 0, 0.35], "left_arm": [-0.35, 0, -0.5], "right_forearm": [-0.5, 0, 0],
                 "left_forearm": [-0.3, 0, 0], "right_shin": [0.35, 0, 0], "right_leg": [-0.15, 0, 0]}
    P = Pack(m, areas=[(0, 0, 128, 63)])                     # the bottom row holds the face swatches

    body = m.part("body", (0, 12, 0))
    if male:
        P.add(body, (-4.5, -12, -2.5), (9, 6, 5), faces(tunic))                        # broader chest
        P.add(body, (-3.5, -6, -2), (7, 3, 4), faces(painter(midriff)))
        P.add(body, (-4.5, -3, -2.75), (9, 4, 5.5), faces(waistband))
        P.add(body, (-5.5, -12.6, -3), (11, 1.5, 6), faces(stole))                    # a narrow shoulder mantle
    else:
        P.add(body, (-4, -12, -2.5), (8, 6, 5), faces(silk_wrap))
        P.add(body, (-3.5, -6, -2), (7, 3, 4), faces(painter(midriff)))
        P.add(body, (-4.5, -3, -2.75), (9, 4, 5.5), faces(waistband))
        P.add(body, (-5, -12.6, -3), (10, 2, 6), faces(stole))
    sash = body.part("sash", (0, 1, -2.85))
    P.add(sash, (-1.5, 0, 0), (3, 9, 0), faces(painter(sash_panel)))

    neck = body.part("neck", (0, -12, 0))                     # keeps the head level while the body stretches out
    head_part = neck.part("head")
    P.add(head_part, (-4, -8, -4), (8, 8, 8), faces(head_male if male else head))
    P.add(head_part, (-4, -8, -4), (8, 1, 8), faces(circlet), inflate=0.25)   # on the hairline, clear of the brows
    if male:
        P.add(head_part, (-1.5, -10, 0), (3, 2, 3), faces(painter(bun)))       # topknot
        P.add(head_part, (-2, -9.5, 1), (4, 1, 1), faces(pin))
        hair = head_part.part("hair", (0, -9, 3), (0.35, 0, 0))
        P.add(hair, (-1, 0, -0.5), (2, 4, 1), faces(hair_tail(False)))
        hair2 = hair.part("hair2", (0, 4, 0), (0.15, 0, 0))
        P.add(hair2, (-0.5, 0, -0.5), (1, 3, 1), faces(hair_tail(True)))
    else:
        P.add(head_part, (-2, -11, -0.5), (4, 3, 4), faces(painter(bun)))
        P.add(head_part, (-3, -10, 1), (6, 1, 1), faces(pin))
        hair = head_part.part("hair", (0, -9.5, 3.6), (0.25, 0, 0))
        P.add(hair, (-1.5, 0, -0.75), (3, 8, 1.5), faces(hair_tail(False)))
        hair2 = hair.part("hair2", (0, 8, 0), (0.15, 0, 0))
        P.add(hair2, (-1, 0, -0.75), (2, 7, 1.5), faces(hair_tail(True)))

    shoulder = 5.5 if male else 5
    for side, sx in (("right", -1), ("left", 1)):
        mirror = side == "left"
        arm = body.part(f"{side}_arm", (shoulder * sx, -10, 0), (0, 0, -0.08 * sx))
        P.add(arm, (-1.5, -1, -1.5), (3, 6, 3), faces(painter(upper_arm)), mirror, "upper_arm")
        fore = arm.part(f"{side}_forearm", (0, 5, 0))
        P.add(fore, (-1.5, 0, -1.5), (3, 5, 3), faces(painter(bracer_forearm if male else forearm)), mirror, "forearm")
        P.add(fore, (-1, 5, -1.5), (2, 2, 3), faces(painter(hand)), mirror, "hand")
        rib = fore.part(f"{side}_ribbon", (0, 3, 1.55), (0.3, 0, 0.1 * -sx))
        P.add(rib, (-1, 0, 0), (2, 5, 0), faces(ribbon(0)), mirror, "ribbon0")
        rib2 = rib.part(f"{side}_ribbon2", (0, 5, 0), (0.2, 0, 0))
        P.add(rib2, (-1, 0, 0), (2, 4, 0), faces(ribbon(1)), mirror, "ribbon1")

        leg = body.part(f"{side}_leg", (2 * sx, 0, 0))
        P.add(leg, (-2, 0, -2), (4, 6, 4), faces(trousers(0.0, 0.5)), mirror, "thigh")
        shin = leg.part(f"{side}_shin", (0, 6, 0))
        P.add(shin, (-2, 0, -2), (4, 4, 4), faces(trousers(0.5, 1.0)), mirror, "shin")
        P.add(shin, (-1.5, 4, -1.5), (3, 1, 3), faces(painter(anklet)), mirror, "ankle")
        P.add(shin, (-1.5, 5, -3), (3, 1, 4), faces(painter(foot)), mirror, "foot")

        veil_part, pivot = body, (3 * sx, -11.5, 2.65)
        for i, length in enumerate(VEIL_SEGMENTS):
            name = f"{side}_veil" + ("" if i == 0 else str(i + 1))
            rot = (0.18, 0, -0.14 * sx) if i == 0 else (0.12, 0, 0)
            veil_part = veil_part.part(name, pivot, rot)
            P.add(veil_part, (-2, 0, 0), (4, length, 0), faces(veil(i, i == len(VEIL_SEGMENTS) - 1)), mirror, f"veil{i}")
            pivot = (0, length, 0)

    P.apply()
    m.save(geometry=geometry)
    return m


CHILD_VEIL = (5, 5, 4, 3)


def child(gender, complexion, geometry):
    """A child: the same head (the living eyes need it) on a small body, a little bun, short veils. Girls wear
    dawn colours, boys noon colours."""
    use(complexion, 'dawn' if gender == 'f' else 'noon')
    m = Model("cirri_child", 128, 64, seed=27, texture_id=child_texture_id(gender, complexion))
    m.scale = 0.8
    bake_face(m, 112, 63, SKIN[0], IRIS, HAIR[0])
    m.preview = {"right_arm": [-0.3, 0, 0.4], "left_arm": [-0.3, 0, -0.4]}
    P = Pack(m, areas=[(0, 0, 128, 63)])

    body = m.part("body", (0, 17, 0))
    P.add(body, (-3, -6, -2), (6, 4, 4), faces(silk_wrap))
    P.add(body, (-3, -2, -2), (6, 2, 4), faces(waistband))
    P.add(body, (-3.5, -6.5, -2.5), (7, 1.5, 5), faces(stole))
    sash = body.part("sash", (0, 0, -2.05))
    P.add(sash, (-1, 0, 0), (2, 5, 0), faces(painter(sash_panel)))
    neck = body.part("neck", (0, -6, 0))
    head_part = neck.part("head")
    P.add(head_part, (-4, -8, -4), (8, 8, 8), faces(head if gender == 'f' else head_male))
    P.add(head_part, (-4, -8, -4), (8, 1, 8), faces(circlet), inflate=0.25)
    P.add(head_part, (-1.5, -10, -0.5), (3, 2, 3), faces(painter(bun)))
    hair = head_part.part("hair", (0, -9, 2.5), (0.3, 0, 0))
    P.add(hair, (-1, 0, -0.5), (2, 4, 1), faces(hair_tail(False)))
    hair2 = hair.part("hair2", (0, 4, 0), (0.15, 0, 0))
    P.add(hair2, (-0.5, 0, -0.5), (1, 3, 1), faces(hair_tail(True)))

    for side, sx in (("right", -1), ("left", 1)):
        mirror = side == "left"
        arm = body.part(f"{side}_arm", (3.8 * sx, -5, 0), (0, 0, -0.1 * sx))
        P.add(arm, (-1, -0.5, -1), (2, 3, 2), faces(painter(upper_arm)), mirror, "upper_arm")
        fore = arm.part(f"{side}_forearm", (0, 2.5, 0))
        P.add(fore, (-1, 0, -1), (2, 2.5, 2), faces(painter(forearm)), mirror, "forearm")
        P.add(fore, (-1, 2.5, -1), (2, 1.5, 2), faces(painter(hand)), mirror, "hand")
        rib = fore.part(f"{side}_ribbon", (0, 2, 1.05), (0.3, 0, 0.1 * -sx))
        P.add(rib, (-1, 0, 0), (2, 3, 0), faces(ribbon(0)), mirror, "ribbon0")
        rib2 = rib.part(f"{side}_ribbon2", (0, 3, 0), (0.2, 0, 0))
        P.add(rib2, (-1, 0, 0), (2, 2, 0), faces(ribbon(1)), mirror, "ribbon1")

        leg = body.part(f"{side}_leg", (1.5 * sx, 0, 0))
        P.add(leg, (-1.5, 0, -1.5), (3, 3.5, 3), faces(trousers(0.0, 0.5)), mirror, "thigh")
        shin = leg.part(f"{side}_shin", (0, 3.5, 0))
        P.add(shin, (-1.5, 0, -1.5), (3, 2.5, 3), faces(trousers(0.5, 1.0)), mirror, "shin")
        P.add(shin, (-1, 2.5, -1), (2, 0.5, 2), faces(painter(anklet)), mirror, "ankle")
        P.add(shin, (-1, 3, -2), (2, 0.5, 3), faces(painter(foot)), mirror, "foot")

        veil_part, pivot = body, (2 * sx, -6, 2.05)
        for i, length in enumerate(CHILD_VEIL):
            name = f"{side}_veil" + ("" if i == 0 else str(i + 1))
            rot = (0.18, 0, -0.14 * sx) if i == 0 else (0.12, 0, 0)
            veil_part = veil_part.part(name, pivot, rot)
            P.add(veil_part, (-1.5, 0, 0), (3, length, 0), faces(veil(i, i == len(CHILD_VEIL) - 1, CHILD_VEIL)), mirror, f"veil{i}")
            pivot = (0, length, 0)

    P.apply()
    m.save(geometry=geometry)
    return m


def build():
    """Every look: women and men in 3 complexions x 4 palettes, girls and boys in 3 complexions."""
    out = []
    for gender in ("f", "m"):
        first = True
        for c in range(len(COMPLEXIONS)):
            for pal in PALETTE_ORDER:
                adult(gender, c, pal, geometry=first)
                out.append(texture_id(gender, c, pal))
                first = False
    first = True
    for gender in ("f", "m"):
        for c in range(len(COMPLEXIONS)):
            child(gender, c, geometry=first)
            out.append(child_texture_id(gender, c))
            first = False
    return out


if __name__ == "__main__":
    print(len(build()), "Cirri textures")
