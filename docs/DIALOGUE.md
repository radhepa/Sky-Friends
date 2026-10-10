# Talking with the Cirri

Right-click a Cirri to talk. This document is the canon for everything the Cirri say (their voice, their world,
the words they use), the format the lines are written in, and how the game chooses them. The system follows
Village Friends' talk engine: hand-written lines in pools, chosen by what is actually happening.

## How a line is chosen

Every reply has a **topic** (greet, chat, work, sky, ground, song, news, heart; children: chat, play, sky, ground,
song, secret, family). For the moment you ask, the game reads the world into a **context**: the time of day, the
weather, today's wind, the moon, what the Cirri was doing, their personality and job, how well they know you,
what you hold and how you look, what is near (a Cloud Whale, koi, children, a wind harp, the Evensong) and things
you told them before. Each topic draws from several **pools**, weighted by that context (`talk/Talk.java`). A line
whose placeholder can't be filled (a `{partner}` for someone who has none) is skipped, and nobody repeats a line
they said to you lately.

Sometimes, on "How's your day?", a Cirri **asks you a question** instead (once per question, ever) and remembers
your answer: later lines call back to it (`remember.<flag>`). Or they **offer to help** when they see you need it
(hurt, hungry, soaked, standing at the edge without a veil): once a day per offer.

**News** and **Anyone special?** come from the village itself: who is married to whom, whose baby was born, who
grew up, the whale that passed, the storm last night, what you did. **Gossip** names real neighbours.

## The voice of the Cirri

The Cirri (SEER-eye; one Cirri, many Cirri) are a people of the high sky. They fly on two long veils of woven
cirrus cloud and **never set foot on the ground**. They are musical, light-hearted, curious and courteous, a little
dreamy, proud of their villages and their weaving, and gently amazed by people who walk.

- **Light, airy, warm.** Short sentences, open vowels, sky images. Wonder rather than worry. They tease kindly.
- **Wind words.** Weather is not small talk to them: it is news, mood and road. They say "fair wind" for hello and
  goodbye, "a light breeze" for a little while, "high" for happy ("I'm high today!") and "low" or "heavy" for sad.
  "Grounded" is the saddest word they have.
- **Not human.** They have never walked, sat on a chair, cooked over a fire or swum. Stairs puzzle them. Doors are
  a courtesy for guests. They sleep curled in the air over cushions. They eat sky peaches, berries, honey and
  flowers, in the air, and never cook (fire is the one thing the sky fears).
- **They call the player and every ground-dweller a "walker"** (never an insult; children say "groundling"). They
  admire walkers' sturdiness and pity their heavy feet.
- Speakers may be women or men. **Never reveal or assume the speaker's gender**, and never give anyone else a
  gender either: no he, she, him, her, his, hers, husband, wife, son, daughter, brother, sister, boy, girl. Use
  names, "they", or the placeholders (`{spouse}` is "husband" or "wife", filled by the game). Children may say
  "Mum" and "Dad".
- Modern words are out (no okay, cool, guys, stuff like that). No em dashes: use commas, colons or full stops.
  Plain ASCII apostrophes and quotes. No swearing. Lines are at most 220 characters; most are one to three
  sentences.

### Their world (canon)

- **Veils.** A Cirri's two veils are woven from cirrus cloud by the weavers and grow from the stole over their
  shoulders: sky blue at the root, cloud white along their length, dawn rose at the frayed tips, threaded with gold.
  "A Cirri is only as high as their veil is whole." Children have short veils; when a child grows up the weavers
  weave their long veils (**the Lengthening**, a big day). Torn veils are mended with phantom membrane and string.
- **The Four Winds**, by name: **Aure** (the east wind, the dawn wind, gentle and dewy), **Sefa** (the south wind,
  warm and lazy, smells of peaches), **Vell** (the west wind, the evening wind that carries songs) and **Borre** (the
  north wind, cold and sharp, the storm-bringer). Each day one of them "has the sky" (`{wind}`). Cirri greet the
  wind like a neighbour.
