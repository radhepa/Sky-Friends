"""Every block and item Sky Friends adds, in one list.

The asset generator (gen_blocks.py) writes their blockstates, models, item definitions, loot, tags,
recipes and names from it; the building kit accepts these ids; the Java registries (SkyBlocks,
SkyItems) follow it by hand, and the game test checks the two agree.

Shapes:
  cube        a full block, one texture             pillar   a column (texture <id> sides, <id>_top ends)
  log         like a vanilla log (<id>, <id>_top)    wood     bark on all six faces (base = its log)
  stairs / slab / wall / fence / fence_gate          made from ``base`` (its texture and recipe)
  leaves      not biome-tinted                      sapling  a cross plant that grows a skywood tree
  carpet      made from ``base`` cloth              custom   hand-made model (see gen_blocks.CUSTOM)
"""

# id -> spec. ``material`` sets sound, hardness and the tool tag: stone, wood, cloth, cloud, plant, metal.
BLOCKS = {
    # -- skystone: the pale stone of the floating isles ---------------------------------------
    'skystone': dict(shape='cube', material='stone', name='Skystone'),
    'skystone_stairs': dict(shape='stairs', base='skystone', name='Skystone Stairs'),
    'skystone_slab': dict(shape='slab', base='skystone', name='Skystone Slab'),
    'skystone_bricks': dict(shape='cube', material='stone', name='Skystone Bricks', made_from='skystone'),
    'skystone_brick_stairs': dict(shape='stairs', base='skystone_bricks', name='Skystone Brick Stairs'),
    'skystone_brick_slab': dict(shape='slab', base='skystone_bricks', name='Skystone Brick Slab'),
    'skystone_brick_wall': dict(shape='wall', base='skystone_bricks', name='Skystone Brick Wall'),
    'polished_skystone': dict(shape='cube', material='stone', name='Polished Skystone', made_from='skystone'),
    'polished_skystone_stairs': dict(shape='stairs', base='polished_skystone', name='Polished Skystone Stairs'),
    'polished_skystone_slab': dict(shape='slab', base='polished_skystone', name='Polished Skystone Slab'),
    'gilded_skystone': dict(shape='cube', material='stone', name='Gilded Skystone'),
    'skystone_pillar': dict(shape='pillar', material='stone', name='Skystone Pillar', made_from='skystone'),
    # -- cloud: soft, and you never take fall damage landing on it ------------------------------
    'cloud_block': dict(shape='cube', material='cloud', name='Cloud'),
    # -- skywood: the pale trees of the isles -----------------------------------------------------
    'skywood_log': dict(shape='log', material='wood', name='Skywood Log'),
    'skywood': dict(shape='wood', base='skywood_log', material='wood', name='Skywood'),
    'skywood_planks': dict(shape='cube', material='wood', name='Skywood Planks'),
    'skywood_stairs': dict(shape='stairs', base='skywood_planks', name='Skywood Stairs'),
    'skywood_slab': dict(shape='slab', base='skywood_planks', name='Skywood Slab'),
    'skywood_fence': dict(shape='fence', base='skywood_planks', name='Skywood Fence'),
    'skywood_fence_gate': dict(shape='fence_gate', base='skywood_planks', name='Skywood Fence Gate'),
    'skywood_leaves': dict(shape='leaves', material='plant', name='Skywood Leaves'),
    'skywood_sapling': dict(shape='sapling', material='plant', name='Skywood Sapling'),
    # -- veilcloth: cloth woven from cirrus -------------------------------------------------------
    'white_veilcloth': dict(shape='cube', material='cloth', name='White Veilcloth'),
    'sky_veilcloth': dict(shape='cube', material='cloth', name='Sky Veilcloth'),
    'rose_veilcloth': dict(shape='cube', material='cloth', name='Rose Veilcloth'),
    'white_veilcloth_carpet': dict(shape='carpet', base='white_veilcloth', name='White Veilcloth Carpet'),
    'sky_veilcloth_carpet': dict(shape='carpet', base='sky_veilcloth', name='Sky Veilcloth Carpet'),
    'rose_veilcloth_carpet': dict(shape='carpet', base='rose_veilcloth', name='Rose Veilcloth Carpet'),
    # -- the Cirri's things -------------------------------------------------------------------------
    'wind_chime': dict(shape='custom', material='metal', name='Wind Chime'),
    'wind_harp': dict(shape='custom', material='wood', name='Wind Harp'),
    'sky_lantern': dict(shape='custom', material='metal', name='Sky Lantern'),
    'wind_stone': dict(shape='custom', material='stone', name='Wind Stone'),
}

# Plain items (block items come with their blocks). id -> display name.
ITEMS = {
    'sky_scale': 'Sky Scale',
    'sky_peach': 'Sky Peach',
    'windsong_flute': 'Windsong Flute',
    'cirrus_veil': 'Cirrus Veil',
}

# Every texture a block needs (block/<name>.png), for the texture painter and the checker.
def block_textures():
    out = []
    for bid, spec in BLOCKS.items():
        shape = spec['shape']
        if shape in ('cube', 'leaves', 'sapling'):
            out.append(bid)
        elif shape in ('pillar', 'log'):
            out += [bid, bid + '_top']
    out += ['wind_chime', 'wind_harp', 'sky_lantern', 'wind_stone', 'wind_stone_top']
    return sorted(set(out))


def item_textures():
    return sorted(list(ITEMS) + ['wind_chime', 'sky_lantern'])


def ids():
    return set(BLOCKS)


if __name__ == '__main__':
    print(len(BLOCKS), 'blocks;', len(ITEMS), 'items')
    print('block textures:', ', '.join(block_textures()))
    print('item textures:', ', '.join(item_textures()))
