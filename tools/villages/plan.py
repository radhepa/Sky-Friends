"""Plans sky villages and the wild sky structures: floating islands, buildings, bridges and gardens.

A plan is made from a ``Program`` (which buildings, how spread out, how high the islets sit) and a
seed, so every layout is fixed and reproducible. The result is a ``Layout``: one ``kit.Build`` canvas
in layout space (y = 0 is the village floor, the court's surface) holding everything, islands
included (in the sky nothing else is there to meet them), plus the residents' spots and the lift.

Sky villages: the Veil Court on a central island; the Lift Dock on its rim with its shaft open to the
ground; every other building on its own islet round the court at its own height, its door toward the
court; skywood bridges with rails and sky lanterns joining them (the Cirri fly; the bridges are for
guests). Islands: grass, dirt, skystone, tapering to a rough point, hanging roots and clinging cloud.

    python tools/villages/plan.py village_a          plan one layout and print what it holds
"""
import heapq
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'buildings'))
import kit  # noqa: E402

FRONT = ['north', 'east', 'south', 'west']       # a building's front after 0..3 quarter turns
STEP = {'north': (0, -1), 'east': (1, 0), 'south': (0, 1), 'west': (-1, 0)}
Y0 = 40           # layout y = 0 sits at canvas layer Y0 (room for the islands' undersides)
HEIGHT = 96       # canvas height

SKY = 'skyfriends:'
PATH, EDGE, STAIRS = SKY + 'polished_skystone', SKY + 'skystone_bricks', SKY + 'skystone_brick_stairs'
DECK, DECK_STAIRS, RAIL = SKY + 'skywood_planks', SKY + 'skywood_stairs', SKY + 'skywood_fence'
FLOWERS = ['azure_bluet', 'oxeye_daisy', 'lily_of_the_valley', 'white_tulip', 'pink_tulip', 'cornflower', 'allium']


@dataclass
class Program:
    """What a layout is made of. ``plaza``: the centre building (None for a bare wild islet).
    ``buildings``: names round it, in placement order. ``gap``: (min, max) blocks of open sky between
    neighbouring islets. ``tiers``: islet tops a building may sit at, relative to the court.
    ``dock``: put the Lift Dock on the central island's rim. ``extra_islets``: (count, radius range)
    of bare wild islets scattered round the layout. ``ruin``: break the islands up."""
    kind: str
    plaza: str = None
    buildings: list = field(default_factory=list)
    gap: tuple = (6, 10)
    tiers: tuple = (0,)
    dock: bool = False
    extra_islets: tuple = (0, (4, 7))
    trees: float = 0.012
    ruin: bool = False
    koi: int = 0            # Cloud Koi released at each 'koi' spot


@dataclass
class Plot:
    name: str
    build: object          # the finished, turned kit.Build
    x: int                 # min corner in layout space
    z: int
    top: int               # islet top (layout y of the building's ground layer)
    turns: int
    spec: dict

    @property
    def w(self):
        return self.build.w

    @property
    def d(self):
        return self.build.d

    def rect(self, pad=0):
        return (self.x - pad, self.z - pad, self.x + self.w - 1 + pad, self.z + self.d - 1 + pad)

    def center(self):
        return (self.x + (self.w - 1) / 2, self.z + (self.d - 1) / 2)

    def door_cell(self):
        """The layout cell just outside the entrance (where the path starts)."""
        lx, lz = self.spec['door'], -1
        w0, d0 = self.spec['size'][0], self.spec['size'][2]
        for _ in range(self.turns):
            lx, lz, w0, d0 = d0 - 1 - lz, lx, d0, w0
        return self.x + lx, self.z + lz

    def spots(self):
        """The building's spots in layout space."""
        out = []
        for s in self.build.meta.get('spots', []):
            x, y, z = s['pos']
            out.append({'kind': s['kind'], 'pos': [self.x + x, self.top - self.build.ground + y, self.z + z]})
        return out


def overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


