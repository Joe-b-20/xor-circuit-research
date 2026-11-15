#!/usr/bin/env python3
"""T3: region-1 anatomy (XOR gates of AND level 1): each gate's function written as
(N-part over the 2-dim T-space and the rest of N) + x-linear part + 'Q' if it has a quadratic part
outside span{N bits}; consumers (level-2 AND operand / region 2 / region 1).
    python3 region1.py CIRCUIT"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                   # noqa: E402
from boolflux.hub.common import load, metrics, ONES, _gpow, _bit_tables   # noqa: E402
from pairs import and_levels, Basis                         # noqa: E402
from prodswap import RBasis                                 # noqa: E402

c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
X = core.input_tables(8)
Nt = Basis([v for v in _bit_tables(lambda x: _gpow(x, 17)) if v not in (0, ONES)]).gens
# T = N + N^4 functionals: span of bits of x^17 + x^68
Tt = Basis([v for v in _bit_tables(lambda x: _gpow(x, 17) ^ _gpow(x, 68)) if v not in (0, ONES)]).gens
A1 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 1]
R = RBasis([ONES] + X + Tt + Nt + [t[g] for g in A1])
cons = {s: [] for s in range(NS)}
for g in range(n, NS):
    op, a, b = c.gates[g - n]
    for x in {a, b}: cons[x].append(g)
print(metrics(c), 'T dims', len(Tt), 'A1', len(A1))
cnt = {}
for g in range(n, NS):
    op, a, b = c.gates[g - n]
    if op == 8 or al[g] != 1: continue
    r, m = R.reduce(t[g])
    xs = (m >> 1) & 0xFF; tp = (m >> 9) & 3; npart = (m >> 11) & 0xF; ap = m >> 15
    kinds = set()
    for u in cons[g]:
        if c.gates[u - n][0] == 8: kinds.add('AND%d' % al[u])
        else: kinds.add('R%d' % al[u])
    desc = '%s%s%s%s' % ('T' if tp else '', 'N' if npart else '', 'x' if xs else '', '+A1' if ap else '')
    key = (desc, ','.join(sorted(kinds)))
    cnt[key] = cnt.get(key, 0) + 1
for k, v in sorted(cnt.items(), key=lambda x: -x[1]): print('%3d  form %-8s used by %s' % (v, k[0], k[1]))
