"""The Market Pavilion: an open trading tent of striped veilcloth over a skywood counter."""
from kit import building
from civic.cirri_parts import (BRICKS, FENCE, GILDED, LOOT, PILLAR, PLANKS, POLISHED, ROSE, SKY, SKY_CARPET, WHITE,
                               WOOD, WOOD_SLAB, check, lamp, slab)

W, D = 11, 9
PROFILE = (4, 5, 6, 6, 7, 6, 6, 5, 4)      # the tent's height at each z, eaves to ridge to eaves
STRIPES = (ROSE, WHITE, SKY, WHITE)       # rose and sky stripes on white, along x


@building('market_pavilion', 'cirri', 'work', (W, 9, D), door=5, residents=0, job='skymerchant',
          about='An open trading pavilion: a tent of rose, white and sky veilcloth stripes on skystone posts, a skywood '
                'counter set with flowers and wares, barrels and crates behind, lanterns under the ridge.')
def market_pavilion(b):
    b.fill(0, 0, 0, W - 1, 0, D - 1, POLISHED)
    for x in range(W):
        for z in range(D):
            if x in (0, W - 1) or z in (0, D - 1):
                b.set(x, 0, z, BRICKS)
    b.set(5, 0, 0, POLISHED)

    # ---- posts: skystone pillars at the corners, tall skywood tent poles under the ridge ends
    for x, z in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
        for y in range(1, PROFILE[z]):
            b.set(x, y, z, PILLAR)
        b.set(x, PROFILE[z] - 1, z, GILDED)
    for x in (0, W - 1):
        for y in range(1, PROFILE[4]):
            b.set(x, y, 4, FENCE)

    # ---- the striped tent with a scalloped valance front and back
    for x in range(W):
        cloth = STRIPES[x % 4]
        for z in range(D):
            b.set(x, PROFILE[z], z, cloth)
            # close the riser down to the lower neighbour, so the canopy is one unbroken sheet
            low = min(PROFILE[max(z - 1, 0)], PROFILE[min(z + 1, D - 1)])
            for y in range(low, PROFILE[z]):
                b.set(x, y, z, cloth)
        if x % 2 == 0 and 0 < x < W - 1:
            b.set(x, PROFILE[0] - 1, 0, cloth)
            b.set(x, PROFILE[-1] - 1, D - 1, cloth)
    for x in (1, 5, 9):
        lamp(b, x, PROFILE[4] + 1, 4)             # lanterns along the ridge
        lamp(b, x, PROFILE[4] - 2, 4, hanging=True)

    # ---- the counter: skywood with a polished top, wares and flowers on it
    for x in range(2, 9):
        b.set(x, 1, 3, PLANKS if x % 2 else WOOD)
    for x in (2, 8):
        b.set(x, 1, 4, PLANKS)
    wares = {2: 'potted_pink_tulip', 3: ('white_candle', 3), 4: 'decorated_pot', 6: 'potted_azure_bluet',
             7: ('pink_candle', 2), 8: 'potted_allium'}
    for x, thing in wares.items():
        if isinstance(thing, tuple):
            b.candles(x, 2, 3, thing[1], thing[0][:-len('_candle')])
        elif thing == 'decorated_pot':
            b.set(x, 2, 3, 'decorated_pot', facing='north', cracked=False, waterlogged=False)
        else:
            b.set(x, 2, 3, thing)
    b.set(5, 2, 3, SKY_CARPET)                     # a bolt of sky cloth laid out on the counter
    b.spot('work', 5, 1, 5)

    # ---- stock behind: barrels, crates of skywood, a chest, bolts of veilcloth
    for x, z, stack in ((1, 7, 2), (2, 7, 1), (9, 7, 2), (8, 7, 1), (1, 6, 1)):
        for k in range(stack):
            b.set(x, 1 + k, z, 'barrel', facing='up' if k == stack - 1 else 'north', open=False)
    for x, z in ((3, 7), (7, 7)):
        b.set(x, 1, z, PLANKS)
        slab(b, x, 2, z, WOOD_SLAB)
    for x in (1, 9):
        lamp(b, x, 3, 7)                           # lanterns on the barrel stacks
    b.chest(5, 1, 7, 'north', loot=LOOT)
    b.set(4, 1, 7, WHITE)
    b.set(6, 1, 7, ROSE)
    b.set(6, 2, 7, SKY)
    b.set(9, 1, 6, 'potted_lily_of_the_valley')
    # flowers by the front posts
    b.set(1, 1, 0, 'potted_azure_bluet')
    b.set(W - 2, 1, 0, 'potted_pink_tulip')
    check(b)
