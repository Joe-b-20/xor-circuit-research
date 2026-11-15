#!/usr/bin/env python3
"""Rank mc1 results: distinct (metrics, structure), dominance against an archive's cell minima and the pinned
NIST set, distance to the user's goals B-G.   judge_found.py CAMPAIGN JSONL [JSONL ...]"""
import json, sys
from pathlib import Path
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux.hub.archive import Archive
from boolflux.hub.common import leq, published

GOALS = {'B': (28, 4, 130, 22, 'eq'), 'C': (28, 5, 127, 19, 'eq'), 'D': (32, 4, 116, 19, 'eqad'), 'E': (32, 6, 102, 31, 'le'),
         'F': (35, 3, 138, 26, 'eqad'), 'G': (44, 4, 140, 11, 'le')}


def gdist(m, g):
    A, AD, G, GD, kind = g
    if kind == 'eq' and (m[0] != A or m[1] != AD): return None
    if kind == 'eqad' and (m[0] > A or m[1] != AD): return None
    if kind == 'le' and (m[0] > A or m[1] > AD): return None
    return max(0, m[2] - G) + max(0, m[3] - GD)


ar = Archive(sys.argv[1]); pts = ar.points() + list(published())
rows = {}
for fn in sys.argv[2:]:
    for l in open(fn):
        d = json.loads(l)
        if 'm_new' not in d or not d.get('ok'): continue
        m = tuple(d['m_new'])
        rows.setdefault(m, d)
out = []
for m, d in sorted(rows.items()):
    dom = any(leq(u, m) for u in pts)
    slack = min([m[2] - u[2] for u in pts if leq((u[0], u[1], 0, u[3]), (m[0], m[1], 0, m[3]))] or [None]) if dom else None
    gd = {g: gdist(m, v) for g, v in GOALS.items() if gdist(m, v) is not None}
    out.append((m, dom, slack, gd, d['id'], d['m'], d.get('file')))
for r in out:
    print('%-16s %s G-excess %-4s goals %s  from %s %s' % ('/'.join(map(str, r[0])), 'dominated' if r[1] else 'NEW', r[2], r[3], r[4], r[5]))
