#!/usr/bin/env python3
"""qhubcheck/vert_key.py -- diagnose the one key where HUB2 without FM and HUB2 with FM differ: for the key given on the
command line (default 9 6 8 7 0 Mt), list the (hub case, dark case) pairs that are LP-feasible under GstarN1HUB2DARKPK
(no FM) and under GstarN1HUB2DARKPKFM (own FM tables), print one vertex of a feasible no-FM case, and evaluate on it
W + y1 against 7 (q - A) + top(A) (FM7) with the own table, to show which row kills it and by how much."""
import sys, json
import numpy as np
from scipy.optimize import linprog
sys.path.insert(0, '/home/joebachir20/xs-campaigns/2026-11-07-sprint/qhubcheck')
import lp_qhc

def solve(cols, EQ, LE, c=None):
    idx = {cc: i for i, cc in enumerate(cols)}
    def mat(rows):
        A = np.zeros((len(rows), len(cols)))
        for i, (row, _) in enumerate(rows):
            for k, val in row.items(): A[i, idx[k]] = val
        return A, np.array([b for _, b in rows], float)
    A_eq, b_eq = mat(EQ); A_ub, b_ub = mat(LE)
    r = linprog(np.zeros(len(cols)) if c is None else c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    return r

if __name__ == '__main__':
    a = sys.argv[1:] or ['9', '6', '8', '7', '0', 'Mt']
    h, y, F, q, z = map(int, a[:5]); ori = a[5]
    top, top3 = lp_qhc.fm_table(ori)
    print(f'key (h,y,F,q,z,ori) = ({h},{y},{F},{q},{z},{ori}); own FM table top[:9] = {top[:9]}, top3[:9] = {top3[:9]}')
    for V in ('GstarN1HUB2DARKPK', 'GstarN1HUB2DARKPKFM'):
        feas = []
        for hc in lp_qhc.hub_cases(V, q):
            for dc in lp_qhc.dark_cases(V, q):
                cols, EQ, LE = lp_qhc.system(h, y, F, q, z, ori, V, hc, dc)
                r = solve(cols, EQ, LE)
                if r.status == 0: feas.append((hc, dc))
        print(f'{V}: feasible (hub case, dark case) pairs: {feas}')
        if feas and 'FM' not in V:
            hc, dc = feas[0]
            cols, EQ, LE = lp_qhc.system(h, y, F, q, z, ori, V, hc, dc)
            # a vertex minimizing A (to see how far FM7 is from binding) and one maximizing A
            for name, sign in (('min A', 1), ('max A', -1)):
                c = np.array([sign * (t[1] if isinstance(t, tuple) and t[0] == 3 else 0) for t in cols], float)
                r = solve(cols, EQ, LE, c)
                x = dict(zip(cols, r.x))
                W = sum(t[0] * t[1] * v for t, v in x.items() if isinstance(t, tuple))
                A = sum(t[1] * v for t, v in x.items() if isinstance(t, tuple) and t[0] == 3)
                y1 = x.get('y1', 0.0)
                # concave envelope of top at real A
                a0 = min(int(np.floor(A)), len(top) - 2); s = top[a0 + 1] - top[a0]; topA = top[a0] + s * (A - a0)
                print(f'   case {hc} {dc}, vertex ({name}): ' + ' '.join(f'{t}:{v:.3g}' for t, v in x.items() if abs(v) > 1e-9))
                print(f'      W = {W:.3f}, y1 = {y1:.3f}, A = {A:.3f}: FM7 needs W + y1 <= 7 (q - A) + top(A) = {7 * (q - A) + topA:.3f}; '
                      f'L7* allowed {7 * q}; violation of FM7 by {W + y1 - (7 * (q - A) + topA):.3f}')
