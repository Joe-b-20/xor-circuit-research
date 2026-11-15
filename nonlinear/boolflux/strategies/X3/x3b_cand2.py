"""X3b x3b_cand2.py FILE DROP [O2|O] [LIMIT]: the d = 2 version of x3b_cand.py (k - 1 = 2 new products for a
dropped window W of 3): stage 1 free (E_b = span(1, x, Quad, middle) + X), every l in O (Gray code), m solved
for each of the 3 nonzero T-bar elements, whole kernel cosets; products grouped by T-bar class; for every
pair (p1, p2) from two different classes: U' = V_N + quadratic parts of the outputs over A + X + p1 + p2,
dim U', dim D (Quad cap (A + X + p1 + p2) mod V_N), exact or SAT 9-cover of U' (G eval3.cover_sat)."""
import sys, json, time
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1', 'X3'):
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
    def __init__(self, vs=()):
        self.b = {}
        for v in vs: self.add(v)
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
    def nf(self, v):
        for h in sorted(self.b, reverse=True):
            if (v >> h) & 1: v ^= self.b[h][0]
        return v
    def dim(self): return len(self.b)

Eb = Ech([ONES] + list(gf.X) + QUAD + mid + X)
tb = Ech()
for t in T: tb.add(Eb.nf(t))
assert tb.dim() == 2, tb.dim()
b0, b1 = [v for v, _ in tb.b.values()]
tbar = [b0, b1, b0 ^ b1]
tbar = [Eb.nf(t) for t in tbar]
def basis(vs):
    e = Ech(); return [v for v in vs if e.add(v)]
O = basis([ONES] + list(gf.X) + list(NC) + list(nC) + (mid if Oname == 'O2' else []))
k = len(O)
R = [[Eb.nf(O[i] & O[j]) for j in range(k)] for i in range(k)]
def comb(mask):
    t = 0
    for i in range(k):
        if mask >> i & 1: t ^= O[i]
    return t
prods = {0: set(), 1: set(), 2: set()}
l = 0; cur = [0] * k; t0 = time.time()
for g in range(1, 1 << k):
    i = ((g ^ (g >> 1)) ^ l).bit_length() - 1
    l ^= 1 << i
    for j in range(k): cur[j] ^= R[i][j]
    e = Ech(); ker = []
    for j in range(k):
        v, t2 = e.red(cur[j], 1 << j)
        if v == 0: ker.append(t2)
        else: e.add(cur[j], 1 << j)
    for ci, tv in enumerate(tbar):
        r, tg0 = e.red(tv)
        if r: continue
        kk = ker[:10]
        L = comb(l)
        for s in range(1 << len(kk)):
            tg = tg0
            for q in range(len(kk)):
                if s >> q & 1: tg ^= kk[q]
            prods[ci].add(L & comb(tg))
print(Path(f).name, 'drop', sorted(drop), 'products per T-bar class:', [len(prods[i]) for i in range(3)],
      'secs', round(time.time() - t0, 1), flush=True)
import eval3
A = [ONES] + list(gf.X) + list(NC) + list(nC) + mid
seen = {}; npairs = 0
for a in range(3):
    for b in range(a + 1, 3):
        for p1 in prods[a]:
            for p2 in prods[b]:
                npairs += 1
                full = Ech()
                for v in A + X + [p1, p2]: full.add(v, 0)
                for j, q in enumerate(QUAD): full.add(q, 1 << j)
                qs = []; ok = True
                for t in T:
                    r, tag = full.red(t)
                    if r: ok = False; break
                    q = 0
                    for j in range(28):
                        if tag >> j & 1: q ^= QUAD[j]
                    qs.append(q)
                if not ok: continue
                U = Ech(list(AFFX) + list(NC) + qs)
                key = tuple(sorted(U.nf(v) for v in qs))
                if key in seen: seen[key]['n'] += 1; continue
                dU = U.dim() - 9
                capD = (Ech(list(AFFX) + QUAD).dim() + Ech(A + X + [p1, p2]).dim()
                        - Ech(A + X + [p1, p2] + QUAD).dim() - Ech(list(AFFX) + list(NC)).dim())
                a0 = Ech(list(AFFX)); Ub = []
                for t in list(NC) + qs:
                    if a0.add(t): Ub.append(t)
                cov, _ = eval3.cover_sat(Ub, 9, LIMIT) if dU <= 9 else (False, None)
                seen[key] = {'n': 1, 'dimU': dU, 'dimD': capD, 'cover9': cov}
                if cov: print('COVERABLE U', seen[key], hex(p1)[:20], hex(p2)[:20], flush=True)
hist = {}
for v in seen.values():
    kk = str((v['dimU'], v['dimD'], v['cover9'])); hist[kk] = hist.get(kk, 0) + v['n']
print('pairs', npairs, 'distinct U', len(seen), '(dimU, dimD, 9-cover) -> pairs:', hist, 'secs', round(time.time() - t0, 1))
Path.home().joinpath('xs-campaigns/2026-11-15-study/X3/x3b/cand2_%s_%s_%s.json' % (Path(f).stem[:30], '-'.join(map(str, sorted(drop))), Oname)).write_text(
    json.dumps({'file': f, 'drop': sorted(drop), 'O': Oname, 'nprods': [len(prods[i]) for i in range(3)], 'pairs': npairs,
                'U': list(seen.values())}, indent=1))
