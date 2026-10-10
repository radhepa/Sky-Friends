"""Writes every block's and item's assets and data from tools/blocks/catalog.py.

  python tools/blocks/gen_blocks.py

Assets: blockstates, block models, item definitions and item models, English names (merged with the
sound subtitles in tools/sounds/lang.json and the mob names from tools/gen_assets.py).
Data: block loot, block and item tags, recipes, chest loot, and the skywood tree feature.

Stairs, slabs, walls, fences, fence gates, logs, carpets, leaves and saplings use vanilla's own
blockstate, recipe and loot files as templates, read from Minecraft's jars in the Gradle cache and
renamed, so they always match the game's format. (Nothing of vanilla's is copied into the mod.)
"""
import json
import os
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import catalog  # noqa: E402

NS = 'skyfriends'
ROOT = HERE.parent.parent
ASSETS = ROOT / 'src' / 'main' / 'resources' / 'assets' / NS
DATA = ROOT / 'src' / 'main' / 'resources' / 'data'
LOOM = Path.home() / '.gradle' / 'caches' / 'fabric-loom' / '26.3'
CLIENT_JAR, COMMON_JAR = LOOM / 'minecraft-client.jar', LOOM / 'minecraft-common.jar'
B = catalog.BLOCKS


def vanilla(path):
    jar = CLIENT_JAR if path.startswith('assets/') else COMMON_JAR
    with zipfile.ZipFile(jar) as z:
        return json.loads(z.read(path))


def swap(obj, pairs):
    """Rename ids in a vanilla JSON template: pairs of (vanilla string, ours), longest first."""
    if isinstance(obj, dict):
        return {k: swap(v, pairs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [swap(v, pairs) for v in obj]
    if isinstance(obj, str):
        for old, new in pairs:
            if obj == old:
                return new
        for old, new in pairs:
            if old in obj and obj.startswith('minecraft:'):
                return obj.replace(old, new)
        return obj
    return obj


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def ns(name):
    return f'{NS}:{name}'


def tex(base):
    """The texture a full-block base shows (its own, or a log's bark for wood)."""
    spec = B[base]
    if spec['shape'] == 'wood':
        return ns('block/' + spec['base'])
    return ns('block/' + base)


def model(name, parent, **textures):
    write(ASSETS / 'models' / 'block' / f'{name}.json', {'parent': parent, 'textures': textures})


def item(name, model_id, **extra):
    write(ASSETS / 'items' / f'{name}.json', {'model': {'type': 'minecraft:model', 'model': model_id, **extra}})


def item_generated(name, texture):
    write(ASSETS / 'models' / 'item' / f'{name}.json', {'parent': 'minecraft:item/generated', 'textures': {'layer0': texture}})
    item(name, ns('item/' + name))


# ------------------------------------------------------------------------------------- assets
def assets(bid, spec):
    shape = spec['shape']
    if shape == 'cube':
        model(bid, 'minecraft:block/cube_all', all=ns('block/' + bid))
        write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {'': {'model': ns('block/' + bid)}}})
        item(bid, ns('block/' + bid))
    elif shape in ('pillar', 'log'):
        model(bid, 'minecraft:block/cube_column', end=ns(f'block/{bid}_top'), side=ns(f'block/{bid}'))
        model(bid + '_horizontal', 'minecraft:block/cube_column_horizontal', end=ns(f'block/{bid}_top'), side=ns(f'block/{bid}'))
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/oak_log.json'),
                                                         [('minecraft:block/oak_log', ns('block/' + bid))]))
        item(bid, ns('block/' + bid))
    elif shape == 'wood':
        bark = ns('block/' + spec['base'])
        model(bid, 'minecraft:block/cube_column', end=bark, side=bark)
        model(bid + '_horizontal', 'minecraft:block/cube_column_horizontal', end=bark, side=bark)
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/oak_log.json'),
                                                         [('minecraft:block/oak_log', ns('block/' + bid))]))
        item(bid, ns('block/' + bid))
    elif shape == 'stairs':
        t = tex(spec['base'])
        for suffix, parent in (('', 'stairs'), ('_inner', 'inner_stairs'), ('_outer', 'outer_stairs')):
            model(bid + suffix, 'minecraft:block/' + parent, bottom=t, top=t, side=t)
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/andesite_stairs.json'),
                                                         [('minecraft:block/andesite_stairs', ns('block/' + bid))]))
        item(bid, ns('block/' + bid))
    elif shape == 'slab':
        t = tex(spec['base'])
        model(bid, 'minecraft:block/slab', bottom=t, top=t, side=t)
        model(bid + '_top', 'minecraft:block/slab_top', bottom=t, top=t, side=t)
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/andesite_slab.json'),
                                                         [('minecraft:block/andesite_slab', ns('block/' + bid)),
                                                          ('minecraft:block/andesite', ns('block/' + spec['base']))]))
        item(bid, ns('block/' + bid))
    elif shape == 'wall':
        t = tex(spec['base'])
        for suffix, parent in (('_post', 'template_wall_post'), ('_side', 'template_wall_side'),
                               ('_side_tall', 'template_wall_side_tall'), ('_inventory', 'wall_inventory')):
            model(bid + suffix, 'minecraft:block/' + parent, wall=t)
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/andesite_wall.json'),
                                                         [('minecraft:block/andesite_wall', ns('block/' + bid))]))
        item(bid, ns(f'block/{bid}_inventory'))
    elif shape == 'fence':
        t = tex(spec['base'])
        for suffix, parent in (('_post', 'fence_post'), ('_side', 'fence_side'), ('_inventory', 'fence_inventory')):
            model(bid + suffix, 'minecraft:block/' + parent, texture=t)
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/oak_fence.json'),
                                                         [('minecraft:block/oak_fence', ns('block/' + bid))]))
        item(bid, ns(f'block/{bid}_inventory'))
    elif shape == 'fence_gate':
        t = tex(spec['base'])
        for suffix, parent in (('', 'template_fence_gate'), ('_open', 'template_fence_gate_open'),
                               ('_wall', 'template_fence_gate_wall'), ('_wall_open', 'template_fence_gate_wall_open')):
            model(bid + suffix, 'minecraft:block/' + parent, texture=t)
        write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/oak_fence_gate.json'),
                                                         [('minecraft:block/oak_fence_gate', ns('block/' + bid))]))
        item(bid, ns('block/' + bid))
    elif shape == 'carpet':
        model(bid, 'minecraft:block/carpet', wool=tex(spec['base']))
        write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {'': {'model': ns('block/' + bid)}}})
        item(bid, ns('block/' + bid))
    elif shape == 'leaves':
        model(bid, 'minecraft:block/leaves', all=ns('block/' + bid))
        write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {'': {'model': ns('block/' + bid)}}})
        item(bid, ns('block/' + bid))
    elif shape == 'sapling':
        model(bid, 'minecraft:block/cross', cross=ns('block/' + bid))
        write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {'': {'model': ns('block/' + bid)}}})
        item_generated(bid, ns('block/' + bid))
    elif shape == 'custom':
        CUSTOM[bid](bid)
    else:
        raise ValueError(f'{bid}: unknown shape {shape}')


