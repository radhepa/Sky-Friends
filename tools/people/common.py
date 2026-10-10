"""Shared painting helpers for the Sky Friends people models (palettes live with each people)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from mobkit import shade, mix, hexc  # noqa: E402,F401

SIDES = ("front", "back", "left", "right")


def tone(c, y, col, k=0.14):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k * 1.4
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def ring_u(c, w, d):
    """Column offset of a side face when walking round a box, so patterns continue round corners."""
    return {"front": 0, "left": w, "back": w + d, "right": w + d + w}.get(c.face, 0)


def glow_as(c, x, y, base, light):
    """A lit pixel whose emissive layer is a darker shade, so the additive glow keeps its hue."""
    if not c.inside(x, y):
        return
    c.set(x, y, base)
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), hexc(light))


def painter(fn):
    """fn(c, x, y) -> colour or None, applied to every pixel of a face (None leaves it see-through)."""
    def run(c):
        for y in range(c.h):
            for x in range(c.w):
                col = fn(c, x, y)
                if col is not None:
                    c.set(x, y, col)
    return run


def gradient(stops, t):
    """Colour at t (0..1) along a list of colour stops."""
    t = max(0.0, min(1.0, t))
    if len(stops) == 1:
        return hexc(stops[0])
    seg = t * (len(stops) - 1)
    i = min(int(seg), len(stops) - 2)
    return mix(stops[i], stops[i + 1], seg - i)


def face_paint(c, eyes, skin, *, brow=None, mouth=None, blush=None, liner=None):
    """A front face: eyes is a list of (x, y, colour) pixels drawn over skin noise."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(skin))
    for (x, y, col) in eyes:
        c.set(x, y, col)
    for group in (brow, liner, mouth, blush):
        for (x, y, col) in group or ():
            c.set(x, y, col)
