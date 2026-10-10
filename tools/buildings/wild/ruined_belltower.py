"""The Ruined Belltower: an old Cirri bell tower on a cracked wild islet, half fallen.

Drawn whole first (an octagonal brick shaft with corner pillars and trim bands, an arched door, an open
belfry under a three-tier roof, a bell on a beam), then broken with a seeded random so it comes out the same
every time: the east side has collapsed down to the belfry floor, the roof survives only on the west and is
cracked, the walls are holed and weathered, rubble lies heaped where it fell, moss and vines have crept
over it, and the bell lies on the floor of the shaft beside a half-buried chest. Unlit on purpose."""
import math
import random

from kit import building
from homes.style import (STONE, BRICKS, POLISHED, GILDED, PILLAR, P_STAIRS, P_SLAB, B_STAIRS, B_SLAB, octagon,
                         rim, inside, put, column, roof_ring, toward)

C = 4
SEED = 'ruined_belltower'
FACINGS = ('north', 'east', 'south', 'west')


def intact(b):
    base = octagon(0, 0, 8, 8, 2)
    shaft = octagon(1, 1, 7, 7, 2)
    hall = inside(shaft)
    wall = rim(shaft)
    corners = {(3, 1), (5, 1), (1, 3), (1, 5), (7, 3), (7, 5), (3, 7), (5, 7)}
    b.clear(0, 1, 0, 8, 15, 8)
    # platform and a step all round the tower's foot
    put(b, base, 0, BRICKS)
    put(b, hall, 0, POLISHED)
    b.set(C, 0, C, GILDED)
    roof_ring(b, rim(base), 1, C, C, spec=B_STAIRS)
    b.set(4, 1, 0, 'air')                            # the way in    # the shaft (y 1..12), corner pillars, trim bands
    for y in range(1, 13):
        put(b, wall, y, BRICKS)
    for (x, z) in corners:
        column(b, x, 1, 12, z)
    for y in (4, 8):
        for (x, z) in wall - corners:
            b.set(x, y, z, POLISHED)
    for (x, z) in corners:
        b.set(x, 8, z, GILDED)
    # arched door on the north, slit windows, an open belfry on all eight faces
    b.set(4, 1, 1, 'air')
    b.set(4, 2, 1, 'air')
    b.set(4, 3, 1, GILDED)
    for (x, z) in ((1, 4), (7, 4), (4, 7)):
        b.set(x, 5, z, 'air')
        b.set(x, 6, z, 'air')
    for (x, z) in wall - corners:
        for y in (9, 10, 11):
            b.set(x, y, z, 'air')
    # belfry floor and the bell beam
    put(b, hall, 8, P_SLAB, type='top')
    for x in range(2, 7):
        b.set(x, 12, 4, PILLAR, axis='x')
    put(b, hall - {(x, 4) for x in range(2, 7)}, 12, 'air')
    # three-tier roof and a gilded finial
    t1 = inside(shaft)
    t2 = inside(t1)
    roof_ring(b, wall, 13, C, C)
    put(b, rim(t1), 13, POLISHED)
    roof_ring(b, rim(t1), 14, C, C)
    put(b, t2, 14, POLISHED)
    roof_ring(b, rim(t2), 15, C, C)
    b.set(C, 15, C, GILDED)
    # stair remnants on the inner walls, the old way up
    for (x, y, z) in ((5, 1, 2), (6, 2, 3), (6, 3, 4), (6, 4, 5), (5, 5, 6), (3, 6, 6), (2, 7, 5)):
        b.set(x, y, z, B_STAIRS, facing=toward(C, C, x, z), half='bottom')
    return shaft, wall, corners


def drop(b, x, z, state, top=6, **kw):
    """Let a piece of rubble fall down column (x, z) onto whatever is there; returns its y or None."""
    for y in range(1, top + 1):
        if not b.solid(x, y, z) and b.solid(x, y - 1, z) and not b.get(x, y - 1, z)[0].endswith(('chest', 'bell', 'carpet', 'chain')):
            b.set(x, y, z, state, **kw)
            return y
        if not b.solid(x, y, z) and not b.solid(x, y - 1, z):
            return None
    return None


def settle(b):
    """Remove every block no longer joined to the ground layer through other blocks (chains need a block above)."""
    loose = ('vine', 'moss_carpet', 'cobweb', 'iron_chain')
    solid = {p for p, s in b.grid.items() if not s[0].endswith('air') and not s[0].endswith(loose)}
    seen = {p for p in solid if p[1] == 0}
    todo = list(seen)
    while todo:
        x, y, z = todo.pop()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + d[0], y + d[1], z + d[2])
            if n in solid and n not in seen:
                seen.add(n)
                todo.append(n)
    for p in solid - seen:
        b.set(*p, 'air')
    for (x, y, z), s in sorted(b.grid.items(), key=lambda kv: -kv[0][1]):
        if s[0].endswith('iron_chain') and b.get(x, y + 1, z)[0].endswith('air'):
            b.set(x, y, z, 'air')


