"""per cut over exit-free reduced MC circuits: min far, sigma range among min-far circuits,
min (far - sigma) with witness; non-MC line counts; named references."""
import os, json
from collections import Counter
import olib
from scanlib import sources, WP, WM
minfar = {}; ties = {}; mfs = {}; nonmc = Counter(); n_exitfree = Counter()
REFS = {("kste/circuits_3.txt", 13114), ("kste/circuits_3.txt", 15380), ("kste/circuits_2.txt", 313),
        ("kste/circuits_2.txt", 360), ("kste/circuits_2.txt", 213), ("kste/circuits_2.txt", 260), ("kste/circuits_1.txt", 40)}
refout = []
for src, ln, g in sources():
    comp, red, _ = olib.check(g, olib.ROWS)
    if not comp or not red:
        nonmc[(src, comp, red, len(g))] += 1
        continue
    vals = olib.values(g); ops = [(vals[a], vals[b]) for a, b in g]
    cases = [("P", b, "-", vals, ops, olib.PBLOCK[b], WP[b]) for b in range(8)]
    for order in ("fwd", "rev"):
        Tm, Tops, outs = olib.transpose(g, olib.ROWS, order=order)
        rv, rops, rg = olib.reduce_mirror(Tm, Tops)
        cases += [("M", k, order, rv, rops, olib.MBLOCK[k], WM[k]) for k in range(8)]
    for kind, k, order, vv, oo, low, W in cases:
        st = olib.split(vv, oo, 32, low)
        sig = st["e"] - W["dimW"]
        if (src, ln) in REFS:
            refout.append((src, ln, kind, k, order, len(g), st["f"], st["h"], st["e"], st["N"], st["x"], st["far"], sig))
        if st["x"]:
            continue
        key = (kind, k); n_exitfree[key] += 1
        far = st["far"]
        if key not in minfar or far < minfar[key]:
            minfar[key] = far; ties[key] = Counter()
        if far == minfar[key]:
            ties[key][sig] += 1
        d = far - sig
        if key not in mfs or d < mfs[key][0]:
            mfs[key] = (d, far, sig, src, ln, order, st["f"], st["h"], st["e"])
print("non-MC or non-reduced:", dict(nonmc) if len(nonmc) < 20 else Counter((k[0], k[1], k[2]) for k in nonmc.elements()))
for key in sorted(minfar):
    print(key, "exitfree circuits(+orders)", n_exitfree[key], "minfar", minfar[key], "sigma among minfar", dict(ties[key]), "min(far-sigma)", mfs[key])
for r in refout:
    if r[2] == "P" and r[3] == 7 or r[2] == "M" and r[3] in (1, 3, 4):
        print("ref", r)
