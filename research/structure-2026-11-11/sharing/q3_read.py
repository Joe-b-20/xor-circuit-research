"""The 28-gate circuit of Q_3 in the sheet language: charges, double services, and its lifts to covers.

usage: python3 q3_read.py [--cover k]         (reads ../rotation/circuits/q3_28.txt; nothing is searched)

Part 1  every gate: window (pair of blocks or single block), mask, the sheets it is charged to
        (charged to j: nonzero on block j and ancestor-or-equal of an output gate of sheet j).
Part 2  per sheet: the charge set D_j split into gates of the sheet's own window {j-1, j}, single-block gates,
        and gates borrowed from the other two windows; the identity G = 10 m + over + uncharged - excess.
Part 3  the block-cancelling gates with both operands (the "partner" carries the same cancelled component).
Part 4  lift to the k-fold cover Q_(3k): a two-block signal on blocks {b, b+1 mod 3} has k lift classes
        (position difference d = 1 mod 3, taken mod 3k).  Outputs need the class d = 1.  A gate inside one
        window passes its class to its two-block operands; a triangle gate [i,j] + [j,k] -> [i,k] may place the
        cancelled block j at any of k positions.  The script minimises, over these placements, the number of
        (gate, class) pairs needed; the lifted circuit for Q_(3k) has k times that many gates.  This is a count
        under the stated lifting model (one position choice per triangle gate and class); the lifted circuit is
        not written out or verified here, because the count is above 10 m and so is not a saving.
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}
M = 3


def main():
    path = os.path.join(HERE, "..", "rotation", "circuits", "q3_28.txt")
    n, gates = qm.read_circuit(path)
    targets = qm.rows(M)
    vals = qm.masks(n, gates)
    assert qm.computes(n, gates, targets)
    G = len(gates)
    sup = [frozenset(j for j in range(M) if (v >> (4 * j)) & 15) for v in vals]
    first = {}
    for i in range(n, n + G):
        first.setdefault(vals[i], i)
    tix = {first[t]: i for i, t in enumerate(targets)}
    anc = [set() for _ in range(M)]
    for oi, t in enumerate(targets):
        seen, stack = set(), [first[t]]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[oi // 4] |= seen

    def name(s):
        if s < n:
            return f"in({s % 4},{s // 4})"
        if s in tix:
            return f"OUT({tix[s] % 4},{tix[s] // 4})"
        return f"g{s - n}"

    def desc(v):
        return " ".join(f"{j}:{NAMES[(v >> (4 * j)) & 15]}" for j in range(M) if (v >> (4 * j)) & 15)

    charged = {g: [j for j in range(M) if j in sup[g] and g in anc[j]] for g in range(n, n + G)}
    print("PART 1  gates (window of sheet j is {j-1, j}: sheet 0 = {2,0}, sheet 1 = {0,1}, sheet 2 = {1,2})")
    for g in range(n, n + G):
        a, b = gates[g - n]
        print(f"  {name(g):>9} = {name(a):>9} + {name(b):<9} [{desc(vals[g]):<12}] blocks {sorted(sup[g])}  charged to sheets {charged[g]}")
    mu = {g: len(c) for g, c in charged.items()}
    print("gates with mu >= 2:", ", ".join(f"{name(g)}{charged[g]}" for g in charged if mu[g] >= 2))
    print("PART 2")
    over = 0
    for j in range(M):
        Dj = [g for g in charged if j in charged[g]]
        own = [g for g in Dj if sup[g] == frozenset([(j - 1) % M, j])]
        single = [g for g in Dj if len(sup[g]) == 1]
        borrowed = [g for g in Dj if g not in own and g not in single]
        over += len(Dj) - 10
        print(f"  sheet {j}: |D_j| = {len(Dj)} = own window {len(own)} + single-block {len(single)} + borrowed {len(borrowed)}"
              f"   borrowed: {', '.join(name(g) + '[' + desc(vals[g]) + ']' for g in borrowed)}")
    excess = sum(max(0, x - 1) for x in mu.values())
    unch = sum(1 for x in mu.values() if x == 0)
    print(f"  G = {G};  10m + over + uncharged - excess = {10 * M} + {over} + {unch} - {excess} = {10 * M + over + unch - excess}")
    by_win = {}
    for g in range(n, n + G):
        by_win.setdefault(tuple(sorted(sup[g])), []).append(g)
    print("  gates by support:", {k: len(v) for k, v in sorted(by_win.items())})
    print("PART 3  block-cancelling gates")
    tri = []
    for g in range(n, n + G):
        a, b = gates[g - n]
        lost = (sup[a] | sup[b]) - sup[g]
        if lost:
            tri.append(g)
            print(f"  {name(g)} = {name(a)}[{desc(vals[a])}] + {name(b)}[{desc(vals[b])}] = [{desc(vals[g])}]  cancels block {sorted(lost)};"
                  f" operands charged to {charged.get(a, [])} and {charged.get(b, [])}")
    # ---------------- Part 4: lifting
    k = int(sys.argv[sys.argv.index("--cover") + 1]) if "--cover" in sys.argv else 2
    print(f"PART 4  lift to the {k}-fold cover Q_{M * k}")
    # class of a two-block signal with support {b, b+1 mod 3}: e in Z_k, meaning position(b+1) - position(b) = 1 + 3e (mod 3k)
    # (for support {2,0}: lower block is 2, upper block is 0)

    def low_high(s):
        (x, y) = sorted(s)
        return (x, y) if (y - x) == 1 else (y, x)      # {0,2}: low = 2, high = 0

    two = [g for g in range(n, n + G) if len(sup[g]) == 2]
    best = None
    choices_space = list(itertools.product(range(k), repeat=len(tri)))
    for choice in itertools.product(range(k), repeat=2 * len(tri)):
        # choice[2*t + r]: offset used by triangle gate t when it is needed in class index r (r = 0, 1): only the
        # first two needed classes get an independent choice; further classes reuse choice r mod 2
        need = {g: set() for g in range(n, n + G)}
        for g in tix:
            need[g].add(0)                # outputs: adjacent blocks
        ok = True
        plan = {}
        for g in range(n + G - 1, n - 1, -1):
            if len(sup[g]) != 2 or not need[g]:
                if len(sup[g]) == 1 and g in set().union(*anc):
                    need[g].add(0)        # single-block gates: one class
                    a, b = gates[g - n]
                    for o in (a, b):
                        if o >= n and len(sup[o]) == 2:
                            need[o].add(0)     # an exit: both operands in the same (any) class; take class 0
                continue
            a, b = gates[g - n]
            lo, hi = low_high(sup[g])
            for ri, e in enumerate(sorted(need[g])):
                if g in tri:
                    t = tri.index(g)
                    f = choice[2 * t + (ri % 2)]
                    # g = a + b, cancelled block j; a on {x, j}, b on {j, y}
                    j = next(iter((sup[a] | sup[b]) - sup[g]))
                    # positions: lo at 0, hi at 1 + 3e; block j at position p_j = (j - lo) mod 3 + 3f relative to lo
                    pj = ((j - lo) % 3) + 3 * f
                    for o in (a, b):
                        olo, ohi = low_high(sup[o])
                        pos = {lo: 0, hi: 1 + 3 * e, j: pj}
                        d = (pos[ohi] - pos[olo]) % (3 * k)
                        assert d % 3 == 1
                        need[o].add((d - 1) // 3)
                    plan[(g, e)] = f
                else:
                    for o in (a, b):
                        if o >= n and len(sup[o]) == 2:
                            if sup[o] != sup[g]:
                                ok = False
                            need[o].add(e)
        if not ok:
            continue
        total = sum(len(need[g]) for g in range(n, n + G) if need[g])
        if best is None or total < best[0]:
            best = (total, {g: sorted(need[g]) for g in need if len(need[g]) > 1}, dict(plan))
    total, multi, plan = best
    print(f"  minimum number of (gate, class) pairs: {total}  -> lifted circuit for Q_{M * k} with {k * total} gates "
          f"(k * 28 = {k * G}; block-monotone bound 10 m = {10 * M * k})")
    print("  gates needed in more than one class:", {name(g): c for g, c in multi.items()})


if __name__ == "__main__":
    main()
