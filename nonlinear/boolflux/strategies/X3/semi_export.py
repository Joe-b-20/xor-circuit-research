"""X3 semi_export.py: write semi_members.tsv: one line per rank-2 tensor lying in a T_b-coset with >= 2 tensors.
Columns: tensor(hex) coset(hex) coset_size A1 A2 e1 e2 xclass nclass   (all field elements hex, AES field 0x11B)
Product witness (gamma = 0): (Tr(A1 x) + Tr_K(e2 n)) * (Tr(A2 x) + Tr_K(e1 n)),  n = x^238, Tr_K = trace GF(16) -> GF(2).
Its x(x)n part is Tr(A1 x) Tr_K(e1 n) + Tr(A2 x) Tr_K(e2 n)."""
import os
from gfinv import gmul, gpow
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
def tr(z):
    s = 0
    for _ in range(8): s ^= z; z = gmul(z, z, 8)
    return s & 1
def trK(z):
    s = 0
    for _ in range(4): s ^= z; z = gmul(z, z, 8)
    return s & 1
nn = [gpow(x, 238, 8) for x in range(256)]
Kset = sorted(set(nn)); Q = {x for x in Kset if gpow(x, 4, 8) == x}
A_of = {sum(tr(gmul(A, 1 << i, 8)) << i for i in range(8)): A for A in range(256)}
def tt(f): return sum((f(x) & 1) << x for x in range(256))
NBidx = []; bas = []
for i in range(8):
    r = tt(lambda x: nn[x] >> i)
    for b in bas: r = min(r, r ^ b)
    if r: bas.append(r); bas.sort(reverse=True); NBidx.append(i)
def mask_of(e): 
    vals = tuple(trK(gmul(e, k, 8)) for k in Kset)
    for m in range(16):
        if tuple(bin(m & sum(((k >> NBidx[j]) & 1) << j for j in range(4))).count('1') & 1 for k in Kset) == vals: return m
e_of = {mask_of(e): e for e in Kset}
assert len(e_of) == 16
def cls(r): return 'Q' if r in Q else ('K' if r in Kset else 'F')
out = open(D + 'semi_members.tsv', 'w'); n = 0; bad = 0
print('# n-form coordinates: bits', NBidx, 'of n = x^238', file=out)
for ln in open(D + 'bil_cosets2.txt'):
    p = ln.split(); c = p[1]; sz = p[2]
    for th in p[3:]:
        t = int(th, 16); rows = [(t >> (8 * j)) & 255 for j in range(4)]
        l1 = next(v for v in rows if v); l2 = next(v for v in rows if v and v != l1)
        m1 = m2 = 0
        for j, v in enumerate(rows):
            if v == l1: m1 |= 1 << j
            elif v == l2: m2 |= 1 << j
            elif v == l1 ^ l2: m1 |= 1 << j; m2 |= 1 << j
            elif v: bad += 1
        A1, A2, e1, e2 = A_of[l1], A_of[l2], e_of[m1], e_of[m2]
        out.write('%s\t%s\t%s\t%02x\t%02x\t%02x\t%02x\t%s\t%s\n' % (th, c, sz, A1, A2, e1, e2,
                  cls(gmul(A1, gpow(A2, 254, 8), 8)), cls(gmul(e1, gpow(e2, 254, 8), 8)))); n += 1
print('written', n, 'bad', bad, 'NBidx', NBidx)
