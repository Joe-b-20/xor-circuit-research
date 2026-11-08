#!/usr/bin/env python3
"""qhub LP: qreal's qr_lp.py with the per-r hub capacity of finite fact H2 (hub2.py): variant HUB2 =
exact case split on A = sum_{r=3} u n with u <= (3 - r) + (q - A) for every type with r <= 2.
Original header follows.

qreal LP: qbound's qb_lp.py (package rows L1-L23 + G* + N1) extended with the qreal rows.

Variants are substrings of the variant name:
  Gstar, N1   as in qbound/qb_lp.py (reproduced unchanged: 1,313 claims / 681 keys at G = 75)
  HUB         finite fact H1 (hub.py): kappa = 4.  For every helper i with r_i < 3:  u_i <= kappa + (q - A),
              A = sum_{r=3} u n (the missing labels that meet a full helper; exactly one each, Lemma 4.5).
              EXACT case split on A: cases d = 0..q-kappa-1 with A = q - d and no type (r<3, u > kappa + d), plus
              the case A <= kappa.  A key is feasible iff some case is LP-feasible (each case Farkas-certifiable).
  HUBlin      the linear aggregate instead: sum_{r<3} (u-kappa)_+ n + 4A + 2 sum f_min n <= 4q + 2F.
  DARK        Task (c): exact case split on q_D = number of dark missing labels (0..q), with the package's quotient
              rows re-derived KEEPING the -q_D terms, bright/dark occurrence budgets and the y_2 decomposition
              (aux columns y2d = ee gates whose single missing signal is dark, Fb/Fd = sum of f over bright/dark
              labels).  See dark_rows().
  BD          finite fact (fullsets.py): boundary-degree budget and output assignment for the full helpers:
              n3 <= m_max(key) where m_max is the largest m with 9m + 64 - C(m) <= sum_B d_v and flow(m) >= 2m.
  INT         integer feasibility (HiGHS branch and bound) on top of the LP.
usage: python3 qr_lp.py scan VARIANT [G]
       python3 qr_lp.py vertex h y F q z ori [VARIANT]
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
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhubcheck'
QREAL = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}
KAPPA = 4            # hub.py: kappa_0 = kappa_1 = 4 for M and Mt
KR2 = {0: 3, 1: 2, 2: 1}   # hub2.py (H2): a helper with r <= 2 has at most 3 - r full-met missing labels (M and Mt)
def kr(variant, r):
    return KR2[r] if 'HUB2' in variant else KAPPA
AUX_BASE = ['y0', 'y1', 'y2']; AUX_DARK = ['y2d', 'Fb', 'Fd']
FULLSETS = {}
def fullsets(ori):
    if ori not in FULLSETS:
        d = json.load(open(QREAL/f'fullsets_{ori}.json'))
        FULLSETS[ori] = {int(m): v for m, v in d['per_m'].items()}, d['complete']
    return FULLSETS[ori]

FULLMET = {}
def fullmet_tab(ori):
    if ori not in FULLMET: FULLMET[ori] = json.load(open(QREAL/f'fullmet_{ori}.json'))
    return FULLMET[ori]

def f_min(r, u, v): return max(0, (r + u + v - 3) // 2)
def deficit(r, u): return u - 1 if r == 0 else 0
def overflow(r, u): return max(0, u - 2) if r == 3 else 0

def build(h, y, F, q, z, ori, variant='base', extra_q=0, hub_case=None, dark_case=None):
    """Return (cols, A_eq, b_eq, A_ub, b_ub, names).
    hub_case: None | ('d', d) [A = q - d, types r<3 need u <= kappa + d] | ('low',) [A <= kappa]
    dark_case: None | qD (exact number of dark labels)."""
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    if hub_case and hub_case[0] == 'd':
        d = hub_case[1]
        types = [t for t in types if not (t[0] < 3 and t[1] > kr(variant, t[0]) + d)]
    use_aux = 'Gstar' in variant
    AUX = (AUX_BASE + (AUX_DARK if 'DARK' in variant else [])) if use_aux else []
    xy = GCUR[0] - 32 - h            # x + y of the phase = number of even signals; x + y - q = represented labels
    def row(fn, aux=None):
        r_ = [fn(*t) for t in types] + [0.0] * len(AUX)
        if aux:
            for k, c in aux.items(): r_[len(types) + AUX.index(k)] = c
        return r_
    rho = RHO6[ori]; res = RESERVE[ori]
    eq, le = [], []
    def EQ(name, fn, b, aux=None): eq.append((name, row(fn, aux), b))
    def LE(name, fn, b, aux=None): le.append((name, row(fn, aux), b))
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
    if 'PK' in variant:
        # Lemma 10.4's argument at q = 4, 5: the missing-label sets of the helpers with u >= 3 are subsets of a q-set
        # pairwise intersecting in <= 1 element.  q = 4: two 3-subsets of a 4-set share 2, so N_3 <= 1 (N_j = #{u >= j}).
        # q = 5: three 3-sets pairwise sharing <= 1 need >= 6 points; a 4- or 5-set excludes every other set of size >= 3.
        if q == 4: LE('PK4: N3 <= 1', lambda r, u, v: 1 if u >= 3 else 0, 1)
        if q == 5: LE('PK5: N3 + 2 N4 <= 2', lambda r, u, v: {3: 1, 4: 2, 5: 2}.get(u, 0), 2)
    if use_aux:
        EQ('y0+y1+y2 = y', lambda r, u, v: 0, y, {'y0': 1, 'y1': 1, 'y2': 1})
        LE('ee missing incidence', lambda r, u, v: u + 2 * f_min(r, u, v), 4 * q + 2 * F, {'y1': 1, 'y2': 1})
        if q == 0:
            LE('G* q=0: z >= 32 - rho6 + n_r0', lambda r, u, v: int(r == 0), z - (32 - rho))
    if 'N1' in variant:
        LE('N1 full-helper labels distinct: 3 n3 <= x+y-q', lambda r, u, v: 3 if r == 3 else 0, xy - q)
    if 'HUBlin' in variant:
        LE('HUBlin: sum_{r<3}(u-k)_+ n + 4A + 2 sum fmin n <= 4q+2F',
           lambda r, u, v: (max(0, u - KAPPA) if r < 3 else 4 * u) + 2 * f_min(r, u, v), 4 * q + 2 * F)
    if hub_case:
        if hub_case[0] == 'd':
            EQ(f'HUB case A = q - {hub_case[1]}', lambda r, u, v: u if r == 3 else 0, q - hub_case[1])
            if 'HUB2L' in variant:
                # linear aggregate of H2 in the case A = q - d: m_i >= u_i - d for non-full helpers; the (non-full helper,
                # full-met label) incidences at a full-met label l number <= 3 + 2 f_l ((3.2) minus the full helper's edge);
                # summed over the A full-met labels: sum_{r<3} (u - d)_+ n <= 3 A + 2 (F - F_H).
                dd = hub_case[1]
                LE(f'HUB2L: sum_(r<3) (u-{dd})_+ n + 2 F_H <= 3 (q-{dd}) + 2F', lambda r, u, v, dd=dd: (max(0, u - dd) if r < 3 else 0) + 2 * f_min(r, u, v), 3 * (q - dd) + 2 * F)
        else:
            LE(f'HUB case A <= {hub_case[1]}', lambda r, u, v: u if r == 3 else 0, hub_case[1])
    if dark_case is not None:
        dark_rows(EQ, LE, h, y, F, q, z, ori, dark_case, use_aux, rho, res)
    if "BDEG" in variant:
        per_m, complete = fullsets(ori)
        dB = 2 * (xy - q) + 32 + h - y + q - z           # sum of boundary degrees = 2 #BB + #HB
        mmax = 0
        for m in sorted(per_m):
            if 9 * m + 64 - per_m[m]['C'] <= dB and per_m[m].get('flow_ok', 1) > 0: mmax = m
            else: break
        if complete:
            # sizes above the largest enumerated size do not exist (the enumeration is complete)
            LE(f'BD: n3 <= {mmax} (boundary degree sum {dB}, output assignment)', lambda r, u, v: 1 if r == 3 else 0, mmax)
    if 'FM' in variant:
        # finite fact FM (fullmet.py): at a full-met missing label l = f + c, W_l + Y_l <= rank(C_l) and
        # Z_l <= min(3, rank(C_l) - 1); summing over the A full-met labels (distinct) and 7 / 3 over the others:
        #   (FM7) W + y1 <= 7 (q - A) + top_full(A),   (FM9) Z <= 3 (q - A) + top3_full(A)
        # top_full, top3_full are concave piecewise linear in the integer A: equal to the min of their chord lines.
        fm = fullmet_tab(ori)
        top, top3 = fm['top'], fm['top3']
        for a0 in range(0, q):
            s = top[a0 + 1] - top[a0]; s3 = top3[a0 + 1] - top3[a0]
            LE(f'FM7 chord {a0}: W + y1 + (7 - {s}) A <= 7q + {top[a0] - s * a0}',
               lambda r, u, v, s=s: r * u + ((7 - s) * u if r == 3 else 0), 7 * q + top[a0] - s * a0, ({'y1': 1} if use_aux else None))
            LE(f'FM9 chord {a0}: Z + (3 - {s3}) A <= 3q + {top3[a0] - s3 * a0}',
               lambda r, u, v, s3=s3: max(0, r - 1) * u + ((3 - s3) * u if r == 3 else 0), 3 * q + top3[a0] - s3 * a0)
    if extra_q: LE('hyp q >= C', lambda r, u, v: 0, q - extra_q)
    names = [n for n, _, _ in eq] + [n for n, _, _ in le]
    A_eq = np.array([r_ for _, r_, _ in eq], float); b_eq = np.array([b for _, _, b in eq], float)
    A_ub = np.array([r_ for _, r_, _ in le], float); b_ub = np.array([b for _, _, b in le], float)
    cols = types + AUX
    return cols, A_eq, b_eq, A_ub, b_ub, names

def dark_rows(EQ, LE, h, y, F, q, z, ori, d, use_aux, rho, res):
    """Rows valid when EXACTLY d of the q missing labels are dark (no H-B edge at an anchored helper).
    Notation: W = sum r u n, A = sum_{r=3} u n, Z = sum (r-1)_+ u n, E = sum_{r=3} (u-2)_+ n, D0 = sum_{r=0} (u-1) n,
    rho = 32 - dim J (8 for M, 4 for Mt), eps = 2 (M) / 0 (Mt).  From PROOF.md's proofs of (L13)-(L18) with the
    nonpositive q_D terms RETAINED (and y -> y2, +y1 as in qbound's G* when use_aux):
      sum_bright k_l =: dk >= rho - y2 - z - D0 + d                                  (G*)
      W + y1 <= 7 (q - d) - 2 dk          -> W + y1 - 2 D0 <= 2 y2 + 2 z + 7 q - 2 rho - 9 d       (L13d)
      W + A + y1 <= 7 (q - d) + eps - 2 dk -> W + A + y1 - 2 D0 <= 2 y2 + 2 z + 7 q - 2 rho + eps - 9 d  (L14d)
      Z <= 3 (q - d) - dk                 -> Z - D0 <= y2 + z + 3 q - rho - 4 d                    (L15d)
      M : 2Z + 2E + 3 dk <= 6 (q - d)     -> 2Z + 2E - 3 D0 <= 3 y2 + 3 z + 6 q - 24 - 9 d         (L17Md)
      Mt: Z + E + 3 dk <= 3 (q - d)       -> Z + E - 3 D0 <= 3 y2 + 3 z + 3 q - 12 - 6 d           (L17Td)
      Mt: W + A + 3 dk <= 7 (q - d)       -> W + A - 3 D0 <= 3 y2 + 3 z + 7 q - 12 - 10 d          (L18d)
    Occurrence budgets ((3.2): a missing label l occurs in <= 4 + 2 f_l equations):
      every bright label has an H-B edge at an anchored helper:          sum_{r>=1} u n >= q - d
      all missing H-B edges of anchored helpers and all kind-1 gates sit at bright labels:
                                                                           sum_{r>=1} u n + y1 <= 4 (q - d) + 2 Fb
      ee gates whose only missing signal is dark:                          y2d <= 4 d + 2 Fd
      Fb + Fd + sum f_min n <= F;  y2d <= y2;  y2 - y2d = y2m <= C(q,2) (a pair of missing labels is in <= 1 gate)
      (I'):  y1 + y2d + 2 y2m + U + 2 F_H <= 4 q + 2 F   ->   y1 + 2 y2 - y2d + U + 2 sum f_min n <= 4 q + 2 F
      d = q: Fb = 0 (no bright label);  d = 0: Fd = 0, y2d = 0."""
    eps = 2 if ori == 'M' else 0
    Yc = (lambda c: 0) if use_aux else (lambda c: c * y)
    def D0c(r, u, v): return (u - 1) if r == 0 else 0
    LE(f'L13d qD={d}', lambda r, u, v: r * u - 2 * D0c(r, u, v), Yc(2) + 2 * z + 7 * q - 2 * res - 9 * d, ({'y2': -2, 'y1': 1} if use_aux else None))
    LE(f'L14d qD={d}', lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * D0c(r, u, v), Yc(2) + 2 * z + 7 * q - 2 * res + eps - 9 * d, ({'y2': -2, 'y1': 1} if use_aux else None))
    LE(f'L15d qD={d}', lambda r, u, v: max(0, r - 1) * u - D0c(r, u, v), Yc(1) + z + 3 * q - res - 4 * d, ({'y2': -1} if use_aux else None))
    if ori == 'M':
        LE(f'L17Md qD={d}', lambda r, u, v: 2 * max(0, r - 1) * u + 2 * overflow(r, u) - 3 * D0c(r, u, v), Yc(3) + 3 * z + 6 * q - 24 - 9 * d, ({'y2': -3} if use_aux else None))
    else:
        LE(f'L17Td qD={d}', lambda r, u, v: max(0, r - 1) * u + overflow(r, u) - 3 * D0c(r, u, v), Yc(3) + 3 * z + 3 * q - 12 - 6 * d, ({'y2': -3} if use_aux else None))
        LE(f'L18d qD={d}', lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * D0c(r, u, v), Yc(3) + 3 * z + 7 * q - 12 - 10 * d, ({'y2': -3} if use_aux else None))
    LE(f'bright lower qD={d}', lambda r, u, v: -(u if r >= 1 else 0), -(q - d))
    if use_aux:
        LE(f'bright capacity qD={d}', lambda r, u, v: (u if r >= 1 else 0), 4 * (q - d), {'y1': 1, 'Fb': -2})
        LE(f'dark capacity qD={d}', lambda r, u, v: 0, 4 * d, {'y2d': 1, 'Fd': -2})
        LE('Fb + Fd + F_H <= F', f_min, F, {'Fb': 1, 'Fd': 1})
        LE('y2d <= y2', lambda r, u, v: 0, 0, {'y2d': 1, 'y2': -1})
        LE('y2m <= C(q,2)', lambda r, u, v: 0, comb(q, 2), {'y2': 1, 'y2d': -1})
        LE("(I') y1 + 2y2 - y2d + U + 2F_H <= 4q + 2F", lambda r, u, v: u + 2 * f_min(r, u, v), 4 * q + 2 * F, {'y1': 1, 'y2': 2, 'y2d': -1})
        if d == q: LE('no bright labels: Fb = 0', lambda r, u, v: 0, 0, {'Fb': 1})
        if d == 0: LE('no dark labels: Fd = 0, y2d = 0', lambda r, u, v: 0, 0, {'Fd': 1, 'y2d': 1})
    else:
        LE(f'bright capacity qD={d}', lambda r, u, v: (u if r >= 1 else 0) + 2 * f_min(r, u, v), 4 * (q - d) + 2 * F)

VARIANT = ['base']; EXTRA_Q = [0]; GCUR = [75]
UNKNOWN = []

def lp_feasible(cols, A_eq, b_eq, A_ub, b_ub, integer=False):
    if not cols: return False
    r = linprog(np.zeros(len(cols)), A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    if r.status == 2: return False
    if r.status != 0: UNKNOWN.append(('lp', r.status)); return True
    if integer:
        from scipy.optimize import milp, LinearConstraint, Bounds
        A = np.vstack([A_eq, A_ub]); lb = np.concatenate([b_eq, -np.inf * np.ones(len(b_ub))]); ub = np.concatenate([b_eq, b_ub])
        rm = milp(np.zeros(len(cols)), constraints=LinearConstraint(A, lb, ub), integrality=np.ones(len(cols)), bounds=Bounds(0, np.inf))
        if rm.status == 2: return False
        if rm.status != 0: UNKNOWN.append(('milp', rm.status)); return True
    return True

def cases(variant, q, ori):
    """the disjunctive cases of a variant: list of (hub_case, dark_case)."""
    hubs = [None]
    kmin = min(kr(variant, r) for r in (0, 1, 2))
    if 'HUB' in variant and 'HUBlin' not in variant and q > kmin:
        hubs = [('d', d) for d in range(0, q - kmin)] + [('low', kmin)]
    darks = [None]
    if 'DARK' in variant and ('DARKM' in variant or ori == 'Mt'):
        darks = list(range(0, q + 1))
    return [(hc, dc) for hc in hubs for dc in darks]

@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    if lp_regen.direct(ori, q, z): return False
    if 2 * h + y + z + comb(q, 2) < 32: return False
    variant = VARIANT[0]
    if "DARK" in variant:
        # the dark cases only add rows inside each hub case: pre-check the hub cases alone (cheap, usually infeasible)
        if not any(lp_feasible(*build(h, y, F, q, z, ori, variant.replace("DARKM", "").replace("DARK", ""), EXTRA_Q[0], hc, None)[:5])
                   for hc, _ in cases(variant.replace("DARKM", "").replace("DARK", ""), q, ori)):
            return False
    for hc, dc in cases(variant, q, ori):
        cols, A_eq, b_eq, A_ub, b_ub, names = build(h, y, F, q, z, ori, variant, EXTRA_Q[0], hc, dc)
        if lp_feasible(cols, A_eq, b_eq, A_ub, b_ub, integer=('INT' in variant)): return True
    return False
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
    nM = sum(1 for s in surv if s['ori'] == 'M'); nMt = len(surv) - nM
    print(f'variant {variant} q>={extra_q}: survivors {len(surv)} (M {nM}, Mt {nMt}); '
          f'of the 1134 baseline-feasible keys still feasible: {len(still)} (by q: {sorted(Counter(k[3] for k in still).items())}; '
          f'by ori: {dict(Counter(k[5] for k in still))}); shortfall hist {sorted(Counter(s["shortfall"] for s in surv).items())}; '
          f'unknown {len(UNKNOWN)}; {time.time()-t0:.0f}s', flush=True)
    json.dump(dict(variant=variant, extra_q=extra_q, survivors=surv, keys_still_feasible=[list(k) for k in still]),
              open(OUT/f'scan_{variant}_q{extra_q}_g{G}.json', 'w'), indent=1)
    return surv, still

def vertices(h, y, F, q, z, ori, variant='base', n=6):
    GCUR[0] = 75
    for hc, dc in cases(variant, q, ori):
        cols, A_eq, b_eq, A_ub, b_ub, names = build(h, y, F, q, z, ori, variant, 0, hc, dc)
        print(f'key (h,y,F,q,z,ori)=({h},{y},{F},{q},{z},{ori}) variant {variant} case {hc} {dc}: {len(cols)} columns, {len(names)} rows')
        rng = np.random.default_rng(1)
        seen = set()
        objs = [np.zeros(len(cols))]
        def obj(fn): return np.array([fn(*c) if isinstance(c, tuple) else 0.0 for c in cols])
        objs += [obj(lambda r, u, v: -(r == 3)), obj(lambda r, u, v: (r == 3)), obj(lambda r, u, v: -(r == 0)),
                 obj(lambda r, u, v: -(r + u + v - 3)), obj(lambda r, u, v: (r + u + v - 3)), obj(lambda r, u, v: -u), obj(lambda r, u, v: -v)]
        for _ in range(n): objs.append(rng.normal(size=len(cols)))
        for c in objs:
            r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
            if r.status != 0:
                print('  status', r.status, r.message[:60]); break
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
    elif sys.argv[1] == 'vertex':
        toks = sys.argv[2:]
        ints = [int(t) for t in toks if t.lstrip('-').isdigit()]
        words = [t for t in toks if not t.lstrip('-').isdigit()]
        h, y, F, q, z = ints[:5]; ori = words[0]
        variant = words[1] if len(words) > 1 else 'base'
        vertices(h, y, F, q, z, ori, variant)
