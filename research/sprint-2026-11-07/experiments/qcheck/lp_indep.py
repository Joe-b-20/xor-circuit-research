#!/usr/bin/env python3
"""qcheck: independent implementation of the local LP (package rows L1-L23 from PROOF.md + the qbound rows
N1, L7*, L12*, (I), (Q0), y->y2 in L13-L20/L22, W->W+y1 in L13/L14) written from the statements, not from qb_lp.py.

mode keys : evaluate the 1,134 baseline-feasible keys of lb76/g75_keys.json under base / new rows; compare the surviving
            key set with qbound/scan_GstarN1_q0_g75.json (681 keys).
mode scan : plug this feasibility function into the package driver lp_regen.run(75) and count surviving oriented claims.
usage: python3 lp_indep.py keys | scan [variant]      variant in base, N1, Gstar, GstarN1 (default GstarN1)
"""
import sys, json, time
from math import comb
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
import lp_regen
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
G = 75
VARIANT = ['GstarN1']

def system(h, y, F, q, z, ori, variant):
    new = 'Gstar' in variant; n1 = 'N1' in variant
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    nt = len(types); ncol = nt + (3 if new else 0)        # columns: types, then y0, y1, y2
    rho6 = RHO6[ori]; rho = RHO[ori]; eps = EPS[ori]
    fm = lambda r, u, v: max(0, (r + u + v - 3) // 2)
    pos = lambda t: max(0, t)
    def vec(fn, y0=0, y1=0, y2=0):
        row = [float(fn(r, u, v)) for r, u, v in types]
        if new: row += [float(y0), float(y1), float(y2)]
        return row
    # in the new system y enters the quotient rows only through (G*), i.e. as the variable y2; in base it is the constant y
    Y = (lambda c: 0) if new else (lambda c: c * y)      # constant part
    Yv = (lambda c: -c) if new else (lambda c: 0)        # coefficient of the variable y2 moved to the left-hand side
    Y1 = (lambda c: c) if new else (lambda c: 0)         # coefficient of y1 on the left (L7*, L13*, L14*)
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
        # L19: 3 <= y + sum_{r=0}(u+v-1) n + sum_{r=1} v n   ->  -sum(...) - y2 <= y - 3
        LE.append((vec(lambda r, u, v: -((u + v - 1) if r == 0 else (v if r == 1 else 0)), y2=Yv(1)), Y(1) - 3))
        # L20: 9 <= 3y + 2z + sum_{r=0}(3u+v-3) n
        LE.append((vec(lambda r, u, v: -((3 * u + v - 3) if r == 0 else 0), y2=Yv(3)), Y(3) + 2 * z - 9))
        if q == 0:
            LE.append((vec(lambda r, u, v: -1 if r == 0 else 0), -1))                                                               # L21
            LE.append((vec(lambda r, u, v: -((v - 1) if r == 0 else 0), y2=Yv(1)), Y(1) - 3))                                      # L22
    if q == 6: LE.append((vec(lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0)), 4))
    if q == 7: LE.append((vec(lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0)), 14))
    if new:
        EQ.append((vec(lambda r, u, v: 0, y0=1, y1=1, y2=1), y))                                       # y0 + y1 + y2 = y
        LE.append((vec(lambda r, u, v: u + 2 * fm(r, u, v), y1=1, y2=1), 4 * q + 2 * F))               # (I)
        if q == 0: LE.append((vec(lambda r, u, v: 1 if r == 0 else 0), z - (32 - rho6)))              # (Q0): h0 <= z - (32 - rho6)
    if n1:
        LE.append((vec(lambda r, u, v: 3 if r == 3 else 0), (G - 32 - h) - q))                        # N1: 3 n3 <= x + y - q
    return ncol, EQ, LE

@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    if (q == 0 and z == 0) or (ori == 'Mt' and q == 0 and z < 8): return False       # Lemma 10.3
    if 2 * h + y + z + comb(q, 2) < 32: return False                                 # (4.4)
    ncol, EQ, LE = system(h, y, F, q, z, ori, VARIANT[0])
    if ncol == 0: return False
    A_eq = np.array([r for r, _ in EQ]); b_eq = np.array([b for _, b in EQ], float)
    A_ub = np.array([r for r, _ in LE]); b_ub = np.array([b for _, b in LE], float)
    r = linprog(np.zeros(ncol), A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    if r.status == 2: return False
    if r.status != 0: print('LP status', r.status, (h, y, F, q, z, ori), file=sys.stderr)
    return True

if __name__ == '__main__':
    mode = sys.argv[1]; VARIANT[0] = sys.argv[2] if len(sys.argv) > 2 else 'GstarN1'
    t0 = time.time()
    if mode == 'keys':
        keys = [tuple(k) for k in json.load(open(SPRINT/'lb76/g75_keys.json'))['feasible']]
        still = [k for k in keys if feasible(*k)]
        from collections import Counter
        print(f'variant {VARIANT[0]}: of {len(keys)} baseline-feasible keys, {len(still)} still feasible; by q {sorted(Counter(k[3] for k in still).items())}; {time.time()-t0:.0f}s')
        ref_file = SPRINT/'qbound'/f'scan_{VARIANT[0]}_q0_g{G}.json'
        if ref_file.exists():
            ref = {tuple(k) for k in json.load(open(ref_file))['keys_still_feasible']}
            mine = set(still)
            print(f'compared with qbound {ref_file.name}: ref {len(ref)}, mine {len(mine)}, only-ref {len(ref - mine)}, only-mine {len(mine - ref)}')
            for k in sorted(ref ^ mine)[:20]: print('   differs:', k, 'ref' if k in ref else 'mine')
        json.dump([list(k) for k in still], open(SPRINT/'qcheck'/f'lp_indep_keys_{VARIANT[0]}.json', 'w'))
    elif mode == 'scan':
        lp_regen.feasible = feasible
        states, claims, survivors = lp_regen.run(G)
        from collections import Counter
        byo = Counter(ori for st, ori, k, ell in survivors)
        print(f'variant {VARIANT[0]}: survivors {len(survivors)} (M {byo["M"]}, Mt {byo["Mt"]}); LP keys evaluated {feasible.cache_info().currsize}; {time.time()-t0:.0f}s')
        ref_file = SPRINT/'qbound'/f'scan_{VARIANT[0]}_q0_g{G}.json'
        if ref_file.exists():
            ref = {(tuple(s['state']), s['ori']) for s in json.load(open(ref_file))['survivors']}
            mine = {(tuple(st), ori) for st, ori, k, ell in survivors}
            print(f'compared with qbound: ref {len(ref)}, mine {len(mine)}, symmetric difference {len(ref ^ mine)}')
        json.dump([(list(st), ori, k, ell) for st, ori, k, ell in survivors], open(SPRINT/'qcheck'/f'lp_indep_scan_{VARIANT[0]}.json', 'w'))
