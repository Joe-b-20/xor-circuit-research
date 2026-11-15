#!/usr/bin/env python3
"""T4: like scan47 but over every 7-AND option (all7) of every design; level-aware choices.
    python3 scan47b.py DONOR DESIGNS.jsonl [min_share]"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import build47 as B  # noqa
from coversearch import bound  # noqa
donor, dfile = sys.argv[1], sys.argv[2]
ms = int(sys.argv[3]) if len(sys.argv) > 3 else 1
designs = [json.loads(l) for l in open(dfile) if l.startswith('{')]
for i, d in enumerate(designs):
    for oi, r in enumerate(d.get('all7') or []):
        if r['share5'] < ms: continue
        d2 = dict(d); d2['best7'] = r
        try:
            sk, ok, b, nA, nb = B.build(donor, d2, 0)
        except AssertionError as e:
            print(json.dumps({'design': i, 'opt': oi, 'error': str(e)[:80]}), flush=True); continue
        _, arr, ol = bound(sk, 8)
        lv = arr[9:]
        print(json.dumps({'design': i, 'opt': oi, 'ok': ok, 'bound': b, 'A': nA, 'A2': lv[9:12], 'A3': lv[12:16], 'outs': ol}), flush=True)
