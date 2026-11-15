"""REAL-model (256 points) preparation for gen13: candidates = GF(4)-norm members on v_g = Q + g D
for every g in GAMMAS (several gammas may be mixed in one layer), plus optionally pure bilinear
products tau(lam) * tau(mu(v_g)) ('bil').  Free = span(1, x, early products, BMP's 5 products).
Writes OUT.img (images mod free + T_full) and OUT.pkl (candidate descriptions, early, gammas).
usage: rprep.py EARLY GAMMAS(comma) OUT [bil]"""
import sys, pickle, itertools
from h2lib import Basis
import tsearch as TS, tbuild as TB, a28parse as AP
from tower import m4, tau, W, W2, MUL, INV16, norm, ONE16

early_kind, gl, out = sys.argv[1], [int(x) for x in sys.argv[2].split(',')], sys.argv[3]
extra = sys.argv[4:]
LRx = [TB.LR(x) for x in range(256)]
Dx = [norm(*lr) for lr in LRx]
T256 = TB.T256
early = []
if early_kind == 'umi':
    for a, b, c in TS.ROWS:
        for r in (1, W, W2):
            early.append((T256(lambda x, a=a, r=r: tau(m4(r, TS.lam_val(a, *LRx[x])))),
                          T256(lambda x, b=b, r=r: tau(m4(r, TS.lam_val(b, *LRx[x]))))))
elif early_kind.startswith('kara:'):
    p = list(map(int, early_kind[5:].split(','))); a, b, c, d = p[:4]
    CLS = [(0, 1), (W, 0), (W, 1), (W, W), (W, 3)]
    for pi in p[4:7]:
        c1, c0 = CLS[pi]
        ev = lambda u, c1=c1, c0=c0: m4(c1, TS.g16(u)[0]) ^ m4(c0, TS.g16(u)[1])
        for r in (1, W, W2):
            early.append((T256(lambda x, r=r, ev=ev: tau(m4(r, ev(MUL[a][LRx[x][0]] ^ MUL[b][LRx[x][1]])))),
                          T256(lambda x, r=r, ev=ev: tau(m4(r, ev(MUL[c][LRx[x][0]] ^ MUL[d][LRx[x][1]]))))))
elif early_kind.startswith('h4:'):
    import json as _json
    early = [(int(a, 16), int(b, 16)) for a, b in _json.load(open(early_kind[3:]))['l1ops']]
elif early_kind.startswith('masks:'):
    import json
    fn, idx = early_kind[6:].rsplit(':', 1)
    cov = json.load(open(fn))[int(idx)]
    def lin(mask):
        t = 0
        for bb in range(8):
            if mask >> bb & 1: t ^= AP.XT[bb]
        return t
    early = [(lin(l), lin(m)) for l, m in cov]
elif early_kind.startswith('file:'):
    _, ANDS = AP.load(early_kind[5:])
    early = [(A['a'], A['b']) for A in ANDS if A['stage'] == 'L']
db = [TS.d_bits(Dx[x]) for x in range(256)]
d0, d1, d2, d3 = [T256(lambda x, i=i: db[x][i]) for i in range(4)]
M1 = (d0 ^ d1) & (d2 ^ d3); M2 = d1 & (d2 ^ M1); M3 = (d0 ^ M1) & d3; M4 = d2 & (M1 ^ M3)
M5 = (d0 ^ M2) & (d2 ^ M1 ^ M4)
midp = [M1, M2, M3, M4, M5]
mid_ops = None
for e in extra:
    if e.startswith('midfile:'):
        _, MA = AP.load(e[8:])
        mid_ops = [(A['a'], A['b']) for A in MA if A['stage'] == 'M']
        midp = [a & b for a, b in mid_ops]
free = [AP.ONE] + AP.BITS + [a & b for a, b in early] + midp
if 'xfree' in extra:
    free += [AP.BITS[i] & AP.BITS[j] for i in range(8) for j in range(i + 1, 8)]
FB = Basis()
for f in free: FB.add(f)
for j in range(4):
    assert FB.contains(T256(lambda x, j=j: Dx[x] >> j & 1)), 'early does not span D'
