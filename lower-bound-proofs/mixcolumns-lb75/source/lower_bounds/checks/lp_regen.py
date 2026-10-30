#!/usr/bin/env python3
"""Independent regeneration of the G=74 steady-orbit exclusion (and a G=75 survivor count) with my own LP model.

Rows are written from the proof documents (same functions as stress.check_rows), not copied from certify75.py.
For every oriented claim of CERTIFICATES75.json the lower bounds k, ell are recomputed from scratch with scipy's
HiGHS LP (numerical, used here only as a cross-check of the exact certificates), and the final test is re-evaluated.
"""
import json, sys, time
from math import comb
from functools import lru_cache
import numpy as np
from scipy.optimize import linprog

RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}

def rows_for(h, y, F, q, z, ori):
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    def f(r, u, v): return max(0, (r + u + v - 3) // 2)
    def deficit(r, u): return u - 1 if r == 0 else 0
    def overflow(r, u): return max(0, u - 2) if r == 3 else 0
    rho = RHO6[ori]; res = RESERVE[ori]
    eq = [(lambda r, u, v: 1, h), (lambda r, u, v: r + u + v, 32 + h - y + q + z), (lambda r, u, v: v, 2 * z)]
    le = [
        (f, F),
        (lambda r, u, v: comb(u, 2), comb(q, 2)),
        (lambda r, u, v: u if r == 3 else 0, q),
        (lambda r, u, v: r * u, 7 * q),
        (lambda r, u, v: 1 + 2 * f(r, u, v) if r == 3 else 0, 3 * h + 2 * F + y - 32),
        (lambda r, u, v: max(0, r - 1) * u, 3 * q),
        (lambda r, u, v: u + 2 * f(r, u, v), 4 * q + 2 * F),
        (lambda r, u, v: u + v if r == 3 else 0, q + z),
        (lambda r, u, v: max(0, r - 1), rho),
        (lambda r, u, v: r * u - 2 * deficit(r, u), 2 * y + 2 * z + 7 * q - 2 * res),
        (lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * deficit(r, u), 2 * y + 2 * z + 7 * q - 2 * res + (2 if ori == 'M' else 0)),
        (lambda r, u, v: max(0, r - 1) * u - deficit(r, u), y + z + 3 * q - res),
        (lambda r, u, v: max(0, r - 1) * u + overflow(r, u), 3 * q),
    ]
    if ori == 'M':
        le.append((lambda r, u, v: 2 * max(0, r - 1) * u + 2 * overflow(r, u) - 3 * deficit(r, u), 3 * y + 3 * z + 6 * q - 24))
    else:
        le += [(lambda r, u, v: max(0, r - 1) * u + overflow(r, u) - 3 * deficit(r, u), 3 * y + 3 * z + 3 * q - 12),
               (lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * deficit(r, u), 3 * y + 3 * z + 7 * q - 12),
               (lambda r, u, v: -(u + v - 1) if r == 0 else (-v if r == 1 else 0), y - 3),
               (lambda r, u, v: -(3 * u + v - 3) if r == 0 else 0, 3 * y + 2 * z - 9)]
        if q == 0:
            le += [(lambda r, u, v: -int(r == 0), -1), (lambda r, u, v: -(v - 1) if r == 0 else 0, y - 3)]
    if q == 6: le.append((lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0), 4))
    if q == 7: le.append((lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0), 14))
    A_eq = np.array([[fn(*t) for t in types] for fn, _ in eq], float); b_eq = np.array([b for _, b in eq], float)
    A_ub = np.array([[fn(*t) for t in types] for fn, _ in le], float); b_ub = np.array([b for _, b in le], float)
    return types, A_eq, b_eq, A_ub, b_ub

def direct(ori, q, z): return (q == 0 and z == 0) or (ori == 'Mt' and q == 0 and z < 8)

