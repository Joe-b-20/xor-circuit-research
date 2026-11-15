"""Check the n-block equations of a GF(4)-norm last layer on real circuits (agent H1):
for each output j with last-layer coefficients c_jm (unique, ANDs independent):
  (i)  sum_m c_jm Y_m = b_j  (the class-127 coefficient of output j, i.e. coeff(y_j, 239))
  (ii) sum_m c_jm z_m = 0    (z = zeta Y: the class-47 component cancels)
with (z_m, zeta_m) from track C\x27s member model (zcheck mapping), Y = z / zeta.
Also prints the per-class parities eps_{P,j}."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "C"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gf, qmc, wsat, xag
from xag import deps
from exp_stage3 import tables_of
from fam_check import gp
from kj_search import Model
from zdfs import MU5, CUBE_ROOT
f, gam = sys.argv[1], sys.argv[2]
M = Model(gp(int(gam)) if gam != "none" else None, "hard")
l1, inv = tables_of(f)
En = qmc.Normal([gf.ONES] + gf.X + l1 + inv)
idx = {}
for z in range(1, 256):
    for zeta in MU5:
        s = CUBE_ROOT[zeta]; Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
        idx.setdefault(En.nf(wsat.member_table(M, A, s)), (z, zeta))
c, ands, outs, ot = xag.parse(f)
top = max(A["level"] for A in ands)
last = [k for k, A in enumerate(ands) if A["level"] == top]
zz = {k: idx[En.nf(ands[k]["tab"])] for k in last}
ok1 = ok2 = True
for j, o in enumerate(outs):
    sY = sz = 0; eps = {}
    for k in deps(o):
        if k in zz:
            z, zeta = zz[k]; sY ^= gf.mul(z, gf.INV[zeta]); sz ^= z
            eps[zeta] = eps.get(zeta, 0) ^ 1
    b = xag.coeff(ot[j], 239)
    ok1 &= (sY == b); ok2 &= (sz == 0)
    print("y%d: sumY=%3d coeff239=%3d sumz=%3d eps=%s" % (j, sY, b, sz, {xag.LOG[k]: v for k, v in sorted(eps.items())}))
print("(i) holds:", ok1, " (ii) holds:", ok2)
