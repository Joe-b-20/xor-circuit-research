#!/usr/bin/env python3
"""qcert generator (G = 75): extended local systems, LP scan, exact integer Farkas certificates.

Extended local system of a key (h, y, F, ori, q, z):
  columns  = the package's helper types (r,u,v), r+u+v >= 3  (exactly certify75.system's list)  +  [y0, y1, y2]
  rows     = the package's rows (L1)-(L23), UNCHANGED, in certify75.system's order (imported from the package copy),
             followed by the new rows in the fixed order below (see PROOF_ADDENDUM.md, section A.6):
       y split <=, y split >=            y0 + y1 + y2 = y
       N1                                3 n_3 <= G - 32 - h - q                 (the only G-dependent row)
       L7*                               W + y1 <= 7q
       L12*                              sum (r-1)_+ n + y0 <= rho_6
       L13*, L14*, L15*                  package rows with y -> y2 and (L13, L14) W -> W + y1
       L17-M*  |  L17-Mt*, L18*, L19*, L20*, [q=0: L22*]      package rows with y -> y2
       I                                 sum (u + 2 f_min) n + y1 + y2 <= 4q + 2F
       [q=0: Q0]                         sum_{r=0} n <= z - (32 - rho_6)
A certificate is a nonnegative integer vector lambda over the rows with lambda^T A >= 0 in every column
(helper-type columns AND the three y-columns) and lambda^T b < 0.  Multipliers are found by an LP
(SciPy/HiGHS), rationalized with fractions, scaled to integers, gcd-reduced, and verified here in exact
integer arithmetic; the LP's status is never trusted.  A second, independent checker is check_ext75.py.

usage: nice -n 8 python3 gen_certs.py          (writes CERTIFICATES_EXT75.json, scan_ext75.json, gen_certs.log)
"""
import sys, json, time
from fractions import Fraction
from math import comb, lcm, gcd
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
PKG = SPRINT / 'lb76/pkg_copy/source/lower_bounds/checks'
HERE = SPRINT / 'qcert'
sys.path.insert(0, str(PKG))
import certify75   # noqa: E402  (package copy, unchanged; only system() and direct_exclusion() are used)
import lp_regen    # noqa: E402  (package copy, unchanged; only scalar_states()/run()/first_s() driver is used)

G = 75
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
LOG = [None]     # opened on first use inside main() only, so that importing this module (crosscheck.py) has no side effect
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True)
    if LOG[0] is None: LOG[0] = open(HERE / 'gen_certs.log', 'a')
    LOG[0].write(s + '\n'); LOG[0].flush()


