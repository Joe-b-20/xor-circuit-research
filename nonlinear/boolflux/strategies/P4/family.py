"""P4: the 'scaled-Frobenius' family of the 103: same GF(2^4) inversion block, input y = lambda * x^(2^k).

S(x) = A x^-1 + c.  With y = L x, L(x) = lambda x^(2^k) (GF(2)-linear), x^-1 = N y^-1 with
N(z) = (lambda z)^(2^(8-k)).  The 103 computes A z^-1 + c from z through top forms, 9 level-1
ANDs, pre-inversion, inversion block, 18 output ANDs and the bottom M.  Feeding y instead of x:
  top forms     g  ->  g o L        (functionals on x)
  pre x-parts   X  ->  X o L        (product parts P unchanged, rank X unchanged = 4)
  inversion     unchanged (13 XOR)
  bottom        M  ->  T M,  T = A N A^-1 (8 x 8 on the outputs)
For each (lambda, k) this computes, exactly: number of non-trivial forms, the bottom XOR count
(transposition + closure, minh_c), and (optionally) the top minimum (topenum_c, no deadline) and the
rank of Avail meet V (14-gate pre needs 4).

    python3 family.py CIRC OUT.jsonl [--top]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import bottomvar
import circ
import pairscan
import preinj

HERE = Path(__file__).resolve().parent


def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
    return r


def gpow(a, e):
    r = 1
    while e:
        if e & 1:
            r = gmul(r, a)
        a = gmul(a, a)
        e >>= 1
    return r


def ginv(a):
    return gpow(a, 254)


# NIST bit order: x_i = bit (7 - i) of the byte.  Represent a GF(2)-linear map F on bytes as the
# 8x8 matrix over NIST indices: Mt[i] = mask over j of input x_j contributing to output bit i.
def lin_matrix(F):
    cols = []
    for j in range(8):
        byte = 1 << (7 - j)
        cols.append(F(byte))
    # out bit i (NIST) of F(e_j)
    rows = []
    for i in range(8):
        m = 0
        for j in range(8):
            if (cols[j] >> (7 - i)) & 1:
                m |= 1 << j
        rows.append(m)
    return rows


def apply_rows(rows, vec):
    """vec: mask over NIST indices; returns rows * vec."""
    out = 0
    for i, r in enumerate(rows):
        if bin(r & vec).count('1') & 1:
            out |= 1 << i
    return out


def transpose(rows):
    t = [0] * 8
    for i, r in enumerate(rows):
        for j in range(8):
            if (r >> j) & 1:
                t[j] |= 1 << i
    return t


def aes_affine(b):
    v = 0
    for i in range(8):
        bit = ((b >> i) ^ (b >> ((i + 4) % 8)) ^ (b >> ((i + 5) % 8)) ^ (b >> ((i + 6) % 8)) ^ (b >> ((i + 7) % 8))) & 1
        v |= bit << i
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('out')
    ap.add_argument('--top', action='store_true')
    ap.add_argument('--hmax', type=int, default=3)
    a = ap.parse_args()
    gates, s, lvl1, pairs, X, P = pairscan.setup(a.circ)
    _, col = bottomvar.bottom_columns(a.circ)
    cols0 = [col[(i, sd)] for i in range(9) for sd in (0, 1)]
    forms0 = [f for pr in pairs for f in pr]
    Arows = lin_matrix(aes_affine)
    # inverse of A as a byte map
    Ainv_tab = {aes_affine(b): b for b in range(256)}
    Ainv = lambda b: Ainv_tab[b]
    out = open(a.out, 'w')
    recs = []
    for k in range(8):
        for lam in range(1, 256):
            L = lambda x, lam=lam, k=k: gmul(lam, gpow(x, 1 << k)) if x else 0
            # x^(2^k) is linear; check linearity cheaply on basis is implied
            Lrows = lin_matrix(L)
            LT = transpose(Lrows)
            Nf = lambda z, lam=lam, k=k: gpow(gmul(lam, z), 1 << ((8 - k) % 8)) if z else 0
            T = lambda b: aes_affine(Nf(Ainv(b)))     # A N A^-1 on output bytes
            Trows = lin_matrix(T)
            forms = [apply_rows(LT, g) for g in forms0]
            nontriv = {f for f in forms if bin(f).count('1') > 1}
            Xn = [apply_rows(LT, v) for v in X]
            # bottom columns: vectors over outputs y0..y7 (NIST index = bit j of col)
            colsn = [apply_rows(Trows, c) for c in cols0]
            nt = sorted({c for c in colsn if c & (c - 1)})
            V = {0}
            for v in Xn:
                if v not in V:
                    V |= {u ^ v for u in V}
            cover_forms = preinj.rank([f for f in nontriv | {1 << i for i in range(8)} if f in V])
            recs.append(dict(lam=lam, k=k, nforms=len(nontriv), forms=sorted(nontriv), X=Xn, nt=nt,
                             cover_forms=cover_forms))
    # bottom exact in one batch
    lines = [str(2)] + [' '.join(map(str, [len(r['nt'])] + r['nt'])) for r in recs]
    rr = subprocess.run([str(HERE / 'minh_c')], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    hs = [int(x) for x in rr.stdout.split()]
    for r, h in zip(recs, hs):
        r['bottomH'] = h
        r['bottom'] = len(r['nt']) + h + 10 if h <= 2 else None
        out.write(json.dumps({k2: v for k2, v in r.items() if k2 not in ('forms',)}) + '\n')
    out.close()
    from collections import Counter
    cnt = Counter((r['nforms'], r['bottom']) for r in recs)
    print(json.dumps({str(k2): v for k2, v in sorted(cnt.items(), key=lambda t: (t[0][0], t[0][1] or 99))}))
    ident = [r for r in recs if r['lam'] == 1 and r['k'] == 0][0]
    print('identity', {k2: ident[k2] for k2 in ('nforms', 'bottom', 'cover_forms')})


if __name__ == '__main__':
    main()
