"""X3b x3b_pairjunk.py: junk of the gamma = 0 witnesses of all rank <= 2 tensors, and of compatible pairs.
A rank-2 tensor u1(x)v1 + u2(x)v2 (u = 8-bit x-mask, v = 4-bit n-mask in the bits b = (0, 2, 4, 5) of n) has
witness (l_u1 + lam_v2)(l_u2 + lam_v1): x-junk = l_u1 l_u2 (depends only on the x-plane, mod linear),
n-junk = lam_v1 lam_v2 (only on the n-plane).  x-junk coordinates (c3, c5, c9) (univariate coefficients);
n-junk residue mod span(1, N, n) (zero = free for a BMP middle).
Counts, per class mod M8 of singleton-coset tensors (pairs whose cosets sum into M8):
pairs with n-junk sum free, and among them those whose x-junk sum has c5 != 0 (reaches stage 1's x^5 dims)."""
import numpy as np, os, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies/H1'))
sys.path.insert(0, str(Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies/G'))
sys.path.insert(0, str(Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies/C'))
import xag
from xag import coeff, ONES, NC, nC
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
Z = np.load(D + 'x3b/singleton_classes.npz')
# also members and semis for comparison: recompute all tensors' cosets is in x3b_pairs; here singletons only
T, C, K = Z['tensor'], Z['coset'], Z['cls']
par = [bin(i).count('1') & 1 for i in range(256)]
L = [sum(par[u & x] << x for x in range(256)) for u in range(256)]          # l_u truth tables
# n-bit forms
from gfinv import gpow
nn = [gpow(x, 238, 8) if x else 0 for x in range(256)]
bits = (0, 2, 4, 5)
LN = [sum((par[sum(((v >> j) & 1) << bits[j] for j in range(4)) & nn[x]]) << x for x in range(256)) for v in range(16)]
# x-plane junk table
def plane_key(a, b):
    s = sorted((a, b, a ^ b)); return (s[0] << 16) | (s[1] << 8) | s[2]
xj = {}
for a in range(1, 256):
    for b in range(a + 1, 256):
        if (a ^ b) < b: continue
        t = L[a] & L[b]
        xj[plane_key(a, b)] = (coeff(t, 3), coeff(t, 5), coeff(t, 9))
print('x-planes', len(xj), flush=True)
# n-junk residue mod span(1, N, n)
B = {}
for v in [ONES] + list(NC) + list(nC):
    while v:
        h = v.bit_length() - 1
        if h in B: v ^= B[h]
        else: B[h] = v; break
BH = sorted(B, reverse=True)
def resid(t):                      # canonical residue: distinct leading bits, processed high -> low
    for h in BH:
        if (t >> h) & 1: t ^= B[h]
    return t
nj = {}; nid = {0: 0}
for a in range(1, 16):
    for b in range(a + 1, 16):
        if (a ^ b) < b: continue
        r = resid(LN[a] & LN[b])
        if r not in nid: nid[r] = len(nid)
        nj[plane_key(a, b)] = nid[r]
print('n-planes', len(nj), 'distinct n-junk residues', len(nid), ' free n-planes', sum(1 for v in nj.values() if v == 0), flush=True)
# n-junk residues form a space? record ids -> residues for xor
res_of = {i: r for r, i in nid.items()}
# per-tensor planes
def planes(t):
    rows = [(t >> (8 * j)) & 255 for j in range(4)]
    cols = [sum(((rows[j] >> i) & 1) << j for j in range(4)) for i in range(8)]
    def pl(vs):
        nz = [v for v in vs if v]
        a = nz[0]; b = next((v for v in nz if v != a), None)
        return None if b is None else plane_key(a, b)
    return pl(rows), pl(cols)
c5 = np.zeros(len(T), dtype=np.int64); xjv = np.zeros(len(T), dtype=np.int64); njr = []
for i, t in enumerate(T.tolist()):
    px, pn = planes(t)
    if px is None:                   # rank 1: no junk
        njr.append(0); continue
    c3_, c5_, c9_ = xj[px]
    c5[i] = c5_; xjv[i] = c3_ | (c5_ << 8) | (c9_ << 16)
    njr.append(res_of[nj[pn]])
print('per-tensor junk done', flush=True)
rid = {0: 0}
nja = np.array([rid.setdefault(r, len(rid)) for r in njr], dtype=np.int64)
njr = nja
print('distinct n-junk residues among singleton tensors:', len(rid), ' tensors with free n-junk:', int((njr == 0).sum()))
# pairs in one class with n-junk SUM free: n-junk residues are vectors; sum free iff equal residues
key = K.astype(np.int64) * 1000003 + nja
order = np.lexsort((c5, key))
k2, c52 = key[order], c5[order]
uk, st, cnt = np.unique(k2, return_index=True, return_counts=True)
free_pairs = int((cnt * (cnt - 1) // 2).sum())
# among them, pairs with equal c5 (x^5 junk cancels)
kk = k2 * 0 + k2  # composite (key, c5)
comp = np.unique(np.stack([k2, c52]), axis=1, return_counts=True)[1]
same_c5 = int((comp * (comp - 1) // 2).sum())
print('compatible singleton pairs (same class mod M8) with n-junk sum free (equal residues):', free_pairs)
print('   of which x^5 part of the x-junk sum is nonzero:', free_pairs - same_c5, ' zero:', same_c5)
print('   (pairs with both n-junks free:', int(((njr == 0) * 1).sum()), 'tensors with free n-junk)')
