#!/usr/bin/env python3
"""qcert3: stress test of the batch-3 rows -- Lemma H2 (r_i + m_i <= 3), row HUB2, PK4 / PK5, FM7 / FM9 -- with their
per-helper and per-label strong forms, on top of everything qcert2/stress_ext2.py evaluates (the batch-1, HUB (H1) and
DARK rows, Lemma O1, the package rows re-asserted).  An extension of stress_ext2.py (which extends qcert/stress_ext.py,
which extends the package's stress.py, imported unchanged from the copy stress_pkg.py; the originals are not touched).

Part A (circuits).  For every circuit C and its orbit C, T(C), T(T(C)), T^3(C) (step 0 raw, steps 1-3 canonical
transposes), in addition to stress_ext2's rows (slack = right side - left side, must be >= 0; equalities asserted):
  H2 (Lemma H2)    per helper i: r_i + m_i <= 3, m_i = #(missing labels at i that have an H-B edge at a full helper
                   other than i);  strong form: m_i <= cap_{R_i}(h_i) <= 3 - r_i, where cap_{R_i}(h_i) is the largest
                   |S| with the family F(h_i, R_i, S) of condition C1 independent, R_i = the helper's actual
                   represented triples, recomputed here by exhaustive search and compared with qhub's hub2 table.
  HUB2             per helper i with r_i <= 2:  u_i <= (3 - r_i) + (q - A), A = sum_{r=3} u = #(full-met labels).
  PK4 / PK5 / L23  q = 4: #{u >= 3} <= 1;  q = 5: n3 + 2 n4 + 2 n5 <= 2;  q = 6, 7: the package's L23 (slack recorded).
  FM7 / FM9        W + y1 <= 7 (q - A) + top(A), Z <= 3 (q - A) + top3(A) with the phase's A, and every chord row
                   FM7(a0), FM9(a0), a0 = 0..q-1, of the local system; per label: W_l + Y_l <= rank(C_l) (all missing
                   labels), Z_l <= min(3, rank(C_l) - 1) (bright labels), rank(C_l) >= 3 at every full-met label.
Part B (synthetic local configurations, NOT circuits).  All maximal configurations (h, R, S) with |S| = 3 - r at the
hub values attaining H2's bound (from qhub's hub2_{M,Mt}.json capacity table; S re-enumerated here), plus the nine
explicit witnesses of qhub/REPORT.md section 3.3: the gate equations of the configuration are independent and their
elimination (the two pivot steps of condition C1) yields exactly F(h, R, S); Lemma H2 holds with equality; HUB2 with
q = A = m holds with slack 0 and its constant-(2 - r) mutation is violated; pairs disjoint, full helpers pairwise
non-adjacent, labels distinct; W_l = 3 + r <= rank(C_l) at every full-met label (FM's per-label condition).
Mutation: the H1 cap-4 witness sets (r = 0, m = 4) give a dependent C1 family and dependent gate equations and are
flagged as H2 violations (the checker is live on m >= 1 data).

usage: nice -n 8 python3 stress_ext3.py [N_REAL]       (default: all 303 real circuits of bridge/profiles.json)
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert3'
sys.path.insert(0, str(HERE))
from stress_pkg import Circuit, BOUNDARY, parity, check_rows, PAIRVALS   # noqa: E402  (package stress.py, copied unchanged)
from profile_real_copy import reconstruct                                 # noqa: E402  (bridge reconstruction, copied unchanged)

RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}; DIMJ = {'M': 24, 'Mt': 28}; KAPPA = 4
KR = {0: 3, 1: 2, 2: 1}
CAPTAB = {o: {int(k): v for k, v in json.load(open(HERE / f'hub_cap_{o}.json'))['cap'].items()} for o in ('M', 'Mt')}
FM_HIST = {'M': {7: 4, 6: 108, 5: 140, 4: 692, 3: 3696}, 'Mt': {6: 216, 5: 144, 4: 1176, 3: 4960}}
def fm_tables(ori, n=20):
    ranks = sorted((r for r, c in FM_HIST[ori].items() for _ in range(c)), reverse=True)
    top = [0]; top3 = [0]
    for r in ranks[:n]: top.append(top[-1] + r)
    for r in sorted((min(3, r - 1) for r in ranks), reverse=True)[:n]: top3.append(top3[-1] + r)
    return top, top3
FMTAB = {o: fm_tables(o) for o in ('M', 'Mt')}
HUB = 1 << 64
def FC(j): return 1 << (65 + j)
HUB2TAB = {}
def hub2_table(ori):
    if ori not in HUB2TAB:
        d = json.load(open(SPRINT / f'qhub/hub2_{ori}.json'))
        HUB2TAB[ori] = {int(r): {int(h): b['c1'] for h, b in tab.items()} for r, tab in d['cap'].items()}
    return HUB2TAB[ori]


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
    def copy(self):
        b = Basis(); b.piv = dict(self.piv); return b
    def dim(self): return len(self.piv)


def rank_of(vectors):
    b = Basis()
    for v in vectors: b.add(v)
    return b.dim()


TAB = {}
def tables(ori):
    """boundary tables: R6 basis, forms per label value, rank(C_l), J (F9), sigma per pair, top(m), full values, pair values."""
    if ori in TAB: return TAB[ori]
    t0 = time.time()
    B = BOUNDARY[ori]; idx = {b: i for i, b in enumerate(B)}
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    six = set()
    for ts in trip.values():
        for a, b in itertools.combinations(ts, 2):
            assert a & b == 0; six.add(a | b)
    R6 = Basis()
    for w in six: R6.add(w)
    assert R6.dim() == RHO6[ori], (ori, R6.dim())
    forms = defaultdict(list)
    pairmask = {}
    for i, j in itertools.combinations(range(64), 2):
        forms[B[i] ^ B[j]].append((1 << i) | (1 << j)); pairmask[B[i] ^ B[j]] = (1 << i) | (1 << j)
    for S in itertools.combinations(range(64), 4):
        v = B[S[0]] ^ B[S[1]] ^ B[S[2]] ^ B[S[3]]
        forms[v].append((1 << S[0]) | (1 << S[1]) | (1 << S[2]) | (1 << S[3]))
    assert sum(len(v) for v in forms.values()) == 637392
    rankC = {}
    for l, fs in forms.items():
        rankC[l] = 1 + rank_of([fs[0] ^ f for f in fs[1:]])
    assert max(rankC.values()) == 7                                      # F6
    J = R6.copy()
    if ori == 'M':
        for l, fs in forms.items():
            if rankC[l] == 7:
                for f in fs[1:]: J.add(fs[0] ^ f)
    assert J.dim() == DIMJ[ori], (ori, J.dim())                          # F9
    sixl = list(six); sigma = {}
    for i, j in itertools.combinations(range(64), 2):
        m = (1 << i) | (1 << j)
        sigma[m] = rank_of([s for s in sixl if s & m == m])
    hist = Counter(sigma.values())
    top = [0]
    for s in sorted(sigma.values(), reverse=True): top.append(top[-1] + s)
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    assert len(full) == {'M': 80, 'Mt': 112}[ori]                        # F3
    PV = PAIRVALS[ori]; assert len(PV) == 2016                           # F2
    # finite fact FM recomputed on the way: rank(C_l) over the distinct labels f + c
    fmh = Counter(rankC[f ^ c] for f in full for c in B for _ in [0] if True)
    fmh = Counter(rankC[l] for l in {f ^ c for f in full for c in B})
    assert dict(fmh) == FM_HIST[ori], (ori, dict(fmh))
    TAB[ori] = dict(B=B, idx=idx, R6=R6, forms=forms, rankC=rankC, J=J, sigma=sigma, sigma_hist=dict(hist), top=top,
                    full=full, trip=trip, PV=PV, pairmask=pairmask, capmemo={}, c1memo={})
    print(f'  tables {ori}: rho6 {R6.dim()}, dim J {J.dim()}, full values {len(full)}, sigma histogram {dict(sorted(hist.items()))}, '
          f'FM rank histogram {dict(sorted(fmh.items()))} (= finite fact FM), {time.time()-t0:.1f}s', flush=True)
    return TAB[ori]


def cap_own(ori, h):
    """cap(h) of finite fact H1, recomputed (the 3|S| vectors H_f + T alone)."""
    T = tables(ori)
    if h in T['capmemo']: return T['capmemo'][h]
    N = [f for f in T['full'] if (h ^ f) in T['PV']]
    def indep(S):
        vecs = [t | (1 << (64 + i)) for i, f in enumerate(S) for t in T['full'][f]]
        return rank_of(vecs) == 3 * len(S)
    c = 0
    for size in range(len(N), 0, -1):
        if any(indep(S) for S in itertools.combinations(N, size)): c = size; break
    T['capmemo'][h] = c
    return c


def c1_family(T, h, R, S):
    """F(h, R, S) = {H_f + T} u {H_i + T : T in R} u {H_i + H_f + P_f}  (condition C1), coordinates: boundary index -> bit,
    hub -> bit 64, full helper j -> bit 65 + j."""
    vecs = [t | HUB for t in R]
    for n, f in enumerate(S):
        vecs += [t | FC(n) for t in T['full'][f]]
        vecs.append(T['pairmask'][h ^ f] | HUB | FC(n))
    return vecs


def cap_c1(ori, h, R, upto=4):
    """cap_R(h): the largest |S|, S subset of N(h), with F(h, R, S) independent (exhaustive, sizes upto..1)."""
    T = tables(ori); key = (h, tuple(sorted(R)))
    if key in T['c1memo']: return T['c1memo'][key]
    N = [f for f in T['full'] if (h ^ f) in T['PV']]
    assert rank_of([t | HUB for t in R]) == len(R), 'represented triples of the helper dependent'
    c = 0
    for size in range(min(len(N), upto), 0, -1):
        if any(rank_of(c1_family(T, h, R, S)) == 4 * size + len(R) for S in itertools.combinations(N, size)): c = size; break
    T['c1memo'][key] = c
    return c


def k_mod(ori, label, space):
    T = tables(ori); fs = T['forms'].get(label, [])
    if len(fs) < 2: return 0
    bs = space.copy(); k = 0
    for f in fs[1:]:
        if bs.add(fs[0] ^ f): k += 1
    return k


def phase(C, I):
    """slacks of every row for one phase (C a package Circuit, I = C.analyse()); dict name -> slack (>= 0 required)."""
    ori = C.ori; T = tables(ori); B = I['B']; H = set(I['H']); q, z, y, F, F_H = I['q'], I['z'], I['y'], I['F'], I['F_H']
    rho6, rho, eps = RHO6[ori], RESERVE[ori], EPS[ori]
    edges = []                                                                      # (p, q, label, result)
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e, s))
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    bb = {}
    for p, qq, e, res in edges:
        if p in B and qq in B: bb[e] = (p, qq, res)
    missing = [e for e in evens if e not in bb]; missing_set = set(missing)
    assert len(missing) == q
    rtype = {v: [0, 0, 0] for v in H}
    Ul = Counter(); Vl = Counter(); eel = Counter(); meets = defaultdict(list); rep_meets = defaultdict(list)
    hedges = {v: [] for v in H}
    for p, qq, e, res in edges:
        hs = [v for v in (p, qq) if v in H]
        for v in hs: hedges[v].append((qq if v == p else p, e, res))
        if len(hs) == 2:
            for v in hs: rtype[v][2] += 1
            Vl[e] += 1
        elif len(hs) == 1:
            v = hs[0]
            if e in bb: rtype[v][0] += 1; rep_meets[e].append(v)
            else: rtype[v][1] += 1; Ul[e] += 1; meets[e].append(v)
    anchored = {v for v in H if rtype[v][0] >= 1}; full = [v for v in H if rtype[v][0] == 3]
    bright = {e for e in missing if any(v in anchored for v in meets[e])}
    dark = [e for e in missing if e not in bright]
    h0 = sum(1 for v in H if rtype[v][0] == 0); U0 = sum(rtype[v][1] for v in H if rtype[v][0] == 0); D0 = U0 - h0
    qD = len(dark); n3 = len(full); n2 = sum(1 for v in H if rtype[v][0] == 2)
    W = sum(r * u for r, u, v in rtype.values()); A = sum(u for r, u, v in rtype.values() if r == 3)
    Z = sum(max(0, r - 1) * u for r, u, v in rtype.values()); E = sum(max(0, u - 2) for r, u, v in rtype.values() if r == 3)
    U = sum(u for r, u, v in rtype.values()); UA = sum(rtype[v][1] for v in anchored)
    y0 = y1 = y2 = y2d = y2m = 0; Yl = Counter(); ee1 = Counter(); kind_checks = 0; pairs = Counter()
    pairmask = lambda e: (1 << T['idx'][C.mask[bb[e][0]]]) | (1 << T['idx'][C.mask[bb[e][1]]])
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] or C.odd[b]: continue
        for e in (a, b, s): eel[e] += 1
        miss = [e for e in (a, b, s) if e not in bb]
        for e1, e2 in itertools.combinations(sorted(miss), 2): pairs[(e1, e2)] += 1
        if not miss:
            y0 += 1
            m = pairmask(a) ^ pairmask(b) ^ pairmask(s)
            assert bin(m).count('1') == 6 and T['R6'].reduce(m) == 0, 'kind-0 row not a weight-6 element of R6'
            kind_checks += 1
        elif len(miss) == 1 and miss[0] in bright:
            y1 += 1; Yl[miss[0]] += 1
            rep = [e for e in (a, b, s) if e in bb]
            D = pairmask(rep[0]) ^ pairmask(rep[1])
            assert bin(D).count('1') in (2, 4) and D in T['forms'][C.mask[miss[0]]], 'kind-1 row not a form of its label'
            kind_checks += 1
        else:
            y2 += 1
            if len(miss) == 1: y2d += 1; ee1[miss[0]] += 1
            else: y2m += 1
    assert y0 + y1 + y2 == y and y2d + y2m == y2
    Fb = sum(I['f'][e] for e in bright); Fd = sum(I['f'][e] for e in dark)
    kR6 = {e: k_mod(ori, C.mask[e], T['R6']) for e in bright}
    kJ = {e: k_mod(ori, C.mask[e], T['J']) for e in bright}
    sl = {}
    # ---- qcert batch-1 rows (stress_ext.py)
    sl['N1'] = (len(evens) - q) - 3 * n3
    sl['L7*'] = 7 * q - W - y1
    sl['L12*'] = rho6 - sum(max(0, r - 1) for r, u, v in rtype.values()) - y0
    sl['G*_R6'] = y2 + z + D0 - qD + sum(kR6.values()) - (32 - rho6)
    sl['G*_J'] = y2 + z + D0 - qD + sum(kJ.values()) - (32 - DIMJ[ori])
    sl['I'] = 4 * q + 2 * F - U - 2 * F_H - (y1 + y2)
    sl['L13*'] = (2 * y2 + 2 * z + 7 * q - 2 * rho) - (W + y1 - 2 * D0)
    sl['L14*'] = (2 * y2 + 2 * z + 7 * q - 2 * rho + eps) - (W + A + y1 - 2 * D0)
    sl['L15*'] = (y2 + z + 3 * q - rho) - (Z - D0)
    if ori == 'M':
        sl['L17-M*'] = (3 * y2 + 3 * z + 6 * q - 24) - (2 * Z + 2 * E - 3 * D0)
    else:
        sl['L17-Mt*'] = (3 * y2 + 3 * z + 3 * q - 12) - (Z + E - 3 * D0)
        sl['L18*'] = (3 * y2 + 3 * z + 7 * q - 12) - (W + A - 3 * D0)
        sl['L19*'] = y2 + sum((u + v - 1) for r, u, v in rtype.values() if r == 0) + sum(v for r, u, v in rtype.values() if r == 1) - 3
        sl['L20*'] = 3 * y2 + 2 * z + sum((3 * u + v - 3) for r, u, v in rtype.values() if r == 0) - 9
        if q == 0: sl['L22*'] = sum((v - 1) for r, u, v in rtype.values() if r == 0) - 3
    if q == 0: sl['Q0'] = z - (32 - rho6) - h0
    # ---- DARK rows with the actual q_D (Addendum 2, B.3-B.4)
    d = qD
    sl['L13d'] = (2 * y2 + 2 * z + 7 * q - 2 * rho - 9 * d) - (W + y1 - 2 * D0)
    sl['L14d'] = (2 * y2 + 2 * z + 7 * q - 2 * rho + eps - 9 * d) - (W + A + y1 - 2 * D0)
    sl['L15d'] = (y2 + z + 3 * q - rho - 4 * d) - (Z - D0)
    if ori == 'M': sl['L17Md'] = (3 * y2 + 3 * z + 6 * q - 24 - 9 * d) - (2 * Z + 2 * E - 3 * D0)
    else:
        sl['L17Td'] = (3 * y2 + 3 * z + 3 * q - 12 - 6 * d) - (Z + E - 3 * D0)
        sl['L18d'] = (3 * y2 + 3 * z + 7 * q - 12 - 10 * d) - (W + A - 3 * D0)
    sl['bright_lower'] = UA - (q - d)
    sl['bright_cap'] = 4 * (q - d) + 2 * Fb - (UA + y1)
    sl['dark_cap'] = 4 * d + 2 * Fd - y2d
    sl['F_budget'] = F - Fb - Fd - F_H
    sl['y2d<=y2'] = y2 - y2d
    sl['y2m<=C(q,2)'] = comb(q, 2) - y2m
    sl["I'"] = 4 * q + 2 * F - (y1 + 2 * y2 - y2d + U + 2 * F_H)
    if d == q: sl['Fb=0 (d=q)'] = -Fb
    if d == 0: sl['Fd=y2d=0 (d=0)'] = -(Fd + y2d)
    # ---- HUB (Lemma H1), per helper and aggregate (stress_ext2)
    fullmet = {}
    for v in full:
        for o, e, res in hedges[v]:
            if o in B and e in missing_set:
                assert e not in fullmet, 'a missing label meets two full helpers (Lemma 4.5)'
                fullmet[e] = v
    assert A == len(fullmet)
    hub_strong = []; hub_lp = []; cap_checks = 0
    for v in H:
        if rtype[v][0] == 3: continue
        fm = sum(1 for o, e, res in hedges[v] if o in B and e in fullmet)
        cap_t = CAPTAB[ori].get(C.mask[v], 0); cap_o = cap_own(ori, C.mask[v])
        assert cap_t == cap_o, ('cap table differs from own computation', hex(C.mask[v]), cap_t, cap_o)
        assert cap_o <= KAPPA; cap_checks += 1
        hub_strong.append(cap_o - fm)
        hub_lp.append(KAPPA + q - A - rtype[v][1])
    sl['HUB_strong_label'] = min(hub_strong, default=99); sl['HUB_lp'] = min(hub_lp, default=99)
    sl['HUBlin'] = 4 * q + 2 * F - (sum(max(0, u - KAPPA) for r, u, v in rtype.values() if r < 3) + 4 * A + 2 * F_H)
    # ---- Lemma H2 / HUB2 (batch 3): m_i, cap_{R_i}(h_i) by own exhaustive search, comparison with qhub's table
    h2 = []; hub2 = []; h2_strong = []; c1_checks = 0; tab_eq = 0; tab_le = 0
    H2T = hub2_table(ori)
    for v in H:
        r_i, u_i, v_i = rtype[v]
        m_i = sum(1 for o, e, res in hedges[v] if o in B and e in fullmet and fullmet[e] != v)
        h2.append(3 - r_i - m_i)
        if r_i <= 2:
            hub2.append((3 - r_i) + (q - A) - u_i)
            R = []
            for o, e, res in hedges[v]:
                if o in B and e in bb:
                    b1, b2, _ = bb[e]
                    R.append((1 << T['idx'][C.mask[o]]) | (1 << T['idx'][C.mask[b1]]) | (1 << T['idx'][C.mask[b2]]))
            assert len(R) == r_i and all(parity(C.mask[v] ^ 0) for _ in [0])
            cap = cap_c1(ori, C.mask[v], R); c1_checks += 1
            assert cap <= KR[r_i], ('finite fact H2 violated at a helper mask', hex(C.mask[v]), r_i, cap)
            h2_strong.append(cap - m_i)
            tab = H2T[r_i].get(C.mask[v], 0)              # qhub's cap_r(h) = max over the R choices (>= ours; equal at r = 0)
            assert cap <= tab, ('own C1 capacity exceeds qhub table', hex(C.mask[v]), r_i, cap, tab)
            if cap == tab: tab_eq += 1
            else: tab_le += 1
            if r_i == 0: assert cap == tab
        else:
            assert m_i == 0
    sl['H2'] = min(h2, default=99); sl['HUB2'] = min(hub2, default=99); sl['H2_strong'] = min(h2_strong, default=99)
    # ---- PK4 / PK5 / L23
    cu = Counter(u for r, u, v in rtype.values())
    if q == 4: sl['PK4'] = 1 - sum(c for u, c in cu.items() if u >= 3)
    if q == 5: sl['PK5'] = 2 - (cu[3] + 2 * cu[4] + 2 * cu[5])
    if q == 6: sl['L23-6'] = 4 - (cu[3] + 3 * cu[4] + 4 * cu[5] + 4 * cu[6])
    if q == 7: sl['L23-7'] = 14 - (2 * cu[3] + 7 * cu[4] + 12 * cu[5] + 14 * cu[6] + 14 * cu[7])
    # ---- FM7 / FM9 with the actual A, every chord row, per label
    top, top3 = FMTAB[ori]
    sl['FM7'] = 7 * (q - A) + top[A] - (W + y1); sl['FM9'] = 3 * (q - A) + top3[A] - Z
    ch7 = []; ch9 = []
    for a0 in range(q):
        s = top[a0 + 1] - top[a0]; s3 = top3[a0 + 1] - top3[a0]
        ch7.append(7 * q + top[a0] - s * a0 - (W + y1 + (7 - s) * A)); ch9.append(3 * q + top3[a0] - s3 * a0 - (Z + (3 - s3) * A))
    sl['FM7_chords'] = min(ch7, default=99); sl['FM9_chords'] = min(ch9, default=99)
    # ---- per-label strong forms
    l7 = []; i_lab = []; l13 = []; l14 = []; l15 = []; bcl = []; dcl = []; ex_sum = 0; dark_zero = 0; bright_anch = []; fm9l = []; fm_rank = []
    for e in missing:
        Wl = sum(rtype[v][0] for v in meets[e]); Zl = sum(max(0, rtype[v][0] - 1) for v in meets[e]); Al = int(any(rtype[v][0] == 3 for v in meets[e]))
        UAl = sum(1 for v in meets[e] if v in anchored); rc = T['rankC'].get(C.mask[e], 1)
        assert Ul[e] + Vl[e] + eel[e] == C.d[e] + 1, ('occurrence count of a missing label', e)       # d_l + 1 gate equations
        l7.append(rc - Wl - Yl[e]); assert rc <= 7
        i_lab.append(4 + 2 * I['f'][e] - (Ul[e] + Vl[e] + eel[e]))
        if e in fullmet:
            assert rc in FM_HIST[ori], ('full-met label with a rank outside finite fact FM', rc)
            fm_rank.append(rc - 3)
        if e in bright:
            bright_anch.append(UAl - 1)
            bcl.append(4 + 2 * I['f'][e] - (UAl + Yl[e]))
            l13.append(7 - 2 * kJ[e] - Wl - Yl[e])
            ex = Wl + Yl[e] + Al + 2 * kJ[e] - 7
            l14.append(7 - (Wl + Yl[e] + Al + 2 * kJ[e]) + max(0, ex)); ex_sum += max(0, ex)
            l15.append(min(3 - Zl - kJ[e], rc - 1 - kJ[e] - Zl))
            fm9l.append(min(3, rc - 1) - Zl)
            assert rc + 2 * kJ[e] <= 7                                   # F9 (for the labels occurring)
        else:
            dark_zero += Wl + Zl + Al + Yl[e] + UAl
            dcl.append(4 + 2 * I['f'][e] - ee1[e])
    sl['L7*_label'] = min(l7, default=99); sl['I_label'] = min(i_lab, default=99)
    sl['L13*_label'] = min(l13, default=99); sl['L14*_label'] = min(l14, default=99); sl['L14*_ex'] = eps - ex_sum
    sl['L15_label'] = min(l15, default=99); sl['bright_cap_label'] = min(bcl, default=99); sl['bright_anchored_label'] = min(bright_anch, default=99)
    sl['dark_cap_label'] = min(dcl, default=99); sl['dark_zero'] = -dark_zero; sl['FM9_label'] = min(fm9l, default=99); sl['FM_rank_fullmet'] = min(fm_rank, default=99)
    sl['pair_once'] = 1 - max(pairs.values(), default=1)
    # ---- Lemma S / S2
    s_sl = []; poor_at_r2 = 0
    for e, hs in rep_meets.items():
        sig = T['sigma'][pairmask(e)]
        s_sl.append(sig - sum(max(0, rtype[v][0] - 1) for v in hs))
        if any(rtype[v][0] >= 2 for v in hs) and sig < 2: poor_at_r2 += 1
    sl['LemmaS_label'] = min(s_sl, default=99); sl['S2_poor_at_r2'] = -poor_at_r2
    m = len(evens) - q
    sl['S2_aggregate'] = T['top'][min(m, len(T['top']) - 1)] - (6 * n3 + 2 * n2)
    # ---- Lemma 4.6 (own check): two helpers share <= 1 missing label
    ms = {v: {e for o, e, res in hedges[v] if o in B and e in missing_set} for v in H}
    sl['L4.6_pairs'] = 1 - max((len(ms[v1] & ms[v2]) for v1, v2 in itertools.combinations(H, 2)), default=0)
    # ---- Lemma O1
    owned = []; o1_viol = 0; per_full = []
    for v in full:
        if sum(1 for o, e, res in hedges[v] if res == v) != 1: o1_viol += 1
        outs = []
        for o, e, res in hedges[v]:
            if not (o in B and e in bb) or res == v: continue
            b1, b2, res2 = bb[e]
            if res == e:
                if res2 not in (b1, b2) or res2 not in C.out_index: o1_viol += 1; continue
                outs.append(res2)
            elif res == o:
                if o not in C.out_index: o1_viol += 1; continue
                outs.append(o)
            else: o1_viol += 1
            if outs and outs[-1] not in (o, b1, b2): o1_viol += 1
        per_full.append(len(outs)); owned += outs
        if len(outs) < 2: o1_viol += 1
    if len(owned) != len(set(owned)): o1_viol += 1
    sl['O1'] = -o1_viol
    facts = dict(ori=ori, x=I['x'], y=y, h=I['h'], q=q, z=z, F=F, n3=n3, n2=n2, y0=y0, y1=y1, y2=y2, y2d=y2d, y2m=y2m, Fb=Fb, Fd=Fd,
                 h0=h0, D0=D0, qD=qD, W=W, U=U, A=A, kind_checks=kind_checks, cap_checks=cap_checks, c1_checks=c1_checks, tab_eq=tab_eq, tab_le=tab_le,
                 m_max=max((3 - s for s in h2), default=0) if False else max((rtype[v][0] + 0 for v in []), default=0),
                 hub_fullmet_max=max((sum(1 for o, e, res in hedges[v] if o in B and e in fullmet) for v in H if rtype[v][0] < 3), default=0),
                 cap_max=max((cap_own(ori, C.mask[v]) for v in H if rtype[v][0] < 3), default=0),
                 c1cap_max=max((cap - 0 for cap in [cap_c1(ori, C.mask[v], []) for v in H if rtype[v][0] == 0]), default=0),
                 n_u3=sum(c for u, c in cu.items() if u >= 3), o1_outputs=per_full)
    return sl, facts


def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); out = []
    for step in range(steps):
        I = C.analyse()
        rows = check_rows(I, C.ori)                       # the package's own rows, re-asserted
        for name, s in rows.items(): assert s >= 0, f'PACKAGE ROW VIOLATED step {step} {C.ori} {name} {s}'
        sl, facts = phase(C, I)
        out.append((step, C.ori, sl, facts, min(rows.values())))
        if step + 1 < steps:
            T, _ = C.canonical_transpose(I)
            C = T
    return out


# ---------------------------------------------------------------- Part B: synthetic local configurations
WITNESSES = [  # qhub/REPORT.md section 3.3 (R as 64-bit masks over boundary indices, S as full values)
    ('M', 0, 0x80800080, [], [0x181, 0x406000, 0x80800040]),
    ('M', 0, 0x40404000, [], [0x2030, 0x20404000, 0x80004080]),
    ('M', 1, 0x2020200, [0x2020200], [0x181, 0x4000204]),
    ('M', 1, 0x80800080, [0x80800080], [0x181, 0x404020]),
    ('M', 2, 0x80800080, [0x80800080, 0x800000404000], [0x181]),
    ('Mt', 0, 0x2020200, [], [0x301, 0x60200, 0x4080004]),
    ('Mt', 0, 0x20202, [], [0x602, 0x1000003, 0x4040800]),
    ('Mt', 1, 0x2020200, [0x204000004], [0x301, 0x60200]),
    ('Mt', 2, 0x2020200, [0x204000004, 0x2020200], [0x301]),
]
LBIT = 1 << 100


def bits(m):
    while m:
        b = m & -m; yield b.bit_length() - 1; m ^= b


def gate_equations(T, h, R, S):
    """formal gate equations of the local configuration (apex = the lowest boundary index of each triple; hub's end of
    P_j = its lowest index): B-B references E_L + B_b + B_c, represented H-B equations E_L + H_owner + B_a, and the two
    missing H-B equations E_{l_j} + H_i + B_{b_j}, E_{l_j} + H_{f_j} + B_{c_j}.  Even labels: bit 100 + index."""
    rows = []; labels = {}
    def lab(key):
        if key not in labels: labels[key] = LBIT << len(labels)
        return labels[key]
    trips = [(HUB, t) for t in R] + [(FC(j), t) for j, f in enumerate(S) for t in T['full'][f]]
    for owner, t in trips:
        a = min(bits(t)); rest = t & ~(1 << a)
        L = lab(('rep', rest))
        rows.append(L | rest); rows.append(L | (1 << a) | owner)
    nrep = len(labels)
    for j, f in enumerate(S):
        P = T['pairmask'][h ^ f]; b = min(bits(P)); c = max(bits(P))
        L = lab(('miss', j))
        rows.append(L | (1 << b) | HUB); rows.append(L | (1 << c) | FC(j))
    rows = list(dict.fromkeys(rows))
    return rows, nrep


def eliminate(rows):
    """the two pivot steps of C1: (1) add each reference to the H-B rows carrying its label, drop the references;
    (2) add the hub's missing row of l_j to f_j's, drop the hub's.  Returns the surviving rows."""
    low = (1 << 100) - 1; helpers = ((1 << 100) - 1) ^ ((1 << 64) - 1)
    refs = {}; others = []
    for v in rows:
        L = v >> 100
        if L and not (v & helpers): refs[L] = v
        else: others.append(v)
    out = []; miss = defaultdict(list)
    for v in others:
        L = v >> 100
        if L in refs: out.append(v ^ refs[L])
        else: miss[L].append(v)
    for L, pr in miss.items():
        assert len(pr) == 2
        hubrow = next(v for v in pr if v & HUB); other = next(v for v in pr if not v & HUB)
        out.append(hubrow ^ other)
    assert all(v >> 100 == 0 for v in out)
    return out


