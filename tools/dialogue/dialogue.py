"""Compiles the Cirri's handwritten dialogue into src/main/resources/data/skyfriends/dialogue/cirri.json.

The canon (the Cirri's voice, their world, every pool and what it is for) is docs/DIALOGUE.md. Sources are plain
text, easy to write and review:

  tools/dialogue/lines/*.txt       pools of lines, under "## pool.key" headings
  tools/dialogue/questions/*.txt   questions the Cirri ask (and offers they make), with your possible answers

Lines:
    ## work.weaver
    Dawn's the time for combing cirrus. Before Aure wakes it's soft as down.
    # a comment

Questions ("?" asks once ever; "!" is an offer that can come up once a day when its conditions hold):
    ? favourite_wind | when: day
    Q: Which of the Four Winds would you fly with, if you could?
    - Aure, the dawn wind :: Aure! Dew on your face and the whole sky blushing. @likes:aure {points:1} [SPARKLE]
    - Borre, the storm :: Borre? You're braver than you look, walker. @likes:borre {points:1} [EXCLAIM]

Answers are "Label :: reply". After the reply, "@flag" is remembered about you (and the pool
"remember.<flag>", with ":" as "_", can call back to it), "{effect}" does something (see talk/TalkWorld.java),
"{points:N}" adds friendship and "[MOOD]" picks the bubble. "when:" lists context tags that must all hold ("!rain"
means not raining, "level:4" means friendship level 4 or more, "a|b" means either).

    python tools/dialogue/dialogue.py               # compile
    python tools/dialogue/dialogue.py --check       # validate, and confirm the compiled file is current
    python tools/dialogue/dialogue.py --stats       # counts by pool family
    python tools/dialogue/dialogue.py --file x.txt  # check one source file on its own (writers use this)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
OUT = PROJECT / 'src/main/resources/data/skyfriends/dialogue/cirri.json'

PLACEHOLDERS = {'player', 'name', 'village', 'job', 'wind', 'moon', 'day', 'item', 'partner', 'spouse', 'child', 'mother',
                'father', 'friend', 'neighbour', 'coworker', 'crush', 'who', 'other', 'gift'}
MOODS = {'EXCLAIM', 'QUESTION', 'HEART', 'NOTE', 'ANGER', 'SWEAT', 'DOTS', 'SLEEP', 'SPARKLE', 'IDEA', 'GLOOM', 'BLUSH'}
EFFECTS = {'heal', 'peach', 'slowfall', 'lantern', 'scale', 'feather', 'flower', 'mend_held', 'lift', 'song', 'dry', 'emerald_tip'}
MAX_LINE, MAX_LABEL = 220, 30

PERSONALITIES = ['dreamer', 'merry', 'gentle', 'shy', 'proud', 'restless', 'busy', 'wise', 'curious']
CHILD_PERSONALITIES = ['playful', 'shy', 'curious', 'cheeky', 'dreamy', 'fidgety']
JOBS = ['harpist', 'weaver', 'gardener', 'bellkeeper', 'lamplighter', 'skymerchant', 'windkeeper', 'none']
PERIODS = ['dawn', 'morning', 'noon', 'afternoon', 'evening', 'night', 'late']
WEATHERS = ['clear', 'rain', 'thunder', 'snow']
WINDS = ['aure', 'sefa', 'vell', 'borre']
MOONS = ['full', 'waning_gibbous', 'last_quarter', 'waning_crescent', 'new', 'waxing_crescent', 'first_quarter', 'waxing_gibbous']
BANDS = ['stranger', 'acquaintance', 'friend', 'close', 'best']
ROUTINES = ['work', 'gather', 'soar', 'chat', 'evensong', 'escort', 'shelter', 'idle']
CHILD_ROUTINES = ['play', 'follow', 'evensong', 'shelter', 'idle']
THINGS = ['whale', 'koi', 'children', 'harp', 'evensong']
HELD = ['weapon', 'pickaxe', 'tool', 'fishing_rod', 'map', 'spyglass', 'book', 'flower', 'emerald', 'diamond', 'gold', 'fire',
        'lantern', 'bucket', 'food', 'peach', 'treat', 'music', 'flute', 'harp', 'veil', 'scale', 'feather', 'membrane', 'string',
        'amethyst', 'elytra', 'firework', 'breeze', 'cloud', 'sapling', 'potion', 'totem', 'pet']
STATES = ['hurt', 'hungry', 'wet', 'fire', 'dark', 'unarmored', 'diamond', 'golden', 'elytra', 'veil', 'flying', 'edge', 'pumpkin']
CHILD_STATES = ['hurt', 'wet', 'elytra', 'veil', 'flying', 'edge']
NEWS = ['born', 'grew_up', 'passed', 'whale', 'storm', 'visitor', 'gift', 'struck', 'story', 'none']
MOMENTS = ['first_meeting', 'hurt', 'night', 'walk_off', 'busy_off', 'apology_accepted', 'apology_wary', 'gift.loved', 'gift.liked',
           'gift.neutral', 'gift.disliked', 'gift.limit', 'level_up', 'gift.bring']
GENDERED = re.compile(r"\b(he|she|him|her|his|hers|himself|herself|husband|husbands|wife|wives|son|sons|daughter|daughters|brother|"
                      r"brothers|sister|sisters|boy|boys|girl|girls|man|woman|men|women|lady|ladies|gentleman|sir|madam|ma'am)\b", re.I)
MODERN = re.compile(r"\b(okay|ok|cool|guys|stuff|awesome|yeah)\b", re.I)


def pool_keys():
    """Every pool key the game can ask for (remember.* keys are checked against the questions' flags instead)."""
    k = set()
    for p in PERIODS:
        k |= {f'greet.{p}', f'time.{p}', f'baby.time.{p}'}
    for b in BANDS:
        k.add(f'greet.band.{b}')
    for p in PERSONALITIES:
        k |= {f'greet.personality.{p}', f'chat.{p}', f'ground.{p}', f'song.{p}'}
    for p in CHILD_PERSONALITIES:
        k.add(f'baby.{p}')
    for r in ROUTINES:
        k |= {f'greet.routine.{r}', f'routine.{r}'}
    for r in CHILD_ROUTINES:
        k.add(f'baby.routine.{r}')
    for w in WEATHERS:
        k |= {f'weather.{w}', f'baby.weather.{w}'}
        if w != 'clear':   # only bad weather gets its own greetings, work talk and songs
            k |= {f'greet.weather.{w}', f'work.weather.{w}', f'song.weather.{w}'}
    for w in WINDS:
        k |= {f'greet.wind.{w}', f'wind.{w}'}
    for m in MOONS:
        k.add(f'moon.{m}')
    for t in THINGS:
        k |= {f'village.{t}', f'baby.village.{t}'}
    for h in HELD:
        k.add(f'held.{h}')
    for s in STATES:
        k.add(f'player.{s}')
    for s in CHILD_STATES:
        k.add(f'baby.player.{s}')
    for j in JOBS:
        k.add(f'work.{j}')
    for n in NEWS:
        k.add(f'news.{n}')
    k |= {'chat.general', 'chat.new', 'chat.friendly', 'chat.close', 'work.on', 'work.off',
          'sky.general', 'sky.winds', 'sky.clouds', 'sky.whales', 'sky.koi', 'sky.stars', 'sky.storms', 'sky.veils', 'sky.history',
          'ground.general', 'ground.villages', 'ground.wonders', 'ground.fears',
          'song.general', 'song.evensong', 'song.night', 'song.harpist',
          'heart.partner', 'heart.single', 'heart.crush', 'heart.parent',
          'mention.partner', 'mention.child', 'mention.friend', 'mention.coworker', 'mention.neighbour',
          'trade.open', 'evensong.invite', 'whale.sighted'}
    for m in MOMENTS:
        k |= {m, 'baby.' + m}
    k |= {'baby.greet', 'baby.chat', 'baby.play', 'baby.sky', 'baby.ground', 'baby.song', 'baby.song.night', 'baby.secret',
          'baby.family', 'baby.family.mum', 'baby.family.dad', 'baby.held'}
    return k


# placeholders that only make sense in some pools
ONLY_IN = {'crush': ('heart.crush',), 'who': ('news.',), 'other': ('news.',), 'gift': ('gift.', 'baby.gift.'),
           'mother': ('baby.',), 'father': ('baby.',)}


def when_tags():
    t = set(PERIODS) | {'day', 'night', 'adult', 'child', 'friends', 'newcomers'} | set(WEATHERS)
    t |= {'personality:' + p for p in PERSONALITIES + CHILD_PERSONALITIES} | {'job:' + j for j in JOBS}
    t |= {'routine:' + r for r in ROUTINES + CHILD_ROUTINES} | {'wind:' + w for w in WINDS} | {'moon:' + m for m in MOONS}
    t |= {'held:' + h for h in HELD} | set(STATES) | set(THINGS) | {'partnered', 'parent', 'damaged'}
    return t


def fail(where, message):
    raise SystemExit(f'{where}: {message}')


def check_text(where, text, limit=MAX_LINE, key=''):
    if not text.strip():
        fail(where, 'empty text')
    if len(text) > limit:
        fail(where, f'too long ({len(text)} > {limit}): {text[:60]}...')
    if any(ord(c) > 126 or ord(c) < 32 for c in text):
        fail(where, f'plain ASCII only (no curly quotes, dashes or symbols): {text[:60]}')
    if '--' in text:
        fail(where, 'no dashes between clauses: use a comma, colon or full stop')
    for name in re.findall(r'\{([a-z_]+)\}', text):
        if name not in PLACEHOLDERS:
            fail(where, f'unknown placeholder {{{name}}}')
        only = ONLY_IN.get(name)
        if only and key and not key.startswith(only):
            fail(where, f'{{{name}}} only works in {", ".join(only)} pools')
    if text.count('{') != text.count('}'):
        fail(where, 'unbalanced braces')
    bare = re.sub(r'\{[a-z_]+\}', '', text)
    m = GENDERED.search(bare)
    if m:
        fail(where, f'gendered word "{m.group(0)}": the Cirri never assume anyone\'s gender (use names, they, or {{spouse}})')
    m = MODERN.search(bare)
    if m:
        fail(where, f'modern word "{m.group(0)}"')


def read_lines(paths):
    pools, known = {}, pool_keys()
    for path in paths:
        key = None
        for n, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            line = raw.strip()
            where = f'{path.name}:{n}'
            if not line or line.startswith('# ') or line == '#':
                continue
            if line.startswith('## '):
                key = line[3:].strip()
                if not re.fullmatch(r'[a-z0-9_.]+', key):
                    fail(where, f'bad pool key {key!r}')
                if key not in known and not key.startswith('remember.'):
                    fail(where, f'unknown pool {key!r} (see docs/DIALOGUE.md, "Pools")')
                pools.setdefault(key, [])
                continue
            if key is None:
                fail(where, 'line before any "## pool" heading')
            check_text(where, line, key=key)
            pools[key].append(line)
    return pools


ANSWER = re.compile(r'^-\s*(.+?)\s*::\s*(.+)$')


def parse_answer(where, text):
    m = ANSWER.match(text)
    if not m:
        fail(where, 'answers look like "- Label :: reply"')
    label, reply = m.group(1).strip(), m.group(2).strip()
    answer = {'label': label}
    for flag in re.findall(r'\s@([a-z0-9_:]+)', ' ' + reply):
        answer['flag'] = flag
    reply = re.sub(r'\s*@[a-z0-9_:]+', '', reply)
    for name, value in re.findall(r'\{(?:effect:)?([a-z_]+)(?::(-?\d+))?\}', reply):
        if name == 'points':
            answer['points'] = int(value or 1)
        elif name in EFFECTS:
            answer['effect'] = name
        elif name in PLACEHOLDERS:
            continue
        else:
            fail(where, f'unknown effect {{{name}}}')
    reply = re.sub(r'\s*\{(?:effect:)?(?:points|' + '|'.join(EFFECTS) + r')(?::-?\d+)?\}', '', reply)
    mood = re.search(r'\s*\[([A-Z]+)\]\s*', reply)
    if mood:
        if mood.group(1) not in MOODS:
            fail(where, f'unknown mood [{mood.group(1)}]')
        answer['mood'] = mood.group(1)
        reply = (reply[:mood.start()] + ' ' + reply[mood.end():]).strip()
    check_text(where, label, MAX_LABEL)
    check_text(where, reply)
    answer['reply'] = reply.strip()
    return answer


def read_questions(paths):
    questions, ids, tags = [], set(), when_tags()
    for path in paths:
        current = None
        for n, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            line = raw.strip()
            where = f'{path.name}:{n}'
            if not line or line.startswith('# ') or line == '#':
                continue
            if line[0] in '?!' and (len(line) == 1 or line[1] == ' '):
                head = [part.strip() for part in re.split(r'\s\|\s', line[1:])]
                qid = head[0]
                if not re.fullmatch(r'[a-z0-9_]{2,40}', qid):
                    fail(where, f'bad question id {qid!r}')
                if qid in ids:
                    fail(where, f'duplicate question id {qid}')
                ids.add(qid)
                when = []
                for part in head[1:]:
                    if part.startswith('when:'):
                        when += part[5:].split()
                    else:
                        fail(where, f'unknown question option {part!r}')
                for cond in when:
                    if cond.startswith('level:'):
                        if not cond[6:].isdigit():
                            fail(where, f'bad level condition {cond}')
                        continue
                    for option in cond.lstrip('!').split('|'):
                        if option not in tags:
                            fail(where, f'unknown when tag {option!r}')
                current = {'id': qid, 'offer': line[0] == '!', 'when': when, 'ask': [], 'answers': []}
                questions.append(current)
                continue
            if current is None:
                fail(where, 'text before a "? id" heading')
            if line.startswith('Q:'):
                text = line[2:].strip()
                check_text(where, text)
                current['ask'].append(text)
            elif line.startswith('-'):
                current['answers'].append(parse_answer(where, line))
            else:
                fail(where, f'expected "Q:" or "- answer": {line[:40]}')
    for q in questions:
        if not q['ask'] or not 2 <= len(q['answers']) <= 4:
            fail(q['id'], 'each question needs a "Q:" line and 2-4 answers')
        if q['offer'] and 'child' in q['when']:
            fail(q['id'], 'only grown-ups make offers')
    return questions


def compile_all(line_paths, question_paths, whole=True):
    pools, questions = read_lines(line_paths), read_questions(question_paths)
    seen = Counter(line for lines in pools.values() for line in lines)
    duplicates = [line for line, count in seen.items() if count > 1]
    if duplicates:
        fail('lines', f'{len(duplicates)} duplicate lines, e.g. {duplicates[0]!r}')
    if whole:
        flags = {a['flag'].replace(':', '_') for q in questions for a in q['answers'] if a.get('flag')}
        for key in pools:
            if key.startswith('remember.') and key[9:] not in flags:
                fail(key, 'no answer sets this flag')
    return {'format': 1, 'pools': pools, 'questions': questions}


def count(data):
    lines = sum(len(v) for v in data['pools'].values())
    asks = sum(len(q['ask']) for q in data['questions'])
    answers = sum(len(q['answers']) for q in data['questions'])
    return lines, asks, answers


def render(data):
    return json.dumps(data, ensure_ascii=False, indent=0, separators=(',', ':')) + '\n'


def main():
    args = sys.argv[1:]
    if '--file' in args:
        name = args[args.index('--file') + 1]
        path = next((p for p in (ROOT / 'lines' / name, ROOT / 'questions' / name, Path(name)) if p.exists()), None)
        if path is None:
            fail(name, 'no such file')
        is_q = path.parent.name == 'questions'
        data = compile_all([] if is_q else [path], [path] if is_q else [], whole=False)
        lines, asks, answers = count(data)
        print(f'{path.name}: OK, {lines} lines in {len(data["pools"])} pools, {len(data["questions"])} questions')
        return
    data = compile_all(sorted((ROOT / 'lines').glob('*.txt')), sorted((ROOT / 'questions').glob('*.txt')))
    lines, asks, answers = count(data)
    total = lines + asks + answers * 2
    if '--stats' in args:
        families = Counter()
        for key, values in data['pools'].items():
            families[key.split('.')[0] if not key.startswith('baby.') else 'baby.' + key.split('.')[1]] += len(values)
        for family, n in families.most_common():
            print(f'{family:18} {n}')
        print(f'questions          {len(data["questions"])} ({asks} asks, {answers} answers)')
        missing = sorted(pool_keys() - set(data['pools']))
        if missing:
            print(f'{len(missing)} pools still empty: {", ".join(missing[:40])}{" ..." if len(missing) > 40 else ""}')
    if '--check' in args:
        if not OUT.exists() or OUT.read_text(encoding='utf-8') != render(data):
            raise SystemExit('cirri.json is out of date: run python tools/dialogue/dialogue.py')
        print(f'Dialogue is up to date: {total} pieces of dialogue ({lines} lines, {len(data["questions"])} questions with {answers} answers).')
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data), encoding='utf-8')
    print(f'Dialogue: {total} pieces of dialogue: {lines} lines in {len(data["pools"])} pools, {len(data["questions"])} questions '
          f'with {answers} answers and replies.')


if __name__ == '__main__':
    main()
