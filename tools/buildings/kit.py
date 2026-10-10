"""The Sky Friends building kit.

A ``Build`` is a sparse voxel canvas. Buildings are small Python functions (see ``homes/``,
``civic/``, ``work/``, ``decor/`` and ``wild/``) that draw into one; the village planner
(``tools/villages``) sets finished buildings on floating islands and exports whole villages as
Minecraft structure templates (``Build.save_nbt``).

Coordinates: x east, y up, z south. A building's FRONT faces north (z = 0) and its entrance is on
that face; the planner turns buildings to face their paths.

Ground: layer ``y = b.ground`` is the island surface the building stands on (0 unless the building
is sunk into its island). Draw your floor on that layer. Layers below it are inside the island:
anything you draw there replaces the island's own blocks, and cells you set to ``'air'`` explicitly
are carved out.

Templates are placed with KNOWN SHAPES: Minecraft keeps the stored block states instead of
recomputing them from neighbours. ``Build.finish()`` therefore fills in what the game would derive
(fence/pane/wall/bar connections, wall posts, stair corner shapes), so draw them plainly and let
finish() connect them.

Mod blocks are written ``skyfriends:<id>`` (the ids in tools/blocks/catalog.py).
"""
from collections import Counter
import gzip
import json
import math
import random
import re
import struct
import zlib
from pathlib import Path

NS = 'skyfriends'
DATA_VERSION = 5023  # Minecraft 26.3 world format, as Village Friends uses.
HERE = Path(__file__).resolve().parent
BLOCK_IDS = set((HERE / 'block_ids.txt').read_text().split())
import sys as _sys  # noqa: E402
_sys.path.insert(0, str(HERE.parent / 'blocks'))
import catalog as _catalog  # noqa: E402
MOD_IDS = set(_catalog.BLOCKS)
MOD_FULL = {k for k, v in _catalog.BLOCKS.items() if v['shape'] in ('cube', 'pillar', 'log', 'wood')} - {'wind_stone'}
DIRS = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}
CLOCKWISE = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north'}
COUNTER = {v: k for k, v in CLOCKWISE.items()}
AXIS = {'north': 'z', 'south': 'z', 'east': 'x', 'west': 'x'}
AIR = ('minecraft:air', ())


def full_id(name):
    return name if ':' in name else 'minecraft:' + name


def block(spec, **props):
    """``block('purpur_stairs[facing=north]', half='top')`` -> canonical (id, props)."""
    if isinstance(spec, tuple):
        name, base = spec[0], dict(spec[1])
    else:
        match = re.fullmatch(r'([a-z0-9_:]+)(?:\[(.*)\])?', spec.strip())
        assert match, f'Bad block spec: {spec}'
        name, base = match.group(1), {}
        if match.group(2):
            for pair in match.group(2).split(','):
                key, value = pair.split('=')
                base[key.strip()] = value.strip()
    base.update({k: v for k, v in props.items() if v is not None})
    ident = full_id(name)
    if ident.endswith('_leaves'):
        base.setdefault('persistent', 'true')   # placed leaves must never decay
        base.setdefault('distance', '7')
        base.setdefault('waterlogged', 'false')
    if ident.startswith('minecraft:'):
        assert ident[10:] in BLOCK_IDS or ident == 'minecraft:air', f'Unknown block id {ident} (26.3 renamed chain -> iron_chain)'
    elif ident.startswith(NS + ':'):
        assert ident[len(NS) + 1:] in MOD_IDS, f'Unknown Sky Friends block {ident} (see tools/blocks/catalog.py)'
    else:
        raise AssertionError(f'Blocks from other mods are not allowed: {ident}')
    return ident, tuple(sorted((k, str(v).lower()) for k, v in base.items()))


def props(state):
    return dict(state[1])


def bid(state):
    return state[0][state[0].index(':') + 1:]


def with_props(state, **changes):
    merged = props(state)
    merged.update({k: str(v).lower() for k, v in changes.items()})
    return state[0], tuple(sorted(merged.items()))


