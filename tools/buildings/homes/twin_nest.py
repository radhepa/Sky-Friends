"""The twin nest: two round nests joined by a shared terrace, for two couples (or one big family).

Two calcite drums, each with a living room below and a nest room for two above, stand either side of a
narrow entrance passage. Over the passage and the open porches before and behind it lies the shared
terrace, railed and lit, with a striped veilcloth awning across its front on skywood posts; both nest rooms
open onto it through arched doorways, and a ladder climbs to it from the passage."""
from kit import building
from homes.style import (BRICKS, POLISHED, GILDED, PILLAR, P_STAIRS, PLANKS, FENCE, GLASS, CARPET, CLOTH,
                         circle, rim, inside, put, column, roof_ring, lantern, chime, nest, clear_mask,
                         round_window)


def drum(b, cx, outer, cloth_a, cloth_b, room):
    """One nest drum centred on (cx, 4); ``outer`` is -1 (its outside faces west) or +1 (east)."""
    g = b.ground
    cz = 4
    c7, c5 = circle(cx, cz, 3.4), circle(cx, cz, 2.4)
    e7, e5 = rim(c7), rim(c5)
    inner_x = cx - 3 * outer                  # the flat facing the terrace
    out_x = cx + 3 * outer
    clear_mask(b, c7, g + 1, g + 9)
    put(b, e7, g, BRICKS)
    put(b, c5, g, POLISHED)
    b.set(cx, g, cz, GILDED)
    for y in range(g + 1, g + 8):
        put(b, e7, y, 'calcite')
    for (x, z) in ((cx - 2, 2), (cx + 2, 2), (cx - 2, 6), (cx + 2, 6)):
        column(b, x, g + 1, g + 3, z)
    # floor between the storeys, gilded points
    put(b, e7, g + 4, POLISHED)
    put(b, c5, g + 4, PLANKS)
    for (x, z) in ((cx, 1), (cx, 7), (out_x, 4)):
        b.set(x, g + 4, z, GILDED)
    # windows: round ones on the outer flat, small ones front and back below, round ones above
    round_window(b, out_x, g + 2, cz, 'z')
    round_window(b, out_x, g + 6, cz, 'z')
    for z in (1, 7):
        b.set(cx, g + 2, z, GLASS)
        round_window(b, cx, g + 6, z, 'x')
    # arched openings to the passage (below) and to the terrace (above)
    for y in (g + 1, g + 2, g + 5, g + 6):
        b.set(inner_x, y, cz, 'air')
    b.set(inner_x, g + 3, cz, GILDED)
    b.set(inner_x, g + 7, cz, GILDED)
    # dome: eave stairs, a drum ring, upper stairs, gilded crown, lantern finial
    roof_ring(b, e7, g + 8, cx, cz)
    put(b, e5, g + 8, GILDED)
    roof_ring(b, e5, g + 9, cx, cz)
    put(b, inside(c5), g + 9, GILDED)
    lantern(b, cx, g + 10, cz)
    # nest room: two nests, a shelf, flowers, a chime and a lantern
    nest(b, cx, g + 5, 2, cloth=cloth_a)
    nest(b, cx, g + 5, 6, cloth=cloth_b)
    b.set(out_x - outer, g + 5, cz, 'chiseled_bookshelf', facing='east' if outer < 0 else 'west')
    b.set(out_x - outer, g + 6, cz, 'potted_azure_bluet')
    lantern(b, cx, g + 8, cz, hanging=True)
    chime(b, cx + outer, g + 7, 2)
    # living room below
    room(b, cx, outer)
    lantern(b, cx, g + 3, cz, hanging=True)


def west_room(b, cx, outer):
    g = b.ground
    b.set(cx - 2, g + 1, 3, 'chiseled_bookshelf', facing='east')
    b.set(cx - 2, g + 1, 5, 'chiseled_bookshelf', facing='east')
    b.set(cx - 2, g + 1, 4, CLOTH['sky'])
    b.set(cx - 1, g + 1, 4, CARPET['white'])
    b.set(cx, g + 1, 2, 'potted_white_tulip')
    b.set(cx, g + 1, 6, 'loom', facing='north')


