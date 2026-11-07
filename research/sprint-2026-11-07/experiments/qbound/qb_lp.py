#!/usr/bin/env python3
"""Step 2: the package LP (rows L1-L23 as in lp_regen.py) with optional NEW rows, and vertex solutions.

Columns: helper types (r,u,v) with r+u+v>=3, plus auxiliary variables when a variant needs them:
  y0 = even+even gates whose three even signals are all represented      (all three pairs: a weight-6 boundary relation)
  y1 = even+even gates with exactly one missing signal, that signal bright (a 2/4-form of a bright missing label)
  y2 = the other even+even gates                                          (y0 + y1 + y2 = y)
Variants (each is a set of extra/replaced rows; 'base' must reproduce lp_regen exactly):
  base      : rows exactly as lp_regen.rows_for
  Gstar     : (G*) sharpening: y -> y2 in L13..L18 (quotient rows) and L19, L20 (Mt dark rows);
              y1 + y2 <= 4q + 2F - sum(u+2f_min) n (every non-short ee gate is an incidence of a missing label);
              W + y1 <= 7q (forms of a bright label are independent: L7*), and L13*, L14* get +y1 on the left;
              L12*: sum (r-1)_+ n + y0 <= rho6;
              q = 0 => (G*) with J = R6: z >= 12 + n_{r=0} (M), z >= 4 + n_{r=0} (Mt, weaker than Lemma 10.3(ii))
  Gstar_q   : Gstar plus the hypothetical row q >= C (C from the command line) -- for the table only
usage: python3 qb_lp.py scan VARIANT [G]        -> survivors / feasible keys of the G=75 scan under the variant
       python3 qb_lp.py vertex h y F q z ori [VARIANT]  -> print a few vertex solutions of the local system
"""
import json, sys, time
from math import comb
from functools import lru_cache
import numpy as np
from scipy.optimize import linprog
from pathlib import Path
PKG = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'
sys.path.insert(0, str(PKG))
import lp_regen  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qbound'

RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}
AUX = ['y0', 'y1', 'y2']