# ---------------------------------------------------------------- block traits
def is_air(state):
    return state is None or state[0] in ('minecraft:air', 'minecraft:cave_air', 'minecraft:structure_void')


def is_stairs(state):
    return state is not None and state[0].endswith('_stairs')


def is_fence(state):
    return state is not None and state[0].endswith('_fence')


def is_gate(state):
    return state is not None and state[0].endswith('_fence_gate')


def is_pane(state):
    return state is not None and (state[0].endswith('glass_pane') or state[0] == 'minecraft:iron_bars')


def is_wall(state):
    return state is not None and state[0].endswith('_wall') and state[0].startswith(('minecraft:', NS + ':'))


def is_chorus(state):
    return state is not None and state[0] in ('minecraft:chorus_plant', 'minecraft:chorus_flower')


NOT_FULL_SUFFIXES = ('_stairs', '_fence', '_fence_gate', '_wall', '_pane', '_door', '_trapdoor', '_carpet',
                     '_pressure_plate', '_button', '_sign', '_banner', 'lantern', 'torch', '_rod', '_candle', 'candle',
                     '_shelf', '_head', '_skull', '_bud', '_cluster', 'potted_', '_slab')
NOT_FULL = {
    'iron_bars', 'iron_chain', 'chorus_plant', 'chorus_flower', 'ladder', 'vine', 'lectern', 'brewing_stand',
    'cauldron', 'water_cauldron', 'anvil', 'chipped_anvil', 'bell', 'enchanting_table', 'campfire',
    'soul_campfire', 'hopper', 'scaffolding', 'end_portal_frame', 'grindstone', 'stonecutter', 'chest',
    'ender_chest', 'trapped_chest', 'flower_pot', 'cobweb', 'sea_pickle', 'conduit', 'decorated_pot',
    'shulker_box', 'dragon_egg', 'end_gateway', 'end_portal', 'snow', 'moss_carpet', 'pale_moss_carpet',
    'heavy_core', 'pointed_dripstone', 'amethyst_cluster', 'small_amethyst_bud', 'resin_clump',
}


def full_cube(state):
    """Whether a block is a full cube that fences, panes and walls connect to."""
    if is_air(state):
        return False
    name = bid(state)
    if name.endswith('_slab'):
        return props(state).get('type') == 'double'
    if name in NOT_FULL or name.endswith('_shulker_box') or name.endswith(NOT_FULL_SUFFIXES) or name.startswith('potted_'):
        return False
    if state[0].startswith(NS + ':'):
        return name in MOD_FULL
    return True


def sturdy(state, face):
    """Whether ``state`` presents a full face toward ``face`` (a horizontal direction from the block)."""
    if is_stairs(state):
        return props(state).get('facing') == face
    return full_cube(state)


POST_OVERRIDES = ('torch', 'lantern', 'sign', 'banner', 'end_rod', 'campfire', 'flower_pot', 'potted_', 'skull',
                  'head', 'candle', 'iron_chain', 'lightning_rod')


def gate_connects(gate, direction):
    return AXIS[props(gate).get('facing', 'north')] == AXIS[CLOCKWISE[direction]]


# ---------------------------------------------------------------- rotation
ROT_FACING = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north', 'up': 'up', 'down': 'down'}
SIDE_KEYS = ('north', 'east', 'south', 'west')


def turn_state(state, turns):
    """The block state turned ``turns`` quarter turns clockwise (seen from above)."""
    turns %= 4
    if turns == 0 or not state[1]:
        return state
    p = props(state)
    for _ in range(turns):
        q = {}
        for k, v in p.items():
            if k == 'facing':
                q[k] = ROT_FACING.get(v, v)
            elif k == 'axis':
                q[k] = {'x': 'z', 'z': 'x'}.get(v, v)
            elif k == 'rotation':
                q[k] = str((int(v) + 4) % 16)
            elif k in SIDE_KEYS:
                q[ROT_FACING[k]] = v
            elif k == 'orientation':
                a, _, b = v.partition('_')
                q[k] = ROT_FACING.get(a, a) + '_' + ROT_FACING.get(b, b)
            else:
                q[k] = v
        p = q
    return state[0], tuple(sorted(p.items()))


