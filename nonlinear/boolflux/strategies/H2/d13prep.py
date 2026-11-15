"""Prepare data for the exact d = 13 search (13 bilinearly independent members).

Relaxed tower model, free = affine + early set + allowed v-quadratics(gamma).  Every member m gets
b_m = its bilinear part mod T (8 bits) and j_m = its junk coordinate: img_m (mod T_full, canonical)
minus the fixed linear lift of b_m.  A 13-member layer with bilinear span of dim 13 exists iff there
is a 5-dim W <= F_2^8 and a linear phi: W -> J with >= 13 members m, b_m in W, j_m = phi(b_m),
of full rank 13 (then their span is T_full + graph).  Writes a text file for d13.c.
usage: d13prep.py EARLY GAMMA OUT
"""
import sys, os, pickle, itertools
from h2lib import Basis
import tsearch as TS
from tower import tab, VAR, ONE, m4, tau, W, norm

early_kind, gamma, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
from tower import MUL as _MUL
CLS = [(0, 1), (W, 0), (W, 1), (W, W), (W, 3)]


def kara_products(spec):
    p = list(map(int, spec[5:].split(',')))
    a, b, c, d = p[:4]; pts = p[4:7]
    out = []
    for pi in pts:
        c1, c0 = CLS[pi]
        def ev(u, c1=c1, c0=c0):
            A1, A0 = TS.g16(u) if hasattr(TS, 'g16') else None
            return m4(c1, A1) ^ m4(c0, A0)
        for r in (1, W, 3):
            out.append(tab(lambda L, R, v, r=r, ev=ev: tau(m4(r, ev(_MUL[a][L] ^ _MUL[b][R]))) &
                           tau(m4(r, ev(_MUL[c][L] ^ _MUL[d][R])))))
    return out


free = [ONE] + VAR + TS.allowed_vquads(gamma)
if early_kind == 'umi':
    free += TS.early_products()
elif early_kind.startswith('kara:'):
    # kara:a,b,c,d,P1,P2,P3[,F] : Karatsuba cover of (aL + bR)(cL + dR) over GF(4) at the 3 points
    # P_i of P^1(GF(4)) (indices into CL), each GF(4) product by tau(r x) tau(r y), r = 1, W, W^2
    free += kara_products(early_kind)
elif early_kind.startswith('file:'):
    import tbuild as TB, a28parse as AP
    inv = {TB.LR(x): x for x in range(256)}
    _, ANDS = AP.load(early_kind[5:])
    for A in ANDS:
        if A['stage'] == 'L':
            o = A['out']; free.append(tab(lambda L, R, v, o=o: (o >> inv[(L, R)]) & 1))
FB = Basis()
for f in free: FB.add(f)
# D must be free
for j in range(4):
    assert FB.contains(tab(lambda L, R, v, j=j: norm(L, R) >> j & 1))
red = lambda v: FB.full_reduce(v)[0]
mt = pickle.load(open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/mtab-all.pkl'), 'rb'))


def bil(t):
    out = 0
    for p in range(4096):
        lr = p & 255; v = p >> 8
        if ((t >> p) ^ (t >> lr) ^ (t >> (v << 8)) ^ t) & 1: out |= 1 << p
    return out


Tt = TS.targets(gamma)
Tb = [bil(t) for t in Tt]
# bilinear coordinates mod T
BB = Basis(track=True); nbb = 0
for t in Tb:
    BB.add(t, 0)
mem = []
seen = set()
for lc, mc, tt in mt:
    r = red(tt)
    if r == 0 or r in seen: continue
    seen.add(r)
    mem.append((lc, mc, tt, r))
mb = [bil(m[2]) for m in mem]
# quotient basis of Bil/T from member bil parts
QBb = Basis(track=True); bbasis = []
for i, b in enumerate(mb):
    r = BB.full_reduce(b)[0]
    if QBb.add(r, 1 << len(bbasis)): bbasis.append(i)
assert len(bbasis) == 8, len(bbasis)
bcoord = []
for b in mb:
    r = BB.full_reduce(b)[0]
    rr, tag = QBb.full_reduce(r); assert rr == 0
    bcoord.append(tag)
# full quotient: T_full first
QB = Basis(track=True); n = 0
for t in Tt:
    QB.add(red(t), 1 << n); n += 1
for m in mem:
    if QB.add(m[3], 1 << n): n += 1
TMASK = (1 << 8) - 1
def img(v):
    r, tag = QB.full_reduce(v); assert r == 0
    return tag & ~TMASK        # drop the T_full components
im = [img(m[3]) for m in mem]
# lift: for unit vector e_i of the b-coordinates, the image of the combination of basis members
# whose b-coordinates give e_i
Bm = Basis(track=True)
for k, i in enumerate(bbasis): Bm.add(bcoord[i], 1 << k)
lift = []
for e in range(8):
    r, tag = Bm.full_reduce(1 << e); assert r == 0
    u = 0
    for k in range(8):
        if tag >> k & 1: u ^= im[bbasis[k]]
    lift.append(u)
jj = []
for i in range(len(mem)):
    u = im[i]
    for e in range(8):
        if bcoord[i] >> e & 1: u ^= lift[e]
    jj.append(u)
with open(out, 'w') as f:
    f.write('%d %d\n' % (len(mem), n))
    for i in range(len(mem)):
        f.write('%d %x %x\n' % (bcoord[i], jj[i] >> 64, jj[i] & ((1 << 64) - 1)))
with open(out + '.img', 'w') as f:
    f.write('%d %d\n' % (len(mem), n))
    for i in range(len(mem)):
        f.write('%x %x\n' % (im[i] >> 64, im[i] & ((1 << 64) - 1)))
pickle.dump({'mem': [(m[0], m[1]) for m in mem], 'b': bcoord, 'j': jj, 'early': early_kind, 'gamma': gamma},
            open(out + '.pkl', 'wb'))
print('members', len(mem), 'quotient dim', n, 'zero-j members', sum(1 for x in jj if x == 0))
