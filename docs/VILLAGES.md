# Sky villages and sky structures

## What a sky village is

A Cirri village floats high over the land, its floor about y 205-235, so the islands' undersides hang down into
and through the cloud layer (vanilla clouds sit at y 192). From the ground you see floating islands with
dangling roots and wisps of cloud under them, and Cirri soaring round them.

- A **central island** with the **Veil Court** (the plaza) and the village's civic buildings close by.
- **4-9 smaller islets** round it at different heights (up to about 10 blocks above or below the court), one to
  three buildings each, joined to the court by **skywood bridges** with fence rails and sky lanterns (the Cirri
  fly; the bridges are for guests).
- The islands: a grass surface, a few layers of dirt, then **skystone**, tapering to a rough point underneath,
  with hanging roots and skystone spikes, and **cloud** blocks clinging to the underside. Skywood trees,
  flowers and paths on top.
- A **Lift Dock** on the rim of the central island. Straight below it, on the ground, stands a **Wind Stone**
  (a ring of skystone round it). Stand in the wind column over the stone and it lifts you to the dock; on the
  dock, step into the shaft and hold sneak to sink gently back down. This is how a walking player reaches a
  sky village.
- Lit everywhere (no mob spawns inside the village), no beds (the Cirri sleep floating in the air over
  cushions in their nests).

## The Cirri's architecture

Open, airy and light: white **calcite** and pale **skystone** walls, **polished skystone** and **gilded
skystone** trim, **skystone pillars** in colonnades, domed and tiered roofs, big round windows, arches,
balconies and upper doorways open to the sky (a Cirri flies in through the top; walking guests use the
door on the ground floor and stairs or ladders). Cloth is everywhere: **veilcloth** awnings, canopies and
hangings in white, sky and rose. **Wind chimes** hang under eaves, **sky lanterns** light paths and rooms,
**wind harps** stand in halls and courts. Gold accents (gilded skystone, a few gold blocks at most on the
grandest roofs), sky-blue glass (light blue stained glass), flowers in pots, skywood furniture.

Palette (mod blocks are `skyfriends:<id>`; see tools/blocks/catalog.py):
- stone: skystone, skystone_bricks, polished_skystone, gilded_skystone, skystone_pillar, their stairs/slabs/wall;
  vanilla calcite, smooth quartz, quartz slabs/stairs, white concrete only sparingly.
- wood: skywood_log, skywood, skywood_planks, skywood_stairs/slab/fence/fence_gate; vanilla birch/cherry doors,
  trapdoors and signs (the mod has no doors).
- cloth: white/sky/rose_veilcloth and their carpets; vanilla white/light_blue/pink wool and carpets are fine.
- light: skyfriends:sky_lantern (`hanging=true|false`), vanilla lanterns rarely; glowing candles.
- glass: light_blue_stained_glass(_pane), white_stained_glass(_pane), glass_pane.
- nature: skywood_leaves (`persistent=true` is set for you), skywood_sapling, flowers, azalea, moss, lily pads.
- furniture: wind_harp (`facing`), wind_chime (must hang under a block), loom, note_block, bell, barrel,
  chiseled bookshelf, flower_pot / potted plants, lectern, decorated_pot.

## Jobs and where they work

| Job | Building | Work |
|---|---|---|
| Harpist (2) | Hall of Echoes | plays the wind harps |
| Weaver (2) | Loom House | weaves veilcloth |
| Gardener (2) | Cloud Garden | tends the koi pool and the trees |
| Bellkeeper | Bell Pagoda | rings the bell at dawn and dusk |
| Lamplighter | Lantern Spire | tends the great lantern |
| Skymerchant | Market Pavilion | trades with guests |
| Windkeeper | Lift Dock | keeps the Wind Stone, greets guests |

Children have no job. Homes hold couples (a woman and a man) and their children.

## Buildings (front faces north, door at `door` on the north face)

Village core: `veil_court` (plaza), `bell_pagoda`, `hall_of_echoes`, `loom_house`, `cloud_garden`,
`market_pavilion`, `lantern_spire`, `lift_dock` (rim). Homes: `nest_house` (2), `nest_house_large` (4),
`twin_nest` (4), `rim_house` (2, rim). Decor: `sky_lamp`, `veil_bench`, `chime_arch`, `koi_pond`,
`harp_stand`. Wild structures: `wind_shrine`, `ruined_belltower`.