def synthetic(ori):
    T = tables(ori); H2T = hub2_table(ori); Bset = set(T['B']); PV = T['PV']
    t0 = time.time()
    confs = []                                   # (h, R, S, source)
    for (o, r, h, Rm, S) in WITNESSES:
        if o == ori: confs.append((h, tuple(Rm), tuple(S), 'witness'))
    n_att = {}
    for r in (0, 1, 2):
        att = sorted(h for h, c in H2T[r].items() if c == 3 - r)
        n_att[r] = len(att)
        for h in att:
            N = [f for f in T['full'] if (h ^ f) in PV]
            for R in (itertools.combinations(T['trip'][h], r) if r else [()]):
                if rank_of([t | HUB for t in R]) < r: continue
                for S in itertools.combinations(N, 3 - r):
                    if rank_of(c1_family(T, h, R, S)) == 4 * (3 - r) + r: confs.append((h, tuple(R), tuple(S), 'maximal'))
    stats = Counter(); bad = []
    for h, R, S, src in confs:
        r = len(R); m = len(S)
        assert h not in Bset and parity(h) and all(f in T['full'] for f in S) and all((h ^ f) in PV for f in S)
        assert all(t in T['trip'][h] for t in R) and len(set(R)) == r
        fam = c1_family(T, h, R, S); indep = rank_of(fam) == len(fam) == 4 * m + r
        rows, nrep = gate_equations(T, h, R, S)
        rk = rank_of(rows); gates_indep = rk == len(rows)
        identity = rk == nrep + m + rank_of(fam)
        elim = sorted(eliminate(rows)) == sorted(fam)
        pairs = [T['pairmask'][h ^ f] for f in S]
        disjoint = all(p1 & p2 == 0 for p1, p2 in itertools.combinations(pairs, 2))
        nonadj = all((f1 ^ f2) not in PV for f1, f2 in itertools.combinations(S, 2))
        labels = [h ^ T['B'][min(bits(P))] for P in pairs]
        distinct = len(set(labels)) == m and all(parity(l) == 0 for l in labels)
        fm_ok = all(T['rankC'][l] >= 3 + r for l in labels)
        q = A = u_i = m
        h2_ok = r + m <= 3; h2_tight = r + m == 3
        hub2_ok = u_i <= (3 - r) + (q - A); hub2_slack = (3 - r) + (q - A) - u_i; mut_viol = not (u_i <= (2 - r) + (q - A))
        ok = indep and gates_indep and identity and elim and disjoint and nonadj and distinct and fm_ok and h2_ok and h2_tight and hub2_ok and hub2_slack == 0 and mut_viol
        stats[(src, r, ok)] += 1
        if not ok: bad.append((src, r, hex(h), [hex(t) for t in R], [hex(f) for f in S], indep, gates_indep, identity, elim, disjoint, nonadj, distinct, fm_ok, h2_ok, hub2_ok, mut_viol))
    # mutation: H1 cap-4 witness sets (r = 0, m = 4): the C1 family and the gate equations must be dependent, H2 flags them
    muts = 0; flagged = 0
    for h in [hh for hh in CAPTAB[ori] if CAPTAB[ori][hh] == 4]:
        N = [f for f in T['full'] if (h ^ f) in PV]
        for S in itertools.combinations(N, 4):
            if rank_of([t | FC(n) for n, f in enumerate(S) for t in T['full'][f]]) != 12: continue
            muts += 1
            fam = c1_family(T, h, (), S); rows, nrep = gate_equations(T, h, (), S)
            if rank_of(fam) < len(fam) and rank_of(rows) < len(rows) and not (0 + 4 <= 3): flagged += 1
    n_conf = sum(v for (src, r, ok), v in stats.items() if src == 'maximal')
    qhc = None
    try:
        rep = json.load(open(SPRINT / 'qhubcheck/h2_check.json'))[ori]
        qhc = {r: rep[f'r{r}']['n_maximal_configs'] for r in (0, 1, 2)}
    except Exception:  # noqa: BLE001
        pass
    mine = {r: sum(v for (src, rr, ok), v in stats.items() if src == 'maximal' and rr == r) for r in (0, 1, 2)}
    print(f'  synthetic {ori}: hub values attaining 3 - r: {n_att}; maximal configurations re-enumerated {mine} (qhubcheck: {qhc}); '
          f'witnesses {sum(v for (src, r, ok), v in stats.items() if src == "witness")}; all checks passed on {sum(v for k, v in stats.items() if k[2])} of {sum(stats.values())}; '
          f'H1 cap-4 mutations {muts}, flagged (dependent C1 family, dependent gate equations, r + m = 4 > 3) {flagged}; {time.time()-t0:.0f}s', flush=True)
    assert not bad, bad[:3]
    assert muts == flagged and muts > 0
    assert qhc is None or qhc == mine, ('maximal configuration counts differ from qhubcheck', qhc, mine)
    return dict(attaining=n_att, maximal=mine, qhubcheck_maximal=qhc, witnesses=sum(v for (src, r, ok), v in stats.items() if src == 'witness'),
                total=sum(stats.values()), passed=sum(v for k, v in stats.items() if k[2]), h1_cap4_mutations=muts, flagged=flagged)