- **Villages** float above the clouds (the clouds are *below* them; they look down on weather). Each has a name.
  The **Veil Court** is the plaza at the heart; the **Bell Pagoda**, the **Hall of Echoes** (wind harps), the
  **Loom House**, the **Cloud Garden** (skywood trees, sky peaches, the koi pool), the **Market Pavilion**, the
  **Lantern Spire** and the **Lift Dock** stand round it on their own islets, joined by skywood bridges. The
  bridges and doors are for walkers: a courtesy. Homes are **nests**; a couple shares a nest with their children.
- **The Wind Stone.** Far below each village's Lift Dock stands a Wind Stone in a ring of skystone. Stand in its
  wind and it lifts you up; on the dock, step into the shaft and hold sneak to sink back down. The first
  windkeepers set the stones so that walkers could visit: **the Courtesy**, an old promise of welcome.
- **The Evensong.** At dusk the village gathers over the Veil Court and sings the day down, the harpists leading.
  Every Cirri knows it. Missing it is like missing a meal.
- **The bell** rings at dawn and at dusk (the bellkeeper), and in a long peal before a storm.
- **Cloud Whales**, "the Old Singers", swim slowly across the high sky with little clouds resting on their backs.
  Cirri believe the whales herd the clouds and sing the weather into being. Meeting one is a blessing; Cirri fly
  out to swim beside them and sing back.
- **Cloud Koi** swim in schools round the koi pools. The gardeners tend them. Now and then one sheds a **Sky
  Scale**: lucky, kept, given to friends.
- **Food:** sky peaches (from skywood trees), sweet berries, glow berries, honey, apples, melon, flower nectar.
- **Fears:** lightning and thunderstorms (they shelter in their nests and hum to the children), fire, phantoms
  ("the night-moths"; their membranes mend veils), fireworks (loud, dangerous, rude), anything heavy. Being
  grounded.
- **Death** is "going up past the blue". **Dawns** count the days. Old sayings: "Keep your veil whole and your
  heart light." "The sky is wide enough for everyone." "Never trust a still day." "Sing the day down."
- **Ruins.** The **Ruined Belltowers** were villages that "grew too heavy": iron bells and stone piled on until the
  islands sank into the clouds. The Cirri build light because of them. The **Wind Shrines** are lone places where
  Cirri leave gifts for the winds.
