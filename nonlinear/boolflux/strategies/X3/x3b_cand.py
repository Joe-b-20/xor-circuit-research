"""X3b x3b_cand.py FILE DROP [O2|O] [LIMIT]: complete the stage-1-free 12 + 1 test (x3b_fixkq) for a three-stage
file: enumerate EVERY l in O (Gray code, as fixk), solve m for the missing T-bar element modulo
E_b = span(1, x, Quad, middle) + X (X = top products minus DROP), build p = l * m (particular solution m0 and
the whole kernel coset if small), and for each p: U' = V_N + quadratic parts of the outputs over
A + X + p (A = span(1, x, N, n, middle)), dim U', dim D = Quad cap (A + X + p) mod V_N (0: U' unique),
and the exact 9-cover test of U' (G eval3.cover_sat; exact enumeration when 9 - dim U' <= 2).
A U' that is 9-coverable gives 9 + |middle| + 13 = 27 (then build + aes_check)."""
import sys, json, time
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    sys.path.insert(0, str(S / d))
import gf, xag
from xag import ONES, AFFX, NC, nC
f = sys.argv[1]; drop = {int(i) for i in sys.argv[2].split(',')}
Oname = sys.argv[3] if len(sys.argv) > 3 else 'O2'
LIMIT = float(sys.argv[4]) if len(sys.argv) > 4 else 20
QUAD = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
T = [gf.bit_table(gf.INV, k) for k in range(8)]
c, ands, outs, otabs = xag.parse(f)
roles = [xag.role(A) for A in ands]
mid = [A['tab'] for A, r in zip(ands, roles) if r == 'MID']
last = [A['tab'] for A, r in zip(ands, roles) if r not in ('S1', 'MID')]
X = [t for i, t in enumerate(last) if i not in drop]

class Ech:
    def __init__(self, vs=(), tags=False):
        self.b = {}
        for i, v in enumerate(vs): self.add(v, (1 << i) if tags else 0)
    def add(self, v, tg=0):
        while v:
            h = v.bit_length() - 1
            if h in self.b: bv, bt = self.b[h]; v ^= bv; tg ^= bt
            else: self.b[h] = (v, tg); return True
        return False
    def red(self, v, tg=0):
        while v:
            h = v.bit_length() - 1
            if h not in self.b: return v, tg
            bv, bt = self.b[h]; v ^= bv; tg ^= bt
        return 0, tg
    def nf(self, v):          # canonical full reduction
        out = v
        for h in sorted(self.b, reverse=True):
            if (out >> h) & 1: out ^= self.b[h][0]
        return out
    def dim(self): return len(self.b)

Eb = Ech([ONES] + list(gf.X) + QUAD + mid + X)
tb = [Eb.nf(t) for t in T]
TB = Ech([t for t in tb if t]); d = TB.dim()
print(Path(f).name, 'drop', sorted(drop), 'd =', d, flush=True)
assert d == 1
tv = next(t for t in tb if t)
def basis(vs):
    e = Ech(); return [v for v in vs if e.add(v)]
if Oname == 'OV':
    O = basis([ONES] + list(gf.X) + list(xag.V0))
else:
    O = basis([ONES] + list(gf.X) + list(NC) + list(nC) + (mid if Oname == 'O2' else []))
k = len(O)
R = [[Eb.nf(O[i] & O[j]) for j in range(k)] for i in range(k)]
hits = []
A0, B0 = (map(int, sys.argv[5].split(':')) if len(sys.argv) > 5 else (0, 1 << k))
A0 = max(A0, 1)
l = 0; cur = [0] * k; t0 = time.time()
g0 = A0 ^ (A0 >> 1)                       # Gray value at A0
for i in range(k):
    if g0 >> i & 1:
        for j in range(k): cur[j] ^= R[i][j]
l = g0
for g in range(A0, B0):
    if g > A0:
        i = ((g ^ (g >> 1)) ^ l).bit_length() - 1
        l ^= 1 << i
        for j in range(k): cur[j] ^= R[i][j]
    e = Ech()
    for j in range(k):
        if cur[j]: e.add(cur[j], 1 << j)
    r, tg = e.red(tv)
    if r == 0:
        # kernel of m -> nf(l * m): rebuild with kernel tracking
        e2 = Ech(); ker = []
        for j in range(k):
            v, t2 = e2.red(cur[j], 1 << j)
            if v == 0: ker.append(t2)
            else: e2.add(cur[j], 1 << j)
        hits.append((l, tg, ker))
print('hits (l, m0):', len(hits), 'kernel dims', sorted({len(h[2]) for h in hits}), 'secs', round(time.time() - t0, 1), flush=True)
def comb(mask):
    t = 0
    for i in range(k):
        if mask >> i & 1: t ^= O[i]
    return t
import eval3
A = [ONES] + list(gf.X) + list(NC) + list(nC) + mid
seen = {}; res = []
allm = []
for l, tg0, ker in hits:
    kk = ker[:12]
    for s in range(1 << len(kk)):
        tg = tg0
        for i in range(len(kk)):
            if s >> i & 1: tg ^= kk[i]
        allm.append((l, tg))
print('products to test (all kernel cosets, kernel truncated at 12):', len(allm), flush=True)
pseen = set()
for l, tg in allm:
    p = comb(l) & comb(tg)
    if p in pseen: continue
    pseen.add(p)
    base = Ech(A + X + [p])
    assert base.red(tv)[0] != 0 or True
    full = Ech()
    for v in A + X + [p]: full.add(v, 0)
    for j, q in enumerate(QUAD): full.add(q, 1 << j)
    qs = []
    ok = True
    for t in T:
        r, tag = full.red(t)
        if r: ok = False; break
        q = 0
        for j in range(28):
            if tag >> j & 1: q ^= QUAD[j]
        qs.append(q)
    if not ok: res.append({'l': hex(l), 'err': 'T not in span'}); continue
    U = Ech(list(AFFX) + list(NC) + qs)
    dU = U.dim() - 9
    key = tuple(sorted(U.nf(v) for v in qs))
    capD = Ech(list(AFFX) + QUAD).dim() + base.dim() - Ech(A + X + [p] + QUAD).dim() - Ech(list(AFFX) + list(NC)).dim()
    if key in seen: seen[key]['n'] += 1; continue
    a0 = Ech(list(AFFX)); Ub = []
    for t in list(NC) + qs:
        if a0.add(t): Ub.append(t)
    cov, pairs = eval3.cover_sat(Ub, 9, LIMIT) if dU <= 9 else (False, None)
    seen[key] = {'n': 1, 'dimU': dU, 'dimD': capD, 'cover9': cov, 'l': hex(l), 'm': hex(tg)}
    if cov: print('COVERABLE U', seen[key], flush=True)
print('distinct U:', len(seen))
hist = {}
for v in seen.values():
    kk = (v['dimU'], v['dimD'], v['cover9']); hist[str(kk)] = hist.get(str(kk), 0) + v['n']
print('(dimU, dimD, 9-cover) -> number of hits:', hist)
Path.home().joinpath('xs-campaigns/2026-11-15-study/X3/x3b/cand_%s_%s_%s_%d.json' % (Path(f).stem[:30], '-'.join(map(str, sorted(drop))), Oname, A0)).write_text(
    json.dumps({'file': f, 'drop': sorted(drop), 'O': Oname, 'hits': len(hits), 'U': list(seen.values())}, indent=1))
