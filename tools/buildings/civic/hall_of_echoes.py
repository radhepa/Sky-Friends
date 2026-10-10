"""The Hall of Echoes: the Cirri music hall, a skystone colonnade under a barrel vault, open to the wind."""
from kit import building
from civic.cirri_parts import (BRICK_SLAB, BRICK_STAIRS, BRICK_WALL, BRICKS, GILDED, PILLAR, POL_SLAB, POL_STAIRS,
                               POLISHED, ROSE, ROSE_CARPET, SKY, SKY_CARPET, WHITE, WOOD_STAIRS, check, chime, harp,
                               lamp, slab, stair)

W, D = 15, 11
COLS = (0, 2, 5, 9, 12, 14)          # pillars along the front and back, widening toward the middle bay
END_COLS = (0, 3, 7, 10)             # pillars along the two ends
# the vault's profile across the hall: z -> [(y, piece)], piece 'block', 'stair', 'slab' or 'ridge'
BEAM = 7                              # pillars stand y 1..6, the beam runs round at y 7
VAULT = {0: [(8, 'stair')], 1: [(9, 'stair')], 2: [(10, 'stair')], 3: [(11, 'slab')], 4: [(11, 'slab')],
         5: [(11, 'ridge')]}


@building('hall_of_echoes', 'cirri', 'civic', (W, 13, D), door=7, residents=0, job='harpist',
          about='The music hall: a colonnade of skystone pillars under a polished barrel vault with a gilded ridge '
                'and sky-glass fan windows at its ends; wind harps and note blocks on a stage open to the sky, '
                'benches for listeners.')
def hall_of_echoes(b):
    b.fill(0, 0, 0, W - 1, 0, D - 1, POLISHED)
    for x in range(W):
        b.set(x, 0, 0, BRICKS)
        b.set(x, 0, D - 1, BRICKS)

    # ---- colonnades: pillars on bases, a beam round the top with gilded capitals
    pillars = [(x, z) for x in COLS for z in (0, D - 1)] + [(x, z) for x in (0, W - 1) for z in END_COLS]
    for x, z in set(pillars):
        b.set(x, 1, z, POLISHED)
        for y in range(2, BEAM):
            b.set(x, y, z, PILLAR)
    for x in range(W):
        for z in (0, D - 1):
            b.set(x, BEAM, z, GILDED if (x, z) in pillars else POLISHED)
    for z in range(1, D - 1):
        for x in (0, W - 1):
            b.set(x, BEAM, z, GILDED if (x, z) in pillars else POLISHED)

    # ---- the barrel vault
    for z in range(D):
        dz = min(z, D - 1 - z)
        inward = 'south' if z < D // 2 else 'north'
        for y, piece in VAULT[dz]:
            for x in range(W):
                rib = x in COLS              # brick ribs over every pillar line, polished panels between
                if piece == 'stair':
                    stair(b, x, y, z, BRICK_STAIRS if rib else POL_STAIRS, inward)
                elif piece == 'slab':
                    slab(b, x, y, z, BRICK_SLAB if rib else POL_SLAB)
                else:
                    b.set(x, y, z, GILDED)
    for x in (1, 7, 13):
        lamp(b, x, 12, 5)                     # lanterns along the ridge
    # sky-glass fan windows filling the ends of the vault, a gilded sun in the middle
    for x in (0, W - 1):
        for z in range(1, D - 1):
            top = min(y for y, _ in VAULT[min(z, D - 1 - z)])
            for y in range(BEAM + 1, top):
                b.set(x, y, z, 'light_blue_stained_glass_pane')
        b.set(x, BEAM + 2, 5, GILDED)
    # three chandeliers hung from the ridge
    for x in (3, 7, 11):
        for y in (9, 10):
            b.set(x, y, 5, 'iron_chain', axis='y', waterlogged=False)
        lamp(b, x, 8, 5, hanging=True)
    # chimes in the middle bays, lanterns in the outer gaps and along the ends, all hung from the beam
    for x in (6, 8):
        chime(b, x, BEAM - 1, 0)
        chime(b, x, BEAM - 1, D - 1)
    lamp(b, 7, BEAM - 1, 0, hanging=True)
    # veilcloth valances hung under the beam across the side bays and either side of the end lanterns
    for x in (3, 4, 10, 11):
        b.set(x, BEAM - 1, 0, ROSE)
        b.set(x, BEAM - 1, D - 1, SKY)
    for x in (0, W - 1):
        for z in (4, 6):
            b.set(x, BEAM - 1, z, WHITE)
    for x in (4, 10):                           # small lanterns under the valances
        lamp(b, x, BEAM - 2, 0, hanging=True)
        lamp(b, x, BEAM - 2, D - 1, hanging=True)
    for x in (1, W - 2):
        lamp(b, x, BEAM - 1, 0, hanging=True)
        lamp(b, x, BEAM - 1, D - 1, hanging=True)
    for x in (0, W - 1):
        lamp(b, x, BEAM - 1, 5, hanging=True)

    # ---- the stage: a raised floor at the back, a step along its front, a low rail behind
    for x in range(1, W - 1):
        stair(b, x, 1, 6, POL_STAIRS, 'south')
        for z in range(7, D):
            if not b.solid(x, 1, z):
                b.set(x, 1, z, POLISHED)
        if (x, D - 1) not in pillars:
            b.set(x, 2, D - 1, BRICK_WALL)
    for x in (1, 2, W - 3, W - 2):
        b.set(x, 2, 9, 'note_block', instrument='harp', note=0, powered=False)
        b.candles(x, 3, 9, 2, 'white')
    for x, facing in ((3, 'north'), (5, 'north'), (9, 'north'), (11, 'north')):
        harp(b, x, 2, 8, facing)
    harp(b, 7, 2, 9, 'north')                  # the great harp at the back of the stage
    for x in (6, 8):
        b.candles(x, 2, 8, 4, 'white')         # candles either side of the great harp
    b.set(6, 2, 9, 'potted_azure_bluet')
    b.set(8, 2, 9, 'potted_azure_bluet')
    b.spot('work', 4, 2, 8)
    b.spot('work', 10, 2, 8)
    for x in range(3, 12):
        b.set(x, 2, 7, SKY_CARPET)

    # ---- the listeners: two rows of skywood benches either side of a rose aisle
    for z in (2, 4):
        for x in list(range(2, 6)) + list(range(9, 13)):
            stair(b, x, 1, z, WOOD_STAIRS, 'north')
    for z in range(1, 6):
        b.set(7, 1, z, ROSE_CARPET)
    b.spot('sit', 3, 1, 3)
    b.spot('sit', 11, 1, 3)
    b.spot('sit', 4, 1, 5)
    check(b)
