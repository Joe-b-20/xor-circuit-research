#!/usr/bin/env python3
"""How short is the shortest flip sequence to a merge?  Breadth-first over flips (both directions of every
factor-sharing pair) from the circuit's product program, depth <= D, counting states with a merge
(equal usage + shared factor).   python3 t_bfs.py D MAXSTATES FILE..."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X
from boolflux.hub.common import load, metrics


def pairs(p):
    d = {}
    for k, (L, R) in p.ands.items():
        for a in set(X.Prog.span3(L, R)): d.setdefault(a, []).append(k)
    for a, ks in d.items():
        for i in ks:
            for j in ks:
                if i != j: yield i, j, a


def merges(p):
    u = p.usage(); out = []
    sp = {k: set(X.Prog.span3(*p.ands[k])) for k in p.ands}
    g = {}
    for k, s in u.items(): g.setdefault(s, []).append(k)
    for ks in g.values():
        for x in range(len(ks)):
            for y in range(x + 1, len(ks)):
                if sp[ks[x]] & sp[ks[y]]: out.append((ks[x], ks[y]))
    return out


def key(p):
    return (tuple(sorted((k, v[0], v[1]) for k, v in p.ands.items())), tuple(p.outs))


D = int(sys.argv[1]); MAXS = int(sys.argv[2])
for f in sys.argv[3:]:
    c = load(f); p = X.extract(c); p.reduce(); t0 = time.time()
    level = [(p, [])]; seen = {key(p)}; found = None; nstates = 1
    for d in range(D + 1):
        hits = [(q, path) for q, path in level if merges(q)]
        print('%s %s depth %d: states %d, with a merge %d  (%.1f s)' % (Path(f).name[:40], metrics(c), d, len(level), len(hits), time.time() - t0), flush=True)
        if hits and found is None: found = (d, hits[0][1])
        if d == D or nstates > MAXS: break
        nxt = []
        for q, path in level:
            for i, j, a in pairs(q):
                if q.depends(j, i): continue
                r = q.copy()
                if not r.flip(i, j, a): continue
                k = key(r)
                if k in seen: continue
                seen.add(k); nxt.append((r, path + [(i, j, a)])); nstates += 1
                if nstates > MAXS: break
            if nstates > MAXS: break
        level = nxt
    print('  first merge at depth', found[0] if found else None)
