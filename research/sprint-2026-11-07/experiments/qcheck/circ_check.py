#!/usr/bin/env python3
"""qcheck: independent re-check of the qbound claims (N1, Lemma S, L7*, L12*, G*, I, Q0, y->y2 rows, L19/L20 tolerance)
on real circuits and their canonical transposes.

Only stress.Circuit (normalization asserts, output detection, canonical_transpose) and profile_real.reconstruct*
(gate lists from value lists) are reused; every odd-graph / label / type / rank computation below is written here
from PROOF.md's definitions, and the lemmas are checked in their STRONG form (explicit vector families, ranks,
membership in R6 + sum K_l, per-label bounds), not just as aggregate slacks.
usage: python3 circ_check.py [N_REAL] [N_LOOSE]
"""
import sys, json, glob, itertools, random, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
import stress
from stress import Circuit
from profile_real import reconstruct, reconstruct_loose, read_ncff
T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)

# ---------------------------------------------------------------- boundary tables (own, from the matrix file)
MAT = Path.home()/'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt'
lines = [l.split() for l in open(MAT).read().strip().split('\n') if l.strip()]
lines = lines[lines.index(['32', '32']):]        # the file starts with a count line '1'
ROWS =[sum(int(b) << c for c, b in enumerate(l)) for l in lines[1:33]]
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]
UNITS = [1 << i for i in range(32)]
BND = {'M': UNITS + ROWS, 'Mt': UNITS + COLS}
assert BND['M'] == stress.BOUNDARY['M'] and BND['Mt'] == stress.BOUNDARY['Mt'], 'matrix file and package boundary differ'
def parity(m): return bin(m).count('1') & 1
def wt(m): return bin(m).count('1')
def rank(vs):
    piv = {}
    for v in vs:
        while v:
            hb = v.bit_length() - 1
            if hb in piv: v ^= piv[hb]
            else: piv[hb] = v; break
    return len(piv)
class Basis:
    def __init__(self): self.piv = {}
    def reduce(self, v):
        while v:
            hb = v.bit_length() - 1
            if hb in self.piv: v ^= self.piv[hb]
            else: return v
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
    def dim(self): return len(self.piv)
    def copy(self):
        b = Basis(); b.piv = dict(self.piv); return b

def inverse_rows(rows):
    aug = [rows[r] | (1 << (32 + r)) for r in range(32)]
    for c in range(32):
        p = next(r for r in range(c, 32) if (aug[r] >> c) & 1)
        aug[c], aug[p] = aug[p], aug[c]
        for r in range(32):
            if r != c and (aug[r] >> c) & 1: aug[r] ^= aug[c]
    return [aug[r] >> 32 for r in range(32)]

TAB = {}
def tables(ori):
    if ori in TAB: return TAB[ori]
    B = BND[ori]; idx = {b: i for i, b in enumerate(B)}
    pairvals = {B[i] ^ B[j] for i, j in itertools.combinations(range(64), 2)}
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    six = set()
    for ts in trip.values():
        if len(ts) >= 2:
            for a, b in itertools.combinations(ts, 2): six.add(a | b)
    R6 = Basis()
    for s in six: R6.add(s)
    rho6 = R6.dim(); assert rho6 == {'M': 20, 'Mt': 28}[ori]
    forms = defaultdict(list)
    for i, j in itertools.combinations(range(64), 2): forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
    for c in itertools.combinations(range(64), 4):
        forms[B[c[0]] ^ B[c[1]] ^ B[c[2]] ^ B[c[3]]].append((1 << c[0]) | (1 << c[1]) | (1 << c[2]) | (1 << c[3]))
    sixl = list(six)
    sig_cache = {}
    def sigma(Pkey):
        if Pkey not in sig_cache:
            P = (1 << Pkey[0]) | (1 << Pkey[1]); sig_cache[Pkey] = rank([s for s in sixl if s & P == P])
        return sig_cache[Pkey]
    cap_cache = {}
    def cap(l):
        if l not in cap_cache: cap_cache[l] = rank([f | (1 << 64) for f in forms.get(l, [])])
        return cap_cache[l]
    # R10: zero-sum boundary subsets of weight <= 10 (unit part u = XOR of the chosen rows)
    R = B[32:]; INV = inverse_rows(R)
    def rows_for_units(u):
        # u = XOR_{r in w} R[r] = R^T w  =>  w = (R^-1)^T u, i.e. w_r = sum_i u_i (R^-1)_{i,r}: w = XOR_{i in u} INV[i]
        w = 0
        for i in range(32):
            if (u >> i) & 1: w ^= INV[i]
        return w
    for _ in range(20):
        w = random.getrandbits(32); u = 0
        for r in range(32):
            if (w >> r) & 1: u ^= R[r]
        assert rows_for_units(u) == w
    words = set()
    for k in range(1, 6):
        for ws in itertools.combinations(range(32), k):
            u = 0
            for r in ws: u ^= R[r]
            if k + wt(u) <= 10: words.add(u | (sum(1 << r for r in ws) << 32))
    for k in range(1, 5):
        for us in itertools.combinations(range(32), k):
            u = sum(1 << i for i in us); w = rows_for_units(u)
            if k + wt(w) <= 10: words.add(u | (w << 32))
    R10 = Basis()
    for wd in words: R10.add(wd)
    assert all(not R10.reduce(s) for s in six)
    wh = Counter(wt(wd) for wd in words)
    log(ori, 'zero-sum words by weight (<=10):', dict(sorted(wh.items())), 'rho10 =', R10.dim())
    if ori == 'Mt': assert R10.dim() == 29 and wh[6] == 84 and wh[8] == 276 and wh[10] == 1300
    TAB[ori] = dict(B=B, idx=idx, pairvals=pairvals, trip=trip, R6=R6, rho6=rho6, forms=forms, sigma=sigma, cap=cap, R10=R10)
    return TAB[ori]

