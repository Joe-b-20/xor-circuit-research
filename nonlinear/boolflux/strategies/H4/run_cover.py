"""usage: run_cover.py NAME K   -> one JSON line (level-1 quadratic complexity test)
NAME: pow3 pow5 pow9 pow17 (coordinates of x^d, d quadratic), nkq (N_{K/Q} on GF(16), 4 vars),
      qscal (P * m, P in F = GF(4)^4, m in GF(4): 10 vars, 8 bilinear targets),
      kscal (x^16 * n: x in F, n in K: 12 vars, 8 bilinear targets),
      pow5q (x^5 projected to one K-line?) ..."""
import json
import sys

import cover1
import blocks
from h4lib import pw, mul, K, Q, F


def targets_pow(d):
    ts = []
    for k in range(8):
        tt = 0
        for p in range(256):
            if (pw(p, d) >> k) & 1 if p else 0: tt |= 1 << p
        ts.append(cover1.form_from_anf(8, cover1.anf_quadratic_part(tt, 8)))
    return 8, ts


def targets_bilinear(fin_a, fin_b, func):
    """func(a, b) -> F element; a over GF(2)-basis of fin_a, b over basis of fin_b"""
    Ba, Bb = blocks.gf2_basis(fin_a), blocks.gf2_basis(fin_b)
    na, nb = len(Ba), len(Bb)
    d = na + nb
    ts = []
    for k in range(8):
        mons = []
        for i in range(na):
            for j in range(nb):
                if (func(Ba[i], Bb[j]) >> k) & 1: mons.append((i, na + j))
        ts.append(cover1.form_from_anf(d, mons))
    return d, ts


def targets_padj(name):
    """formal variables x (8, standard bits), N (4, GF(2)-basis of K).  Targets: coordinates
    of P^16 = x * N^4 (bilinear; P's coordinates are a linear image of these).  Free space E:
    C = {Tr(b x N)} (bilinear forms whose functions are x-quadratic: x N = x^18), all
    x-quadratic forms (absorbed by level-1 junk) and, unless 'strict', all N-quadratic forms.
    padj_n4: N4 = N^5 targets added (and N-quadratics not free)."""
    Bk = blocks.gf2_basis(K)
    d = 12
    def bil(func):
        out = []
        for k in range(8):
            mons = [(i, 8 + j) for i in range(8) for j in range(4) if (func(1 << i, Bk[j]) >> k) & 1]
            out.append(cover1.form_from_anf(d, mons))
        return out
    ts = bil(lambda a, n: mul(a, pw(n, 4)))
    E = bil(lambda a, n: mul(a, n))
    E += [cover1.form_from_anf(d, [(a, b)]) for a in range(8) for b in range(a + 1, 8)]
    if name == 'padj':
        E += [cover1.form_from_anf(d, [(8 + a, 8 + b)]) for a in range(4) for b in range(a + 1, 4)]
    if name == 'padj_n4':
        cm = blocks.coord_map(Bk); cq = blocks.coord_map(blocks.gf2_basis(Q))
        for o in range(2):
            tt = 0
            for a, c in cm.items():
                if (cq[pw(a, 5)] >> o) & 1: tt |= 1 << c
            mons = cover1.anf_quadratic_part(tt, 4)
            ts.append(cover1.form_from_anf(d, [(8 + a, 8 + b) for a, b in mons]))
    return d, ts, E


def targets_nkq():
    Bk = blocks.gf2_basis(K); cm = blocks.coord_map(blocks.gf2_basis(Q))
    cmk = blocks.coord_map(Bk)
    ts = []
    for o in range(2):
        tt = 0
        for a, c in cmk.items():
            if (cm[pw(a, 5)] >> o) & 1: tt |= 1 << c
        ts.append(cover1.form_from_anf(4, cover1.anf_quadratic_part(tt, 4)))
    return 4, ts


def main():
    name, k = sys.argv[1], int(sys.argv[2])
    if name.startswith('pow'):
        d, ts = targets_pow(int(name[3:]))
    elif name == 'nkq':
        d, ts = targets_nkq()
    elif name == 'qscal':
        d, ts = targets_bilinear(F, Q, mul)
    elif name == 'kscal':
        d, ts = targets_bilinear(F, K, mul)
    elif name == 'kmul':
        d, ts = targets_bilinear(K, K, mul)
    elif name in ('qscal_n9', 'qscal_d4'):
        d, ts = targets_bilinear(F, Q, mul)
        # free P*P junk: quadratic forms Tr(c P^17) (= functions of N, class 153) and, for d4,
        # Tr(c P^5) (class 165); P = the 8 formal variables (standard bits of P)
        E = []
        exps = [17] if name == 'qscal_n9' else [17, 5]
        for e in exps:
            for c in range(1, 256):
                tt = 0
                for P in range(256):
                    v = pw(P, e) if P else 0
                    tr = 0; y = mul(c, v)
                    for _ in range(8): tr ^= y; y = mul(y, y)
                    if tr & 1: tt |= 1 << P
                E.append(cover1.form_from_anf(d, cover1.anf_quadratic_part(tt, 8)))
        E = list(cover1.rowspace(E).values())
    elif name in ('padj', 'padj_n4', 'padj_strict'):
        d, ts, E = targets_padj(name)
    else:
        raise SystemExit('?')
    if not (name.startswith('padj') or name.startswith('qscal_')): E = []
    dim = len(cover1.rowspace(ts))
    prods, dt = cover1.solve(d, [t for t in ts if t], k, E=E)
    ok = cover1.check(d, ts, prods, E=E) if prods else None
    print(json.dumps({'name': name, 'k': k, 'd': d, 'target_dim': dim, 'sat': prods is not None,
                      'check': ok, 'secs': round(dt, 2), 'prods': prods}), flush=True)


if __name__ == '__main__':
    main()
