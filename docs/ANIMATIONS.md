# Animations

The Cirri have an animation pack: 126 clips that make them feel alive. Hovering, they idle in their own
way and practise their trade, chat with a neighbour, greet you as you come up, gesture while their line types out in
a conversation and listen while you choose a reply, and react to what happens: a gift they love, one they don't, a
level of friendship, a sorry accepted, a blow. The system is End Friends' and Nether Friends' (itself after Village
Friends' resident life), ported.

Packs only describe motion. The director (`client/anim/Life.java`) decides when each clip plays and the poser
(`client/anim/Poser.java`) adds it on top of the model's live pose. Nothing about animation is saved or synced except
what the server already knows: each Cirri's job, manner and routine (the synced `motion` string) and reactions to
conversation moments (the `skyfriends:cue` packet).

## The pack

`src/main/resources/assets/skyfriends/animations/cirri.json`, written in Python under `tools/animations/cirri/*.py`
with `tools/animations/kit.py`. One pack fits all three models: women (`cirri`), men (`cirri_male`) and children
(`cirri_child`). Never hand-edit the JSON.

```text
python tools/animations/compile.py                 # compile
python tools/animations/compile.py --check         # validate, coverage, at least 60 distinct motions, JSON current
python tools/animations/compile.py --list cirri    # every clip: trigger, length, weight, requirements
python tools/animations/compile.py --parts cirri   # the parts each model has, and the waist
python tools/animations/sheet.py cirri --clips veil_stretch,greet_air_bow --frames 7 [--view 90] [--look cirri_child] [--mirror]
                                                   # frames of clips on the real model, offline -> tools/animations/out/
python tools/animations/live_sheet.py cirri ...    # the same, with the hovering pose under each frame (what the game draws)
```

## The Cirri's live pose

A Cirri never stands: clips are added on top of a body that is always flying (`client/model/CirriModel.java`).
Hovering, it is upright on nothing and bobs gently; the arms float out to the sides (about 20 degrees) and drift as if
treading water, forearms softly bent; the legs hang with soft knees and tread slowly; the two long veils (four
segments each side) float round it in slow waves; the hair tail, sash and wrist ribbons sway. Cruising, it lies out
flat. **Clips play only while it hovers** (the director fades them out as it picks up speed), so they are written for
the hovering body. The sheet shows the bare model (rest pose) plus the clip.

Parts: `body` (everything above the hips hangs from it), `neck`, `head`, `hair`, `hair2`, `sash`, `right_arm`/`left_arm`,
`right_forearm`/`left_forearm`, `right_leg`/`left_leg`, `right_shin`/`left_shin`, `right_ribbon`/`right_ribbon2` (and
left), `right_veil` to `right_veil4` (and left). The waist bends the body at the hips (13 pixels up); `root` turns or
moves the whole Cirri, about its hips (not its feet: it is in the air). Being airborne, a Cirri can do what walkers can't: a slow somersault (`root` pitch 360 with a
`root_pos` lift so it turns about its middle), a barrel roll, a spin, a little rise and sink, kicking its legs, tucking
its knees up.

## How the director chooses

Each Cirri near the player is ticked on the client. When it has hovered for a second and its last clip has finished,
it rests a moment (children less), then picks a clip for the moment:

| Trigger | When |
|---|---|
| `idle` | Hovering about: everyday moments and their work compete by weight. |
| `chat_speak`, `chat_listen` | Another Cirri hovers within about three blocks in front of them; they take turns. |
| `greet` | A player comes within five and a half blocks in front of them (once a minute at most), or a conversation opens. |
| `talk` | In a conversation with you, while their line types out. |
| `listen` | In a conversation, while you choose a reply. |
| `farewell` | The conversation ends (or they leave it: busy, sleepy, or upset). |
| `happy` | A gift they love, or a new level of friendship. |
| `thanks` | A gift they like or don't mind. |
| `decline` | A gift they dislike, or a sorry they aren't ready to accept. |
| `pleased` | A sorry accepted. |
| `annoyed` | Still upset with you, they turn away. |
| `hurt` | They take damage. |

Reactions play on a second layer and briefly replace the current activity. Nobody repeats their last two clips if
anything else fits. One Cirri in nine is left-handed and mirrors one-handed gestures. Nobody animates asleep; while a
clip plays, the model's own working gestures rest.

Clips are picked by **tags**:

| Tag | Meaning |
|---|---|
| `adult`, `child` | Age. |
| `job:<job>` | harpist, weaver, gardener, bellkeeper, lamplighter, skymerchant, windkeeper (children have none). |
| `manner:<manner>` | steady, shy, restless, busy, flighty. |
| `routine:<routine>` | What they are doing: work, gather, soar, chat, evensong, escort, shelter, idle (children: play, follow, evensong, shelter, idle). |
| `working` | At their workplace in working hours: boost work clips with it. |
| `social` | A chat partner is near. |
| `talking` | In a conversation with you. |

## File format

See `tools/animations/kit.py` (its docstring has the conventions) and End Friends' `docs/ANIMATIONS.md`, whose format
this is: `id`, `name`, `trigger`, `length` (up to 30 s), `weight`, `require`, `avoid`, `boost`, `blend`, `mirror`
(`hand`, `free`, `never`) and `tracks` of `<part>.rot` (degrees) and `<part>.pos` (model pixels), keys `[seconds, x,
y, z]`. A part a model doesn't have is skipped.
