"""Positive control for zdfs2.py: the 15 umizame last products, mapped to C-model members
(z, zeta) (zcheck.py), pass zdfs2\x27s exact test over umizame\x27s E and have pi-rank 7 (the prune
threshold), while every 14-subset fails (agent H1)."""
import sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "C"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gf, qmc, wsat, xag
from exp_stage3 import tables_of
from kj_search import Model
from zdfs import MU5, CUBE_ROOT
f = "/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt"
M = Model(None, "hard"); l1, inv = tables_of(f)
E = [gf.ONES] + gf.X + l1 + inv
En = qmc.Normal(E); ET = qmc.Normal(E + M.T); Tn = [En.nf(t) for t in M.T]
idx = {}; mem = {}
for z in range(1, 256):
    for zeta in MU5:
        s = CUBE_ROOT[zeta]; Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
        t = wsat.member_table(M, A, s); idx.setdefault(En.nf(t), (z, zeta)); mem[(z, zeta)] = t
c, ands, outs, ot = xag.parse(f)
S = [idx[En.nf(A["tab"])] for A in ands if A["level"] == 5]
ok = lambda SS: all(gf.Span([En.nf(mem[m]) for m in SS]).contains(t) for t in Tn)
print("full layer passes:", ok(S), " pi-rank:", gf.Span([ET.nf(mem[m]) for m in S]).dim(),
      " some 14-subset passes:", any(ok(SS) for SS in itertools.combinations(S, 14)))
