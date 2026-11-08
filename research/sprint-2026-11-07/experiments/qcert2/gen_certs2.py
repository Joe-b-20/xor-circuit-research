#!/usr/bin/env python3
"""qcert2 generator (G = 75): the extended local systems WITH the HUB and DARK case splits, the two LP scans
(batch-1 system; batch-1 + HUB + DARK), and exact integer Farkas certificates PER CASE.

Local system of a key (h, y, F, ori, q, z) and a case (hub, dark):
  columns  = the package's helper types (r,u,v), r+u+v >= 3 (certify75.system's list), MINUS, in a hub case A = a,
             the types with r <= 2 and u > 4 + (q - a) (Lemma H1: such helpers do not exist in that case),
             + [y0, y1, y2]  and, in a dark case, + [y2d, Fb, Fd]
  rows     = the package rows (L1)-(L23), UNCHANGED, in certify75.system's order (imported from the package copy),
             then the batch-1 rows of qcert (y split, N1, L7*, L12*, L13*, L14*, L15*, L17*, [L18*, L19*, L20*, L22*],
             I, [Q0]) in qcert's order (PROOF_ADDENDUM.md A.6), then the case rows:
       hub = ('eq', a):   sum_{r=3} u n = a  (two inequalities)            [A = a, a = 5..q]
       hub = ('le', 4):   sum_{r=3} u n <= 4                                [A <= 4]
       dark = d:          L13d, L14d, L15d, L17Md | L17Td, L18d, bright lower, bright capacity, dark capacity,
                          F budget, y2d <= y2, y2m <= C(q,2), (I'), [d = q: Fb = 0], [d = 0: Fd + y2d = 0]
                          (PROOF_ADDENDUM_2.md, sections B.3-B.4; qreal/REPORT.md 4.1)
  Cases of a key: hub in {None} if q <= 4, else {('eq', 5), ..., ('eq', q), ('le', 4)}; dark in {0, ..., q}.
  A key is excluded iff every leaf case (hub, dark) is infeasible.  A certificate for (hub, None) covers every
  (hub, d); one for (None, None) covers everything.
A certificate is a nonnegative integer vector lambda over the rows of its case with lambda^T A >= 0 in every
column of the case and lambda^T b < 0.  Multipliers come from an LP (SciPy/HiGHS), are rationalized, scaled to
integers, gcd-reduced and verified here in exact integer arithmetic; the LP's status is never trusted for an
exclusion.  The second, independent checker is check_cases75.py.

usage: nice -n 8 python3 gen_certs2.py      (writes CERTIFICATES_CASES75.json, scan_cases75.json, gen_certs2.log)
"""
import sys, json, time
from fractions import Fraction
from math import comb, lcm, gcd
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
PKG = SPRINT / 'lb76/pkg_copy/source/lower_bounds/checks'
HERE = SPRINT / 'qcert2'
sys.path.insert(0, str(PKG))
import certify75   # noqa: E402  (package copy, unchanged; only system() and direct_exclusion() are used)
import lp_regen    # noqa: E402  (package copy, unchanged; only the scalar_states()/run()/first_s() driver is used)

G = 75; KAPPA = 4
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
LOG = [None]
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True)
    if LOG[0] is None: LOG[0] = open(HERE / 'gen_certs2.log', 'a')
    LOG[0].write(s + '\n'); LOG[0].flush()


def hub_cases(q):
    """the HUB split: for q <= 4 no split (the row is vacuous); for q >= 5 the cases A = 5, ..., q and A <= 4."""
    if q <= KAPPA: return [None]
    return [('eq', a) for a in range(KAPPA + 1, q + 1)] + [('le', KAPPA)]


def dark_cases(q): return list(range(q + 1))