def box(frm, to, uv_all, faces='nsewud', rot=None, texture='#t'):
    names = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down'}
    out = {'from': frm, 'to': to, 'faces': {names[f]: {'uv': uv_all, 'texture': texture} for f in faces}}
    if rot:
        out['rotation'] = rot
    return out


def wind_chime(bid):
    t = ns('block/wind_chime')
    wood, gold, silver, bead, cord = [0, 0, 8, 8], [8, 0, 9, 16], [10, 0, 11, 16], [12, 0, 16, 4], [12, 4, 13, 16]
    tubes = [  # x, z, low end y, metal
        (4, 5, 4, gold), (10.5, 4.5, 6, silver), (11, 10.5, 3, gold), (5, 11, 5, silver), (8, 3, 7, gold)]
    elements = [box([3, 14, 3], [13, 15, 13], wood),                    # the wooden disc
                box([7.5, 15, 7.5], [8.5, 16, 8.5], cord, 'nsew'),      # hung from the block above
                box([7.5, 9, 7.5], [8.5, 14, 8.5], cord, 'nsew'),       # the striker's cord
                box([7, 7, 7], [9, 9, 9], bead)]                        # the striker bead
    for x, z, low, metal in tubes:
        elements.append(box([x - 0.5, low, z - 0.5], [x + 0.5, 14, z + 0.5], [metal[0], 0, metal[2], 14 - low], 'nsewd'))
    write(ASSETS / 'models' / 'block' / f'{bid}.json', {'textures': {'t': t, 'particle': t}, 'elements': elements})
    write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {'': {'model': ns('block/' + bid)}}})
    item_generated(bid, ns('item/' + bid))


