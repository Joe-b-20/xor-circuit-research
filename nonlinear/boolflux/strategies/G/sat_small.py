"""Exact SAT for small nlb problems (track G): k products (any depth) over the free wires
(constant + inputs), every target of every group an affine combination of inputs, products and
the group's addends.  CHM encoding (as track C's mc_small.py) extended with addends.

usage: python3 sat_small.py PROB.prob [--solver cadical153]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'C'))
import qmc                                         # noqa: E402


def read_prob(path):
    tok = Path(path).read_text().split('\n')
    i = 0
    nw, npts = map(int, tok[i].split()); i += 1
    nf = int(tok[i]); i += 1

    def tab(line):
        ws = [int(w, 16) for w in line.split()]
        return sum(w << (64 * k) for k, w in enumerate(ws))
    free = [tab(tok[i + j]) for j in range(nf)]; i += nf
    K = int(tok[i]); i += 1 + K
    ng = int(tok[i]); i += 1
    groups = []
    for _ in range(ng):
        w, nt, na = tok[i].split(); i += 1
        nt, na = int(nt), int(na)
        T = [tab(tok[i + j]) for j in range(nt)]; i += nt
        A = [tab(tok[i + j]) for j in range(na)]; i += na
        groups.append((T, A))
    return npts, free, K, groups


def encode(npts, free, K, groups):
    f = qmc.CNF()
    zero = f.var(); f.cl.append([-zero])
    nf = len(free)                    # free[0] = constant 1
    A = [[f.vars(nf + i) for _ in range(2)] for i in range(K)]
    Cs = []
    for T, Ad in groups:
        Cs.append([(f.vars(nf + K), f.vars(len(Ad))) for _ in T])
    for p in range(npts):
        fv = [(t >> p) & 1 for t in free]
        ts = []
        for i in range(K):
            ops = []
            for s in range(2):
                co = A[i][s]
                terms = [co[j] for j in range(nf) if fv[j]] + [f.and2(co[nf + r], ts[r]) for r in range(i)]
                ops.append(f.xor_list(terms) or zero)
            ts.append(f.and2(ops[0], ops[1]))
        for (T, Ad), C in zip(groups, Cs):
            av = [(t >> p) & 1 for t in Ad]
            for t, (cp, ca) in zip(T, C):
                terms = [cp[j] for j in range(nf) if fv[j]] + [f.and2(cp[nf + r], ts[r]) for r in range(K)] \
                        + [ca[j] for j in range(len(Ad)) if av[j]]
                f.fix(f.xor_list(terms), (t >> p) & 1)
    return f


def main():
    path = sys.argv[1]
    solver = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == '--solver' else 'cadical153'
    npts, free, K, groups = read_prob(path)
    f = encode(npts, free, K, groups)
    ok, model, dt = qmc.solve(f, solver)
    out = {'prob': Path(path).name, 'K': K, 'sat': ok, 'secs': round(dt, 1), 'vars': f.n, 'clauses': len(f.cl)}
    print(json.dumps(out), flush=True)


if __name__ == '__main__':
    main()
