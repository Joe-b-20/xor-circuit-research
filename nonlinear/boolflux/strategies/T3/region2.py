#!/usr/bin/env python3
"""T3: list the region-2 XOR gates (AND level 2, not AND) of an AD3 circuit with their role:
R(c) = Tr(c x^84), Q(w) = Tr(w x^170), V+S1 = Tr(c x^84) + element of span{1, x, A1}, etc.
    python3 region2.py CIRCUIT"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, ONES      # noqa: E402
from pairs import and_levels, Basis                      # noqa: E402
from prodswap import RBasis                              # noqa: E402
from gf4basis import RT, QT                              # noqa: E402

c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
S1 = [ONES] + [t[s] for s in range(NS) if al[s] <= 1]
a2 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
Vb = [RT[1 << i] for i in range(8)]
Qb = [QT[w] for w in sorted(set(QT))[:0]]
B1 = Basis(S1); s1 = B1.gens
# coordinates: [S1 basis | V basis (8) | A2 products]
R = RBasis(s1 + Vb + [t[g] for g in a2])
ns = len(s1)
inv = {}
for k, v in RT.items(): inv[v] = k; inv[v ^ ONES] = k
invq = {}
for w, v in QT.items(): invq.setdefault(v, w); invq.setdefault(v ^ ONES, w)
print(metrics(c), 'dim S1', ns)
names = {g: 'P%d' % i for i, g in enumerate(a2)}
for g in range(n, NS):
    op, a, b = c.gates[g - n]
    if op == 8 or al[g] != 2: continue
    r, m = R.reduce(t[g])
    vpart = (m >> ns) & 0xFF; ppart = m >> (ns + 8); spart = m & ((1 << ns) - 1)
    lab = []
    if t[g] in inv: lab.append('R(%d)' % inv[t[g]])
    if t[g] in invq: lab.append('Q(%d)' % invq[t[g]])
    if not lab:
        lab.append('V%s%s%s' % ('*' if vpart else '0', '+P' + ','.join(str(i) for i in range(12) if (ppart >> i) & 1) if ppart else '', '+S1' if spart else ''))
    def nm(x):
        return names.get(x, 's%d' % x) if al[x] == 2 or x in names else 'L%d' % al[x]
    print('s%d = %s(%s, %s)  %s' % (g, 'XOR' if op == 6 else 'XNOR' if op == 9 else 'NOT', nm(a), nm(b), ' '.join(lab)))
