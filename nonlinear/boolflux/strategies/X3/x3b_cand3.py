"""X3b x3b_cand3.py FILE DROP [O2|O] [LIMIT] [MAXCOMBO]: general d (<= 3) completion of a dropped top window W
with stage 1 free; d = missing output dims (E_b = span(1, x, Quad, middle) + X, X = top products minus W).
1. every l in O (Gray code); for each nonzero T-bar class c, m solved with the whole kernel coset ->
   products by class.
2. linear junk: for a product p, e(p) = p + nf_Eb(p) lies in E_b; q(p) = its Quad component (over the
   decomposition (A + X) + Quad, A = span(1, x, N, n, middle)), taken in Quad / V_N coordinates. For outputs,
   e_i likewise. With d products whose classes form a basis, output i = sum_j alpha_ij p_j + (e_i + sum_j
   alpha_ij e(p_j)), so U' = V_N + span_i(q(e_i) + sum_j alpha_ij q(p_j)) (exact; alpha from the classes).
3. every basis of classes and every product combination: dim U'; distinct U' tested for a 9- and 10-cover
   (G eval3.cover_sat: exact enumeration when l - dim U' <= 2, else SAT with LIMIT seconds; None = timeout).
   9-cover -> 9 + 5 + (|X| + d); 10-cover -> 10 + 5 + (|X| + d).
D = dim(Quad cap (A + X)) mod V_N is reported: if D > 0, U' is only defined modulo that space (reported,
and the junk is then taken modulo it, which can only make U' smaller - still exact for the cover test
because any representative choice is allowed)."""
import sys, os, json, time, itertools
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1', 'X3'):
    sys.path.insert(0, str(S / d))
import gf, xag
from xag import ONES, AFFX, NC, nC
f = sys.argv[1]; drop = {int(i) for i in sys.argv[2].split(',')}
Oname = sys.argv[3] if len(sys.argv) > 3 else 'O2'
LIMIT = float(sys.argv[4]) if len(sys.argv) > 4 else 10
MAXC = int(sys.argv[5]) if len(sys.argv) > 5 else 3000000
QUAD = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
T = [gf.bit_table(gf.INV, k) for k in range(8)]
c, ands, outs, otabs = xag.parse(f)
roles = [xag.role(A) for A in ands]
mid = [A['tab'] for A, r in zip(ands, roles) if r == 'MID']
last = [A['tab'] for A, r in zip(ands, roles) if r not in ('S1', 'MID')]
lastops = [(A['Lt'], A['Rt']) for A, r in zip(ands, roles) if r not in ('S1', 'MID')]
midops = [(A['Lt'], A['Rt']) for A, r in zip(ands, roles) if r == 'MID']
Xops = [o for i, o in enumerate(lastops) if i not in drop]
OPS = {}                                   # product table -> (L, M) operand tables
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

t0 = time.time()
Eb = Ech([ONES] + list(gf.X) + QUAD + mid + X)
tbE = Ech()
for t in T: tbE.add(Eb.nf(t))
d = tbE.dim()
tb = [Eb.nf(v) for v, _ in tbE.b.values()]        # basis of T-bar (canonical nf vectors)
# coordinates of an nf vector in the tb basis
TBc = Ech()
for i, v in enumerate(tb): TBc.add(v, 1 << i)
def tcoord(v):
    r, tg = TBc.red(v); assert r == 0; return tg
classes = list(range(1, 1 << d))
cvec = {}
for cl in classes:
    v = 0
    for i in range(d):
        if cl >> i & 1: v ^= tb[i]
    cvec[cl] = Eb.nf(v)
print(Path(f).name, 'drop', sorted(drop), 'd =', d, 'top kept', len(X), flush=True)
# decomposition E_b = (A + X) + Quad with Quad tags; quotient by V_N quad tags
A = [ONES] + list(gf.X) + list(NC) + list(nC) + mid
DEC = Ech()
for v in A + X: DEC.add(v, 0)
for j, q in enumerate(QUAD): DEC.add(q, 1 << j)
VNq = Ech()
for t in NC:
    r, tg = DEC.red(t); assert r == 0
    # NC is in A (tag 0 if reduced via A first); get its quad tag independently:
QD = Ech()
for t in list(AFFX): QD.add(t, 0)
for j, q in enumerate(QUAD): QD.add(q, 1 << j)
for t in NC:
    r, tg = QD.red(t); assert r == 0; VNq.add(tg)
