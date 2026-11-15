"""Is there a k-product level-1 cover of V_N whose x^5-class projection has GF(2)-rank <= R?
(agent H1; question from NOTES.md section 2 / TRICKS.md section 2: all 9-covers seen in the record
circuits have rank exactly 2; rank <= 1 would give a 9-product stage 1 room for 4 dims of
GF(4)-norm-type junk).

Model: track C's exact stage-1 SAT encoding (strategies/C/stage1.py, c free, lex symmetry or one
product fixed to an orbit representative of x -> a x^(2^i), which also preserves the rank of the
x^5 projection since it acts GF(2)-linearly and bijectively on the x^5 coefficient), plus:
c5(product j) = sum_r W[j][r] c5(U_a U_b) (8 bits, linear in the wedge bits), and for R = 1:
c5_j = s_j * beta (one common 8-bit beta); for R = 0: c5_j = 0.
usage: python3 rho2_sat.py K R [--reps]
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'C'))
sys.path.insert(0, str(HERE))
import gf          # noqa: E402
import qmc         # noqa: E402
import stage1      # noqa: E402
import xag         # noqa: E402


def c5_of_pair(a, b):
    t = gf.X[a] & gf.X[b]
    return xag.coeff(t, 5)


C5 = [c5_of_pair(a, b) for a, b in stage1.PAIRS]


def add_rank(f, k, R):
    # recover W: stage1.encode builds W[j] as fresh vars; we rebuild them from L, M which are the
    # first 16 k variables (L then M per product), see stage1.encode
    L = [list(range(1 + 8 * j, 9 + 8 * j)) for j in range(k)]
    M = [list(range(1 + 8 * k + 8 * j, 9 + 8 * k + 8 * j)) for j in range(k)]
    if R >= 8: return                       # no constraint (positive control)
    betas = [f.vars(8) for _ in range(R)]
    for j in range(k):
        W = [f.xor2(f.and2(L[j][a], M[j][b]), f.and2(L[j][b], M[j][a])) for a, b in stage1.PAIRS]
        s = [f.var() for _ in range(R)]
        for bit in range(8):
            terms = [W[r] for r in range(28) if (C5[r] >> bit) & 1]
            c = f.xor_list(terms)
            # c == sum_r s_r & beta_r[bit]
            ys = [f.and2(s[r], betas[r][bit]) for r in range(R)]
            y = f.xor_list(ys)
            if c is None and y is None: continue
            if y is None: f.fix(c, 0); continue
            if c is None: f.fix(y, 0); continue
            f.cl.append([-c, y]); f.cl.append([c, -y])


def main():
    k = int(sys.argv[1]); R = int(sys.argv[2])
    runs = [None]
    if '--reps' in sys.argv:
        runs = [(la, lb) for la, lb, sz in stage1.orbit_reps()]
    for i, R1 in enumerate(runs):
        f = stage1.encode(k, R1)
        add_rank(f, k, R)
        ok, model, dt = qmc.solve(f, 'cadical153')
        print(json.dumps({'k': k, 'R': R, 'rep': i, 'sat': ok, 'secs': round(dt, 1),
                          'vars': f.n, 'clauses': len(f.cl)}), flush=True)
        if ok:
            break


if __name__ == '__main__':
    main()
