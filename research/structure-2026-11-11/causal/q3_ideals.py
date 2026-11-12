"""Ancestor ideals of the three sheets in the recorded 28-gate circuit for Q_3 (one object; no search).

usage: python3 q3_ideals.py

Prints the ideals A_j (ancestors-or-equal of the outputs of sheet j), their intersections, the gates with
charge 2, and for every sheet the split of its charged gates into "entry" gates (one operand zero on the own
block j after restriction to the blocks j-1, j) and "body" gates, with the unrestricted free operand of each
entry: in a block-monotone circuit that operand lives on block j-1 alone.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def main():
    m = 3
    n, gates = qm.read_circuit(os.path.join(HERE, "..", "rotation", "circuits", "q3_28.txt"))
    targets = qm.rows(m)
    vals = qm.masks(n, gates)
    G = len(gates)
    idx = {v: i for i, v in enumerate(vals)}
    tix = {t: i for i, t in enumerate(targets)}

    def desc(v):
        return " ".join(f"{j}:{NAMES[(v >> (4 * j)) & 15]}" for j in range(m) if (v >> (4 * j)) & 15) or "0"

    def name(i):
        if i < n:
            return f"in({i % 4},{i // 4})"
        if vals[i] in tix:
            k = tix[vals[i]]
            return f"OUT({k % 4},{k // 4})"
        return f"g{i - n}"

    anc = []
    for j in range(m):
        seen, stack = set(), [idx[targets[4 * j + c]] for c in range(4)]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc.append(seen)
    show = lambda S: ", ".join(name(i) for i in sorted(S))
    for j in range(m):
        print(f"|A_{j}| = {len(anc[j])}")
    trunk = anc[0] & anc[1] & anc[2]
    print(f"A_0 & A_1 & A_2 ({len(trunk)}): {show(trunk)}")
    for a, b in ((0, 1), (0, 2), (1, 2)):
        print(f"(A_{a} & A_{b}) minus trunk ({len((anc[a] & anc[b]) - trunk)}): {show((anc[a] & anc[b]) - trunk)}")
    for j in range(m):
        own = anc[j] - set().union(*[anc[k] for k in range(m) if k != j])
        print(f"only A_{j} ({len(own)}): {show(own)}")
    # is the trunk a principal ideal?
    for g in sorted(trunk):
        seen, stack = set(), [g]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        if seen == trunk:
            print(f"trunk = ancestors-or-equal of {name(g)} [{desc(vals[g])}]")
    mu = {}
    for g in range(n, n + G):
        mu[g] = [j for j in range(m) if g in anc[j] and (vals[g] >> (4 * j)) & 15]
    print("gates with charge 2:", ", ".join(f"{name(g)}{mu[g]}" for g in mu if len(mu[g]) >= 2))
    for j in range(m):
        a = (j - 1) % m
        keep = (15 << (4 * j)) | (15 << (4 * a))
        Dj = sorted(g for g in anc[j] if (vals[g] >> (4 * j)) & 15)
        print(f"sheet {j} (own block {j}, neighbour block {a}): {len(Dj)} charged gates")
        for g in Dj:
            x, y = gates[g - n]
            fx = not ((vals[x] >> (4 * j)) & 15)
            fy = not ((vals[y] >> (4 * j)) & 15)
            if fx or fy:
                f = x if fx else y
                o = y if fx else x
                pure = "pure (lives on the neighbour block)" if vals[f] & ~(15 << (4 * a)) == 0 else \
                    "IMPURE: carries a third block, cancelled here or later"
                print(f"   entry {name(g):>9} = {name(o)} + {name(f)}   free operand [{desc(vals[f])}] "
                      f"restricted [{desc(vals[f] & keep)}]  {pure}")
            else:
                third = [s for s in (x, y, g) if vals[s] & ~keep]
                tag = "" if not third else "   (members carrying the third block: " + ", ".join(name(s) for s in third) + ")"
                print(f"   body  {name(g):>9} = {name(x)} + {name(y)}{tag}")


if __name__ == "__main__":
    main()
