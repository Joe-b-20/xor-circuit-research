"""Independent check of the one-sheet local lemma by SAT (python-sat).

usage: python3 local_lemma.py K

Base signals (free): the 8 unit vectors of blocks a and b, and the 11 vectors of weight >= 2 supported
on block a. Question: do K gates suffice to compute the four vectors  E_c on block b + s_c on block a,
c = 0..3 ?  The lemma says: K = 9 is impossible, K = 10 is possible.
Encoding written independently of rotation/scheme_sat.py: one-hot operand pair per gate, mask bits,
operands ordered, gate values nonzero. A small bounded computation about an 8-input map.
"""
import sys
from itertools import combinations

from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

N = 8  # bits 0..3 = block a, bits 4..7 = block b


def targets():
    out = []
    for c in range(4):
        E = 0xF ^ (1 << c)
        s = (1 << c) | (1 << ((c + 1) % 4))
        out.append((E << 4) | s)
    return out


def solve(K):
    base = [1 << i for i in range(8)] + [v for v in range(1, 16) if bin(v).count("1") >= 2]
    nb = len(base)
    cnf, top = [], [0]

    def new():
        top[0] += 1
        return top[0]

    V = nb + K
    m = [[new() for _ in range(N)] for _ in range(V)]
    for i, v in enumerate(base):
        for b in range(N):
            cnf.append([m[i][b] if (v >> b) & 1 else -m[i][b]])
    sel = {}
    for g in range(nb, V):
        lits = []
        for (i, j) in combinations(range(g), 2):
            if j < nb and i >= 8 and j >= 8:
                continue  # two free vectors of block a: the sum is free already
            s = new()
            sel[(g, i, j)] = s
            lits.append(s)
            for b in range(N):
                x, y, o = m[i][b], m[j][b], m[g][b]
                cnf += [[-s, -x, -y, -o], [-s, x, y, -o], [-s, x, -y, o], [-s, -x, y, o]]
        enc = CardEnc.equals(lits=lits, bound=1, top_id=top[0], encoding=EncType.seqcounter)
        top[0] = max(top[0], enc.nv)
        cnf += enc.clauses
        # a useful gate is nonzero on block b (otherwise its value is free or zero)
        cnf.append([m[g][b] for b in range(4, 8)])
    for r in targets():
        lits = []
        for g in range(nb, V):
            o = new()
            lits.append(o)
            for b in range(N):
                cnf.append([-o, m[g][b] if (r >> b) & 1 else -m[g][b]])
        cnf.append(lits)
    with Cadical153(bootstrap_with=cnf) as s:
        return s.solve()


if __name__ == "__main__":
    K = int(sys.argv[1])
    print(f"K = {K}:", "possible (SAT)" if solve(K) else "impossible (UNSAT)")