def ext_system(key, with_new=True):
    """(types, A, B, names): rows as <= constraints; columns = types + [y0, y1, y2]."""
    h, y, F, ori, q, z = key
    types, A, B, names = certify75.system(key)
    A = [list(row) + [0, 0, 0] for row in A]; B = list(B); names = list(names)
    if not with_new:
        return types, A, B, names
    def fmin(r, u, v): return max(0, (r + u + v - 3) // 2)
    def d0(r, u): return (u - 1) if r == 0 else 0
    def ovf(r, u): return max(0, u - 2) if r == 3 else 0
    def add(name, fn, b, y0=0, y1=0, y2=0):
        A.append([fn(r, u, v) for r, u, v in types] + [y0, y1, y2]); B.append(b); names.append(name)
    rho6, rho, eps = RHO6[ori], RHO[ori], EPS[ori]
    add('y split <=', lambda r, u, v: 0, y, 1, 1, 1)
    add('y split >=', lambda r, u, v: 0, -y, -1, -1, -1)
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
    return types, A, B, names


def exact_ok(ints, A, B):
    """pure integer check: lambda >= 0 integers, lambda^T A >= 0 per column, lambda^T b < 0."""
    if len(ints) != len(A) or any((type(w) is not int) or w < 0 for w in ints): return False
    ncol = len(A[0])
    for j in range(ncol):
        if sum(w * row[j] for w, row in zip(ints, A)) < 0: return False
    return sum(w * b for w, b in zip(ints, B)) < 0


def farkas(A, B):
    """LP for multipliers: min sum(lambda), -A^T lambda <= 0, b^T lambda = -1, lambda >= 0. Returns float vector or None."""
    AA = np.array(A, float); m = len(A)
    for method in ('highs', 'highs-ds', 'highs-ipm'):
        res = linprog(np.ones(m), A_ub=-AA.T, b_ub=np.zeros(AA.shape[1]), A_eq=np.array([B], float), b_eq=[-1.0],
                      bounds=(0, None), method=method)
        if res.status == 0: return res.x
        if res.status == 2: return None
    return None


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


def certificate(key, with_new):
    types, A, B, names = ext_system(key, with_new)
    lam = farkas(A, B)
    if lam is None: return None, len(A)
    ints = rationalize(lam, A, B)
    if ints is None:
        # second attempt with the zero objective (different vertex)
        AA = np.array(A, float); m = len(A)
        res = linprog(np.zeros(m), A_ub=-AA.T, b_ub=np.zeros(AA.shape[1]), A_eq=np.array([B], float), b_eq=[-1.0], bounds=(0, None), method='highs')
        if res.status == 0: ints = rationalize(res.x, A, B)
    return ints, len(A)


# ---------------------------------------------------------------- feasibility (primal LP) and the package driver
CACHE = {}
def feas(key, with_new):
    k = (key, with_new)
    if k in CACHE: return CACHE[k]
    h, y, F, ori, q, z = key
    if certify75.direct_exclusion(key) or 2 * h + y + z + comb(q, 2) < 32:
        CACHE[k] = False; return False
    types, A, B, names = ext_system(key, with_new)
    if not types:
        CACHE[k] = False; return False
    res = linprog(np.zeros(len(A[0])), A_ub=np.array(A, float), b_ub=np.array(B, float), bounds=(0, None), method='highs')
    if res.status == 2: out = False
    elif res.status == 0: out = True
    else:
        log('LP status', res.status, key, with_new); out = True
    CACHE[k] = out; return out

MODE = [True]
from functools import lru_cache
@lru_cache(None)
def feasible_for_driver(h, y, F, q, z, ori):
    return feas((h, y, F, ori, q, z), MODE[0])
lp_regen.feasible = feasible_for_driver


def main():
    t0 = time.time()
    # 1. the two scans with the package's own driver (lp_regen.run), feasibility = our LP on the two systems
    MODE[0] = False
    states, claims_base, surv_base = lp_regen.run(G)
    MODE[0] = True; feasible_for_driver.cache_clear()
    states2, claims_ext, surv_ext = lp_regen.run(G)
    assert states == states2
    sb = {(st, o) for st, o, k, l in surv_base}; se = {(st, o) for st, o, k, l in surv_ext}
    assert se <= sb, 'extended survivors not a subset of base survivors'
    excluded = sorted(sb - se)
    log(f'scalar states {len(states)}, oriented claims {len(claims_base)}; base survivors {len(sb)}; extended survivors {len(se)}; '
        f'newly excluded claims {len(excluded)}; {time.time()-t0:.0f}s')
    # bounds must never go down
    for c in claims_base:
        kb, lb, db = claims_base[c]; ke, le, de = claims_ext[c]
        assert ke >= kb and (ke > kb or le >= lb), (c, claims_base[c], claims_ext[c])
    # 2. the baseline-feasible keys and those the extended system kills
    gk = json.load(open(SPRINT / 'lb76/g75_keys.json'))
    base_feasible = sorted((k[0], k[1], k[2], k[5], k[3], k[4]) for k in gk['feasible'])   # file order is (h,y,F,q,z,ori)
    mine_base = [k for k in base_feasible if feas(k, False)]
    assert len(mine_base) == len(base_feasible), (len(mine_base), len(base_feasible))
    killed = [k for k in base_feasible if not feas(k, True)]
    log(f'baseline-feasible keys {len(base_feasible)} (all re-found feasible with package rows); killed by the extended system: {len(killed)}')
    # 3. keys referenced by the coverage of the newly excluded claims (exactly certify75.verify's enumeration)
    needed = {}
    for st, ori in excluded:
        a, b, Y, V, he, ho, le_, lo_, Se, So, budget = st
        k, l, dead = claims_ext[(st, ori)]
        assert dead and (k > Se or l > So or k + l > budget)
        other = 'Mt' if ori == 'M' else 'M'
        for h, y, F, o, least, greatest, claimed in ((he, Y, V, ori, le_, Se, k), (ho, V, Y, other, lo_, So, l)):
            for s in range(least, min(claimed - 1, greatest) + 1):
                for q in range(s + 1):
                    z = s - q
                    if 2 * h + y + z + comb(q, 2) < 32: continue
                    key = (h, y, F, o, q, z)
                    if certify75.direct_exclusion(key): continue
                    assert not feas(key, True), ('referenced key feasible?!', key)
                    needed[key] = 'package' if not feas(key, False) else 'new'
    n_new_needed = sum(1 for v in needed.values() if v == 'new'); n_pkg_needed = len(needed) - n_new_needed
    extra_new = sorted(set(k for k, v in needed.items() if v == 'new') - set(killed))
    log(f'coverage of the {len(excluded)} claims references {len(needed)} distinct keys: {n_new_needed} need the new rows '
        f'({len(extra_new)} of them outside the 1,134 baseline-visited set), {n_pkg_needed} are infeasible with the package rows alone')
    # 4. certificates: every killed key (new rows) + every referenced key
    todo = {k: 'new' for k in killed}
    for k, v in needed.items(): todo.setdefault(k, v)
    certs = []; failed = []; max_rhs = -10 ** 9; rows_total = 0; coeffs = 0
    for i, key in enumerate(sorted(todo)):
        kind = todo[key]
        ints, m = certificate(key, with_new=(kind == 'new'))
        if ints is None:
            failed.append((key, kind)); log('  NO CERTIFICATE', key, kind); continue
        if kind == 'package':
            # pad to the full extended row count with zeros so every certificate has the extended system's length
            _, A_full, B_full, _ = ext_system(key, True)
            ints = ints + [0] * (len(A_full) - len(ints))
            assert exact_ok(ints, A_full, B_full)
        else:
            _, A_full, B_full, _ = ext_system(key, True)
            assert exact_ok(ints, A_full, B_full)
            # sanity: a 'new' certificate must use at least one new row (the package rows alone leave the key feasible)
            n_pkg_rows = len(certify75.system(key)[1])
            assert any(ints[n_pkg_rows:]), ('new certificate without new rows', key)
        rhs = sum(w * b for w, b in zip(ints, B_full)); max_rhs = max(max_rhs, rhs)
        rows_total += len(ints); coeffs += len(A_full[0])
        certs.append({'key': list(key), 'kind': kind, 'weights': ints})
        if (i + 1) % 500 == 0: log(f'  {i+1}/{len(todo)} certificates, {time.time()-t0:.0f}s')
    log(f'certificates: {len(certs)} ({sum(1 for c in certs if c["kind"]=="new")} new-row, {sum(1 for c in certs if c["kind"]=="package")} package-row); '
        f'failed {len(failed)}; largest weighted rhs {max_rhs}; multipliers {rows_total}; coefficients checked {coeffs}; {time.time()-t0:.0f}s')
    out = {
        'gates': G,
        'system': 'package rows (L1)-(L23) as certify75.system, unchanged, followed by: y split (=), N1, L7*, L12*, L13*, L14*, L15*, '
                  'L17-M* | L17-Mt*, L18*, L19*, L20*, [q=0: L22*], I, [q=0: Q0]; columns = helper types + [y0, y1, y2]',
        'claims': [{'state': list(st), 'orientation': ori, 'lower_even': claims_ext[(st, ori)][0], 'lower_odd': claims_ext[(st, ori)][1],
                    'package_lower_even': claims_base[(st, ori)][0], 'package_lower_odd': claims_base[(st, ori)][1]} for st, ori in excluded],
        'killed_keys': [list(k) for k in killed],
        'certificates': certs,
        'uncertified': [[list(k), v] for k, v in failed],
        'counts': {'scalar_states': len(states), 'oriented_claims': len(claims_base), 'base_survivors': len(sb), 'extended_survivors': len(se),
                   'newly_excluded_claims': len(excluded), 'baseline_feasible_keys': len(base_feasible), 'killed_keys': len(killed),
                   'referenced_keys': len(needed), 'referenced_new': n_new_needed, 'referenced_package': n_pkg_needed,
                   'certificates': len(certs), 'certificates_new': sum(1 for c in certs if c['kind'] == 'new'),
                   'certificates_package': sum(1 for c in certs if c['kind'] == 'package'), 'failed': len(failed), 'largest_rhs': max_rhs},
    }
    json.dump(out, open(HERE / 'CERTIFICATES_EXT75.json', 'w'), indent=1)
    json.dump({'G': G, 'states': [list(s) for s in states],
               'claims': [{'state': list(st), 'orientation': o, 'base': list(claims_base[(st, o)]), 'ext': list(claims_ext[(st, o)])} for st, o in sorted(claims_base)],
               'base_survivors': [[list(st), o] for st, o in sorted(sb)], 'ext_survivors': [[list(st), o] for st, o in sorted(se)]},
              open(HERE / 'scan_ext75.json', 'w'))
    log('written CERTIFICATES_EXT75.json, scan_ext75.json; total', f'{time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
