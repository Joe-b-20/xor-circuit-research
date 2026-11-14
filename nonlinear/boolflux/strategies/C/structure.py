"""Exact structure of an AND/XOR circuit for the AES S-box: each AND's operands as affine forms
over [1, U0..U7, a1..a_{j-1}], AND levels, and checks of the tower decomposition claims.

usage: python3 structure.py FILE [--quiet]
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))      # nonlinear/boolflux
sys.path.insert(0, str(HERE))

from core import read_ncff, NONLINEAR_OPS      # noqa: E402
import gf                                       # noqa: E402


def op_as_product(op):
    """nonlinear op -> (alpha, beta, gamma) with op(a,b) = (a^alpha)(b^beta)^gamma"""
    for al in (0, 1):
        for be in (0, 1):
            for ga in (0, 1):
                if all(((op >> ((a << 1) | b)) & 1) == (((a ^ al) & (b ^ be)) ^ ga)
                       for a in (0, 1) for b in (0, 1)):
                    return al, be, ga
    raise ValueError(op)


def analyse(path):
    c = read_ncff(path)
    n = c.n
    sym = [1 << (1 + i) for i in range(n)]          # bit0 = const, 1..8 inputs, 9.. ANDs
    tabs = list(gf.X)
    ands = []                                       # (left sym, right sym, gamma)
    alev = [0] * n
    for op, a, b in c.gates:
        if op in (6, 9):
            s = sym[a] ^ sym[b] ^ (1 if op == 9 else 0)
            t = tabs[a] ^ tabs[b] ^ (gf.ONES if op == 9 else 0)
            lv = max(alev[a], alev[b])
        elif op == 3:
            s = sym[a] ^ 1; t = tabs[a] ^ gf.ONES; lv = alev[a]
        elif op in NONLINEAR_OPS:
            al, be, ga = op_as_product(op)
            L = sym[a] ^ al; R = sym[b] ^ be
            k = len(ands)
            ta = tabs[a] ^ (gf.ONES if al else 0); tb = tabs[b] ^ (gf.ONES if be else 0)
            ands.append({'L': L, 'R': R, 'tab': ta & tb, 'Ltab': ta, 'Rtab': tb,
                         'level': 1 + max(alev[a], alev[b])})
            s = (1 << (1 + n + k)) ^ (1 if ga else 0)
            t = (ta & tb) ^ (gf.ONES if ga else 0)
            lv = 1 + max(alev[a], alev[b])
        else:
            raise ValueError(op)
        sym.append(s); tabs.append(t); alev.append(lv)
    outs = [sym[o] for o in c.outputs]
    return c, ands, outs, tabs


def fmt(s, n=8):
    parts = []
    if s & 1: parts.append('1')
    for i in range(n):
        if (s >> (1 + i)) & 1: parts.append('U%d' % i)
    k = 0; s >>= 1 + n
    while s:
        if s & 1: parts.append('a%d' % (k + 1))
        s >>= 1; k += 1
    return '+'.join(parts) or '0'


def main():
    path = sys.argv[1]
    c, ands, outs, tabs = analyse(path)
    print(path)
    levels = {}
    for k, A in enumerate(ands):
        levels.setdefault(A['level'], []).append(k + 1)
    print('ANDs per level:', {l: len(v) for l, v in sorted(levels.items())})
    for k, A in enumerate(ands):
        print('a%-2d L%d  (%s) * (%s)' % (k + 1, A['level'], fmt(A['L']), fmt(A['R'])))
    for j, o in enumerate(outs):
        print('S%d = %s' % (j, fmt(o)))

    # ---- tower checks
    N = [gf.power(p, 17) for p in range(256)]
    Ninv = [gf.INV[v] for v in N]
    U = [N[p] ^ Ninv[p] for p in range(256)]
    b16 = [1, 0, 0, 0]
    # basis of GF(16) subfield: pick 4 independent elements
    sp = gf.Span(); basis = []
    for v in gf.SUB16:
        if v and sp.add(v): basis.append(v)
    Nt = gf.coord_tables(N, basis); Nit = gf.coord_tables(Ninv, basis); Ut = gf.coord_tables(U, basis)
    aff = gf.affine_x()
    lvl1 = [A['tab'] for A in ands if A['level'] == 1]
    S1 = gf.Span(aff + lvl1)
    print('level-1 ANDs:', len(lvl1), ' N bits in span(1,x,level1):', [S1.contains(t) for t in Nt])
    # x^33 quadratic part
    X33 = gf.coord_tables([gf.power(p, 33) for p in range(256)])
    print('x^33 bits in span(1,x,level1):', [S1.contains(t) for t in X33])
    # minimal subset of level-1 ANDs needed for N
    import itertools
    for r in range(4, len(lvl1) + 1):
        ok = None
        for sub in itertools.combinations(range(len(lvl1)), r):
            S = gf.Span(aff + [lvl1[i] for i in sub])
            if all(S.contains(t) for t in Nt): ok = sub; break
        if ok is not None:
            print('smallest level-1 subset spanning N: size', r, [i + 1 for i in ok]); break
    # stage 2 inputs / outputs: which ANDs are functions of N only
    spN = gf.Span([gf.ONES] + Nt)
    stage = {}
    for k, A in enumerate(ands):
        fN = lambda t: all(  # function of N?
            True for _ in [0])
    # function-of-N test: table constant on fibres of N
    def is_fun_of(t, key):
        seen = {}
        for p in range(256):
            v = (t >> p) & 1; kk = key[p]
            if seen.setdefault(kk, v) != v: return False
        return True
    for k, A in enumerate(ands):
        tags = []
        if is_fun_of(A['tab'], N): tags.append('fun(N)')
        if is_fun_of(A['Ltab'], N) and is_fun_of(A['Rtab'], N): tags.append('operands fun(N)')
        if spN.contains(A['Ltab']) and spN.contains(A['Rtab']): tags.append('operands aff(N)')
        A['tags'] = tags
    print('ANDs whose operands are functions of N:',
          [k + 1 for k, A in enumerate(ands) if 'operands fun(N)' in A['tags']])
    spU = gf.Span(aff + Ut)
    spNi = gf.Span(aff + Nit)
    spUN = gf.Span(aff + Ut + Nt)
    for k, A in enumerate(ands):
        if A['level'] >= max(levels) :
            print('a%d operands in aff(x,u): %s %s | aff(x,N^-1): %s %s | aff(x,u,N): %s %s' % (
                k + 1, spU.contains(A['Ltab']), spU.contains(A['Rtab']),
                spNi.contains(A['Ltab']), spNi.contains(A['Rtab']),
                spUN.contains(A['Ltab']), spUN.contains(A['Rtab'])))
    # outputs: decompose S = sum last-stage ANDs + ?
    last = [k for k, A in enumerate(ands) if A['level'] == max(levels)]
    print('last-level ANDs:', len(last))


if __name__ == '__main__':
    main()
