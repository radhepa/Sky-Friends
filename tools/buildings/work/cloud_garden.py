"""The Cloud Garden: a koi pool with stepping stones, flower beds, two skywood trees and a veilcloth gazebo."""
from kit import building
from civic.cirri_parts import (BRICKS, FENCE, LEAVES, LOG, PILLAR, POL_STAIRS, POLISHED, ROSE, SKY, SKYSTONE, WHITE,
                               WOOD_STAIRS, check, chime, lamp, stair)

N = 13
G = 2                      # ground: two layers below for the pool
TERRACE = 8                # the raised terrace runs z 8..11 (its front row is brick)
POOL_C, POOL_R = (6, 4), (3.2, 2.2)
STONES = ((6, 2), (6, 4), (6, 6))


def _pool():
    (cx, cz), (rx, rz) = POOL_C, POOL_R
    return {(x, z) for x in range(N) for z in range(N) if ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 <= 1.0}


def _tree(b, x, y0, z, trunk):
    """A small skywood tree: a log trunk and a round flowering canopy."""
    for y in range(y0, y0 + trunk):
        b.set(x, y, z, LOG, axis='y')
    top = y0 + trunk - 1
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz:
                b.set(x + dx, top, z + dz, LEAVES)
            b.set(x + dx, top + 1, z + dz, LEAVES)
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2), (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        if abs(dx) == 2 or abs(dz) == 2:
            b.set(x + dx, top + 1, z + dz, LEAVES)
        else:
            b.set(x + dx, top + 2, z + dz, LEAVES)


@building('cloud_garden', 'cirri', 'work', (N, 9, N), ground=G, door=6, residents=0, job='gardener',
          about='A terraced garden: a koi pool with lily pads and stepping stones in a polished rim, flower beds, '
                'two flowering skywood trees and a little gazebo under a veilcloth roof, all inside a blossom hedge.')
def cloud_garden(b):
    g = G
    pool = _pool()
    wet = pool - set(STONES)
    rim = {(x + dx, z + dz) for x, z in pool for dx in (-1, 0, 1) for dz in (-1, 0, 1)} - pool

    # ---- the lawn, and the terrace at the back
    b.fill(0, g, 0, N - 1, g, N - 1, 'grass_block', snowy=False)
    for x in range(1, N - 1):
        for z in range(TERRACE, N - 1):
            b.set(x, g, z, 'dirt')
            if z == TERRACE:
                b.set(x, g + 1, z, BRICKS)
            else:
                b.set(x, g + 1, z, 'grass_block', snowy=False)
    stair(b, 6, g + 1, TERRACE - 1, POL_STAIRS, 'south')
    stair(b, 2, g + 1, TERRACE - 1, POL_STAIRS, 'south')

    # ---- the koi pool: two deep, a skystone basin, a polished rim, stepping stones across
    for x, z in pool | rim:
        b.set(x, g - 2, z, SKYSTONE)
    for x, z in rim:
        b.set(x, g - 1, z, SKYSTONE)
        b.set(x, g, z, POLISHED)
    for x, z in wet:
        b.set(x, g - 1, z, 'water', level=0)
        b.set(x, g, z, 'water', level=0)
    for x, z in STONES:
        b.set(x, g - 1, z, SKYSTONE)
        b.set(x, g, z, POLISHED)
    for x, z in ((8, 3), (4, 5), (9, 4), (5, 2)):
        b.set(x, g + 1, z, 'lily_pad')
    b.spot('koi', 4, g + 1, 4)
    # stepping stones across the lawn
    b.set(6, g, 0, POLISHED)
    for x, z in ((2, 5), (2, 6), (1, 4)):
        b.set(x, g, z, POLISHED)

    # ---- the blossom hedge round the edge, open in the middle of the north side; lantern posts
    for x in range(N):
        for z in range(N):
            if not (x in (0, N - 1) or z in (0, N - 1)) or (z == 0 and 4 <= x <= 8):
                continue
            b.set(x, g + 1, z, LEAVES)
            if z >= TERRACE:
                b.set(x, g + 2, z, LEAVES)
    for x, z, h in ((4, 0, 2), (8, 0, 2), (0, 6, 2), (N - 1, 6, 2)):
        for y in range(g + 1, g + 1 + h):
            b.set(x, y, z, PILLAR)
        lamp(b, x, g + 1 + h, z)

    # ---- flower beds and the trees
    beds = {(9, 1): 'allium', (10, 1): 'azure_bluet', (11, 1): 'pink_tulip', 
            (10, 2): 'oxeye_daisy', (11, 2): 'lily_of_the_valley', (11, 3): 'azure_bluet', (1, 1): 'white_tulip',
            (11, 6): 'allium', (11, 7): 'pink_tulip', (1, 7): 'cornflower'}
    for (x, z), f in beds.items():
        b.set(x, g + 1, z, f)
    terrace_beds = {(1, 9): 'pink_tulip', (2, 9): 'azure_bluet', (3, 9): 'allium', (1, 10): 'lily_of_the_valley',
                    (2, 10): 'cornflower', (3, 10): 'oxeye_daisy', (1, 11): 'white_tulip', (3, 11): 'pink_tulip'}
    for (x, z), f in terrace_beds.items():
        b.set(x, g + 2, z, f)
    _tree(b, 2, g + 1, 2, 3)
    _tree(b, 10, g + 2, 10, 3)
    b.spot('work', 3, g + 1, 3)
    b.spot('work', 10, g + 1, 3)

    # ---- the gazebo on the terrace: skywood posts under a veilcloth roof
    b.fill(5, g + 1, 9, 7, g + 1, 11, POLISHED)
    for x, z in ((5, 9), (7, 9), (5, 11), (7, 11)):
        b.set(x, g + 2, z, FENCE)
        b.set(x, g + 3, z, FENCE)
    roof = g + 4
    for x in range(4, 9):
        for z in range(8, 13):
            edge = x in (4, 8) or z in (8, 12)
            b.set(x, roof, z, (ROSE if (x + z) % 2 else WHITE) if edge else WHITE)
    for x in range(5, 8):
        for z in range(9, 12):
            b.set(x, roof + 1, z, WHITE if (x, z) == (6, 10) else SKY)
    lamp(b, 6, roof + 2, 10)
    lamp(b, 6, roof - 1, 10, hanging=True)
    for x, z in ((4, 8), (8, 8), (4, 12), (8, 12)):
        chime(b, x, roof - 1, z)
    stair(b, 6, g + 2, 11, WOOD_STAIRS, 'south')
    b.set(5, g + 2, 10, 'potted_azure_bluet')
    check(b)

