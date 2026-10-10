"""Who lives in a sky village: the roster the game spawns when the village is placed.

Every home holds a couple (a woman and a man, sleeping over the first two cushions) and, in a large
nest, their two children; a twin nest holds two couples. Each job's work spot is given to a grown-up
(shuffled with the layout's seed), so most villagers work and a few simply live there. Cloud Koi are
released at every koi pool.

Entries are in layout space (x and z from the village centre, y from the court floor):
  {"type": "cirri", "gender": "f"|"m", "child": bool, "bed": [x, y, z], "job": str, "work": [x, y, z] | null,
   "mother": index | -1}
  {"type": "cloud_koi", "bed": [x, y, z]}
"""
import random

KIDS = {'nest_house_large': 2}


def roster(lay, seed):
    rng = random.Random(seed)
    out, adults = [], []
    for plot in lay.plots:
        if plot.spec.get('role') != 'home':
            continue
        beds = [s['pos'] for s in plot.spots() if s['kind'] == 'sleep']
        kids = KIDS.get(plot.name, 0) if len(beds) >= 4 else 0
        grown, young = beds[:len(beds) - kids], beds[len(beds) - kids:]
        mothers = []
        for i, bed in enumerate(grown):
            female = i % 2 == 0
            out.append({'type': 'cirri', 'gender': 'f' if female else 'm', 'child': False, 'bed': bed, 'job': '', 'work': None,
                        'mother': -1})
            adults.append(len(out) - 1)
            if female:
                mothers.append(len(out) - 1)
        for bed in young:
            out.append({'type': 'cirri', 'gender': rng.choice('fm'), 'child': True, 'bed': bed, 'job': '', 'work': None,
                        'mother': mothers[0] if mothers else -1})
    works = [(plot.spec.get('job'), s['pos']) for plot in lay.plots for s in plot.spots()
             if s['kind'] == 'work' and plot.spec.get('job')]
    rng.shuffle(adults)
    for k, (job, pos) in enumerate(works):
        if k < len(adults):
            out[adults[k]]['job'] = job
            out[adults[k]]['work'] = pos
        else:
            # more jobs than grown-ups: a worker who lives by the court
            out.append({'type': 'cirri', 'gender': rng.choice('fm'), 'child': False, 'bed': None, 'job': job, 'work': pos,
                        'mother': -1})
    for pos in lay.koi:
        for _ in range(lay.program.koi):
            out.append({'type': 'cloud_koi', 'bed': [pos[0], pos[1] + 1, pos[2]]})
    return out
