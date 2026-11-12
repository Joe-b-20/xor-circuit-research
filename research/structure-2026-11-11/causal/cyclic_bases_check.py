"""Check of the order-free (dual) charge inequalities on OTHER triple bases of the value set of a recorded circuit.

usage: python3 cyclic_bases_check.py q M FILE [SAMPLES] [SEED]
       python3 cyclic_bases_check.py mc FILE [SAMPLES] [SEED]

The value set S of the circuit is fixed.  All collinear triples of S are listed; a random basis T of the
relation space is drawn among them (random order, greedy by rank).  Most such bases are not executable
(no gate order).  For each basis the dual solution u is computed by linear algebra over F_2
(u(o)^T N_Y = indicator of o) and the claims of the cyclic charge theorem are asserted:
     |Lam(J)| >= 10 |J|   for every family J of pairwise non-adjacent sheets,
     Lam(J) = { t in T : u_t nonzero on the outputs of J, at least two members of t nonzero on blocks(J) }.
This samples bases of ONE value set; it is a test of a proved statement, not a proof, and not a search for
circuits or systems (nothing is optimised; the value set never changes).
"""
import os
import random
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dual_charges as dc  # noqa: E402


def main():
    a = sys.argv[1:]
    if a[0] == "q":
        m0 = int(a[1])
        n, gates, targets, blk, sheet_of_target, m = dc.load_q(m0, a[2])
        rest = a[3:]
        label = os.path.basename(a[2])
    else:
        n, gates, targets, blk, sheet_of_target, m = dc.load_mc(a[1])
        rest = a[2:]
        label = os.path.basename(a[1])
    samples = int(rest[0]) if rest else 200
    rng = random.Random(int(rest[1]) if len(rest) > 1 else 1)
    vals = [1 << i for i in range(n)]
    for x, y in gates:
        vals.append(vals[x] ^ vals[y])
    assert len(set(vals)) == len(vals)
    G = len(gates)
    idx = {v: i for i, v in enumerate(vals)}
    triples = []
    for i, j in combinations(range(n + G), 2):
        k = idx.get(vals[i] ^ vals[j])
        if k is not None and k > j:
            triples.append((i, j, k))
    sup = [blk(v) for v in vals]
    ssup = [None] * m
    for i, t in enumerate(targets):
        ssup[sheet_of_target[i]] = blk(t)
    adj = [[j != k and (k in ssup[j] or j in ssup[k]) for k in range(m)] for j in range(m)]
    indep = [J for r in range(1, m + 1) for J in combinations(range(m), r)
             if all(not adj[x][y] for x, y in combinations(J, 2))]
    tcar = [idx[t] for t in targets]
    sheet_mask = [0] * m
    for ti in range(len(targets)):
        sheet_mask[sheet_of_target[ti]] |= 1 << ti
    print(f"{label}: G = {G}, collinear triples of the value set: {len(triples)}, independent families: {len(indep)}")
    nonexec = 0
    worst = {}
    min_single = [10 ** 9] * m
    for s in range(samples):
        order = triples[:]
        rng.shuffle(order)
        # greedy basis on non-input coordinates, keeping the combination that produced each pivot
        basis = {}          # pivot bit -> (row, combo over chosen triples)
        chosen = []
        for t in order:
            row = 0
            for i in t:
                if i >= n:
                    row |= 1 << (i - n)
            combo = 1 << len(chosen)
            r = row
            while r:
                h = r.bit_length() - 1
                if h in basis:
                    r ^= basis[h][0]
                    combo ^= basis[h][1]
                else:
                    basis[h] = (r, combo)
                    chosen.append(t)
                    break
            if len(chosen) == G:
                break
        assert len(chosen) == G
        # executable?  peel leaves
        left = set(range(G))
        deg = {}
        for ti, t in enumerate(chosen):
            for i in t:
                if i >= n:
                    deg.setdefault(i, set()).add(ti)
        prog = True
        while prog and left:
            prog = False
            for i, ts in list(deg.items()):
                live = ts & left
                if len(live) == 1:
                    left -= live
                    del deg[i]
                    prog = True
        executable = not left
        nonexec += 0 if executable else 1
        # dual solution: for target o, the combination of chosen triples whose non-input part is {o}
        u = [0] * G          # bitmask over targets, per chosen triple
        for ti, cg in enumerate(tcar):
            r = 1 << (cg - n)
            combo = 0
            while r:
                h = r.bit_length() - 1
                r ^= basis[h][0]
                combo ^= basis[h][1]
            for k in range(G):
                if (combo >> k) & 1:
                    u[k] |= 1 << ti
        # check: the combination has input part = the target mask
        for ti, cg in enumerate(tcar):
            acc = 0
            for k in range(G):
                if (u[k] >> ti) & 1:
                    for i in chosen[k]:
                        acc ^= 1 << i
            assert acc == (1 << cg) | sum(1 << i for i in range(n) if (targets[ti] >> i) & 1)
        for J in indep:
            blocks = set(J)
            mask = 0
            for j in J:
                mask |= sheet_mask[j]
            cnt = 0
            for k, t in enumerate(chosen):
                if u[k] & mask and sum(1 for i in t if sup[i] & blocks) >= 2:
                    cnt += 1
            assert cnt >= 10 * len(J), ("VIOLATION", J, cnt, chosen)
            key = len(J)
            worst[key] = min(worst.get(key, 10 ** 9), cnt - 10 * len(J))
            if len(J) == 1:
                min_single[J[0]] = min(min_single[J[0]], cnt)
    print(f"  {samples} random bases, {nonexec} not executable; no violation.")
    print(f"  smallest single-sheet dual charge seen, per sheet: {min_single}")
    print(f"  smallest slack |Lam(J)| - 10|J| seen, by |J|: {dict(sorted(worst.items()))}")


if __name__ == "__main__":
    main()