# D = Quad cap (A + X) beyond V_N: tags of quad combinations lying in A + X
capD = Ech(list(AFFX) + QUAD).dim() + Ech(A + X).dim() - Ech(A + X + QUAD).dim() - Ech(list(AFFX) + list(NC)).dim()
# kernel of the quad-tag map restricted: compute the D-space tags explicitly (quad tags of elements of Quad cap (A+X))
DT = Ech([v for v, _ in VNq.b.values()])
if capD > 0:
    AXe = Ech()
    for v in A + X: AXe.add(v, 0)
    for j, q in enumerate(QUAD):
        r, tg = AXe.red(q, 1 << j)
        if r == 0: DT.add(tg)
        else: AXe.add(q, 1 << j)
def qtag(e):
    r, tg = DEC.red(e); assert r == 0, 'not in E_b'
    return DT.nf(tg)
print('D (Quad cap (A+X) mod V_N):', capD, ' quotient tag-space dim', 28 - DT.dim(), flush=True)
def basis(vs):
    e = Ech(); return [v for v in vs if e.add(v)]
if Oname == 'OV':          # aff(x) + all functions of N (2^24 operands l)
    O = basis([ONES] + list(gf.X) + list(xag.V0))
else:
    O = basis([ONES] + list(gf.X) + list(NC) + list(nC) + (mid if Oname == 'O2' else []))
k = len(O)
R = [[Eb.nf(O[i] & O[j]) for j in range(k)] for i in range(k)]
def comb(mask):
    t = 0
    for i in range(k):
        if mask >> i & 1: t ^= O[i]
    return t
prods = {cl: {} for cl in classes}            # class -> {product: qtag}
# optional chunk of the Gray-code range: argv[6] = 'A:B' (default all)
A0, B0 = (map(int, sys.argv[6].split(':')) if len(sys.argv) > 6 else (1, 1 << k))
A0 = max(A0, 1)
cur = [0] * k
l = A0 ^ (A0 >> 1)
for i in range(k):
    if l >> i & 1:
        for j in range(k): cur[j] ^= R[i][j]
for g in range(A0, B0):
    if g > A0:
        i = ((g ^ (g >> 1)) ^ l).bit_length() - 1
        l ^= 1 << i
        for j in range(k): cur[j] ^= R[i][j]
    e = Ech(); ker = []
    for j in range(k):
        v, t2 = e.red(cur[j], 1 << j)
        if v == 0: ker.append(t2)
        else: e.add(cur[j], 1 << j)
    L = None
    for cl in classes:
        r, tg0 = e.red(cvec[cl])
        if r: continue
        if L is None: L = comb(l)
        kk = ker[:10]
        for s in range(1 << len(kk)):
            tg = tg0
            for q in range(len(kk)):
                if s >> q & 1: tg ^= kk[q]
            p = L & comb(tg)
            if p not in prods[cl]:
                nfp = Eb.nf(p); assert nfp == cvec[cl]
                prods[cl][p] = qtag(p ^ nfp)
                OPS[p] = (L, comb(tg))
npc = {cl: len(prods[cl]) for cl in classes}
print('products per class:', npc, 'secs', round(time.time() - t0, 1), flush=True)
# outputs: class coordinates beta_i and q(e_i)
beta = []; qe = []
for t in T:
    nft = Eb.nf(t); beta.append(tcoord(nft)); qe.append(qtag(t ^ nft))
def solve(cls, b):            # alpha with sum_j alpha_j cls_j = b (cls independent, as d-bit masks)
    for a in range(1 << len(cls)):
        v = 0
        for j in range(len(cls)):
            if a >> j & 1: v ^= cls[j]
        if v == b: return a
    raise ValueError
def rank_key(vs):
    b = {}
    for v in vs:
        v = DT.nf(v)
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    # canonical: fully reduce
    keys = sorted(b, reverse=True)
    for h in keys:
        for h2 in keys:
            if h2 != h and (b[h2] >> h) & 1: b[h2] ^= b[h]
    return tuple(sorted(b.values()))
seen = {}; WIT = {}; ncomb = 0; truncated = False
for cls in itertools.combinations(classes, d):
    # independent?
    if Ech(list(cls)).dim() != d: continue
    alpha = [solve(list(cls), b) for b in beta]
    plist = [list(prods[cl].items()) for cl in cls]
    if any(not x for x in plist): continue
    for combo in itertools.product(*plist):
        qs = [q for _, q in combo]
        ncomb += 1
        if ncomb > MAXC: truncated = True; break
        rows = []
        for i in range(8):
            v = qe[i]
            for j in range(d):
                if alpha[i] >> j & 1: v ^= qs[j]
            rows.append(v)
        key = rank_key(rows)
        if key in seen: seen[key] += 1
        else: seen[key] = 1; WIT[key] = [p for p, _ in combo]
    if truncated: break
