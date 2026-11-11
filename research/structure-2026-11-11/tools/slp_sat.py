"""Exact XOR-circuit size for a SMALL matrix by SAT (python-sat / cadical).

Usage: python3 slp_sat.py NAME K        decide whether map NAME has a circuit with K gates
Maps (inputs listed in the code):
  sheet   the isolated two-term sheet: 8 inputs a_0..a_3 (previous block), b_0..b_3 (own block);
          4 outputs o_c = b_(c+1) + b_(c+2) + b_(c+3) + a_c + a_(c+1)
  sheet3  the isolated three-term sheet: 12 inputs a, z (two previous blocks), b;
          o_c = E_c(b) + s_c(a) + s_c(z)
A small bounded computation used to examine a simple example; it is not part of any proof for
the 32-bit map. Run under a memory limit.
"""
import sys
from itertools import combinations

from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153


def maps(name):
    if name == "sheet":
        n = 8
        a = lambda c: 1 << (c % 4)
        b = lambda c: 1 << (4 + c % 4)
        rows = [b(c + 1) ^ b(c + 2) ^ b(c + 3) ^ a(c) ^ a(c + 1) for c in range(4)]
        return n, rows
    if name == "sheet3":
        n = 12
        a = lambda c: 1 << (c % 4)
        z = lambda c: 1 << (4 + c % 4)
        b = lambda c: 1 << (8 + c % 4)
        rows = [b(c + 1) ^ b(c + 2) ^ b(c + 3) ^ a(c) ^ a(c + 1) ^ z(c) ^ z(c + 1) for c in range(4)]
        return n, rows
    raise SystemExit("unknown map")


def solve(n, rows, K):
    cnf = []
    top = [0]

    def new():
        top[0] += 1
        return top[0]

    V = n + K
    m = [[new() for _ in range(n)] for _ in range(V)]
    for i in range(n):
        for b in range(n):
            cnf.append([m[i][b] if i == b else -m[i][b]])
    sel = {}
    for g in range(n, V):
        pairs = list(combinations(range(g), 2))
        lits = []
        for (i, j) in pairs:
            s = new()
            sel[(g, i, j)] = s
            lits.append(s)
            for b in range(n):
                x, y, o = m[i][b], m[j][b], m[g][b]
                cnf += [[-s, -x, -y, -o], [-s, x, y, -o], [-s, x, -y, o], [-s, -x, y, o]]
        enc = CardEnc.equals(lits=lits, bound=1, top_id=top[0], encoding=EncType.seqcounter)
        top[0] = max(top[0], enc.nv)
        cnf += enc.clauses
        # nonzero value
        cnf.append([m[g][b] for b in range(n)])
    for r in rows:
        lits = []
        for g in range(n, V):
            o = new()
            lits.append(o)
            for b in range(n):
                cnf.append([-o, m[g][b] if (r >> b) & 1 else -m[g][b]])
        cnf.append(lits)
    with Cadical153(bootstrap_with=cnf) as s:
        ok = s.solve()
        if not ok:
            return None
        model = set(l for l in s.get_model() if l > 0)
    gates = []
    for g in range(n, V):
        for (gg, i, j), s_ in sel.items():
            if gg == g and s_ in model:
                gates.append((i, j))
    return gates


if __name__ == "__main__":
    name, K = sys.argv[1], int(sys.argv[2])
    n, rows = maps(name)
    res = solve(n, rows, K)
    if res is None:
        print(f"{name}: no circuit with {K} gates (UNSAT)")
    else:
        print(f"{name}: circuit with {K} gates found")
        vals = [1 << i for i in range(n)]
        for k, (i, j) in enumerate(res):
            vals.append(vals[i] ^ vals[j])
            print(f"  g{n + k} = s{i} + s{j} = {vals[-1]:0{n}b}")
        print("  outputs ok:", all(r in vals[n:] for r in rows))