@building('ruined_belltower', 'cirri', 'wild', (9, 16, 9), door=4,
          about='A half-collapsed old Cirri bell tower: broken walls, a cracked roof, rubble, moss and vines, the bell fallen, a chest.')
def ruined_belltower(b):
    rng = random.Random(SEED)
    shaft, wall, corners = intact(b)

    # -- the collapse: everything above a broken line that dips toward the east is gone
    fallen = 0
    for (x, y, z), state in list(b.grid.items()):
        if y < 3 or state[0].endswith('air'):
            continue
        dx, dz = x - C + 0.01, z - C
        a = math.atan2(dz, dx)                       # 0 = east
        dip = max(0.0, math.cos(a - 0.35)) ** 1.3
        keep = 15.5 - 10.5 * dip + rng.uniform(-1.2, 0.8)
        if y > keep:
            b.set(x, y, z, 'air')
            fallen += 1
    # -- holes and weathering in what still stands
    for (x, y, z), state in list(b.grid.items()):
        if state[0].endswith('air') or y == 0:
            continue
        name = state[0]
        p = 0.03 + 0.012 * y
        if name.endswith(('skystone_bricks', 'polished_skystone', 'skystone_pillar', '_stairs', '_slab')) and rng.random() < p:
            b.set(x, y, z, 'air')
            fallen += 1
        elif name.endswith('skystone_bricks') and rng.random() < 0.28:
            b.set(x, y, z, STONE if rng.random() < 0.75 else 'mossy_cobblestone')
    # the belfry floor has mostly fallen in
    for (x, z) in inside(shaft):
        if b.get(x, 8, z)[0].endswith('_slab') and rng.random() < 0.6:
            b.set(x, 8, z, 'air')
    # cracks in the floor (never holes: the ground layer stays whole)
    for (x, z) in octagon(0, 0, 8, 8, 2):
        if rng.random() < 0.18:
            b.set(x, 0, z, rng.choice((STONE, STONE, 'mossy_cobblestone', 'moss_block')))

    # -- the bell, fallen to the floor of the shaft, and the half-buried chest
    b.set(4, 1, 4, 'bell', attachment='floor', facing='east', powered='false')
    b.chest(3, 1, 5, 'east', loot='skyfriends:chests/ruined_belltower')
    # the broken beam's chain still dangling
    for x in range(2, 7):
        if b.get(x, 12, 4)[0].endswith('skystone_pillar'):
            b.set(x, 11, 4, 'iron_chain', axis='y')
            b.set(x, 10, 4, 'iron_chain', axis='y')
            break

    # -- rubble: heaped mostly east of the tower and inside it
    pieces = [BRICKS] * 5 + [STONE] * 5 + [POLISHED, POLISHED, 'mossy_cobblestone', 'mossy_cobblestone', 'moss_block', GILDED]
    spots = [(x, z) for x in range(9) for z in range(9) if (x, z) in octagon(0, 0, 8, 8, 2)]
    weights = [3.0 if x >= 5 else (1.6 if (x, z) in inside(shaft) else 0.5) for (x, z) in spots]
    budget = min(fallen, 110)
    for _ in range(budget):
        x, z = rng.choices(spots, weights)[0]
        if (x, z) in ((4, 4), (3, 5), (4, 2), (4, 1), (4, 0)):
            continue                                  # keep the bell, chest and doorway clear
        r = rng.random()
        if r < 0.22:
            drop(b, x, z, B_STAIRS, top=3, facing=rng.choice(FACINGS), half=rng.choice(('bottom', 'top')))
        elif r < 0.4:
            drop(b, x, z, B_SLAB, top=3, type='bottom')
        else:
            drop(b, x, z, rng.choice(pieces), top=2 if x < 5 else 4)

    # -- nothing floats: drop whatever lost its hold on the ground
    settle(b)

    # -- moss on what lies open to the sky, vines down the north and west faces, cobwebs inside
    for (x, y, z), state in list(b.grid.items()):
        if state[0].endswith('air') or not b.inside(x, y + 1, z) or b.solid(x, y + 1, z):
            continue
        if state[0].endswith(('skystone_bricks', ':skystone', 'mossy_cobblestone', 'moss_block', 'polished_skystone')) \
                and rng.random() < 0.3 and state[0] != 'minecraft:bell':
            b.set(x, y + 1, z, 'moss_carpet')
    for (x, z) in wall:
        for side, (ox, oz) in (('south', (0, -1)), ('east', (-1, 0)), ('north', (0, 1))):
            vx, vz = x + ox, z + oz
            if not b.inside(vx, 0, vz) or (vx, vz) in shaft:
                continue
            if rng.random() < 0.35:
                top = rng.randint(6, 11)
                length = rng.randint(3, 6)
                for y in range(top, max(2, top - length), -1):
                    if b.solid(x, y, z) and not b.solid(vx, y, vz):
                        sides = {d: 'true' if d == side else 'false' for d in FACINGS}
                        b.set(vx, y, vz, 'vine', up='false', **sides)
                    else:
                        break
    for (x, y, z) in ((2, 7, 3), (6, 9, 5), (3, 1, 3), (5, 3, 6)):
        if not b.solid(x, y, z):
            b.set(x, y, z, 'cobweb')
