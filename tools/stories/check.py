"""Check the Cirri's story books: src/main/resources/data/skyfriends/stories/*.json.

    python tools/stories/check.py            check both books, print counts
    python tools/stories/check.py cirri      check one
    python tools/stories/check.py --part tools/stories/parts/x.json --book cirri    check a writer's part

The game reads the same files (dev.skyfriends.talk.StoryBook). Two books, cirri (grown-ups) and cirri_child:

    {
      "bank": "<file name>",
      "locked": ["what they say if you open the Story tab before they know you", ...],   at least 4
      "stories": [
        {
          "id": "lantern_dark", "title": "The Lantern That Went Dark", "jobs": ["lamplighter"],
          "intro": "They bring it up (Story tab, first).",
          "requests": [
            {"id": "glow", "title": "A brighter flame", "item": "minecraft:glowstone_dust", "count": 8,
             "prompt": "What they ask for.", "thanks": "What they say when you bring it."}
          ],
          "waiting": "After the first request, before they are ready to say more.",
          "ready": "When they are ready to tell you the rest.",
          "confide": "The heart of the story.",
          "endings": [
            {"id": "relight", "label": "Light it again", "text": "What they decide.", "memory": "For the Journal."},
            {"id": "let_rest", "label": "Let it rest", "text": "...", "memory": "..."}
          ],
          "gift": {"item": "skyfriends:sky_scale", "count": 1}
        }
      ]
    }

Grown-ups' stories have three requests (the first opens the story, the other two can be done any time after),
"waiting", "ready", "confide" and two "endings". Children's stories are short: one request, then the gift; no
waiting, ready, confide or endings. "jobs" ties a story to jobs (a Cirri with that job is likelier to tell it);
empty means anyone. Item ids are "minecraft:<id>" or "skyfriends:<id>". Text may use *asterisks* for what they do
("*loops once, slowly*"), single quotes inside text, and the placeholders {player} {name} {village} {job} {wind}.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'dialogue'))
from dialogue import GENDERED, MODERN  # noqa: E402  the same rules as the dialogue

ROOT = HERE.parents[1]
DIR = ROOT / 'src' / 'main' / 'resources' / 'data' / 'skyfriends' / 'stories'
BOOKS = ['cirri', 'cirri_child']
CHILD = {'cirri_child'}
JOBS = ['harpist', 'weaver', 'gardener', 'bellkeeper', 'lamplighter', 'skymerchant', 'windkeeper']
MIN_STORIES = {'cirri': 24, 'cirri_child': 10}
PLACEHOLDERS = {'player', 'name', 'village', 'job', 'wind'}
VANILLA = set((HERE / 'item_ids.txt').read_text().split())
LANG = json.loads((ROOT / 'src/main/resources/assets/skyfriends/lang/en_us.json').read_text(encoding='utf-8'))
MOD = {k.split('.')[2] for k in LANG if k.startswith(('item.skyfriends.', 'block.skyfriends.')) and k.count('.') == 2}
NOT_ASKED = {'bedrock', 'barrier', 'command_block', 'chain_command_block', 'repeating_command_block',
             'command_block_minecart', 'structure_block', 'structure_void', 'jigsaw', 'light', 'debug_stick',
             'knowledge_book', 'petrified_oak_slab', 'end_portal_frame', 'reinforced_deepslate', 'budding_amethyst',
             'spawner', 'trial_spawner', 'vault', 'dragon_egg', 'player_head', 'test_block', 'test_instance_block',
             'farmland', 'dirt_path', 'frogspawn', 'infested_stone', 'suspicious_sand', 'suspicious_gravel', 'wind_stone'}
NOT_GIVEN = NOT_ASKED | {'elytra', 'nether_star', 'beacon', 'totem_of_undying', 'enchanted_golden_apple', 'netherite_block',
                         'netherite_ingot', 'netherite_scrap', 'ancient_debris', 'heavy_core', 'mace', 'dragon_head',
                         'trident', 'conduit', 'heart_of_the_sea', 'diamond_block', 'emerald_block', 'enchanted_book',
                         'cirrus_veil'}
LIMITS = {'label': 32, 'title': 40, 'intro': 420, 'prompt': 240, 'thanks': 240, 'waiting': 300,
          'ready': 300, 'confide': 480, 'text': 420, 'memory': 120, 'locked': 200}
ID = re.compile(r'[a-z0-9_]{1,40}')


def text(where, s, kind, problems):
    if not isinstance(s, str) or not s.strip():
        problems.append(f'{where}: missing text')
        return
    if len(s) > LIMITS[kind]:
        problems.append(f'{where}: {len(s)} chars (max {LIMITS[kind]}): {s[:60]}...')
    for p in re.findall(r'\{([^}]*)\}', s):
        if p not in PLACEHOLDERS:
            problems.append(f'{where}: unknown placeholder {{{p}}}')
    if s.count('{') != s.count('}'):
        problems.append(f'{where}: unbalanced braces')
    bare = re.sub(r'\{[a-z_]+\}', '', s)
    m = GENDERED.search(bare)
    if m:
        problems.append(f'{where}: gendered word "{m.group(0)}" (speakers may be women or men; never assume a gender): {s}')
    m = MODERN.search(bare)
    if m:
        problems.append(f'{where}: modern word "{m.group(0)}"')
    if '"' in s:
        problems.append(f'{where}: use single quotes inside text')
    if any(ord(c) > 126 or ord(c) < 32 for c in s):
        problems.append(f'{where}: plain ASCII only (no curly quotes, dashes or line breaks): {s[:50]}')
    if '--' in s:
        problems.append(f'{where}: no dashes between clauses')


def item(where, value, banned, problems):
    if not isinstance(value, str) or ':' not in value:
        problems.append(f'{where}: item ids are "minecraft:<id>" or "skyfriends:<id>": {value!r}')
        return
    ns, iid = value.split(':', 1)
    known = VANILLA if ns == 'minecraft' else MOD if ns == 'skyfriends' else set()
    if iid not in known:
        problems.append(f'{where}: unknown item "{value}"')
    if iid in banned or iid.endswith('_spawn_egg'):
        problems.append(f'{where}: "{value}" is not allowed here')


def check(name, path=None, part=False):
    path = path or DIR / f'{name}.json'
    problems = []
    try:
        book = json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        return [f'{path.name}: {e}'], 0, 0
    if not part and book.get('bank') != name:
        problems.append(f'"bank" must be "{name}"')
    child = name in CHILD

    locked = book.get('locked', [])
    if len(locked) < (0 if part else 4):
        problems.append('"locked" needs at least 4 lines')
    for i, s in enumerate(locked):
        text(f'locked[{i}]', s, 'locked', problems)

    stories = book.get('stories', [])
    if not part and len(stories) < MIN_STORIES[name]:
        problems.append(f'"stories": needs at least {MIN_STORIES[name]} (has {len(stories)})')
    ids, words = set(), 0
    job_stories = {j: 0 for j in JOBS}
    anyone = 0
    for i, s in enumerate(stories):
        sid = s.get('id', '')
        where = f'stories[{i}:{sid}]'
        if not ID.fullmatch(sid) or sid in ids:
            problems.append(f'{where}: bad or repeated id')
        ids.add(sid)
        text(f'{where}.title', s.get('title'), 'title', problems)
        text(f'{where}.intro', s.get('intro'), 'intro', problems)
        sj = s.get('jobs', [])
        if not sj:
            anyone += 1
        if child and sj:
            problems.append(f'{where}: children have no jobs')
        for j in sj:
            if j not in JOBS:
                problems.append(f'{where}: unknown job "{j}"')
            else:
                job_stories[j] += 1
        reqs = s.get('requests', [])
        if len(reqs) != (1 if child else 3):
            problems.append(f'{where}: needs {1 if child else 3} request(s)')
        rids = set()
        for k, r in enumerate(reqs):
            rw = f'{where}.requests[{k}]'
            if not ID.fullmatch(r.get('id', '')) or r.get('id') in rids:
                problems.append(f'{rw}: bad or repeated id')
            rids.add(r.get('id'))
            text(f'{rw}.title', r.get('title'), 'title', problems)
            text(f'{rw}.prompt', r.get('prompt'), 'prompt', problems)
            text(f'{rw}.thanks', r.get('thanks'), 'thanks', problems)
            item(f'{rw}.item', r.get('item'), NOT_ASKED, problems)
            c = r.get('count')
            if not isinstance(c, int) or not 1 <= c <= 64:
                problems.append(f'{rw}: count must be 1..64')
            words += sum(len(str(r.get(f, '')).split()) for f in ('prompt', 'thanks'))
        if child:
            for f in ('waiting', 'ready', 'confide', 'endings'):
                if f in s:
                    problems.append(f'{where}: children\'s stories have no "{f}"')
        else:
            for f in ('waiting', 'ready', 'confide'):
                text(f'{where}.{f}', s.get(f), f, problems)
                words += len(str(s.get(f, '')).split())
            ends = s.get('endings', [])
            if len(ends) != 2:
                problems.append(f'{where}: needs exactly 2 endings')
            eids = set()
            for k, e in enumerate(ends):
                ew = f'{where}.endings[{k}]'
                if not ID.fullmatch(e.get('id', '')) or e.get('id') in eids:
                    problems.append(f'{ew}: bad or repeated id')
                eids.add(e.get('id'))
                text(f'{ew}.label', e.get('label'), 'label', problems)
                text(f'{ew}.text', e.get('text'), 'text', problems)
                text(f'{ew}.memory', e.get('memory'), 'memory', problems)
                words += len(str(e.get('text', '')).split())
        g = s.get('gift', {})
        item(f'{where}.gift', g.get('item'), NOT_GIVEN, problems)
        gc = g.get('count')
        if not isinstance(gc, int) or not 1 <= gc <= 16:
            problems.append(f'{where}.gift: count must be 1..16')
        words += len(str(s.get('intro', '')).split())
    if not child and not part:
        for j, n in job_stories.items():
            if n < 2:
                problems.append(f'"stories": the {j} needs at least 2 (has {n})')
        if anyone < 8:
            problems.append(f'"stories": at least 8 must be for anyone (no "jobs"; has {anyone})')
    titles = [s.get('title') for s in stories]
    for t in {t for t in titles if titles.count(t) > 1}:
        problems.append(f'repeated title: {t}')
    return problems, len(stories), words


def main():
    if '--part' in sys.argv:
        # a writer's part of a book: python tools/stories/check.py --part tools/stories/parts/x.json --book cirri
        path = Path(sys.argv[sys.argv.index('--part') + 1])
        name = sys.argv[sys.argv.index('--book') + 1]
        problems, count, words = check(name, path, part=True)
        print(f'{path.name}: {count} stories, {words} words' + (f', {len(problems)} problems' if problems else ', ok'))
        for p in problems[:80]:
            print('   ', p)
        sys.exit(1 if problems else 0)
    names = sys.argv[1:] or BOOKS
    bad = 0
    for name in names:
        problems, count, words = check(name)
        print(f'{name}: {count} stories, {words} words' + (f', {len(problems)} problems' if problems else ', ok'))
        for p in problems[:80]:
            print('   ', p)
        bad += len(problems)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