def ext_system(key, hub=None, dark=None):
    """(types, aux, A, B, names, n_pkg, n_b1): rows as <= constraints over columns types + aux."""
    h, y, F, ori, q, z = key
    types0, A0, B0, names0 = certify75.system(key)
    if hub is not None and hub[0] == 'eq':
        umax = KAPPA + q - hub[1]
        keep = [j for j, (r, u, v) in enumerate(types0) if not (r < 3 and u > umax)]
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
    # ---- HUB case rows (Lemma H1; the column deletion above is the other half of the case)
    if hub is not None:
        Afn = lambda r, u, v: u if r == 3 else 0
        if hub[0] == 'eq':
            add(f'HUB A = {hub[1]} <=', Afn, hub[1])
            add(f'HUB A = {hub[1]} >=', lambda r, u, v: -Afn(r, u, v), -hub[1])
        else:
            assert hub == ('le', KAPPA)
            add(f'HUB A <= {KAPPA}', Afn, KAPPA)
    # ---- DARK case rows: exactly d dark labels (qreal/REPORT.md 4.1; PROOF_ADDENDUM_2.md B.3-B.4)
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
    return types, aux, A, B, names, n_pkg, n_b1


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
    """Farkas LP (min sum lambda, -A^T lambda <= 0, b^T lambda = -1, lambda >= 0) over the rows of the case
    ('package': the package rows only; 'all': every row of the case).  Returns (status, ints):
    status 'cert' (exact integer certificate over ALL rows of the case, zeros on unused rows),
    'feasible' (the Farkas LP is infeasible, i.e. the primal case system is LP-feasible), 'fail' (no exact
    certificate could be extracted), 'unknown' (solver trouble)."""
    types, aux, A, B, names, n_pkg, n_b1 = ext_system(key, hub, dark)
    if rows == 'package': A_use, B_use = A[:n_pkg], B[:n_pkg]
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
    types, aux, A, B, names, n_pkg, n_b1 = ext_system(key, hub, dark)
    res = linprog(np.zeros(len(A[0])), A_ub=np.array(A, float), b_ub=np.array(B, float), bounds=(0, None), method='highs')
    if res.status == 2: out = False
    elif res.status == 0: out = True
    else:
        log('LP status', res.status, key, hub, dark); out = True
    CACHE[k] = out; return out


def prefilter(key):
    h, y, F, ori, q, z = key
    return not (certify75.direct_exclusion(key) or 2 * h + y + z + comb(q, 2) < 32)


def feasible_b1(key):
    """the batch-1 system (package rows + qcert rows), no case split."""
    return prefilter(key) and feas_case(key, None, None)


def feasible_full(key):
    """batch-1 system + HUB split + DARK split: feasible iff some leaf case (hub, dark) is LP-feasible."""
    if not prefilter(key): return False
    if not feas_case(key, None, None): return False
    q = key[4]
    for hc in hub_cases(q):
        if hc is not None and not feas_case(key, hc, None): continue
        for d in dark_cases(q):
            if feas_case(key, hc, d): return True
    return False


MODE = [feasible_b1]
from functools import lru_cache
@lru_cache(None)
def feasible_for_driver(h, y, F, q, z, ori):
    return MODE[0]((h, y, F, ori, q, z))
lp_regen.feasible = feasible_for_driver


def certify_key(key):
    """the certificate tree of one key.  Returns (kind, certs, problem): kind in 'package', 'batch1', 'case',
    'feasible' (some leaf case is LP-feasible: the key is NOT excluded), 'fail'; certs = [(hub, dark, ints)]."""
    q = key[4]
    st, ints = farkas_int(key, None, None, 'package')
    if st == 'cert': return 'package', [(None, None, ints)], None
    st, ints = farkas_int(key, None, None, 'all')
    if st == 'cert': return 'batch1', [(None, None, ints)], None
    if st != 'feasible': return 'fail', [], ('batch1', st)
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


