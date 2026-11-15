#!/usr/bin/env python3
"""T4: greedy search over per-output bottom designs (build46 plans) on a fixed GD-11 front:
repeatedly add the (output, design) that lowers the AND count most while the skeleton bound stays
<= CAP; junk ANDs are shared through the growing span.  Several processing orders.
    python3 greedy46.py FILE OUTDIR [CAP] [ROUNDS_RANDOM]"""
import sys, json, os, random, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import build46 as B  # noqa
from coversearch import bound  # noqa

DESIGNS = ['p3 %d %d' % ab for ab in itertools.combinations(range(4), 2)] + \
          ['p2 0 1 2 3', 'p2 0 2 1 3', 'p2 0 3 1 2']


def evaluate(f, plans, order):
    os.environ['T4_ORDER'] = ','.join(map(str, order))
    try:
        sk, ok = B.build(f, plans)
    except ValueError:
        return None
    if not ok: return None
    b, arr, ol = bound(sk, 8)
    return len(sk['ands']), b, sk


def greedy(f, cap, order, rng=None):
    plans = {}
    cur = evaluate(f, plans, order)
    while True:
        best = None
        cands = [(k, d) for k in range(8) if k not in plans for d in DESIGNS]
        if rng: rng.shuffle(cands)
        for k, d in cands:
            p2 = dict(plans); p2[k] = d
            ordk = [x for x in order if x in p2] + [x for x in order if x not in p2]
            r = evaluate(f, p2, ordk)
            if r is None or r[1] > cap: continue
            if r[0] < cur[0] and (best is None or r[0] < best[0][0]):
                best = (r, k, d)
        if best is None: return plans, cur
        cur, k, d = best
        plans[k] = d
        print(json.dumps({'order': order, 'plans': plans, 'ANDs': cur[0], 'bound': cur[1]}), flush=True)


if __name__ == '__main__':
    f, outdir = sys.argv[1], Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 11
    nr = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    results = []
    orders = [list(range(8))]
    rng = random.Random(1)
    for _ in range(nr):
        o = list(range(8)); rng.shuffle(o); orders.append(o)
    best = None
    for i, o in enumerate(orders):
        plans, cur = greedy(f, cap, o, rng if i else None)
        rec = {'order': o, 'plans': plans, 'ANDs': cur[0], 'bound': cur[1]}
        print(json.dumps({'final': rec}), flush=True)
        if best is None or cur[0] < best[0]:
            best = (cur[0], rec, cur[2])
            (outdir / 'best.json').write_text(json.dumps({'rec': rec, 'ands': [[hex(L), hex(R)] for L, R in cur[2]['ands']],
                                                          'outputs': [hex(F) for F in cur[2]['outputs']]}))
    print(json.dumps({'best': best[1]}), flush=True)
