"""The Wind Shrine: a small open Cirri shrine standing alone on a wild islet.

Four skystone pillars with gilded capitals carry a two-tier roof: a wide eave that floats out on every side,
hung with wind chimes, then a short white drum under a second eave and a gilded crown. Under it, a wind harp plays on a gilded dais ringed with candles; flowers in pots, a
sky lantern under the vault and another as the finial; a chest of Cirri goods at the back."""
from kit import building
from homes.style import (STONE, BRICKS, POLISHED, GILDED, PILLAR, P_STAIRS, P_SLAB, B_SLAB, B_STAIRS, CLOTH,
                         CARPET, octagon, rim, inside, put, column, roof_ring, lantern, chime, clear_mask)

C = 4


@building('wind_shrine', 'cirri', 'wild', (9, 10, 9), door=4,
          about='A small open shrine on a lone islet: four pillars, a floating two-tier roof, a wind harp, chimes and a chest.')
def wind_shrine(b):
    t0 = octagon(0, 0, 8, 8, 2)
    tiers = [t0]
    while len(tiers[-1]) > 1:
        tiers.append(inside(tiers[-1]))
    t1, t2, t3 = tiers[1], tiers[2], tiers[3]          # 7 wide, 5x5, 3x3

    clear_mask(b, t0, 1, 9)
    # -- platform: a brick border, polished paving, a gilded star at the centre
    put(b, rim(t0), 0, BRICKS)
    put(b, inside(t0), 0, POLISHED)
    for (x, z) in ((4, 2), (4, 6), (2, 4), (6, 4)):
        b.set(x, 0, z, GILDED)

    # -- the four pillars on low plinths, gilded capitals
    for (x, z) in ((2, 2), (6, 2), (2, 6), (6, 6)):
        column(b, x, 1, 4, z)
        b.set(x, 5, z, GILDED)

    # -- the dais and the harp
    b.set(C, 1, C, GILDED)
    for (x, z) in ((3, 4), (5, 4), (4, 3), (4, 5)):
        b.set(x, 1, z, P_SLAB, type='bottom')
    b.set(C, 2, C, 'skyfriends:wind_harp', facing='north')
    for (x, z) in ((3, 3), (5, 3), (3, 5), (5, 5)):
        b.candles(x, 1, z, 3 if (x + z) % 4 else 2, 'white')
    # flowers at the pillar feet, cushions to kneel on before the harp
    b.set(1, 1, 4, 'potted_azure_bluet')
    b.set(7, 1, 4, 'potted_lily_of_the_valley')
    b.set(4, 1, 1, CARPET['sky'])
    b.set(3, 1, 1, CARPET['white'])
    b.set(5, 1, 1, CARPET['white'])
    # the chest of Cirri goods at the back
    b.chest(4, 1, 7, 'north', loot='skyfriends:chests/wind_shrine')
    b.set(3, 1, 7, 'potted_flowering_azalea_bush')
    b.set(5, 1, 7, 'potted_allium')

    # -- the roof: a wide floating eave, a short white drum, a second eave, a gilded crown
    roof_ring(b, rim(t0), 5, C, C)
    put(b, rim(t1), 5, GILDED)
    put(b, rim(t2), 5, POLISHED)
    for (x, z) in ((2, 2), (6, 2), (2, 6), (6, 6)):
        b.set(x, 5, z, GILDED)
        b.set(x, 6, z, PILLAR, axis='y')
    for (x, z) in rim(t2):
        if not b.solid(x, 6, z):
            b.set(x, 6, z, 'calcite')
    roof_ring(b, rim(t1), 7, C, C)
    put(b, rim(t2), 7, GILDED)
    roof_ring(b, rim(t2), 8, C, C)
    put(b, t3, 8, POLISHED)
    b.set(C, 8, C, GILDED)
    lantern(b, C, 9, C)
    lantern(b, C, 7, C, hanging=True)
    # chimes all round under the lower eave
    for (x, z) in ((3, 1), (5, 1), (1, 3), (1, 5), (7, 3), (7, 5), (3, 7), (5, 7)):
        chime(b, x, 4, z)
