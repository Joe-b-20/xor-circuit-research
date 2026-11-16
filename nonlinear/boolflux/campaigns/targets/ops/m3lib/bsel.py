#!/usr/bin/env python3
"""P7: per-output Y-basis selection for a rank-1 bottom over a fixed front.

Every AES output is y_j = c_j + sum_i Y_i * u_ij(x), Y_i = Tr(alpha_i N^-1) the four base
Y-forms of the front (the Y operands of the circuit's AND-level-4 gates) and u_ij linear forms.
Any other basis {Y_b1..Y_b4} of span(Y_1..Y_4) gives another 4-product decomposition of y_j
(w = M^-T u).  Outputs that pick bases with common (Y-form, x-form) pairs share products.
Depth model: base Y-forms at level Lb (from the circuit), a sum of k base forms at Lb + ceil(log2 k),
product one level later (x-forms are early), output = XOR tree of its products (Kraft at cap D).

    bsel.py CIRCUIT --cap 12 [--restarts 200] [--seed 1] [--out plan.json]
"""
import argparse, itertools, json, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402


def gauss_solve(basis, target):
    """express target as XOR of basis tables; returns index list or None."""
    piv = {}   # pivot bit -> (vec, combo)
    for k, v in enumerate(basis):
        cmb = 1 << k
        for p, (pv, pc) in piv.items():
            if (v >> p) & 1: v ^= pv; cmb ^= pc
        if v:
            p = v.bit_length() - 1
            # reduce existing
            for q in list(piv):
                qv, qc = piv[q]
                if (qv >> p) & 1: piv[q] = (qv ^ v, qc ^ cmb)
            piv[p] = (v, cmb)
    t = target; cmb = 0
    for p, (pv, pc) in piv.items():
        if (t >> p) & 1: t ^= pv; cmb ^= pc
    if t: return None
    return [k for k in range(len(basis)) if (cmb >> k) & 1]


def front_info(c):
    T, lg, la = L.sim(c)
    n = c.n
    Ys = []; Ylev = []
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in L.core.NONLINEAR_OPS and la[s] == 4:
            for o in (a, b):
                if L.deg(T[o]) > 1:
                    t = T[o] ^ (L.ONES if T[o] & 1 else 0)
                    if t not in Ys: Ys.append(t); Ylev.append(lg[o])
    return T, lg, la, Ys, Ylev


def decompose_outputs(c, T, Ys):
    """u[j][i] masks with y_j = c_j + sum_i Y_i * lin(u_ij)."""
    basis = []; names = []
    for i, Y in enumerate(Ys):
        for l in range(8):
            basis.append(Y & L.VAR[l]); names.append(('YX', i, l))
    for i, Y in enumerate(Ys):
        basis.append(Y); names.append(('Y', i))
    for l in range(8):
        basis.append(L.VAR[l]); names.append(('X', l))
    basis.append(L.ONES); names.append(('1',))
    U = []; C = []
    for j, o in enumerate(c.outputs):
        sol = gauss_solve(basis, T[o])
        assert sol is not None, 'output %d not in span' % j
        u = [0] * len(Ys); cst = 0; v = 0; yt = 0
        for k in sol:
            nm = names[k]
            if nm[0] == 'YX': u[nm[1]] |= 1 << nm[2]
            elif nm[0] == '1': cst = 1
            elif nm[0] == 'X': v |= 1 << nm[1]       # linear junk (complemented Y operands)
            else: yt |= 1 << nm[1]                   # Y-form terms (complemented x operands)
        U.append(u); C.append((cst, v, yt))
    return U, C


def inv4(M):
    """inverse of 4x4 GF(2) matrix given as list of 4-bit row masks, or None."""
    A = [[(M[r] >> k) & 1 for k in range(4)] + [1 if k == r else 0 for k in range(4)] for r in range(4)]
    for col in range(4):
        pr = next((r for r in range(col, 4) if A[r][col]), None)
        if pr is None: return None
        A[col], A[pr] = A[pr], A[col]
        for r in range(4):
            if r != col and A[r][col]: A[r] = [x ^ y for x, y in zip(A[r], A[col])]
    return [sum(A[r][4 + k] << k for k in range(4)) for r in range(4)]


