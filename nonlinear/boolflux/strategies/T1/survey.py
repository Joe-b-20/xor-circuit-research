#!/usr/bin/env python3
"""T1 survey: list archive records near goals B (28/4/<=130/<=22) and C (28/5/<=127/<=19)."""
import json, sys
from pathlib import Path
from collections import Counter

AR = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
recs = {}
for f in AR.glob('*.json'):
    if f.name == 'cells.json': continue
    try: r = json.loads(f.read_text())
    except Exception: continue
    recs[r['id']] = r
print('records', len(recs))
c = Counter((r['A'], r['AD']) for r in recs.values())
print('A,AD counts (A<=30):', sorted((k, v) for k, v in c.items() if k[0] <= 30))

def show(sel, title):
    print('==', title, len(sel))
    for r in sorted(sel, key=lambda r: (r['G'], r['GD'])):
        print('%s %d/%d/%d/%d op=%s par=%s' % (r['id'], r['A'], r['AD'], r['G'], r['GD'], r['operator'], ','.join(r.get('parents') or [])))

show([r for r in recs.values() if r['A'] == 28 and r['AD'] == 4 and r['G'] <= 136], 'B reach 28/4 G<=136')
show([r for r in recs.values() if r['A'] == 28 and r['AD'] == 5 and r['G'] <= 133], 'C reach 28/5 G<=133')
show([r for r in recs.values() if r['A'] == 29 and r['AD'] == 4 and r['G'] <= 132], '29/4 G<=132')
show([r for r in recs.values() if r['A'] == 28 and r['AD'] >= 6], '28/AD>=6')
# pareto (G,GD) per (A,AD)
for key in [(28, 4), (28, 5)]:
    pts = sorted({(r['G'], r['GD']) for r in recs.values() if (r['A'], r['AD']) == key})
    fr = [p for p in pts if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in pts)]
    print('front', key, fr)
