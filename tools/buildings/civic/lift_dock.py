"""The Lift Dock: the landing of the wind lift on the rim of the central island."""
from kit import building
from civic.cirri_parts import (BRICKS, FENCE, GILDED, PILLAR, POL_SLAB, POL_STAIRS, POLISHED, WOOD_STAIRS, check,
                               chime, lamp, slab, stair)

W, H, D = 9, 7, 13
SHAFT = (3, 5, 8, 10)          # x0, x1, z0, z1 of the 3x3 lift shaft, open all the way down
ARCH_Z = 1


@building('lift_dock', 'cirri', 'dock', (W, H, D), door=4, residents=0, job='windkeeper', rim=True,
          about='The landing of the wind lift: a polished skystone deck jutting out over the sky, a gilded welcome '
                'arch hung with chimes, railed walks, and the open lift shaft with its sign. Stand in the wind '
                'below to rise; hold sneak in the shaft to sink.')
def lift_dock(b):
    sx0, sx1, sz0, sz1 = SHAFT
    # ---- the deck: polished skystone, brick edges, a gilded rim round the shaft
    for x in range(W):
        for z in range(D):
            edge = x in (0, W - 1) or z == D - 1
            rim = sx0 - 1 <= x <= sx1 + 1 and sz0 - 1 <= z <= sz1 + 1
            b.set(x, 0, z, BRICKS if edge else GILDED if rim else POLISHED)
    b.clear(sx0, 0, sz0, sx1, H - 1, sz1)            # the shaft: deck cells and everything above are open air
    b.spot('lift', 4, 0, 9)

    # ---- rails: skywood fences between skystone posts with sky lanterns along both sides and the back
    posts = [(x, z) for x in (0, W - 1) for z in (ARCH_Z, 5, 9, D - 1)]
    for x in (0, W - 1):
        for z in range(ARCH_Z, D):
            b.set(x, 1, z, FENCE)
    for x in (1, W - 2):
        b.set(x, 1, ARCH_Z, FENCE)
        b.set(x, 1, D - 1, FENCE)
    for x, z in posts:
        b.set(x, 1, z, PILLAR)
        lamp(b, x, 2, z)
    # the shaft's rail: west, east and south sides; the north side stays open as the way in
    for z in range(sz0, sz1 + 1):
        b.set(sx0 - 1, 1, z, FENCE)
        b.set(sx1 + 1, 1, z, FENCE)
    for x in range(sx0 - 1, sx1 + 2):
        b.set(x, 1, sz1 + 1, FENCE)
    for x, z in ((sx0 - 1, sz0), (sx1 + 1, sz0)):
        b.set(x, 1, z, PILLAR)                        # posts flanking the way in to the shaft
        lamp(b, x, 2, z)
    # behind the shaft: a low brick plinth with a tall lantern post bearing the sign
    for x in range(sx0 - 1, sx1 + 2):
        b.set(x, 1, D - 1, BRICKS)
        slab(b, x, 2, D - 1, POL_SLAB)
    for y in range(1, 4):
        b.set(4, y, D - 1, PILLAR)
    b.set(4, 4, D - 1, GILDED)
    lamp(b, 4, 5, D - 1)
    b.sign(4, 2, D - 2, ["Wind Stone Lift", "Stand in the wind", "to rise. Hold sneak", "to sink."],
           facing='north', wood='birch')

    # ---- the welcome arch over the entrance
    for x in (2, 6):
        for y in range(1, 4):
            b.set(x, y, ARCH_Z, PILLAR)
    b.clear(3, 1, ARCH_Z, 5, 2, ARCH_Z)
    stair(b, 3, 3, ARCH_Z, POL_STAIRS, 'west', 'top')
    stair(b, 5, 3, ARCH_Z, POL_STAIRS, 'east', 'top')
    for x in range(1, 8):
        b.set(x, 4, ARCH_Z, GILDED if x in (2, 4, 6) else POLISHED)
    for x in range(2, 7):
        if x != 4:
            slab(b, x, 5, ARCH_Z, POL_SLAB)
    b.set(4, 5, ARCH_Z, GILDED)
    lamp(b, 4, 6, ARCH_Z)
    for x in (1, 4, 7):
        chime(b, x, 3, ARCH_Z)
    b.spot('work', 1, 1, ARCH_Z + 1)

    # ---- benches for waiting guests, flowers
    for z in (3, 4):
        stair(b, 1, 1, z, WOOD_STAIRS, 'west')
        stair(b, W - 2, 1, z, WOOD_STAIRS, 'east')
    b.set(1, 1, 6, 'potted_azure_bluet')
    b.set(W - 2, 1, 6, 'potted_pink_tulip')
    b.set(1, 1, 11, 'potted_allium')
    b.set(W - 2, 1, 11, 'potted_lily_of_the_valley')
    check(b)