def f_min(r, u, v): return max(0, (r + u + v - 3) // 2)
def deficit(r, u): return u - 1 if r == 0 else 0
def overflow(r, u): return max(0, u - 2) if r == 3 else 0

def build(h, y, F, q, z, ori, variant='base', extra_q=0):
    """Return (cols, A_eq, b_eq, A_ub, b_ub, names). cols = types + AUX (AUX only if variant != base)."""
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    use_aux = 'Gstar' in variant
    xy = GCUR[0] - 32 - h            # x + y of the phase = number of even signals; x + y - q = represented labels
    ncol = len(types) + (len(AUX) if use_aux else 0)
    def row(fn, aux=None):
        r_ = [fn(*t) for t in types] + ([0.0] * len(AUX) if use_aux else [])
        if aux:
            for k, c in aux.items(): r_[len(types) + AUX.index(k)] = c
        return r_
    rho = RHO6[ori]; res = RESERVE[ori]
    eq, le = [], []
    def EQ(name, fn, b, aux=None): eq.append((name, row(fn, aux), b))
    def LE(name, fn, b, aux=None): le.append((name, row(fn, aux), b))
    # yy = coefficient dict for "y" in the quotient rows: constant y (base) or the variable y2 (Gstar)
    Yv = (lambda c: {'y2': -c}) if use_aux else (lambda c: None)
    Yc = (lambda c: 0) if use_aux else (lambda c: c * y)
    EQ('L1 helper count', lambda r, u, v: 1, h)
    EQ('L2 helper degree', lambda r, u, v: r + u + v, 32 + h - y + q + z)
    EQ('L3 HH incidence', lambda r, u, v: v, 2 * z)
    LE('L4 reverse EE budget', f_min, F)
    LE('L5 missing pairs', lambda r, u, v: comb(u, 2), comb(q, 2))
    LE('L6 full missing incidence', lambda r, u, v: u if r == 3 else 0, q)
    if use_aux: LE('L7* label rank capacity (+y1)', lambda r, u, v: r * u, 7 * q, {'y1': 1})
    else: LE('L7 label rank capacity', lambda r, u, v: r * u, 7 * q)
    LE('L8 full helper budget', lambda r, u, v: 1 + 2 * f_min(r, u, v) if r == 3 else 0, 3 * h + 2 * F + y - 32)
    LE('L9 weighted label capacity', lambda r, u, v: max(0, r - 1) * u, 3 * q)
    LE('L10 even signal fanout', lambda r, u, v: u + 2 * f_min(r, u, v), 4 * q + 2 * F)
    LE('L11 full helper incidence', lambda r, u, v: u + v if r == 3 else 0, q + z)
    if use_aux: LE('L12* boundary R6 rank (+y0)', lambda r, u, v: max(0, r - 1), rho, {'y0': 1})
    else: LE('L12 boundary R6 rank', lambda r, u, v: max(0, r - 1), rho)
    # quotient rows: y enters only through (G); in Gstar it becomes y2 (and L13/L14 get +y1 from the bright forms)
    a13 = {'y2': -2, 'y1': 1} if use_aux else None
    LE('L13 quotient rank capacity', lambda r, u, v: r * u - 2 * deficit(r, u), Yc(2) + 2 * z + 7 * q - 2 * res, a13)
    LE('L14 quotient full capacity', lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * deficit(r, u),
       Yc(2) + 2 * z + 7 * q - 2 * res + (2 if ori == 'M' else 0), a13)
    LE('L15 quotient excess capacity', lambda r, u, v: max(0, r - 1) * u - deficit(r, u), Yc(1) + z + 3 * q - res, Yv(1))
    LE('L16 full excess overflow', lambda r, u, v: max(0, r - 1) * u + overflow(r, u), 3 * q)
    if ori == 'M':
        LE('L17-M quotient joint deficit', lambda r, u, v: 2 * max(0, r - 1) * u + 2 * overflow(r, u) - 3 * deficit(r, u), Yc(3) + 3 * z + 6 * q - 24, Yv(3))
    else:
        LE('L17-Mt quotient joint deficit', lambda r, u, v: max(0, r - 1) * u + overflow(r, u) - 3 * deficit(r, u), Yc(3) + 3 * z + 3 * q - 12, Yv(3))
        LE('L18 quotient full strengthened', lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * deficit(r, u), Yc(3) + 3 * z + 7 * q - 12, Yv(3))
        LE('L19 dark repeated pairs', lambda r, u, v: -(u + v - 1) if r == 0 else (-v if r == 1 else 0), Yc(1) - 3, Yv(1))
        LE('L20 dark quotient rank', lambda r, u, v: -(3 * u + v - 3) if r == 0 else 0, Yc(3) + 2 * z - 9, Yv(3))
        if q == 0:
            LE('L21 unanchored required', lambda r, u, v: -int(r == 0), -1)
            LE('L22 short boundary rank', lambda r, u, v: -(v - 1) if r == 0 else 0, Yc(1) - 3, Yv(1))
    if q == 6: LE('L23 six packing', lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0), 4)
    if q == 7: LE('L23 seven packing', lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0), 14)
    if use_aux:
        EQ('y0+y1+y2 = y', lambda r, u, v: 0, y, {'y0': 1, 'y1': 1, 'y2': 1})
        # every non-short ee gate contains a missing label; incidences of missing labels: U + 2F_H + (ee incidences) <= 4q + 2F
        LE('ee missing incidence', lambda r, u, v: u + 2 * f_min(r, u, v), 4 * q + 2 * F, {'y1': 1, 'y2': 1})
        if q == 0:
            # (G*) with J = R6 and no bright labels: 32 - rho6 <= y2 + z + D0 = z - n_{r=0}  (y2 = 0 when q = 0)
            LE('G* q=0: z >= 32 - rho6 + n_r0', lambda r, u, v: int(r == 0), z - (32 - rho))
    if 'N1' in variant:
        # (N1) the represented edges of full helpers carry pairwise distinct labels (Lemma 4.1 at one helper;
        # Lemma 4.5 across two full helpers, since a shared label makes their XOR a boundary pair): 3 n3 <= x+y-q
        LE('N1 full-helper labels distinct: 3 n3 <= x+y-q', lambda r, u, v: 3 if r == 3 else 0, xy - q)
    if 'N7' in variant:
        # (N7) every represented edge at a helper with r >= 2 carries a RICH label (sigma >= 2), rich labels are
        # distinct across full helpers, and the excess at a rich label is <= sigma(P) <= 5: a crude aggregate
        # 6 n3 + 2 n2 <= top(x+y-q) with top(m) = sum of the m largest sigma (pair_sigma.json), here linearised
        top = TOP[ori]; m = max(0, min(xy - q, 64))
        LE('N7 rich-label excess: 6 n3 + 2 n2 <= top(x+y-q)', lambda r, u, v: r * max(0, r - 1), top[m])
    if extra_q: LE('hyp q >= C', lambda r, u, v: 0, q - extra_q)   # infeasible row when q < C
    names = [n for n, _, _ in eq] + [n for n, _, _ in le]
    A_eq = np.array([r_ for _, r_, _ in eq], float); b_eq = np.array([b for _, _, b in eq], float)
    A_ub = np.array([r_ for _, r_, _ in le], float); b_ub = np.array([b for _, _, b in le], float)
    cols = types + (AUX if use_aux else [])
    return cols, A_eq, b_eq, A_ub, b_ub, names

