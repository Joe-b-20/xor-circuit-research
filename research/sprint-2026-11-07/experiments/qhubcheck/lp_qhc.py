#!/usr/bin/env python3
"""qhubcheck/lp_qhc.py -- independent LP with the HUB2 case split and the packing rows PK4/PK5, written from the
statements in qhub/REPORT.md section 4 (Lemma H2, row HUB2, PK4, PK5) on top of qrealcheck's lp_qrc.py rows
(base rows L1-L23 + qbound's G*/N1 modifications + qreal's DARK split, which qrealcheck verified to reproduce
qreal's 1,134 / 681 / 585 / 381 key sets and 1,256 / 996 survivor sets exactly).  Nothing is imported from
qh_lp.py / qr_lp.py; only the package's lp_regen.run (the claim enumeration driver) is reused.

  HUB2   Lemma H2 / row HUB2: for every helper with r <= 2,  u <= (3 - r) + (q - A),  A = sum_{r=3} u n.
         Case split as qhub: for q >= 2 the cases A = q - d, d = 0..q-2 (every type with r <= 2 and u > 3 - r + d
         removed, equality sum_{r=3} u n = q - d added) and the case A <= 1 (row sum_{r=3} u n <= 1, nothing removed).
         q <= 1: no split (the row is vacuous).
  HUB2X  my refinement: integer cases A = a for every a = 0..q (types r <= 2 with u > 3 - r + q - a removed).  At least
         as strong as HUB2; a cross-check that the fractional 'A <= 1' case loses nothing.
  PK     q = 4:  n_{u>=3} <= 1;   q = 5:  n_3 + 2 n_4 + 2 n_5 <= 2   (pk_enum.py: the exact hull facets).
  HUB    qreal's row (kappa = 4) with qreal's split, as in lp_qrc.py, for reproducing 996 / 381.
  DARK   qreal's exact split on q_D = 0..q (both orientations), as in lp_qrc.py.
  FM is NOT implemented (qhub's variants carry it; qhub and qreal report that it changes nothing: 996/381 with and
  without it).  If the counts below differ from qhub's, FM is the first suspect.
usage: python3 lp_qhc.py keys VARIANT | scan VARIANT
       VARIANT in GstarN1HUBDARK, GstarN1HUB2DARK, GstarN1HUB2DARKPK, GstarN1HUB2XDARK, GstarN1HUB2XDARKPK
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
OUT = SPRINT/'qhubcheck'
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
G = 75; KAPPA = 4
KR = {0: 3, 1: 2, 2: 1}            # finite fact H2: a helper with r <= 2 has at most 3 - r full-met missing labels
VARIANT = ['GstarN1HUB2DARKPK']
REF = {'GstarN1HUBDARK': SPRINT/'qhub/scan_GstarN1HUBDARKMFM_q0_g75.json',
       'GstarN1HUB2DARK': SPRINT/'qhub/scan_GstarN1HUB2DARKMFM_q0_g75.json',
       'GstarN1HUB2DARKPK': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json',
       'GstarN1HUB2XDARK': SPRINT/'qhub/scan_GstarN1HUB2DARKMFM_q0_g75.json',
       'GstarN1HUB2XDARKPK': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json',
       'GstarN1HUB2DARKFM': SPRINT/'qhub/scan_GstarN1HUB2DARKMFM_q0_g75.json',
       'GstarN1HUB2DARKPKFM': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json'}

FMTAB = {}
def fm_table(ori):
    if ori not in FMTAB:
        d = json.load(open(OUT/f'fm_tab_{ori}.json')); FMTAB[ori] = (d['top'], d['top3'])
    return FMTAB[ori]

def ucap(variant, r, slack):
    """largest u allowed for a non-full helper when q - A = slack"""
    return (KR[r] if 'HUB2' in variant else KAPPA) + slack

def system(h, y, F, q, z, ori, variant, hub=None, dark=None):
    """hub: None | ('eq', a) [A = a, types r<3 with u > cap(r) + q - a removed] | ('le', a) [A <= a, nothing removed].
    dark: None | d (exactly d dark labels).  Returns (columns, EQ, LE) with rows as dicts column -> coefficient."""
    new = 'Gstar' in variant; n1 = 'N1' in variant; dk = dark is not None
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    if hub and hub[0] == 'eq':
        types = [t for t in types if not (t[0] < 3 and t[1] > ucap(variant, t[0], q - hub[1]))]
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
    Y = (lambda c: 0) if new else (lambda c: c * y)
    Yv = (lambda c: -c) if new else (lambda c: 0)
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
    if q == 6: LE.append((vec(lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0)), 4))                                             # L23
    if q == 7: LE.append((vec(lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0)), 14))
    if 'PK' in variant:
        if q == 4: LE.append((vec(lambda r, u, v: 1 if u >= 3 else 0), 1))                                                          # PK4
        if q == 5: LE.append((vec(lambda r, u, v: {3: 1, 4: 2, 5: 2}.get(u, 0)), 2))                                                # PK5
    if new:
        EQ.append((vec(lambda r, u, v: 0, y0=1, y1=1, y2=1), y))
        LE.append((vec(lambda r, u, v: u + 2 * fm(r, u, v), y1=1, y2=1), 4 * q + 2 * F))               # (I)
        if q == 0: LE.append((vec(lambda r, u, v: 1 if r == 0 else 0), z - (32 - rho6)))              # (Q0)
    if n1:
        LE.append((vec(lambda r, u, v: 3 if r == 3 else 0), (G - 32 - h) - q))                        # N1
    if 'FM' in variant:
        # qreal's FM7 / FM9 chord rows with MY tables (fm_check.py): W + y1 <= 7 (q - A) + top(A), Z <= 3 (q - A) + top3(A)
        top, top3 = fm_table(ori)
        for a0 in range(0, q):
            s = top[a0 + 1] - top[a0]; s3 = top3[a0 + 1] - top3[a0]
            LE.append((vec(lambda r, u, v, s=s: r * u + ((7 - s) * u if r == 3 else 0), y1=Y1(1)), 7 * q + top[a0] - s * a0))
            LE.append((vec(lambda r, u, v, s3=s3: pos(r - 1) * u + ((3 - s3) * u if r == 3 else 0)), 3 * q + top3[a0] - s3 * a0))
    if hub:
        A_row = vec(lambda r, u, v: u if r == 3 else 0)
        if hub[0] == 'eq': EQ.append((A_row, hub[1]))
        else: LE.append((A_row, hub[1]))
    if dk:
        d = dark; assert new
        W = lambda r, u, v: r * u
        Afn = lambda r, u, v: u if r == 3 else 0
        Zfn = lambda r, u, v: pos(r - 1) * u
        Efn = lambda r, u, v: ovf(r, u)
        D0 = lambda r, u, v: dfc(r, u)
        LE.append((vec(lambda r, u, v: W(r, u, v) - 2 * D0(r, u, v), y1=1, y2=-2), 7 * q - 9 * d - 2 * rho + 2 * z))
        LE.append((vec(lambda r, u, v: W(r, u, v) + Afn(r, u, v) - 2 * D0(r, u, v), y1=1, y2=-2), 7 * q - 9 * d - 2 * rho + 2 * z + eps))
        LE.append((vec(lambda r, u, v: Zfn(r, u, v) - D0(r, u, v), y2=-1), 3 * q - 4 * d - rho + z))
        if ori == 'M':
            LE.append((vec(lambda r, u, v: 2 * Zfn(r, u, v) + 2 * Efn(r, u, v) - 3 * D0(r, u, v), y2=-3), 6 * q - 9 * d - 3 * rho + 3 * z))
        else:
            LE.append((vec(lambda r, u, v: Zfn(r, u, v) + Efn(r, u, v) - 3 * D0(r, u, v), y2=-3), 3 * q - 6 * d - 3 * rho + 3 * z))
            LE.append((vec(lambda r, u, v: W(r, u, v) + Afn(r, u, v) - 3 * D0(r, u, v), y2=-3), 7 * q - 10 * d - 3 * rho + 3 * z))
        Uanch = lambda r, u, v: u if r >= 1 else 0
        LE.append((vec(lambda r, u, v: -Uanch(r, u, v)), -(q - d)))
        LE.append((vec(Uanch, y1=1, Fb=-2), 4 * (q - d)))
        LE.append((vec(lambda r, u, v: 0, y2d=1, Fd=-2), 4 * d))
        LE.append((vec(fm, Fb=1, Fd=1), F))
        LE.append((vec(lambda r, u, v: 0, y2d=1, y2=-1), 0))
        LE.append((vec(lambda r, u, v: 0, y2=1, y2d=-1), comb(q, 2)))
        LE.append((vec(lambda r, u, v: u + 2 * fm(r, u, v), y1=1, y2=2, y2d=-1), 4 * q + 2 * F))
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
    if 'HUB2X' in variant: return [('eq', a) for a in range(0, q + 1)]
    if 'HUB2' in variant:
        if q >= 2: return [('eq', q - d) for d in range(0, q - 1)] + [('le', 1)]
        return [None]
    if 'HUB' in variant and q >= KAPPA + 1: return [('eq', q - d) for d in range(0, q - KAPPA)] + [('le', KAPPA)]
    return [None]
def dark_cases(variant, q):
    return list(range(0, q + 1)) if 'DARK' in variant else [None]

RECORD = {}
@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    res = _feasible(h, y, F, q, z, ori); RECORD[(h, y, F, q, z, ori)] = res; return res

def _feasible(h, y, F, q, z, ori):
    if (q == 0 and z == 0) or (ori == 'Mt' and q == 0 and z < 8): return False       # Lemma 10.3
    if 2 * h + y + z + comb(q, 2) < 32: return False                                 # (4.4)
    variant = VARIANT[0]
    for hc in hub_cases(variant, q):
        if not lp_ok(*system(h, y, F, q, z, ori, variant, hc, None)): continue
        for dc in dark_cases(variant, q):
            if dc is None: return True
            if lp_ok(*system(h, y, F, q, z, ori, variant, hc, dc)): return True
    return False

if __name__ == '__main__':
    mode = sys.argv[1]; VARIANT[0] = sys.argv[2] if len(sys.argv) > 2 else 'GstarN1HUB2DARKPK'
    t0 = time.time(); V = VARIANT[0]
    ref_file = REF.get(V)
    if mode == 'keys':
        keys = [tuple(k) for k in json.load(open(SPRINT/'lb76/g75_keys.json'))['feasible']]
        still = [k for k in keys if feasible(*k)]
        print(f'variant {V}: of {len(keys)} baseline-feasible keys, {len(still)} still feasible; by q {sorted(Counter(k[3] for k in still).items())}; '
              f'by ori {dict(Counter(k[5] for k in still))}; {time.time()-t0:.0f}s', flush=True)
        if ref_file and ref_file.exists():
            ref = {tuple(k) for k in json.load(open(ref_file))['keys_still_feasible']}; mine = set(still)
            print(f'compared with qhub {ref_file.name}: ref {len(ref)}, mine {len(mine)}, only-ref {len(ref - mine)}, only-mine {len(mine - ref)}')
            for k in sorted(ref ^ mine)[:40]: print('   differs:', k, 'ref' if k in ref else 'mine')
        json.dump([list(k) for k in still], open(OUT/f'lp_qhc_keys_{V}.json', 'w'))
    elif mode == 'scan':
        lp_regen.feasible = feasible
        states, claims, survivors = lp_regen.run(G)
        byo = Counter(ori for st, ori, k, ell in survivors)
        sf = Counter(st[10] - (k + ell) for st, ori, k, ell in survivors)
        print(f'variant {V}: survivors {len(survivors)} (M {byo["M"]}, Mt {byo["Mt"]}); shortfall hist {sorted(sf.items())}; LP keys evaluated {feasible.cache_info().currsize}; {time.time()-t0:.0f}s', flush=True)
        if ref_file and ref_file.exists():
            refd = json.load(open(ref_file))
            ref = {(tuple(s['state']), s['ori']) for s in refd['survivors']}
            refkl = {(tuple(s['state']), s['ori']): (s['k'], s['ell']) for s in refd['survivors']}
            mine = {(tuple(st), ori) for st, ori, k, ell in survivors}
            minekl = {(tuple(st), ori): (k, ell) for st, ori, k, ell in survivors}
            same_kl = sum(1 for key in ref & mine if refkl[key] == minekl[key])
            print(f'compared with qhub {ref_file.name}: ref {len(ref)}, mine {len(mine)}, only-ref {len(ref - mine)}, only-mine {len(mine - ref)}; identical (k, ell) on {same_kl} common survivors')
        # complete key bookkeeping (qrealcheck remark 8.1): every key the scan touched, the feasible ones, the load-bearing ones
        feas = {k for k, v in RECORD.items() if v}
        base = {tuple(k) for k in json.load(open(SPRINT/'lb76/g75_keys.json'))['feasible']}
        lb = set()
        for st, ori, k, ell in survivors:
            other = 'Mt' if ori == 'M' else 'M'
            for q in range(0, k + 1):
                if (st[4], st[2], st[3], q, k - q, ori) in feas: lb.add((st[4], st[2], st[3], q, k - q, ori))
            for q in range(0, ell + 1):
                if (st[5], st[3], st[2], q, ell - q, other) in feas: lb.add((st[5], st[3], st[2], q, ell - q, other))
        print(f'keys touched {len(RECORD)}; LP-feasible {len(feas)} (by q {sorted(Counter(k[3] for k in feas).items())}; in the baseline 1,134: {len(feas & base)}); '
              f'load-bearing {len(lb)} (by q {sorted(Counter(k[3] for k in lb).items())}; by ori {dict(Counter(k[5] for k in lb))}; in the baseline: {len(lb & base)})', flush=True)
        json.dump([(list(st), ori, k, ell) for st, ori, k, ell in survivors], open(OUT/f'lp_qhc_scan_{V}.json', 'w'))
        json.dump(dict(feasible=sorted(list(k) for k in feas), load_bearing=sorted(list(k) for k in lb)), open(OUT/f'lp_qhc_keysfull_{V}.json', 'w'))
