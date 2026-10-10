"""Path furniture the planner scatters through a village: lamps and benches.

(Also the worked example for the kit: a building is a function decorated with ``kit.building`` that
draws into ``b``, a fresh canvas of ``size``; the front faces north, z = 0.)"""
from kit import building


@building('sky_lamp', 'cirri', 'decor', (1, 5, 1), about='A sky lantern on a skywood post.')
def sky_lamp(b):
    b.set(0, 0, 0, 'skyfriends:polished_skystone')            # footing set into the path
    b.set(0, 1, 0, 'skyfriends:skywood_fence')
    b.set(0, 2, 0, 'skyfriends:skywood_fence')
    b.set(0, 3, 0, 'skyfriends:skywood_fence')
    b.set(0, 4, 0, 'skyfriends:sky_lantern', hanging='false', waterlogged='false')


@building('veil_bench', 'cirri', 'decor', (3, 3, 2), about='A skywood bench under a little rose awning.')
def veil_bench(b):
    for x in range(3):
        b.set(x, 1, 1, 'skyfriends:skywood_stairs', facing='south', half='bottom')
    b.set(0, 1, 0, 'flower_pot')
    b.set(2, 1, 0, 'potted_azure_bluet')
    b.spot('sit', 1, 1, 0)