def east_room(b, cx, outer):
    g = b.ground
    b.set(cx + 2, g + 1, 4, 'skyfriends:wind_harp', facing='west')
    b.set(cx + 2, g + 1, 3, CLOTH['rose'])
    b.set(cx + 2, g + 1, 5, CLOTH['white'])
    b.set(cx + 1, g + 1, 4, CARPET['rose'])
    b.set(cx, g + 1, 2, 'potted_flowering_azalea_bush')
    b.set(cx, g + 1, 6, 'barrel', facing='up', open='false')
    b.set(cx - 1, g + 1, 6, 'potted_allium')


@building('twin_nest', 'cirri', 'home', (15, 11, 9), residents=4, door=7,
          about='Two round Cirri nests joined by a shared railed terrace with a striped veilcloth awning.')
def twin_nest(b):
    g = b.ground
    a, c = circle(3, 4, 3.4), circle(11, 4, 3.4)
    deck = {(x, z) for x in range(4, 11) for z in range(9)} - a - c      # the shared terrace

    clear_mask(b, deck, g + 1, g + 9)
    drum(b, 3, -1, 'rose', 'sky', west_room)
    drum(b, 11, +1, 'sky', 'rose', east_room)

    # -- ground: porches front and back, the passage between them
    put(b, deck, g, BRICKS)
    for z in range(0, 9):
        b.set(7, g, z, POLISHED)
    for (x, z) in ((6, 2), (8, 2), (6, 6), (8, 6), (7, 6)):
        for y in range(g + 1, g + 4):
            b.set(x, y, z, 'calcite')
    b.door(7, g + 1, 2, 'north', 'cherry')
    b.set(7, g + 3, 2, GILDED)
    for y in range(g + 1, g + 5):                  # ladder up to the terrace
        b.set(7, y, 5, 'ladder', facing='north', waterlogged='false')
    lantern(b, 7, g + 3, 3, hanging=True)
    # pillars at the porch corners carry the terrace
    for (x, z) in ((4, 0), (10, 0), (4, 8), (10, 8)):
        column(b, x, g + 1, g + 3, z)
    # -- the terrace floor, its railing, posts, awning and lights
    put(b, deck, g + 4, POLISHED)
    b.set(7, g + 4, 5, 'ladder', facing='north', waterlogged='false')
    for (x, z) in ((7, 3), (7, 4)):
        b.set(x, g + 4, z, GILDED)
    edge = {(x, z) for (x, z) in deck if z in (0, 8)}
    for (x, z) in edge:
        b.set(x, g + 5, z, FENCE)
    for (x, z) in ((4, 0), (10, 0)):            # awning posts
        for y in (g + 5, g + 6, g + 7):
            b.set(x, y, z, FENCE)
    for (x, z) in deck:
        if z <= 1:
            b.set(x, g + 8, z, CLOTH['sky'] if x % 2 else CLOTH['white'])
    chime(b, 6, g + 7, 0)
    chime(b, 8, g + 7, 0)
    lantern(b, 7, g + 7, 1, hanging=True)
    for (x, z) in ((4, 8), (10, 8)):
        lantern(b, x, g + 6, z)
    # under the terrace's front edge: chimes over the porch, lanterns by the door
    chime(b, 5, g + 3, 0)
    chime(b, 9, g + 3, 0)
    lantern(b, 6, g + 1, 1)
    lantern(b, 8, g + 1, 1)
    # cushions and flowers on the terrace
    b.set(6, g + 5, 7, CLOTH['rose'])
    b.set(8, g + 5, 7, CLOTH['sky'])
    b.set(7, g + 5, 7, 'potted_flowering_azalea_bush')
    b.spot('sit', 6, g + 6, 7)
    b.spot('sit', 8, g + 6, 7)
    b.set(5, g + 5, 1, 'potted_azure_bluet')
    b.set(9, g + 5, 1, 'potted_pink_tulip')
