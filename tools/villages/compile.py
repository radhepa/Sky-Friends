"""Compile every sky layout into Minecraft data.

For each layout it plans the place (plan.py), cuts the canvas into 32x32 column tiles (structure
templates under data/skyfriends/structure/<layout>/), writes its roster (roster.py), and writes one
``skyfriends:sky_structure`` per kind with its layouts embedded, the structure sets and the biome tags.

    python tools/villages/compile.py                 everything
    python tools/villages/compile.py village_a       one layout (worldgen JSON still lists all)
    python tools/villages/compile.py --preview       also write tools/villages/out/<layout>.json for a preview page
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / 'src' / 'main' / 'resources' / 'data' / 'skyfriends'
sys.path.insert(0, str(HERE.parent / 'buildings'))
sys.path.insert(0, str(HERE))
import kit  # noqa: E402
import look  # noqa: E402
from plan import Program, plan, Y0  # noqa: E402
from roster import roster  # noqa: E402

TILE = 32

CORE = ['bell_pagoda', 'hall_of_echoes', 'loom_house', 'cloud_garden', 'market_pavilion', 'lantern_spire']
LAYOUTS = {
    # sky villages: the court, the dock, the core, homes for a dozen and more, a few floating gardens
    'village_a': (Program('village', 'veil_court', CORE + ['nest_house', 'nest_house', 'nest_house_large', 'twin_nest', 'rim_house',
                                                          'twin_nest', 'koi_pond', 'harp_stand'],
                          gap=(5, 9), tiers=(-4, -1, 0, 2, 4, 7), dock=True, extra_islets=(3, (4, 7)), koi=4), 11),
    'village_b': (Program('village', 'veil_court', ['hall_of_echoes', 'cloud_garden', 'bell_pagoda', 'market_pavilion', 'loom_house',
                                                    'lantern_spire', 'nest_house_large', 'nest_house', 'rim_house', 'twin_nest',
                                                    'nest_house', 'nest_house', 'chime_arch', 'koi_pond'],
                          gap=(6, 10), tiers=(-3, 0, 3, 5, 8), dock=True, extra_islets=(4, (4, 8)), koi=4), 23),
    'village_c': (Program('village', 'veil_court', CORE + ['twin_nest', 'nest_house_large', 'nest_house', 'rim_house', 'koi_pond'],
                          gap=(5, 8), tiers=(-6, -2, 0, 3, 6), dock=True, extra_islets=(5, (3, 7)), koi=5), 37),
    # wild sky islets
    'islet_a': (Program('islet', extra_islets=(1, (4, 6)), trees=0.03), 101),
    'islet_b': (Program('islet', buildings=['koi_pond'], extra_islets=(2, (3, 6)), trees=0.025, koi=5), 113),
    'islet_c': (Program('islet', extra_islets=(0, (4, 6)), trees=0.04), 127),
    'islet_d': (Program('islet', buildings=['harp_stand'], extra_islets=(2, (4, 7)), trees=0.03), 131),
    'islet_e': (Program('islet', extra_islets=(3, (3, 5)), trees=0.02), 149),
    # lone wild structures
    'wind_shrine_a': (Program('wind_shrine', 'wind_shrine', extra_islets=(2, (3, 5)), trees=0.02), 211),
    'ruined_belltower_a': (Program('ruined_belltower', 'ruined_belltower', extra_islets=(2, (3, 5)), trees=0.015, ruin=True), 223),
}

# kind -> (structure id, altitude of the floor [min, max], clearance over the terrain below the islands)
KINDS = {
    'sky_village': (['village_a', 'village_b', 'village_c'], (206, 234), 30),
    'sky_islet': (['islet_a', 'islet_b', 'islet_c', 'islet_d', 'islet_e'], (170, 246), 18),
    'wind_shrine': (['wind_shrine_a'], (184, 240), 22),
    'ruined_belltower': (['ruined_belltower_a'], (178, 236), 22),
}


def build_layout(name):
    program, seed = LAYOUTS[name]
    return plan(name, program, seed)


def bounds(canvas):
    ys = [y for (x, y, z) in canvas.grid]
    return min(ys), max(ys)


def layout_pos(lay, pos):
    return [int(pos[0]), int(pos[1]), int(pos[2])]


def write_layout(lay, seed):
    """Cut the canvas into tiles and return the layout record for the structure JSON."""
    c = lay.canvas
    folder = DATA / 'structure' / lay.name
    if folder.exists():
        shutil.rmtree(folder)
    lo, hi = bounds(c)
    tiles = []
    for tz in range(0, c.d, TILE):
        for tx in range(0, c.w, TILE):
            path = folder / f'{tx // TILE}_{tz // TILE}.nbt'
            n = c.save_nbt(path, tx, tz, min(tx + TILE, c.w), min(tz + TILE, c.d), lo, hi + 1)
            if n == 0:
                path.unlink()
                continue
            tiles.append({'template': f'skyfriends:{lay.name}/{tx // TILE}_{tz // TILE}', 'offset': [tx, lo - Y0, tz]})
    record = {'name': lay.name, 'kind': lay.program.kind, 'width': c.w, 'depth': c.d, 'min_y': lo - Y0, 'max_y': hi - Y0,
              'center_x': lay.ox, 'center_z': lay.oz, 'tiles': tiles, 'centre': lay.centre()}
    people = roster(lay, seed)
    if people:
        record['residents'] = [{k: v for k, v in r.items() if v is not None} for r in people]
    if lay.lift:
        record['lift'] = lay.lift
    return record


def write_json(path, value, indent=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=indent) + '\n', encoding='utf-8')


def preview(lay):
    data = look.export(lay.canvas)
    data['center'] = [lay.ox, Y0, lay.oz]
    data['name'] = lay.name
    out = HERE / 'out' / f'{lay.name}.json'
    write_json(out, data, indent=None)
    return out


def worldgen(records):
    for kind, (names, (lo, hi), clearance) in KINDS.items():
        layouts = [records[n] for n in names if n in records]
        if not layouts:
            continue
        write_json(DATA / 'worldgen' / 'structure' / f'{kind}.json', {
            'type': 'skyfriends:sky_structure', 'biomes': f'#skyfriends:has_structure/{kind}', 'step': 'surface_structures',
            'spawn_overrides': {}, 'terrain_adaptation': 'none',
            'altitude': {'min_floor': lo, 'max_floor': hi, 'clearance': clearance}, 'layouts': layouts}, indent=None)
        write_json(DATA / 'tags' / 'worldgen' / 'biome' / 'has_structure' / f'{kind}.json', {'values': ['#minecraft:is_overworld']})
        write_json(DATA / 'tags' / 'worldgen' / 'structure' / f'{kind}.json', {'values': [f'skyfriends:{kind}']})
    sets = {
        'sky_villages': ('sky_village', 44, 16, 1830216513, None),
        'sky_islets': ('sky_islet', 13, 4, 1027741935, ('skyfriends:sky_villages', 3)),
        'wind_shrines': ('wind_shrine', 36, 12, 734019287, ('skyfriends:sky_villages', 4)),
        'ruined_belltowers': ('ruined_belltower', 40, 14, 588102774, ('skyfriends:sky_villages', 4)),
    }
    for name, (kind, spacing, separation, salt, exclude) in sets.items():
        placement = {'type': 'minecraft:random_spread', 'spacing': spacing, 'separation': separation, 'salt': salt}
        if exclude:
            placement['exclusion_zone'] = {'other_set': exclude[0], 'chunk_count': exclude[1]}
        write_json(DATA / 'worldgen' / 'structure_set' / f'{name}.json',
                   {'structures': [{'structure': f'skyfriends:{kind}', 'weight': 1}], 'placement': placement})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*')
    ap.add_argument('--preview', action='store_true')
    args = ap.parse_args()
    kit.load_all()
    names = args.names or list(LAYOUTS)
    records_path = HERE / 'out' / 'records.json'
    records = json.loads(records_path.read_text()) if records_path.exists() and args.names else {}
    for name in names:
        lay = build_layout(name)
        records[name] = write_layout(lay, LAYOUTS[name][1])
        r = records[name]
        people = r.get('residents', [])
        cirri = [p for p in people if p['type'] == 'cirri']
        print(f'{name:20s} {r["width"]}x{r["max_y"] - r["min_y"] + 1}x{r["depth"]}  {len(r["tiles"])} tiles  {len(lay.plots)} buildings  '
              f'{len(cirri)} Cirri ({sum(1 for p in cirri if p["child"])} children, {sum(1 for p in cirri if p.get("job"))} working)  '
              f'{len(people) - len(cirri)} koi  {len(lay.paths)} paths' + ('  lift' if lay.lift else ''))
        if args.preview:
            preview(lay)
    write_json(records_path, records, indent=None)
    worldgen(records)


if __name__ == '__main__':
    main()
