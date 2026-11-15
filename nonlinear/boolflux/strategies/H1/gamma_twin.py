"""gamma twins (agent H1): keep a layer's member indices (z, zeta) - so the n-block equations
(i)-(ii) of TRICKS 2.2, which do not involve gamma, stay satisfied - and change gamma.
Report the minimal junk the layer then needs:
  Jx = dim(A1 + S + T) - dim(A1 + S), A1 = span(1, x, V0)          (x-quadratic junk, N-junk free)
  J0 = dim(A2 + S + T) - dim(A2 + S), A2 = span(1, x, N, n, Quad)  (N-function junk, x-junk free)
  feasible = T inside span(1, x, V0, Quad, S).
usage: python3 gamma_twin.py FILE1 GAMMA1 FILE2 GAMMA2"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "C"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gf, qmc, wsat, xag
from exp_stage3 import tables_of
from fam_check import gp
from kj_search import Model
from zdfs import MU5, CUBE_ROOT


def model(gam):
    return Model(gp(int(gam)) if gam != "none" else None, "hard")


def table(M, z, zeta):
    s = CUBE_ROOT[zeta]; Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
    return wsat.member_table(M, A, s)


def members_of(f, gam):
    M = model(gam)
    l1, inv = tables_of(f); En = qmc.Normal([gf.ONES] + gf.X + l1 + inv); idx = {}
    for z in range(1, 256):
        for zeta in MU5:
            idx.setdefault(En.nf(table(M, z, zeta)), (z, zeta))
    c, ands, outs, ot = xag.parse(f); top = max(A["level"] for A in ands)
    return [idx[En.nf(A["tab"])] for A in ands if A["level"] == top], ot


V0 = xag.V0
Q = [a & b for i, a in enumerate(gf.X) for b in gf.X[i + 1:]]


def junk(S, gam, T):
    M = model(gam)
    mem = [table(M, z, zeta) for z, zeta in S]
    d = lambda *L: xag.span(*L).dim()
    A1 = [[gf.ONES], gf.X, V0]; A2 = [[gf.ONES], gf.X, xag.NC, xag.nC, Q]
    Jx = d(*A1, mem, T) - d(*A1, mem)
    J0 = d(*A2, mem, T) - d(*A2, mem)
    feas = d(*A1, Q, mem, T) == d(*A1, Q, mem)
    return Jx, J0, feas


if __name__ == '__main__':
    a = sys.argv[1:]
    for f, g0 in ((a[0], a[1]), (a[2], a[3])):
        S, T = members_of(f, g0)
        out = [(gam, junk(S, gam, T)) for gam in ["none"] + [str(17 * i) for i in range(15)]]
        print(Path(f).name[9:30], "own gamma", g0, "->", out)
