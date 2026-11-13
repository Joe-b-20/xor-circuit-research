"""Machine review: check, on the named circuits, the consequence of J9 + Corollary 7.2 used in REVIEW.md
(every gate charged to two sheets is a proper ancestor of an event gate). Read-only measurement.
usage: python3 rv_cone.py"""
import json
import os
from rv_measure import MCB, MCSHEET, ST, evalc, read_kste, read_ncff, ROOT


def cone(name, g):
    n = 32
    v = evalc(n, g)
    N = len(v)
    onode = {m: v.index(m) for m in MCSHEET}
    anc = {}
    for j in range(8):
        st, A = [onode[m] for m, t in MCSHEET.items() if t == j], set()
        while st:
            x = st.pop()
            if x not in A:
                A.add(x)
                if x >= n:
                    st.extend(g[x - n])
        anc[j] = A
    mu = {x: sum(1 for j in range(8) if x in anc[j] and v[x] & MCB[j]) for x in range(n, N)}
    ev = [n + i for i, (a, b) in enumerate(g)
          if any(v[a] & MCB[c] and not v[n + i] & MCB[c] for c in range(8))]
    pa = set()
    for e in ev:
        st = list(g[e - n])
        while st:
            x = st.pop()
            if x not in pa:
                pa.add(x)
                if x >= n:
                    st.extend(g[x - n])
    pa = {x for x in pa if x >= n}
    dbl = [x for x in mu if mu[x] >= 2]
    R = sum(mu[x] - 1 for x in dbl)
    print("%s: G %d, events %d, gates with mu>=2: %d (R = %d), all proper ancestors of an event: %s, "
          "proper-ancestor cone of events: %d gates" % (name, len(g), len(ev), len(dbl), R,
                                                        all(x in pa for x in dbl), len(pa)))


for fn, ln in (("circuits_3.txt", 1451), ("circuits_3.txt", 3001), ("circuits_3.txt", 7451),
               ("circuits_3.txt", 7651), ("circuits_2.txt", 783)):
    cone("%s:%d" % (fn, ln), read_kste(fn, ln))
cone("r88", read_ncff(os.path.join(ROOT, "circuits", "aes-mixcolumns", "aes-mixcolumns-xor88-depth5.circ.txt")))
for nm in ("block", "wire"):
    cone("witness " + nm, [tuple(x) for x in json.load(open(os.path.join(ST, "cancel", "witness",
                                                                         "witness_mc_%s.json" % nm)))])