# ------------------------------------------------------------------- the canvas
class Build:
    """Sparse voxel canvas for one building (or one whole village)."""

    def __init__(self, name, size, ground=0):
        self.name = name
        self.w, self.h, self.d = size
        self.ground = ground
        self.grid = {}          # (x, y, z) -> state; explicit air is kept (it carves)
        self.nbt = {}           # block entity data
        self.entities = []
        self.meta = {}

    # ---- access
    def inside(self, x, y, z):
        return 0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.d

    def get(self, x, y, z):
        return self.grid.get((x, y, z), AIR)

    def solid(self, x, y, z):
        return not is_air(self.grid.get((x, y, z)))

    def set(self, x, y, z, spec, nbt=None, clip=False, **kw):
        if not self.inside(x, y, z):
            if clip:
                return None
            raise AssertionError(f'{self.name}: block outside template at {(x, y, z)} size {(self.w, self.h, self.d)}')
        state = spec if isinstance(spec, tuple) and not kw else block(spec, **kw)
        pos = (x, y, z)
        self.grid[pos] = state
        self.nbt.pop(pos, None)
        if nbt is not None:
            self.nbt[pos] = nbt
        return state

    def __call__(self, x, y, z, spec, **kw):
        return self.set(x, y, z, spec, **kw)

    def fill(self, x0, y0, z0, x1, y1, z1, spec, only_air=False, clip=False, **kw):
        state = block(spec, **kw) if not isinstance(spec, tuple) or kw else spec
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                for x in range(min(x0, x1), max(x0, x1) + 1):
                    if only_air and self.solid(x, y, z):
                        continue
                    self.set(x, y, z, state, clip=clip)

    def clear(self, x0, y0, z0, x1, y1, z1):
        """Explicit air: carves whatever is there in the world (use it for rooms sunk below ground)."""
        self.fill(x0, y0, z0, x1, y1, z1, 'air', clip=True)

    def erase(self, x0, y0, z0, x1, y1, z1):
        """Forget cells entirely (the world keeps its own blocks there)."""
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                for x in range(min(x0, x1), max(x0, x1) + 1):
                    self.grid.pop((x, y, z), None)
                    self.nbt.pop((x, y, z), None)

    def replace(self, old, new, box=None):
        old_id = full_id(old)
        for (x, y, z), state in list(self.grid.items()):
            if box and not (box[0] <= x <= box[3] and box[1] <= y <= box[4] and box[2] <= z <= box[5]):
                continue
            if state[0] == old_id:
                self.set(x, y, z, new)

    # ---- shapes
    def disc(self, cx, y, cz, r, spec, only_air=False, **kw):
        """A filled circle of radius ``r`` centred on (cx, cz); half-integer centres work."""
        for z in range(math.floor(cz - r), math.ceil(cz + r) + 1):
            for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + 0.25 and self.inside(x, y, z):
                    if only_air and self.solid(x, y, z):
                        continue
                    self.set(x, y, z, spec, **kw)

    def ring(self, cx, y, cz, r, spec, thick=1.0, **kw):
        """A circle outline: cells whose distance from the centre is within ``thick`` of ``r``."""
        for z in range(math.floor(cz - r - 1), math.ceil(cz + r) + 2):
            for x in range(math.floor(cx - r - 1), math.ceil(cx + r) + 2):
                dist = math.hypot(x - cx, z - cz)
                if r - thick < dist <= r + 0.35 and self.inside(x, y, z):
                    self.set(x, y, z, spec, **kw)

    # ---- multi-block helpers with the state pairs Minecraft requires
    def door(self, x, y, z, facing='north', kind='birch', hinge='left', open_=False):
        """A two-block door; ``facing`` is the side you walk out toward."""
        for dy, half in ((0, 'lower'), (1, 'upper')):
            self.set(x, y + dy, z, f'{kind}_door', facing=facing, half=half, hinge=hinge, open=open_, powered=False)

    def chest(self, x, y, z, facing='south', loot=None):
        nbt = {'id': 'minecraft:chest'}
        if loot:
            nbt['LootTable'] = loot
        self.set(x, y, z, 'chest', nbt=nbt, facing=facing, type='single', waterlogged=False)

    def barrel(self, x, y, z, facing='up', loot=None):
        nbt = {'id': 'minecraft:barrel', 'LootTable': loot} if loot else None
        self.set(x, y, z, 'barrel', nbt=nbt, facing=facing, open=False)

    def sign(self, x, y, z, lines, facing='north', wood='birch', wall=True, color='black', glowing=False):
        """A sign reading ``lines`` (up to four). ``facing`` is the side the text faces."""
        text = (list(lines) + [''] * 4)[:4]
        sides = {'messages': text, 'color': color, 'has_glowing_text': bool(glowing)}
        nbt = {'id': 'minecraft:sign', 'front_text': sides,
               'back_text': {'messages': [''] * 4, 'color': 'black', 'has_glowing_text': False}, 'is_waxed': True}
        if wall:
            self.set(x, y, z, f'{wood}_wall_sign', nbt=nbt, facing=facing, waterlogged=False)
        else:
            rotation = {'south': 0, 'west': 4, 'north': 8, 'east': 12}[facing]
            self.set(x, y, z, f'{wood}_sign', nbt=nbt, rotation=rotation, waterlogged=False)

    def candles(self, x, y, z, count=3, color='white', lit=True):
        self.set(x, y, z, f'{color}_candle' if color else 'candle', candles=count, lit=lit, waterlogged=False)

    def lantern(self, x, y, z, hanging=False, kind='lantern'):
        self.set(x, y, z, kind, hanging=hanging, waterlogged=False)

    def end_rod(self, x, y, z, facing='up'):
        self.set(x, y, z, 'end_rod', facing=facing)

    def chorus(self, x, y, z, height=4, rng=None, branches=True, flower=True):
        """A planted chorus plant growing up from (x, y, z); it needs end stone directly below.

        Like vanilla's, it only branches from the top of a stalk (a stalk cell with chorus beside it
        and blocks above and below breaks on the first update). Flowers are fully grown (age 5) so
        plantings keep their shape. Drawn as plain ``chorus_plant``; ``finish()`` connects them."""
        rng = rng or random.Random(zlib.crc32(f'{self.name}:{x},{y},{z}'.encode()))
        assert self.get(x, y - 1, z)[0] == 'minecraft:end_stone', f'{self.name}: chorus at {(x, y, z)} needs end stone below'
        self._grow(x, y, z, height, rng, 0 if branches else 9, flower)

    def _grow(self, x, y, z, h, rng, depth, flower):
        def free(cx, cy, cz):
            return self.inside(cx, cy, cz) and not self.solid(cx, cy, cz)
        top = y - 1
        for k in range(h):
            if not free(x, y + k, z):
                break
            self.set(x, y + k, z, 'chorus_plant')
            top = y + k
        if top < y:
            return
        if depth < 2 and top - y >= (1 if depth else 2) and rng.random() < 0.85:
            grown = False
            for direction in rng.sample(list(DIRS), rng.randint(1, 3)):
                dx, dz = DIRS[direction]
                bx, bz = x + dx, z + dz
                if free(bx, top, bz) and not self.solid(bx, top - 1, bz) and free(bx, top + 1, bz)                         and not any(is_chorus(self.grid.get((bx + ex, top, bz + ez))) for ex, ez in DIRS.values() if (bx + ex, bz + ez) != (x, z)):
                    self._grow(bx, top, bz, rng.randint(1, 3), rng, depth + 1, flower)
                    grown = True
            if grown:
                return
        if flower and free(x, top + 1, z):
            self.set(x, top + 1, z, 'chorus_flower', age=5)

    def spot(self, kind, x, y, z):
        """Mark a place for the village: 'sleep' (one per resident), 'work', 'sit', 'stand', 'koi' (over a koi
        pool, where Cloud Koi are released) or 'lift' (the centre of the lift shaft, at the dock's floor level).

        Spots go into the village catalogue, not into the template; (x, y, z) is the air cell a Cirri hovers in."""
        assert kind in ('sleep', 'work', 'sit', 'stand', 'koi', 'lift'), kind
        assert self.inside(x, y, z), f'{self.name}: spot outside template {(x, y, z)}'
        self.meta.setdefault('spots', []).append({'kind': kind, 'pos': [x, y, z]})

    def end_crystal(self, x, y, z, base=False):
        """An end crystal floating over (x, y, z); it can't be broken by players (the Court's)."""
        self.entities.append({'pos': [x + .5, float(y), z + .5], 'blockPos': [x, y, z],
                              'nbt': {'id': 'minecraft:end_crystal', 'ShowBottom': bool(base), 'Invulnerable': True}})

    # ---- composition
    def paste(self, other, ox, oy, oz, turns=0):
        """Copy ``other`` into this canvas with its (0, 0, 0) at (ox, oy, oz), turned clockwise first."""
        src = other.turned(turns) if turns % 4 else other
        for (x, y, z), state in src.grid.items():
            p = (ox + x, oy + y, oz + z)
            if self.inside(*p):
                self.grid[p] = state
                self.nbt.pop(p, None)
                if (x, y, z) in src.nbt:
                    self.nbt[p] = json.loads(json.dumps(src.nbt[(x, y, z)]))
        for e in src.entities:
            e2 = json.loads(json.dumps(e))
            e2['pos'] = [e['pos'][0] + ox, e['pos'][1] + oy, e['pos'][2] + oz]
            e2['blockPos'] = [e['blockPos'][0] + ox, e['blockPos'][1] + oy, e['blockPos'][2] + oz]
            self.entities.append(e2)

    def turned(self, turns):
        """A copy turned ``turns`` quarter turns clockwise seen from above (north -> east)."""
        turns %= 4
        if turns == 0:
            return self
        out = self
        for _ in range(turns):
            nxt = Build(out.name, (out.d, out.h, out.w), out.ground)
            nxt.meta = dict(out.meta)
            if 'spots' in out.meta:
                nxt.meta['spots'] = [{**s, 'pos': [out.d - 1 - s['pos'][2], s['pos'][1], s['pos'][0]]} for s in out.meta['spots']]
            for (x, y, z), state in out.grid.items():
                p = (out.d - 1 - z, y, x)
                nxt.grid[p] = turn_state(state, 1)
                if (x, y, z) in out.nbt:
                    nxt.nbt[p] = out.nbt[(x, y, z)]
            for e in out.entities:
                e2 = json.loads(json.dumps(e))
                px, py, pz = e['pos']
                e2['pos'] = [out.d - pz, py, px]
                bx, by, bz = e['blockPos']
                e2['blockPos'] = [out.d - 1 - bz, by, bx]
                nxt.entities.append(e2)
            out = nxt
        return out

    # ------------------------------------------------------------ finishing
    def _connect(self):
        for pos, state in list(self.grid.items()):
            x, y, z = pos
            if is_fence(state) or is_pane(state) or is_wall(state):
                sides = {}
                for direction, (dx, dz) in DIRS.items():
                    other = self.grid.get((x + dx, y, z + dz))
                    if other is None or is_air(other):
                        sides[direction] = False
                    elif is_fence(state):
                        wooden = 'nether_brick' not in state[0]
                        sides[direction] = (is_fence(other) and ('nether_brick' not in other[0]) == wooden) \
                            or (is_gate(other) and gate_connects(other, direction)) \
                            or sturdy(other, OPPOSITE[direction])
                    elif is_pane(state):
                        sides[direction] = is_pane(other) or is_wall(other) or sturdy(other, OPPOSITE[direction])
                    else:
                        sides[direction] = is_wall(other) or is_pane(other) or (
                            is_gate(other) and gate_connects(other, direction)) or sturdy(other, OPPOSITE[direction])
                if is_wall(state):
                    above = self.grid.get((x, y + 1, z))
                    tall = above is not None and full_cube(above)
                    values = {k: ('tall' if tall else 'low') if v else 'none' for k, v in sides.items()}
                    n, s, e, w = (sides[k] for k in ('north', 'south', 'east', 'west'))
                    corner = (not (n or s or e or w)) or n != s or e != w
                    straight_tall = tall and ((n and s) or (e and w))
                    post_override = above is not None and not is_air(above) and any(t in bid(above) for t in POST_OVERRIDES)
                    up = corner or (not straight_tall and (post_override or tall))
                    self.grid[pos] = with_props(state, up=up, waterlogged=False, **values)
                else:
                    self.grid[pos] = with_props(state, waterlogged=False, **sides)
            elif state[0] == 'minecraft:chorus_plant':
                sides = {}
                for direction, (dx, dz) in DIRS.items():
                    sides[direction] = is_chorus(self.grid.get((x + dx, y, z + dz)))
                sides['up'] = is_chorus(self.grid.get((x, y + 1, z)))
                below = self.grid.get((x, y - 1, z))
                sides['down'] = is_chorus(below) or (below is not None and below[0] == 'minecraft:end_stone')
                self.grid[pos] = with_props(state, **sides)
        for pos, state in list(self.grid.items()):
            if is_stairs(state):
                p = props(state)
                if 'shape' not in p:
                    self.grid[pos] = with_props(state, shape=self._stair_shape(pos, state))
                    state = self.grid[pos]
                if 'waterlogged' not in props(state):
                    self.grid[pos] = with_props(state, waterlogged=False)
                if 'half' not in props(self.grid[pos]):
                    self.grid[pos] = with_props(self.grid[pos], half='bottom')
            elif bid(state).endswith('_slab') and 'type' not in props(state):
                self.grid[pos] = with_props(state, type='bottom', waterlogged=False)

    def _stair_shape(self, pos, state):
        x, y, z = pos
        p = props(state)
        facing, half = p.get('facing', 'north'), p.get('half', 'bottom')

        def stairs_at(direction):
            dx, dz = DIRS[direction]
            other = self.grid.get((x + dx, y, z + dz))
            return other if is_stairs(other) and props(other).get('half', 'bottom') == half else None

        def can_take(direction):
            dx, dz = DIRS[direction]
            other = self.grid.get((x + dx, y, z + dz))
            return not is_stairs(other) or props(other).get('facing', 'north') != facing \
                or props(other).get('half', 'bottom') != half

        front = stairs_at(facing)
        if front:
            f1 = props(front).get('facing', 'north')
            if AXIS[f1] != AXIS[facing] and can_take(OPPOSITE[f1]):
                return 'outer_left' if f1 == COUNTER[facing] else 'outer_right'
        back = stairs_at(OPPOSITE[facing])
        if back:
            f2 = props(back).get('facing', 'north')
            if AXIS[f2] != AXIS[facing] and can_take(f2):
                return 'inner_left' if f2 == COUNTER[facing] else 'inner_right'
        return 'straight'

    def _passable(self, state):
        if is_air(state):
            return True
        name = bid(state)
        if name.endswith('_door'):
            return False
        return name in ('ladder', 'torch', 'wall_torch', 'redstone_wire', 'rail', 'end_rod') \
            or name.endswith(('_pressure_plate', '_button', '_sign', '_banner', '_carpet'))

    def _check_doors(self):
        for (x, y, z), state in self.grid.items():
            if not state[0].endswith('_door') or props(state).get('half') != 'lower':
                continue
            upper = self.grid.get((x, y + 1, z))
            assert upper is not None and upper[0] == state[0] and props(upper).get('half') == 'upper', \
                f'{self.name}: door at {(x, y, z)} has no upper half'
            dx, dz = DIRS[props(state).get('facing', 'north')]
            for sx, sz in ((x + dx, z + dz), (x - dx, z - dz)):
                for h in (0, 1):
                    cell = (sx, y + h, sz)
                    if self.inside(*cell):
                        assert self._passable(self.get(*cell)), \
                            f'{self.name}: door at {(x, y, z)} needs two clear blocks on both sides; {cell} is {self.get(*cell)[0]}'

    def _check_chorus(self):
        """Vanilla ChorusPlantBlock / ChorusFlowerBlock.canSurvive, so no planting breaks on its first update."""
        def at(px, py, pz):
            return self.grid.get((px, py, pz), AIR)

        for (x, y, z), state in self.grid.items():
            if not is_chorus(state):
                continue
            below = at(x, y - 1, z)
            ok = below[0] in ('minecraft:chorus_plant', 'minecraft:end_stone')
            if state[0] == 'minecraft:chorus_plant':
                sandwiched = not is_air(at(x, y + 1, z)) and not is_air(below)
                for dx, dz in DIRS.values():
                    if at(x + dx, y, z + dz)[0] == 'minecraft:chorus_plant':
                        assert not sandwiched, f'{self.name}: chorus at {(x, y, z)} has chorus beside it and blocks above and below'
                        if at(x + dx, y - 1, z + dz)[0] in ('minecraft:chorus_plant', 'minecraft:end_stone'):
                            ok = True
            elif not ok and is_air(below):
                ok = sum(at(x + dx, y, z + dz)[0] == 'minecraft:chorus_plant' for dx, dz in DIRS.values()) == 1
            assert ok, f'{self.name}: chorus at {(x, y, z)} has nothing holding it up'

    def finish(self):
        self._connect()
        self._check_doors()
        self._check_chorus()
        return self

    # ------------------------------------------------------------- export
    def blocks(self, x0=0, z0=0, x1=None, z1=None, y0=None, y1=None):
        """(pos, state, nbt) for every stored cell in the column range, positions relative to (x0, y0, z0)."""
        x1 = self.w if x1 is None else x1
        z1 = self.d if z1 is None else z1
        y0 = 0 if y0 is None else y0
        for (x, y, z), state in self.grid.items():
            if x0 <= x < x1 and z0 <= z < z1 and (y1 is None or y < y1) and y >= y0:
                yield (x - x0, y - y0, z - z0), state, self.nbt.get((x, y, z))

    def save_nbt(self, path, x0=0, z0=0, x1=None, z1=None, y0=0, y1=None):
        """Write a gzipped structure template of the column range (default: everything)."""
        x1 = self.w if x1 is None else x1
        z1 = self.d if z1 is None else z1
        y1 = self.h if y1 is None else y1
        cells = list(self.blocks(x0, z0, x1, z1, y0, y1))
        counts = Counter(s for _, s, _ in cells)
        order = sorted(counts, key=lambda s: (-counts[s], s))
        index = {s: i for i, s in enumerate(order)}
        palette = []
        for state in order:
            # 26.3 writes block states with lower-case fields ('Name'/'Properties' load as air)
            entry = {'id': state[0]}
            if state[1]:
                entry['properties'] = dict(state[1])
            palette.append(entry)
        blocks = []
        for pos, state, nbt in sorted(cells, key=lambda c: (c[0][1], c[0][2], c[0][0])):
            entry = {'pos': list(pos), 'state': index[state]}
            if nbt:
                entry['nbt'] = nbt
            blocks.append(entry)
        entities = []
        for e in self.entities:
            bx, by, bz = e['blockPos']
            if x0 <= bx < x1 and z0 <= bz < z1 and y0 <= by < y1:
                entities.append({'pos': [float(e['pos'][0] - x0), float(e['pos'][1] - y0), float(e['pos'][2] - z0)],
                                 'blockPos': [bx - x0, by - y0, bz - z0], 'nbt': e['nbt']})
        data = {'DataVersion': DATA_VERSION, 'size': [x1 - x0, y1 - y0, z1 - z0], 'palette': palette,
                'blocks': blocks, 'entities': entities}
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        packed = gzip.compress(b'\x0a\x00\x00' + _payload(data), mtime=0)
        path.write_bytes(packed[:9] + b'\x03' + packed[10:])   # pin the gzip OS byte: identical output everywhere
        return len(blocks)


