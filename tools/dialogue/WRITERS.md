# Writing the Cirri's lines

A style guide for anyone adding lines for the Cirri. Lines are hand-written, one per line, in plain-text pools that
the game picks from by context. `docs/DIALOGUE.md` is the canon (read all of it first), then `docs/PEOPLE.md` and
`docs/VILLAGES.md` for the people and their villages.

## The bar

The sister mod Village Friends has the best dialogue in this modpack: its pools (tools/dialogue/lines and
questions in that repo) set the quality bar. Take the craft, never the content: they are villagers, not Cirri.

What makes a line good:

- **Specific and concrete.** A real detail of their life (a koi that sulks, a bridge plank that squeaks for walkers,
  the weaver's comb, a sky peach going soft, Vell bringing the smell of rain) beats a general feeling.
- **Characterful.** Each personality must sound like itself: the dreamer drifts off mid-thought, the proud one is
  a little grand, the busy one talks while doing three things, the shy one trails off ("...if that's all right").
- **Varied.** Mix lengths (a few words to three sentences), openings (don't start ten lines with "The" or "I"),
  questions, jokes, sayings, small confessions. Vary rhythm. No two lines may say the same thing in other words.
- **Of the sky.** Everything is seen from the air: clouds are below them, rain falls *past* them, they look down
  on birds. They have never walked. Use the canon (the Four Winds, veils, the Evensong, the Old Singers, koi,
  the Courtesy, the Lengthening, nests, the Wind Stone) often but not in every line.
- **Warm toward the player**, more so at higher friendship; teasing, curious, kind. `{player}` in at most one line
  in six.
- **Fits the pool.** A `greet.*` line is a hello (it opens a conversation). A `chat.*` line is a thought, a bit of
  news about their day, a story or an opinion. A line in a `rain` pool must make sense in rain, and so on. A line
  must stand alone: the player never sees what came before it.

## Rules (the checker enforces most of them)

- Plain ASCII: straight quotes and apostrophes, no em or en dashes, no `--`. At most 220 characters a line.
- **No gendered words at all**: he, she, him, her, his, hers, husband, wife, son, daughter, brother, sister, boy, girl,
  man, woman, lady, sir. Speakers may be women or men and the line must fit either. Use names, "they", or the
  placeholders (`{partner}` is the first name of the one they share a nest with, `{spouse}` is "husband" or "wife").
  Whales and koi are "it" or "they". Children may say Mum and Dad.
- No modern words (okay, cool, stuff, guys, awesome, yeah). No swearing. No real-world places, religions or brands.
- Only the placeholders listed in docs/DIALOGUE.md, only in the pools where they are allowed.
- No duplicates (exact or near). Don't reuse an example from this guide.

Check a file as you go, and fix everything it reports:

    python tools/dialogue/dialogue.py --file <file>.txt

Format of a lines file:

    # what this file is (a comment line starts with "# ")

    ## greet.dawn
    Fair wind! Aure's barely awake and neither am I.
    Another line.
