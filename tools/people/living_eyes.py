"""Living eyes, the same eyes Village Friends residents have.

The face itself is painted as clean skin. The eyes, brows, mouth and blush are tiny planes in front of
it (built and animated by the client's LivingEyes class), and each plane samples one pixel of a face
swatch strip baked into the texture here: eleven colours on one row.

The colours follow Village Friends' FaceDetails exactly: the eye white, the iris, the skin (for the lid
that follows a blink), and from those the brow and lash (from the hair), the neck shadow, the Starlit
upper white (the iris lifted toward white), the pupil, two lip tones and a blush.
"""
from mobkit import hexc

# Order of the strip; the client reads the same order (LivingEyes.Swatch).
ORDER = ("white", "iris", "lid", "brow", "lash", "shadow", "tint", "pupil", "lip", "rose_lip", "blush")
VF_WHITE = "#ede0cd"     # every Village Friends complexion uses this eye white


def _round(v):
    return int(v + 0.5)       # Java's Math.round for positive values


def _shade(c, f):
    r, g, b, a = hexc(c)
    return (_round(r * f), _round(g * f), _round(b * f), a)


def _blend(a, b, t):
    a, b = hexc(a), hexc(b)
    return (_round(a[0] + (b[0] - a[0]) * t), _round(a[1] + (b[1] - a[1]) * t), _round(a[2] + (b[2] - a[2]) * t), a[3])


def colours(skin, iris, hair, white=VF_WHITE):
    return {
        "white": hexc(white),
        "iris": hexc(iris),
        "lid": hexc(skin),
        "brow": _shade(hair, 0.8),
        "lash": _shade(hair, 0.35),
        "shadow": _shade(skin, 0.9),
        "tint": _blend(_blend(iris, "#ffffff", 0.4), white, 0.68),
        "pupil": _shade(iris, 0.5),
        "lip": _blend(_shade(skin, 0.78), "#a04648", 0.18),
        "rose_lip": _blend(_shade(skin, 0.84), "#cd4e62", 0.42),
        "blush": _blend(skin, "#ec6876", 0.32),
    }


def bake(model, u, v, skin, iris, hair, white=VF_WHITE):
    """Write the strip at (u..u+10, v) and record where it is in the geometry file."""
    cols = colours(skin, iris, hair, white)
    for i, name in enumerate(ORDER):
        model.image.putpixel((u + i, v), cols[name])
    model.extra["face"] = [u, v]