def wind_harp(bid):
    t = ns('block/wind_harp')
    wood, gold, strings, inlay = [0, 0, 16, 6], [0, 6, 8, 10], [8, 6, 16, 16], [0, 10, 8, 16]
    elements = [box([2, 0, 5], [14, 2, 11], wood),                      # the base
                box([3, 2, 6.5], [5, 13, 9.5], wood),                    # left post
                box([11, 2, 6.5], [13, 15, 9.5], wood),                  # right post (taller)
                box([3, 13, 7], [11, 15, 9], wood),                      # the top bar
                box([2.5, 15, 6.5], [5.5, 16, 9.5], gold),               # finials
                box([10.5, 15, 6.5], [13.5, 16.5, 9.5], gold),
                box([4, 2, 6], [12, 2.5, 10], inlay, 'u'),               # inlay on the base
                box([5, 2, 8], [11, 13, 8], strings, 'ns')]              # the strings
    write(ASSETS / 'models' / 'block' / f'{bid}.json', {'textures': {'t': t, 'particle': t}, 'elements': elements})
    write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {
        f'facing={f}': {'model': ns('block/' + bid), **({'y': y} if y else {})}
        for f, y in (('north', 0), ('east', 90), ('south', 180), ('west', 270))}})
    item(bid, ns('block/' + bid))


def sky_lantern(bid):
    t = ns('block/' + bid)
    model(bid, 'minecraft:block/template_lantern', lantern=t)
    model(bid + '_hanging', 'minecraft:block/template_hanging_lantern', lantern=t)
    write(ASSETS / 'blockstates' / f'{bid}.json', swap(vanilla('assets/minecraft/blockstates/lantern.json'),
                                                     [('minecraft:block/lantern', ns('block/' + bid))]))
    item_generated(bid, ns('item/' + bid))


def wind_stone(bid):
    model(bid, 'minecraft:block/cube_bottom_top', top=ns('block/wind_stone_top'), bottom=ns('block/polished_skystone'),
          side=ns('block/wind_stone'))
    write(ASSETS / 'blockstates' / f'{bid}.json', {'variants': {'': {'model': ns('block/' + bid)}}})
    item(bid, ns('block/' + bid))


CUSTOM = {'wind_chime': wind_chime, 'wind_harp': wind_harp, 'sky_lantern': sky_lantern, 'wind_stone': wind_stone}


# ------------------------------------------------------------------------------------- data
def loot(bid, spec):
    shape = spec['shape']
    path = DATA / NS / 'loot_table' / 'blocks' / f'{bid}.json'
    if bid == 'wind_stone':
        return                                   # unbreakable: the village's
    if shape == 'slab':
        write(path, swap(vanilla('data/minecraft/loot_table/blocks/andesite_slab.json'),
                         [('minecraft:andesite_slab', ns(bid)), ('minecraft:blocks/andesite_slab', ns('blocks/' + bid))]))
    elif shape == 'leaves':
        table = swap(vanilla('data/minecraft/loot_table/blocks/oak_leaves.json'),
                     [('minecraft:oak_leaves', ns(bid)), ('minecraft:oak_sapling', ns('skywood_sapling')),
                      ('minecraft:apple', ns('sky_peach')), ('minecraft:blocks/oak_leaves', ns('blocks/' + bid))])
        # sky peaches are a little commoner than apples
        for pool in table['pools']:
            for entry in pool['entries']:
                if entry.get('name') == ns('sky_peach'):
                    for term in entry['condition']['terms']:
                        if term.get('type') == 'minecraft:table_bonus':
                            term['chances'] = [0.02, 0.0225, 0.025, 0.03, 0.06]
        write(path, table)
    else:
        write(path, swap(vanilla('data/minecraft/loot_table/blocks/andesite.json'),
                         [('minecraft:andesite', ns(bid)), ('minecraft:blocks/andesite', ns('blocks/' + bid))]))