def main():
    t0 = time.time()
    # 1. the two scans with the package's own driver (lp_regen.run)
    MODE[0] = feasible_b1
    states, claims_b1, surv_b1 = lp_regen.run(G)
    MODE[0] = feasible_full; feasible_for_driver.cache_clear()
    states2, claims_full, surv_full = lp_regen.run(G)
    assert states == states2
    sb = {(st, o) for st, o, k, l in surv_b1}; sf = {(st, o) for st, o, k, l in surv_full}
    assert sf <= sb, 'full survivors not a subset of batch-1 survivors'
    excluded = sorted(sb - sf)
    log(f'scalar states {len(states)}, oriented claims {len(claims_b1)}; batch-1 survivors {len(sb)} '
        f'(M {sum(1 for s, o in sb if o == "M")}); full survivors {len(sf)} (M {sum(1 for s, o in sf if o == "M")}); '
        f'newly excluded claims {len(excluded)} (M {sum(1 for s, o in excluded if o == "M")}); {time.time()-t0:.0f}s')
    for c in claims_b1:
        kb, lb, db = claims_b1[c]; ke, le, de = claims_full[c]
        assert ke >= kb and (ke > kb or le >= lb), (c, claims_b1[c], claims_full[c])
    # cross-check of the batch-1 scan against qcert's scan file (same system, same driver)
    qc = json.load(open(SPRINT / 'qcert/scan_ext75.json'))
    qc_se = {(tuple(st), o) for st, o in qc['ext_survivors']}
    assert qc_se == sb, ('batch-1 survivors differ from qcert', len(qc_se), len(sb))
    qc_claims = {(tuple(c['state']), c['orientation']): tuple(c['ext']) for c in qc['claims']}
    assert all(qc_claims[c] == tuple(claims_b1[c]) for c in claims_b1), 'batch-1 (k, l) differ from qcert'
    # 2. the batch-1-feasible keys (qbound's GstarN1 list, 681) and those the case splits kill
    qb = json.load(open(SPRINT / 'qbound/scan_GstarN1_q0_g75.json'))
    b1_feasible = sorted((k[0], k[1], k[2], k[5], k[3], k[4]) for k in qb['keys_still_feasible'])   # file order (h,y,F,q,z,ori)
    assert all(feasible_b1(k) for k in b1_feasible), 'a batch-1-feasible key is infeasible in our batch-1 LP'
    killed = [k for k in b1_feasible if not feasible_full(k)]
    surviving = [k for k in b1_feasible if feasible_full(k)]
    log(f'batch-1-feasible keys {len(b1_feasible)} (all re-found feasible); killed by HUB + DARK: {len(killed)}; surviving {len(surviving)}; {time.time()-t0:.0f}s')
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
    # 4. certificates: every killed key + every referenced key, per case
    todo = sorted(set(killed) | set(needed))
    certs = []; failed = []; kinds = {}; max_rhs = -10 ** 9; n_mult = 0; n_coef = 0; per_key_cases = {}
    for i, key in enumerate(todo):
        kind, kc, problem = certify_key(key)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind in ('feasible', 'fail'):
            failed.append([list(key), kind, str(problem)]); log('  NOT CERTIFIED', key, kind, problem)
        else:
            per_key_cases[key] = len(kc)
        for hub, dark, ints in kc:
            types, aux, A, B, names, n_pkg, n_b1 = ext_system(key, hub, dark)
            assert exact_ok(ints, A, B)
            if kind == 'package': assert not any(ints[n_pkg:])
            if kind == 'batch1': assert any(ints[n_pkg:])
            rhs = sum(w * b for w, b in zip(ints, B)); max_rhs = max(max_rhs, rhs)
            n_mult += len(ints); n_coef += len(A[0])
            certs.append({'key': list(key), 'kind': kind, 'hub': list(hub) if hub else None, 'dark': dark, 'weights': ints})
        if (i + 1) % 100 == 0: log(f'  {i+1}/{len(todo)} keys, {len(certs)} certificates, kinds {kinds}, {time.time()-t0:.0f}s')
    n_case_certs = sum(1 for c in certs if c['kind'] == 'case')
    log(f'keys to certify {len(todo)} (killed {len(killed)}, referenced {len(needed)}, both {len(set(killed) & set(needed))}); '
        f'kinds {kinds}; certificates {len(certs)} ({n_case_certs} per-case); not certified {len(failed)}; largest weighted rhs {max_rhs}; '
        f'multipliers {n_mult}; coefficients checked {n_coef}; {time.time()-t0:.0f}s')
    killed_kinds = {}
    for key in killed:
        kd = next((c['kind'] for c in certs if tuple(c['key']) == key), None)
        killed_kinds[kd] = killed_kinds.get(kd, 0) + 1
    log('killed keys by certificate kind:', killed_kinds)
    out = {
        'gates': G, 'kappa': KAPPA,
        'system': 'package rows (L1)-(L23) as certify75.system, unchanged; then qcert batch-1 rows: y split (=), N1, L7*, L12*, L13*, '
                  'L14*, L15*, L17-M* | L17-Mt*, L18*, L19*, L20*, [q=0: L22*], I, [q=0: Q0]; then the case rows: '
                  'hub ("eq", a): A = a (two inequalities) with the columns (r <= 2, u > 4 + q - a) removed; hub ("le", 4): A <= 4; '
                  'dark d: L13d, L14d, L15d, L17Md | L17Td, L18d, bright lower, bright capacity, dark capacity, F budget, y2d <= y2, '
                  'y2m <= C(q,2), (I\'), [d = q: Fb = 0], [d = 0: Fd + y2d = 0]; columns = helper types + [y0, y1, y2] (+ [y2d, Fb, Fd] in a dark case)',
        'cases': 'hub cases: none if q <= 4, else A = 5..q and A <= 4; dark cases: q_D = 0..q.  A key is excluded iff every leaf '
                 '(hub, dark) has a certificate; a certificate with dark = null covers all dark cases of its hub case; one with '
                 'hub = null and dark = null covers every case.',
        'batch1_feasible_keys': [list(k) for k in b1_feasible],
        'killed_keys': [list(k) for k in killed],
        'surviving_keys': [list(k) for k in surviving],
        'claims': [{'state': list(st), 'orientation': ori, 'lower_even': claims_full[(st, ori)][0], 'lower_odd': claims_full[(st, ori)][1],
                    'batch1_lower_even': claims_b1[(st, ori)][0], 'batch1_lower_odd': claims_b1[(st, ori)][1]} for st, ori in excluded],
        'certificates': certs,
        'uncertified': failed,
        'counts': {'scalar_states': len(states), 'oriented_claims': len(claims_b1), 'batch1_survivors': len(sb), 'full_survivors': len(sf),
                   'newly_excluded_claims': len(excluded), 'batch1_feasible_keys': len(b1_feasible), 'killed_keys': len(killed),
                   'surviving_keys': len(surviving), 'referenced_keys': len(needed), 'keys_certified': len(per_key_cases),
                   'key_kinds': kinds, 'killed_key_kinds': killed_kinds, 'certificates': len(certs), 'case_certificates': n_case_certs,
                   'failed': len(failed), 'largest_rhs': max_rhs, 'multipliers': n_mult, 'coefficients_checked': n_coef},
    }
    json.dump(out, open(HERE / 'CERTIFICATES_CASES75.json', 'w'))
    json.dump({'G': G, 'states': [list(s) for s in states],
               'claims': [{'state': list(st), 'orientation': o, 'batch1': list(claims_b1[(st, o)]), 'full': list(claims_full[(st, o)])} for st, o in sorted(claims_b1)],
               'batch1_survivors': [[list(st), o] for st, o in sorted(sb)], 'full_survivors': [[list(st), o] for st, o in sorted(sf)]},
              open(HERE / 'scan_cases75.json', 'w'))
    log('written CERTIFICATES_CASES75.json, scan_cases75.json; total', f'{time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