Spots (`b.spot(kind, x, y, z)`, the air cell a Cirri hovers in): `sleep` (one per resident, in the air over a
cushion or nest), `work` (beside the work block), `sit` and `stand` (gathering places), and `koi` (over a koi
pool, where Cloud Koi are released) and `lift` (the centre of the lift shaft at the dock's floor level).

## Wild sky structures

Scattered through the overworld sky, each one rare, each on its own floating islet:
- **Sky islets**: small wild islands with skywood trees and flowers, now and then a school of Cloud Koi.
- **Wind Shrine**: a small open shrine on a lone islet, a wind harp and chimes, a chest of Cirri goods.
- **Ruined Belltower**: a broken old Cirri bell tower on a cracked islet, the bell fallen, a chest.

## How it is built

- **Buildings:** `tools/buildings/<folder>/*.py`, each a function drawing into a `kit.Build` (kit ported from End
  Friends; `skyfriends:` ids are checked against `tools/blocks/catalog.py`). Preview: `python tools/buildings/preview.py
  <name>`; check all: `python tools/buildings/preview.py --all --check`.
- **Plans:** `tools/villages/plan.py` sets the court on a central island, the Lift Dock on its rim (its shaft kept
  open to the ground), every other building on its own islet round the court at its own height, door toward the
  court; A* paths become paved paths on land and railed skywood bridges over open sky; islands are drawn straight
  into the canvas (grass, dirt, skystone tapering to a rough point, hanging roots, clinging cloud), with skywood trees,
  flowers, sky lamps (every stretch of island lit) and loose puffs of cloud round about. `roster.py` lists who lives
  there; `compile.py` cuts each layout into 32x32 tiles and writes `data/skyfriends/worldgen/structure/*.json`.
- **Layouts:** three villages (`village_a/b/c`, 12-18 Cirri each, 10 jobs, 8-10 koi), five wild islets, a wind shrine
  and a ruined belltower.
- **In the game:** one structure type, `skyfriends:sky_structure` (`world/SkyStructure`): a random layout, turned,
  its floor at a random height in its band and at least `clearance` blocks over the highest ground under it.
  `SkyPieces`: `TilePiece` (the templates), `ResidentPiece` (spawns the roster once per chunk; every resident's UUID
  comes from the village start and their place on the roster, so a child names its mother before she exists),
  `LiftPiece` (the Wind Stone in its ring on the ground under the dock's shaft, connected to the dock).
- **Placement:** villages spacing 44 chunks (separation 16), islets 13 (4), shrines 36 (12), ruins 40 (14); islets,
  shrines and ruins keep a few chunks away from villages. All in any overworld biome. Nothing else in the modpack
  builds in the sky, so they never overlap Village Friends villages, homesteads, Plata dens or Cave Expansion delves.

## Verified (2026-10-10)

`gradlew runClientGameTest -PskyTests=Sky -PtestHeap=2g` (a normal world, seed 20261010, structures on) passes: a
village found at (224, 192) floating at y 197-253; 18 of 18 Cirri spawned (8 women, 8 men, 2 children with mothers,
10 with jobs, all named); the Wind Stone at y 62 lifts a survival player 164 blocks to the dock in 11 s and sets them
on the landing; holding sneak they sink back in 25 s unhurt; at night 12-13 of 16 fly home and sleep within 30 s; by
day several are at work; the Skymerchant's trades open; a baby is born; 8 Cloud Koi keep to their pools; an islet, a
shrine and a ruin are found; a whale swims on at y 227; a Cirrus Veil saves a 40-block fall.

Lessons: superflat test worlds only build their preset's structures (use `setUseConsistentSettings(false)`); a 2-block
doorway with a carpet in it is too low for a 1.95-tall hitbox (the Cirri's is now 1.8); flying paths only search
about 40 blocks, so a Cirri indoors first paths out toward its goal, and one that makes no headway for 10 s, unseen,
slips free.