dh = {}
for kk, v in seen.items(): dh[4 + len(kk)] = dh.get(4 + len(kk), 0) + v
print('combinations', ncomb, 'truncated' if truncated else 'complete', 'distinct U', len(seen),
      'dimU histogram', dict(sorted(dh.items())), 'secs', round(time.time() - t0, 1), flush=True)
import eval3
def tags_to_tab(tg):
    t = 0
    for j in range(28):
        if tg >> j & 1: t ^= QUAD[j]
    return t
res = []; BUILT = [0]
for key, n in sorted(seen.items(), key=lambda kv: len(kv[0])):
    dU = 4 + len(key)
    if dU > 10: res.append((dU, n, False, False)); continue
    Ub = list(NC) + [tags_to_tab(tg) for tg in key]
    c9, pr9 = eval3.cover_sat(Ub, 9, LIMIT) if dU <= 9 else (False, None)
    # 10-cover only where it can matter (10 + middle + kept + d <= build threshold); else 'skip'
    if c9: c10, pr10 = True, None
    elif 10 + len(midops) + len(X) + d <= int(os.environ.get('X3B_BUILD_MAX', '27')) + int(os.environ.get('X3B_C10_EXTRA', '0')):
        c10, pr10 = eval3.cover_sat(Ub, 10, LIMIT)
    else: c10, pr10 = 'skip', None
    res.append((dU, n, c9, c10))
    if c9 or c10 is True: print('COVERABLE', {'dimU': dU, 'n': n, '9': c9, '10': c10, 'key': [hex(x) for x in key]}, flush=True)
    total = (9 if c9 else 10) + len(midops) + len(X) + d
    if (c9 or c10 is True) and total <= int(os.environ.get('X3B_BUILD_MAX', '27')) and BUILT[0] < 3:
        BUILT[0] += 1
        # build: stage-1 cover, the file's middle, kept top products, the new products; then aes_check
        print('CANDIDATE total', total, '- building', flush=True)
        try:
            from ll_prob import build_tables
            from aes_prob import sbox_tables
            from core import write_ncff
            import subprocess
            pairs = list(pr9 if c9 else pr10) + midops + Xops + [OPS[p] for p in WIT[key]]
            circ = build_tables(pairs, sbox_tables(), name='aes-sbox-x3b')
            fd = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies/X3/found'
            fd.mkdir(exist_ok=True)
            stem = 'x3b-%s-drop%s-%d' % (Path(f).stem[:30], '-'.join(map(str, sorted(drop))), int(time.time()))
            cf = fd / (stem + '.circ.txt')
            cf.write_text(write_ncff(circ, comments=['X3b x3b_cand3: window re-solve with free stage 1 of ' + Path(f).name]),
                          encoding='utf-8', newline='\n')
            chk = subprocess.run([sys.executable, str(Path.home() / 'xcr-boolflux/nonlinear/boolflux/campaigns/aes_check.py'), str(cf)],
                                 capture_output=True, text=True)
            (fd / (stem + '.check.txt')).write_text(chk.stdout + chk.stderr)
            (fd / (stem + '.json')).write_text(json.dumps({'method': 'X3b x3b_cand3 (stage-1-free window re-solve, G cover_sat stage 1, G build_tables)',
                'source': f, 'drop': sorted(drop), 'O': Oname, 'total_predicted': total, 'dimU': dU,
                'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}, indent=1))
            print('BUILT', cf, chk.stdout.strip().splitlines()[:2], flush=True)
        except Exception as ex:
            print('BUILD FAILED', repr(ex), flush=True)
hist = {}
for dU, n, c9, c10 in res:
    kk = str((dU, c9, c10)); hist[kk] = hist.get(kk, 0) + n
print('(dimU, 9-cover, 10-cover) -> combinations:', hist, 'secs', round(time.time() - t0, 1))
Path.home().joinpath('xs-campaigns/2026-11-15-study/X3/x3b/cand3_%s_%s_%s.json' % (Path(f).stem[:34], '-'.join(map(str, sorted(drop))), Oname)).write_text(
    json.dumps({'file': f, 'drop': sorted(drop), 'O': Oname, 'd': d, 'D': capD, 'nprods': {str(k): v for k, v in npc.items()},
                'combinations': ncomb, 'truncated': truncated, 'hist': hist}, indent=1))