- **Walkers** they know of: the bell-villages far below (villagers), travellers with elytra ("walkers who borrowed
  wings", admired and teased), and you.

### Jobs

| Job | Where | What they do |
|---|---|---|
| harpist | Hall of Echoes | play the wind harps, tune them to the day's wind, lead the Evensong |
| weaver | Loom House | comb cirrus cloud at dawn, weave veilcloth and veils, mend torn veils |
| gardener | Cloud Garden | tend the skywood trees, the sky peaches, the flowers, the koi pool and its Cloud Koi |
| bellkeeper | Bell Pagoda | ring the bell at dawn and dusk and before storms, keep the village's time |
| lamplighter | Lantern Spire | tend the great lantern and the sky lanterns on the bridges, lit at dusk |
| skymerchant | Market Pavilion | trade with walkers: sell veilcloth, peaches, lanterns, flutes, veils; buy amethyst, feathers, phantom membrane, string |
| windkeeper | Lift Dock | keep the Wind Stone and its column of wind, greet walkers who come up, read the winds |
| (none) | anywhere | help wherever the wind needs them (the pool is `work.none`) |

### Personalities

| Grown-ups | Manner while you talk |
|---|---|
| `dreamer`: head in the clouds, poetic, wonders about stars, distances and the ground | hovers still |
| `merry`: cheerful, teasing, loves games, loops and laughing | darts off for a quick loop now and then |
| `gentle`: soft-spoken and kind, notices if you're hurt or tired | hovers still |
| `shy`: quiet, few words at first, warms slowly | keeps a little further off |
| `proud`: proud of the village, the craft and Cirri ways, a bit grand about walkers, softens as a friend | hovers still |
| `restless`: can't stay still, longs to fly far, talks of distant skies | drifts round you as you talk |
| `busy`: always in the middle of something, brisk but fond | excuses themselves after a while |
| `wise`: old-souled, full of sayings and the old stories | hovers still |
| `curious`: fascinated by walkers and the ground, asks everything | hovers still, leans in |

| Children | |
|---|---|
| `playful` | drifts and bobs round you |
| `shy` | keeps a little further off |
| `curious` | hovers still |
| `cheeky` | darts off for a loop now and then |
| `dreamy` | hovers still |
| `fidgety` | runs off to play after a while |

## Friendship

Ten levels, shown as ten little clouds that fill with gold: 0 Walker, 1 Passing Cloud, 2 Light Breeze, 3 Fair
Wind, 4 Kind Air, 5 Open Sky, 6 Updraft, 7 High Wind, 8 Windsong, 9 Veil-Kin, 10 One Sky. At level 3 they tell
you the village news; at 5 they talk about the people they love; at 7 they wave you over with a heart and bring
you a little present once a day; at 1 they bring up their story.

| | Friendship |
|---|---|
| First conversation of the day | +4 |
| Each topic, once a day | +3 (How's your day? +4) |
| Answering their question | +1 or +2, and they remember |
| A gift they love, like, don't mind, dislike (two a day) | +20 / +10 / +3 / -8 |
| Their story: offering help, the first request, hearing the rest, the other requests, the ending | +3, +15, +10, +10 each, +25 |
| Striking them | -15, and a grudge until you say sorry (or a day or two passes) |

Levels need 10, 25, 45, 70, 100, 135, 175, 220, 270 and 330 points. Friendship is kept by each Cirri, per player.

## The conversation window

`client/screen/TalkScreen.java`: the Village Friends layout in the colours of a clear sky. A portrait of the speaker
with their mood bubble, their name on a ribbon (rose for women, sky blue for men, pale blue for children) with their
job and village, and the line typing out in a breath of flute (higher for children). Tabs: **Talk**, **Story** (marked
with a little cloud when there is something to do there) and **Journal** (Tab cycles them). Replies are numbered
bubbles (press 1-8). The dock: **Greet**, **Gift** (what you hold), **Trade** (the Skymerchant) and **Farewell** (Esc).
The card shows ten clouds filling with gold; a banner drops in when you grow closer.

## While you talk

They stop and hover in front of you at about your eye level, by their manner: the steady hover still, the shy keep
four blocks off (and drift back if you crowd them), the restless sway slowly round you, the flighty dart up into a
quick loop every ten seconds or so and come straight back, and the busy excuse themselves after half a minute (two or
three for close friends, level 6+). Whatever their manner, someone still upset with you turns away a few seconds in;
someone you woke at night goes back to sleep (unless you are very dear to them, level 8). They won't talk to you
again for a little while after cutting a conversation short. A conversation nobody touches for five minutes ends.

## Stories and the Journal

Every Cirri has a story (`data/skyfriends/stories/cirri.json`, 25 stories, two for each job and the rest for anyone;
`cirri_child.json`, 10 short ones). From level 1 they bring it up; bring the first thing they ask for; talk on three
different days and reach level 3 and they tell you the rest; do their other two requests; talk on five days, reach
level 5, and answer them one of two ways; they give you something. Children's stories are one request and a gift.
Check the books with `python tools/stories/check.py` (its docstring is the schema).

The Journal: **Memories** (dated: meeting them, gifts, what you told them, growing closer, each step of their story, a
blow struck, a sorry said, a present they brought), **About** (their personality, who they share a nest with, their
children or parents, their closest friend, your friendship, the gifts you've found they love or don't) and **Story
notes** (each step, done or still to do).

## Village life

`life/VillageLife.java`, a few times a second on the server, for every sky village with someone near:

- **Arriving:** the village's name on a title card (`client/ArrivalBanner.java`) with how many live there; a walker's
  visit is village news once a day.
- **Emote bubbles** (`life/Emote`, `client/EmoteBubbles`, the sheet drawn by `tools/gui/emotes.py`): little clouds over
  their heads, Tomodachi Life style. Greeting you, answering you, chatting, singing, sheltering, sleeping ("Zz").
- **Chatting:** neighbours near each other stop in pairs to hover face to face for a while; their bubbles show how
  they feel about each other (hearts between partners, notes in a family, ideas between friends, a blush for a crush,
  "..." between near strangers), and the animation director gives them chat gestures.
- **The Evensong:** from just before dusk until nightfall everyone free (all but the bellkeeper and the lamplighter,
  busy at dusk) circles slowly over the Veil Court, each at their own height, humming more often, notes in the air.
- **Whales:** when a Cloud Whale swims within 140 blocks, two or three fly out to swim alongside it and sing; once a
  day it's news.
- **Children** at a loose end play tag: one chases, the other flees, and it swaps on a tag.
- **Thunder:** everyone flies home to their nest and stays there, awake, till it passes; a storm is news.
- **Close friends** (level 7) wave you over with a heart once a day, and once a day one who sees you flies over with a
  little present (a sky peach, a sky scale, honey, amethyst, a flower...).
- **News** (`life/Chronicle`, kept with the world): births, children grown up, Cirri gone up past the blue, whales,
  storms, walkers' visits, gifts loved, blows struck, stories helped along. A village keeps its last 24 pieces of news.
- **Families** (`life/Kin`): partners (set from the village roster), children, a child's Mum and Dad, each Cirri's
  closest friend, a coworker, and for some without a partner, someone they're sweet on.

## Writing lines

Lines are plain text in `tools/dialogue/lines/*.txt`, under `## pool.key` headings, one line per line:

    ## greet.dawn
    Fair wind, {player}! Aure is still yawning; you're up before the east wind.
    # a comment

Questions and offers are in `tools/dialogue/questions/*.txt`:

    ? favourite_wind
    Q: Which wind would you choose, if you could fly? Everyone has one.
    Q: Settle something for me: which of the Four Winds is the kindest?
    - Aure, the dawn wind :: Aure! Dew on your face and the whole sky blushing. You'd be up early with me. @likes:aure {points:1} [SPARKLE]
    - Borre, the storm :: Borre? You're braver than you look, walker. @likes:borre {points:1} [EXCLAIM]

    ! patch_up | when: hurt job:gardener
    Q: You're hurt! Hold still, I keep a cloud-salve for scraped koi and scraped walkers alike.
    - Yes, please :: There. Cool, isn't it? Like lying in a raincloud. {heal} [HEART]
    - I'm fine :: Fine, the walker says, dripping. Come back if it stings. [SWEAT]

`?` asks once ever; `!` is an **offer**, at most once a day, and only grown-ups make offers. `when:` lists context
tags that must all hold (`!rain` means not raining, `level:4` means friendship 4 or more, `a|b` either). Answers are
`- Label :: reply` (labels at most 30 characters). After the reply: `@flag` is remembered about you (and opens the
pool `remember.<flag>` with `:` turned into `_`), `{points:N}` adds friendship, `{effect}` makes something happen,
`[MOOD]` is the bubble they show.

Compile and check:

    python tools/dialogue/dialogue.py           # compile to src/main/resources/data/skyfriends/dialogue/cirri.json
    python tools/dialogue/dialogue.py --check   # validate, and confirm the compiled file is current
    python tools/dialogue/dialogue.py --stats   # counts by pool family

### Placeholders

| | |
|---|---|
| `{player}` | your name |
| `{name}` | the speaker's first name |
| `{village}` | their village's name |
| `{job}` | their job in lower case ("harpist") |
| `{wind}` | the wind that has the sky today: Aure, Sefa, Vell or Borre |
| `{moon}` | tonight's moon ("full moon", "waxing crescent moon") |
| `{day}` | how many dawns this world has seen |
| `{item}` | what you hold, in lower case |
| `{partner}` | the first name of the one they share their nest with (a grown-up's), if any |
| `{spouse}` | "husband" or "wife": what `{partner}` is to them |
| `{child}` | one of their children's names, if any |
| `{mother}`, `{father}` | a child's parents' names |
| `{friend}` | their closest friend in the village |
| `{neighbour}` | someone else who lives there |
| `{coworker}` | someone with the same job |
| `{crush}` | someone they're sweet on (only in `heart.crush`) |
| `{who}`, `{other}` | the people in a piece of news (only in `news.*`) |
| `{gift}` | the gift you just gave (only in `gift.*`) |

### Moods

`EXCLAIM QUESTION HEART NOTE ANGER SWEAT DOTS SLEEP SPARKLE IDEA GLOOM BLUSH`: the bubble over their head.

### Effects (offers and answers)

| | |
|---|---|
| `heal` | patches you up (3 hearts and a little regeneration) |
| `peach` | gives you two Sky Peaches |
| `slowfall` | wraps a breath of wind round you (Slow Falling for a minute) |
| `lantern` | gives you a Sky Lantern |
| `scale` | gives you a Sky Scale |
| `feather` | gives you three feathers |
| `flower` | gives you a flower |
| `mend_held` | mends what you hold a little (a weaver with an elytra, a veil, anything worn) |
| `lift` | tells you where the Wind Stone is (in your chat) |
| `song` | sings you a little song (Regeneration for a few seconds) |
| `dry` | a warm gust dries you off, and they keep you company (+3 friendship) |
| `emerald_tip` | presses an emerald into your hand |

## Pools

Grown-ups (`<p>` a personality, `<job>` a job or `none`, `<period>` dawn morning noon afternoon evening night late,
`<weather>` clear rain thunder snow, `<wind>` aure sefa vell borre, `<moon>` full waning_gibbous last_quarter
waning_crescent new waxing_crescent first_quarter waxing_gibbous, `<band>` stranger acquaintance friend close best,
`<routine>` work gather soar chat evensong escort shelter idle):

| Topic | Pools (weight) |
|---|---|
| greet | `greet.<period>` 3, `greet.band.<band>` 3, `greet.personality.<p>` 2, `greet.routine.<routine>` 3, `greet.weather.<weather>` 5 (not clear), `greet.wind.<wind>` 1, `held.<kind>` 2, `player.<state>` 4 |
| chat | `chat.<p>` 6, `chat.general` 3, `routine.<routine>` 3, `time.<period>` 2, `chat.new` (0-1) / `chat.friendly` / `chat.close` (6+) 2, `weather.<weather>` 4 (clear: 1), `moon.<moon>` 2 (night), `wind.<wind>` 2, `village.<thing>` 2, `held.<kind>` 2, `player.<state>` 3, `remember.<flag>` 3; sometimes a neighbour is mentioned (`mention.*`) |
| work | `work.<job>` 7, `work.on` (at work) / `work.off` 2, `work.weather.<weather>` 1 (not clear) |
| sky | `sky.general` 3, `sky.winds` 2, `sky.clouds` 2, `sky.whales` 2 (6 with a whale near), `sky.koi` 1 (4 with koi near), `sky.stars` 4 at night (else 1), `sky.storms` 4 in rain or thunder (else 1), `sky.veils` 2, `sky.history` 2 (3 from level 3) |
| ground | `ground.general` 4, `ground.<p>` 3, `ground.villages` 1, `ground.wonders` 2, `ground.fears` 2 |
| song | `song.general` 4, `song.<p>` 2, `song.evensong` 4 (evening, or at the Evensong; else 1), `song.night` 4 (night), `song.weather.<weather>` 2 (not clear), `song.harpist` 4 (harpists) |
| news | `news.<kind>` for the village's recent news (born, grew_up, passed, whale, storm, visitor, gift, struck, story), `news.none` when there is none |
| heart | `heart.partner`, `heart.single`, `heart.crush`, `heart.parent` |

`village.<thing>`: whale, koi, children, harp, evensong. `held.<kind>`: weapon, pickaxe, tool, fishing_rod, map,
spyglass, book, flower, emerald, diamond, gold, fire, lantern, bucket, food, peach, treat, music, flute, harp, veil,
scale, feather, membrane, string, amethyst, elytra, firework, breeze, cloud, sapling, potion, totem, pet.
`player.<state>`: hurt, hungry, wet, fire, dark, unarmored, diamond, golden, elytra, veil, flying, edge, pumpkin.

`mention.partner` (`{partner}`), `mention.child` (`{child}`), `mention.friend` (`{friend}`), `mention.coworker`
(`{coworker}`), `mention.neighbour` (`{neighbour}`): a sentence about someone in the village, added after a chat or
work line now and then.

Moments: `first_meeting`, `hurt` (you struck them lately), `night` (you woke them), `walk_off` (still upset with you,
they end it), `busy_off` (busy, they excuse themselves), `apology_accepted`, `apology_wary`, `gift.loved`,
`gift.liked`, `gift.neutral`, `gift.disliked`, `gift.limit` (no more today), `level_up`, `trade.open` (the
Skymerchant opens their wares), `gift.bring` (a close friend brings you a little present), `evensong.invite`
(at dusk, they invite you to the Evensong), `whale.sighted` (a whale is passing: they're off to meet it).

Children use `baby.` pools: `baby.greet`, `baby.chat`, `baby.<p>` (their personality), `baby.play`, `baby.sky`,
`baby.ground`, `baby.song`, `baby.song.night`, `baby.secret`, `baby.family`, `baby.family.mum` (`{mother}`),
`baby.family.dad` (`{father}`), `baby.weather.<weather>`, `baby.time.<period>`, `baby.routine.<routine>` (play,
follow, evensong, shelter, idle), `baby.village.<thing>`, `baby.held` (`{item}`), `baby.player.<state>` (hurt, wet,
elytra, veil, flying, edge), and the moments `baby.first_meeting`, `baby.hurt`, `baby.night`, `baby.walk_off`,
`baby.busy_off` (off to play), `baby.apology_accepted`, `baby.apology_wary`, `baby.gift.loved`, `baby.gift.liked`,
`baby.gift.neutral`, `baby.gift.disliked`, `baby.gift.limit`, `baby.level_up`, `baby.gift.bring`.

Gifts: what the Cirri love, like and don't like is in `talk/Tastes.java`.

## What's in it

5,558 pieces of dialogue (4,955 lines in 407 pools, 86 questions with 250 answers and replies), written to the canon
above: greetings and moments, chat for nine personalities, the hours, weathers, winds and moons, every job, the sky
and the ground, songs, gossip and heart-to-hearts, reactions to what you hold and how you look, call-backs to 89 of
your answers, and a whole children's bank. 25 grown-up stories and 10 children's. The checks: `python
tools/dialogue/dialogue.py --check` and `python tools/stories/check.py`.

## Verified (2026-10-10)

- 13 unit tests (`gradlew test`), including `talk/TalkTest`: pools by context, placeholders that can't be filled,
  questions by their conditions, friendship levels, and the shipped bank (every personality and job has lines, every
  remembered answer has its call-backs).
- `gradlew runClientGameTest -PskyTests=Cirri,Sky,Talk -PtestHeap=2560m -PcompatMods=<the VillageFriends pack>` passes
  inside the full modpack (Village Friends 2.29.0 and RPG 1.1.0, End Friends 0.3.0, Nether Friends 0.5.0, Not-So-Vanilla
  Mobs 1.5.0, Plata Clan 1.2.0, Cave Expansion 1.0.0, Ocean Expansion 1.0.0, Sea Friends 0.2.0, Turning Seasons 1.1.0).
  The Talk test, in the seed-20261010 village (Driftwhistle): the title card on arriving; 16 Cirri whose partner names
  them back and a child who knows Mum and Dad; right-click opens the window, they hover in front of you (3.3 blocks),
  every topic answers with its placeholders filled; an offer made and carried out (the way to the Wind Stone); a sky
  scale loved (+20), cobblestone not (-8); the news of a real birth ("Noa has a baby! Little Jaro..."); a
  heart-to-heart naming their partner; a whole story told, ending with their gift; the Journal's memories, About and
  story notes; a child's play, family, sky and ground; the Skymerchant's Trade button opening the wares; a busy Cirri
  excusing themselves; a sorry accepted; two neighbours meeting to chat with bubbles; the Evensong (10 of 13 circling
  over the court within 16-28 s); Cirri swimming out beside a whale; everyone sheltering from thunder; a birth as news;
  a close friend flying over with a present; the animation pack (126 clips) loaded.
- Film: `-PskyFilm`, then `python tools/film.py build/film/sky-life.mp4 sky-life`.
