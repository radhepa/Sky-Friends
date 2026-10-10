"""How blocks look in the offline previews: colour per face and an approximate shape.

Colours are averaged from the vanilla block textures (``texture_colors.json``, the same table
Village Friends uses), so silhouettes and palettes read correctly. Final checks belong in
Minecraft (``gradlew runClientGameTest -PskyTests=Villages``).
"""
import json
from pathlib import Path

from kit import Build, full_cube, is_air, props, bid

HERE = Path(__file__).resolve().parent
COLORS = json.loads((HERE / 'texture_colors.json').read_text())
if (HERE / 'mod_colors.json').exists():   # Sky Friends blocks, averaged from our own textures
    COLORS.update(json.loads((HERE / 'mod_colors.json').read_text()))
WOODS = ('oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak', 'mangrove', 'cherry', 'pale_oak', 'bamboo',
         'crimson', 'warped', 'poplar')
SUFFIXES = ('_stairs', '_slab', '_wall', '_fence_gate', '_fence', '_pressure_plate', '_button', '_carpet',
            '_trapdoor', '_door', '_pane', '_wall_banner', '_banner', '_wall_sign', '_sign', '_wall_hanging_sign',
            '_hanging_sign')
SPECIAL = {
    'lantern': (226, 170, 80), 'soul_lantern': (90, 190, 200), 'copper_lantern': (120, 220, 160),
    'campfire': (230, 140, 50), 'end_rod': (246, 240, 250), 'iron_chain': (60, 60, 72), 'bell': (230, 190, 60),
    'chorus_plant': (94, 57, 94), 'chorus_flower': (175, 140, 176), 'brewing_stand': (120, 110, 100),
    'water': (63, 118, 228), 'lava': (207, 92, 20), 'cauldron': (70, 70, 75), 'end_portal_frame': (130, 150, 110),
    'dragon_head': (30, 30, 30), 'dragon_wall_head': (30, 30, 30), 'shulker_box': (150, 110, 150),
}
GLOWING = ('end_rod', 'lantern', 'froglight', 'sea_lantern', 'glowstone', 'shroomlight', 'candle', 'crying_obsidian',
           'respawn_anchor', 'campfire', 'beacon', 'torch', 'redstone_lamp', 'amethyst_cluster', 'magma')


def _lookup(*names):
    for name in names:
        if name in COLORS:
            return COLORS[name]
    return None


def color(name, face, p):
    if name in SPECIAL:
        return SPECIAL[name]
    if name.endswith('_shulker_box'):
        found = _lookup(name)
        if found:
            return tuple(found[:3])
    base = name
    for suffix in SUFFIXES:
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break
    if name.endswith(('_carpet', '_wool', '_banner', '_wall_banner')):
        found = _lookup(name.split('_carpet')[0].split('_wall_banner')[0].split('_banner')[0] + '_wool')
        if found:
            return tuple(found[:3])
    if name.endswith('candle'):
        found = _lookup(name)
        if found:
            return tuple(found[:3])
    candidates = []
    if face == 'top':
        candidates += [name + '_top', base + '_top']
    candidates += [name, name + '_side', base, base + 's', base + '_planks', base + '_side', base + '_bricks',
                   base.replace('_tile', '_tiles'), base.replace('brick', 'bricks'), base + '_block']
    if base in WOODS:
        candidates.insert(0, base + '_planks')
    if base == 'purpur':
        candidates.insert(0, 'purpur_block')
    if base == 'end_stone_brick':
        candidates.insert(0, 'end_stone_bricks')
    if name == 'purpur_pillar':
        candidates.insert(0, 'purpur_pillar_top' if face == 'top' and p.get('axis', 'y') == 'y' else 'purpur_pillar_side')
    if name.startswith('potted_'):
        candidates = [name[7:], 'flower_pot']
    found = _lookup(*candidates)
    if found is None and name.endswith('_door'):
        found = _lookup(name + '_bottom')
    if found is None and 'glass' in name:
        found = (170, 200, 215)
    if found is None:
        found = (200, 0, 200)
    return tuple(found[:3])


def alpha(name):
    if 'glass' in name:
        return 0.55
    return 1.0


def glows(name):
    return any(g in name for g in GLOWING)