TAGS = {
    'block': {
        'minecraft:mineable/pickaxe': lambda b, s: s.get('material') == 'stone' or s.get('material') == 'metal'
                                                   or (s['shape'] in ('stairs', 'slab', 'wall') and 'skystone' in s.get('base', '')),
        'minecraft:mineable/axe': lambda b, s: s.get('material') == 'wood' or 'skywood' in s.get('base', ''),
        'minecraft:mineable/hoe': lambda b, s: s['shape'] == 'leaves',
        'minecraft:stairs': lambda b, s: s['shape'] == 'stairs',
        'minecraft:slabs': lambda b, s: s['shape'] == 'slab',
        'minecraft:walls': lambda b, s: s['shape'] == 'wall',
        'minecraft:wooden_stairs': lambda b, s: s['shape'] == 'stairs' and 'skywood' in s['base'],
        'minecraft:wooden_slabs': lambda b, s: s['shape'] == 'slab' and 'skywood' in s['base'],
        'minecraft:fences': lambda b, s: s['shape'] == 'fence',
        'minecraft:wooden_fences': lambda b, s: s['shape'] == 'fence',
        'minecraft:fence_gates': lambda b, s: s['shape'] == 'fence_gate',
        'minecraft:logs': lambda b, s: s['shape'] in ('log', 'wood'),
        'minecraft:logs_that_burn': lambda b, s: s['shape'] in ('log', 'wood'),
        'minecraft:planks': lambda b, s: b == 'skywood_planks',
        'minecraft:leaves': lambda b, s: s['shape'] == 'leaves',
        'minecraft:saplings': lambda b, s: s['shape'] == 'sapling',
        'minecraft:wool_carpets': lambda b, s: False,
        f'{NS}:skywood_logs': lambda b, s: s['shape'] in ('log', 'wood'),
    },
    'item': {
        'minecraft:stairs': lambda b, s: s['shape'] == 'stairs',
        'minecraft:slabs': lambda b, s: s['shape'] == 'slab',
        'minecraft:walls': lambda b, s: s['shape'] == 'wall',
        'minecraft:wooden_stairs': lambda b, s: s['shape'] == 'stairs' and 'skywood' in s['base'],
        'minecraft:wooden_slabs': lambda b, s: s['shape'] == 'slab' and 'skywood' in s['base'],
        'minecraft:fences': lambda b, s: s['shape'] == 'fence',
        'minecraft:wooden_fences': lambda b, s: s['shape'] == 'fence',
        'minecraft:fence_gates': lambda b, s: s['shape'] == 'fence_gate',
        'minecraft:logs': lambda b, s: s['shape'] in ('log', 'wood'),
        'minecraft:logs_that_burn': lambda b, s: s['shape'] in ('log', 'wood'),
        'minecraft:planks': lambda b, s: b == 'skywood_planks',
        'minecraft:leaves': lambda b, s: s['shape'] == 'leaves',
        'minecraft:saplings': lambda b, s: s['shape'] == 'sapling',
        f'{NS}:skywood_logs': lambda b, s: s['shape'] in ('log', 'wood'),
    },
}


def tags():
    for kind, table in TAGS.items():
        for tag, test in table.items():
            space, name = tag.split(':')
            values = [ns(b) for b, s in B.items() if test(b, s)]
            if not values:
                continue
            write(DATA / space / 'tags' / kind / f'{name}.json', {'replace': False, 'values': values})


def shaped(name, pattern, key, result, count=1, category='building'):
    write(DATA / NS / 'recipe' / f'{name}.json', {'type': 'minecraft:crafting_shaped', 'category': category,
                                                  'key': key, 'pattern': pattern,
                                                  'result': {'count': count, 'id': result}})


def shapeless(name, ingredients, result, count=1, category='building'):
    write(DATA / NS / 'recipe' / f'{name}.json', {'type': 'minecraft:crafting_shapeless', 'category': category,
                                                  'ingredients': ingredients, 'result': {'count': count, 'id': result}})


def cutting(name, ingredient, result, count=1):
    write(DATA / NS / 'recipe' / f'{name}.json', {'type': 'minecraft:stonecutting', 'ingredient': ingredient,
                                                  'result': {'count': count, 'id': result}})


