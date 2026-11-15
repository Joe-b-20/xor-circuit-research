#!/usr/bin/env python3
"""X1b: registry of known U subspaces (x1b_ufilter.py) of circuits with A <= AMAX.

    python3 x1b_uregistry.py OUT.json TABLE.jsonl [--amax 28] [--archive CAMPAIGN_DIR]... PATH...
OUT.json = list of U hashes; TABLE.jsonl = one row per circuit (file, metrics, U info)."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1b_ufilter as UF
from boolflux.hub.common import load, metrics

a = sys.argv[1:]
out = Path(a[0]); tab = Path(a[1]); amax = 28; arch = []; paths = []
i = 2
while i < len(a):
    if a[i] == '--amax': amax = int(a[i + 1]); i += 2
    elif a[i] == '--archive': arch.append(a[i + 1]); i += 2
    else: paths.append(a[i]); i += 1
fl = []
for p in paths:
    p = Path(p)
    fl += sorted(list(p.glob('*.bfx')) + list(p.glob('*.circ.txt'))) if p.is_dir() else [p]
for d in arch:
    ad = Path(d) / 'archive'
    for j in ad.glob('*.json'):
        if j.name == 'cells.json': continue
        try: r = json.loads(j.read_text())
        except Exception: continue
        if r.get('A', 99) <= amax: fl.append(ad / (r['id'] + '.bfx'))
known = set(json.loads(out.read_text())) if out.exists() else set()
t0 = time.time(); n = 0
with open(tab, 'a') as tf:
    for f in fl:
        try:
            c = load(f); m = metrics(c)
            if m[0] > amax: continue
            r = UF.ujunk(c=c)
        except Exception as e:
            print('skip', f, repr(e)); continue
        n += 1; known.add(r['U'])
        tf.write(json.dumps({'file': str(f), 'm': m, **r}) + '\n')
out.write_text(json.dumps(sorted(known)))
print('%d circuits, %d distinct U, %.1f s' % (n, len(known), time.time() - t0))
