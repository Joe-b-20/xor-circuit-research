#!/usr/bin/env python3
"""qcert3 generator (G = 75): the FULL local systems (package + batch-1 + PK + FM + HUB2 split + DARK split), the LP
scan with the package driver, and exact integer Farkas certificates PER CASE.

Local system of a key (h, y, F, ori, q, z) and a case (hub, dark):
  columns  = the package's helper types (r,u,v), r+u+v >= 3 (certify75.system's list), MINUS, in a hub case A = a,
             the types with r <= 2 and u > (3 - r) + (q - a) (Lemma H2 / row HUB2: such helpers do not exist in that case),
             + [y0, y1, y2]  and, in a dark case, + [y2d, Fb, Fd]
  rows     = 1. the package rows (L1)-(L23), UNCHANGED, in certify75.system's order (imported from the package copy);
             2. the batch-1 rows of qcert (y split, N1, L7*, L12*, L13*, L14*, L15*, L17*, [L18*, L19*, L20*, L22*], I, [Q0]);
             3. the flat batch-3 rows: [q = 4: PK4] [q = 5: PK5], then for a0 = 0..q-1 the chord rows FM7(a0), FM9(a0)
                of finite fact FM (rank(C_l) over the labels f + c, f full);
             4. hub = ('eq', a):  sum_{r=3} u n = a  (two inequalities)   [A = a, a = 2..q];  hub = ('le', 1): sum_{r=3} u n <= 1;
             5. dark = d: L13d, L14d, L15d, L17Md | L17Td, L18d, bright lower, bright capacity, dark capacity, F budget,
                y2d <= y2, y2m <= C(q,2), (I'), [d = q: Fb = 0], [d = 0: Fd + y2d = 0]   (PROOF_ADDENDUM_2.md B.3-B.4).
  Cases of a key: hub in {None} if q <= 1, else {('eq', 2), ..., ('eq', q), ('le', 1)}; dark in {0, ..., q}.
  A key is excluded iff every leaf case (hub, dark) is infeasible.  A certificate for (hub, None) covers every
  (hub, d); one for (None, d) covers every (hub, d); one for (None, None) covers everything (Lemma C1).
A certificate is a nonnegative integer vector lambda over the rows of its case with lambda^T A >= 0 in every
column of the case and lambda^T b < 0.  Multipliers come from an LP (SciPy/HiGHS), are rationalized, scaled to
integers, gcd-reduced and verified here in exact integer arithmetic; the LP's status is never trusted for an
exclusion.  The second, independent checker is check_cases3.py.

Keys certified: (a) the 381 keys LP-feasible under the batch-2 system on the baseline (qcert2 surviving_keys) that the
full system kills; (b) qrealcheck's complete list of 1,661 keys LP-feasible under the batch-2 system anywhere in its
scan (keys_full.json) that the full system kills; (c) every key referenced by the coverage of a claim that the full
system excludes and the batch-2 system does not.

usage: nice -n 8 python3 gen_certs3.py      (writes CERTIFICATES_CASES75_B3.json, scan_cases3.json, keysfull3.json, gen_certs3.log)
"""
import sys, json, time
from fractions import Fraction
from math import comb, lcm, gcd
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.optimize import linprog

SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
PKG = SPRINT / 'lb76/pkg_copy/source/lower_bounds/checks'
HERE = SPRINT / 'qcert3'
sys.path.insert(0, str(PKG))
import certify75   # noqa: E402  (package copy, unchanged; only system() and direct_exclusion() are used)
import lp_regen    # noqa: E402  (package copy, unchanged; only the run() driver is used)

G = 75
KR = {0: 3, 1: 2, 2: 1}      # finite fact H2 / Lemma H2: a helper with r <= 2 has at most 3 - r full-met missing labels
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
# finite fact FM: rank(C_l) histogram over the DISTINCT labels f + c (f a full value, c in B); qreal/fullmet.py,
# qhubcheck/fm_check.py and qcert3/fm_tab3.py agree.  top(a) = sum of the a largest ranks, top3(a) = sum of the a
# largest values of min(3, rank - 1).
FM_HIST = {'M': {7: 4, 6: 108, 5: 140, 4: 692, 3: 3696}, 'Mt': {6: 216, 5: 144, 4: 1176, 3: 4960}}
LOG = [None]
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True)
    if LOG[0] is None: LOG[0] = open(HERE / 'gen_certs3.log', 'a')
    LOG[0].write(s + '\n'); LOG[0].flush()


