"""The Lantern Spire: a slender skystone tower crowned with a cluster of sky lanterns under a gilded cap."""
from kit import building
from civic.cirri_parts import (BRICKS, FENCE, GILDED, PILLAR, POL_STAIRS, POLISHED, check, chime, column, inward,
                               lamp, square_ring, stair)

C = 3            # the centre column (3, 3)
TOP = 14         # the shaft's walls rise y 1..TOP; the balcony floor is TOP + 1
SLITS = ((4, 5), (8, 9), (12, 13))


@building('lantern_spire', 'cirri', 'civic', (7, 22, 7), door=3, residents=0, job='lamplighter',
          about='A slender tower of skystone with sky-glass slits and a ladder inside, a little balcony near the top '
                'and an open lantern stage where a cluster of sky lanterns hangs under a gilded cap.')
def lantern_spire(b):
    b.fill(0, 0, 0, 6, 0, 6, POLISHED)
    for x, z in square_ring(0, 6):
        b.set(x, 0, z, BRICKS)
    b.set(C, 0, 0, POLISHED)
    # a sloped plinth round the foot
    for x, z in square_ring(0, 6):
        if (x, z) != (C, 0):
            stair(b, x, 1, z, POL_STAIRS, inward(x, z, 0, 6) or ('south' if z == 0 else 'north'))

    # ---- the shaft: 5x5, pillar corners, brick faces, polished string courses, sky-glass slits
    for x, z in square_ring(1, 5):
        corner = x in (1, 5) and z in (1, 5)
        for y in range(1, TOP + 1):
            if corner:
                b.set(x, y, z, PILLAR)
            elif y in (6, 10):
                b.set(x, y, z, POLISHED)
            else:
                b.set(x, y, z, BRICKS)
    for x, z in ((C, 1), (1, C), (5, C)):         # the south face backs the ladder, so it stays solid
        for pair in SLITS:
            for y in pair:
                b.set(x, y, z, 'light_blue_stained_glass_pane')
    b.clear(C, 1, 1, C, 2, 1)                 # the doorway
    b.set(C, 3, 1, GILDED)
    b.set(C, 4, 1, BRICKS)                    # no slit right over the door
    b.set(C, 5, 1, 'light_blue_stained_glass_pane')

    # ---- inside: the ladder up the south wall, lanterns on corner brackets
    for y in range(1, TOP + 2):
        b.set(C, y, 4, 'ladder', facing='north', waterlogged=False)
    b.set(2, 5, 2, POLISHED)
    lamp(b, 2, 6, 2)
    b.set(4, 10, 2, POLISHED)
    lamp(b, 4, 11, 2)
    b.set(4, 1, 2, 'potted_azure_bluet')

    # ---- the balcony: a 7x7 floor on corbels, chimes under its corners, a skywood rail
    y = TOP + 1
    b.fill(0, y, 0, 6, y, 6, POLISHED)
    b.set(C, y, 4, 'ladder', facing='north', waterlogged=False)   # the ladder comes up through the floor
    for x, z in square_ring(0, 6):
        facing = inward(x, z, 0, 6)
        if facing:
            stair(b, x, TOP, z, POL_STAIRS, facing, 'top')
            b.set(x, y + 1, z, FENCE)
        else:
            b.set(x, y, z, GILDED)
            chime(b, x, TOP, z)
            lamp(b, x, y + 1, z)

    # ---- the lantern stage: four pillars, a cluster of sky lanterns under a gilded cap
    for x, z in ((2, 2), (4, 2), (2, 4), (4, 4)):
        column(b, x, y + 1, y + 3, z, PILLAR)
    cap = y + 4
    b.fill(2, cap, 2, 4, cap, 4, GILDED)
    for x, z in square_ring(1, 5):
        facing = inward(x, z, 1, 5)
        stair(b, x, cap, z, POL_STAIRS, facing or ('south' if z == 1 else 'north'))
        if facing is None:
            chime(b, x, cap - 1, z)
    for x, z in ((C, C), (C, 2), (2, C), (4, C), (C, 4)):
        lamp(b, x, cap - 1, z, hanging=True)
    b.spot('work', C, y + 1, 2)
    # the crown: a stepped gilded cap with one more lantern on its point
    for x, z in square_ring(2, 4):
        stair(b, x, cap + 1, z, POL_STAIRS, inward(x, z, 2, 4) or ('south' if z == 2 else 'north'))
    b.set(C, cap + 1, C, GILDED)
    lamp(b, C, cap + 2, C)
    check(b)
