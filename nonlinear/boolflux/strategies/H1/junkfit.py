"""Fit the x-quadratic junk coefficients of GF(4)-norm members (agent H1): for exponent e in the
cosets of 3, 5, 9 find (i, j) with c_e(member) = kappa * z^i * zeta^j for all members (gamma none),
and for gamma != 0 the deviation c_e(gamma) - c_e(none)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cond27, xag
from cond27 import gf, MU5
def coset(e):
    c=[]
    while e not in c: c.append(e); e = 2*e % 255
    return c
mem = [(z, zt) for z in range(1, 256, 5) for zt in MU5]
for g in sys.argv[1:]:
    tabs = {m: cond27.member_table(m[0], m[1], g) for m in mem}
    for base in (3, 5, 9, 17):
        for e in coset(base):
            vals = {m: xag.coeff(tabs[m], e) for m in mem}
            if all(v == 0 for v in vals.values()):
                print(g, "class", base, "e", e, "always 0"); break
            found = None
            for i in range(255):
                for j in range(5):
                    ks = set()
                    for (z, zt), v in vals.items():
                        f = gf.mul(gf.power(z, i), gf.power(zt, j))
                        ks.add(gf.mul(v, gf.INV[f]) if f else None)
                        if len(ks) > 1: break
                    if len(ks) == 1: found = (i, j, ks.pop()); break
                if found: break
            print(g, "class", base, "e", e, "c_e = kappa z^i zeta^j:", found)
            if found: break