UNKNOWN = []
@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    """True if the relaxed type system may have a nonnegative real solution (LP not proven infeasible)."""
    if direct(ori, q, z): return False
    if 2 * h + y + z + comb(q, 2) < 32: return False
    types, A_eq, b_eq, A_ub, b_ub = rows_for(h, y, F, q, z, ori)
    if not types: return False
    r = linprog(np.zeros(len(types)), A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    if r.status == 2: return False
    if r.status != 0: UNKNOWN.append((h, y, F, q, z, ori, r.status)); return True
    return True

def first_s(h, y, F, ori, least, greatest):
    for s in range(least, greatest + 1):
        for q in range(s + 1):
            if feasible(h, y, F, q, s - q, ori): return s
    return greatest + 1

def scalar_states(G):
    def low(h, y): return next(s for s in range(65) if 2 * h + y + max(s, comb(s, 2)) >= 32)
    for a in range(24, G - 44):
        for Y in range(G - 31 - a):
            he = G - 32 - a - Y
            for b in range(24, G - 31):
                for V in range(Y + 1):
                    ho = G - 32 - b - V
                    if ho < 0 or ho + Y < 13: continue
                    Se = min(3 * he + 2 * V + Y - 32, 2 * b - a + G - 96 + V)
                    So = min(3 * ho + 2 * Y + V - 32, 2 * a - b + G - 96 + Y)
                    if min(Se, So) < 0: continue
                    le, lo = low(he, Y), low(ho, V); budget = a + b + 2 * G - 192
                    if le <= Se and lo <= So and le + lo <= budget:
                        yield (a, b, Y, V, he, ho, le, lo, Se, So, budget)

def run(G):
    t0 = time.time(); states = list(scalar_states(G)); survivors = []; claims = {}
    for st in states:
        a, b, Y, V, he, ho, le, lo, Se, So, budget = st
        for ori, other in (('M', 'Mt'), ('Mt', 'M')):
            k = first_s(he, Y, V, ori, le, min(Se, budget - lo))
            ell = lo
            if k <= Se and k + ell <= budget:
                ell = first_s(ho, V, Y, other, lo, min(So, budget - k))
            dead = k > Se or ell > So or k + ell > budget
            claims[(st, ori)] = (k, ell, dead)
            if not dead: survivors.append((st, ori, k, ell))
    print(f'G={G}: scalar states {len(states)}, oriented claims {len(claims)}, survivors {len(survivors)}, LP keys {feasible.cache_info().currsize}, unknown {len(UNKNOWN)}, {time.time()-t0:.0f}s', flush=True)
    return states, claims, survivors

if __name__ == '__main__':
    states, claims, survivors = run(74)
    assert not survivors, survivors[:5]
    # compare with the bundle's claims file
    from pathlib import Path
    data = json.load(open(Path(__file__).with_name('CERTIFICATES75.json')))
    theirs = {(tuple(c['state']), c['orientation']): (c['lower_even'], c['lower_odd']) for c in data['claims']}
    assert set(theirs) == set(claims), 'claim domains differ'
    same = sum(1 for key in claims if claims[key][:2] == theirs[key]); mine_weaker = []; mine_stronger = 0
    for key, (k, ell, dead) in claims.items():
        tk, tl = theirs[key]
        if (k, ell) == (tk, tl): continue
        # my bounds must never be BELOW a certified bound for the same side (an exact certificate proves infeasibility)
        if k < tk or (k == tk and ell < tl): mine_weaker.append((key, (k, ell), (tk, tl)))
        else: mine_stronger += 1
    print('claims identical', same, 'mine stronger/different', mine_stronger, 'mine below certified (must be 0 unless the certified side was not reached):', len(mine_weaker))
    for w in mine_weaker[:10]: print('  ', w)
    certs = {tuple(e['key']) for e in data['certificates']}
    # every certified key must be LP-infeasible in my model too
    bad = [kk for kk in certs if feasible(kk[0], kk[1], kk[2], kk[4], kk[5], kk[3])]
    print('certified keys that my LP finds feasible (must be 0):', len(bad), bad[:5])
    json.dump({'G74_states': len(states), 'G74_claims': len(claims), 'G74_survivors': len(survivors), 'identical_claims': same,
               'mine_below_certified': len(mine_weaker), 'certified_but_feasible_in_mine': len(bad), 'unknown_lp': UNKNOWN},
              open(__file__.replace('.py', '_74.json'), 'w'), indent=1, default=str)
    if survivors or mine_weaker or bad or UNKNOWN or same != len(claims):
        print('LP CROSS-CHECK FAILED (see the counts above)', file=sys.stderr); sys.exit(1)
    print('LP CROSS-CHECK PASSED: 0 survivors at G=74, all claims identical, no certified key feasible')
    if len(sys.argv) > 1 and sys.argv[1] == '75':
        states, claims, survivors = run(75)
        json.dump({'G75_states': len(states), 'G75_claims': len(claims), 'G75_survivors': len(survivors),
                   'survivors': [(list(st), ori, k, ell) for st, ori, k, ell in survivors]},
                  open(__file__.replace('.py', '_75.json'), 'w'), indent=1)
