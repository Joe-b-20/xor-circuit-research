#!/usr/bin/env python3
"""qrealcheck: independent LP with the qreal case splits (HUB, DARK), written from the statements in
qreal/REPORT.md 1.2 and 4.1 and from PROOF.md Lemma 10.2 / (L13)-(L18), not from qr_lp.py.

Base rows (L1-L23 + qbound's N1, L7*, L12*, (I), (Q0), y->y2, W->W+y1) are taken from qcheck's lp_indep.py, which
qcheck verified to reproduce qbound's key sets exactly (1,134 / 755 / 1,051 / 681).  Added here:

  HUB   Lemma H1: u_i <= 4 + (q - A) for every helper with r_i <= 2, A = sum_{r=3} u n.
        split (as qreal): for q >= 5 the cases  A = q - d, d = 0..q-5  (types r<3 with u > 4 + d removed) and  A <= 4.
  HUBX  my refinement: the exact integer cases A = a, a = 0..q (types r<3 with u > 4 + q - a removed); at least as
        strong as HUB (an LP point of the case A <= 4 with fractional A is lost).  Not claimed by qreal; a cross-check.
  DARK  exact split on d = q_D = 0..q with (written from the derivation):
        dk := sum_bright k_l >= rho - y2 - z - D0 + d                               [(G*) with J of F9]
        W + y1 <= sum_bright (7 - 2 k_l)                                            [L7* per label + F9]
        W + A + y1 <= sum_bright (7 + ex_l - 2 k_l), sum ex <= eps                  [as (L14)]
        Z <= sum_bright (3 - k_l)                                                   [as (L15)]
        M:  2Z + 2E + 3 dk <= 6 (q - d);   Mt: Z + E + 3 dk <= 3 (q - d), W + A + 3 dk <= 7 (q - d)   [as (L17), (L18)]
        occurrence budgets: sum_{r>=1} u n >= q - d;  sum_{r>=1} u n + y1 <= 4 (q - d) + 2 Fb;  y2d <= 4 d + 2 Fd;
        Fb + Fd + F_H <= F;  y2d <= y2;  y2 - y2d <= C(q, 2);  y1 + y2d + 2 (y2 - y2d) + U + 2 F_H <= 4 q + 2 F;
        d = q -> Fb = 0;  d = 0 -> Fd = y2d = 0.
usage: python3 lp_qrc.py keys VARIANT | scan VARIANT      VARIANT in GstarN1, GstarN1HUB, GstarN1HUBX, GstarN1HUBDARK, GstarN1HUBXDARK
"""
import sys, json, time
from math import comb
from functools import lru_cache
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
import lp_regen
OUT = SPRINT/'qrealcheck'
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
G = 75; KAPPA = 4
VARIANT = ['GstarN1HUBDARK']
REF = {'GstarN1': SPRINT/'qreal/scan_GstarN1_q0_g75.json', 'GstarN1HUB': SPRINT/'qreal/scan_GstarN1HUB_q0_g75.json',
       'GstarN1HUBDARK': SPRINT/'qreal/scan_GstarN1HUBDARKM_q0_g75.json', 'GstarN1HUBDARKFM': SPRINT/'qreal/scan_GstarN1HUBDARKMFM_q0_g75.json'}

