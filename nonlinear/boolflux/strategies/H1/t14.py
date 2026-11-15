"""Full 14 -> 13 test for a verified 9 + 5 + 14 circuit (agent H1), stage 1 and middle FIXED:
 (a) every 13-subset of the last layer: d = 0 would be a 27 directly;
 (b) every pair with d = 1: search every single product over O (O2, optionally OV) closing it;
 (c) every triple with d = 2 not containing a d = 1 pair (those are implied by (b)): search
     products whose pi-values span T-bar (two new products).
A hit prints CANDIDATE (27 ANDs; build by adding the product, then aes_check).
usage: python3 t14.py FILE [--ov] --out LOG"""
import itertools
import json
import subprocess
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xag
from xag import gf

f = sys.argv[1]; ov = '--ov' in sys.argv
out = sys.argv[sys.argv.index('--out') + 1]
c, a, o, T = xag.parse(f)
r = [(xag.role(A), A['tab']) for A in a]
pre = [t for ro, t in r if ro in ('S1', 'MID')]
last = [t for ro, t in r if ro not in ('S1', 'MID')]


def d(drop):
    S = xag.span([gf.ONES], gf.X, pre, [t for k, t in enumerate(last) if k not in drop]); d0 = S.dim()
    for t in T: S.add(t)
    return S.dim() - d0


log = open(out, 'a')
rec = {'file': Path(f).name, 'k': len(last), 'roles': {ro: sum(1 for x, _ in r if x == ro) for ro, _ in r}}
singles = [d((i,)) for i in range(len(last))]
rec['d_single'] = singles
if 0 in singles: rec['event'] = 'CANDIDATE-13subset'
pairs1 = [p for p in itertools.combinations(range(len(last)), 2) if d(p) <= 1]
triples2 = [t for t in itertools.combinations(range(len(last)), 3)
            if d(t) <= 2 and not any(set(p) <= set(t) for p in pairs1)]
rec.update({'pairs_d1': pairs1, 'triples_d2': triples2})
print(json.dumps(rec), file=log, flush=True)
jobs = [(p, 'O2') for p in pairs1] + [(t, 'O2') for t in triples2]
if ov: jobs += [(p, 'OV') for p in pairs1]
for drop, O in jobs:
    tot = 1 << (18 if O == 'O2' else 24)
    step = 1 << 17
    reach = set()
    for s in range(0, tot, step):
        res = subprocess.run([sys.executable, str(HERE / 'fixk.py'), '--S', f, '--M', f, '--L', f,
                              '--drop', ','.join(map(str, drop)), '--O', O, '--chunk', '%d:%d' % (s, s + step)],
                             capture_output=True, text=True)
        line = res.stdout.strip().splitlines()[-1]
        dd = json.loads(line); reach |= set(dd.get('reach_idx', []))
    need = 1 if len(drop) == 2 else 2
    r2 = {'file': Path(f).name, 'drop': drop, 'O': O, 'reach_idx': sorted(reach)}
    if len(reach) >= need: r2['event'] = 'CANDIDATE'
    print(json.dumps(r2), file=log, flush=True)
print(json.dumps({'file': Path(f).name, 'event': 'done'}), file=log, flush=True)
