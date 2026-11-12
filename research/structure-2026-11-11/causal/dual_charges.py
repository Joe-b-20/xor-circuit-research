"""Order-free (dual) charges and joint charges of recorded circuits.  Examines existing circuits only.

usage: python3 dual_charges.py q M FILE        rotation model Q_M, text format of rotation/qm.py
       python3 dual_charges.py mc FILE         MixColumns, NCFF text (.circ.txt)

For a circuit with gate triples T (gate t = {result, operand, operand}) and outputs o:
   u_t(o) = parity of the number of wire paths from the result of t to the carrier of o
          = the unique solution of the star equations (transposed system).  It is defined for every
            based cyclic system; for a circuit, u_t(o) = 1 implies "result of t is an ancestor-or-equal of o".
A triple is LIVE on a set of blocks X if at least two of its three members are nonzero somewhere on X.
   dual charge set of a family J of sheets:  Lam(J) = { t : u_t nonzero on the outputs of J, t live on blocks(J) }
   wire charge set:                           D(J)  = { g : g ancestor-or-equal of an output of J, g nonzero on blocks(J) }
Claims checked here (report sections 3 and 4): |Lam(J)| >= 10|J| and |D(J)| >= 10|J| for every family J of
sheets no two of which are "adjacent" (j' in support(sheet j) or j in support(sheet j')).
The script lists all maximal such families (a fixed small graph, 3..8 vertices) and the counts.
"""
import os
import pathlib
import re
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402

GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