VARIANT = ['base']; EXTRA_Q = [0]; GCUR = [75]
try:
    TOP = {k: v['top'] for k, v in json.load(open(OUT/'pair_sigma.json')).items()}
except FileNotFoundError:
    TOP = {}
UNKNOWN = []
@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    if lp_regen.direct(ori, q, z): return False
    if 2 * h + y + z + comb(q, 2) < 32: return False
    cols, A_eq, b_eq, A_ub, b_ub, names = build(h, y, F, q, z, ori, VARIANT[0], EXTRA_Q[0])
    if not cols: return False
    r = linprog(np.zeros(len(cols)), A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    if r.status == 2: return False
    if r.status != 0: UNKNOWN.append((h, y, F, q, z, ori, r.status)); return True
    if 'INT' in VARIANT[0]:
        # integer feasibility (helper-type counts and y0,y1,y2 are integers) by HiGHS branch-and-bound
        from scipy.optimize import milp, LinearConstraint, Bounds
        A = np.vstack([A_eq, A_ub]); lb = np.concatenate([b_eq, -np.inf * np.ones(len(b_ub))]); ub = np.concatenate([b_eq, b_ub])
        rm = milp(np.zeros(len(cols)), constraints=LinearConstraint(A, lb, ub), integrality=np.ones(len(cols)), bounds=Bounds(0, np.inf))
        if rm.status == 2: return False
        if rm.status != 0: UNKNOWN.append((h, y, F, q, z, ori, 'milp', rm.status)); return True
    return True
lp_regen.feasible = feasible

def scan(variant, G=75, extra_q=0):
    VARIANT[0] = variant; EXTRA_Q[0] = extra_q; GCUR[0] = G; feasible.cache_clear()
    t0 = time.time()
    states, claims, survivors = lp_regen.run(G)
    keys = json.load(open(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/g75_keys.json'))
    base_feas = [tuple(k) for k in keys['feasible']]
    still = [k for k in base_feas if feasible(*k)]
    from collections import Counter
    surv = [dict(state=list(st), ori=ori, k=k, ell=ell, shortfall=st[10] - (k + ell)) for st, ori, k, ell in survivors]
    print(f'variant {variant} q>={extra_q}: survivors {len(surv)} (M {sum(1 for s in surv if s["ori"]=="M")}, Mt {sum(1 for s in surv if s["ori"]=="Mt")}); '
          f'of the 1134 baseline-feasible keys still feasible: {len(still)} (by q: {sorted(Counter(k[3] for k in still).items())}); '
          f'unknown {len(UNKNOWN)}; {time.time()-t0:.0f}s', flush=True)
    json.dump(dict(variant=variant, extra_q=extra_q, survivors=surv, keys_still_feasible=[list(k) for k in still]),
              open(OUT/f'scan_{variant}_q{extra_q}_g{G}.json', 'w'), indent=1)
    return surv, still

def vertices(h, y, F, q, z, ori, variant='base', n=6):
    cols, A_eq, b_eq, A_ub, b_ub, names = build(h, y, F, q, z, ori, variant)
    print(f'key (h,y,F,q,z,ori)=({h},{y},{F},{q},{z},{ori}) variant {variant}: {len(cols)} columns, {len(names)} rows')
    rng = np.random.default_rng(1)
    seen = set()
    objs = [np.zeros(len(cols))]
    # a few structured objectives: minimise / maximise full helpers, unanchored helpers, total degree excess
    def obj(fn): return np.array([fn(*c) if isinstance(c, tuple) else 0.0 for c in cols])
    objs += [obj(lambda r, u, v: -(r == 3)), obj(lambda r, u, v: (r == 3)), obj(lambda r, u, v: -(r == 0)),
             obj(lambda r, u, v: -(r + u + v - 3)), obj(lambda r, u, v: (r + u + v - 3)), obj(lambda r, u, v: -u), obj(lambda r, u, v: -v)]
    for _ in range(n): objs.append(rng.normal(size=len(cols)))
    for c in objs:
        r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
        if r.status != 0: print('  status', r.status, r.message); continue
        sol = tuple(round(float(v), 3) for v in r.x)
        if sol in seen: continue
        seen.add(sol)
        parts = [f'{c}:{v:g}' for c, v in zip(cols, sol) if abs(v) > 1e-6]
        tight = [names[i] for i, s in enumerate(list(A_eq @ r.x - b_eq) + list(b_ub - A_ub @ r.x)) if abs(s) < 1e-7 and i >= len(b_eq)]
        print('  ', ' '.join(parts))
        print('      tight:', '; '.join(tight))

if __name__ == '__main__':
    if sys.argv[1] == 'scan':
        variant = sys.argv[2]; G = int(sys.argv[3]) if len(sys.argv) > 3 else 75
        eq = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        scan(variant, G, eq)
    elif sys.argv[1] == 'milp':
        # integer feasibility (all columns integral) of the keys an LP scan left feasible; branch-and-bound by HiGHS
        from scipy.optimize import milp, LinearConstraint, Bounds
        variant = sys.argv[2]; GCUR[0] = int(sys.argv[3]) if len(sys.argv) > 3 else 75
        keys = json.load(open(OUT/f'scan_{variant}_q0_g{GCUR[0]}.json'))['keys_still_feasible']
        from collections import Counter
        left = []
        for h, y, F, q, z, ori in keys:
            cols, A_eq, b_eq, A_ub, b_ub, names = build(h, y, F, q, z, ori, variant)
            A = np.vstack([A_eq, A_ub]); lb = np.concatenate([b_eq, -np.inf * np.ones(len(b_ub))]); ub = np.concatenate([b_eq, b_ub])
            r = milp(np.zeros(len(cols)), constraints=LinearConstraint(A, lb, ub), integrality=np.ones(len(cols)), bounds=Bounds(0, np.inf))
            if r.status == 0: left.append((h, y, F, q, z, ori))
            elif r.status != 2: print('  milp status', r.status, r.message, (h, y, F, q, z, ori))
        print(f'variant {variant}: {len(keys)} LP-feasible keys, {len(left)} integer-feasible; by q: {sorted(Counter(k[3] for k in left).items())}; by ori: {Counter(k[5] for k in left)}')
        json.dump([list(k) for k in left], open(OUT/f'milp_{variant}_g{GCUR[0]}.json', 'w'))
    elif sys.argv[1] == 'vertex':
        toks = sys.argv[2:]
        ints = [int(t) for t in toks if t.lstrip('-').isdigit()]
        words = [t for t in toks if not t.lstrip('-').isdigit()]
        h, y, F, q, z = ints[:5]; ori = words[0]
        variant = words[1] if len(words) > 1 else 'base'
        vertices(h, y, F, q, z, ori, variant)