red = lambda v: FB.full_reduce(v)[0]
cands = []; seen = set(); SINGCLS = {}
if 'semi' in extra:
    # X3's rank<=2 tensors in 2-, 3-, 5-cosets (bil_cosets2.txt), realised as (l1 + lam2(v)) (l2 + lam1(v)),
    # v = n + gamma_real N (real FIPS coordinates); members (5-cosets) first.
    import os
    from h2lib import gmul as _gm, gpow as _gp
    import gmap as _GM
    nnr = [INV16 and _gp(x, 238) for x in range(256)]
    Nr = [_gp(x, 17) for x in range(256)]
    nbidx = []; _B = Basis()
    for i in range(8):
        if _B.add(T256(lambda x, i=i: nnr[x] >> i & 1)): nbidx.append(i)
    lines = [ln.split() for ln in open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/bil_cosets2.txt'))]
    lines.sort(key=lambda p: -int(p[2]))
    def fact(t):
        rows = [(t >> (8 * j)) & 255 for j in range(4)]
        bs = []
        for v in rows:
            if v and v not in bs and (len(bs) < 2) and not (len(bs) == 1 and False): pass
        nz = [v for v in rows if v]
        l1 = nz[0]; l2 = next((v for v in nz if v != l1), None)
        if l2 is None: return [(l1, sum(1 << j for j in range(4) if rows[j] == l1))]
        lam1 = lam2 = 0
        for j, v in enumerate(rows):
            for a, b in ((0, 0), (1, 0), (0, 1), (1, 1)):
                if (l1 if a else 0) ^ (l2 if b else 0) == v: lam1 |= a << j; lam2 |= b << j; break
            else: return None
        return [(l1, lam1), (l2, lam2)]
    for g in gl:
        gr = [k for k in range(256) if k in set(Nr) and _GM.tower_gamma(k) == g][0] if g else 0
        vr = [nnr[x] ^ _gm(gr, Nr[x]) for x in range(256)]
        xl = lambda u: T256(lambda x: bin(u & x).count('1') & 1)
        vl = lambda m: T256(lambda x: sum(((vr[x] >> nbidx[j]) & 1) for j in range(4) if m >> j & 1) & 1)
        XL = {}; VL = {}
        for p in lines:
            for th in p[3:]:
                fa = fact(int(th, 16))
                if fa is None: continue
                for u, m in fa:
                    if u not in XL: XL[u] = xl(u)
                    if m not in VL: VL[m] = vl(m)
                if len(fa) == 1: t = XL[fa[0][0]] & VL[fa[0][1]]
                else:
                    (l1, m1), (l2, m2) = fa
                    t = (XL[l1] ^ VL[m2]) & (XL[l2] ^ VL[m1])
                r = red(t)
                if r and r not in seen: seen.add(r); cands.append((r, ('s', g, int(th, 16), int(p[2]), fa, int(p[1], 16))))
        if 'all2' in extra:
            # X3b: singleton-coset rank<=2 tensors with their class mod M8 (singleton_classes.npz)
            import numpy as _np
            _z = _np.load(os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/x3b/singleton_classes.npz'))
            for th, co, cl in zip(_z['tensor'].tolist(), _z['coset'].tolist(), _z['cls'].tolist()):
                fa = fact(th)
                if fa is None: continue
                for u, m in fa:
                    if u not in XL: XL[u] = xl(u)
                    if m not in VL: VL[m] = vl(m)
                if len(fa) == 1: t = XL[fa[0][0]] & VL[fa[0][1]]
                else:
                    (l1, m1), (l2, m2) = fa
                    t = (XL[l1] ^ VL[m2]) & (XL[l2] ^ VL[m1])
                r = red(t)
                if r and r not in seen:
                    seen.add(r); cands.append((r, ('s', g, th, 1, fa, co))); SINGCLS[co] = cl
    gl_members = []
else:
    gl_members = gl
for g in gl_members:
    vx = [INV16[Dx[x]] ^ MUL[g][Dx[x]] for x in range(256)]
    for lc in TS.all_lams():
        lv = [TS.lam_val(lc, *LRx[x]) for x in range(256)]
        for mc in TS.all_mus():
            t = T256(lambda x: (tau(lv[x]) ^ tau(m4(W, TS.mu_val(mc, vx[x])))) & (tau(m4(W, lv[x])) ^ tau(TS.mu_val(mc, vx[x]))))
            r = red(t)
            if r and r not in seen: seen.add(r); cands.append((r, ('m', g, lc, mc)))
            if 'bil' in extra:
                t = T256(lambda x: tau(lv[x]) & tau(TS.mu_val(mc, vx[x])))
                r = red(t)
                if r and r not in seen: seen.add(r); cands.append((r, ('b', g, lc, mc)))
QB = Basis(track=True); n = 0
for t in AP.Stabs:
    if QB.add(red(t), 1 << n): n += 1
assert n == 8
for r, _ in cands:
    if QB.add(r, 1 << n): n += 1
im = []; full = []
for r, _ in cands:
    rr, tag = QB.full_reduce(r); assert rr == 0
    im.append(tag & ~0xFF); full.append(tag)
with open(out + '.full', 'w') as f:
    for v in full: f.write('%x\n' % v)
_cls = {}
try:
    import os as _os
    for _ln in open(_os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/semi_classes.tsv')):
        if _ln.startswith('#'): continue
        _p = _ln.split(); _cls[int(_p[0], 16)] = int(_p[1], 16)
except Exception: pass
with open(out + '.cls', 'w') as _f:
    for c in cands:
        if c[1][0] == 's':
            _f.write('%d\n' % (0 if c[1][3] == 5 else _cls.get(c[1][5], SINGCLS.get(c[1][5], -1))))
        else: _f.write('0\n')
open(out + '.n0', 'w').write(str(sum(1 for c in cands if c[1][0] == 'm' or (c[1][0] == 's' and c[1][3] == 5))))
with open(out + '.img', 'w') as f:
    f.write('%d %d\n' % (len(cands), n))
    for v in im: f.write('%x %x\n' % (v >> 64, v & ((1 << 64) - 1)))
pickle.dump({'cands': [c[1] for c in cands], 'early': early_kind, 'gammas': gl, 'early_ops': early, 'mid_ops': mid_ops},
            open(out + '.pkl', 'wb'))
from collections import Counter
print('candidates', len(cands), 'quotient dim', n, 'max image multiplicity', max(Counter(im).values()),
      'zero images', sum(1 for v in im if v == 0))
