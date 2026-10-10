"""The large nest house: an octagonal two-storey home for a family of four.

A white octagonal hall (a recessed porch under a rose veilcloth valance, a spiral stair winding up a
skystone column) carries a narrower nest drum set to the front, so its roof becomes a railed terrace at the
back with a veilcloth awning over the arch the Cirri fly in by. Upstairs: four nests. On top: a stepped
dome with a gilded crown and a sky lantern finial."""
from kit import building
from homes.style import (BRICKS, POLISHED, GILDED, PILLAR, P_STAIRS, P_SLAB, PLANKS, FENCE, GLASS,
                         CARPET, CLOTH, octagon, rim, inside, put, column, roof_ring, lantern, chime, nest,
                         clear_mask, round_window)


def spiral(b, y_floor, cx, cz, steps):
    """Slab steps winding clockwise round the column at (cx, cz), half a block per step, starting on the
    west side; the last step lands on the upper floor at y_floor + 1 + (steps - 1) // 2."""
    ring = [(-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1)]
    cells = []
    for i in range(steps):
        dx, dz = ring[i % 8]
        half = i + 1                       # rise in half blocks above the floor's top
        y = y_floor + 1 + (half - 1) // 2
        b.set(cx + dx, y, cz + dz, P_SLAB, type='bottom' if half % 2 else 'top')
        cells.append((cx + dx, y, cz + dz))
    return cells


@building('nest_house_large', 'cirri', 'home', (11, 13, 11), residents=4, door=5,
          about='An octagonal two-storey Cirri home: spiral stair, four nests, a railed back terrace with an awning, a gilded dome.')
