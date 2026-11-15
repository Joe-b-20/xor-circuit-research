#!/usr/bin/env python3
"""T4: skeleton depth bound of build47 skeletons for every design line and realisation pick.
    python3 scan47.py DONOR DESIGNS.jsonl [maxpick]"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import build47 as B  # noqa
from coversearch import bound  # noqa
donor, dfile = sys.argv[1], sys.argv[2]
maxpick = int(sys.argv[3]) if len(sys.argv) > 3 else 4
designs = [json.loads(l) for l in open(dfile) if l.startswith('{')]
for i, d in enumerate(designs):
    if not d.get('best7'): continue
    for pk in range(maxpick):
        try:
            sk, ok, b, nA, nb = B.build(donor, d, pk)
        except AssertionError as e:
            print(json.dumps({'design': i, 'pick': pk, 'error': str(e)[:80]})); continue
        _, arr, ol = bound(sk, 8)
        lv = arr[9:]
        print(json.dumps({'design': i, 'pick': pk, 'ok': ok, 'bound': b, 'A': nA, 'bottom': nb,
                          'st1': lv[:9], 'A2': lv[9:12], 'A3': lv[12:16], 'bot_max': max(lv[16:]), 'outs': ol}), flush=True)
