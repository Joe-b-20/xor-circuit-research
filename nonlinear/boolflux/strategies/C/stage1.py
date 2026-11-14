"""Stage-1 bound: least k such that k products of linear forms in x (8 bits) span, modulo
affine functions, the 4 coordinate functions of N = x^17 (equivalently: the quadratic
complexity of the norm map, which equals that of GF(16) multiplication up to linear terms).

Exact SAT model over alternating forms (28 coordinates).  Symmetry breaking (all sound):
  * c = [I_4 | C'] (GL(4) on the target basis and column permutation),
  * products 1..4 lex-ordered and products 5..k lex-ordered by first operand,
  * optional: product 1 fixed to a representative of each orbit of the group
    x -> a x^(2^i) (a in GF(256)*), which maps the coordinate space of N to itself.

usage: python3 stage1.py K [--orbits]
"""
from __future__ import annotations

import itertools
import json
import sys
import time

import gf
import qmc

PAIRS = list(itertools.combinations(range(8), 2))


def lin_form_of_elem(alpha):
    """linear form x -> Tr(alpha x) as 8-bit coefficient vector over wires U0..U7"""
    tr = [0] * 256
    for p in range(256):
        v = gf.mul(alpha, p); t = 0
        for i in range(8):
            t ^= gf.power(v, 1 << i)
        tr[p] = t & 1
    # coefficient of U_i = Tr(alpha * e) with e = byte having bit 7-i
    return [tr[1 << (7 - i)] for i in range(8)]


def wedge(l, m):
    w = 0
    for n, (a, b) in enumerate(PAIRS):
        if (l[a] & m[b]) ^ (l[b] & m[a]): w |= 1 << n
    return w


def subspace_key(l, m):
    vs = sorted(int(''.join(map(str, v)), 2) for v in (l, m, [x ^ y for x, y in zip(l, m)]))
    return tuple(vs)


def orbit_reps():
    """representatives of 2-dim subspaces of linear forms under x -> a x^(2^i)."""
    forms = {}
    for alpha in range(1, 256):
        forms[alpha] = lin_form_of_elem(alpha)
    # form of Tr(alpha x) under x -> a x^(2^i): Tr(alpha a x^(2^i)) = Tr((alpha a)^(2^-i) x)
    seen = set(); reps = []
    for b in range(2, 256):
        key = frozenset([1, b, 1 ^ b])
        if key in seen: continue
        orb = set()
        for a in range(1, 256):
            for i in range(8):
                e = [gf.power(gf.mul(z, a), 1 << ((8 - i) % 8)) for z in (1, b, 1 ^ b)]
                orb.add(frozenset(e))
        reps.append((b, len(orb)))
        # mark only those of the form {1, b', 1+b'}
        for s in orb:
            if 1 in s: seen.add(s)
    return [(forms[1], forms[b], sz) for b, sz in reps]


def encode(k, R1=None):
    N = [gf.power(p, 17) for p in range(256)]
    sp = gf.Span(); basis = []
    for v in gf.SUB16:
        if v and sp.add(v): basis.append(v)
    Nt = gf.coord_tables(N, basis)
    targets = [gf.anf_quadratic_part(t) for t in Nt]
    f = qmc.CNF()
    L = [f.vars(8) for _ in range(k)]; M = [f.vars(8) for _ in range(k)]
    C = [[f.var() for _ in range(k)] for _ in range(4)]
    W = []
    for j in range(k):
        W.append([f.xor2(f.and2(L[j][a], M[j][b]), f.and2(L[j][b], M[j][a])) for a, b in PAIRS])
    for s in range(4):
        for r in range(28):
            zs = [f.and2(C[s][j], W[j][r]) for j in range(k)]
            f.fix(f.xor_list(zs), (targets[s] >> r) & 1)
    for j in range(k):          # nondegenerate products
        f.cl.append([W[j][r] for r in range(28)])
    if R1 is None:
        for j in range(k - 1):   # c free (fixing c=[I|C'] for a FIXED target basis is unsound)
            qmc.lex_le(f, L[j], L[j + 1])
    else:
        # product 0 fixed to an orbit representative of the stabiliser x -> a x^(2^i) of V_N
        # (sound: map any solution so that one of its products becomes the representative;
        # the target basis changes inside V_N and c is free); lex among the others.
        la, lb = R1
        for b in range(8): f.fix(L[0][b], la[b]); f.fix(M[0][b], lb[b])
        for j in range(1, k - 1):
            qmc.lex_le(f, L[j], L[j + 1])
    return f


def main():
    k = int(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == '--reps':
        reps = orbit_reps()
        print(json.dumps({'k': k, 'orbits': len(reps), 'sizes': [r[2] for r in reps]}), flush=True)
        allok = False
        for i, (la, lb, sz) in enumerate(reps):
            f = encode(k, (la, lb))
            ok, model, dt = qmc.solve(f, 'cadical153')
            print(json.dumps({'k': k, 'rep': i, 'orbit': sz, 'sat': ok, 'secs': round(dt, 1)}), flush=True)
            allok = allok or ok
            if ok: break
        print(json.dumps({'k': k, 'result': 'SAT' if allok else 'UNSAT (all orbits)'}), flush=True)
        return
    f = encode(k)
    t0 = time.time()
    ok, model, dt = qmc.solve(f, sys.argv[2] if len(sys.argv) > 2 else 'cadical153')
    print(json.dumps({'k': k, 'sat': ok, 'secs': round(dt, 1), 'vars': f.n, 'clauses': len(f.cl)}))


if __name__ == '__main__':
    main()