def nest_house_large(b):
    g = b.ground
    base = octagon(0, 0, 10, 10, 3)
    drum = octagon(1, 0, 9, 8, 2)             # the upper storey, flush with the front
    rb, rd = rim(base), rim(drum)
    corners = {(3, 0), (7, 0), (0, 3), (0, 7), (10, 3), (10, 7), (3, 10), (7, 10)}
    terrace = base - drum

    clear_mask(b, base, g + 1, g + 12)

    # -- floor
    put(b, rb, g, BRICKS)
    put(b, inside(base), g, POLISHED)
    for (x, z) in ((4, 0), (5, 0), (6, 0), (5, 1)):
        b.set(x, g, z, POLISHED)
    b.set(5, g, 5, GILDED)

    # -- the hall walls (g+1..g+4)
    for y in range(g + 1, g + 5):
        put(b, rb, y, 'calcite')
    for (x, z) in corners:
        column(b, x, g + 1, g + 4, z)
    # recessed porch: an open bay in the north flat, the door one block in, a rose valance above
    for x in (4, 5, 6):
        for y in range(g + 1, g + 4):
            b.set(x, y, 0, 'air')
        b.set(x, g + 4, 0, CLOTH['rose'])
    for x in (4, 6):
        for y in range(g + 1, g + 4):
            b.set(x, y, 1, 'calcite')
    b.set(5, g + 3, 1, GILDED)
    b.door(5, g + 1, 1, 'north', 'birch')
    b.set(4, g + 1, 0, 'potted_azure_bluet')
    b.set(6, g + 1, 0, 'potted_azure_bluet')
    chime(b, 5, g + 3, 0)
    for (x, z) in ((1, 2), (2, 1), (8, 1), (9, 2), (1, 8), (2, 9), (8, 9), (9, 8)):
        b.set(x, g + 2, z, GLASS)
        b.set(x, g + 3, z, GLASS)
    round_window(b, 0, g + 3, 5, 'z')
    round_window(b, 10, g + 3, 5, 'z')
    round_window(b, 5, g + 3, 10, 'x')

    # -- the hall: spiral stair round a column, cushions, shelves, harp, loom
    column(b, 5, g + 1, g + 8, 5)
    spiral(b, g, 5, 5, 10)
    for z in (4, 5, 6):
        b.set(1, g + 1, z, 'chiseled_bookshelf', facing='east')
    b.set(1, g + 2, 4, 'potted_lily_of_the_valley')
    b.set(1, g + 2, 6, 'potted_allium')
    b.set(2, g + 1, 5, CARPET['sky'])
    b.set(9, g + 1, 5, 'skyfriends:wind_harp', facing='west')
    b.set(9, g + 1, 4, CLOTH['rose'])
    b.set(9, g + 1, 6, CLOTH['sky'])
    b.set(8, g + 1, 5, CARPET['rose'])
    b.set(5, g + 1, 9, 'loom', facing='north')
    b.set(4, g + 1, 9, 'barrel', facing='up', open='false')
    b.set(6, g + 1, 9, 'potted_flowering_azalea_bush')
    b.set(3, g + 1, 2, 'potted_white_tulip')
    b.set(7, g + 1, 2, 'potted_pink_tulip')
    for (x, z) in ((2, 3), (8, 3), (2, 7), (8, 7)):
        lantern(b, x, g + 4, z, hanging=True)

    # -- g+5: the upper floor inside the drum, the terrace outside it, a polished cornice
    put(b, drum, g + 5, PLANKS)
    put(b, terrace, g + 5, POLISHED)
    put(b, rb, g + 5, POLISHED)
    for (x, z) in corners:
        b.set(x, g + 5, z, GILDED)
    for (x, z) in ((6, 4), (6, 5), (6, 6), (5, 6)):           # the stairwell
        b.set(x, g + 5, z, 'air')
    for (x, z) in ((4, 6), (4, 5)):                           # the top two steps
        b.set(x, g + 5, z, P_SLAB, type='bottom' if z == 6 else 'top')
    b.set(5, g + 5, 5, PILLAR, axis='y')

    # -- terrace railing with lanterns on the posts
    for (x, z) in rb & terrace:
        b.set(x, g + 6, z, FENCE)
    for (x, z) in ((0, 7), (10, 7), (3, 10), (7, 10)):
        lantern(b, x, g + 7, z)

    # -- the nest drum (g+6..g+8)
    for y in range(g + 6, g + 9):
        put(b, rd, y, 'calcite')
    for (x, z) in ((3, 0), (7, 0), (1, 2), (9, 2), (1, 6), (9, 6), (3, 8), (7, 8)):
        column(b, x, g + 6, g + 8, z)
    round_window(b, 5, g + 7, 0, 'x')
    round_window(b, 1, g + 7, 4, 'z')
    round_window(b, 9, g + 7, 4, 'z')
    for (x, z) in ((2, 1), (8, 1), (2, 7), (8, 7)):
        b.set(x, g + 7, z, GLASS)
    # the arch onto the terrace: three wide, a gilded keystone
    for x in (4, 5, 6):
        b.set(x, g + 6, 8, 'air')
        b.set(x, g + 7, 8, 'air')
    b.set(4, g + 8, 8, P_STAIRS, facing='west', half='top')
    b.set(6, g + 8, 8, P_STAIRS, facing='east', half='top')
    b.set(5, g + 8, 8, GILDED)

    # -- four nests, shelves, flowers, the column's capital and lantern
    nest(b, 3, g + 6, 2, cloth='rose')
    nest(b, 7, g + 6, 2, cloth='sky')
    nest(b, 2, g + 6, 5, cloth='sky')
    nest(b, 8, g + 6, 5, cloth='rose')
    b.set(3, g + 6, 7, 'chiseled_bookshelf', facing='north')
    b.set(3, g + 7, 7, 'potted_azure_bluet')
    b.set(7, g + 6, 7, 'potted_flowering_azalea_bush')
    b.set(5, g + 6, 1, CLOTH['white'])
    b.set(5, g + 8, 5, GILDED)
    lantern(b, 5, g + 9, 5)

    # -- veilcloth awning over the terrace arch, on skywood posts, chimes beneath
    for x in (3, 4, 5, 6, 7):
        b.set(x, g + 9, 9, CLOTH['rose'] if x % 2 else CLOTH['white'])
    for x in (3, 7):
        for y in (g + 6, g + 7, g + 8):
            b.set(x, y, 9, FENCE)
    chime(b, 4, g + 8, 9)
    chime(b, 6, g + 8, 9)

    # -- stepped dome on the drum: each tier steps in one block
    tiers = [drum]
    while len(tiers[-1]) > 9:
        tiers.append(inside(tiers[-1]))
    y = g + 9
    for outer, inner in zip(tiers, tiers[1:]):
        roof_ring(b, rim(outer), y, 5, 4)
        put(b, rim(inner), y, GILDED if y == g + 9 else POLISHED)
        y += 1
    put(b, tiers[-1], y - 1, GILDED)
    lantern(b, 5, y, 4)
    for (x, z) in ((5, 1), (2, 4), (8, 4)):
        lantern(b, x, g + 8, z, hanging=True)
