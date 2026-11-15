#!/usr/bin/env python3
"""T4: express a circuit's inversion block (AND levels 2, 3) as functions of N (16-point tables).
    python3 ownInv.py FILE"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import inv6 as I  # noqa
from rank2 import load, analyse  # noqa
from boolflux import core  # noqa
c = load(sys.argv[1]); n = c.n
T, lg, la, fa, ba, V, X = analyse(c)
Nx = [I.p256(x, 17) for x in range(256)]
def as16(t):
    f = {}
    for x in range(256):
        v = (t >> x) & 1; k = I.IDX[Nx[x]]
        if f.setdefault(k, v) != v: return None
    return sum(v << k for k, v in f.items())
for s in fa:
    if la[s] < 2: continue
    op, a, b = c.gates[s - n]
    print('AND sig %d AL%d GL%d: out %s  ops %s %s' % (s, la[s], lg[s], hex(as16(T[s]) or 0) if as16(T[s]) is not None else None,
          hex(as16(T[a])) if as16(T[a]) is not None else None, hex(as16(T[b])) if as16(T[b]) is not None else None))
A2 = sorted(as16(T[s]) for s in fa if la[s] == 2)
print('A2 functions', [hex(q) for q in A2], json.dumps(A2))