# ---------------------------------------------------------------- one phase
def f_min(r, u, v): return max(0, (r + u + v - 3) // 2)

def phase(C):
    ori = C.ori; T = tables(ori); B = T['B']; bidx = T['idx']; rho6 = T['rho6']; res = 32 - rho6
    n = C.n; mask = C.mask; odd = [parity(m) for m in mask]; G = C.G
    outs = set(C.out_index); Bset = set(range(32)) | outs
    H = [v for v in range(32, n) if odd[v] and v not in outs]; Hset = set(H); h = len(H)
    bco = {v: bidx[mask[v]] for v in Bset}
    uses = [[] for _ in range(n)]
    for k, (a, b) in enumerate(C.gates): uses[a].append(32 + k); uses[b].append(32 + k)
    d = [len(uses[v]) + (1 if v in outs else 0) for v in range(n)]
    edges = []; ee = []; x = y = 0
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if odd[a] and odd[b]: x += 1; edges.append((a, b, s))
        elif odd[a] != odd[b]:
            o, e = (a, b) if odd[a] else (b, a); edges.append((o, s, e))
        else: y += 1; ee.append((a, b, s))
    assert G == 32 + x + y + h
    evens = [v for v in range(32, n) if not odd[v]]; assert len(evens) == x + y
    for p, q_, e in edges: assert mask[p] ^ mask[q_] == mask[e]
    bylab = defaultdict(list)
    for p, q_, e in edges: bylab[e].append((p, q_))
    assert len({frozenset((p, q_)) for p, q_, _ in edges}) == len(edges), 'odd graph not simple'
    for e, es in bylab.items():
        vs = [v for pq in es for v in pq]; assert len(vs) == len(set(vs)), 'label not a matching'
    pair = {}
    for e in evens:
        bb = [(p, q_) for p, q_ in bylab.get(e, []) if p in Bset and q_ in Bset]
        assert len(bb) <= 1, 'two B-B edges with one label'
        if bb: pair[e] = bb[0]
    rep = set(pair); miss = [e for e in evens if e not in rep]; q = len(miss)
    HH = [(p, q_, e) for p, q_, e in edges if p in Hset and q_ in Hset]; z = len(HH)
    rr = {v: 0 for v in H}; uu = {v: 0 for v in H}; vv = {v: 0 for v in H}
    rep_edges = defaultdict(list); mis_edges = defaultdict(list); lab_HB = defaultdict(list)
    for p, q_, e in edges:
        hs = [v for v in (p, q_) if v in Hset]
        if len(hs) == 2: vv[p] += 1; vv[q_] += 1
        elif len(hs) == 1:
            i = hs[0]; a = q_ if p == i else p
            lab_HB[e].append((i, a))
            if e in rep: rr[i] += 1; rep_edges[i].append((a, e))
            else: uu[i] += 1; mis_edges[i].append((a, e))
    for v in H: assert rr[v] + uu[v] + vv[v] == d[v] + 1
    assert sum(rr.values()) + sum(uu.values()) == 32 + h - y + q - z           # Lemma 4.2
    anchored = {v for v in H if rr[v] >= 1}; h0 = h - len(anchored)
    bright = {e for e in miss if any(i in anchored for i, a in lab_HB.get(e, []))}
    qD = sum(1 for e in miss if e not in bright)
    U0 = sum(uu[v] for v in H if rr[v] == 0); D0 = U0 - h0
    types = Counter((rr[v], uu[v], vv[v]) for v in H)
    n3 = sum(1 for v in H if rr[v] == 3)
    def triple(i, a, e):
        b, c = pair[e]; assert len({a, b, c}) == 3 and mask[i] == mask[a] ^ mask[b] ^ mask[c]
        return (1 << bco[a]) | (1 << bco[b]) | (1 << bco[c])
    trip_of = {i: [triple(i, a, e) for a, e in rep_edges[i]] for i in H}
    for i in H:
        assert len(set(trip_of[i])) == rr[i] <= 3
        for t, t2 in itertools.combinations(trip_of[i], 2): assert t & t2 == 0
    # ---- N1 (strong form: labels pairwise distinct)
    full_labels = [e for i in H if rr[i] == 3 for a, e in rep_edges[i]]
    assert len(set(full_labels)) == 3 * n3, 'N1 REFUTED: two full helpers share a represented label'
    N1slack = (x + y - q) - 3 * n3; assert N1slack >= 0
    fulls = [i for i in H if rr[i] == 3]
    for i, j in itertools.combinations(fulls, 2): assert (mask[i] ^ mask[j]) not in T['pairvals'], 'Lemma 4.5 fails'
    # ---- Lemma S per represented label (strong form)
    S_min = 99; S_rich_viol = 0
    for e in rep:
        inc = lab_HB.get(e, [])
        if not inc: continue
        b, c = pair[e]; P = (1 << bco[b]) | (1 << bco[c]); sig = T['sigma'](tuple(sorted((bco[b], bco[c]))))
        excess = sum(rr[i] - 1 for i, a in inc)
        vecs = []
        for i, a in inc:
            t0 = triple(i, a, e)
            for t in trip_of[i]:
                if t != t0: assert t & t0 == 0; vecs.append(t | t0)
        assert len(vecs) == excess and rank(vecs) == excess, 'Lemma S: six-sets dependent'
        assert all(v6 & P == P and wt(v6) == 6 for v6 in vecs)
        assert excess <= sig, 'Lemma S REFUTED'
        S_min = min(S_min, sig - excess)
        if excess >= 1 and sig < 2: S_rich_viol += 1
    # ---- even+even classification
    y0 = y1 = y2 = 0; Y_l = Counter(); kind0_rows = []; kind1_forms = defaultdict(list)
    for a, b, s in ee:
        ms = [e for e in (a, b, s) if e not in rep]
        if not ms:
            y0 += 1; pr = 0
            for e in (a, b, s): pr ^= (1 << bco[pair[e][0]]) | (1 << bco[pair[e][1]])
            assert wt(pr) == 6 and T['R6'].reduce(pr) == 0, 'kind-0 reduced row is not a six-set of R6'
            kind0_rows.append(pr)
        elif len(ms) == 1 and ms[0] in bright:
            y1 += 1; l = ms[0]; Y_l[l] += 1; D = 0
            for e in (a, b, s):
                if e != l: D ^= (1 << bco[pair[e][0]]) | (1 << bco[pair[e][1]])
            assert wt(D) in (2, 4)
            xr = 0
            for t in range(64):
                if (D >> t) & 1: xr ^= B[t]
            assert xr == mask[l], 'kind-1 reduced row is not a form of its missing label'
            kind1_forms[l].append(D)
        else: y2 += 1
    assert y0 + y1 + y2 == y
    # ---- (L7*) per missing label, strong form
    L7_min = 99
    for l in miss:
        inc = lab_HB.get(l, []); W_l = sum(rr[i] for i, a in inc); vecs = []
        for i, a in inc:
            for t in trip_of[i]:
                Dm = t ^ (1 << bco[a]); assert wt(Dm) in (2, 4); vecs.append(Dm | (1 << 64))
        for D in kind1_forms.get(l, []): vecs.append(D | (1 << 64))
        assert len(vecs) == W_l + Y_l[l] and rank(vecs) == len(vecs), '(L7*) forms dependent'
        cp = T['cap'](mask[l]); assert len(vecs) <= cp <= 7, '(L7*) REFUTED'
        L7_min = min(L7_min, cp - len(vecs))
        if l not in bright: assert W_l == 0 and Y_l[l] == 0
    W = sum(rr[i] * uu[i] for i in H); assert W + y1 <= 7 * q
    # ---- (L12*) strong form
    diffs = []
    for i in anchored:
        ts = trip_of[i]
        for t in ts[1:]: diffs.append(t ^ ts[0])
    L12v = diffs + kind0_rows
    assert rank(L12v) == len(L12v) and all(T['R6'].reduce(v) == 0 for v in L12v), '(L12*) fails'
    Zx = sum(max(0, rr[i] - 1) for i in H); assert len(diffs) == Zx
    L12s = rho6 - Zx - y0; assert L12s >= 0, '(L12*) REFUTED'
    # ---- (G*) with J = R6, strong form (explicit family, residual membership)
    hidx = {v: k for k, v in enumerate(H)}; eidx = {e: k for k, e in enumerate(evens)}
    Hc = lambda i: 1 << (64 + hidx[i]); Ec = lambda e: 1 << (64 + h + eidx[e])
    fam = [Ec(e) | (1 << bco[b]) | (1 << bco[c]) for e, (b, c) in pair.items()]
    for i in H:
        for a, e in rep_edges[i]: fam.append(Hc(i) | (1 << bco[a]) | Ec(e))
        if i in anchored:
            for b, e in mis_edges[i]: fam.append(Hc(i) | (1 << bco[b]) | Ec(e))
    kind_rows = []
    for a, b, s in ee:
        ms = [e for e in (a, b, s) if e not in rep]
        if not ms or (len(ms) == 1 and ms[0] in bright): kind_rows.append(Ec(a) | Ec(b) | Ec(s))
    fam += kind_rows
    N = len(fam); assert N == (x + y - q) + sum(rr.values()) + sum(uu[i] for i in anchored) + y0 + y1
    assert rank(fam) == N, '(G*) retained family dependent'
    bs = Basis()
    for v in fam: bs.add(v)
    bdry = [v for v in bs.piv.values() if v.bit_length() <= 64]; dimVB = len(bdry)
    touched = len({t for v in fam for t in range(64, v.bit_length()) if (v >> t) & 1})
    m_cl = (x + y - q) + (h - h0) + (q - qD); assert touched == m_cl, (touched, m_cl)
    lower = 32 - y2 - z - D0 + qD; assert N - m_cl == lower and dimVB >= lower
    Kb = T['R6'].copy(); sumk = 0
    for l in bright:
        fs = T['forms'].get(mask[l], [])
        for f in fs[1:]:
            if Kb.add(fs[0] ^ f): sumk += 1
    assert all(Kb.reduce(v) == 0 for v in bdry), '(G*) residual outside R6 + sum_bright K_l'
    Gs = y2 + z + D0 - qD + sumk - res; assert Gs >= 0, '(G*) REFUTED'
    # ---- adjoints -> F, F_H ; (I) in per-label form
    adj = [0] * n
    for v in range(n - 1, -1, -1):
        a_ = 0
        for w in uses[v]: a_ ^= adj[w]
        if v in C.out_index: a_ ^= 1 << C.out_index[v]
        adj[v] = a_
    other = BND['Mt' if ori == 'M' else 'M'][32:]
    assert all(adj[i] == other[i] for i in range(32))
    ff = [0] * n
    for v in range(n):
        kv = sum(parity(adj[w]) for w in uses[v]) + (1 if v in outs else 0)
        ff[v] = max(0, d[v] - (kv + 1) // 2 - 1); assert d[v] <= 3 + 2 * ff[v]
    F = sum(ff); F_H = sum(ff[v] for v in H); U = sum(uu.values())
    for l in miss:
        U_l = len(lab_HB.get(l, [])); V_l = sum(1 for i, j, e in HH if e == l); ee_l = sum(1 for a, b, s in ee if l in (a, b, s))
        assert U_l + V_l + ee_l == d[l] + 1 <= 4 + 2 * ff[l]
    Is = 4 * q + 2 * F - U - 2 * F_H - (y1 + y2); assert Is >= 0, '(I) REFUTED'
    # ---- (Q0)
    Q0s = None
    if q == 0:
        assert y2 == 0 and U0 == 0
        Q0s = z - (32 - rho6) - h0; assert Q0s >= 0, '(Q0) REFUTED'
    # ---- the package rows with y -> y2 (and W -> W + y1 in L13, L14), evaluated on the type counts
    def S(fn): return sum(fn(r, u, v) * c for (r, u, v), c in types.items())
    deficit = lambda r, u: u - 1 if r == 0 else 0
    overflow = lambda r, u: max(0, u - 2) if r == 3 else 0
    A_ = S(lambda r, u, v: u if r == 3 else 0); Z_ = S(lambda r, u, v: max(0, r - 1) * u); E_ = S(lambda r, u, v: overflow(r, u))
    assert D0 == S(lambda r, u, v: deficit(r, u)) and W == S(lambda r, u, v: r * u)
    rows = {
        'L13* W+y1-2D0 <= 2y2+2z+7q-2rho': 2 * y2 + 2 * z + 7 * q - 2 * res - (W + y1 - 2 * D0),
        'L14* W+y1+A-2D0 <= 2y2+2z+7q-2rho+eps': 2 * y2 + 2 * z + 7 * q - 2 * res + (2 if ori == 'M' else 0) - (W + y1 + A_ - 2 * D0),
        'L15* Z-D0 <= y2+z+3q-rho': y2 + z + 3 * q - res - (Z_ - D0),
    }
    if ori == 'M':
        rows['L17M* 2Z+2E-3D0 <= 3y2+3z+6q-24'] = 3 * y2 + 3 * z + 6 * q - 24 - (2 * Z_ + 2 * E_ - 3 * D0)
    else:
        rows['L17Mt* Z+E-3D0 <= 3y2+3z+3q-12'] = 3 * y2 + 3 * z + 3 * q - 12 - (Z_ + E_ - 3 * D0)
        rows['L18* W+A-3D0 <= 3y2+3z+7q-12'] = 3 * y2 + 3 * z + 7 * q - 12 - (W + A_ - 3 * D0)
        rows['L19* 3 <= y2+sum_{r=0}(u+v-1)+sum_{r=1}v'] = y2 + S(lambda r, u, v: (u + v - 1) if r == 0 else (v if r == 1 else 0)) - 3
        rows['L20* 9 <= 3y2+2z+sum_{r=0}(3u+v-3)'] = 3 * y2 + 2 * z + S(lambda r, u, v: (3 * u + v - 3) if r == 0 else 0) - 9
        if q == 0: rows['L22* 3 <= y2+sum_{r=0}(v-1)'] = y2 + S(lambda r, u, v: (v - 1) if r == 0 else 0) - 3
    rows['L7* W+y1 <= 7q'] = 7 * q - W - y1
    rows['L12* Z+y0 <= rho6'] = L12s
    rows['I'] = Is; rows['G*R6'] = Gs; rows['N1'] = N1slack
    for k_, v_ in rows.items(): assert v_ >= 0, f'ROW VIOLATED {k_} slack {v_}'
    # ---- (L19)/(L20) tolerance for Mt: extended elimination family modulo R10
    L19ext = None
    if ori == 'Mt':
        fam2 = list(fam) + [Hc(i) | Hc(j) | Ec(e) for i, j, e in HH if i in anchored and j in anchored]
        N2 = len(fam2); assert rank(fam2) == N2
        bs2 = Basis()
        for v in fam2: bs2.add(v)
        bd2 = [v for v in bs2.piv.values() if v.bit_length() <= 64]
        touched2 = len({t for v in fam2 for t in range(64, v.bit_length()) if (v >> t) & 1})
        z0 = sum(1 for i, j, e in HH if i not in anchored or j not in anchored)
        qA = len({e for i, j, e in HH if i in anchored and j in anchored and e not in rep} | bright)
        assert touched2 == (x + y - q) + (h - h0) + qA
        assert N2 - touched2 == 32 - y2 + h0 - U0 - z0 + (q - qA)
        qdim = rank([T['R10'].reduce(v) for v in bd2])      # dimension of the residual modulo R10
        z1 = S(lambda r, u, v: v if r == 1 else 0)
        L19ext = dict(dim_residual=len(bd2), count=N2 - touched2, quot_mod_R10=qdim, z1=z1, bound20=2 * (z - z0) / 3)
        assert len(bd2) >= N2 - touched2 and qdim <= z1 and qdim <= 2 * (z - z0) / 3 and len(bd2) <= 29 + qdim, L19ext
    return dict(ori=ori, G=G, x=x, y=y, h=h, q=q, z=z, F=F, F_H=F_H, n3=n3, h0=h0, D0=D0, qD=qD, y0=y0, y1=y1, y2=y2, sumk=sumk,
                dimVB=dimVB, lowerVB=lower, N1=N1slack, Smin=S_min, Srich_viol=S_rich_viol, L7min=L7_min, L12=L12s, Gs=Gs, I=Is, Q0=Q0s,
                rows={k_: v_ for k_, v_ in rows.items()}, L19ext=L19ext, types={'%d,%d,%d' % t: c for t, c in types.items()})

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); out = []
    for st in range(steps):
        rec = phase(C); rec['step'] = st; out.append(rec)
        if st + 1 < steps:
            I = C.analyse(); C, _ = C.canonical_transpose(I)
    return out

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    nloose = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    tables('M'); tables('Mt')
    jobs = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        jobs.append(('ctrl:' + Path(fn).name, [tuple(x) for x in g]))
    for name in ('xor88-depth5', 'xor89-depth4', 'xor97-depth3'):
        jobs.append(('repo:' + name, read_ncff(str(Path.home()/f'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns-{name}.circ.txt'))))
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    vals_list = [(r['tag'], r['values']) for r in d['results'] if 'error' not in r][:nreal]
    for tag, vals in vals_list:
        g, _, _ = reconstruct(vals, 'ymax', 0, True); jobs.append(('ymax:' + tag, g))
    nl = 0
    for tag, vals in vals_list[:nloose]:
        for sd in (11, 12):
            try:
                g, _, _ = reconstruct_loose(vals, sd); Circuit(g, 'M'); jobs.append((f'loose{sd}:' + tag, g)); nl += 1
            except (ValueError, AssertionError): pass
        try:
            g, _, _ = reconstruct(vals, 'rand', 5, True); Circuit(g, 'M'); jobs.append(('rand5:' + tag, g)); nl += 1
        except (ValueError, AssertionError): pass
    log('jobs', len(jobs), '(controls 13, repo 3, ymax', len(vals_list), ', loose/rand', nl, ')')
    out = []; fails = []
    for k, (tag, g) in enumerate(jobs):
        try:
            out.append(dict(tag=tag, phases=orbit(g)))
        except AssertionError as ex:
            fails.append((tag, str(ex))); log('FAIL', tag, str(ex))
        if (k + 1) % 100 == 0: log(k + 1, 'circuits done')
    json.dump(dict(fails=fails, circuits=out), open(SPRINT/'qcheck/circ_check.json', 'w'), indent=0, default=str)
    ph = [p for r in out for p in r['phases']]
    log('circuits', len(out), 'phases', len(ph), 'failures', len(fails))
    for ori in ('M', 'Mt'):
        sel = [p for p in ph if p['ori'] == ori]
        can = [p for p in sel if p['step'] >= 1]
        log(f'== {ori}: {len(sel)} phases ({len(can)} canonical)')
        for key in ('N1', 'Smin', 'L7min', 'L12', 'Gs', 'I', 'n3', 'y0', 'y1', 'y2', 'q', 'z', 'h0', 'qD', 'sumk'):
            v = [p[key] for p in sel if p[key] is not None]
            log(f'   {key:6s} min {min(v):3d} median {sorted(v)[len(v)//2]:3d} max {max(v):3d}')
        for name in sorted({k_ for p in sel for k_ in p['rows']}):
            v = [p['rows'][name] for p in sel if name in p['rows']]
            log(f'   row {name:45s} min slack {min(v):3d}  (tight on {sum(1 for t in v if t == 0)} phases)')
        log('   Q0 phases (q=0):', sum(1 for p in sel if p['Q0'] is not None), '; phases with n3>=1:', sum(1 for p in sel if p['n3'] >= 1),
            '; with y1>=1:', sum(1 for p in sel if p['y1'] >= 1), '; dimVB - lower bound distribution:', dict(Counter(p['dimVB'] - p['lowerVB'] for p in sel)))
        if ori == 'Mt':
            e = [p['L19ext'] for p in sel]
            log('   L19ext: max quotient mod R10', max(t['quot_mod_R10'] for t in e), '; max z1', max(t['z1'] for t in e),
                '; max residual dim', max(t['dim_residual'] for t in e), '; quotient>0 on', sum(1 for t in e if t['quot_mod_R10'] > 0), 'phases')
    log('rich violations (r>=2 helper at a poor represented label):', sum(p['Srich_viol'] for p in ph))
    if fails: log('CIRCUIT CHECK: FAILURES', len(fails)); sys.exit(1)
    log('CIRCUIT CHECK PASSED: no violation of any claimed row or lemma')

if __name__ == '__main__':
    main()