def boxes(name, p):
    """Approximate visual boxes in 1/16 block units: (x0, y0, z0, x1, y1, z1)."""
    half = p.get('half')
    if name.endswith('_slab'):
        t = p.get('type', 'bottom')
        return [(0, 0, 0, 16, 16, 16)] if t == 'double' else [(0, 0 if t == 'bottom' else 8, 0, 16, 8 if t == 'bottom' else 16, 16)]
    if name.endswith('_stairs'):
        f = p.get('facing', 'north')
        bottom = (0, 0, 0, 16, 8, 16) if half != 'top' else (0, 8, 0, 16, 16, 16)
        y0, y1 = (8, 16) if half != 'top' else (0, 8)
        back = {'north': (0, y0, 0, 16, y1, 8), 'south': (0, y0, 8, 16, y1, 16),
                'west': (0, y0, 0, 8, y1, 16), 'east': (8, y0, 0, 16, y1, 16)}[f]
        return [bottom, back]
    if name.endswith('_fence') or name.endswith('_wall') or name.endswith('_pane') or name == 'iron_bars':
        wall = name.endswith('_wall')
        r = 4 if wall else (2 if name.endswith('_fence') else 1)
        top = 16 if not wall or p.get('up', 'true') == 'true' else 14
        out = [(8 - r, 0, 8 - r, 8 + r, top, 8 + r)]
        arm = 3 if wall else 1
        ay0, ay1 = (0, 14) if wall else ((6, 15) if name.endswith('_fence') else (0, 16))
        for d, box in (('north', (8 - arm, ay0, 0, 8 + arm, ay1, 8)), ('south', (8 - arm, ay0, 8, 8 + arm, ay1, 16)),
                       ('west', (0, ay0, 8 - arm, 8, ay1, 8 + arm)), ('east', (8, ay0, 8 - arm, 16, ay1, 8 + arm))):
            if p.get(d, 'false') not in ('false', 'none'):
                out.append(box)
        return out
    if name == 'chorus_plant':
        out = [(4, 4, 4, 12, 12, 12)]
        for d, box in (('north', (4, 4, 0, 12, 12, 4)), ('south', (4, 4, 12, 12, 12, 16)), ('west', (0, 4, 4, 4, 12, 12)),
                       ('east', (12, 4, 4, 16, 12, 12)), ('up', (4, 12, 4, 12, 16, 12)), ('down', (4, 0, 4, 12, 4, 12))):
            if p.get(d) == 'true':
                out.append(box)
        return out
    if name == 'chorus_flower':
        return [(2, 2, 2, 14, 14, 14)]
    if name.endswith('_fence_gate'):
        return [(0, 5, 7, 16, 15, 9)] if p.get('facing', 'north') in ('north', 'south') else [(7, 5, 0, 9, 15, 16)]
    if name.endswith('_door'):
        f = p.get('facing', 'north')
        if p.get('open') == 'true':
            f = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north'}[f]
        return [{'north': (0, 0, 13, 16, 16, 16), 'south': (0, 0, 0, 16, 16, 3),
                 'west': (13, 0, 0, 16, 16, 16), 'east': (0, 0, 0, 3, 16, 16)}[f]]
    if name.endswith('_trapdoor'):
        if p.get('open') == 'true':
            f = p.get('facing', 'north')
            return [{'north': (0, 0, 13, 16, 16, 16), 'south': (0, 0, 0, 16, 16, 3),
                     'west': (13, 0, 0, 16, 16, 16), 'east': (0, 0, 0, 3, 16, 16)}[f]]
        return [(0, 13, 0, 16, 16, 16)] if half == 'top' else [(0, 0, 0, 16, 3, 16)]
    if name.endswith('_carpet') or name.endswith('_pressure_plate'):
        return [(0, 0, 0, 16, 1, 16)]
    if name in ('lantern', 'soul_lantern', 'copper_lantern'):
        return [(5, 1, 5, 11, 10, 11)] if p.get('hanging') == 'true' else [(5, 0, 5, 11, 9, 11)]
    if name in ('end_rod', 'lightning_rod', 'torch'):
        f = p.get('facing', 'up')
        if f in ('up', 'down'):
            return [(7, 0, 7, 9, 16, 9)]
        return [(0, 7, 7, 16, 9, 9)] if f in ('east', 'west') else [(7, 7, 0, 9, 9, 16)]
    if name == 'iron_chain':
        a = p.get('axis', 'y')
        return [(7, 0, 7, 9, 16, 9)] if a == 'y' else [(0, 7, 7, 16, 9, 9)] if a == 'x' else [(7, 7, 0, 9, 9, 16)]
    if name.endswith('candle'):
        n = int(p.get('candles', 1))
        return [(6, 0, 6, 10, 6, 10)] if n == 1 else [(4, 0, 4, 12, 6, 12)]
    if name in ('campfire', 'soul_campfire'):
        return [(0, 0, 0, 16, 7, 16)]
    if name == 'flower_pot' or name.startswith('potted_'):
        return [(5, 0, 5, 11, 6, 11), (6, 6, 6, 10, 12, 10)] if name.startswith('potted_') else [(5, 0, 5, 11, 6, 11)]
    if name in ('bell',):
        return [(4, 4, 4, 12, 13, 12)]
    if name.endswith('_wall_banner') or name.endswith('_banner'):
        f = p.get('facing', 'north')
        return [{'north': (0, 0, 14, 16, 16, 16), 'south': (0, 0, 0, 16, 16, 2),
                 'west': (14, 0, 0, 16, 16, 16), 'east': (0, 0, 0, 2, 16, 16)}.get(f, (6, 0, 6, 10, 16, 10))]
    if name.endswith('_wall_sign'):
        f = p.get('facing', 'north')
        return [{'north': (0, 4, 14, 16, 12, 16), 'south': (0, 4, 0, 16, 12, 2),
                 'west': (14, 4, 0, 16, 12, 16), 'east': (0, 4, 0, 2, 12, 16)}[f]]
    if name.endswith('_sign'):
        return [(1, 8, 7, 15, 16, 9), (7, 0, 7, 9, 8, 9)]
    if name == 'ladder':
        f = p.get('facing', 'north')
        return [{'north': (0, 0, 14, 16, 16, 16), 'south': (0, 0, 0, 16, 16, 2),
                 'west': (14, 0, 0, 16, 16, 16), 'east': (0, 0, 0, 2, 16, 16)}[f]]
    if name in ('anvil', 'grindstone', 'brewing_stand', 'cauldron', 'water_cauldron', 'lectern'):
        return [(1, 0, 1, 15, 14, 15)]
    if name == 'stonecutter':
        return [(0, 0, 0, 16, 9, 16)]
    if name == 'end_portal_frame':
        return [(0, 0, 0, 16, 13, 16)] + ([(4, 13, 4, 12, 16, 12)] if p.get('eye') == 'true' else [])
    if name == 'enchanting_table':
        return [(0, 0, 0, 16, 12, 16)]
    if name in ('chest', 'ender_chest', 'trapped_chest'):
        return [(1, 0, 1, 15, 14, 15)]
    if name.endswith('_head') or name.endswith('_skull'):
        return [(4, 0, 4, 12, 8, 12)]
    if name.endswith('_shelf'):
        f = p.get('facing', 'north')
        return [{'north': (0, 0, 10, 16, 16, 16), 'south': (0, 0, 0, 16, 16, 6),
                 'west': (10, 0, 0, 16, 16, 16), 'east': (0, 0, 0, 6, 16, 16)}[f]]
    if name in ('amethyst_cluster', 'large_amethyst_bud', 'medium_amethyst_bud', 'small_amethyst_bud'):
        return [(4, 0, 4, 12, 10, 12)]
    if name == 'dragon_egg':
        return [(2, 0, 2, 14, 16, 14)]
    return [(0, 0, 0, 16, 16, 16)]


