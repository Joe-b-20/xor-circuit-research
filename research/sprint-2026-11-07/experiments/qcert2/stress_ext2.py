#!/usr/bin/env python3
"""qcert2: stress test of the batch-1 rows AND the HUB / DARK rows (with their per-label and per-helper strong forms)
and of Lemma O1 on real circuits.  An extension of qcert/stress_ext.py (which extends the package's stress.py,
imported unchanged from the copy stress_pkg.py; the originals are not touched).

For every circuit C and its orbit C, T(C), T(T(C)), T^3(C) (step 0 raw, steps 1-3 canonical transposes), every
package row of stress_pkg.check_rows is re-asserted, every qcert row of stress_ext.py is re-evaluated, and in
addition (slack = right side - left side, must be >= 0; equalities asserted):

  HUB (Lemma H1)   per helper i with r_i <= 2:  #(missing labels at i meeting a full helper) <= cap(h_i) <= 4
                   (cap from the finite fact H1 table hub_cap_{ori}.json AND recomputed here by an exhaustive search
                   for every helper mask met), and u_i <= 4 + q - A, A = sum_{r=3} u = #(labels meeting a full helper);
                   each missing label meets <= 1 full helper (Lemma 4.5); HUBlin aggregate.
  DARK rows        with the phase's actual q_D, y2d, y2m, Fb, Fd: L13d, L14d, L15d, L17Md | L17Td, L18d, bright lower,
                   bright capacity, dark capacity, F budget, y2d <= y2, y2m <= C(q,2), (I'), d = q / d = 0 rows.
  per label        every missing label l: U_l + V_l + ee_l = d_l + 1 <= 4 + 2 f_l (equality asserted);
                   bright l: UA_l >= 1 (anchored missing edge), UA_l + Y_l <= 4 + 2 f_l, W_l + Y_l <= 7 - 2 k_l,
                   Z_l + k_l <= 3, Z_l <= rank(C_l) - 1 - k_l;  dark l: W_l = Y_l = Z_l = A_l = UA_l = 0,
                   ee1_l (gates whose only missing signal is l) <= 4 + 2 f_l;  no pair of missing labels in two gates.
  O1               every full helper has exactly one defining gate; each represented edge that is not the defining
                   gate defines an output in that edge's triple; >= 2 per full helper; all such outputs distinct.
Also recomputed from the matrix: rho6, F6, F9 (dim J, k_l), S1, and cap(h) for the helper masks met.

usage: nice -n 8 python3 stress_ext2.py [N_REAL]       (default: all 303 real circuits of bridge/profiles.json)
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert2'
sys.path.insert(0, str(HERE))
from stress_pkg import Circuit, BOUNDARY, parity, check_rows, PAIRVALS   # noqa: E402  (package stress.py, copied unchanged)
from profile_real_copy import reconstruct                                 # noqa: E402  (bridge reconstruction, copied unchanged)

RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}; DIMJ = {'M': 24, 'Mt': 28}; KAPPA = 4
CAPTAB = {o: {int(k): v for k, v in json.load(open(HERE / f'hub_cap_{o}.json'))['cap'].items()} for o in ('M', 'Mt')}


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
    for i, j in itertools.combinations(range(64), 2): forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
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
    TAB[ori] = dict(B=B, idx=idx, R6=R6, forms=forms, rankC=rankC, J=J, sigma=sigma, sigma_hist=dict(hist), top=top,
                    full=full, PV=PV, capmemo={})
    print(f'  tables {ori}: rho6 {R6.dim()}, dim J {J.dim()}, full values {len(full)}, sigma histogram {dict(sorted(hist.items()))}, {time.time()-t0:.1f}s', flush=True)
    return TAB[ori]


def cap_own(ori, h):
    """cap(h) of finite fact H1, recomputed: the largest S subset of N(h) = {f full: h + f a pair value} whose 3|S|
    relation vectors H_f + T (private coordinate per f) are independent.  Exhaustive by decreasing size."""
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


def k_mod(ori, label, space):
    T = tables(ori); fs = T['forms'].get(label, [])
    if len(fs) < 2: return 0
    bs = space.copy(); k = 0
    for f in fs[1:]:
        if bs.add(fs[0] ^ f): k += 1
    return k


def phase(C, I):
    """slacks of every new row for one phase (C a package Circuit, I = C.analyse()); dict name -> slack (>= 0 required)."""
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
    # even+even gates by kind; dark / multi-missing split; pairs of missing labels
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
    # ---- HUB (Lemma H1), per helper and aggregate
    fullmet = Counter()
    for v in full:
        for o, e, res in hedges[v]:
            if o in B and e in missing_set: fullmet[e] += 1
    assert all(c == 1 for c in fullmet.values()), 'a missing label meets two full helpers (Lemma 4.5)'
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
    # ---- per-label strong forms
    l7 = []; i_lab = []; l13 = []; l14 = []; l15 = []; bcl = []; dcl = []; ex_sum = 0; dark_zero = 0; bright_anch = []
    for e in missing:
        Wl = sum(rtype[v][0] for v in meets[e]); Zl = sum(max(0, rtype[v][0] - 1) for v in meets[e]); Al = int(any(rtype[v][0] == 3 for v in meets[e]))
        UAl = sum(1 for v in meets[e] if v in anchored); rc = T['rankC'].get(C.mask[e], 1)
        assert Ul[e] + Vl[e] + eel[e] == C.d[e] + 1, ('occurrence count of a missing label', e)       # d_l + 1 gate equations
        l7.append(rc - Wl - Yl[e]); assert rc <= 7
        i_lab.append(4 + 2 * I['f'][e] - (Ul[e] + Vl[e] + eel[e]))
        if e in bright:
            bright_anch.append(UAl - 1)
            bcl.append(4 + 2 * I['f'][e] - (UAl + Yl[e]))
            l13.append(7 - 2 * kJ[e] - Wl - Yl[e])
            ex = Wl + Yl[e] + Al + 2 * kJ[e] - 7
            l14.append(7 - (Wl + Yl[e] + Al + 2 * kJ[e]) + max(0, ex)); ex_sum += max(0, ex)
            l15.append(min(3 - Zl - kJ[e], rc - 1 - kJ[e] - Zl))
            assert rc + 2 * kJ[e] <= 7                                   # F9 (for the labels occurring)
        else:
            dark_zero += Wl + Zl + Al + Yl[e] + UAl
            dcl.append(4 + 2 * I['f'][e] - ee1[e])
    sl['L7*_label'] = min(l7, default=99); sl['I_label'] = min(i_lab, default=99)
    sl['L13*_label'] = min(l13, default=99); sl['L14*_label'] = min(l14, default=99); sl['L14*_ex'] = eps - ex_sum
    sl['L15_label'] = min(l15, default=99); sl['bright_cap_label'] = min(bcl, default=99); sl['bright_anchored_label'] = min(bright_anch, default=99)
    sl['dark_cap_label'] = min(dcl, default=99); sl['dark_zero'] = -dark_zero
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
    # ---- Lemma O1
    owned = []; o1_viol = 0; per_full = []
    for v in full:
        if sum(1 for o, e, res in hedges[v] if res == v) != 1: o1_viol += 1
        outs = []
        for o, e, res in hedges[v]:
            if not (o in B and e in bb) or res == v: continue
            b1, b2, res2 = bb[e]
            if res == e:                       # the label is this gate's result: its B-B gate must then define b1 or b2
                if res2 not in (b1, b2) or res2 not in C.out_index: o1_viol += 1; continue
                outs.append(res2)
            elif res == o:                     # the boundary end is the result: an output
                if o not in C.out_index: o1_viol += 1; continue
                outs.append(o)
            else: o1_viol += 1
            if outs and outs[-1] not in (o, b1, b2): o1_viol += 1
        per_full.append(len(outs)); owned += outs
        if len(outs) < 2: o1_viol += 1
    if len(owned) != len(set(owned)): o1_viol += 1
    sl['O1'] = -o1_viol
    facts = dict(ori=ori, x=I['x'], y=y, h=I['h'], q=q, z=z, F=F, n3=n3, n2=n2, y0=y0, y1=y1, y2=y2, y2d=y2d, y2m=y2m, Fb=Fb, Fd=Fd,
                 h0=h0, D0=D0, qD=qD, W=W, U=U, A=A, kind_checks=kind_checks, cap_checks=cap_checks,
                 hub_fullmet_max=max((sum(1 for o, e, res in hedges[v] if o in B and e in fullmet) for v in H if rtype[v][0] < 3), default=0),
                 cap_max=max((cap_own(ori, C.mask[v]) for v in H if rtype[v][0] < 3), default=0), o1_outputs=per_full)
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


def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    t0 = time.time()
    tables('M'); tables('Mt')
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
    o1_hist = Counter(); cap_checks = 0; A_pos = 0
    for n, (tag, gates) in enumerate(jobs):
        try:
            res = orbit(gates)
        except AssertionError as ex:
            viol.append((tag, 'assertion', str(ex))); print('FAIL', tag, ex, flush=True); continue
        group = 'ctrl' if tag.startswith('ctrl') else 'real'
        for step, ori, sl, facts, pkgmin in res:
            kind = 'raw' if step == 0 else 'canonical'
            nph[(group, kind, ori)] += 1
            if facts['q'] == 0: q0 += 1
            if facts['A'] > 0: A_pos += 1
            o1_hist.update(facts['o1_outputs']); cap_checks += facts['cap_checks']
            for name, s in sl.items():
                key = (group, kind, ori, name)
                mins[key] = min(mins.get(key, 10 ** 9), s)
                if s < 0: viol.append((tag, step, ori, name, s))
                if s == 0: tight[(group, ori, name)] += 1
            for k in ('n3', 'y0', 'y1', 'y2', 'y2d', 'y2m', 'q', 'z', 'y', 'h', 'h0', 'qD', 'A', 'Fb', 'Fd', 'hub_fullmet_max', 'cap_max'):
                fr = facts_range[(group, ori, k)]; fr[0] = min(fr[0], facts[k]); fr[1] = max(fr[1], facts[k])
        if (n + 1) % 50 == 0: print(f'  {n+1}/{len(jobs)} circuits, {len(viol)} violations, {time.time()-t0:.0f}s', flush=True)
    print(f'\nphases: {dict(nph)}; phases with q = 0: {q0}; phases with A > 0: {A_pos}; helper cap checks (table = own search): {cap_checks}; '
          f'distinct helper masks with cap recomputed: {sum(len(TAB[o]["capmemo"]) for o in TAB)}')
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
    rep = dict(circuits=len(jobs), controls=n_ctrl, real=len(jobs) - n_ctrl, phases=sum(nph.values()), q0_phases=q0, A_positive_phases=A_pos,
               cap_checks=cap_checks, o1_histogram=dict(o1_hist), violations=viol,
               min_slack={'/'.join(map(str, k)): v for k, v in sorted(mins.items())},
               tight={'/'.join(k): v for k, v in sorted(tight.items())}, ranges={'/'.join(k): v for k, v in sorted(facts_range.items())},
               sigma_hist={o: TAB[o]['sigma_hist'] for o in TAB}, seconds=time.time() - t0)
    json.dump(rep, open(HERE / 'stress_ext2.json', 'w'), indent=1, default=str)
    if viol:
        print(f'\nSTRESS EXT2 FAILED: {len(viol)} violations', viol[:10], file=sys.stderr); sys.exit(1)
    print(f'\nSTRESS EXT2 PASSED: {len(jobs)} circuits, {sum(nph.values())} phases, 0 violations of the batch-1, HUB and DARK rows and of O1, {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