def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    t0 = time.time()
    tables('M'); tables('Mt')
    syn = {o: synthetic(o) for o in ('M', 'Mt')}
    jobs = []
    for fn in sorted(glob.glob(str(SPRINT / 'lb76/pkg_copy/source/circuits/*.json'))):
        d = json.load(open(fn)); g = d['gates'] if isinstance(d, dict) else d
        jobs.append(('ctrl:' + Path(fn).name, g))
    n_ctrl = len(jobs)
    prof = json.load(open(SPRINT / 'bridge/profiles.json'))
    for r in prof['results'][:nreal]:
        if 'error' in r: continue
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        jobs.append((r['tag'], gates))
    print(f'{n_ctrl} control circuits + {len(jobs)-n_ctrl} real circuits; {time.time()-t0:.0f}s', flush=True)
    mins = {}; viol = []; nph = Counter(); tight = Counter(); facts_range = defaultdict(lambda: [10 ** 9, -10 ** 9]); q0 = 0
    o1_hist = Counter(); cap_checks = 0; c1_checks = 0; tab_eq = 0; tab_le = 0; A_pos = 0; qhist = Counter()
    for n, (tag, gates) in enumerate(jobs):
        try:
            res = orbit(gates)
        except AssertionError as ex:
            viol.append((tag, 'assertion', str(ex))); print('FAIL', tag, ex, flush=True); continue
        group = 'ctrl' if tag.startswith('ctrl') else 'real'
        for step, ori, sl, facts, pkgmin in res:
            kind = 'raw' if step == 0 else 'canonical'
            nph[(group, kind, ori)] += 1; qhist[facts['q']] += 1
            if facts['q'] == 0: q0 += 1
            if facts['A'] > 0: A_pos += 1
            o1_hist.update(facts['o1_outputs']); cap_checks += facts['cap_checks']; c1_checks += facts['c1_checks']; tab_eq += facts['tab_eq']; tab_le += facts['tab_le']
            for name, s in sl.items():
                key = (group, kind, ori, name)
                mins[key] = min(mins.get(key, 10 ** 9), s)
                if s < 0: viol.append((tag, step, ori, name, s))
                if s == 0: tight[(group, ori, name)] += 1
            for k in ('n3', 'y0', 'y1', 'y2', 'y2d', 'y2m', 'q', 'z', 'y', 'h', 'h0', 'qD', 'A', 'Fb', 'Fd', 'hub_fullmet_max', 'cap_max', 'c1cap_max', 'n_u3'):
                fr = facts_range[(group, ori, k)]; fr[0] = min(fr[0], facts[k]); fr[1] = max(fr[1], facts[k])
        if (n + 1) % 50 == 0: print(f'  {n+1}/{len(jobs)} circuits, {len(viol)} violations, {time.time()-t0:.0f}s', flush=True)
    print(f'\nphases: {dict(nph)}; q histogram {dict(sorted(qhist.items()))}; phases with q = 0: {q0}; phases with A > 0: {A_pos}; '
          f'helper cap checks H1 (table = own search): {cap_checks}; helper cap checks H2 / C1 (own search <= qhub table): {c1_checks} (equal {tab_eq}, below {tab_le}); '
          f'distinct (mask, R) with cap_R recomputed: {sum(len(TAB[o]["c1memo"]) for o in TAB)}; distinct masks with H1 cap recomputed: {sum(len(TAB[o]["capmemo"]) for o in TAB)}')
    print(f'outputs defined per full helper (Lemma O1, must be >= 2): {dict(sorted(o1_hist.items()))}')
    print('\nminimum slack per row (group, raw/canonical, orientation):')
    names = sorted({k[3] for k in mins})
    for name in names:
        parts = []
        for g in ('ctrl', 'real'):
            for kind in ('raw', 'canonical'):
                for ori in ('M', 'Mt'):
                    v = mins.get((g, kind, ori, name))
                    if v is not None: parts.append(f'{g}/{kind}/{ori}:{v}')
        print(f'  {name:22s} ' + '  '.join(parts))
    print('\nrows tight (slack 0) on some phase:', {f'{g}/{o}/{n}': c for (g, o, n), c in sorted(tight.items())})
    print('\nranges of the quantities:', {f'{g}/{o}/{k}': tuple(v) for (g, o, k), v in sorted(facts_range.items())})
    rep = dict(circuits=len(jobs), controls=n_ctrl, real=len(jobs) - n_ctrl, phases=sum(nph.values()), q_hist=dict(qhist), q0_phases=q0, A_positive_phases=A_pos,
               cap_checks_H1=cap_checks, cap_checks_C1=c1_checks, c1_table_equal=tab_eq, c1_table_below=tab_le, o1_histogram=dict(o1_hist), violations=viol,
               min_slack={'/'.join(map(str, k)): v for k, v in sorted(mins.items())},
               tight={'/'.join(k): v for k, v in sorted(tight.items())}, ranges={'/'.join(k): v for k, v in sorted(facts_range.items())},
               sigma_hist={o: TAB[o]['sigma_hist'] for o in TAB}, synthetic=syn, seconds=time.time() - t0)
    json.dump(rep, open(HERE / 'stress_ext3.json', 'w'), indent=1, default=str)
    if viol:
        print(f'\nSTRESS EXT3 FAILED: {len(viol)} violations', viol[:10], file=sys.stderr); sys.exit(1)
    print(f'\nSTRESS EXT3 PASSED: {len(jobs)} circuits, {sum(nph.values())} phases, 0 violations of the batch-1, HUB, DARK, H2, HUB2, PK, FM rows and of O1; '
          f'synthetic maximal configurations {sum(s["total"] for s in syn.values())} all passed; {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
