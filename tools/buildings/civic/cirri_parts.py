"""Small drawing helpers shared by the Cirri civic and work buildings (no buildings here).

Imported by ``civic/*`` and ``work/*`` as ``from civic.cirri_parts import ...``. ``check(b)`` runs at the
end of every building and asserts that hanging and standing things have something to hang on or
stand on (wind chimes, lanterns, bells, ladders, signs, candles, carpets, pots, lily pads) and that
every spot is an empty cell.
"""
from kit import bid, full_cube, is_air, is_fence, is_wall, props

NS = 'skyfriends:'

# The palette, spelled once.
SKYSTONE = NS + 'skystone'
BRICKS = NS + 'skystone_bricks'
BRICK_STAIRS = NS + 'skystone_brick_stairs'
BRICK_SLAB = NS + 'skystone_brick_slab'
BRICK_WALL = NS + 'skystone_brick_wall'
POLISHED = NS + 'polished_skystone'
POL_STAIRS = NS + 'polished_skystone_stairs'
POL_SLAB = NS + 'polished_skystone_slab'
STONE_STAIRS = NS + 'skystone_stairs'
STONE_SLAB = NS + 'skystone_slab'
GILDED = NS + 'gilded_skystone'
PILLAR = NS + 'skystone_pillar'
CLOUD = NS + 'cloud_block'
LOG = NS + 'skywood_log'
WOOD = NS + 'skywood'
PLANKS = NS + 'skywood_planks'
WOOD_STAIRS = NS + 'skywood_stairs'
WOOD_SLAB = NS + 'skywood_slab'
FENCE = NS + 'skywood_fence'
GATE = NS + 'skywood_fence_gate'
LEAVES = NS + 'skywood_leaves'
WHITE = NS + 'white_veilcloth'
SKY = NS + 'sky_veilcloth'
ROSE = NS + 'rose_veilcloth'
WHITE_CARPET = NS + 'white_veilcloth_carpet'
SKY_CARPET = NS + 'sky_veilcloth_carpet'
ROSE_CARPET = NS + 'rose_veilcloth_carpet'
CHIME = NS + 'wind_chime'
HARP = NS + 'wind_harp'
LANTERN = NS + 'sky_lantern'
LOOT = 'skyfriends:chests/sky_village'


def stair(b, x, y, z, name, facing, half='bottom'):
    b.set(x, y, z, name, facing=facing, half=half, waterlogged=False)


def slab(b, x, y, z, name, kind='bottom'):
    b.set(x, y, z, name, type=kind, waterlogged=False)


def lamp(b, x, y, z, hanging=False):
    """A sky lantern standing on the block below (or hanging from the block above)."""
    b.set(x, y, z, LANTERN, hanging='true' if hanging else 'false', waterlogged='false')


def chime(b, x, y, z):
    b.set(x, y, z, CHIME)


def harp(b, x, y, z, facing):
    b.set(x, y, z, HARP, facing=facing)


def column(b, x, y0, y1, z, name=PILLAR):
    for y in range(y0, y1 + 1):
        b.set(x, y, z, name)


def toward(dx, dz):
    """The horizontal direction that points along (dx, dz) (the larger component wins; ties go to z)."""
    if abs(dx) > abs(dz):
        return 'east' if dx > 0 else 'west'
    return 'south' if dz > 0 else 'north'


def square_ring(lo, hi):
    """The (x, z) cells on the outline of the square lo..hi."""
    for x in range(lo, hi + 1):
        for z in range(lo, hi + 1):
            if x in (lo, hi) or z in (lo, hi):
                yield x, z


def inward(x, z, lo, hi):
    """Facing toward the middle for a cell on the outline of the square lo..hi; None at the corners."""
    on_x, on_z = x in (lo, hi), z in (lo, hi)
    if on_x and on_z:
        return None
    if on_x:
        return 'east' if x == lo else 'west'
    return 'south' if z == lo else 'north'


# ------------------------------------------------------------------ checks
def _hangs_from(state):
    """Whether a wind chime / hanging lantern / bell can hang under ``state``."""
    if is_air(state):
        return False
    name = bid(state)
    if full_cube(state) or is_fence(state) or is_wall(state) or name == 'iron_chain':
        return True
    if name.endswith('_slab'):
        return props(state).get('type') in ('bottom', 'double')
    if name.endswith('_stairs'):
        return props(state).get('half', 'bottom') == 'bottom'
    return False


def _stands_on(state):
    """Whether a lantern / candle / pot can stand on ``state`` (a sturdy centre on its top face)."""
    if is_air(state):
        return False
    name = bid(state)
    if full_cube(state) or is_fence(state) or is_wall(state):
        return True
    if name.endswith('_slab'):
        return props(state).get('type') in ('top', 'double')
    if name.endswith('_stairs'):
        return props(state).get('half') == 'top'
    return False


def check(b):
    """Assert every hanging or standing thing is held up and every spot is an empty cell."""
    def at(x, y, z):
        return b.grid.get((x, y, z))

    off = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}
    for (x, y, z), state in b.grid.items():
        if is_air(state):
            continue
        name, p = bid(state), props(state)
        where = f'{b.name}: {name} at {(x, y, z)}'
        if name == 'wind_chime':
            assert _hangs_from(at(x, y + 1, z)), f'{where} has nothing to hang from'
        elif name in ('sky_lantern', 'lantern'):
            if p.get('hanging') == 'true':
                assert _hangs_from(at(x, y + 1, z)), f'{where} (hanging) has nothing above'
            else:
                assert _stands_on(at(x, y - 1, z)), f'{where} has nothing to stand on'
        elif name == 'bell':
            if p.get('attachment') == 'ceiling':
                assert _hangs_from(at(x, y + 1, z)), f'{where} has no ceiling'
            elif p.get('attachment') == 'floor':
                assert _stands_on(at(x, y - 1, z)), f'{where} has no floor'
        elif name in ('ladder',) or name.endswith('_wall_sign'):
            dx, _, dz = off[p['facing']]
            behind = at(x - dx, y, z - dz)
            assert behind is not None and full_cube(behind), f'{where} has no wall behind it'
        elif name.endswith('candle') or name == 'flower_pot' or name.startswith('potted_') or name == 'decorated_pot':
            assert _stands_on(at(x, y - 1, z)), f'{where} has nothing to stand on'
        elif name.endswith('_carpet') or name == 'wind_harp' or name in ('loom', 'note_block'):
            assert not is_air(at(x, y - 1, z)) or y == 0, f'{where} floats'
        elif name == 'lily_pad':
            below = at(x, y - 1, z)
            assert below is not None and below[0] == 'minecraft:water', f'{where} is not on water'
        elif name in ('short_grass', 'fern') or name.endswith(('_tulip', '_orchid', 'allium', 'azure_bluet', 'cornflower',
                                                               'lily_of_the_valley', 'oxeye_daisy', 'dandelion', 'poppy')):
            below = at(x, y - 1, z)
            assert below is not None and bid(below) in ('grass_block', 'dirt', 'moss_block', 'rooted_dirt', 'podzol'), \
                f'{where} needs soil below'
    for s in b.meta.get('spots', []):
        assert is_air(at(*s['pos'])), f"{b.name}: {s['kind']} spot {s['pos']} is not an empty cell"
