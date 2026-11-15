r"""X3 semi_check.py: x-junk Tr(Ax)Tr(kAx): univariate coefficient of x^5 (and x^3, x^9, x^17) for k in GF(4)* and K \ GF(4).
Claim [P]: coefficient of x^5 is A^5 (k + k^4): zero iff k in GF(4)."""
from gfinv import gmul, gpow
def tr(z):
    s = 0
    for _ in range(8): s ^= z; z = gmul(z, z, 8)
    return s & 1
K = sorted({gpow(x, 17, 8) for x in range(256)}); Q = [k for k in K if gpow(k, 4, 8) == k]
def coef(f, e):   # sum_x f(x) x^(255-e)
    s = 0
    for x in range(1, 256):
        if f[x]: s ^= gpow(x, 255 - e, 8)
    return s
bad = 0
for A in (1, 2, 3, 0x53, 0xca):
    for k in K:
        if k < 2: continue
        f = [tr(gmul(A, x, 8)) & tr(gmul(gmul(k, A, 8), x, 8)) for x in range(256)]
        c5 = coef(f, 5); pred = gmul(gpow(A, 5, 8), k ^ gpow(k, 4, 8), 8)
        if c5 != pred: bad += 1
        if A == 3: print('A=3 k=%02x inGF4=%d  c3=%02x c5=%02x c9=%02x c17=%02x' % (k, k in Q, coef(f, 3), c5, coef(f, 9), coef(f, 17)))
print('mismatches with A^5 (k + k^4):', bad)
