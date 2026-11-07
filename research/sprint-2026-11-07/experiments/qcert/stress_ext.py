#!/usr/bin/env python3
"""qcert: stress test of the NEW rows on real circuits (an extension of the package's stress.py, which is
imported unchanged from the copy stress_pkg.py; the original is not touched).

For every circuit C and its orbit C, T(C), T(T(C)), T^3(C) (step 0 is the raw circuit, steps 1-3 canonical
transposes), every package identity/row of stress_pkg.check_rows is re-asserted, and the following new
quantities and rows are evaluated (slack = right side - left side, must be >= 0):

  N1        3 n3 <= x + y - q
  L7*       W + y1 <= 7q ;  per missing label: W_l + Y_l <= rank(C_l) <= 7
  L12*      sum (r-1)_+ n + y0 <= rho6
  G*_R6     32 - rho6 <= y2 + z + D0 - qD + sum_bright k_l(R6)
  G*_J      32 - dim J <= y2 + z + D0 - qD + sum_bright k_l(J),  J the package's F9 space (dim 24 M / 28 Mt)
  I         y1 + y2 + U + 2 F_H <= 4q + 2F ;  per missing label: U_l + V_l + ee_l <= 4 + 2 f_l
  L13*..L15*, L17*, L18*, L19*, L20*, L22*   the package rows with y -> y2 (and +y1 in L13*, L14*)
  L13*/L14* per bright label:  W_l + Y_l + 2 k_l(J) <= 7 ;  W_l + Y_l + A_l + 2 k_l(J) <= 7 + ex_l, sum ex_l <= eps
  Q0        q = 0  =>  z >= 32 - rho6 + h0
  Lemma S   per represented label l met by a helper: sum_{i meets l} (r_i - 1)_+ <= sigma(P_l)
  S2        a represented label met by a helper with r >= 2 is rich (sigma >= 2); 6 n3 + 2 n2 <= top(x+y-q)
  kinds     y0 + y1 + y2 = y; each kind-0 gate reduces to a weight-6 zero-sum set in R6; each kind-1 gate
            to a 2- or 4-form of its (bright) missing label
Also recomputed here from the matrix: rho6, F6's rank(C_l) <= 7, F9's dim J and k_l, S1's sigma histogram.

usage: nice -n 8 python3 stress_ext.py [N_REAL]       (default: all 303 real circuits of bridge/profiles.json)
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert'
sys.path.insert(0, str(HERE))
from stress_pkg import Circuit, BOUNDARY, parity, check_rows, PAIRVALS   # noqa: E402  (package stress.py, copied unchanged)
from profile_real_copy import reconstruct                                 # noqa: E402  (bridge reconstruction, copied unchanged)

RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}; DIMJ = {'M': 24, 'Mt': 28}


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
    """boundary tables: R6 basis, forms per label value, rank(C_l), K_l differences, J (F9), sigma per pair, top(m)."""
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
    # sigma(P): rank of the weight-6 zero-sum sets containing the pair P
    sixl = list(six); sigma = {}
    for i, j in itertools.combinations(range(64), 2):
        m = (1 << i) | (1 << j)
        sigma[m] = rank_of([s for s in sixl if s & m == m])
    hist = Counter(sigma.values())
    top = [0]
    for s in sorted(sigma.values(), reverse=True): top.append(top[-1] + s)
    TAB[ori] = dict(B=B, idx=idx, R6=R6, forms=forms, rankC=rankC, J=J, sigma=sigma, sigma_hist=dict(hist), top=top)
    print(f'  tables {ori}: rho6 {R6.dim()}, dim J {J.dim()}, sigma histogram {dict(sorted(hist.items()))}, {time.time()-t0:.1f}s', flush=True)
    return TAB[ori]


def k_mod(ori, label, space):
    """dim((K_l + space)/space), K_l = differences of the 2/4-forms of the label value."""
    T = tables(ori); fs = T['forms'].get(label, [])
    if len(fs) < 2: return 0
    bs = space.copy(); k = 0
    for f in fs[1:]:
        if bs.add(fs[0] ^ f): k += 1
    return k


def phase(C, I):
    """new-row slacks for one phase (C a package Circuit, I = C.analyse()). Returns dict name -> slack (>= 0 required)."""
    ori = C.ori; T = tables(ori); B = I['B']; H = set(I['H']); q, z, y, F, F_H = I['q'], I['z'], I['y'], I['F'], I['F_H']
    rho6, rho, eps = RHO6[ori], RESERVE[ori], EPS[ori]
    edges = []
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e))
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    bb = {}
    for p, qq, e in edges:
        if p in B and qq in B: bb[e] = (p, qq)
    missing = [e for e in evens if e not in bb]
    assert len(missing) == q
    rtype = {v: [0, 0, 0] for v in H}
    Ul = Counter(); Vl = Counter(); eel = Counter(); meets = defaultdict(list)     # meets[l] = helpers with a missing H-B edge of label l
    rep_meets = defaultdict(list)                                                   # represented label -> helpers with an H-B edge of that label
    for p, qq, e in edges:
        hs = [v for v in (p, qq) if v in H]
        if len(hs) == 2:
            for v in hs: rtype[v][2] += 1
            Vl[e] += 1
        elif len(hs) == 1:
            v = hs[0]
            if e in bb: rtype[v][0] += 1; rep_meets[e].append(v)
            else: rtype[v][1] += 1; Ul[e] += 1; meets[e].append(v)
    anchored = {v for v in H if rtype[v][0] >= 1}
    bright = {e for e in missing if any(v in anchored for v in meets[e])}
    dark = [e for e in missing if e not in bright]
    h0 = sum(1 for v in H if rtype[v][0] == 0); U0 = sum(rtype[v][1] for v in H if rtype[v][0] == 0); D0 = U0 - h0
    qD = len(dark); n3 = sum(1 for v in H if rtype[v][0] == 3); n2 = sum(1 for v in H if rtype[v][0] == 2)
    W = sum(r * u for r, u, v in rtype.values()); A = sum(u for r, u, v in rtype.values() if r == 3)
    Z = sum(max(0, r - 1) * u for r, u, v in rtype.values()); E = sum(max(0, u - 2) for r, u, v in rtype.values() if r == 3)
    U = sum(u for r, u, v in rtype.values())
    # even+even gates by kind
    y0 = y1 = y2 = 0; Yl = Counter(); kind_checks = 0
    pairmask = lambda e: (1 << T['idx'][C.mask[bb[e][0]]]) | (1 << T['idx'][C.mask[bb[e][1]]])
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] or C.odd[b]: continue
        for e in (a, b, s): eel[e] += 1
        miss = [e for e in (a, b, s) if e not in bb]
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
    assert y0 + y1 + y2 == y
    kR6 = {e: k_mod(ori, C.mask[e], T['R6']) for e in bright}
    kJ = {e: k_mod(ori, C.mask[e], T['J']) for e in bright}
    sl = {}
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
    # per-label strong forms
    l7 = []; i_lab = []; l13 = []; l14 = []; ex_sum = 0
    for e in missing:
        Wl = sum(rtype[v][0] for v in meets[e]); rc = T['rankC'].get(C.mask[e], 1)
        l7.append(rc - Wl - Yl[e]); assert rc <= 7
        i_lab.append(4 + 2 * I['f'][e] - (Ul[e] + Vl[e] + eel[e]))
        if e in bright:
            Al = int(any(rtype[v][0] == 3 for v in meets[e]))
            l13.append(7 - 2 * kJ[e] - Wl - Yl[e])
            ex = Wl + Yl[e] + Al + 2 * kJ[e] - 7
            l14.append(7 - (Wl + Yl[e] + Al + 2 * kJ[e]) + max(0, ex)); ex_sum += max(0, ex)
            assert rc + 2 * kJ[e] <= 7                                   # F9 (for the labels occurring)
    sl['L7*_label'] = min(l7, default=99); sl['I_label'] = min(i_lab, default=99)
    sl['L13*_label'] = min(l13, default=99); sl['L14*_label'] = min(l14, default=99); sl['L14*_ex'] = eps - ex_sum
    # Lemma S / S2
    s_sl = []; poor_at_r2 = 0
    for e, hs in rep_meets.items():
        sig = T['sigma'][pairmask(e)]
        s_sl.append(sig - sum(max(0, rtype[v][0] - 1) for v in hs))
        if any(rtype[v][0] >= 2 for v in hs) and sig < 2: poor_at_r2 += 1
    sl['LemmaS_label'] = min(s_sl, default=99); sl['S2_poor_at_r2'] = -poor_at_r2
    m = len(evens) - q
    sl['S2_aggregate'] = T['top'][min(m, len(T['top']) - 1)] - (6 * n3 + 2 * n2)
    facts = dict(ori=ori, x=I['x'], y=y, h=I['h'], q=q, z=z, F=F, n3=n3, n2=n2, y0=y0, y1=y1, y2=y2, h0=h0, D0=D0, qD=qD, W=W, U=U, kind_checks=kind_checks)
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
            for name, s in sl.items():
                key = (group, kind, ori, name)
                mins[key] = min(mins.get(key, 10 ** 9), s)
                if s < 0: viol.append((tag, step, ori, name, s))
                if s == 0: tight[(group, ori, name)] += 1
            for k in ('n3', 'y0', 'y1', 'y2', 'q', 'z', 'y', 'h', 'h0', 'qD'):
                fr = facts_range[(group, ori, k)]; fr[0] = min(fr[0], facts[k]); fr[1] = max(fr[1], facts[k])
        if (n + 1) % 50 == 0: print(f'  {n+1}/{len(jobs)} circuits, {len(viol)} violations, {time.time()-t0:.0f}s', flush=True)
    print(f'\nphases: {dict(nph)}; phases with q = 0: {q0}')
    print('\nminimum slack per new row (group, raw/canonical, orientation):')
    names = sorted({k[3] for k in mins})
    for name in names:
        parts = []
        for g in ('ctrl', 'real'):
            for kind in ('raw', 'canonical'):
                for ori in ('M', 'Mt'):
                    v = mins.get((g, kind, ori, name))
                    if v is not None: parts.append(f'{g}/{kind}/{ori}:{v}')
        print(f'  {name:14s} ' + '  '.join(parts))
    print('\nrows tight (slack 0) on some phase:', {f'{g}/{o}/{n}': c for (g, o, n), c in sorted(tight.items())})
    print('\nranges of the new quantities:', {f'{g}/{o}/{k}': tuple(v) for (g, o, k), v in sorted(facts_range.items())})
    rep = dict(circuits=len(jobs), controls=n_ctrl, real=len(jobs) - n_ctrl, phases=sum(nph.values()), q0_phases=q0,
               violations=viol, min_slack={'/'.join(map(str, k)): v for k, v in sorted(mins.items())},
               tight={'/'.join(k): v for k, v in sorted(tight.items())}, ranges={'/'.join(k): v for k, v in sorted(facts_range.items())},
               sigma_hist={o: TAB[o]['sigma_hist'] for o in TAB}, seconds=time.time() - t0)
    json.dump(rep, open(HERE / 'stress_ext.json', 'w'), indent=1, default=str)
    if viol:
        print(f'\nSTRESS EXT FAILED: {len(viol)} violations', viol[:10], file=sys.stderr); sys.exit(1)
    print(f'\nSTRESS EXT PASSED: {len(jobs)} circuits, {sum(nph.values())} phases, 0 violations of the new rows, {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
