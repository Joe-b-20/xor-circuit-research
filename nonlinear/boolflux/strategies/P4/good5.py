"""P4: for each feasible 17-gate top (forms + 2 helpers, no deadline), does ANY k-injection
pattern (any multiset of k reach vectors, i.e. ignoring which product-part circuit provides them)
realise the pre-inversion x-parts X with injected values in Avail = inputs + forms + helpers?
If not, every pre-inversion over that top needs >= amin + k + 1 = 11 + k gates. [C, that case]

    python3 good5.py CIRC K
"""
import itertools
import json
import sys

import build
import circ
import preinj
import reinject
import topenum


def any_solution(X, avail, k, ntg=4):
    rv = list(range(1, 1 << ntg))
    av = sorted(avail)
    n = 0
    for B in itertools.combinations_with_replacement(rv, k):
        if preinj.rank(list(B)) < preinj.rank(X):
            continue
        basis = []
        for i in range(k):
            if preinj.rank([B[j] for j in basis] + [B[i]]) > len(basis):
                basis.append(i)
        free = [i for i in range(k) if i not in basis]
        for fv in itertools.product(av, repeat=len(free)):
            Xr = list(X)
            for i, v in zip(free, fv):
                for j in range(ntg):
                    if (B[i] >> j) & 1:
                        Xr[j] ^= v
            Sb = preinj.solve_basis([B[i] for i in basis], Xr, ntg)
            if Sb is None:
                continue
            if all(v in avail for v in Sb):
                return (B, list(fv), Sb)
    return None


def main():
    path, k = sys.argv[1], int(sys.argv[2])
    ref = circ.read(path)
    s = circ.symbolic(ref)
    xs = {f'x{i}' for i in range(8)}
    xm = lambda atoms: sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')
    forms = {xm(s[i][0]) for op, o, ins in ref if op == 'AND' for i in ins if s[i][0] <= xs and len(s[i][0]) > 1}
    X = [xm(s[t][0]) for t in ['t30', 't31', 't32', 't33']]
    allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in forms]
    for hs in itertools.combinations(allv, 2):
        S = forms | set(hs)
        lv = topenum.closure_levels(S)
        if not all(t in lv for t in S):
            continue
        avail = S | {1 << i for i in range(8)}
        r = any_solution(X, avail, k)
        print(json.dumps(dict(helpers=[build.nm(h) for h in hs], k=k, solution=r)), flush=True)


if __name__ == '__main__':
    main()
