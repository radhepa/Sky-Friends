"""Shared drawing helpers for Cirri buildings (homes, decor and wild structures import these).

Round plans are sets of (x, z) columns: ``circle`` gives the classic Minecraft circles (radius 2.4 -> 5 wide,
3.4 -> 7, 4.3 -> 9, 5.4 -> 11), ``rim`` their one-block outline and ``inside`` what the outline encloses.
No buildings are registered here.
"""
import math

SKY = 'skyfriends:'
STONE = SKY + 'skystone'
BRICKS = SKY + 'skystone_bricks'
POLISHED = SKY + 'polished_skystone'
GILDED = SKY + 'gilded_skystone'
PILLAR = SKY + 'skystone_pillar'
P_STAIRS = SKY + 'polished_skystone_stairs'
P_SLAB = SKY + 'polished_skystone_slab'
B_STAIRS = SKY + 'skystone_brick_stairs'
B_SLAB = SKY + 'skystone_brick_slab'
B_WALL = SKY + 'skystone_brick_wall'
S_STAIRS = SKY + 'skystone_stairs'
S_SLAB = SKY + 'skystone_slab'
PLANKS = SKY + 'skywood_planks'
W_STAIRS = SKY + 'skywood_stairs'
W_SLAB = SKY + 'skywood_slab'
FENCE = SKY + 'skywood_fence'
LOG = SKY + 'skywood_log'
LEAVES = SKY + 'skywood_leaves'
CLOUD = SKY + 'cloud_block'
CHIME = SKY + 'wind_chime'
HARP = SKY + 'wind_harp'
LANTERN = SKY + 'sky_lantern'
GLASS = 'light_blue_stained_glass'
CLOTH = {c: f'{SKY}{c}_veilcloth' for c in ('white', 'sky', 'rose')}
CARPET = {c: f'{SKY}{c}_veilcloth_carpet' for c in ('white', 'sky', 'rose')}


def circle(cx, cz, r):
    """Columns within ``r`` of (cx, cz)."""
    out = set()
    for z in range(math.floor(cz - r) - 1, math.ceil(cz + r) + 2):
        for x in range(math.floor(cx - r) - 1, math.ceil(cx + r) + 2):
            if (x - cx) ** 2 + (z - cz) ** 2 <= r * r:
                out.add((x, z))
    return out


def octagon(x0, z0, x1, z1, cut):
    """A rectangle with its corners cut by ``cut`` cells."""
    out = set()
    for z in range(z0, z1 + 1):
        for x in range(x0, x1 + 1):
            dx = min(x - x0, x1 - x)
            dz = min(z - z0, z1 - z)
            if dx + dz >= cut:
                out.add((x, z))
    return out


def rim(mask):
    """The cells of ``mask`` with a side neighbour outside it (a one-block outline)."""
    return {(x, z) for (x, z) in mask
            if any((x + dx, z + dz) not in mask for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def inside(mask):
    return set(mask) - rim(mask)


def toward(cx, cz, x, z):
    """The horizontal direction from (x, z) toward the centre (the facing of a roof stair sloping up inward)."""
    dx, dz = cx - x, cz - z
    if abs(dx) > abs(dz):
        return 'east' if dx > 0 else 'west'
    return 'south' if dz > 0 else 'north'


def away(cx, cz, x, z):
    return {'east': 'west', 'west': 'east', 'north': 'south', 'south': 'north'}[toward(cx, cz, x, z)]


def put(b, cells, y, spec, **kw):
    for (x, z) in cells:
        b.set(x, y, z, spec, **kw)


def column(b, x, y0, y1, z, spec=PILLAR):
    for y in range(y0, y1 + 1):
        if spec.endswith(('_pillar', '_log')) or spec == SKY + 'skywood':
            b.set(x, y, z, spec, axis='y')
        else:
            b.set(x, y, z, spec)


def roof_ring(b, cells, y, cx, cz, spec=P_STAIRS, half='bottom'):
    """Stairs along ``cells`` all sloping up toward the centre (finish() rounds the corners)."""
    for (x, z) in cells:
        b.set(x, y, z, spec, facing=toward(cx, cz, x, z), half=half)


def corbels(b, cells, y, cx, cz, spec=P_STAIRS):
    """Upside-down stairs under an overhang, their solid side against the wall toward the centre."""
    for (x, z) in cells:
        b.set(x, y, z, spec, facing=toward(cx, cz, x, z), half='top')


def lantern(b, x, y, z, hanging=False):
    b.set(x, y, z, LANTERN, hanging='true' if hanging else 'false', waterlogged='false')


def chime(b, x, y, z):
    """A wind chime; it must hang directly under a solid block, a fence or a slab."""
    assert not b.get(x, y + 1, z)[0].endswith('air'), f'{b.name}: wind chime at {(x, y, z)} has nothing to hang from'
    b.set(x, y, z, CHIME)


def nest(b, x, y, z, cloth='rose', ring='white', spot=True):
    """A round sleeping nest on the floor below ``y``: a veilcloth cushion with cloth pillows round it.

    The Cirri sleeps floating in the air cell right over the cushion."""
    b.set(x, y, z, CLOTH[cloth])
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if b.inside(x + dx, y, z + dz) and not b.solid(x + dx, y, z + dz):
            b.set(x + dx, y, z + dz, CARPET[ring])
    if spot:
        b.spot('sleep', x, y + 1, z)


def clear_mask(b, cells, y0, y1):
    for y in range(y0, y1 + 1):
        for (x, z) in cells:
            if b.inside(x, y, z):
                b.set(x, y, z, 'air')


def round_window(b, x, y, z, axis, spec=GLASS):
    """A plus-shaped 'round' window centred at (x, y, z) in a wall running along ``axis`` ('x' or 'z')."""
    b.set(x, y, z, spec)
    b.set(x, y + 1, z, spec)
    b.set(x, y - 1, z, spec)
    if axis == 'x':
        b.set(x - 1, y, z, spec)
        b.set(x + 1, y, z, spec)
    else:
        b.set(x, y, z - 1, spec)
        b.set(x, y, z + 1, spec)
