"""Validation for zdfs2.py: every last-layer product of FILE (GF(4)-norm, given gamma) must equal
a member (z, zeta) of track C\x27s model modulo E (agent H1)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "C"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gf, qmc, wsat, xag
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
        idx.setdefault(En.nf(wsat.member_table(M, A, s)), []).append((z, zeta))
c, ands, outs, ot = xag.parse(f)
top = max(A["level"] for A in ands)
found = [idx.get(En.nf(A["tab"])) for A in ands if A["level"] == top]
print(Path(f).name, "gamma", gam, "last products matched to members:", sum(1 for x in found if x), "/", len(found))
print("z values:", [x[0][0] if x else None for x in found])
