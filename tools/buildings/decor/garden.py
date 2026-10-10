"""Cirri path and garden decor: chime arches, koi ponds, harp stands, flower beds, small skywood trees and
cloud seats. The planner scatters these along paths and on free island ground (front = north, z = 0)."""
from kit import building
from homes.style import (STONE, BRICKS, POLISHED, GILDED, PILLAR, P_SLAB, B_SLAB, FENCE, LOG, LEAVES, CLOUD,
                         CLOTH, CARPET, circle, rim, inside, put, column, lantern, chime)


@building('chime_arch', 'cirri', 'decor', (5, 6, 2),
          about='A white arch over a path, gilded capitals, a sky veilcloth band, wind chimes and a lantern hanging in it.')
def chime_arch(b):
    for z in (0, 1):
        for x in (0, 4):
            b.set(x, 0, z, POLISHED)                    # footings set into the path
            column(b, x, 1, 4, z)
            b.set(x, 5, z, GILDED)                      # capitals
        for x in (1, 2, 3):
            b.set(x, 5, z, P_SLAB if z == 0 else CLOTH['sky'])
        for x in (1, 3):                                 # hangers that round the opening's corners
            b.set(x, 4, z, FENCE)
            chime(b, x, 3, z)
    lantern(b, 2, 4, 0, hanging=True)
    chime(b, 2, 4, 1)
    b.clear(1, 1, 0, 3, 2, 1)                            # keep the path through it clear of plants


@building('koi_pond', 'cirri', 'decor', (5, 3, 5), ground=1,
          about='A little round koi pond: still water over a gilded floor, lily pads, a polished rim and a lantern.')
def koi_pond(b):
    g = b.ground
    pond = circle(2, 2, 2.4)
    water = inside(pond)
    put(b, pond, 0, STONE)                               # basin
    b.set(2, 0, 2, GILDED)                               # a glint of gold under the water
    put(b, rim(pond), g, POLISHED)
    put(b, water, g, 'water', level=0)
    put(b, rim(pond), g + 1, B_SLAB, type='bottom')
    b.set(1, g + 1, 1, 'lily_pad')
    b.set(3, g + 1, 3, 'lily_pad')
    b.set(2, g + 1, 2, 'air')
    b.set(1, g + 1, 3, 'air')
    b.set(3, g + 1, 1, 'air')
    b.spot('koi', 2, g + 1, 2)
    b.set(4, g, 4, POLISHED)                             # lantern on the corner
    lantern(b, 4, g + 1, 4)
    b.set(0, g, 0, 'grass_block', snowy='false')
    b.set(0, g + 1, 0, 'blue_orchid')


@building('harp_stand', 'cirri', 'decor', (3, 3, 3),
          about='A wind harp on a little polished dais, a sky lantern on a skywood post beside it.')
def harp_stand(b):
    for x in range(3):
        for z in range(3):
            b.set(x, 0, z, POLISHED)
    b.set(1, 0, 1, GILDED)
    b.set(1, 1, 1, 'skyfriends:wind_harp', facing='north')
    for (x, z) in ((0, 1), (2, 1), (1, 2)):
        b.set(x, 1, z, P_SLAB, type='bottom')
    b.set(0, 1, 2, 'potted_azure_bluet')
    b.set(2, 1, 2, FENCE)
    lantern(b, 2, 2, 2)
    b.set(0, 1, 0, 'air')
    b.set(1, 1, 0, 'air')
    b.set(2, 1, 0, 'air')
    b.spot('stand', 1, 1, 0)


@building('flower_bed', 'cirri', 'decor', (5, 2, 3),
          about='A rounded flower bed of sky-coloured flowers inside a skystone kerb, with a lantern at one end.')
def flower_bed(b):
    bed = {(x, z) for x in range(5) for z in range(3)} - {(0, 0), (0, 2), (4, 0), (4, 2)}
    soil = {(1, 1), (2, 1), (3, 1)}
    for (x, z) in bed - soil:
        b.set(x, 0, z, BRICKS)
        b.set(x, 1, z, B_SLAB, type='bottom')
    for (x, z) in soil:
        b.set(x, 0, z, 'grass_block', snowy='false')
    b.set(1, 1, 1, 'azure_bluet')
    b.set(2, 1, 1, 'cornflower')
    b.set(3, 1, 1, 'lily_of_the_valley')
    lantern(b, 0, 1, 1)
    b.set(4, 1, 1, 'potted_allium')


@building('skywood_tree_small', 'cirri', 'decor', (5, 8, 5),
          about='A small skywood tree: a pale trunk, a rounded canopy of blossoming leaves, a chime on a low bough.')
def skywood_tree_small(b):
    for y in range(1, 6):
        b.set(2, y, 2, LOG, axis='y')
    b.set(2, 0, 2, 'rooted_dirt')
    for y, r in ((4, 2.4), (5, 2.4), (6, 1.5), (7, 0.9)):
        for (x, z) in circle(2, 2, r):
            if b.inside(x, y, z) and not b.solid(x, y, z):
                b.set(x, y, z, LEAVES)
    b.set(3, 4, 2, LOG, axis='x')                        # low boughs: a chime under one, a lantern under the other
    b.set(4, 4, 2, LOG, axis='x')
    chime(b, 4, 3, 2)
    b.set(1, 4, 2, LOG, axis='x')
    b.set(0, 4, 2, LOG, axis='x')
    lantern(b, 0, 3, 2, hanging=True)
    for (x, z) in ((0, 1), (4, 3), (1, 4), (3, 0)):     # a ragged lower edge to the canopy
        b.erase(x, 4, z, x, 4, z)
    b.set(1, 1, 3, 'pink_petals', facing='north', flower_amount='3')
    b.set(3, 1, 1, 'pink_petals', facing='east', flower_amount='2')


@building('cloud_seat', 'cirri', 'decor', (3, 3, 2),
          about='A fluffy armchair of cloud with a sky veilcloth cushion and a lantern on one arm.')
def cloud_seat(b):
    for x in range(3):
        b.set(x, 1, 1, CLOUD)
    b.set(0, 2, 1, CLOUD)
    b.set(2, 2, 1, CLOUD)
    b.set(1, 2, 1, CLOTH['white'])
    b.set(0, 1, 0, CLOUD)
    b.set(2, 1, 0, CLOUD)
    b.set(1, 1, 0, CARPET['sky'])
    lantern(b, 2, 2, 0)
    b.set(0, 2, 0, 'potted_azure_bluet')
    for x in range(3):
        for z in range(2):
            b.set(x, 0, z, POLISHED)
    b.spot('sit', 1, 2, 0)
