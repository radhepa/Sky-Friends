# Sky Friends

A Fabric mod for Minecraft 26.3 that makes the sky more interesting. High above the clouds float the villages of
the **Cirri** (SEER-eye), a people who fly on long veils of woven cloud and never set foot on the ground. Wild
islands drift in the sky, a shrine and a ruined bell tower wait to be found, flying koi swim round the islands, and
now and then a great Cloud Whale swims across the sky, singing.

Sky Friends belongs to the same modpack as Village Friends, End Friends, Nether Friends and Cave Expansion, and
works with or without any of them.

## The Cirri

- **Always flying.** They soar in long swooping arcs, hover upright on the air, and never land. Cruising, they
  stretch out flat with their veils, hair and ribbons streaming behind; hovering, the veils float round them like
  weed in a current.
- **Women, men and children**, each with a name, a look (three complexions, four outfits) and a voice: wordless
  humming, a greeting when they turn to you, cries when hurt.
- **Living eyes**, the same as Village Friends villagers': two eye styles, blinking, glances and eye contact.
- **A day in the village.** At night they sleep floating over the cushions of their nests. By day they work (the
  harpists play the wind harps, the bellkeeper rings the bell at dawn and dusk, the weavers weave, the gardeners
  tend the koi), gather at the Veil Court, and soar round their islands.
- **Families.** Couples share a nest; now and then at dawn a baby is born, who keeps close to its mother.
- **The Skymerchant** trades Cirri goods for emeralds, including the Cirrus Veil and the Windsong Flute.
- **Music.** Play a wind harp or a Windsong Flute and the Cirri nearby come to listen. Hit one and it flies away.

## The sky

- **Sky villages** float at about y 205-235: a central island with the Veil Court, a Bell Pagoda, the Hall of
  Echoes, a Loom House, a Cloud Garden with a koi pool, a Market Pavilion, a Lantern Spire and the Cirri's nest
  houses, each on its own islet, joined by skywood bridges.
- **The wind lift.** Straight under each village's Lift Dock, on the ground, stands a **Wind Stone** in a ring of
  skystone. Stand in its wind and it lifts you up to the dock; on the dock, step into the shaft and hold sneak to
  sink gently back down.
- **Wild sky islets** with skywood trees and flowers, some with a koi pond; **Wind Shrines** with a wind harp and a
  chest of Cirri goods; **Ruined Belltowers**, broken and overgrown, with a fallen bell and a chest.
- **Cloud Koi** swim through the air in schools round the koi pools and now and then shed a Sky Scale.
- **Cloud Whales** swim slowly across the high sky with little clouds resting on their backs, and sing.

## Blocks and items

Skystone (with bricks, polished, gilded and pillar forms, stairs, slabs and a wall), cloud blocks (nothing that
lands on cloud takes fall damage), skywood (logs, planks, stairs, slabs, fences, gates, blossoming leaves and
saplings that grow skywood trees), veilcloth in white, sky and rose (and carpets), wind chimes (they ring in the
wind and the rain), wind harps, sky lanterns, and the Wind Stone. Items: Sky Scales, Sky Peaches, the Windsong
Flute and the Cirrus Veil (wear it and you glide gently whenever you fall; sneak to drop).

Find a village: `/locate structure skyfriends:sky_village`. Spawn eggs and every block are in the Sky Friends
creative tab.

## Building

```
gradlew build
```

Requires Java 25. Minecraft 26.3, Fabric Loader 0.19.5, Fabric API 0.161.0+26.3.

Everything generated lives in `tools/` (Python 3 with Pillow, numpy and scipy; ffmpeg for the sounds):

| What | How |
|---|---|
| Mob models and textures | `python tools/gen_assets.py` |
| Block textures | `python tools/blocks/textures.py` |
| Block models, loot, tags, recipes, names | `python tools/blocks/gen_blocks.py` |
| Sounds | `python tools/sounds/synth.py` |
| Buildings (previews) | `python tools/buildings/preview.py <name>` |
| Villages and sky structures | `python tools/villages/compile.py` |

The in-game tests:

```
gradlew runClientGameTest -PskyTests=Cirri,Sky -PtestHeap=2g
```

Add `-PskyFilm` to film them (then `python tools/film.py`), and `-PcompatMods=<a modpack's mods folder>` to run
them inside a modpack. Design notes are in `docs/`.

## License

MIT
