#!/usr/bin/env python3
"""X2 hub operator gjoin: join (hub/join.py, both roles, all cut levels) of the input with partners taken from
the input's GOAL pool instead of the front.  Goal from env X2_GOAL (set by hub/scheduler_goal.py; default: the
goal nearest to the input).  Common CLI of hub/ops.py.

Why (L1, 2026-11-15 [C] counts on the hub logs): op_join's partner list is the front first (K = 4 copies per
cell), truncated to 300, so stepping-stone / nursery circuits are almost never partners.  Here: partners = the
records nearest to the goal (scalar <= best + 10 or stepping stones, up to 80, one record per tuple first, then
second copies), then up to 40 random cell minima of the same A class (|A - A_in| <= 1); candidates the archive
would place, best goal key first, at most --max-cands."""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))      # nonlinear/
from boolflux.hub import ops as HO           # noqa: E402
from boolflux.hub import join as J           # noqa: E402
from boolflux.hub import goals as GL         # noqa: E402
from boolflux.hub.common import core, metrics   # noqa: E402


def op_gjoin(ar, args, rng, out):
    X = J.Prepared(ar.circuit(args.inp), args.inp)
    mi = metrics(X.c)
    gname = os.environ.get('X2_GOAL')
    if gname not in GL.BY_NAME:
        gname = min(GL.NAMES, key=lambda n: (GL.key(GL.goal(n), mi), n))
    g = GL.goal(gname)
    rows = []
    for i, r in ar.rec.items():
        if i == args.inp: continue
        m = (r['A'], r['AD'], r['G'], r['GD'])
        rows.append((GL.scalar(g, m), m, i, GL.stepping(g, m)))
    smin = min(s for s, m, i, st in rows)
    near = sorted([x for x in rows if x[0] <= smin + 10 or x[3]], key=lambda x: (x[0], x[1]))
    seen_t = set(); first = []; second = []
    for s, m, i, st in near:
        (second if m in seen_t else first).append(i); seen_t.add(m)
    partners = (first + second)[:80]
    others = [ids[0] for k, ids in ar.cells.items() if ids and abs(k[0] - mi[0]) <= 1 and ids[0] not in partners
              and ids[0] != args.inp]
    rng.shuffle(others)
    partners += others[:40]
    t0 = time.time(); tried = 0; kept = []; seen = set()
    for pid in partners:
        if time.time() - t0 > args.seconds: break
        P = J.Prepared(ar.circuit(pid), pid)
        for F, B in ((X, P), (P, X)):
            for c, LX, LY, nint in J.join_all(F, B):
                tried += 1
                m = metrics(c)
                if not ar.would_place(m): continue
                k = core.to_kernel(c)
                if k in seen: continue
                seen.add(k)
                kept.append(((GL.key(g, m), m), c, {'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY, 'interface_gates': nint}))
    kept.sort(key=lambda x: x[0])
    kept = kept[:args.max_cands]
    return [c for k, c, d in kept], {'goal': gname, 'partners': len(partners), 'tried': tried,
                                     'joins': [d for k, c, d in kept]}


HO.OPS['gjoin'] = op_gjoin

if __name__ == '__main__':
    sys.exit(HO.main('gjoin'))