def fm_tables(ori, n=20):
    ranks = sorted((r for r, c in FM_HIST[ori].items() for _ in range(c)), reverse=True)
    top = [0]; top3 = [0]
    for r in ranks[:n]: top.append(top[-1] + r)
    for r in sorted((min(3, r - 1) for r in ranks), reverse=True)[:n]: top3.append(top3[-1] + r)
    return top, top3
FMTAB = {o: fm_tables(o) for o in ('M', 'Mt')}


def hub_cases(q):
    """the HUB2 split: for q <= 1 no split (u <= q <= 3 - r + q - 1 for every r <= 2 whatever A is); for q >= 2 the
    cases A = 2, ..., q (column deletion) and A <= 1 (no deletion)."""
    if q <= 1: return [None]
    return [('eq', a) for a in range(2, q + 1)] + [('le', 1)]


def dark_cases(q): return list(range(q + 1))


def ext_system(key, hub=None, dark=None):
    """(types, aux, A, B, names, n_pkg, n_b1, n_flat): rows as <= constraints over columns types + aux."""
    h, y, F, ori, q, z = key
    types0, A0, B0, names0 = certify75.system(key)
    if hub is not None and hub[0] == 'eq':
        keep = [j for j, (r, u, v) in enumerate(types0) if not (r < 3 and u > KR[r] + q - hub[1])]
    else:
        keep = list(range(len(types0)))
    types = [types0[j] for j in keep]
    aux = ['y0', 'y1', 'y2'] + (['y2d', 'Fb', 'Fd'] if dark is not None else [])
    A = [[row[j] for j in keep] + [0] * len(aux) for row in A0]; B = list(B0); names = list(names0)
    n_pkg = len(A)
    def fmin(r, u, v): return max(0, (r + u + v - 3) // 2)
    def d0(r, u): return (u - 1) if r == 0 else 0
    def ovf(r, u): return max(0, u - 2) if r == 3 else 0
    def add(name, fn, b, **ax):
        for a in ax: assert a in aux, (name, a)
        A.append([fn(r, u, v) for r, u, v in types] + [ax.get(a, 0) for a in aux]); B.append(b); names.append(name)
    rho6, rho, eps = RHO6[ori], RHO[ori], EPS[ori]
    # ---- batch-1 rows (qcert/gen_certs.py ext_system, same text and order)
    add('y split <=', lambda r, u, v: 0, y, y0=1, y1=1, y2=1)
    add('y split >=', lambda r, u, v: 0, -y, y0=-1, y1=-1, y2=-1)
    add('N1 full helper labels distinct', lambda r, u, v: 3 if r == 3 else 0, G - 32 - h - q)
    add('L7* label rank capacity (+y1)', lambda r, u, v: r * u, 7 * q, y1=1)
    add('L12* boundary R6 rank (+y0)', lambda r, u, v: max(0, r - 1), rho6, y0=1)
    add('L13* quotient rank capacity', lambda r, u, v: r * u - 2 * d0(r, u), 2 * z + 7 * q - 2 * rho, y1=1, y2=-2)
    add('L14* quotient full capacity', lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * d0(r, u), 2 * z + 7 * q - 2 * rho + eps, y1=1, y2=-2)
    add('L15* quotient excess capacity', lambda r, u, v: max(0, r - 1) * u - d0(r, u), z + 3 * q - rho, y2=-1)
    if ori == 'M':
        add('L17-M* quotient joint deficit', lambda r, u, v: 2 * max(0, r - 1) * u + 2 * ovf(r, u) - 3 * d0(r, u), 3 * z + 6 * q - 24, y2=-3)
    else:
        add('L17-Mt* quotient joint deficit', lambda r, u, v: max(0, r - 1) * u + ovf(r, u) - 3 * d0(r, u), 3 * z + 3 * q - 12, y2=-3)
        add('L18* quotient full strengthened', lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * d0(r, u), 3 * z + 7 * q - 12, y2=-3)
        add('L19* dark repeated pairs', lambda r, u, v: -(u + v - 1) if r == 0 else (-v if r == 1 else 0), -3, y2=-1)
        add('L20* dark quotient rank', lambda r, u, v: -(3 * u + v - 3) if r == 0 else 0, 2 * z - 9, y2=-3)
        if q == 0:
            add('L22* short boundary rank', lambda r, u, v: -(v - 1) if r == 0 else 0, -3, y2=-1)
    add('I missing incidence (ee)', lambda r, u, v: u + 2 * fmin(r, u, v), 4 * q + 2 * F, y1=1, y2=1)
    if q == 0:
        add('Q0 unanchored vs HH', lambda r, u, v: int(r == 0), z - (32 - rho6))
    n_b1 = len(A) - n_pkg
    # ---- flat batch-3 rows: PK4 / PK5 (Lemma 10.4's argument at q = 4, 5) and the FM7 / FM9 chord rows (finite fact FM)
    if q == 4: add('PK4: #{u >= 3} <= 1', lambda r, u, v: int(u >= 3), 1)
    if q == 5: add('PK5: n3 + 2 n4 + 2 n5 <= 2', lambda r, u, v: {3: 1, 4: 2, 5: 2}.get(u, 0), 2)
    top, top3 = FMTAB[ori]
    for a0 in range(q):
        s = top[a0 + 1] - top[a0]; s3 = top3[a0 + 1] - top3[a0]
        add(f'FM7 chord {a0}: W + y1 + (7-{s}) A <= 7q + {top[a0] - s * a0}',
            lambda r, u, v, s=s: r * u + ((7 - s) * u if r == 3 else 0), 7 * q + top[a0] - s * a0, y1=1)
        add(f'FM9 chord {a0}: Z + (3-{s3}) A <= 3q + {top3[a0] - s3 * a0}',
            lambda r, u, v, s3=s3: max(0, r - 1) * u + ((3 - s3) * u if r == 3 else 0), 3 * q + top3[a0] - s3 * a0)
    n_flat = len(A) - n_pkg - n_b1
    # ---- HUB2 case rows (Lemma H2; the column deletion above is the other half of the case)
    if hub is not None:
        Afn = lambda r, u, v: u if r == 3 else 0
        if hub[0] == 'eq':
            add(f'HUB2 A = {hub[1]} <=', Afn, hub[1])
            add(f'HUB2 A = {hub[1]} >=', lambda r, u, v: -Afn(r, u, v), -hub[1])
        else:
            assert hub == ('le', 1)
            add('HUB2 A <= 1', Afn, 1)
    # ---- DARK case rows: exactly d dark labels (PROOF_ADDENDUM_2.md B.3-B.4), unchanged from qcert2
    if dark is not None:
        d = dark
        add(f'L13d qD={d}', lambda r, u, v: r * u - 2 * d0(r, u), 2 * z + 7 * q - 2 * rho - 9 * d, y1=1, y2=-2)
        add(f'L14d qD={d}', lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * d0(r, u), 2 * z + 7 * q - 2 * rho + eps - 9 * d, y1=1, y2=-2)
        add(f'L15d qD={d}', lambda r, u, v: max(0, r - 1) * u - d0(r, u), z + 3 * q - rho - 4 * d, y2=-1)
        if ori == 'M':
            add(f'L17Md qD={d}', lambda r, u, v: 2 * max(0, r - 1) * u + 2 * ovf(r, u) - 3 * d0(r, u), 3 * z + 6 * q - 24 - 9 * d, y2=-3)
        else:
            add(f'L17Td qD={d}', lambda r, u, v: max(0, r - 1) * u + ovf(r, u) - 3 * d0(r, u), 3 * z + 3 * q - 12 - 6 * d, y2=-3)
            add(f'L18d qD={d}', lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * d0(r, u), 3 * z + 7 * q - 12 - 10 * d, y2=-3)
        add(f'bright lower qD={d}', lambda r, u, v: -(u if r >= 1 else 0), -(q - d))
        add(f'bright capacity qD={d}', lambda r, u, v: (u if r >= 1 else 0), 4 * (q - d), y1=1, Fb=-2)
        add(f'dark capacity qD={d}', lambda r, u, v: 0, 4 * d, y2d=1, Fd=-2)
        add('F budget Fb + Fd + F_H <= F', fmin, F, Fb=1, Fd=1)
        add('y2d <= y2', lambda r, u, v: 0, 0, y2d=1, y2=-1)
        add('y2m <= C(q,2)', lambda r, u, v: 0, comb(q, 2), y2=1, y2d=-1)
        add("(I') y1 + 2 y2 - y2d + U + 2 F_H <= 4q + 2F", lambda r, u, v: u + 2 * fmin(r, u, v), 4 * q + 2 * F, y1=1, y2=2, y2d=-1)
        if d == q: add('no bright labels: Fb = 0', lambda r, u, v: 0, 0, Fb=1)
        if d == 0: add('no dark labels: Fd = y2d = 0', lambda r, u, v: 0, 0, Fd=1, y2d=1)
    return types, aux, A, B, names, n_pkg, n_b1, n_flat


def exact_ok(ints, A, B):
    """pure integer check: lambda >= 0 integers, lambda^T A >= 0 per column, lambda^T b < 0."""
    if len(ints) != len(A) or any((type(w) is not int) or w < 0 for w in ints): return False
    ncol = len(A[0])
    for j in range(ncol):
        if sum(w * row[j] for w, row in zip(ints, A)) < 0: return False
    return sum(w * b for w, b in zip(ints, B)) < 0


def rationalize(lam, A, B):
    for den in (10 ** 3, 10 ** 4, 10 ** 6, 10 ** 8, 10 ** 10, 10 ** 12):
        ws = [Fraction(float(w)).limit_denominator(den) for w in lam]
        ws = [w if w > 0 else Fraction(0) for w in ws]
        if not any(ws): continue
        scale = lcm(*(w.denominator for w in ws))
        ints = [int(w * scale) for w in ws]
        g = gcd(*ints)
        ints = [w // g for w in ints]
        if exact_ok(ints, A, B): return ints
    return None


def farkas_int(key, hub, dark, rows='all'):
    """Farkas LP (min sum lambda, -A^T lambda <= 0, b^T lambda = -1, lambda >= 0) over a prefix of the rows of the case
    ('package': the package rows; 'batch1': package + batch-1 rows; 'all': every row of the case).  Returns
    (status, ints): 'cert' (exact integer certificate over ALL rows of the case, zeros on unused rows), 'feasible'
    (the Farkas LP is infeasible, i.e. the primal system over those rows is LP-feasible), 'fail', 'unknown'."""
    types, aux, A, B, names, n_pkg, n_b1, n_flat = ext_system(key, hub, dark)
    if rows == 'package': A_use, B_use = A[:n_pkg], B[:n_pkg]
    elif rows == 'batch1': A_use, B_use = A[:n_pkg + n_b1], B[:n_pkg + n_b1]
    else: A_use, B_use = A, B
    AA = np.array(A_use, float); m = len(A_use)
    x = None
    for method in ('highs', 'highs-ds', 'highs-ipm'):
        res = linprog(np.ones(m), A_ub=-AA.T, b_ub=np.zeros(AA.shape[1]), A_eq=np.array([B_use], float), b_eq=[-1.0],
                      bounds=(0, None), method=method)
        if res.status == 0: x = res.x; break
        if res.status == 2: return 'feasible', None
    if x is None: return 'unknown', None
    ints = rationalize(x, A_use, B_use)
    if ints is None:
        res = linprog(np.zeros(m), A_ub=-AA.T, b_ub=np.zeros(AA.shape[1]), A_eq=np.array([B_use], float), b_eq=[-1.0], bounds=(0, None), method='highs')
        if res.status == 0: ints = rationalize(res.x, A_use, B_use)
    if ints is None: return 'fail', None
    ints = ints + [0] * (len(A) - len(ints))
    assert exact_ok(ints, A, B), ('padded certificate fails', key, hub, dark)
    return 'cert', ints


# ---------------------------------------------------------------- feasibility (primal LP) and the package driver
CACHE = {}
def feas_case(key, hub, dark):
    k = (key, hub, dark)
    if k in CACHE: return CACHE[k]
    types, aux, A, B, names, n_pkg, n_b1, n_flat = ext_system(key, hub, dark)
    res = linprog(np.zeros(len(A[0])), A_ub=np.array(A, float), b_ub=np.array(B, float), bounds=(0, None), method='highs')
    if res.status == 2: out = False
    elif res.status == 0: out = True
    else:
        log('LP status', res.status, key, hub, dark); out = True
    CACHE[k] = out; return out


def prefilter(key):
    h, y, F, ori, q, z = key
    return not (certify75.direct_exclusion(key) or 2 * h + y + z + comb(q, 2) < 32)


def feasible_full(key):
    """full system: feasible iff some leaf case (hub, dark) is LP-feasible."""
    if not prefilter(key): return False
    if not feas_case(key, None, None): return False
    q = key[4]
    for hc in hub_cases(q):
        if hc is not None and not feas_case(key, hc, None): continue
        for d in dark_cases(q):
            if feas_case(key, hc, d): return True
    return False


RECORD = {}
from functools import lru_cache
@lru_cache(None)
def feasible_for_driver(h, y, F, q, z, ori):
    r = feasible_full((h, y, F, ori, q, z)); RECORD[(h, y, F, ori, q, z)] = r; return r
lp_regen.feasible = feasible_for_driver


def certify_key(key):
    """the certificate tree of one key.  Returns (kind, certs, problem): kind in 'package', 'batch1', 'flat', 'case',
    'feasible' (some leaf case is LP-feasible: the key is NOT excluded), 'fail'; certs = [(hub, dark, ints)]."""
    q = key[4]
    st, ints = farkas_int(key, None, None, 'package')
    if st == 'cert': return 'package', [(None, None, ints)], None
    st, ints = farkas_int(key, None, None, 'batch1')
    if st == 'cert': return 'batch1', [(None, None, ints)], None
    st, ints = farkas_int(key, None, None, 'all')
    if st == 'cert': return 'flat', [(None, None, ints)], None
    if st != 'feasible': return 'fail', [], ('flat', st)
    certs = []
    for hc in hub_cases(q):
        if hc is not None:
            st, ints = farkas_int(key, hc, None)
            if st == 'cert': certs.append((hc, None, ints)); continue
            if st != 'feasible': return 'fail', certs, (hc, None, st)
        for d in dark_cases(q):
            st, ints = farkas_int(key, hc, d)
            if st == 'cert': certs.append((hc, d, ints))
            elif st == 'feasible': return 'feasible', certs, (hc, d)
            else: return 'fail', certs, (hc, d, st)
    return 'case', certs, None


conv = lambda k: (k[0], k[1], k[2], k[5], k[3], k[4])      # (h,y,F,q,z,ori) file order -> (h,y,F,ori,q,z)


def main():
    t0 = time.time()
    # finite fact FM: the tables used here equal qreal's and qhubcheck's
    for o in ('M', 'Mt'):
        qr = json.load(open(SPRINT / f'qreal/fullmet_{o}.json')); qh = json.load(open(SPRINT / f'qhubcheck/fm_tab_{o}.json'))
        assert {int(k): v for k, v in qr['hist'].items()} == FM_HIST[o] == {int(k): v for k, v in qh['hist'].items()}, o
        n = min(len(qr['top']), len(qh['top']), len(FMTAB[o][0]))
        assert qr['top'][:n] == qh['top'][:n] == FMTAB[o][0][:n] and qr['top3'][:n] == qh['top3'][:n] == FMTAB[o][1][:n], o
    log('FM tables: histogram and top / top3 identical to qreal and qhubcheck; top(M) =', FMTAB['M'][0][:12], 'top(Mt) =', FMTAB['Mt'][0][:12])
    # 1. the scan with the package's own driver (lp_regen.run) under the full system
    states, claims_full, surv_full = lp_regen.run(G)
    sf = {(st, o) for st, o, k, l in surv_full}
    log(f'full scan: scalar states {len(states)}, oriented claims {len(claims_full)}; survivors {len(sf)} '
        f'(M {sum(1 for s, o in sf if o == "M")}); keys touched {len(RECORD)}, LP-feasible {sum(RECORD.values())}; {time.time()-t0:.0f}s')
    # the batch-2 scan of qcert2 (its full_survivors = the 996 of qreal / qrealcheck) is the baseline of this batch
    q2 = json.load(open(SPRINT / 'qcert2/scan_cases75.json'))
    assert [tuple(s) for s in q2['states']] == sorted(states) or {tuple(s) for s in q2['states']} == set(states)
    sb2 = {(tuple(st), o) for st, o in q2['full_survivors']}
    claims_b2 = {(tuple(c['state']), c['orientation']): tuple(c['full']) for c in q2['claims']}
    assert sf <= sb2, 'full survivors not a subset of the batch-2 survivors'
    excluded = sorted(sb2 - sf)
    for c in claims_full:
        kb, lb, db = claims_b2[c]; ke, le, de = claims_full[c]
        assert ke >= kb and (ke > kb or le >= lb), (c, claims_b2[c], claims_full[c])
    log(f'batch-2 survivors {len(sb2)} (qcert2 = qreal = qrealcheck); full survivors {len(sf)}; newly excluded claims {len(excluded)} '
        f'(M {sum(1 for s, o in excluded if o == "M")}); bounds monotone on all {len(claims_full)} claims')
    # 2. the keys: baseline 381 (qcert2) and qrealcheck's complete batch-2-feasible list (1,661)
    c2 = json.load(open(SPRINT / 'qcert2/CERTIFICATES_CASES75.json'))
    base381 = sorted(tuple(k) for k in c2['surviving_keys']); assert len(base381) == 381
    kf = json.load(open(SPRINT / 'qrealcheck/keys_full.json'))
    full1661 = sorted(conv(tuple(k)) for k in kf['feasible']); assert len(full1661) == 1661
    base = sorted(set(base381) | set(full1661))
    killed = [k for k in base if not feasible_full(k)]
    surviving = [k for k in base if feasible_full(k)]
    bkilled = [k for k in base381 if not feasible_full(k)]; bsurv = [k for k in base381 if feasible_full(k)]
    log(f'batch-2-feasible keys: baseline {len(base381)}, complete list {len(full1661)}, union {len(base)}; killed by the full system '
        f'{len(killed)} (baseline {len(bkilled)}), surviving {len(surviving)} (baseline {len(bsurv)}); {time.time()-t0:.0f}s')
    # 3. keys referenced by the coverage of the newly excluded claims (certify75.verify's enumeration)
    needed = {}
    for st, ori in excluded:
        a, b, Y, V, he, ho, le_, lo_, Se, So, budget = st
        k, l, dead = claims_full[(st, ori)]
        assert dead and (k > Se or l > So or k + l > budget)
        other = 'Mt' if ori == 'M' else 'M'
        for h, y, F, o, least, greatest, claimed in ((he, Y, V, ori, le_, Se, k), (ho, V, Y, other, lo_, So, l)):
            for s in range(least, min(claimed - 1, greatest) + 1):
                for q in range(s + 1):
                    z = s - q
                    if 2 * h + y + z + comb(q, 2) < 32: continue
                    key = (h, y, F, o, q, z)
                    if certify75.direct_exclusion(key): continue
                    assert not feasible_full(key), ('referenced key feasible?!', key)
                    needed[key] = True
    log(f'coverage of the {len(excluded)} claims references {len(needed)} distinct keys; {time.time()-t0:.0f}s')
    # complete bookkeeping of the scan (every key the driver touched)
    feas = {k for k, v in RECORD.items() if v}
    lb = set()
    for st, ori, k, ell in surv_full:
        other = 'Mt' if ori == 'M' else 'M'
        for q in range(0, k + 1):
            kk = (st[4], st[2], st[3], ori, q, k - q)
            if kk in feas: lb.add(kk)
        for q in range(0, ell + 1):
            kk = (st[5], st[3], st[2], other, q, ell - q)
            if kk in feas: lb.add(kk)
    log(f'scan bookkeeping: keys touched {len(RECORD)}; LP-feasible {len(feas)} (by q {sorted(Counter(k[4] for k in feas).items())}; by ori {dict(Counter(k[3] for k in feas))}); '
        f'load-bearing {len(lb)} (by q {sorted(Counter(k[4] for k in lb).items())}; by ori {dict(Counter(k[3] for k in lb))})')
    json.dump(dict(touched=len(RECORD), feasible=sorted(list(k) for k in feas), load_bearing=sorted(list(k) for k in lb)), open(HERE / 'keysfull3.json', 'w'))
    json.dump({'G': G, 'states': [list(s) for s in states],
               'claims': [{'state': list(st), 'orientation': o, 'batch2': list(claims_b2[(st, o)]), 'full': list(claims_full[(st, o)])} for st, o in sorted(claims_full)],
               'batch2_survivors': [[list(st), o] for st, o in sorted(sb2)], 'full_survivors': [[list(st), o] for st, o in sorted(sf)],
               'full_survivor_bounds': [[list(st), o, k, l] for st, o, k, l in sorted(surv_full)]},
              open(HERE / 'scan_cases3.json', 'w'))
    # 4. certificates: every killed key + every referenced key, per case; the baseline killed keys first
    todo = sorted(set(bkilled)) + sorted(set(needed) - set(bkilled)) + sorted(set(killed) - set(bkilled) - set(needed))
    certs = []; failed = []; kinds = {}; max_rhs = -10 ** 9; n_mult = 0; n_coef = 0; per_key_cases = {}
    for i, key in enumerate(todo):
        try:
            kind, kc, problem = certify_key(key)
        except Exception as ex:                      # noqa: BLE001
            kind, kc, problem = 'fail', [], repr(ex)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind in ('feasible', 'fail'):
            failed.append([list(key), kind, str(problem)]); log('  NOT CERTIFIED', key, kind, problem)
        else:
            per_key_cases[key] = len(kc)
        for hub, dark, ints in kc:
            types, aux, A, B, names, n_pkg, n_b1, n_flat = ext_system(key, hub, dark)
            assert exact_ok(ints, A, B)
            if kind == 'package': assert not any(ints[n_pkg:])
            if kind == 'batch1': assert any(ints[n_pkg:n_pkg + n_b1]) and not any(ints[n_pkg + n_b1:])
            if kind == 'flat': assert any(ints[n_pkg + n_b1:n_pkg + n_b1 + n_flat])
            rhs = sum(w * b for w, b in zip(ints, B)); max_rhs = max(max_rhs, rhs)
            n_mult += len(ints); n_coef += len(A[0])
            certs.append({'key': list(key), 'kind': kind, 'hub': list(hub) if hub else None, 'dark': dark, 'weights': ints})
        if (i + 1) % 100 == 0: log(f'  {i+1}/{len(todo)} keys, {len(certs)} certificates, kinds {kinds}, {time.time()-t0:.0f}s')
    n_case_certs = sum(1 for c in certs if c['kind'] == 'case')
    log(f'keys to certify {len(todo)} (killed {len(killed)} [baseline {len(bkilled)}], referenced {len(needed)}, both {len(set(killed) & set(needed))}); '
        f'kinds {kinds}; certificates {len(certs)} ({n_case_certs} per-case); not certified {len(failed)}; largest weighted rhs {max_rhs}; '
        f'multipliers {n_mult}; coefficients checked {n_coef}; {time.time()-t0:.0f}s')
    kind_of = {}
    for c in certs: kind_of.setdefault(tuple(c['key']), c['kind'])
    log('killed keys by certificate kind:', dict(Counter(kind_of.get(k) for k in killed)), '; baseline killed:', dict(Counter(kind_of.get(k) for k in bkilled)))
    out = {
        'gates': G, 'hub_capacity': {'0': 3, '1': 2, '2': 1}, 'fm_hist': {o: {str(k): v for k, v in FM_HIST[o].items()} for o in FM_HIST},
        'fm_top': {o: FMTAB[o][0] for o in FMTAB}, 'fm_top3': {o: FMTAB[o][1] for o in FMTAB},
        'system': 'package rows (L1)-(L23) as certify75.system, unchanged; then qcert batch-1 rows: y split (=), N1, L7*, L12*, L13*, '
                  'L14*, L15*, L17-M* | L17-Mt*, L18*, L19*, L20*, [q=0: L22*], I, [q=0: Q0]; then the flat batch-3 rows: [q=4: PK4] [q=5: PK5], '
                  'FM7 chord a0, FM9 chord a0 for a0 = 0..q-1; then the case rows: hub ("eq", a): A = a (two inequalities) with the columns '
                  '(r <= 2, u > 3 - r + q - a) removed; hub ("le", 1): A <= 1; dark d: L13d, L14d, L15d, L17Md | L17Td, L18d, bright lower, '
                  'bright capacity, dark capacity, F budget, y2d <= y2, y2m <= C(q,2), (I\'), [d = q: Fb = 0], [d = 0: Fd + y2d = 0]; '
                  'columns = helper types + [y0, y1, y2] (+ [y2d, Fb, Fd] in a dark case)',
        'cases': 'hub cases: none if q <= 1, else A = 2..q and A <= 1 (Lemma H2 / row HUB2); dark cases: q_D = 0..q.  A key is excluded iff '
                 'every leaf (hub, dark) has a certificate; a certificate with dark = null covers all dark cases of its hub case; one with '
                 'hub = null covers all hub cases of its dark case; one with hub = null and dark = null covers every case.',
        'baseline_keys': [list(k) for k in base381],
        'batch2_feasible_keys': [list(k) for k in base],
        'batch2_feasible_keys_sources': {'qcert2_surviving_381': 381, 'qrealcheck_keys_full_1661': 1661, 'union': len(base)},
        'killed_keys': [list(k) for k in killed],
        'surviving_keys': [list(k) for k in surviving],
        'baseline_killed_keys': [list(k) for k in bkilled],
        'baseline_surviving_keys': [list(k) for k in bsurv],
        'claims': [{'state': list(st), 'orientation': ori, 'lower_even': claims_full[(st, ori)][0], 'lower_odd': claims_full[(st, ori)][1],
                    'batch2_lower_even': claims_b2[(st, ori)][0], 'batch2_lower_odd': claims_b2[(st, ori)][1]} for st, ori in excluded],
        'certificates': certs,
        'uncertified': failed,
        'counts': {'scalar_states': len(states), 'oriented_claims': len(claims_full), 'batch2_survivors': len(sb2), 'full_survivors': len(sf),
                   'newly_excluded_claims': len(excluded), 'baseline_keys': len(base381), 'batch2_feasible_keys': len(base),
                   'killed_keys': len(killed), 'surviving_keys': len(surviving), 'baseline_killed': len(bkilled), 'baseline_surviving': len(bsurv),
                   'referenced_keys': len(needed), 'keys_certified': len(per_key_cases),
                   'key_kinds': kinds, 'certificates': len(certs), 'case_certificates': n_case_certs,
                   'failed': len(failed), 'largest_rhs': max_rhs, 'multipliers': n_mult, 'coefficients_checked': n_coef,
                   'keys_touched': len(RECORD), 'keys_lp_feasible': len(feas), 'keys_load_bearing': len(lb)},
    }
    json.dump(out, open(HERE / 'CERTIFICATES_CASES75_B3.json', 'w'))
    log('written CERTIFICATES_CASES75_B3.json, scan_cases3.json, keysfull3.json; total', f'{time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