def system(h, y, F, q, z, ori, variant, hub=None, dark=None):
    """hub: None | ('eq', a) [A = a] | ('le', a) [A <= a]; with ('eq', a) types r<3, u > KAPPA + q - a are removed.
    dark: None | d (exactly d dark labels).  Returns (columns, EQ, LE) with rows as dicts column -> coefficient."""
    new = 'Gstar' in variant; n1 = 'N1' in variant; dk = dark is not None
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    if hub and hub[0] == 'eq':
        umax = KAPPA + q - hub[1]
        types = [t for t in types if not (t[0] < 3 and t[1] > umax)]
    aux = (['y0', 'y1', 'y2'] if new else []) + (['y2d', 'Fb', 'Fd'] if dk else [])
    cols = types + aux
    rho6 = RHO6[ori]; rho = RHO[ori]; eps = EPS[ori]
    fm = lambda r, u, v: max(0, (r + u + v - 3) // 2)
    pos = lambda t: max(0, t)
    def vec(fn, **ax):
        row = {t: float(fn(*t)) for t in types if fn(*t) != 0}
        for k, c in ax.items():
            if c: assert k in aux, k; row[k] = float(c)
        return row
    Y = (lambda c: 0) if new else (lambda c: c * y)      # constant y on the right in the base system
    Yv = (lambda c: -c) if new else (lambda c: 0)        # coefficient of the variable y2 moved to the left
    Y1 = (lambda c: c) if new else (lambda c: 0)
    EQ = []; LE = []
    EQ.append((vec(lambda r, u, v: 1), h))                                         # L1
    EQ.append((vec(lambda r, u, v: r + u + v), 32 + h - y + q + z))                # L2
    EQ.append((vec(lambda r, u, v: v), 2 * z))                                     # L3
    LE.append((vec(fm), F))                                                        # L4
    LE.append((vec(lambda r, u, v: comb(u, 2)), comb(q, 2)))                       # L5
    LE.append((vec(lambda r, u, v: u if r == 3 else 0), q))                        # L6
    LE.append((vec(lambda r, u, v: r * u, y1=Y1(1)), 7 * q))                       # L7 / L7*
    LE.append((vec(lambda r, u, v: (1 + 2 * fm(r, u, v)) if r == 3 else 0), 3 * h + 2 * F + y - 32))   # L8
    LE.append((vec(lambda r, u, v: pos(r - 1) * u), 3 * q))                        # L9
    LE.append((vec(lambda r, u, v: u + 2 * fm(r, u, v)), 4 * q + 2 * F))           # L10
    LE.append((vec(lambda r, u, v: (u + v) if r == 3 else 0), q + z))              # L11
    LE.append((vec(lambda r, u, v: pos(r - 1), y0=(1 if new else 0)), rho6))       # L12 / L12*
    dfc = lambda r, u: (u - 1) if r == 0 else 0
    ovf = lambda r, u: pos(u - 2) if r == 3 else 0
    LE.append((vec(lambda r, u, v: r * u - 2 * dfc(r, u), y1=Y1(1), y2=Yv(2)), Y(2) + 2 * z + 7 * q - 2 * rho))                     # L13
    LE.append((vec(lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * dfc(r, u), y1=Y1(1), y2=Yv(2)), Y(2) + 2 * z + 7 * q - 2 * rho + eps))  # L14
    LE.append((vec(lambda r, u, v: pos(r - 1) * u - dfc(r, u), y2=Yv(1)), Y(1) + z + 3 * q - rho))                                  # L15
    LE.append((vec(lambda r, u, v: pos(r - 1) * u + ovf(r, u)), 3 * q))                                                             # L16
    if ori == 'M':
        LE.append((vec(lambda r, u, v: 2 * pos(r - 1) * u + 2 * ovf(r, u) - 3 * dfc(r, u), y2=Yv(3)), Y(3) + 3 * z + 6 * q - 24))  # L17-M
    else:
        LE.append((vec(lambda r, u, v: pos(r - 1) * u + ovf(r, u) - 3 * dfc(r, u), y2=Yv(3)), Y(3) + 3 * z + 3 * q - 12))          # L17-Mt
        LE.append((vec(lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * dfc(r, u), y2=Yv(3)), Y(3) + 3 * z + 7 * q - 12))        # L18
        LE.append((vec(lambda r, u, v: -((u + v - 1) if r == 0 else (v if r == 1 else 0)), y2=Yv(1)), Y(1) - 3))                  # L19
        LE.append((vec(lambda r, u, v: -((3 * u + v - 3) if r == 0 else 0), y2=Yv(3)), Y(3) + 2 * z - 9))                          # L20
        if q == 0:
            LE.append((vec(lambda r, u, v: -1 if r == 0 else 0), -1))                                                               # L21
            LE.append((vec(lambda r, u, v: -((v - 1) if r == 0 else 0), y2=Yv(1)), Y(1) - 3))                                      # L22
    if q == 6: LE.append((vec(lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0)), 4))
    if q == 7: LE.append((vec(lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0)), 14))
    if new:
        EQ.append((vec(lambda r, u, v: 0, y0=1, y1=1, y2=1), y))                                       # y0 + y1 + y2 = y
        LE.append((vec(lambda r, u, v: u + 2 * fm(r, u, v), y1=1, y2=1), 4 * q + 2 * F))               # (I)
        if q == 0: LE.append((vec(lambda r, u, v: 1 if r == 0 else 0), z - (32 - rho6)))              # (Q0)
    if n1:
        LE.append((vec(lambda r, u, v: 3 if r == 3 else 0), (G - 32 - h) - q))                        # N1
    # ---- HUB case rows
    if hub:
        A_row = vec(lambda r, u, v: u if r == 3 else 0)
        if hub[0] == 'eq': EQ.append((A_row, hub[1]))
        else: LE.append((A_row, hub[1]))
    # ---- DARK case rows, exactly d dark labels
    if dk:
        d = dark; assert new
        W = lambda r, u, v: r * u
        Afn = lambda r, u, v: u if r == 3 else 0
        Zfn = lambda r, u, v: pos(r - 1) * u
        Efn = lambda r, u, v: ovf(r, u)
        D0 = lambda r, u, v: dfc(r, u)
        # dk >= rho - y2 - z - D0 + d  and  per-label capacities summed over the q - d bright labels:
        # W + y1 <= 7 (q - d) - 2 dk  =>  W + y1 - 2 D0 - 2 y2 <= 7q - 9d - 2 rho + 2z
        LE.append((vec(lambda r, u, v: W(r, u, v) - 2 * D0(r, u, v), y1=1, y2=-2), 7 * q - 9 * d - 2 * rho + 2 * z))
        # W + A + y1 <= 7 (q - d) + eps - 2 dk
        LE.append((vec(lambda r, u, v: W(r, u, v) + Afn(r, u, v) - 2 * D0(r, u, v), y1=1, y2=-2), 7 * q - 9 * d - 2 * rho + 2 * z + eps))
        # Z <= 3 (q - d) - dk  =>  Z - D0 - y2 <= 3q - 4d - rho + z
        LE.append((vec(lambda r, u, v: Zfn(r, u, v) - D0(r, u, v), y2=-1), 3 * q - 4 * d - rho + z))
        if ori == 'M':
            # 2Z + 2E + 3 dk <= 6 (q - d)  =>  2Z + 2E - 3 D0 - 3 y2 <= 6q - 9d - 3 rho + 3z
            LE.append((vec(lambda r, u, v: 2 * Zfn(r, u, v) + 2 * Efn(r, u, v) - 3 * D0(r, u, v), y2=-3), 6 * q - 9 * d - 3 * rho + 3 * z))
        else:
            # Z + E + 3 dk <= 3 (q - d)  =>  Z + E - 3 D0 - 3 y2 <= 3q - 6d - 3 rho + 3z
            LE.append((vec(lambda r, u, v: Zfn(r, u, v) + Efn(r, u, v) - 3 * D0(r, u, v), y2=-3), 3 * q - 6 * d - 3 * rho + 3 * z))
            # W + A + 3 dk <= 7 (q - d)  =>  W + A - 3 D0 - 3 y2 <= 7q - 10d - 3 rho + 3z
            LE.append((vec(lambda r, u, v: W(r, u, v) + Afn(r, u, v) - 3 * D0(r, u, v), y2=-3), 7 * q - 10 * d - 3 * rho + 3 * z))
        Uanch = lambda r, u, v: u if r >= 1 else 0
        LE.append((vec(lambda r, u, v: -Uanch(r, u, v)), -(q - d)))                                  # every bright label has an anchored H-B edge
        LE.append((vec(Uanch, y1=1, Fb=-2), 4 * (q - d)))                                            # bright occurrences
        LE.append((vec(lambda r, u, v: 0, y2d=1, Fd=-2), 4 * d))                                     # dark occurrences
        LE.append((vec(fm, Fb=1, Fd=1), F))                                                          # F budget
        LE.append((vec(lambda r, u, v: 0, y2d=1, y2=-1), 0))                                         # y2d <= y2
        LE.append((vec(lambda r, u, v: 0, y2=1, y2d=-1), comb(q, 2)))                                # y2m <= C(q,2)
        LE.append((vec(lambda r, u, v: u + 2 * fm(r, u, v), y1=1, y2=2, y2d=-1), 4 * q + 2 * F))     # (I')
        if d == q: LE.append((vec(lambda r, u, v: 0, Fb=1), 0))
        if d == 0: LE.append((vec(lambda r, u, v: 0, Fd=1, y2d=1), 0))
    return cols, EQ, LE

