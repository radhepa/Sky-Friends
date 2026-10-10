"""The Loom House: the weavers' workshop, white walls, looms and bolts of veilcloth, an open gallery above."""
from kit import building
from civic.cirri_parts import (FENCE, GILDED, LOOT, PILLAR, PLANKS, POL_SLAB, POL_STAIRS, POLISHED, ROSE, ROSE_CARPET,
                               SKY, SKY_CARPET, WHITE, WOOD_STAIRS, check, lamp, slab, stair)

W, D = 11, 10
Z0, Z1 = 3, 9        # the house runs z 3..9; the porch under the awning is z 0..2
FLOOR = 4            # the gallery floor
ROOF = 8


@building('loom_house', 'cirri', 'work', (W, 12, D), door=5, residents=0, job='weaver',
          about='The weavers\' workshop: white calcite walls, two looms among bolts of veilcloth, a big rose and white '
                'veilcloth awning over the porch, and an open gallery above where new cloth hangs to dry.')
def loom_house(b):
    b.fill(0, 0, 0, W - 1, 0, D - 1, POLISHED)
    b.fill(1, 0, Z0 + 1, W - 2, 0, Z1 - 1, PLANKS)

    # ---- ground floor walls: calcite between pillars, a wide arch in front, windows on the sides
    for x in range(W):
        for z in range(Z0, Z1 + 1):
            if x not in (0, W - 1) and z not in (Z0, Z1):
                continue
            corner = x in (0, W - 1) and z in (Z0, Z1)
            for y in range(1, FLOOR):
                b.set(x, y, z, PILLAR if corner else 'calcite')
    b.clear(3, 1, Z0, 7, 2, Z0)
    stair(b, 3, 3, Z0, POL_STAIRS, 'west', 'top')
    stair(b, 7, 3, Z0, POL_STAIRS, 'east', 'top')
    b.clear(4, 3, Z0, 6, 3, Z0)
    for x in (0, W - 1):
        for z in (5, 7):
            b.set(x, 2, z, 'light_blue_stained_glass_pane')
    for x in (3, 7):
        b.set(x, 2, Z1, 'light_blue_stained_glass_pane')

    # ---- the workshop: two looms, bolts of veilcloth along the back, carpets, a chest
    for x in (4, 6):
        b.set(x, 1, 7, 'loom', facing='north')
        b.spot('work', x, 1, 6)
    bolts = {2: (WHITE, SKY), 3: (ROSE,), 5: (SKY, WHITE), 7: (WHITE,), 8: (ROSE, SKY)}
    for x, stack in bolts.items():
        for k, cloth in enumerate(stack):
            b.set(x, 1 + k, 8, cloth)
    b.set(9, 1, 4, 'barrel', facing='up', open=False)
    b.set(9, 2, 4, 'potted_azure_bluet')
    b.chest(9, 1, 6, 'west', loot=LOOT)
    b.set(9, 1, 7, 'barrel', facing='west', open=False)
    for z in range(Z0, 6):
        b.set(5, 1, z, ROSE_CARPET)
    for x in (4, 6):
        b.set(x, 1, 5, SKY_CARPET)
    for x, z in ((3, 5), (7, 5), (7, 8)):
        lamp(b, x, FLOOR - 1, z, hanging=True)

    # ---- stairs up the west side to the gallery
    for k in range(4):
        stair(b, 1, 1 + k, 5 + k, WOOD_STAIRS, 'south')

    # ---- the gallery: an open floor with pillars, a rail, cloth drying under the roof
    b.fill(0, FLOOR, Z0, W - 1, FLOOR, Z1, POLISHED)
    stair(b, 1, FLOOR, 8, WOOD_STAIRS, 'south')
    b.clear(1, FLOOR, 5, 1, FLOOR, 7)
    pillars = [(0, Z0), (5, Z0), (W - 1, Z0), (0, Z1), (5, Z1), (W - 1, Z1), (0, 6), (W - 1, 6)]
    for x, z in pillars:
        for y in range(FLOOR + 1, ROOF):
            b.set(x, y, z, PILLAR)
    for x in range(W):
        for z in range(Z0, Z1 + 1):
            if (x in (0, W - 1) or z in (Z0, Z1)) and (x, z) not in pillars:
                b.set(x, FLOOR + 1, z, FENCE)
    for z in (5, 6, 7):
        b.set(2, FLOOR + 1, z, FENCE)           # a rail round the stairwell
    b.set(1, FLOOR + 1, 4, FENCE)
    # cloth drying in long drapes under the roof
    drapes = {3: (ROSE, 2), 4: (WHITE, 1), 5: (SKY, 2), 6: (WHITE, 1), 7: (ROSE, 2), 8: (SKY, 1)}
    for x, (cloth, length) in drapes.items():
        for k in range(length):
            b.set(x, ROOF - 1 - k, 6, cloth)
    b.set(8, FLOOR + 1, 8, 'loom', facing='west')
    for x in (3, 4):
        stair(b, x, FLOOR + 1, 8, WOOD_STAIRS, 'south')
    b.set(7, FLOOR + 1, 4, 'potted_allium')
    for x, z in ((2, 4), (8, 4), (3, 8), (8, 7)):
        lamp(b, x, ROOF - 1, z, hanging=True)

    # ---- the roof: polished skystone, a pitched ridge along the house, gilded ends with lanterns
    for x in range(W):
        stair(b, x, ROOF, Z0, POL_STAIRS, 'south')
        stair(b, x, ROOF, Z1, POL_STAIRS, 'north')
        for z in range(Z0 + 1, Z1):
            b.set(x, ROOF, z, POLISHED)
        stair(b, x, ROOF + 1, Z0 + 1, POL_STAIRS, 'south')
        stair(b, x, ROOF + 1, Z1 - 1, POL_STAIRS, 'north')
        for z in range(Z0 + 2, Z1 - 1):
            b.set(x, ROOF + 1, z, POLISHED)
        stair(b, x, ROOF + 2, Z0 + 2, POL_STAIRS, 'south')
        stair(b, x, ROOF + 2, Z1 - 2, POL_STAIRS, 'north')
        slab(b, x, ROOF + 2, 6, POL_SLAB)
    for x in (0, W - 1):
        b.set(x, ROOF + 2, 6, GILDED)
        lamp(b, x, ROOF + 3, 6)

    # ---- the awning: rose and white stripes over the porch, a scalloped valance on skywood posts
    for x in range(W):
        cloth = ROSE if x % 2 == 0 else WHITE
        b.set(x, FLOOR, 2, cloth)
        b.set(x, FLOOR, 1, cloth)
        b.set(x, FLOOR - 1, 0, cloth)
    for x in (0, W - 1):
        for y in range(1, FLOOR - 1):
            b.set(x, y, 0, FENCE)
    for x in (3, 7):
        lamp(b, x, FLOOR - 1, 1, hanging=True)
    for x in (1, 2):
        stair(b, x, 1, 2, WOOD_STAIRS, 'south')      # a bench with its back to the house
    b.set(9, 1, 2, 'potted_white_tulip')
    b.set(9, 1, 1, 'barrel', facing='up', open=False)
    b.set(9, 2, 1, 'potted_pink_tulip')
    check(b)
