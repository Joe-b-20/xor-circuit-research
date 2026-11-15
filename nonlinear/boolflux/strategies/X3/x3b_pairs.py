"""X3b x3b_pairs.py: all rank <= 2 x(x)n tensors (4 x 8 GF(2) matrices, bit 8j + i as in SEMI.md),
their cosets mod T_b and classes mod M8 (span of the 255 member cosets).  Question: how large is the
family of SINGLETON-coset tensors that can enter a layer only in pairs (or larger sets) whose cosets
sum into M8, as the two non-member products of X1's spangen A28s do?
Output: counts; file x3b/singleton_classes.npz (tensor, coset, class) for later use."""
import numpy as np, os, sys
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
r1 = np.array([sum(((v >> j) & 1) * (u << (8 * j)) for j in range(4)) for u in range(1, 256) for v in range(1, 16)],
              dtype=np.int64)
assert len(np.unique(r1)) == 3825
s = (r1[:, None] ^ r1[None, :]).ravel()
allt = np.unique(np.concatenate([r1, s[s != 0]]))
print('rank<=2 nonzero tensors:', len(allt))
te = [(int(p), int(v, 16)) for p, v in (z.split(':') for z in open(D + 'bil_tb.txt').read().split('TE')[1].split())]
def red(a, basis):
    a = a.copy()
    for p, v in basis:
        m = (a >> p) & 1
        a ^= m * v
    return a
cos = red(allt, te)
uc, inv, cnt = np.unique(cos, return_inverse=True, return_counts=True)
sz = cnt[inv]
hist = {int(k): int(v) for k, v in zip(*np.unique(cnt, return_counts=True))}
print('coset size histogram (cosets):', hist)
memc = uc[cnt == 5]
# echelon basis of M8 with distinct leading bits, processed high -> low
B = {}
for c in memc.tolist():
    v = c
    while v:
        h = v.bit_length() - 1
        if h in B: v ^= B[h]
        else: B[h] = v; break
print('dim M8:', len(B))
Bl = sorted(B.items(), reverse=True)
def redM(a):
    a = a.copy()
    for h, v in Bl:
        m = (a >> h) & 1
        a ^= m * v
    return a
cls = redM(cos)
single = sz == 1
sc = cls[single]
print('singleton tensors:', int(single.sum()), ' with coset in M8:', int((sc == 0).sum()))
ucl, ccl = np.unique(sc, return_counts=True)
print('classes mod M8 hit by singletons:', len(ucl), ' class-size quantiles min/med/max:',
      int(ccl.min()), int(np.median(ccl)), int(ccl.max()))
pairs = int((ccl.astype(np.int64) * (ccl - 1) // 2).sum())
print('singleton pairs in one class mod M8 (cosets sum into M8):', pairs)
# semi classes vs singleton classes
semi = (sz == 2) | (sz == 3)
scl = set(np.unique(cls[semi]).tolist())
print('singleton classes that are also semi classes:', len(set(ucl.tolist()) & scl), 'of', len(ucl))
# pairs whose coset sum is a member coset (nonzero, in M8) vs inside T_b (coset sum 0 = same coset impossible for singletons)
# spangen check
for a, b in ((0x007b297b, 0x6a000008), (0x43620043, 0x29192930), (0x6a006a73, 0x007b4300), (0x00112938, 0x6a6a004b)):
    ia, ib = np.searchsorted(allt, a), np.searchsorted(allt, b)
    print('spangen pair %08x %08x: coset sizes %d %d, classes %x %x, coset sum %x' % (
        a, b, sz[ia], sz[ib], cls[ia], cls[ib], cos[ia] ^ cos[ib]))
np.savez_compressed(D + 'x3b/singleton_classes.npz', tensor=allt[single], coset=cos[single], cls=sc)
