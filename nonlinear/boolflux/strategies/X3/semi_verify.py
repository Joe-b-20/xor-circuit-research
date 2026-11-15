"""X3 semi_verify.py: check semi_members.tsv witnesses: for every coset (sample: every STEP-th), the products of two
tensors of the coset differ by a NONZERO output combination modulo Aff + Quad(x) + V0."""
import os, sys
from gfinv import gmul, gpow
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 50
def trn(z, k):
    s = 0
    for _ in range(k): s ^= z; z = gmul(z, z, 8)
    return s & 1
nn = [gpow(x, 238, 8) for x in range(256)]; inv = [gpow(x, 254, 8) for x in range(256)]; N = [gpow(x, 17, 8) for x in range(256)]
ONE = (1 << 256) - 1
def tt(f): return sum((f(x) & 1) << x for x in range(256))
X = [tt(lambda x, i=i: x >> i) for i in range(8)]
J = [ONE] + X + [X[i] & X[j] for i in range(8) for j in range(i + 1, 8)] + [sum(1 << x for x in range(256) if N[x] == v) for v in set(N)]
T = [tt(lambda x, i=i: inv[x] >> i) for i in range(8)]
def ech(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h not in b: b[h] = v; break
            v ^= b[h]
    return b
def red(b, v):
    while v:
        h = v.bit_length() - 1
        if h not in b: return v
        v ^= b[h]
    return 0
EJ = ech(J); EJT = ech(J + T)
def prod(A1, A2, e1, e2):
    return tt(lambda x: (trn(gmul(A1, x, 8), 8) ^ trn(gmul(e2, nn[x], 8), 4)) & (trn(gmul(A2, x, 8), 8) ^ trn(gmul(e1, nn[x], 8), 4)))
cos = {}
for ln in open(D + 'semi_members.tsv'):
    if ln[0] == '#': continue
    p = ln.split('\t'); cos.setdefault(p[1], []).append([int(z, 16) for z in p[3:7]])
keys = sorted(cos)[::STEP]; ok = 0; fail = 0
for k in keys:
    ps = [prod(*w) for w in cos[k]]
    for q in ps[1:]:
        d = ps[0] ^ q
        if red(EJT, d) == 0 and red(EJ, d) != 0: ok += 1
        else: fail += 1
print('cosets checked', len(keys), 'pairs ok', ok, 'fail', fail)
