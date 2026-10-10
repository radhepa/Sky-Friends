"""The rim house: a home on the very edge of an island, half of it hanging over the sky.

Its lowest three layers are a cellar-nest carved into the island: two nests sunk into the floor, a round
sky-blue window looking out of the island's side. Above, at the island surface, a round living room opens
south through a tall arch onto a cantilevered skywood terrace held out over the void on corbels, where the
Cirri come and go. A dome with a little open cupola of chimes crowns it."""
from kit import building
from homes.style import (STONE, BRICKS, POLISHED, GILDED, PILLAR, P_STAIRS, P_SLAB, PLANKS, FENCE, GLASS,
                         CARPET, CLOTH, circle, rim, inside, put, column, roof_ring, corbels, lantern, chime,
                         clear_mask, round_window)


@building('rim_house', 'cirri', 'home', (9, 13, 10), ground=3, residents=2, door=4, rim=True,
          about='A Cirri home on an island rim: a cellar-nest in the rock below, a terrace cantilevered over the sky.')
def rim_house(b):
    g = b.ground                                   # 3: the island surface
    cx, cz = 4, 3
    c7, c5 = circle(cx, cz, 3.4), circle(cx, cz, 2.4)
    e7, e5 = rim(c7), rim(c5)
    deck = circle(4, 5, 4.3) - c7                  # the terrace, wrapping the south of the drum
    deck = {(x, z) for (x, z) in deck if z >= 4}
    rail = rim(c7 | deck) & deck

    # -- the cellar-nest (layers 0..2, inside the island)
    put(b, c7, 0, BRICKS)
    put(b, c5, 0, STONE)
    for y in (1, 2):
        put(b, e7, y, STONE)                       # rough island stone, the walls of a carved room
    for (x, z) in ((3, 6), (5, 6)):
        for y in (0, 2):
            b.set(x, y, z, BRICKS)                 # a brick surround for the window
    clear_mask(b, c5, 1, 2)
    round_window(b, 4, 1, 6, 'x')                  # looks out of the island's side, under the terrace
    for (x, z), cloth in (((3, 3), 'rose'), ((5, 3), 'sky')):
        b.set(x, 0, z, CLOTH[cloth])                # cushion sunk in the floor
        b.spot('sleep', x, 1, z)                    # the Cirri floats right over it
    for (x, z) in ((2, 3), (3, 2), (3, 4), (4, 3), (5, 2), (5, 4)):
        b.set(x, 1, z, CARPET['white'])
    b.set(2, 1, 2, 'chiseled_bookshelf', facing='east')
    b.set(2, 1, 4, 'potted_lily_of_the_valley')
    b.set(4, 1, 1, 'decorated_pot', facing='south', cracked='false', waterlogged='false')
    b.candles(3, 1, 5, 2, 'white')
    b.candles(5, 1, 5, 2, 'light_blue')
    lantern(b, 4, 2, 2, hanging=True)
    for y in range(1, g + 1):                       # ladder down from the living room
        b.set(6, y, 3, 'ladder', facing='west', waterlogged='false')

    # -- under the terrace: corbels and a hanging lantern on a chain over the void
    corbels(b, deck, g - 1, 4, 3)
    for (x, z) in ((4, 7), (4, 8)):
        b.set(x, g - 1, z, 'air')
    b.set(4, g - 1, 8, 'iron_chain', axis='y')
    lantern(b, 4, g - 2, 8, hanging=True)

    # -- ground layer: drum floor and terrace deck
    clear_mask(b, c7 | deck, g + 1, g + 9)
    put(b, e7, g, POLISHED)
    put(b, c5, g, BRICKS)
    b.set(cx, g, cz, GILDED)
    put(b, deck, g, PLANKS)
    put(b, rail, g, POLISHED)
    b.set(6, g, 3, 'ladder', facing='west', waterlogged='false')

    # -- the living room drum (g+1..g+4)
    for y in range(g + 1, g + 5):
        put(b, e7, y, 'calcite')
    for (x, z) in ((2, 1), (6, 1), (2, 5), (6, 5)):
        column(b, x, g + 1, g + 4, z)
    b.door(4, g + 1, 0, 'north', 'cherry')
    b.set(4, g + 3, 0, GILDED)
    b.set(3, g + 2, 0, GLASS)
    b.set(5, g + 2, 0, GLASS)
    round_window(b, 1, g + 2, 3, 'z')
    round_window(b, 7, g + 2, 3, 'z')
    # the tall arch onto the terrace
    for x in (3, 4, 5):
        for y in (g + 1, g + 2):
            b.set(x, y, 6, 'air')
    b.set(4, g + 3, 6, 'air')
    b.set(3, g + 3, 6, P_STAIRS, facing='west', half='top')
    b.set(5, g + 3, 6, P_STAIRS, facing='east', half='top')
    b.set(4, g + 4, 6, GILDED)
    b.set(4, g, 6, GILDED)
    # inside: cushions, harp, shelf, flowers, lantern
    b.set(2, g + 1, 3, 'skyfriends:wind_harp', facing='east')
    b.set(2, g + 1, 2, CLOTH['white'])
    b.set(2, g + 1, 4, 'potted_azure_bluet')
    b.set(3, g + 1, 3, CARPET['sky'])
    b.set(4, g + 1, 3, CARPET['rose'])
    b.set(3, g + 1, 1, 'potted_white_tulip')
    b.set(5, g + 1, 1, 'chiseled_bookshelf', facing='south')
    b.set(5, g + 2, 1, 'potted_allium')
    lantern(b, 4, g + 5, 3, hanging=True)

    # -- the terrace: railing, lanterns on posts, cushions, chimes under the eave
    for (x, z) in rail:
        b.set(x, g + 1, z, FENCE)
    for (x, z) in ((0, 5), (8, 5), (4, 9)):
        lantern(b, x, g + 2, z)
    b.set(2, g + 1, 7, CLOTH['rose'])
    b.set(6, g + 1, 7, CLOTH['sky'])
    b.spot('sit', 2, g + 2, 7)
    b.spot('sit', 6, g + 2, 7)
    b.set(3, g + 1, 8, 'potted_flowering_azalea_bush')
    b.set(5, g + 1, 8, 'potted_flowering_azalea_bush')

    # -- dome and cupola
    roof_ring(b, e7, g + 5, cx, cz)
    put(b, e5, g + 5, GILDED)
    roof_ring(b, e5, g + 6, cx, cz)
    put(b, inside(c5), g + 6, GILDED)
    for (x, z) in ((3, 2), (5, 2), (3, 4), (5, 4)):
        b.set(x, g + 7, z, FENCE)
        b.set(x, g + 8, z, FENCE)
    put(b, inside(c5), g + 9, P_SLAB)
    b.set(4, g + 9, 3, POLISHED)
    chime(b, 4, g + 8, 3)
    lantern(b, 4, g + 7, 3)