def recipes():
    for bid, spec in B.items():
        base = spec.get('base')
        if spec['shape'] == 'stairs':
            shaped(bid, ['#  ', '## ', '###'], {'#': ns(base)}, ns(bid), 4)
        elif spec['shape'] == 'slab':
            shaped(bid, ['###'], {'#': ns(base)}, ns(bid), 6)
        elif spec['shape'] == 'wall':
            shaped(bid, ['###', '###'], {'#': ns(base)}, ns(bid), 6, 'misc')
        elif spec['shape'] == 'fence':
            shaped(bid, ['W#W', 'W#W'], {'W': ns(base), '#': 'minecraft:stick'}, ns(bid), 3, 'misc')
        elif spec['shape'] == 'fence_gate':
            shaped(bid, ['#W#', '#W#'], {'W': ns(base), '#': 'minecraft:stick'}, ns(bid), 1, 'redstone')
        elif spec['shape'] == 'carpet':
            shaped(bid, ['##'], {'#': ns(base)}, ns(bid), 3, 'misc')
        if spec['shape'] in ('stairs', 'slab', 'wall') and 'skystone' in base:
            # every skystone shape can be cut straight from skystone, and from its own base
            for src in sorted({'skystone', base}):
                n = {'stairs': 1, 'slab': 2, 'wall': 1}[spec['shape']]
                cutting(f'{bid}_from_{src}_stonecutting', ns(src), ns(bid), n)
    shaped('polished_skystone', ['##', '##'], {'#': ns('skystone')}, ns('polished_skystone'), 4)
    shaped('skystone_bricks', ['##', '##'], {'#': ns('polished_skystone')}, ns('skystone_bricks'), 4)
    shaped('skystone_pillar', ['#', '#'], {'#': ns('polished_skystone')}, ns('skystone_pillar'), 2)
    for b in ('polished_skystone', 'skystone_bricks', 'skystone_pillar'):
        cutting(f'{b}_from_skystone_stonecutting', ns('skystone'), ns(b))
    shapeless('gilded_skystone', [ns('polished_skystone'), 'minecraft:gold_nugget', 'minecraft:gold_nugget'], ns('gilded_skystone'))
    shapeless('skywood_planks', [f'#{NS}:skywood_logs'], ns('skywood_planks'), 4)
    shaped('skywood', ['##', '##'], {'#': ns('skywood_log')}, ns('skywood'), 3)
    shapeless('white_veilcloth', ['minecraft:string'] * 4 + [ns('sky_scale')], ns('white_veilcloth'), 2)
    shapeless('sky_veilcloth', [ns('white_veilcloth'), 'minecraft:light_blue_dye'], ns('sky_veilcloth'))
    shapeless('rose_veilcloth', [ns('white_veilcloth'), 'minecraft:pink_dye'], ns('rose_veilcloth'))
    shaped('wind_chime', [' S ', 'N N', 'GIG'], {'S': ns('skywood_slab'), 'N': 'minecraft:string', 'G': 'minecraft:gold_nugget',
                                                  'I': 'minecraft:iron_nugget'}, ns('wind_chime'), 1, 'misc')
    shaped('wind_harp', ['G#G', '#S#', '###'], {'G': 'minecraft:gold_ingot', '#': ns('skywood_planks'),
                                                 'S': 'minecraft:string'}, ns('wind_harp'), 1, 'misc')
    shaped('sky_lantern', ['NNN', 'NTN', 'NNN'], {'N': 'minecraft:gold_nugget', 'T': 'minecraft:torch'}, ns('sky_lantern'), 1, 'misc')
    shaped('windsong_flute', ['  S', ' # ', 'G  '], {'S': ns('sky_scale'), '#': ns('skywood_planks'), 'G': 'minecraft:gold_nugget'},
           ns('windsong_flute'), 1, 'misc')
    shaped('cirrus_veil', ['W W', 'WSW', 'RMR'], {'W': ns('white_veilcloth'), 'S': ns('sky_scale'), 'R': ns('rose_veilcloth'),
                                                   'M': 'minecraft:phantom_membrane'}, ns('cirrus_veil'), 1, 'equipment')


def item_pool(entries, rolls=(2, 5)):
    out = []
    for name, weight, lo, hi in entries:
        e = {'type': 'minecraft:item', 'name': name, 'weight': weight}
        if hi > 1:
            e['modifier'] = {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}
        out.append(e)
    return {'rolls': {'type': 'minecraft:uniform', 'min': rolls[0], 'max': rolls[1]}, 'entries': out}