def bases():
    out = []
    for S in itertools.combinations(range(1, 16), 4):
        if inv4(list(S)) is not None: out.append(S)
    return out


def decomp_in_basis(S, u):
    """rows beta_k = S[k] (4-bit masks over base Y's); find w_k with sum_k M_ki w_k = u_i."""
    # u_i = sum_k [bit i of S[k]] w_k  ->  w = (M^T)^-1 u ; solve per bit of the 8-bit masks
    MT = [sum(((S[k] >> i) & 1) << k for k in range(4)) for i in range(4)]   # row i: coefficients of w_k
    MTi = inv4(MT)
    w = []
    for k in range(4):
        v = 0
        for i in range(4):
            if (MTi[k] >> i) & 1: v ^= u[i]
        w.append(v)
    return w


def ylev(beta, Lb):
    k = bin(beta).count('1')
    return max(Lb[i] for i in range(4) if (beta >> i) & 1) + (0 if k == 1 else 1 if k == 2 else 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--restarts', type=int, default=200); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None); ap.add_argument('--xw', type=float, default=1.0)
    ap.add_argument('--maxP', type=int, default=99)
    a = ap.parse_args()
    c = L.load(a.circuit)
    T, lg, la, Ys, Ylev = front_info(c)
    print('base Y-forms:', len(Ys), 'levels', Ylev)
    assert len(Ys) == 4
    U, C = decompose_outputs(c, T, Ys)
    B = bases()
    # options per output: (basis, products [(beta, w)], feasible)
    opts = []
    for j in range(8):
        oj = []
        for S in B:
            w = decomp_in_basis(S, U[j])
            prods = tuple(sorted(zip(S, w)))
            levs = [ylev(b, Ylev) + 1 for b, _ in prods]
            if sum(2.0 ** (l - a.cap) for l in levs) <= 1 + 1e-9:
                oj.append(prods)
        opts.append(oj)
        print('output %d: %d feasible bases (of %d)' % (j, len(oj), len(B)))

    def cost(choice):
        prods = set(); ysum = set(); xf = set()
        for p in choice:
            for b, w in p:
                prods.add((b, w))
                if bin(b).count('1') > 1: ysum.add(b)
                if bin(w).count('1') > 1: xf.add(w)
        yc = sum(1 if bin(b).count('1') == 2 else 2 for b in ysum)
        return len(prods) + yc + a.xw * len(xf), len(prods)

    rng = random.Random(a.seed)
    best = None
    for r in range(a.restarts):
        ch = [rng.choice(o) for o in opts]
        cur = cost(ch)
        improved = True
        while improved:
            improved = False
            for j in rng.sample(range(8), 8):
                for p in opts[j]:
                    old = ch[j]; ch[j] = p
                    cc = cost(ch)
                    if cc[1] <= a.maxP and (cc < cur or (cur[1] > a.maxP)):
                        cur = cc; improved = True
                    else:
                        ch[j] = old
        if best is None or cur < best[0]:
            best = (cur, list(ch))
            print('restart %d: cost %.1f products %d' % (r, cur[0], cur[1]), flush=True)
    (cst, P), ch = best
    print('BEST cost %.1f, products %d -> bottom ANDs %d' % (cst, P, P))
    for j, p in enumerate(ch):
        print(' y%d:' % j, ' '.join('(%x,%02x)' % bw for bw in p))
    if a.out:
        json.dump({'circuit': a.circuit, 'cap': a.cap, 'Ylev': Ylev, 'C': C,
                   'choice': [[list(bw) for bw in p] for p in ch], 'cost': cst, 'P': P},
                  open(a.out, 'w'))


if __name__ == '__main__':
    main()
