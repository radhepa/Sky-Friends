# The Cirri (SEER-eye)

Sky Friends adds one people of the sky. Three were designed side by side on 2026-10-10 (the Cirri, the Cumulin
balloon-folk and the Nimbari storm-tails; the two that lost are kept in `tools/candidates/`). The Cirri were chosen.

## Decisions

- **The Cirri are the Sky Friends people** (user, 2026-10-10).
- **They have the same eyes as Village Friends villagers** (user, 2026-10-10): the living eyes, ported, not borrowed
  from VF at runtime, so Sky Friends works without VF. Same two eye styles (Starlit, Soft Glint, picked per person
  for life), same blink timing, glances and eye contact, same feminine details (lash wing, arched brow, rosy lips,
  blush), same eye white (`#ede0cd`) and colour formulas. See "Living eyes" below.
- **Always airborne** (user's brief): a Cirri never lands. It flies with a custom animation, and it is humanoid.
- **Women and men, with voices, and babies** (user, 2026-10-10). As in Village Friends, women always wear the
  feminine face details and men never do.

## Look

About two blocks tall and slender. Warm skin; dark hair in a high bun with a long tail; a gold circlet on the
hairline with a sky-blue stone; a cream silk wrap and a rose stole over the shoulders; a rose sash; loose sky-blue
trousers in long pleats with gold cuffs; bare feet with gold anklets; gold armlets and stacked bangles; silk ribbons
at the wrists. Iris colour: a high-sky blue-grey (`#4f7896`).

Their **veils** are what fly: two long scarves of woven cirrus cloud that grow from the stole, sky blue at the
root, cloud white along their length and dawn rose at the frayed tips, threaded with gold at the edges. Inspired by
the flying musicians painted on old temple and cave walls across Asia.

Model: `tools/people/cirri.py` (box model, 128x64 texture; the bottom row is the living eyes' swatch strip).
Preview: `python tools/preview/preview.py cirri --views 4`.

## Flight

A Cirri never flaps. Its pose blends between two ways of being in the air, driven by how fast it is really moving
(`CirriModel`):

- **Hovering:** upright on nothing, bobbing gently; arms float out and drift as if treading water; legs hang with
  soft knees and tread slowly; the veils float round it in slow, wide waves, flaring out at the sides.
- **Cruising:** stretched out flat, chest first, legs together behind with the right knee bent up, arms spread and
  swept back; veils, hair, sash and wrist ribbons stream behind in quick ripples that travel down their length.
- It rolls into turns (the inside arm dips), lifts its chest to climb, and a neck joint keeps the head level so it
  looks where it is going.

Behaviour (`entity/Cirri`, steering maths in `flight/Glide`):

- **Soar:** long arcs between points 12-32 blocks apart, 7-20 blocks over the ground, within 40 blocks of home.
  The heading turns at most about 3 degrees a tick, so it swoops rather than darts. Cruise is 6 blocks a second.
- **Hover:** about one arrival in four, it stops for 3-8 seconds and looks about.
- **Watch:** now and then it stops 5.5 blocks from a player who is near and in sight, faces them and watches for a
  while.
- **Flee:** hurt, it flies up and away at 11 blocks a second for 5 seconds.
- It climbs whenever it is within 3 blocks of the ground or water, and climbs over anything ahead of it.
- No fall damage, never despawns. When it dies its veils give out and it falls.

## Living eyes

`face/LivingFace` (pure: styles, blink timing, glances, lash geometry, numbers identical to VF's `FaceDetails` and
`ResidentMotion`), `client/model/LivingEyes` (the planes, placed exactly as VF's `ResidentModel` places them, and
their animation), `tools/people/living_eyes.py` (bakes the 11-colour swatch strip with VF's colour formulas).
The face texture is clean skin; every eye feature is a plane in front of it. `CirriRenderer` supplies the eye
contact (a camera within 6 blocks and in front of the face) the way VF's `ResidentRenderer` does.

## Verified (2026-10-10)

- 8 unit tests (`gradlew build`): blink timing, lash geometry, the eye-style and face split, glance size, steering
  turn limit, arcs, easing.
- `gradlew runClientGameTest -PskyTests=Cirri -PtestHeap=2g` passes standalone and inside the full VillageFriends
  modpack (`-PcompatMods=%APPDATA%/.minecraft/instances/VillageFriends/mods`: VF 2.29.0, RPG 1.1.0, NSV 1.5.0,
  End 0.2.0, Nether 0.4.0, Plata 1.2.0, Cave Expansion 1.0.0, Turning Seasons 1.1.0). In the pack: 30 s airborne,
  131 blocks covered, never under 10 blocks over the ground, within 39 blocks of home; hover, watch (6.2 blocks
  off, facing the player) and flee (up 10.5, away 29 blocks in 3 s) all as designed; six-strong flock airborne.
  No Sky Friends errors in the log.
- Film: `-PskyFilm` then `python tools/film.py` (build/film/cirri-flight.mp4).

## Women, men and children

- **Looks:** three complexions (each with its own hair and eye colour) and four outfits (dawn, dusk, noon, storm).
  Men have short hair with a topknot, a tunic with a sash across it, a narrow shoulder mantle and gold bracers;
  women a high bun with a long tail, a silk wrap and stacked bangles. Children are small with the same big head
  (the living eyes need it), a little bun and short veils; girls wear dawn colours, boys noon. 30 textures in all
  (`tools/people/cirri.py`: `cirri`, `cirri_male`, `cirri_child` geometry). A job sets the outfit (harpists and
  lamplighters dawn, weavers and Skymerchants dusk, gardeners and Windkeepers noon, the bellkeeper storm).
- **Names:** 28 women's and 28 men's names (`entity/CirriKin`), shown when you look at a Cirri.
- **Voices:** wordless sung hums (like Village Friends villagers'), a greeting when they turn to you, cries when hurt,
  a sigh at death, sleepy breathing: separate women's, men's and children's voices, all synthesized
  (`tools/sounds/synth.py`).
- **Babies:** at dawn, now and then, a woman whose husband shares her nest has a baby (fewer than two little ones
  each, and only while the village holds fewer than 24 Cirri). Children keep close to their mother, sleep by her
  nest, and grow up in twenty days (a child born in the village from the start) or one day (a new baby);
  grown up, they keep to their mother's nest.

## A day in a sky village

- **Night (13000-23300):** everyone flies home along a flying path and sleeps floating over the cushion of their
  nest, curled up, eyes shut, breathing softly.
- **Day:** each Cirri picks what to do next: work (half the time, if they have a job), gather at the Veil Court,
  or soar round the village. Harpists play the wind harps by their spot; the bellkeeper rings the bell at dawn and
  dusk; the others work with busy hands at their spot.
- **The Skymerchant** trades: sky peaches, saplings, cloud, skystone bricks, veilcloth, sky lanterns, wind chimes,
  gilded skystone, wind harps, the Windsong Flute and the Cirrus Veil; buys amethyst, feathers, phantom membranes
  and string. Stock restocks every dawn.
- **Music:** play a wind harp or the Windsong Flute and every Cirri within twenty blocks comes to listen.

## Talking, and village life

Built 2026-10-10 (0.3.0): conversations, friendship, questions and offers, gifts, stories, the Journal, gossip,
emote bubbles, the village title card, pairs chatting, the Evensong, whale escorts, children's tag, sheltering from
thunder, presents from close friends and the animation pack. See `docs/DIALOGUE.md` and `docs/ANIMATIONS.md`. Couples
know each other by name (`partner`, set from the village roster), so children know their Mum and Dad.