def chest_loot():
    tables = {
        'sky_village': [item_pool([(ns('sky_peach'), 20, 1, 4), (ns('white_veilcloth'), 12, 1, 3), (ns('sky_veilcloth'), 8, 1, 2),
                                   (ns('rose_veilcloth'), 8, 1, 2), (ns('sky_scale'), 15, 1, 3), ('minecraft:string', 12, 2, 6),
                                   ('minecraft:amethyst_shard', 8, 1, 3), (ns('skywood_sapling'), 6, 1, 2),
                                   ('minecraft:feather', 10, 1, 4), ('minecraft:gold_nugget', 10, 2, 7)], (3, 6))],
        'wind_shrine': [item_pool([(ns('sky_scale'), 20, 2, 5), (ns('sky_peach'), 15, 1, 3), ('minecraft:amethyst_shard', 12, 2, 5),
                                   ('minecraft:gold_ingot', 6, 1, 3), (ns('sky_lantern'), 6, 1, 2), (ns('wind_chime'), 5, 1, 1),
                                   ('minecraft:music_disc_otherside', 1, 1, 1), ('minecraft:phantom_membrane', 8, 1, 2)], (3, 6)),
                        item_pool([(ns('windsong_flute'), 3, 1, 1), (ns('cirrus_veil'), 1, 1, 1), ('minecraft:air', 4, 1, 1)], (1, 1))],
        'ruined_belltower': [item_pool([('minecraft:gold_nugget', 15, 3, 9), ('minecraft:gold_ingot', 6, 1, 3), (ns('sky_scale'), 12, 1, 4),
                                        ('minecraft:bone', 10, 1, 4), ('minecraft:string', 10, 2, 5), ('minecraft:phantom_membrane', 8, 1, 3),
                                        ('minecraft:emerald', 6, 1, 3), (ns('gilded_skystone'), 5, 1, 3),
                                        ('minecraft:music_disc_strad', 1, 1, 1), ('minecraft:name_tag', 3, 1, 1)], (4, 7)),
                             item_pool([(ns('cirrus_veil'), 1, 1, 1), (ns('windsong_flute'), 2, 1, 1), ('minecraft:air', 6, 1, 1)], (1, 1))],
    }
    for name, pools in tables.items():
        for pool in pools:
            for e in pool['entries']:
                if e['name'] == 'minecraft:air':
                    e['type'] = 'minecraft:empty'
                    del e['name']
        write(DATA / NS / 'loot_table' / 'chests' / f'{name}.json',
              {'type': 'minecraft:chest', 'pools': pools, 'random_sequence': ns('chests/' + name)})


def tree_feature():
    """The skywood tree a sapling grows: a straight pale trunk under a rounded crown of blossom."""
    tree = swap(vanilla('data/minecraft/worldgen/feature/birch.json'),
                [('minecraft:birch_log', ns('skywood_log')), ('minecraft:birch_leaves', ns('skywood_leaves'))])
    tree['trunk_placer'] = {'type': 'minecraft:straight_trunk_placer', 'base_height': 5, 'height_rand_a': 2, 'height_rand_b': 1}
    tree['foliage_placer'] = {'type': 'minecraft:fancy_foliage_placer', 'radius': 2, 'offset': 4, 'height': 4}
    tree['minimum_size'] = {'type': 'minecraft:two_layers_feature_size', 'limit': 0, 'lower_size': 0, 'upper_size': 0}
    write(DATA / NS / 'worldgen' / 'feature' / 'skywood.json', tree)


def lang():
    path = ASSETS / 'lang' / 'en_us.json'
    names = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    for bid, spec in B.items():
        names[f'block.{NS}.{bid}'] = spec['name']
    for iid, name in catalog.ITEMS.items():
        names[f'item.{NS}.{iid}'] = name
    names[f'item.{NS}.cirrus_veil.desc'] = 'Glide gently when falling; sneak to drop'
    names[f'item.{NS}.windsong_flute.desc'] = 'The Cirri turn to listen'
    names[f'block.{NS}.wind_stone.desc'] = 'Stand in its wind to rise; sneak to sink'
    subtitles = HERE.parent / 'sounds' / 'lang.json'
    if subtitles.exists():
        names.update(json.loads(subtitles.read_text(encoding='utf-8')))
    write(path, dict(sorted(names.items())))


def main():
    for bid, spec in B.items():
        assets(bid, spec)
        loot(bid, spec)
    for iid in catalog.ITEMS:
        item_generated(iid, ns('item/' + iid))
    tags()
    recipes()
    chest_loot()
    tree_feature()
    lang()
    missing = [t for t in catalog.block_textures() if not (ASSETS / 'textures' / 'block' / f'{t}.png').exists()]
    missing += ['item/' + t for t in catalog.item_textures() if not (ASSETS / 'textures' / 'item' / f'{t}.png').exists()]
    print(f'{len(B)} blocks, {len(catalog.ITEMS)} items written' + (f'; textures still missing: {", ".join(missing)}' if missing else ''))


if __name__ == '__main__':
    main()