def lp_ok(cols, EQ, LE):
    if not cols: return False
    idx = {c: i for i, c in enumerate(cols)}
    def mat(rows):
        A = np.zeros((len(rows), len(cols)))
        for i, (row, _) in enumerate(rows):
            for c, val in row.items(): A[i, idx[c]] = val
        return A, np.array([b for _, b in rows], float)
    A_eq, b_eq = mat(EQ); A_ub, b_ub = mat(LE)
    r = linprog(np.zeros(len(cols)), A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    if r.status == 2: return False
    if r.status != 0: print('LP status', r.status, file=sys.stderr)
    return True

def hub_cases(variant, q):
    if 'HUBX' in variant: return [('eq', a) for a in range(0, q + 1)]
    if 'HUB' in variant and q >= KAPPA + 1: return [('eq', q - d) for d in range(0, q - KAPPA)] + [('le', KAPPA)]
    return [None]
def dark_cases(variant, q):
    return list(range(0, q + 1)) if 'DARK' in variant else [None]

@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    if (q == 0 and z == 0) or (ori == 'Mt' and q == 0 and z < 8): return False       # Lemma 10.3
    if 2 * h + y + z + comb(q, 2) < 32: return False                                 # (4.4)
    variant = VARIANT[0]
    for hc in hub_cases(variant, q):
        if not lp_ok(*system(h, y, F, q, z, ori, variant, hc, None)): continue       # the hub case alone is infeasible
        for dc in dark_cases(variant, q):
            if dc is None: return True
            if lp_ok(*system(h, y, F, q, z, ori, variant, hc, dc)): return True
    return False

if __name__ == '__main__':
    mode = sys.argv[1]; VARIANT[0] = sys.argv[2] if len(sys.argv) > 2 else 'GstarN1HUBDARK'
    t0 = time.time(); V = VARIANT[0]
    ref_file = REF.get(V.replace('HUBX', 'HUB'))
    if mode == 'keys':
        keys = [tuple(k) for k in json.load(open(SPRINT/'lb76/g75_keys.json'))['feasible']]
        still = [k for k in keys if feasible(*k)]
        print(f'variant {V}: of {len(keys)} baseline-feasible keys, {len(still)} still feasible; by q {sorted(Counter(k[3] for k in still).items())}; '
              f'by ori {dict(Counter(k[5] for k in still))}; {time.time()-t0:.0f}s', flush=True)
        if ref_file and ref_file.exists():
            ref = {tuple(k) for k in json.load(open(ref_file))['keys_still_feasible']}; mine = set(still)
            print(f'compared with qreal {ref_file.name}: ref {len(ref)}, mine {len(mine)}, only-ref {len(ref - mine)}, only-mine {len(mine - ref)}')
            for k in sorted(ref ^ mine)[:40]: print('   differs:', k, 'ref' if k in ref else 'mine')
        json.dump([list(k) for k in still], open(OUT/f'lp_qrc_keys_{V}.json', 'w'))
    elif mode == 'scan':
        lp_regen.feasible = feasible
        states, claims, survivors = lp_regen.run(G)
        byo = Counter(ori for st, ori, k, ell in survivors)
        sf = Counter(st[10] - (k + ell) for st, ori, k, ell in survivors)
        print(f'variant {V}: survivors {len(survivors)} (M {byo["M"]}, Mt {byo["Mt"]}); shortfall hist {sorted(sf.items())}; LP keys evaluated {feasible.cache_info().currsize}; {time.time()-t0:.0f}s', flush=True)
        if ref_file and ref_file.exists():
            ref = {(tuple(s['state']), s['ori']) for s in json.load(open(ref_file))['survivors']}
            mine = {(tuple(st), ori) for st, ori, k, ell in survivors}
            print(f'compared with qreal: ref {len(ref)}, mine {len(mine)}, only-ref {len(ref - mine)}, only-mine {len(mine - ref)}')
        json.dump([(list(st), ori, k, ell) for st, ori, k, ell in survivors], open(OUT/f'lp_qrc_scan_{V}.json', 'w'))
