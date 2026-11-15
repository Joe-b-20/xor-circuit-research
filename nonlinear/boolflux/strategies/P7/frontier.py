#!/usr/bin/env python3
"""P7: frontier of P7/found per target from the sidecars: Pareto in (G, GD) and in (A, G, GD) (AD = 4 here),
strict / tradeoff class against the reference, path_certified.   frontier.py [T09|T10]"""
import json, glob, sys
from pathlib import Path
REF = {'T09': (45, 4, 141, 12), 'T10': (59, 4, 159, 10)}
rows = {}
for f in glob.glob(str(Path.home() / 'xs-campaigns/2026-11-15-targets/P7/found/*.json')):
    d = json.load(open(f))
    k = (d['A'], d['AD'], d['G'], d['GD'])
    rows.setdefault(d['target'], {}).setdefault(k, []).append((Path(f).name, d.get('path_certified')))
for t in (sys.argv[1:] or sorted(rows)):
    A0, AD0, G0, GD0 = REF[t]; R = rows.get(t, {})
    pts = sorted(R)
    def dom(p, q):  # q dominates p in (G, GD)
        return q[2] <= p[2] and q[3] <= p[3] and (q[2], q[3]) != (p[2], p[3])
    def dom4(p, q):
        return all(q[i] <= p[i] for i in range(4)) and q != p
    print('%s (ref %d/%d/%d/%d): %d distinct tuples' % (t, A0, AD0, G0, GD0, len(pts)))
    for p in pts:
        g2 = not any(dom(p, q) for q in pts); g4 = not any(dom4(p, q) for q in pts)
        if not g4: continue
        strict = p[0] <= A0 and p[1] <= AD0 and p[2] <= G0 and p[3] <= GD0 and (p[2] < G0 or p[3] < GD0)
        print('  %d/%d/%d/%d  %s%s  %s  certified=%s' % (p + (('strict' if strict else 'in-limits'),
              ' [G,GD-Pareto]' if g2 else ' [A-Pareto]', R[p][0][0], R[p][0][1])))
