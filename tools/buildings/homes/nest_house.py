"""The nest house: the Cirri family home of two.

A slim calcite drum on the ground floor carries a wider upper nest that overhangs it on corbels; the nest
room upstairs has two cushioned nests, round sky-blue windows and a round flight opening on the back, and a
stepped polished dome with a gilded crown and a sky lantern on top."""
from kit import building
from homes.style import (BRICKS, POLISHED, GILDED, PILLAR, P_STAIRS, PLANKS, W_SLAB, GLASS, CARPET, CLOTH,
                         circle, rim, inside, put, column, roof_ring, corbels, lantern, chime, nest, clear_mask,
                         round_window)


@building('nest_house', 'cirri', 'home', (9, 12, 9), residents=2, door=4,
          about='A round two-storey Cirri home: a calcite drum, an overhanging nest room with two nests, a gilded dome.')
def nest_house(b):
    g = b.ground
    cx = cz = 4
    c9, c7, c5 = circle(cx, cz, 4.3), circle(cx, cz, 3.4), circle(cx, cz, 2.4)
    e9, e7, e5 = rim(c9), rim(c7), rim(c5)
    porch = c9 - c7                      # the ring under the overhang

    # -- carve the volume clear of island plants
    clear_mask(b, c9, g + 1, g + 10)

    # -- ground layer: paving ring, drum floor, gilded centre
    put(b, porch, g, BRICKS)
    put(b, e7, g, BRICKS)
    put(b, inside(c7), g, POLISHED)
    b.set(cx, g, cz, GILDED)
    b.set(4, g, 0, POLISHED)                     # threshold

    # -- ground-floor drum (y g+1..g+3)
    for y in range(g + 1, g + 4):
        put(b, e7, y, 'calcite')
    for (x, z) in ((2, 2), (6, 2), (2, 6), (6, 6)):
        column(b, x, g + 1, g + 3, z, PILLAR)
    b.door(4, g + 1, 1, 'north', 'birch')
    b.set(4, g + 3, 1, GILDED)                   # keystone
    b.set(3, g + 2, 1, GLASS)
    b.set(5, g + 2, 1, GLASS)
    round_window(b, 7, g + 2, 4, 'z')
    b.set(1, g + 2, 4, GLASS)
    b.set(3, g + 2, 7, GLASS)
    b.set(5, g + 2, 7, GLASS)

    # -- corbels under the overhang, with chimes and lanterns at the porch
    corbels(b, porch, g + 3, cx, cz)
    for x in (3, 5):
        b.set(x, g + 3, 0, 'air')
    # -- upper floor (g+4): gilded at the four points, the overhang edge polished
    put(b, e9, g + 4, POLISHED)
    put(b, inside(c9), g + 4, PLANKS)
    put(b, inside(c7), g + 4, BRICKS)
    for (x, z) in ((4, 0), (0, 4), (8, 4), (4, 8)):
        b.set(x, g + 4, z, GILDED)
    for x in (3, 5):
        chime(b, x, g + 3, 0)
        lantern(b, x, g + 1, 0)

    # -- inside, ground floor: bookshelves, harp, tea table with cushions, lantern
    b.set(2, g + 1, 3, 'chiseled_bookshelf', facing='east')
    b.set(2, g + 1, 5, 'chiseled_bookshelf', facing='east')
    b.set(2, g + 1, 4, CLOTH['sky'])
    b.set(2, g + 2, 3, 'potted_azure_bluet')
    b.set(2, g + 2, 5, 'potted_lily_of_the_valley')
    b.set(6, g + 1, 4, 'skyfriends:wind_harp', facing='west')
    b.set(6, g + 1, 3, CARPET['rose'])
    b.set(6, g + 1, 5, 'potted_flowering_azalea_bush')
    b.set(4, g + 1, 4, W_SLAB, type='top')
    b.candles(4, g + 2, 4, 3, 'white')
    b.set(3, g + 1, 4, CARPET['white'])
    b.set(5, g + 1, 4, CARPET['white'])
    b.set(4, g + 1, 3, CARPET['sky'])
    b.set(3, g + 1, 2, 'potted_white_tulip')
    b.set(5, g + 1, 2, 'potted_pink_tulip')
    for y in range(g + 1, g + 5):                # ladder up the back wall, through the floor
        b.set(4, y, 6, 'ladder', facing='north', waterlogged='false')
    b.set(4, g + 3, 4, 'air')
    lantern(b, 3, g + 3, 5, hanging=True)

    # -- upper nest drum (g+5..g+7)
    for y in range(g + 5, g + 8):
        put(b, e9, y, 'calcite')
    for (x, z) in ((1, 1), (7, 1), (1, 7), (7, 7)):
        column(b, x, g + 5, g + 7, z, PILLAR)
    round_window(b, 4, g + 6, 0, 'x')
    round_window(b, 0, g + 6, 4, 'z')
    round_window(b, 8, g + 6, 4, 'z')
    # round flight opening on the back, gilded sill
    for x in (3, 4, 5):
        for y in (g + 5, g + 6):
            b.set(x, y, 8, 'air')
    b.set(4, g + 7, 8, 'air')
    b.set(3, g + 7, 8, P_STAIRS, facing='west', half='top')
    b.set(5, g + 7, 8, P_STAIRS, facing='east', half='top')

    # -- nests, shelf, flowers, chime, chandelier
    nest(b, 2, g + 5, 4, cloth='rose')
    nest(b, 6, g + 5, 4, cloth='sky')
    b.set(1, g + 5, 3, 'chiseled_bookshelf', facing='east')
    b.set(1, g + 6, 3, 'potted_azure_bluet')
    b.set(7, g + 5, 5, 'potted_flowering_azalea_bush')
    b.set(3, g + 5, 1, 'potted_white_tulip')
    b.set(5, g + 5, 1, 'potted_allium')

    # -- dome: eave stairs, a drum ring, upper stairs, gilded crown and lantern
    roof_ring(b, e9, g + 8, cx, cz)
    put(b, e7, g + 8, GILDED)
    for (x, z) in ((4, 1), (1, 4), (7, 4), (4, 7)):
        b.set(x, g + 8, z, GILDED)
    roof_ring(b, e7, g + 9, cx, cz)
    put(b, e5, g + 9, POLISHED)
    roof_ring(b, e5, g + 10, cx, cz)
    put(b, inside(c5), g + 10, GILDED)
    lantern(b, cx, g + 11, cz)
    lantern(b, cx, g + 9, cz, hanging=True)
    # veilcloth eyebrows over the windows and the flight opening
    for cells, cloth in ((((3, 0), (4, 0), (5, 0)), 'white'), (((0, 3), (0, 4), (0, 5)), 'sky'),
                         (((8, 3), (8, 4), (8, 5)), 'sky'), (((3, 8), (4, 8), (5, 8)), 'rose')):
        for (x, z) in cells:
            b.set(x, g + 8, z, CLOTH[cloth])
    chime(b, 4, g + 7, 1)
