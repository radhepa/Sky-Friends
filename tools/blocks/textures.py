"""Paints every Sky Friends block and item texture as a 16x16 RGBA PNG.

    python tools/blocks/textures.py

Deterministic: every texture uses its own fixed random seed, so a re-run writes identical files.
Writes
  src/main/resources/assets/skyfriends/textures/block/<name>.png   (catalog.block_textures())
  src/main/resources/assets/skyfriends/textures/item/<name>.png    (catalog.item_textures())
  tools/blocks/out/sheet.png      every texture at 8x, labelled
  tools/blocks/out/tiled.png      every block texture tiled 4x4 (seam / repetition check)
  tools/buildings/mod_colors.json average colour per block id (for the offline voxel previewer)

Style: vanilla-like pixel art, small palettes, light from the top-left. The look of the isles is
pale cool stone, warm gold trim, sky blue, dawn rose and cream silk.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import catalog  # noqa: E402

TEXTURES = ROOT / 'src' / 'main' / 'resources' / 'assets' / 'skyfriends' / 'textures'
BLOCK_DIR = TEXTURES / 'block'
ITEM_DIR = TEXTURES / 'item'
OUT_DIR = HERE / 'out'
COLORS_JSON = ROOT / 'tools' / 'buildings' / 'mod_colors.json'
N = 16


# ------------------------------------------------------------------------------------- colours
def C(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, t):
    """Blend two '#rrggbb' colours (t=0 -> c1), returned as '#rrggbb'."""
    a, b = C(c1), C(c2)
    return '#%02x%02x%02x' % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# skystone: cool blue-lavender grey
S_DEEP, S_DARK, S_MID, S_BASE = '#7b859b', '#8d97ab', '#a2acbf', '#b8c2d4'
S_LIGHT, S_PALE, S_GLINT = '#c7cfdf', '#d3dbe8', '#f2f5fb'
# gold
G_DEEP, G_DARK, G_MID, G_BASE, G_LIGHT, G_SHINE = '#7a5822', '#a77a2b', '#c99c42', '#e6c15a', '#f8e29a', '#fff6d6'
# sky blue
K_DEEP, K_DARK, K_MID, K_BASE, K_LIGHT, K_PALE = '#43709a', '#5f93bd', '#76abd6', '#8fc4e8', '#b6dcf4', '#e2f2fc'
# dawn rose
R_DEEP, R_DARK, R_MID, R_BASE, R_LIGHT = '#96566a', '#b9707f', '#cf8a99', '#e3a1af', '#f1c3cc'
# cream silk
CR_LIGHT, CR_BASE, CR_SHADE, CR_DARK = '#fbf7ee', '#f4ecdc', '#e6dac3', '#d2c3a6'
# cloud
CL_WHITE, CL_BASE, CL_1, CL_2, CL_3 = '#ffffff', '#f7f8fc', '#e8eaf4', '#d9dbea', '#c3c6dc'
# skywood (pale gold-cream timber)
W_LIGHT, W_BASE, W_MID, W_DARK, W_SEAM, W_OUT = '#f7ebcd', '#ecdbb0', '#dcc593', '#c7aa72', '#a98b58', '#6e5634'
# skywood bark (silver-cream, blue-grey grain)
B_LIGHT, B_BASE, B_MID, B_GREY, B_DGREY, B_KNOT = '#f1ede4', '#e0dace', '#ccc7bc', '#a9b1c1', '#8b93a7', '#6a6878'
# silver
AG_LIGHT, AG_BASE, AG_DARK, AG_DEEP = '#f4f6fa', '#cdd3df', '#99a1b3', '#6e7689'
# leaves
LF_GREEN, LF_DGREEN = '#a7cd92', '#76a36c'


# ------------------------------------------------------------------------------------- helpers
def new():
    return np.zeros((N, N, 4), np.uint8)


def put(a, x, y, col):
    if 0 <= x < N and 0 <= y < N:
        a[y, x] = C(col) if isinstance(col, str) else col


def tnoise(rng, cx, cy=None):
    """Smooth value noise that tiles seamlessly: a cx-by-cy random grid, smoothstep-interpolated."""
    cy = cy or cx
    g = rng.random((cy, cx))
    xs = (np.arange(N) + 0.5) * cx / N - 0.5
    ys = (np.arange(N) + 0.5) * cy / N - 0.5
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    tx, ty = xs - x0, ys - y0
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    X0, X1, Y0, Y1 = x0 % cx, (x0 + 1) % cx, y0 % cy, (y0 + 1) % cy
    a, b = g[np.ix_(Y0, X0)], g[np.ix_(Y0, X1)]
    c, d = g[np.ix_(Y1, X0)], g[np.ix_(Y1, X1)]
    SX, SY = sx[None, :], sy[:, None]
    top, bot = a + (b - a) * SX, c + (d - c) * SX
    return top + (bot - top) * SY


def rank_levels(field, weights):
    """Split a field into len(weights) levels by rank, so each level gets an exact share of pixels."""
    flat = field.ravel()
    order = np.argsort(flat, kind='stable')
    lv = np.empty(flat.size, int)
    bounds = np.round(np.cumsum(weights) / sum(weights) * flat.size).astype(int)
    start = 0
    for i, b in enumerate(bounds):
        lv[order[start:b]] = i
        start = b
    return lv.reshape(field.shape)


def paint(lv, pal):
    a = new()
    for i, col in enumerate(pal):
        a[lv == i] = C(col)
    return a


def from_map(rows, legend):
    a = new()
    assert len(rows) == N, len(rows)
    for y, row in enumerate(rows):
        assert len(row) == N, (y, row)
        for x, ch in enumerate(row):
            if ch != '.':
                a[y, x] = C(legend[ch])
    return a


def outline(a, k=0.42, tint=(14, 6, 28), pal=None):
    """Vanilla-item style outline: every empty pixel touching the sprite (4-neighbour) gets a dark,
    slightly purple version of the colours it touches, snapped to `pal` (a few outline shades)."""
    m = a[..., 3] > 0
    out = a.copy()
    for y in range(N):
        for x in range(N):
            if m[y, x]:
                continue
            nb = [a[y + dy, x + dx, :3].astype(float) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
                  if 0 <= y + dy < N and 0 <= x + dx < N and m[y + dy, x + dx]]
            if nb:
                dark = np.clip(np.mean(nb, 0) * k + np.array(tint), 0, 255)
                out[y, x] = C(nearest(dark, pal)) if pal else (*dark.astype(np.uint8), 255)
    return out


def nearest(rgb, pal):
    best, bd = None, 1e9
    for p in pal:
        c = C(p)
        d = sum((rgb[i] - c[i]) ** 2 for i in range(3))
        if d < bd:
            best, bd = p, d
    return best


# =========================================================================================
#                                          BLOCKS
# =========================================================================================
def torus_d(ax, ay, bx, by):
    dx = (ax - bx + 8) % 16 - 8
    dy = (ay - by + 8) % 16 - 8
    return math.hypot(dx, dy)


def scatter(rng, count, mind, tries=4000):
    """Up to `count` points on the 16x16 torus, at least `mind` apart (so tiling hides the grid)."""
    pts = []
    for _ in range(tries):
        if len(pts) >= count:
            break
        x, y = rng.uniform(0, 16, 2)
        if all(torus_d(x, y, px, py) >= mind for px, py in pts):
            pts.append((float(x), float(y)))
    return pts


LIGHT = np.array([-0.55, -0.7, 0.9]) / np.linalg.norm([-0.55, -0.7, 0.9])


def bumps(puffs):
    """Overlapping round bumps (cx, cy, r, z) on the torus, lit from the top-left.
    Returns height, owner (index of the bump on top, -1 = none) and diffuse light per pixel."""
    h = np.full((N, N), -1.0)
    owner = np.full((N, N), -1)
    dif = np.zeros((N, N))
    for y in range(N):
        for x in range(N):
            for i, (cx, cy, r, z) in enumerate(puffs):
                dx = (x + 0.5 - cx + 8) % 16 - 8
                dy = (y + 0.5 - cy + 8) % 16 - 8
                d2 = dx * dx + dy * dy
                if d2 < r * r:
                    hz = math.sqrt(r * r - d2)
                    if hz + z > h[y, x]:
                        h[y, x] = hz + z
                        owner[y, x] = i
                        dif[y, x] = max(0.0, float(np.array([dx / r, dy / r, hz / r]) @ LIGHT))
    return h, owner, dif


def creased(h, owner, y, x, margin=0.4):
    """True where a higher bump just above or left of this pixel overlaps it (its shadowed rim)."""
    for dy, dx in ((-1, 0), (0, -1)):
        oy, ox = (y + dy) % N, (x + dx) % N
        if owner[oy, ox] != owner[y, x] and h[oy, ox] > h[y, x] + margin:
            return True
    return False


STONE_PAL = [S_MID, S_BASE, S_LIGHT, S_PALE]


def stone_levels(seed):
    """Calm skystone: soft light patches over a pale base, a little single-pixel grain."""
    rng = np.random.default_rng(seed)
    f = 0.7 * tnoise(rng, 4) + 0.3 * tnoise(rng, 8)
    lv = rank_levels(f, [11, 52, 25, 12])  # 0 mid, 1 base, 2 light, 3 pale
    g = rng.random((N, N))
    lv = np.where((g < 0.035) & (lv > 0), lv - 1, lv)
    lv = np.where((g > 0.97) & (lv < 3), lv + 1, lv)
    return lv, rng


def tex_skystone():
    lv, rng = stone_levels(107)
    a = paint(lv, STONE_PAL)
    # two small pits, each with a lit lip on its top-left
    for (x, y) in [(3, 9), (12, 3)]:
        put(a, x, y, S_DARK)
        put(a, x + 1, y, S_MID)
        put(a, x - 1, y - 1, S_LIGHT)
    # tiny frost / mica glints on the palest patches
    ys, xs = np.nonzero(lv == 3)
    for i in rng.choice(len(ys), 3, replace=False):
        a[ys[i], xs[i]] = C(S_GLINT)
    return a


def tex_skystone_bricks():
    rng = np.random.default_rng(202)
    noise = tnoise(rng, 8) * 0.6 + rng.random((N, N)) * 0.4
    a = new()
    tints = {(1, 0): (7, 4, -5), (3, 1): (-5, -1, 7)}  # one warmer brick, one cooler brick
    for y in range(N):
        row, yy = y // 4, y % 4
        off = 4 * (row % 2)
        for x in range(N):
            xx = (x - off) % 8
            k = ((x - off) % 16) // 8
            mortar = yy == 3 or xx == 7
            if mortar:
                col = S_DEEP if (yy == 3 and xx == 7) else S_DARK
            else:
                lvl = 2
                if yy == 0 or xx == 0:
                    lvl = 3
                elif yy == 2 or xx == 6:
                    lvl = 1
                n = noise[y, x]
                if lvl == 2 and n > 0.8:
                    lvl = 3
                elif lvl == 2 and n < 0.18:
                    lvl = 1
                col = [S_MID, S_BASE, S_LIGHT, S_PALE][lvl]
            c = list(C(col))
            t = tints.get((row, k))
            if t and not mortar:
                c = [max(0, min(255, c[i] + t[i])) for i in range(3)] + [255]
            a[y, x] = c
    return a


def bevel(a, hi=S_PALE, lo=S_MID, inner=S_BASE):
    """Thin bevelled border: lit top/left edge, shaded bottom/right edge."""
    for i in range(N):
        put(a, i, 0, hi)
        put(a, 0, i, hi)
        put(a, i, 15, lo)
        put(a, 15, i, lo)
    for i in range(1, 15):
        put(a, i, 14, inner)
        put(a, 14, i, inner)
    put(a, 15, 0, inner)
    put(a, 0, 15, inner)


def tex_polished_skystone():
    # very faint cloudy figure in the polished face, then the bevel
    rng = np.random.default_rng(303)
    f = 0.75 * tnoise(rng, 4) + 0.25 * tnoise(rng, 8)
    lv = rank_levels(f, [7, 79, 14])
    a = paint(lv, [mix(S_BASE, S_LIGHT, 0.5), S_LIGHT, mix(S_LIGHT, S_PALE, 0.55)])
    bevel(a)
    return a


def line_pts(p, q):
    """8-connected pixel line from p to q (inclusive)."""
    (x0, y0), (x1, y1) = p, q
    n = max(abs(x1 - x0), abs(y1 - y0))
    return [(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n))) for i in range(n + 1)]


def vein(points):
    out = []
    for p, q in zip(points, points[1:]):
        for pt in line_pts(p, q):
            if not out or out[-1] != pt:
                out.append(pt)
    return out


def tex_gilded_skystone():
    lv, _ = stone_levels(107)
    a = paint(lv, STONE_PAL)
    main = vein([(1, 3), (3, 4), (5, 6), (7, 7), (9, 9), (12, 10), (13, 13)])
    branch = vein([(7, 7), (8, 10), (7, 12)])
    small = vein([(10, 2), (12, 3), (13, 5)])
    gold = set(main) | set(branch) | set(small)
    for (x, y) in gold:  # a soft shadow under the inlay
        if (x, y + 1) not in gold and (x - 1, y + 1) not in gold:
            put(a, x, y + 1, mix(S_MID, S_BASE, 0.4))
    for i, (x, y) in enumerate(main):
        put(a, x, y, G_LIGHT if i % 5 == 1 else (G_MID if i % 7 == 4 else G_BASE))
    for i, (x, y) in enumerate(branch[1:]):
        put(a, x, y, G_BASE if i < 2 else G_MID)
    for i, (x, y) in enumerate(small):
        put(a, x, y, G_MID if i else G_BASE)
    put(a, 4, 6, G_MID)  # the vein thickens where it bends
    for (x, y, col) in [(3, 11, G_LIGHT), (14, 7, G_BASE), (5, 14, G_MID), (11, 14, G_LIGHT)]:
        put(a, x, y, col)
    return a


def tex_skystone_pillar():
    rng = np.random.default_rng(505)
    noise = rng.random((N, N))
    flute = [S_PALE, S_MID, S_BASE, S_LIGHT]   # fillet (lit), groove shadow, groove, groove lit wall
    a = new()
    for y in range(N):
        for x in range(N):
            col = flute[x % 4]
            if noise[y, x] > 0.9 and x % 4 == 2:
                col = S_LIGHT
            put(a, x, y, col)
    band = [G_LIGHT, G_MID, G_BASE, G_BASE]
    for x in range(N):
        put(a, x, 0, S_LIGHT)
        put(a, x, 1, band[x % 4])
        put(a, x, 2, S_MID if x % 4 else S_BASE)
        put(a, x, 13, S_LIGHT)
        put(a, x, 14, band[x % 4])
        put(a, x, 15, S_MID if x % 4 else S_BASE)
    return a


def tone3(dx, dy, hi, mid, lo):
    s = (dx + dy) / max(1e-6, math.hypot(dx, dy))   # -1.41 facing the light .. +1.41 away
    return hi if s < -0.5 else (lo if s > 0.5 else mid)


def tex_skystone_pillar_top():
    a = new()
    for y in range(N):
        for x in range(N):
            dx, dy = x - 7.5, y - 7.5
            d = math.hypot(dx, dy)
            if d >= 6.9:
                col = S_LIGHT
            elif d >= 5.9:
                col = tone3(dx, dy, S_MID, S_BASE, S_PALE)      # carved ring: shadow on its top-left wall
            elif d >= 4.4:
                col = tone3(dx, dy, S_PALE, S_LIGHT, S_BASE)    # the round top, gently domed
            elif d >= 3.4:
                col = tone3(dx, dy, G_LIGHT, G_BASE, G_MID)     # inlaid gold ring
            elif d >= 1.5:
                ang = math.atan2(dy, dx)
                petal = abs(math.cos(2 * ang)) > 0.72           # four petals on the axes
                col = (S_PALE if (dx + dy) < 0 else S_LIGHT) if petal else S_BASE
            else:
                col = G_BASE
            put(a, x, y, col)
    put(a, 7, 7, G_SHINE)
    put(a, 8, 8, G_MID)
    bevel(a, S_PALE, S_MID, S_LIGHT)
    return a


def tex_cloud_block():
    """Five big round puffs on the torus, lit from the top-left; lavender in the hollows and
    under the rim where one puff rides over another."""
    rng = np.random.default_rng(613)
    pts = scatter(rng, 5, 6.5)
    puffs = [(x, y, float(rng.uniform(4.6, 6.4)), float(rng.uniform(0, 1.5))) for x, y in pts]
    h, owner, dif = bumps(puffs)
    v = np.where(owner >= 0, dif, -1)
    lv = np.select([v > 0.86, v > 0.62, v > 0.36, v > 0.12], [4, 3, 2, 1], 0)
    for y in range(N):
        for x in range(N):
            if creased(h, owner, y, x):
                lv[y, x] = min(lv[y, x], 2)
    return paint(lv, [CL_3, CL_2, CL_1, CL_BASE, CL_WHITE])


def tex_skywood_log():
    rng = np.random.default_rng(707)
    f = 0.65 * tnoise(rng, 8, 1) + 0.35 * tnoise(rng, 16, 3)
    lv = rank_levels(f, [26, 46, 28])
    a = paint(lv, [B_MID, B_BASE, B_LIGHT])
    # soft blue-grey grain: broken vertical lines that wrap top to bottom
    soft = mix(B_GREY, B_MID, 0.45)
    for x in (1, 3, 6, 8, 11, 13, 15):
        for _ in range(2):
            y, run = int(rng.integers(0, N)), int(rng.integers(2, 7))
            for k in range(run):
                core = run >= 4 and 0 < k < run - 1
                put(a, x, (y + k) % N, B_GREY if core else soft)
            if run >= 6:
                put(a, x, (y + run // 2) % N, B_DGREY)
    # two small knots: a dark eye in a grey rim, the bark lifted (lit) just above it
    for (kx, ky) in [(6, 5), (11, 12)]:
        put(a, kx, ky - 1, B_LIGHT)
        put(a, kx - 1, ky, B_GREY)
        put(a, kx, ky, B_KNOT)
        put(a, kx + 1, ky, B_GREY)
        put(a, kx, ky + 1, B_DGREY)
    return a


def tex_skywood_log_top():
    rng = np.random.default_rng(808)
    wob = tnoise(rng, 4) - 0.5
    a = new()
    rings = [W_DARK, W_LIGHT, W_BASE, W_MID, W_LIGHT, W_BASE]
    for y in range(N):
        for x in range(N):
            dx, dy = abs(x - 7.5), abs(y - 7.5)
            d = (dx ** 3 + dy ** 3) ** (1 / 3) + wob[y, x] * 0.8
            col = W_DARK if d < 1.2 else rings[int(d / 1.25) % len(rings)]
            put(a, x, y, col)
    for i in range(1, 15):               # the cambium just inside the bark
        for (x, y) in [(i, 1), (1, i), (i, 14), (14, i)]:
            put(a, x, y, W_MID)
    for i in range(N):                   # bark rim, lit on the top/left
        put(a, i, 0, B_LIGHT if i % 5 else B_BASE)
        put(a, 0, i, B_BASE if i % 4 else B_MID)
        put(a, i, 15, B_GREY if i % 3 else B_DGREY)
        put(a, 15, i, B_MID if i % 3 else B_GREY)
    return a


def tex_skywood_planks():
    rng = np.random.default_rng(909)
    a = new()
    joints = {0: 11, 1: 3, 2: 14, 3: 6}
    face = {0: W_BASE, 1: mix(W_BASE, W_LIGHT, 0.35), 2: W_BASE, 3: mix(W_BASE, W_MID, 0.3)}
    for board in range(4):
        y0 = board * 4
        for x in range(N):
            put(a, x, y0, W_LIGHT)
            put(a, x, y0 + 1, face[board])
            put(a, x, y0 + 2, face[board])
            put(a, x, y0 + 3, W_SEAM)
        for _ in range(2):  # light grain streaks
            gx = int(rng.integers(0, N))
            gy = y0 + int(rng.integers(1, 3))
            for i in range(int(rng.integers(3, 7))):
                put(a, (gx + i) % N, gy, W_MID)
        jx = joints[board]
        for y in range(y0, y0 + 3):
            put(a, jx, y, W_DARK)
        put(a, (jx + 1) % N, y0 + 1, W_LIGHT)
    return a


LEAF_SHADE, LEAF_DEEP = '#93abcb', '#7189ae'


def tex_skywood_leaves():
    rng = np.random.default_rng(1010)
    pts = scatter(rng, 13, 3.8)
    clumps = [(x, y, float(rng.uniform(2.0, 2.7)), float(rng.uniform(0, 0.8))) for x, y in pts]
    white = [bool(rng.random() < 0.55) for _ in clumps]
    h, owner, dif = bumps(clumps)
    gapf = 0.55 * tnoise(rng, 8) + 0.45 * rng.random((N, N))
    gap = owner < 0
    # the gaps between blossom clumps: 30% see-through holes, then deep shade, shade, a few green leaves
    glv = np.full((N, N), 9)
    gy, gx = np.nonzero(gap)
    order = np.argsort(gapf[gy, gx], kind='stable')
    for rank, j in enumerate(order):
        q = rank / len(order)
        glv[gy[j], gx[j]] = 0 if q < 0.3 else (1 if q < 0.58 else (2 if q < 0.82 else 3))
    a = new()
    for y in range(N):
        for x in range(N):
            i = owner[y, x]
            if i < 0:
                g = glv[y, x]
                if g == 0:
                    continue                      # a see-through hole
                put(a, x, y, [None, LEAF_DEEP, LEAF_SHADE, LF_GREEN][min(g, 3)])
                continue
            light, base, shade = (CL_WHITE, CL_BASE, CL_2) if white[i] else (K_PALE, K_LIGHT, K_BASE)
            d = dif[y, x]
            col = light if d > 0.78 else (base if d > 0.42 else shade)
            if creased(h, owner, y, x, 0.2):
                col = shade
            put(a, x, y, col)
    for i, (cx, cy, r, z) in enumerate(clumps):  # tiny gold hearts in some blossoms
        if i % 2 == 0:
            put(a, int(cx) % N, int(cy) % N, G_BASE)
    for y in range(N):                            # a leaf tucked under the lower-right of a few clumps
        for x in range(N):
            i = owner[y, x]
            if i >= 0 and i % 3 == 1 and owner[(y + 1) % N, x] < 0 and a[(y + 1) % N, x, 3]:
                put(a, x, (y + 1) % N, LF_GREEN if (x + y) % 2 else LF_DGREEN)
    return a


def tex_skywood_sapling():
    return from_map([
        '................',
        '................',
        '......wWWw......',
        '.....wWWYWs.....',
        '..KK.sWWWWs.....',
        '.KKYKk.sss..KK..',
        '.kKKKk..T..KKYK.',
        '..kkk.t.T..kKKk.',
        '......tTT.t.kk..',
        '.......TTt......',
        '...gG..TT..Gg...',
        '....gG.TT.Gg....',
        '......tTT.......',
        '.......Tt.......',
        '.......Tt.......',
        '......tTTt......',
    ], {'T': B_LIGHT, 't': B_GREY, 'w': CL_2, 'W': CL_WHITE, 'Y': G_BASE, 's': CL_3,
        'K': K_LIGHT, 'k': K_BASE, 'G': LF_GREEN, 'g': LF_DGREEN})


def veilcloth(light, base, shade, deep, seed):
    """A fine twill: diagonal ribs lit on their top-left, and a faint gold weft every 4 rows
    that shows where it passes over the ribs (two pixels on, two under)."""
    rng = np.random.default_rng(seed)
    rib = [light, base, base, shade]
    g = rng.random((N, N))
    a = new()
    for y in range(N):
        for x in range(N):
            k = (x - y) % 4
            col = rib[k]
            if k == 3 and g[y, x] < 0.12:
                col = deep
            over = (1, 2) if (y // 4) % 2 == 0 else (3, 0)   # alternate rows of gold cross the ribs offset
            if y % 4 == 2 and k in over:
                col = G_LIGHT if k == over[0] else '#fbf0cc'
            put(a, x, y, col)
    return a


def tex_white_veilcloth():
    return veilcloth(CR_LIGHT, CR_BASE, CR_SHADE, CR_DARK, 1111)


def tex_sky_veilcloth():
    return veilcloth(K_LIGHT, K_BASE, K_MID, K_DARK, 1112)


def tex_rose_veilcloth():
    return veilcloth(R_LIGHT, R_BASE, R_MID, R_DARK, 1113)


WIND_SWIRL = [  # two arms, gold (G) and sky (B), around a pale centre (*); 180-degree symmetric
    '................',
    '.....BB.........',
    '....BB..........',
    '...B..GGGGGG....',
    '..BB.GG....GG...',
    '..B.GGBBBBB.GG..',
    '..B.G.B...BB.G..',
    '..B.G.B**G.B.G..',
    '..B.G.B**G.B.G..',
    '..B.GG...G.B.G..',
    '..BB.GGGGGBB.G..',
    '...BB....BB.GG..',
    '....BBBBBB..G...',
    '..........GG....',
    '.........GG.....',
    '................',
]


def tex_wind_stone_top():
    a = tex_polished_skystone()
    for y, row in enumerate(WIND_SWIRL):
        for x, ch in enumerate(row):
            s = (x - 7.5) + (y - 7.5)
            if ch == 'G':
                put(a, x, y, G_LIGHT if s < -3 else (G_MID if s > 3 else G_BASE))
            elif ch == 'B':
                put(a, x, y, K_LIGHT if s < -3 else (K_MID if s > 3 else K_BASE))
    put(a, 7, 7, '#ffffff')
    put(a, 8, 7, K_PALE)
    put(a, 7, 8, K_PALE)
    put(a, 8, 8, K_LIGHT)
    return a


def tex_wind_stone():
    a = tex_polished_skystone()
    band = [                      # a band of gold wind-scrolls with sky-blue beads between
        '..GGG.....GGG...',
        '.G...G...G...G..',
        '.G.G.G.k.G.G.G.k',
        '.G..GG...G..GG..',
        'kGG.....kGG.....',
    ]
    for x in range(1, 15):
        put(a, x, 4, S_MID)
        put(a, x, 5, S_BASE)
        put(a, x, 11, S_PALE)
    for j, row in enumerate(band):
        for x, ch in enumerate(row):
            if 0 < x < 15:
                if ch == 'G':
                    put(a, x, 6 + j, G_LIGHT if j == 0 else (G_BASE if j < 3 else G_MID))
                elif ch == 'k':
                    put(a, x, 6 + j, K_BASE)
    return a


def tex_wind_chime_block():
    a = new()
    # skywood surface (0,0,8,8)
    for y in range(8):
        for x in range(8):
            col = W_BASE
            if y == 0 or x == 0:
                col = W_LIGHT
            elif y == 7 or x == 7:
                col = W_DARK
            elif y in (2, 5) and (x + y) % 5 != 0:
                col = W_MID
            put(a, x, y, col)
    # gold tube (8,0,2,16) and silver tube (10,0,2,16): lit left column, vertical gradient
    for y in range(16):
        put(a, 8, y, G_SHINE if y < 3 else (G_LIGHT if y < 11 else G_BASE))
        put(a, 9, y, G_BASE if y < 5 else (G_MID if y < 12 else G_DARK))
        put(a, 10, y, AG_LIGHT if y < 10 else AG_BASE)
        put(a, 11, y, AG_BASE if y < 5 else (AG_DARK if y < 13 else AG_DEEP))
    # sky-blue glass bead (12,0,4,4)
    bead = ['bKKb', 'KPKk', 'KKkd', 'bkdd']
    lg = {'P': K_PALE, 'K': K_LIGHT, 'k': K_BASE, 'b': K_MID, 'd': K_DARK}
    for y, row in enumerate(bead):
        for x, ch in enumerate(row):
            put(a, 12 + x, y, lg[ch])
    # cord (12,4,1,12)
    for y in range(4, 16):
        put(a, 12, y, G_DARK if y % 2 else G_DEEP)
    return a


def tex_wind_harp():
    a = new()
    # carved skywood frame (0,0,16,6)
    for x in range(16):
        put(a, x, 0, W_LIGHT)
        put(a, x, 1, W_BASE)
        put(a, x, 2, W_DARK if x % 4 == 1 else W_BASE)
        put(a, x, 3, W_DARK if x % 4 in (0, 2) else W_BASE)
        put(a, x, 4, W_MID if x % 4 != 1 else W_BASE)
        put(a, x, 5, W_DARK)
    # gold fittings (0,6,8,4)
    for y in range(6, 10):
        for x in range(8):
            col = G_BASE
            if y == 6 or x == 0:
                col = G_LIGHT
            elif y == 9 or x == 7:
                col = G_DARK
            put(a, x, y, col)
    for rx in (2, 5):
        put(a, rx, 7, G_SHINE)
        put(a, rx + 1, 8, G_MID)
    # strings (8,6,8,10): gold / silver, 1 px apart
    for i, x in enumerate(range(8, 16, 2)):
        for y in range(6, 16):
            if i % 2 == 0:
                put(a, x, y, G_LIGHT if y < 12 else G_BASE)
            else:
                put(a, x, y, AG_LIGHT if y < 12 else AG_BASE)
    # sky-blue inlay (0,10,8,6)
    for y in range(10, 16):
        for x in range(8):
            col = K_BASE
            if y == 10 or x == 0:
                col = K_LIGHT
            elif y == 15 or x == 7:
                col = K_DARK
            elif (x + y) == 16:
                col = K_PALE
            put(a, x, y, col)
    return a


def tex_sky_lantern_block():
    a = new()
    lg = {'G': G_LIGHT, 'g': G_DARK, 'h': G_MID, 'b': K_MID, 'K': K_BASE, 'P': K_LIGHT, 'W': K_PALE,
          'B': G_BASE, 'd': G_DEEP}
    side = [
        'hGGGGh',
        'GbKKbg',
        'GKPPKg',
        'GKWPKg',
        'GKPPKg',
        'GbKKbg',
        'hggggh',
    ]
    for y, row in enumerate(side):          # body sides (0,2) 6x7
        for x, ch in enumerate(row):
            put(a, x, 2 + y, lg[ch])
    top = [
        'hGGGGh',
        'GBBBBg',
        'GBGBBg',
        'GBBBhg',
        'GBBhhg',
        'hggggd',
    ]
    for y, row in enumerate(top):           # body top/bottom (0,9) 6x6; the cap top reuses its inner (1,10) 4x4
        for x, ch in enumerate(row):
            put(a, x, 9 + y, lg[ch])
    for x in range(1, 5):                   # cap sides (1,0) 4x2
        put(a, x, 0, G_LIGHT if x < 4 else G_BASE)
        put(a, x, 1, G_MID if x < 4 else G_DARK)
    for y0 in (1, 10):                      # handle (11,1) and (11,10) 3x2: a little arch
        for x in range(11, 14):
            put(a, x, y0, G_DARK)
        put(a, 11, y0 + 1, G_DEEP)
        put(a, 13, y0 + 1, G_DEEP)
    return a


# =========================================================================================
#                                           ITEMS
# =========================================================================================
def item_sky_scale():
    return from_map([
        '................',
        '.....oooqqq.....',
        '...ooVVVVVVqq...',
        '..oKKPPPPPPRRq..',
        '.oKKPWWPPPPPRrq.',
        '.okKWWPPPPPPRrq.',
        '.okKPPpppppPRrq.',
        '.okKPpPPPPPpRrq.',
        '.okKPPPPPPPPRrq.',
        '..okKPpppppRrq..',
        '..okKpPPPPpRrq..',
        '...okKPPPPRrq...',
        '....okKPPRrq....',
        '.....okVVrq.....',
        '......oVVq......',
        '.......oq.......',
    ], {'o': '#3f5a80', 'q': '#86475d', 'V': '#cdc2ec', 'K': K_LIGHT, 'k': K_BASE, 'R': R_LIGHT, 'r': R_BASE,
        'P': '#eef1fa', 'p': '#d6ddef', 'W': '#ffffff'})


def item_sky_peach():
    a = new()
    cx, cy, R = 7.6, 9.4, 5.3
    L = np.array([-0.5, -0.65, 0.58])
    L /= np.linalg.norm(L)
    ramp = ['#fff7e2', '#f9e3a0', '#f4cb8a', '#eeb09a', '#e396a6', '#c97a8e']
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d2 = dx * dx + dy * dy
            if d2 > R * R:
                continue
            nz = math.sqrt(max(0.0, R * R - d2)) / R
            lit = float(np.array([dx / R, dy / R, nz]) @ L)
            v = 1 - (lit + 0.15) / 1.15 + 0.12 * (dx + dy) / R
            put(a, x, y, ramp[int(max(0, min(len(ramp) - 1, v * len(ramp))))])
    for (x, y) in [(8, 5), (7, 6), (7, 7), (7, 8), (7, 9)]:   # the cleft running down from the stem
        put(a, x, y, '#e8a59a')
    put(a, 5, 6, '#ffffff')
    a = outline(a, pal=['#7a5e48', '#8a4a5c', '#6a3c4e'])
    stem_leaf = {(7, 2): '#7a5a3a', (8, 3): '#7a5a3a', (9, 3): LF_DGREEN, (9, 2): LF_GREEN, (10, 2): LF_GREEN,
                 (10, 1): LF_GREEN, (11, 1): LF_DGREEN, (11, 2): LF_DGREEN, (12, 1): '#3f6b3a',
                 (10, 3): '#3f6b3a', (11, 0): '#3f6b3a', (12, 0): '#3f6b3a', (9, 1): '#3f6b3a',
                 (10, 0): '#3f6b3a', (8, 2): '#3f6b3a', (13, 1): '#3f6b3a', (12, 2): '#3f6b3a'}
    for (x, y), col in stem_leaf.items():
        put(a, x, y, col)
    return a


def item_windsong_flute():
    a = new()
    for y in range(N):
        for x in range(N):
            s, u = x + y, x - y          # s: across the flute, u: along it (bottom-left -12 .. top-right 12)
            if s in (15, 16) and -12 <= u <= 12:
                upper = s == 15
                col = W_LIGHT if upper else W_BASE
                if abs(u) >= 11 or u in (6, 7) or u in (-8, -9):
                    col = G_LIGHT if upper else G_BASE
                put(a, x, y, col)
    for u in (9, 3, -1, -5):            # embouchure hole, then three finger holes
        put(a, (15 + u) // 2, (15 - u) // 2, '#5b4426')
    a = outline(a, 0.5, (16, 8, 2), pal=['#80643a', '#62492a'])
    # a little rose tassel hanging from the upper gold band
    for (x, y, col) in [(11, 6, R_DARK), (11, 7, R_MID), (11, 8, R_MID), (10, 9, R_BASE), (11, 9, R_LIGHT),
                        (12, 9, R_MID), (10, 10, R_DARK), (11, 10, R_BASE), (12, 10, R_DARK)]:
        put(a, x, y, col)
    return a


def catmull(pts, steps=40):
    """Points along a Catmull-Rom curve through pts."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(steps):
            t = k / steps
            out.append(tuple(0.5 * (2 * p1[j] + (p2[j] - p0[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (3 * p1[j] - p0[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    out.append(tuple(pts[-1]))
    return out


def item_cirrus_veil():
    """A veil draped in an arch: sky blue at one end, cloud white over the fold, rose at the
    hanging end; gold thread along the outer edge, fringe on the end and a wisp of ribbon."""
    a = new()
    path = catmull([(2.2, 5.4), (5.4, 3.0), (9.2, 4.0), (11.6, 7.2), (12.2, 11.4)])
    dist = [0.0]
    for p, q in zip(path, path[1:]):
        dist.append(dist[-1] + math.dist(p, q))
    stages = [(K_LIGHT, K_BASE, K_MID), (K_PALE, K_LIGHT, K_BASE), (CL_WHITE, CL_BASE, CL_2),
              ('#fdf0f2', R_LIGHT, R_BASE), (R_LIGHT, R_BASE, R_MID)]
    w = 4.0
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        l = math.dist(path[i], path[i + 1]) or 1e-6
        nx, ny = (y1 - y0) / l, -(x1 - x0) / l
        if ny > 0:
            nx, ny = -nx, -ny                       # the gold edge stays on the outer (upper) side
        light, base, shade = stages[min(4, int(dist[i] / dist[-1] * 5))]
        for k in range(int(w * 6) + 1):
            o = -w / 2 + k / 6
            if o > w / 2 - 0.55:
                col = G_BASE
            elif o > w / 2 - 1.5:
                col = light
            elif o > -w / 2 + 0.9:
                col = base
            else:
                col = shade
            put(a, int(math.floor(x0 + nx * o)), int(math.floor(y0 + ny * o)), col)
    for (x, y, col) in [(10, 13, R_BASE), (12, 13, R_MID), (14, 13, G_BASE), (1, 4, K_BASE), (1, 6, K_MID)]:
        put(a, x, y, col)                           # fringe on both ends
    a = outline(a, 0.42, (16, 10, 34), pal=['#3f5577', '#5a5878', '#7a4a5e', '#7a6030'])
    for (x, y) in [(8, 13), (7, 14), (6, 14), (5, 15)]:  # a wisp of ribbon blowing off the hem
        put(a, x, y, R_DARK if y < 15 else R_MID)
    return a


def item_wind_chime():
    a = from_map([
        '................',
        '................',
        '..WWWWWWWWWWWW..',
        '.wwwwwwwwwwwwwv.',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
    ], {'W': W_LIGHT, 'w': W_MID, 'v': W_DARK})
    a = outline(a, 0.4, (10, 4, 4), pal=['#5a4630'])
    put(a, 7, 0, G_DARK)
    put(a, 8, 0, G_DARK)
    tubes = [(1, 11, G_LIGHT, G_MID, G_DEEP), (4, 13, AG_LIGHT, AG_DARK, AG_DEEP),
             (10, 12, AG_LIGHT, AG_DARK, AG_DEEP), (13, 14, G_LIGHT, G_MID, G_DEEP)]
    for (x, end, lit, shade, cap) in tubes:
        put(a, x + (1 if x < 8 else 0), 5, '#7a5a2a')   # its string
        for y in range(6, end):
            put(a, x, y, lit)
            put(a, x + 1, y, shade)
        put(a, x, end, cap)
        put(a, x + 1, end, cap)
    for y in range(5, 11):                             # the clapper bead on its cord
        put(a, 7 + (y % 2), y, '#7a5a2a')
    for (x, y, col) in [(7, 11, K_PALE), (8, 11, K_LIGHT), (7, 12, K_BASE), (8, 12, K_DARK),
                        (6, 11, '#2f4a6a'), (6, 12, '#2f4a6a'), (9, 11, '#2f4a6a'), (9, 12, '#2f4a6a'),
                        (7, 13, '#2f4a6a'), (8, 13, '#2f4a6a')]:
        put(a, x, y, col)
    return a


def item_sky_lantern():
    a = new()
    lg = {'G': G_LIGHT, 'B': G_BASE, 'g': G_MID, 'h': G_DARK, 'k': K_BASE, 'K': K_LIGHT, 'P': K_PALE,
          'b': K_MID, 'W': '#ffffff'}
    rows = {
        4: '......GBBg......',
        5: '....GGBBBBgh....',
        6: '....GbKKKbbh....',
        7: '....GKPPPKbh....',
        8: '....GKPWPKbh....',
        9: '....GKPPPKbh....',
        10: '....GbKKKbbh....',
        11: '....BBgggghh....',
        12: '.....hhhhhh.....',
    }
    for y, row in rows.items():
        for x, ch in enumerate(row):
            if ch != '.':
                put(a, x, y, lg[ch])
    a = outline(a, 0.38, (8, 4, 2), pal=['#5c4318'])
    for (x, y) in [(7, 1), (8, 1), (6, 2), (9, 2)]:
        put(a, x, y, '#5c4318')
    return a


BLOCK_PAINTERS = {
    'skystone': tex_skystone,
    'skystone_bricks': tex_skystone_bricks,
    'polished_skystone': tex_polished_skystone,
    'gilded_skystone': tex_gilded_skystone,
    'skystone_pillar': tex_skystone_pillar,
    'skystone_pillar_top': tex_skystone_pillar_top,
    'cloud_block': tex_cloud_block,
    'skywood_log': tex_skywood_log,
    'skywood_log_top': tex_skywood_log_top,
    'skywood_planks': tex_skywood_planks,
    'skywood_leaves': tex_skywood_leaves,
    'skywood_sapling': tex_skywood_sapling,
    'white_veilcloth': tex_white_veilcloth,
    'sky_veilcloth': tex_sky_veilcloth,
    'rose_veilcloth': tex_rose_veilcloth,
    'wind_chime': tex_wind_chime_block,
    'wind_harp': tex_wind_harp,
    'sky_lantern': tex_sky_lantern_block,
    'wind_stone': tex_wind_stone,
    'wind_stone_top': tex_wind_stone_top,
}

ITEM_PAINTERS = {
    'sky_scale': item_sky_scale,
    'sky_peach': item_sky_peach,
    'windsong_flute': item_windsong_flute,
    'cirrus_veil': item_cirrus_veil,
    'wind_chime': item_wind_chime,
    'sky_lantern': item_sky_lantern,
}

# block textures that are model atlases or sprites, not seamless full-block faces
NOT_TILING = {'wind_chime', 'wind_harp', 'sky_lantern', 'skywood_sapling'}


# =========================================================================================
#                                     sheets and colours
# =========================================================================================
def font(size):
    for name in ('arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def checker(w, h, s=8):
    img = Image.new('RGBA', (w, h), (60, 64, 76, 255))
    d = ImageDraw.Draw(img)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=(74, 78, 92, 255))
    return img


def contact_sheet(entries, path, scale=8, cols=7, tile=1, title=''):
    cell = N * scale * tile
    pad, label_h, head = 24, 20, 34
    rows = (len(entries) + cols - 1) // cols
    W = cols * (cell + pad) + pad
    H = head + rows * (cell + label_h + pad) + pad
    sheet = Image.new('RGBA', (W, H), (34, 36, 44, 255))
    d = ImageDraw.Draw(sheet)
    f, ft = font(13), font(18)
    d.text((pad, 8), title, fill=(230, 232, 240, 255), font=ft)
    for i, (label, arr) in enumerate(entries):
        r, c = divmod(i, cols)
        x0 = pad + c * (cell + pad)
        y0 = head + r * (cell + label_h + pad)
        img = Image.fromarray(arr, 'RGBA')
        if tile > 1:
            big = Image.new('RGBA', (N * tile, N * tile))
            for ty in range(tile):
                for tx in range(tile):
                    big.paste(img, (tx * N, ty * N))
            img = big
        img = img.resize((cell, cell), Image.NEAREST)
        bg = checker(cell, cell)
        bg.alpha_composite(img)
        sheet.paste(bg, (x0, y0))
        d.text((x0, y0 + cell + 3), label, fill=(220, 222, 232, 255), font=f)
    sheet.save(path)


def avg_color(arr, region=None):
    if region:
        x, y, w, h = region
        arr = arr[y:y + h, x:x + w]
    px = arr.reshape(-1, 4)
    px = px[px[:, 3] > 0][:, :3].astype(float)
    return [int(round(v)) for v in px.mean(0)]


def mod_colors(blocks):
    out = {}
    for bid, spec in catalog.BLOCKS.items():
        shape = spec['shape']
        if shape in ('cube', 'leaves', 'sapling'):
            out[bid] = avg_color(blocks[bid])
        elif shape in ('pillar', 'log'):
            out[bid] = avg_color(blocks[bid])
            out[bid + '_top'] = avg_color(blocks[bid + '_top'])
        elif shape == 'wood':
            out[bid] = avg_color(blocks[spec['base']])
    for bid, spec in catalog.BLOCKS.items():
        if spec['shape'] in ('stairs', 'slab', 'wall', 'fence', 'fence_gate', 'carpet'):
            out[bid] = out[spec['base']]
    # hand-made models: a colour that stands for the whole thing
    out['wind_chime'] = avg_color(blocks['wind_chime'], (8, 0, 4, 16))     # the gold and silver tubes
    out['wind_harp'] = avg_color(blocks['wind_harp'], (0, 0, 16, 6))       # the carved frame
    out['sky_lantern'] = avg_color(blocks['sky_lantern'], (1, 3, 4, 5))    # its glowing sky-blue glass
    out['wind_stone'] = avg_color(blocks['wind_stone'])
    return dict(sorted(out.items()))


def main():
    want_blocks = catalog.block_textures()
    want_items = catalog.item_textures()
    missing = [n for n in want_blocks if n not in BLOCK_PAINTERS] + \
              ['item/' + n for n in want_items if n not in ITEM_PAINTERS]
    if missing:
        raise SystemExit('no painter for: ' + ', '.join(missing))
    BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blocks = {n: BLOCK_PAINTERS[n]() for n in want_blocks}
    items = {n: ITEM_PAINTERS[n]() for n in want_items}
    for n, arr in blocks.items():
        assert arr.shape == (N, N, 4)
        Image.fromarray(arr, 'RGBA').save(BLOCK_DIR / (n + '.png'))
    for n, arr in items.items():
        assert arr.shape == (N, N, 4)
        Image.fromarray(arr, 'RGBA').save(ITEM_DIR / (n + '.png'))

    entries = [('block/' + n, a) for n, a in blocks.items()] + [('item/' + n, a) for n, a in items.items()]
    contact_sheet(entries, OUT_DIR / 'sheet.png', 8, 7, 1, 'Sky Friends textures (8x)')
    # full-block faces first; the model atlases and the sapling sprite last (tiling them is only a sanity look)
    tiled = [(n, a) for n, a in blocks.items() if n not in NOT_TILING] + \
            [(n + ' (atlas)', a) for n, a in blocks.items() if n in NOT_TILING]
    contact_sheet(tiled, OUT_DIR / 'tiled.png', 4, 5, 4, 'Block textures tiled 4x4')

    colors = mod_colors(blocks)
    COLORS_JSON.write_text('{\n' + ',\n'.join(' %s: %s' % (json.dumps(k), json.dumps(v))
                                               for k, v in colors.items()) + '\n}\n')
    print('wrote %d block textures, %d item textures' % (len(blocks), len(items)))
    print('sheets in', OUT_DIR)
    print('colours in', COLORS_JSON)


if __name__ == '__main__':
    main()