def load_q(m, path):
    n, gates = qm.read_circuit(path)
    targets = qm.rows(m)          # index 4j + c
    blk = lambda v: frozenset(j for j in range(m) if (v >> (4 * j)) & 15)
    sheet_of_target = [i // 4 for i in range(4 * m)]
    return n, gates, targets, blk, sheet_of_target, m


def load_mc(path):
    names, gates = {}, []
    n = 0
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        mm = RANGE.match(line)
        if mm and mm.group(1) == "Inputs":
            base = int(mm.group(3))
            n = int(mm.group(4)) - base + 1
            for j in range(n):
                names[f"x{j + base}"] = j
            continue
        mm = GATE.match(line)
        if mm:
            _, out, a, b = mm.groups()
            names[out] = n + len(gates)
            gates.append((names[a], names[b]))
    assert n == 32
    # input (c, j) = bit j of byte c = index 8c + j ; formula (3.1) of RECORD
    def bit(c, j):
        return 1 << (8 * (c % 4) + j)

    def Ev(c, j):
        return bit(c + 1, j) | bit(c + 2, j) | bit(c + 3, j)

    def sv(c, j):
        return bit(c, j) | bit(c + 1, j)

    targets, sheet_of_target = [], []
    for j in range(8):
        for c in range(4):
            v = Ev(c, j) ^ sv(c, (j - 1) % 8)
            if j in (1, 3, 4):
                v ^= sv(c, 7)
            targets.append(v)
            sheet_of_target.append(j)
    blk = lambda v: frozenset(j for j in range(8) if any((v >> (8 * c + j)) & 1 for c in range(4)))
    return n, gates, targets, blk, sheet_of_target, 8


def analyse(n, gates, targets, blk, sheet_of_target, m, label):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    G = len(gates)
    first = {}
    for i in range(n, n + G):
        first.setdefault(vals[i], i)
    assert all(t in first for t in targets), "circuit does not compute the targets"
    distinct = len(set(vals)) == len(vals)
    carrier = [first[t] for t in targets]
    sup = [blk(v) for v in vals]
    ssup = [None] * m
    for i, t in enumerate(targets):
        ssup[sheet_of_target[i]] = blk(t)
    # dual solution: u[g] = bitmask over targets
    readers = [[] for _ in range(n + G)]
    for gi, (a, b) in enumerate(gates):
        readers[a].append(n + gi)
        readers[b].append(n + gi)
    u = [0] * (n + G)
    for s in range(n + G - 1, -1, -1):
        x = 0
        for r in readers[s]:
            x ^= u[r]
        u[s] = x
        for ti, cg in enumerate(carrier):
            if cg == s:
                u[s] ^= 1 << ti
    # check: adjoint of input i = column i of the matrix
    for i in range(n):
        col = sum(1 << ti for ti, t in enumerate(targets) if (t >> i) & 1)
        assert u[i] == col, "dual solution check failed"
    # ancestors
    anc = [set() for _ in range(m)]
    for ti, cg in enumerate(carrier):
        stack, seen = [cg], set()
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[sheet_of_target[ti]] |= seen
    sheet_mask = [0] * m
    for ti in range(len(targets)):
        sheet_mask[sheet_of_target[ti]] |= 1 << ti

    def lam(J):
        blocks = set(J)
        mask = 0
        for j in J:
            mask |= sheet_mask[j]
        out = set()
        for gi, (a, b) in enumerate(gates):
            g = n + gi
            if not (u[g] & mask):
                continue
            live = sum(1 for s in (g, a, b) if sup[s] & blocks)
            if live >= 2:
                out.add(g)
        return out

    def dset(J):
        blocks = set(J)
        out = set()
        for j in J:
            for g in anc[j]:
                if sup[g] & blocks:
                    out.add(g)
        return out

    adj = [[False] * m for _ in range(m)]
    for j in range(m):
        for k in range(m):
            if j != k and (k in ssup[j] or j in ssup[k]):
                adj[j][k] = True
    print(f"{label}: G = {G}, values distinct: {distinct}")
    print("  sheet supports:", [sorted(x) for x in ssup])
    lam1 = [len(lam([j])) for j in range(m)]
    d1 = [len(dset([j])) for j in range(m)]
    print(f"  dual charges |Lam(j)|: {lam1}  sum {sum(lam1)}")
    print(f"  wire charges |D(j)|:   {d1}  sum {sum(d1)}")
    mustar = [0] * (n + G)
    for j in range(m):
        for g in lam([j]):
            mustar[g] += 1
    print(f"  dual excess sum (mu* - 1)+ = {sum(max(0, x - 1) for x in mustar)}; triples with mu* = 0: "
          f"{sum(1 for g in range(n, n + G) if mustar[g] == 0)}")
    parity_only = sum(1 for g in range(n, n + G) if any(g in anc[j] and not (u[g] & sheet_mask[j]) for j in range(m)))
    print(f"  gates that are an ancestor of some sheet with zero path parity to all its outputs: {parity_only}")
    indep = []
    for r in range(1, m + 1):
        for J in combinations(range(m), r):
            if all(not adj[a][b] for a, b in combinations(J, 2)):
                indep.append(J)
    maximal = [J for J in indep if not any(set(J) < set(K) for K in indep)]
    ok = True
    for J in indep:
        lj, dj = len(lam(J)), len(dset(J))
        if lj < 10 * len(J) or dj < 10 * len(J):
            ok = False
            print("  VIOLATION", J, lj, dj)
    print(f"  independent families: {len(indep)}; all satisfy |Lam(J)| >= 10|J| and |D(J)| >= 10|J|: {ok}")
    for J in maximal:
        print(f"    maximal J = {J}: |Lam(J)| = {len(lam(J))}, |D(J)| = {len(dset(J))}, 10|J| = {10 * len(J)}, "
              f"union of single D(j) = {len(set().union(*[dset([j]) for j in J]))}, "
              f"sum of single |D(j)| = {sum(len(dset([j])) for j in J)}")
    if m % 2 == 0 and all(not adj[a][b] for a, b in combinations(range(0, m, 2), 2)) \
            and all(not adj[a][b] for a, b in combinations(range(1, m, 2), 2)):
        ev, od = list(range(0, m, 2)), list(range(1, m, 2))
        X = dset(ev) & dset(od)
        Xl = lam(ev) & lam(od)
        print(f"  even/odd colouring: |D(even)| = {len(dset(ev))}, |D(odd)| = {len(dset(od))}, both: {len(X)}; "
              f"dual: {len(lam(ev))}, {len(lam(od))}, both: {len(Xl)}")


def main():
    a = sys.argv[1:]
    if a[0] == "q":
        m = int(a[1])
        analyse(*load_q(m, a[2]), label=os.path.basename(a[2]))
    else:
        analyse(*load_mc(a[1]), label=os.path.basename(a[1]))


if __name__ == "__main__":
    main()
