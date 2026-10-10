"""The Veil Court: the round open heart of a Cirri village."""
import math

from kit import building
from civic.cirri_parts import (BRICK_WALL, BRICKS, GILDED, PILLAR, POL_STAIRS, POLISHED, ROSE, SKY, WHITE, FENCE,
                               WOOD_STAIRS, check, chime, column, harp, lamp, stair, toward)

C = 7          # the centre column (7, 7)
R = 7.25       # the court's radius
BLUE = 'light_blue_glazed_terracotta'


def _lane(dx, dz):
    """The 3-wide lanes that run in from the middle of each side."""
    return abs(dx) <= 1 or abs(dz) <= 1


@building('veil_court', 'cirri', 'plaza', (15, 10, 15), door=7, residents=0,
          about='The round open court at the heart of the village: a gilded and sky-blue floor, a dais with two '
                'wind harps round a tall veil pillar hung with chimes, lantern posts, benches and low balustrades '
                'open toward all four sides.')
def veil_court(b):
    # ---- the floor: polished disc, gilded inlay ring, a sky-blue compass ring, grass in the corners
    for x in range(b.w):
        for z in range(b.d):
            dx, dz = x - C, z - C
            d = math.hypot(dx, dz)
            if d > R + 0.05:
                b.set(x, 0, z, 'grass_block', snowy=False)
            elif d > 6.3:
                b.set(x, 0, z, BRICKS)
            elif 4.45 < d <= 5.35:
                b.set(x, 0, z, GILDED)
            elif 3.3 < d <= 4.45 and not (dx == 0 or dz == 0 or abs(dx) == abs(dz)):
                b.set(x, 0, z, BLUE, facing=toward(dz, -dx))      # swirls turning round the court
            else:
                b.set(x, 0, z, POLISHED)

    # ---- the balustrade: four low arcs with lanes open in the middle of each side
    for x in range(b.w):
        for z in range(b.d):
            dx, dz = x - C, z - C
            d = math.hypot(dx, dz)
            if 6.0 < d <= 7.25 and not _lane(dx, dz):
                b.set(x, 1, z, BRICK_WALL)
    # arc ends: little pedestals with flowers
    pots = ['potted_azure_bluet', 'potted_lily_of_the_valley', 'potted_allium', 'potted_white_tulip']
    ends = [(5, 1), (9, 1), (13, 5), (13, 9), (9, 13), (5, 13), (1, 9), (1, 5)]
    for i, (x, z) in enumerate(ends):
        assert b.get(x, 1, z)[0].endswith('wall'), (x, z)
        b.set(x, 1, z, POLISHED)
        b.set(x, 2, z, pots[i % len(pots)])

    # ---- four sky-lantern posts on the diagonals, standing in the balustrade
    for x, z in ((2, 2), (12, 2), (2, 12), (12, 12)):
        column(b, x, 1, 3, z, PILLAR)
        b.set(x, 4, z, GILDED)
        lamp(b, x, 5, z)

    # ---- benches inside the north and south arcs (backs to the balustrade), facing the dais
    for x0, z, back in ((4, 2, 'north'), (9, 2, 'north'), (4, 12, 'south'), (9, 12, 'south')):
        for x in (x0, x0 + 1):
            stair(b, x, 1, z, WOOD_STAIRS, back)
    b.spot('sit', 5, 1, 3)
    b.spot('sit', 9, 1, 3)
    b.spot('sit', 5, 1, 11)
    b.spot('sit', 9, 1, 11)
    # planters in the east and west arcs
    for x, z in ((12, 4), (12, 10), (2, 4), (2, 10)):
        b.set(x, 1, z, 'potted_flowering_azalea_bush')
        b.set(x, 0, z, POLISHED)

    # ---- the dais: a round step with stairs all round
    for x in range(C - 3, C + 4):
        for z in range(C - 3, C + 4):
            dx, dz = x - C, z - C
            if dx * dx + dz * dz > 9.25:
                continue
            rim = any((dx + ex) ** 2 + (dz + ez) ** 2 > 9.25 for ex, ez in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if rim:
                stair(b, x, 1, z, POL_STAIRS, toward(-dx, -dz))
            else:
                b.set(x, 1, z, POLISHED)
    # the veil pillar: stone wrapped in bands of veilcloth, a gilded top, a crossbar hung with chimes
    b.set(C, 2, C, PILLAR)
    b.set(C, 3, C, WHITE)
    b.set(C, 4, C, SKY)
    b.set(C, 5, C, WHITE)
    b.set(C, 6, C, ROSE)
    b.set(C, 7, C, GILDED)
    for k in range(-2, 3):
        b.set(C + k, 8, C, FENCE)
        b.set(C, 8, C + k, FENCE)
    for x, z in ((C - 2, C), (C + 2, C), (C, C - 2), (C, C + 2)):
        chime(b, x, 7, z)
    lamp(b, C, 9, C)
    # two wind harps either side of the pillar, candles on the dais
    harp(b, C - 2, 2, C, 'west')
    harp(b, C + 2, 2, C, 'east')
    for x, z in ((C - 1, C - 1), (C + 1, C - 1), (C - 1, C + 1), (C + 1, C + 1)):
        b.candles(x, 2, z, 3, 'white')
    b.spot('stand', C, 2, C - 2)
    b.spot('stand', C, 2, C + 2)
    for x, z in ((4, 4), (10, 4), (4, 10), (10, 10)):
        b.spot('stand', x, 1, z)

    # ---- the grassy corners outside the balustrade
    flowers = {(0, 0): 'azure_bluet', (1, 0): 'short_grass', (0, 1): 'oxeye_daisy', (14, 0): 'lily_of_the_valley',
               (13, 0): 'short_grass', (14, 1): 'azure_bluet', (0, 14): 'oxeye_daisy', (0, 13): 'short_grass',
               (1, 14): 'lily_of_the_valley', (14, 14): 'azure_bluet', (13, 14): 'oxeye_daisy', (14, 13): 'short_grass'}
    for (x, z), f in flowers.items():
        b.set(x, 1, z, f)
    check(b)