@dataclass
class Islet:
    cx: float
    cz: float
    rx: float
    rz: float
    top: int
    depth: float           # underside depth at the centre


class Layout:
    def __init__(self, name, program, seed):
        self.name, self.program, self.rng = name, program, random.Random(seed)
        self.plots, self.islets, self.paths = [], [], []
        self.ground = {}   # (x, z) -> [top, depth]
        self.path_y = {}
        self.decor = []
        self.dock = None
        self.lift = None
        self.canvas = None
        self.koi = []      # layout positions where Cloud Koi are released

    # ------------------------------------------------------------- placing
    def make(self, name, turns):
        return kit.make(name).turned(turns)

    def place_plaza(self):
        p = self.program
        if p.plaza:
            b = self.make(p.plaza, 0)
            plot = Plot(p.plaza, b, -(b.w // 2), -(b.d // 2), 0, 0, kit.CATALOG[p.plaza])
            self.plots.append(plot)
            r = max(plot.w, plot.d) / 2 + 5
        else:
            r = self.rng.uniform(5, 9)
        self.islets.append(Islet(0, 0, r, r * self.rng.uniform(0.85, 1.15), 0, 7 + r * 1.2))
        return r

    def place_dock(self, radius):
        """The Lift Dock on the central island's rim: its front toward the court, its back (and the lift
        shaft) out over the open sky."""
        spec = kit.CATALOG['lift_dock']
        angle = self.rng.uniform(0, 2 * math.pi)
        dx, dz = math.cos(angle), math.sin(angle)
        if abs(dx) > abs(dz):
            turns, dx, dz = (3, 1, 0) if dx > 0 else (1, -1, 0)
        else:
            turns, dx, dz = (0, 0, 1) if dz > 0 else (2, 0, -1)
        w, d = (spec['size'][0], spec['size'][2]) if turns % 2 == 0 else (spec['size'][2], spec['size'][0])
        along = d if turns % 2 == 0 else w
        r = radius + along / 2 - 5          # the front five cells stand on the island
        cx, cz = dx * r, dz * r
        x, z = round(cx - (w - 1) / 2), round(cz - (d - 1) / 2)
        b = self.make('lift_dock', turns)
        plot = Plot('lift_dock', b, x, z, 0, turns, spec)
        self.plots.append(plot)
        self.dock = plot
        shaft = next(s['pos'] for s in plot.spots() if s['kind'] == 'lift')
        toward = STEP[FRONT[turns]]          # from the shaft toward the dock's front (the court)
        landing = [shaft[0] + toward[0] * 3, shaft[1], shaft[2] + toward[1] * 3]
        self.lift = {'shaft': shaft, 'landing': landing}

    def place(self, name, angle, tiers):
        """Put a building on the ray at ``angle`` from the centre, as close as it fits, door toward the centre."""
        spec = kit.CATALOG[name]
        p = self.program
        gap_lo, gap_hi = p.gap
        rng = self.rng
        best = None
        for wiggle in (0, 0.12, -0.12, 0.25, -0.25, 0.4, -0.4, 0.6, -0.6, 0.9, -0.9):
            a = angle + wiggle
            dx, dz = math.cos(a), math.sin(a)
            if abs(dx) > abs(dz):
                turns = 3 if dx > 0 else 1
            else:
                turns = 0 if dz > 0 else 2
            w, d = (spec['size'][0], spec['size'][2]) if turns % 2 == 0 else (spec['size'][2], spec['size'][0])
            gap = rng.randint(gap_lo, gap_hi)
            for r in range(8, 160):
                cx, cz = dx * r, dz * r
                x, z = round(cx - (w - 1) / 2), round(cz - (d - 1) / 2)
                rect = (x, z, x + w - 1, z + d - 1)
                pad = gap + 5
                if any(overlap((rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad), o.rect()) for o in self.plots):
                    continue
                if best is None or r < best[0]:
                    best = (r, x, z, turns)
                break
        r, x, z, turns = best
        top = max(tiers) if spec.get('job') in ('lamplighter', 'bellkeeper') else rng.choice(tiers)
        b = self.make(name, turns)
        plot = Plot(name, b, x, z, top, turns, spec)
        self.plots.append(plot)
        cx, cz = plot.center()
        rx, rz = plot.w / 2 + 3.5 + rng.random() * 2, plot.d / 2 + 3.5 + rng.random() * 2
        self.islets.append(Islet(cx, cz, rx, rz, top, 5 + min(rx, rz) * 1.5))
        return plot

    def place_all(self):
        p = self.program
        radius = self.place_plaza()
        if p.dock:
            self.place_dock(radius)
        names = [n for n in p.buildings if n in kit.CATALOG]
        missing = [n for n in p.buildings if n not in kit.CATALOG]
        if missing:
            print(f'  {self.name}: not designed yet, skipped: {", ".join(missing)}')
        start = self.rng.uniform(0, 2 * math.pi)
        n = len(names)
        for i, name in enumerate(names):
            angle = start + 2 * math.pi * i / max(n, 1) + self.rng.uniform(-0.15, 0.15)
            self.place(name, angle, p.tiers)
        count, (rlo, rhi) = p.extra_islets
        for _ in range(count):
            self.wild_islet(rlo, rhi)

    def wild_islet(self, rlo, rhi):
        """A bare islet off to the side, at its own height (trees and flowers grow on it later)."""
        rng = self.rng
        for _ in range(40):
            a, dist = rng.uniform(0, 2 * math.pi), rng.uniform(14, 34 + 4 * len(self.plots))
            r = rng.uniform(rlo, rhi)
            cx, cz = math.cos(a) * dist, math.sin(a) * dist
            rect = (cx - r - 3, cz - r - 3, cx + r + 3, cz + r + 3)
            if any(overlap(rect, o.rect(3)) for o in self.plots):
                continue
            if any(math.hypot(cx - i.cx, cz - i.cz) < r + max(i.rx, i.rz) + 4 for i in self.islets):
                continue
            self.islets.append(Islet(cx, cz, r, r * rng.uniform(0.8, 1.2), rng.randint(-6, 8), 4 + r * 1.3))
            return

    # ------------------------------------------------------------- ground
    def raster(self):
        """Columns of every islet: each column belongs to the islet it is deepest inside."""
        rng = random.Random(self.rng.random())
        cells = {}
        for k, isl in enumerate(self.islets):
            for z in range(math.floor(isl.cz - isl.rz) - 1, math.ceil(isl.cz + isl.rz) + 2):
                for x in range(math.floor(isl.cx - isl.rx) - 1, math.ceil(isl.cx + isl.rx) + 2):
                    e = ((x - isl.cx) / isl.rx) ** 2 + ((z - isl.cz) / isl.rz) ** 2
                    wob = 1 + 0.14 * math.sin(x * 1.7 + z * 0.9 + k) * math.cos(z * 1.3 - x * 0.6)
                    if e <= wob and ((x, z) not in cells or e < cells[(x, z)][0]):
                        cells[(x, z)] = (e, k)
        for (x, z), (e, k) in cells.items():
            isl = self.islets[k]
            # an inverted cone, rough underneath, now and then a hanging spike
            taper = (1 - min(e, 1.0) ** 0.5) ** 0.75
            depth = 1 + isl.depth * taper * (0.8 + 0.4 * rng.random())
            if taper > 0.25 and rng.random() < 0.08:
                depth += rng.randint(2, 7)
            self.ground[(x, z)] = [isl.top, max(1, round(depth))]
        # buildings stand on their own islet's top even where another islet's edge reaches in
        for plot in self.plots:
            if plot is self.dock:
                continue
            x0, z0, x1, z1 = plot.rect()
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    g = self.ground.get((x, z))
                    self.ground[(x, z)] = [plot.top, max(g[1] if g else 0, 4 + plot.top - (g[0] if g else plot.top))]
        # the lift shaft is open all the way down
        if self.lift:
            sx, _, sz = self.lift['shaft']
            for x in range(sx - 2, sx + 3):
                for z in range(sz - 2, sz + 3):
                    self.ground.pop((x, z), None)

    def on_land(self, x, z):
        return (x, z) in self.ground

    def blocked(self, pad=1):
        cells = set()
        for plot in self.plots[1:] if self.program.plaza else self.plots:
            x0, z0, x1, z1 = plot.rect(pad)
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    cells.add((x, z))
        if self.lift:
            sx, _, sz = self.lift['shaft']
            for x in range(sx - 2, sx + 3):
                for z in range(sz - 2, sz + 3):
                    cells.add((x, z))
        return cells

    # ------------------------------------------------------------- paths
    def route(self, start, goal_rect, blocked):
        """A* from start to any cell inside goal_rect or onto an existing path (prefers land and straight runs)."""
        gx0, gz0, gx1, gz1 = goal_rect

        def h(c):
            return max(gx0 - c[0], 0, c[0] - gx1) + max(gz0 - c[1], 0, c[1] - gz1)

        open_ = [(h(start), 0.0, start, None)]
        came_from, cost, seen = {}, {(start, None): 0.0}, set()
        while open_:
            f, g, cell, d = heapq.heappop(open_)
            if (cell, d) in seen:
                continue
            seen.add((cell, d))
            if (gx0 <= cell[0] <= gx1 and gz0 <= cell[1] <= gz1) or (cell in self.path_y and cell != start):
                path, key = [cell], (cell, d)
                while key in came_from:
                    key = came_from[key]
                    path.append(key[0])
                return path[::-1]
            if g > 500:
                continue
            for nd, (dx, dz) in STEP.items():
                n = (cell[0] + dx, cell[1] + dz)
                if n in blocked:
                    continue
                step = 1.0 if self.on_land(*n) else 1.3
                if d is not None and nd != d:
                    step += 0.8
                ng = g + step
                key = (n, nd)
                if ng < cost.get(key, 1e9):
                    cost[key] = ng
                    came_from[key] = (cell, d)
                    heapq.heappush(open_, (ng + h(n), ng, n, nd))
        return None

    def lay_paths(self):
        if not self.program.plaza:
            return
        plaza = self.plots[0]
        goal = plaza.rect(-1)
        for plot in self.plots[1:]:
            if plot.spec.get('role') in ('decor', 'wild'):
                continue
            blocked = self.blocked(1)
            start = plot.door_cell()
            fx, fz = STEP[FRONT[plot.turns]]
            for k in range(0, 3):
                for s in (-1, 0, 1):
                    blocked.discard((start[0] + fx * k + (fz != 0) * s, start[1] + fz * k + (fx != 0) * s))
            for c in list(self.path_y):
                blocked.discard(c)
            path = self.route(start, goal, blocked)
            if path is None:
                print(f'  {self.name}: no path from {plot.name}')
                continue
            self.paths.append((plot, path))
            self.set_heights(plot, path)

    def set_heights(self, plot, path):
        """Deck heights from the door (the plot's islet top) to the end of the path, one step at a time."""
        end = path[-1]
        y_end = self.path_y.get(end, 0)
        y0 = plot.top
        new = [c for c in path if c not in self.path_y]
        m = max(len(new) - 1, 1)
        rise = y_end - y0
        steps = min(abs(rise), m)
        i = 0
        for c in path:
            if c in self.path_y:
                continue
            t = 0 if m <= 4 else max(0.0, min(1.0, (i - 2) / max(m - 4, 1)))
            self.path_y[c] = y0 + round(math.copysign(steps, rise) * t) if rise else y0
            i += 1

    # ------------------------------------------------------------- drawing
    def draw(self):
        xs = [x for x, z in self.ground] + [c[0] for c in self.path_y]
        zs = [z for x, z in self.ground] + [c[1] for c in self.path_y]
        for plot in self.plots:
            x0, z0, x1, z1 = plot.rect()
            xs += [x0, x1]
            zs += [z0, z1]
        self.minx, self.minz = min(xs) - 4, min(zs) - 4
        W, D = max(xs) - self.minx + 5, max(zs) - self.minz + 5
        c = self.canvas = kit.Build(self.name, (W, HEIGHT, D))
        ox, oz = -self.minx, -self.minz
        self.ox, self.oz = ox, oz
        rng = random.Random(self.rng.random())

        # paths first (they may lay bridge decks over open sky and embankments onto islands)
        deck = {}
        for plot, path in self.paths:
            for i, cell in enumerate(path):
                y = self.path_y[cell]
                nxt = path[min(i + 1, len(path) - 1)]
                prv = path[max(i - 1, 0)]
                along = 'x' if abs(nxt[0] - prv[0]) >= abs(nxt[1] - prv[1]) else 'z'
                sides = [(0, 0), (0, -1), (0, 1)] if along == 'x' else [(0, 0), (-1, 0), (1, 0)]
                for k, (sx, sz) in enumerate(sides):
                    cell2 = (cell[0] + sx, cell[1] + sz)
                    if cell2 in deck and deck[cell2][0] >= y and k:
                        continue
                    deck[cell2] = (y, k == 0, cell, along)
        plaza_rect = self.plots[0].rect() if self.program.plaza else (1, 1, 0, 0)
        self.deck = {}
        for (x, z), (y, centre, owner, along) in deck.items():
            if plaza_rect[0] <= x <= plaza_rect[2] and plaza_rect[1] <= z <= plaza_rect[3]:
                continue
            if any(p.x <= x < p.x + p.w and p.z <= z < p.z + p.d for p in self.plots[1:]):
                continue
            land = self.ground.get((x, z))
            bridge = land is None or land[0] < y - 1
            self.deck[(x, z)] = (y, bridge)
            c.set(x + ox, y + Y0, z + oz, DECK if bridge else (PATH if centre else EDGE))
            for k in (1, 2, 3):
                c.set(x + ox, y + Y0 + k, z + oz, 'air')
            if land is not None and land[0] != y and not bridge:
                self.ground[(x, z)] = [y, max(0, y - land[0]) + land[1]]   # an embankment up to the path

        # islands: grass over dirt over skystone, tapering down; roots and cloud underneath
        for (x, z), (top, depth) in self.ground.items():
            if (x, z) in self.deck and self.deck[(x, z)][1]:
                continue
            gx, gz = x + ox, z + oz
            for k in range(depth + 1):
                y = top - k + Y0
                if c.get(gx, y, gz) != kit.AIR and k == 0:
                    continue
                if k == 0:
                    state = 'grass_block'
                elif k <= 2 + (x * 7 + z * 3) % 2:
                    state = 'dirt'
                else:
                    state = SKY + 'skystone'
                if (x, z) in self.deck and k == 0:
                    continue
                c.set(gx, y, gz, state, **({'snowy': 'false'} if state == 'grass_block' else {}))
            bottom = top - depth + Y0
            edge = any((x + dx, z + dz) not in self.ground for dx, dz in STEP.values())
            r = rng.random()
            if not edge and r < 0.09 and bottom - 1 > 0:
                c.set(gx, bottom - 1, gz, 'hanging_roots', waterlogged='false')
            elif edge and r < 0.05:
                self.cloud(gx, bottom - 1 - rng.randint(0, 2), gz, rng)
        # the dock's own deck covers the island under its front: nothing to do. Rails along every bridge
        self.rails = {}
        for (x, z), (y, bridge) in self.deck.items():
            for dx, dz in STEP.values():
                n = (x + dx, z + dz)
                if n in self.deck or n in self.rails:
                    continue
                if any(p.x - 1 <= n[0] <= p.x + p.w and p.z - 1 <= n[1] <= p.z + p.d for p in self.plots):
                    continue
                land = self.ground.get(n)
                if land is not None and land[0] >= y - 1:
                    continue                        # a path across an island needs no rail
                c.set(n[0] + ox, y + Y0, n[1] + oz, DECK)
                c.set(n[0] + ox, y + Y0 + 1, n[1] + oz, RAIL)
                self.rails[n] = y
        # steps where a path's deck rises
        for plot, path in self.paths:
            for i in range(1, len(path)):
                a, b = path[i - 1], path[i]
                ya, yb = self.path_y[a], self.path_y[b]
                if ya == yb:
                    continue
                lo, hi = (a, b) if ya < yb else (b, a)
                y_lo = min(ya, yb)
                facing = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}[(hi[0] - lo[0], hi[1] - lo[1])]
                along = 'x' if hi[0] != lo[0] else 'z'
                for s in (-1, 0, 1):
                    cx_, cz_ = (lo[0], lo[1] + s) if along == 'x' else (lo[0] + s, lo[1])
                    d = self.deck.get((cx_, cz_))
                    if d and d[0] == y_lo:
                        c.set(cx_ + ox, y_lo + 1 + Y0, cz_ + oz, DECK_STAIRS if d[1] else STAIRS, facing=facing, half='bottom',
                              shape='straight', waterlogged='false')
        # buildings
        for plot in self.plots:
            c.paste(plot.build, plot.x + ox, plot.top + Y0 - plot.build.ground, plot.z + oz)
            for s in plot.spots():
                if s['kind'] == 'koi':
                    self.koi.append(s['pos'])
        self.lamps(ox, oz)
        self.planting(ox, oz, rng)
        self.wisps(ox, oz, rng)
        if self.program.ruin:
            self.crumble(ox, oz, rng)

    def cloud(self, gx, gy, gz, rng, r=None):
        """A puff of cloud blocks (only into empty sky)."""
        r = r or rng.uniform(1.2, 2.4)
        c = self.canvas
        for dy in range(-1, 2):
            for dz in range(-3, 4):
                for dx in range(-3, 4):
                    if (dx / r) ** 2 + (dy / (r * 0.6)) ** 2 + (dz / r) ** 2 <= 1 + rng.random() * 0.3:
                        x, y, z = gx + dx, gy + dy, gz + dz
                        if c.inside(x, y, z) and not c.solid(x, y, z):
                            c.set(x, y, z, SKY + 'cloud_block')

    def free(self, x, z):
        if (x, z) in self.deck or (x, z) in self.rails:
            return False
        for p in self.plots:
            x0, z0, x1, z1 = p.rect(1)
            if x0 <= x <= x1 and z0 <= z <= z1:
                return False
        return (x, z) in self.ground

    def lamps(self, ox, oz):
        """Sky lanterns along the paths: on posts beside them on land, on the rails over open sky."""
        c = self.canvas
        placed = []
        for plot, path in self.paths:
            for i in range(3, len(path) - 2, 6):
                cell = path[i]
                y = self.path_y[cell]
                prv, nxt = path[i - 1], path[i + 1]
                along = 'x' if nxt[0] != prv[0] else 'z'
                for s in (2, -2):
                    x, z = (cell[0], cell[1] + s) if along == 'x' else (cell[0] + s, cell[1])
                    if any(abs(x - a) + abs(z - b) < 5 for a, b in placed):
                        continue
                    if self.free(x, z) and self.ground[(x, z)][0] == y:
                        b = kit.make('sky_lamp')
                        c.paste(b, x + ox, y + Y0, z + oz)
                        placed.append((x, z))
                        break
                    if self.rails.get((x, z)) == y:
                        c.set(x + ox, y + Y0 + 2, z + oz, SKY + 'sky_lantern', hanging='false', waterlogged='false')
                        placed.append((x, z))
                        break
        # and a lantern on every lonely stretch of island, so nothing spawns in the dark
        for (x, z), (top, depth) in sorted(self.ground.items()):
            if not self.free(x, z) or (x + z * 3) % 7:
                continue
            if any(abs(x - a) + abs(z - b) < 9 for a, b in placed):
                continue
            if c.solid(x + ox, top + Y0 + 1, z + oz):
                continue
            c.paste(kit.make('sky_lamp'), x + ox, top + Y0, z + oz)
            placed.append((x, z))

    def planting(self, ox, oz, rng):
        """Skywood trees, flowers and grass on the free island surface."""
        c = self.canvas
        for (x, z), (top, depth) in sorted(self.ground.items()):
            if not self.free(x, z) or depth < 2:
                continue
            gx, gy, gz = x + ox, top + Y0, z + oz
            if c.get(gx, gy, gz)[0] != 'minecraft:grass_block' or c.solid(gx, gy + 1, gz):
                continue
            r = rng.random()
            if r < self.program.trees and all(self.free(x + dx, z + dz) for dx in (-2, 0, 2) for dz in (-2, 0, 2)):
                self.tree(gx, gy + 1, gz, rng)
            elif r < 0.09:
                c.set(gx, gy + 1, gz, rng.choice(FLOWERS))
            elif r < 0.22:
                c.set(gx, gy + 1, gz, 'short_grass')

    def tree(self, x, y, z, rng):
        """A small skywood tree: a pale trunk under a round crown of blossom."""
        c = self.canvas
        h = rng.randint(4, 6)
        for k in range(h):
            c.set(x, y + k, z, SKY + 'skywood_log', axis='y')
        r = rng.choice((2, 2, 3))
        cy = y + h - 1
        for dy in range(-1, r + 1):
            for dz in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dz * dz + (dy * 1.4) ** 2 <= r * r + 1 and not c.solid(x + dx, cy + dy, z + dz):
                        if rng.random() < 0.92 and c.inside(x + dx, cy + dy, z + dz):
                            c.set(x + dx, cy + dy, z + dz, SKY + 'skywood_leaves')

    def wisps(self, ox, oz, rng):
        """A few loose puffs of cloud drifting round the islands."""
        c = self.canvas
        for _ in range(max(2, len(self.islets) // 2)):
            for _ in range(20):
                x, z = rng.randrange(4, c.w - 4), rng.randrange(4, c.d - 4)
                y = rng.randint(Y0 - 24, Y0 - 4)
                if (x - ox, z - oz) in self.ground or not c.inside(x, y, z):
                    continue
                self.cloud(x, y, z, rng, rng.uniform(1.8, 3.2))
                break

    def crumble(self, ox, oz, rng):
        """A ruin: bites out of the islands' edges and loose blocks scattered on top."""
        c = self.canvas
        for (x, z), (top, depth) in list(self.ground.items()):
            edge = sum((x + dx, z + dz) not in self.ground for dx, dz in STEP.values())
            if edge and rng.random() < 0.35:
                for k in range(rng.randint(1, 3)):
                    c.set(x + ox, top - k + Y0, z + oz, 'air')
        for (x, z), (top, depth) in list(self.ground.items()):
            if self.free(x, z) and rng.random() < 0.04 and not c.solid(x + ox, top + Y0 + 1, z + oz):
                c.set(x + ox, top + Y0 + 1, z + oz, rng.choice([SKY + 'skystone', SKY + 'skystone_brick_slab', 'mossy_cobblestone', 'moss_carpet']))

    # ------------------------------------------------------------- results
    def finish(self):
        self.canvas.finish()
        return self

    def spots(self):
        return [(p, s) for p in self.plots for s in p.spots()]

    def centre(self):
        """The village centre (the court, a little above its floor) in layout space."""
        return [0, 2, 0]


def plan(name, program, seed):
    lay = Layout(name, program, seed)
    lay.place_all()
    lay.raster()
    lay.lay_paths()
    lay.draw()
    return lay.finish()


if __name__ == '__main__':
    import compile as compiler
    kit.load_all()
    for n in sys.argv[1:]:
        lay = compiler.build_layout(n)
        print(n, lay.canvas.w, lay.canvas.d, len(lay.plots), 'buildings', len(lay.paths), 'paths', 'lift', lay.lift)
