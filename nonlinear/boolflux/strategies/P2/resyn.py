#!/usr/bin/env python3
"""P2: bottom resynthesis candidates -> circuits.  For every feasible decomposition in an orbsearch
JSON (or fwalk/bsat3 JSONL), build front + bottom with depthsynth (parent = the front circuit, so
its gates are reused), verify, and keep the best by (GD, G).

    python3 resyn.py FRONT CANDS.json[l] OUTDIR [--max N] [--D D]
"""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as Bd   # noqa: E402
import orbit as O    # noqa: E402
from boolflux import core   # noqa: E402

front, cands, outdir = sys.argv[1:4]
mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 10 ** 9
KEEP = int(sys.argv[sys.argv.index('--keep') + 1]) if '--keep' in sys.argv else 10
Dcap = int(sys.argv[sys.argv.index('--D') + 1]) if '--D' in sys.argv else 99
out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
decs = []
txt = Path(cands).read_text()
if cands.endswith('.jsonl'):
    for l in txt.splitlines():
        r = json.loads(l)
        if r.get('dec'): decs.append(r['dec'])
else:
    for r in json.loads(txt):
        if Path(r['front']).resolve() != Path(front).resolve():
            continue
        for f in r['feasible']: decs.append(f['dec'])
print(len(decs), 'candidates', flush=True)
model = core.Model.load('nist')
res = []
keep = []
for i, d in enumerate(decs[:mx]):
    d = [tuple(p) for p in d]
    if not O.check(d): print('bad dec', i); continue
    try:
        c = Bd.build(front, d, parent=True)
    except Exception as e:
        print('build failed', i, e); continue
    m = c.metrics(model)
    inc = sum(bin(O.lvec(w)).count('1') for al, g, w in d)
    res.append((m['GD'], m['G'], i, inc))
    if m['GD'] <= Dcap:
        keep.append((m['G'], i, c)); keep.sort(key=lambda z: z[:2]); del keep[KEEP:]
    if i % 20 == 0: print(i, sorted(res)[:5], flush=True)
res.sort()
for G, i, c in keep:
    (out / ('c%04d-g%d.circ.txt' % (i, G))).write_text(core.write_ncff(c, model, comments=['P2 resyn front %s cand %d of %s' % (front, i, cands)]))
print('best', res[:20])
json.dump(res, open(out / 'summary.json', 'w'))