def export(build, cut=None, ground=None, cull=True):
    """Compact preview data: palette entries with shapes and colours, plus visible blocks.

    ``ground`` optionally adds islet undersides: a dict (x, z) -> (top, depth) in canvas space,
    drawn as end stone below each top. ``cut`` hides everything above that layer."""
    states, index, cells = [], {}, {}
    for (x, y, z), state in build.grid.items():
        if is_air(state) or (cut is not None and y > cut):
            continue
        cells[(x, y, z)] = state
    if ground:
        stone = ('minecraft:end_stone', ())
        for (x, z), (top, depth) in ground.items():
            for y in range(top - depth, top + 1):
                if (x, y, z) not in cells and not (x, y, z) in build.grid:
                    cells[(x, y, z)] = stone
    solid = {pos for pos, s in cells.items() if full_cube(s) and alpha(bid(s)) == 1.0}
    out = []
    for (x, y, z), state in cells.items():
        if cull and (x, y, z) in solid and all(n in solid for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z),
                                                            (x, y, z + 1), (x, y, z - 1))):
            continue
        if state not in index:
            name, p = bid(state), props(state)
            index[state] = len(states)
            states.append({'n': name, 'b': boxes(name, p), 't': color(name, 'top', p), 's': color(name, 'side', p),
                           'a': alpha(name), 'g': 1 if glows(name) else 0, 'f': 1 if (x, y, z) in solid else 0})
        out += [x, y, z, index[state]]
    return {'size': [build.w, build.h, build.d], 'palette': states, 'blocks': out}
