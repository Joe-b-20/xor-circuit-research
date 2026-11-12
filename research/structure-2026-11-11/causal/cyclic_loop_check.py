"""Test of the cyclic (order-free) charge theorem on based cyclic systems that are NOT circuits.

usage: python3 cyclic_loop_check.py q M FILE [TRIALS] [BASES] [SEED]
       python3 cyclic_loop_check.py mc FILE [TRIALS] [BASES] [SEED]

Designed objects (no optimisation, nothing is searched for): start from the value set S of a recorded circuit.
One trial adds ONE new vector z = a + p = q + r, where {a, p, q, r} is a 4-term relation among elements of S
and z is not in S.  S' = S + {z} is a circuit set with G + 1 non-inputs and at least two triples through z, so
its relation space has several triple bases; BASES random bases are drawn (random order, greedy by rank).
A basis that omits a gate triple lying on the loop is typically not executable.  For every basis:
   * the dual solution u is computed by linear algebra and checked (the combination for target o has
     non-input part {o} and input part = the row of o);
   * executability is decided by peeling (leaf property);
   * the inequalities |Lam(J)| >= 10|J| are asserted for every family J of pairwise non-adjacent sheets.
This is a randomised test of a statement proved in the report; it cannot prove it.
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
        n, gates, targets, blk, sheet_of_target, m = dc.load_q(int(a[1]), a[2])
        rest, label = a[3:], os.path.basename(a[2])
    else:
        n, gates, targets, blk, sheet_of_target, m = dc.load_mc(a[1])
        rest, label = a[2:], os.path.basename(a[1])
    trials = int(rest[0]) if rest else 50
    nbases = int(rest[1]) if len(rest) > 1 else 20
    rng = random.Random(int(rest[2]) if len(rest) > 2 else 1)
    base_vals = [1 << i for i in range(n)]
    for x, y in gates:
        base_vals.append(base_vals[x] ^ base_vals[y])
    assert len(set(base_vals)) == len(base_vals)
    base_set = set(base_vals)
    # all sums of two elements, to find 4-term relations a + p = q + r with the sum outside S
    sums = {}
    for i, j in combinations(range(len(base_vals)), 2):
        z = base_vals[i] ^ base_vals[j]
        if z not in base_set:
            sums.setdefault(z, []).append((i, j))
    cands = sorted(z for z, prs in sums.items() if len(prs) >= 2)
    ssup = [None] * m
    for i, t in enumerate(targets):
        ssup[sheet_of_target[i]] = blk(t)
    adj = [[j != k and (k in ssup[j] or j in ssup[k]) for k in range(m)] for j in range(m)]
    indep = [J for r in range(1, m + 1) for J in combinations(range(m), r)
             if all(not adj[x][y] for x, y in combinations(J, 2))]
    sheet_mask = [0] * m
    for ti in range(len(targets)):
        sheet_mask[sheet_of_target[ti]] |= 1 << ti
    print(f"{label}: G = {len(gates)}; vectors z outside S with at least two representations z = a + p: {len(cands)}")
    tot = nonexec = 0
    worst = {}
    min_single = 10 ** 9
    for _ in range(trials):
        z = rng.choice(cands)
        vals = base_vals + [z]
        G = len(vals) - n
        idx = {v: i for i, v in enumerate(vals)}
        sup = [blk(v) for v in vals]
        triples = []
        for i, j in combinations(range(len(vals)), 2):
            k = idx.get(vals[i] ^ vals[j])
            if k is not None and k > j:
                triples.append((i, j, k))
        tcar = [idx[t] for t in targets]
        for _b in range(nbases):
            order = triples[:]
            rng.shuffle(order)
            basis, chosen = {}, []
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
                    elif not live:
                        del deg[i]
            tot += 1
            nonexec += 1 if left else 0
            u = [0] * G
            for ti, cg in enumerate(tcar):
                r = 1 << (cg - n)
                combo = 0
                while r:
                    h = r.bit_length() - 1
                    r ^= basis[h][0]
                    combo ^= basis[h][1]
                acc = 0
                for k in range(G):
                    if (combo >> k) & 1:
                        u[k] |= 1 << ti
                        for i in chosen[k]:
                            acc ^= 1 << i
                assert acc == (1 << cg) | sum(1 << i for i in range(n) if (targets[ti] >> i) & 1)
            for J in indep:
                blocks = set(J)
                mask = 0
                for j in J:
                    mask |= sheet_mask[j]
                cnt = sum(1 for k, t in enumerate(chosen)
                          if u[k] & mask and sum(1 for i in t if sup[i] & blocks) >= 2)
                assert cnt >= 10 * len(J), ("VIOLATION", J, cnt, z, chosen)
                worst[len(J)] = min(worst.get(len(J), 10 ** 9), cnt - 10 * len(J))
                if len(J) == 1:
                    min_single = min(min_single, cnt)
    print(f"  {trials} added vectors x {nbases} random bases = {tot} based cyclic systems, {nonexec} NOT executable; "
          f"no violation of |Lam(J)| >= 10|J|.")
    print(f"  smallest single-sheet dual charge seen: {min_single}; smallest slack by |J|: {dict(sorted(worst.items()))}")


if __name__ == "__main__":
    main()
