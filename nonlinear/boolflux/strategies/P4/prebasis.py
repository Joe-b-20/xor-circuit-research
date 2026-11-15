"""P4: other input bases for the GF(16) inversion block.

The inversion reads t30..t33 (T).  Any invertible M in GL(4,2) gives another 4-tuple T' = M T of
inversion inputs (an inversion circuit for T' exists; its cost is a separate question).  For each M:
  X' = M X (x-parts), P' = M P (product parts);
  k=4 good sets of X' over Avail (the reference's top values) -> pre could need only 4 injections;
  then the product-part minimum for P' (SAT, <= 10 steps) decides whether pre' <= 14.
Output: the bases M with a 4-injection good set, and then their product-part minimum.

    python3 prebasis.py CIRC
"""
import itertools
import json
import sys

import circ
import linslp2
import topjoint


def matmul(M, V):
    return [sum_x(V[c] for c in range(4) if (M[r] >> c) & 1) for r in range(4)]


def sum_x(it):
    r = 0
    for v in it:
        r ^= v
    return r


def main():
    path = sys.argv[1]
    gates = circ.read(path)
    s = circ.symbolic(gates)
    xs = [f'x{i}' for i in range(8)]
    names = ['t30', 't31', 't32', 't33']
    prod = [f'a{i}' for i in range(1, 10)]
    xm = lambda atoms: sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')
    am = lambda atoms: sum(1 << prod.index(t) for t in atoms if t[0] != 'x')
    X = [xm(s[n][0]) for n in names]
    P = [am(s[n][0]) for n in names]
    avail = {xm(s[o][0]) for op, o, ins in gates if op != 'AND' and s[o][0] <= set(xs)} | {1 << i for i in range(8)}
    rows = list(range(1, 16))
    seen = set()
    cands = []
    for M in itertools.permutations(rows, 4):
        # invertible?
        if topjoint.preinj.rank(list(M)) < 4:
            continue
        key = frozenset(M)     # the set of rows matters, not the order (targets are unordered)
        if key in seen:
            continue
        seen.add(key)
        Xp = matmul(M, X)
        Pp = matmul(M, P)
        g = topjoint.good_sets(Xp, avail)
        if g:
            cands.append((M, Xp, Pp, len(g)))
    print(json.dumps(dict(bases=len(seen), with_good_k4=len(cands))), flush=True)
    base = [1 << i for i in range(9)]
    for M, Xp, Pp, ng in cands:
        res = {}
        for k in (9, 10):
            st, ch, el = linslp2.slp(9, base, [p for p in Pp if p], k, budget=2_000_000)
            res[k] = st
            if st == 'sat':
                break
        print(json.dumps(dict(M=list(M), P=[bin(p) for p in Pp], good=ng, amin=res)), flush=True)


if __name__ == '__main__':
    main()
