"""The Bell Pagoda: three tiers of skystone under flared, gold-tipped roofs, the bell in the open top tier."""
from kit import building
from civic.cirri_parts import (BRICKS, FENCE, GILDED, PILLAR, POL_SLAB, POL_STAIRS, POLISHED, ROSE, SKY, check, chime,
                               column, lamp, slab, stair)

C = 4   # the centre column (4, 4): the pagoda's heart pillar, with the ladder on its north face


def _inward(x, z, lo, hi):
    """Facing (toward the middle) of a cell on the ring of the square lo..hi; None at the corners."""
    on_x = x in (lo, hi)
    on_z = z in (lo, hi)
    if on_x and on_z:
        return None
    if on_x:
        return 'east' if x == lo else 'west'
    return 'south' if z == lo else 'north'


def _ring(lo, hi):
    for x in range(lo, hi + 1):
        for z in range(lo, hi + 1):
            if x in (lo, hi) or z in (lo, hi):
                yield x, z


def _eave(b, y, lo, hi, stairs=POL_STAIRS, slabs=POL_SLAB):
    """A ring of eaves: gilded tips at the corners (a lantern on each, a chime under), roof stairs rising
    inward beside them and thinner slabs along the middle of each side, so the eave line flares up to the tips."""
    span = hi - lo
    for x, z in _ring(lo, hi):
        facing = _inward(x, z, lo, hi)
        if facing is None:
            b.set(x, y, z, GILDED)
            lamp(b, x, y + 1, z)
            chime(b, x, y - 1, z)
            continue
        along = x - lo if facing in ('south', 'north') else z - lo
        if min(along, span - along) >= max(2, span // 3):
            slab(b, x, y, z, slabs)
        else:
            stair(b, x, y, z, stairs, facing)


def _walls(b, y0, y1, lo, hi):
    for x, z in _ring(lo, hi):
        corner = x in (lo, hi) and z in (lo, hi)
        for y in range(y0, y1 + 1):
            b.set(x, y, z, PILLAR if corner else BRICKS)


@building('bell_pagoda', 'cirri', 'civic', (9, 20, 9), door=4, residents=0, job='bellkeeper',
          about='A three-tier pagoda of skystone with flared, gold-tipped roofs; chimes hang under every eave and '
                'the great bell hangs in the open top tier, reached by a ladder up the heart pillar.')
def bell_pagoda(b):
    b.fill(0, 0, 0, 8, 0, 8, POLISHED)
    for x, z in _ring(0, 8):
        b.set(x, 0, z, BRICKS)
    b.set(C, 0, 0, POLISHED)

    # ---- tier one: 7x7 hall (x, z 1..7), y 1..4
    _walls(b, 1, 3, 1, 7)
    for x, z in _ring(1, 7):
        b.set(x, 4, z, GILDED if (x in (1, 7) and z in (1, 7)) else POLISHED)
    # three-wide arches on all four sides (the north one is the entrance), gilded keystones over them
    for side in ('north', 'south', 'west', 'east'):
        for k in (3, 4, 5):
            x, z = {'north': (k, 1), 'south': (k, 7), 'west': (1, k), 'east': (7, k)}[side]
            b.clear(x, 1, z, x, 2, z)
            if k == 4:
                b.clear(x, 3, z, x, 3, z)
                b.set(x, 4, z, GILDED)
            else:
                along = 'west' if k == 3 else 'east'
                if side in ('west', 'east'):
                    along = 'north' if k == 3 else 'south'
                stair(b, x, 3, z, POL_STAIRS, along, 'top')
    # inside: veilcloth hangings, flowers, lanterns
    b.set(2, 1, 6, 'potted_azure_bluet')
    b.set(6, 1, 6, 'potted_allium')
    b.set(2, 1, 2, 'barrel', facing='up', open=False)
    b.set(2, 2, 2, 'potted_lily_of_the_valley')
    for x, z in ((2, 3), (3, 6), (5, 6), (6, 3)):
        b.set(x, 1, z, ROSE + '_carpet' if (x + z) % 2 else SKY + '_carpet')
    for x, z in ((2, 6), (6, 2), (6, 6)):
        lamp(b, x, 4, z, hanging=True)
    # the ceiling / first roof
    b.fill(1, 5, 1, 7, 5, 7, POLISHED)
    _eave(b, 5, 0, 8)
    for x, z in _ring(1, 7):
        facing = _inward(x, z, 1, 7)
        stair(b, x, 6, z, POL_STAIRS, facing or ('south' if z == 1 else 'north'))

    # ---- tier two: 5x5 (x, z 2..6), y 6..8
    _walls(b, 6, 8, 2, 6)
    for x, z in ((C, 2), (C, 6), (2, C), (6, C)):
        b.set(x, 7, z, 'light_blue_stained_glass_pane')
    b.set(C, 8, 2, GILDED)
    for x, z in ((3, 5), (5, 5)):
        lamp(b, x, 8, z, hanging=True)
    b.fill(2, 9, 2, 6, 9, 6, POLISHED)
    _eave(b, 9, 1, 7)

    # ---- tier three: the open bell chamber, y 10..12
    for x, z in ((2, 2), (6, 2), (2, 6), (6, 6)):
        column(b, x, 10, 12, z, PILLAR)
    for x, z in _ring(2, 6):
        if not (x in (2, 6) and z in (2, 6)):
            b.set(x, 10, z, FENCE)
    for x, z in ((C, 2), (C, 6), (2, C), (6, C)):
        b.candles(x, 11, z, 3, 'white')
    b.fill(2, 13, 2, 6, 13, 6, POLISHED)
    b.set(C, 12, C, 'bell', attachment='ceiling', facing='north', powered=False)
    b.spot('work', 3, 11, 4)
    _eave(b, 13, 1, 7)
    # the cap: two more stepped rings, a gilded crown, a gold jewel and a lantern
    for x, z in _ring(2, 6):
        stair(b, x, 14, z, POL_STAIRS, _inward(x, z, 2, 6) or ('south' if z == 2 else 'north'))
    b.fill(3, 14, 3, 5, 14, 5, POLISHED)
    for x, z in _ring(3, 5):
        stair(b, x, 15, z, POL_STAIRS, _inward(x, z, 3, 5) or ('south' if z == 3 else 'north'))
    b.set(C, 15, C, GILDED)
    b.set(C, 16, C, GILDED)
    b.set(C, 17, C, 'skyfriends:skystone_brick_wall')
    b.set(C, 18, C, 'gold_block')
    lamp(b, C, 19, C)

    # ---- the heart pillar and the ladder up its north face
    column(b, C, 1, 8, C, PILLAR)
    for y in range(1, 10):
        b.set(C, y, 3, 'ladder', facing='north', waterlogged=False)
    check(b)
