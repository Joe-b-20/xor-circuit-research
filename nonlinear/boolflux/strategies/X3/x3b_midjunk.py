"""X3b x3b_midjunk.py: can a 5-AND middle absorb the n-junk of non-member products?
n-junk of a rank-2 tensor's gamma = 0 witness = lam_v1(n) lam_v2(n) (depends on the n-plane only), a function
of N.  Members (n-plane a GF(4)-line) have norm-class junk, which never lands in G's 30 achievable extra
middle classes (H2 vjunk.py) - that is why BMP is WLOG for members.  Here: all 35 n-planes, and all
sums of two n-plane junks, tested for {free} / {in the 30 classes} with G's exact_mid.search.
Then recount X3b's compatible singleton pairs (x3b_pairjunk) with n-junk sum in {0} + ACH."""
import sys, os
import numpy as np
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1', 'X3'):
    sys.path.insert(0, str(S / d))
import xag
from xag import NC, nC
from gfinv import gpow
import exact_mid as EM
Nv = [gpow(x, 17, 8) if x else 0 for x in range(256)]
pts = sorted(set(Nv)); assert len(pts) == 16
rep = [Nv.index(p) for p in pts]
def to16(t): return sum(((t >> rep[i]) & 1) << i for i in range(16))
ONES16 = 0xFFFF
INP = [to16(t) for t in NC]; NTAB = [to16(t) for t in nC]
EM.INP = INP
base = EM.Sp([ONES16] + INP + NTAB); assert len(base.rows) == 9
comp = []; sp = base.copy()
for x in range(1 << 16):
    if sp.add(x): comp.append(x)
    if len(comp) == 7: break
ACH = set()
for c in range(1, 128):
    v = 0
    for i in range(7):
        if (c >> i) & 1: v ^= comp[i]
    if EM.search(NTAB + [v]): ACH.add(base.red(v))
print('achievable extra middle classes (5-AND):', len(ACH), flush=True)
par = [bin(i).count('1') & 1 for i in range(256)]
nn = [gpow(x, 238, 8) if x else 0 for x in range(256)]
bits = (0, 2, 4, 5)
LN = [sum(par[sum(((v >> j) & 1) << bits[j] for j in range(4)) & nn[x]] << x for x in range(256)) for v in range(16)]
# K-ratio of an n-plane: GF(4)-line iff v1, v2, v1^v2 correspond to s, ws, w^2 s  (test via junk class later)
planes = []
for a in range(1, 16):
    for b in range(a + 1, 16):
        if (a ^ b) < b: continue
        planes.append((a, b, base.red(to16(LN[a] & LN[b]))))
free = [p for p in planes if p[2] == 0]; inach = [p for p in planes if p[2] in ACH]
print('n-planes:', len(planes), ' junk free:', len(free), ' junk in the 30 classes:', len(inach), flush=True)
pair_ok = 0; pair_ach = 0; tot = 0
for i in range(len(planes)):
    for j in range(i, len(planes)):
        r = planes[i][2] ^ planes[j][2]; tot += 1
        if r == 0: pair_ok += 1
        elif r in ACH: pair_ach += 1
print('n-plane pairs (unordered, incl. equal):', tot, ' sum free:', pair_ok, ' sum in the 30 classes:', pair_ach)
# distinct junk residues and their span
B = EM.Sp([p[2] for p in planes])
print('dim span of the 35 n-plane junks mod span(1, N, n):', len(B.rows), '(quotient V0 / span(1,N,n) has dim 7)')