# ------------------------------------------------------------------ NBT writer
class Byte(int):
    pass


def _tag_type(value):
    if isinstance(value, (Byte, bool)):
        return 1
    if isinstance(value, int):
        return 3
    if isinstance(value, float):
        return 6
    if isinstance(value, str):
        return 8
    if isinstance(value, list):
        return 9
    if isinstance(value, dict):
        return 10
    raise TypeError(value)


def _string(value):
    encoded = value.encode('utf-8')
    return struct.pack('>H', len(encoded)) + encoded


def _payload(value):
    kind = _tag_type(value)
    if kind == 1:
        return struct.pack('>b', int(value))
    if kind == 3:
        return struct.pack('>i', value)
    if kind == 6:
        return struct.pack('>d', value)
    if kind == 8:
        return _string(value)
    if kind == 9:
        element = _tag_type(value[0]) if value else 10
        assert all(_tag_type(v) == element for v in value), value
        return bytes([element]) + struct.pack('>i', len(value)) + b''.join(_payload(v) for v in value)
    return b''.join(bytes([_tag_type(v)]) + _string(k) + _payload(v) for k, v in value.items()) + b'\0'


# ------------------------------------------------------------------ catalogue
CATALOG = {}


def building(name, people, role, size, ground=0, residents=0, door=None, about='', **extra):
    """Register a building function ``fn(b)`` that draws into a fresh ``Build`` of ``size``.

    ``people``: 'shulkin', 'chorrin', 'court' or 'shared'. ``role``: 'plaza', 'civic', 'work',
    'home', 'gate', 'wall' or 'decor'. ``door`` is the x of the entrance on the north face; the
    planner runs the path to the cell just outside it, (door, ground, -1). ``residents`` counts
    who will live there. ``extra`` flags go into the catalogue for the planner, e.g. ``rim=True``
    (wants the islet's outer edge, over the void) or ``job='archivist'``."""
    def wrap(fn):
        assert name not in CATALOG, f'duplicate building {name}'
        CATALOG[name] = dict(name=name, people=people, role=role, size=size, ground=ground, residents=residents,
                             door=door if door is not None else size[0] // 2, about=about, fn=fn, **extra)
        return fn
    return wrap


def make(name):
    """Draw and finish a registered building."""
    spec = CATALOG[name]
    b = Build(name, spec['size'], spec['ground'])
    b.meta = {k: v for k, v in spec.items() if k != 'fn'}
    spec['fn'](b)
    spots = b.meta.get('spots', [])
    sleeps = sum(1 for s in spots if s['kind'] == 'sleep')
    assert sleeps in (0, spec['residents']), f'{name}: {sleeps} sleep spots for {spec["residents"]} residents'
    return b.finish()


def load_all():
    """Import every building module so the catalogue is complete."""
    import importlib
    import pkgutil
    for folder in ('homes', 'civic', 'work', 'decor', 'wild', 'shared'):
        pkg = HERE / folder
        if not pkg.is_dir():
            continue
        for info in pkgutil.iter_modules([str(pkg)]):
            importlib.import_module(f'{folder}.{info.name}')
    return CATALOG
