"""Section 3 'Observed on the recorded 88@5', recomputed independently.

Partition at the all-ones point; producers by operand kind; helpers per sheet (= the block on
which the helper is odd); number of sums; attribution of each sum to sheets by forward closure
(the sheets of the odd gates reachable from it through even gates only); flag levels
W1 = constant on every block, W2 = every block in {0000, 1010, 0101, 1111}, W3 = even on every block.
"""
import sys
from collections import Counter, defaultdict

from lib import CIRC, load, par, rank, Span

path = sys.argv[1] if len(sys.argv) > 1 else "aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt"
n, gates, outs, vals, rows = load(CIRC / path, CIRC / "aes-mixcolumns/aes-mixcolumns.mat.txt")
gate_names = [g[0] for g in gates]
outset = set(outs)
odd = {k for k in vals if par(vals[k])}
inputs = [k for k in vals if k not in set(gate_names)]
helpers = [g for g in gate_names if g in odd and g not in outset]


def blocks(mu):
    return [tuple((mu >> (8 * c + j)) & 1 for c in range(4)) for j in range(8)]


# partition
E = Span()
for g in gate_names:
    if g not in odd:
        E.add(vals[g])
part = []
seen = set()
for i in range(32):
    if i in seen:
        continue
    B = [j for j in range(32) if j == i or ((1 << i) ^ (1 << j)) in E]
    seen.update(B)
    part.append(B)
canon = [[8 * c + j for c in range(4)] for j in range(8)]
print("partition is the eight bit blocks:", sorted(part) == sorted(canon), "; blocks:", len(part))

# producers
kinds = Counter()
for o, a, b in gates:
    if a in odd and b in odd:
        k = tuple(sorted(("in" if s in inputs else "out" if s in outset else "helper") for s in (a, b)))
        kinds[k] += 1
print("producers by operand kinds:", dict(kinds), "total", sum(kinds.values()))


def sheet(mu):
    s = [j for j, b in enumerate(blocks(mu)) if sum(b) & 1]
    return s[0] if len(s) == 1 else tuple(s)


print("helpers per sheet:", dict(sorted(Counter(sheet(vals[h]) for h in helpers).items())))
sums = [o for o, a, b in gates if a not in odd and b not in odd]
print("sums:", len(sums))
users = defaultdict(list)
for o, a, b in gates:
    users[a].append(o)
    users[b].append(o)


def reach_sheets(s):
    res, stack, vis = set(), [s], set()
    while stack:
        v = stack.pop()
        for u in users[v]:
            if u in vis:
                continue
            vis.add(u)
            if u in odd:
                res.add(sheet(vals[u]))
            else:
                stack.append(u)
    return frozenset(res)


att = Counter(reach_sheets(s) for s in sums)
print("sums by forward-closure sheet set:", {tuple(sorted(k)): v for k, v in att.items()})


def level(mu):
    bl = blocks(mu)
    if any(sum(b) & 1 for b in bl):
        return 4
    if any(b[0] != b[2] or b[1] != b[3] for b in bl):
        return 3
    if any(b[0] != b[1] for b in bl):
        return 2
    return 1 if mu else 0


lv = [level(vals[g]) for g in gate_names]
inW2 = [vals[g] for g in gate_names if level(vals[g]) <= 2]
inW1 = [vals[g] for g in gate_names if level(vals[g]) <= 1]
print(f"gate signals in W2: {len(inW2)} (rank {rank(inW2)}), in W1: {len(inW1)} (rank {rank(inW1)}),"
      f" in W3: {sum(l <= 3 for l in lv)} (rank {rank([vals[g] for g in gate_names if level(vals[g]) <= 3])})")
