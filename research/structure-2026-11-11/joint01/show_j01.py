"""Print the local gate set G01 of a recorded MixColumns circuit (inspection of an existing circuit; proves nothing).

usage: python3 show_j01.py [FILE.circ.txt]
G01 = gates that are ancestors-or-equal of an output of sheet 0 or 1 and are not supported on block 7 alone.
Each gate is printed restricted to blocks 7 (= a, free), 0 (= b), 1 (= b') as three nibbles (bit c of block j),
with its two operands (u = own unit, free = vector on block 7, g = earlier gate of the set).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation", "mc"))
import mc  # noqa: E402


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def s(x):
    return "".join(str((x >> c) & 1) for c in range(4))


def main():
    f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "..", "..", "..", "circuits", "aes-mixcolumns", "aes-mixcolumns-xor88-depth5.circ.txt")
    gates = mc.parse_ncff(f)
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    anc = set()
    stack = [first[mc.TARGETS[8 * c + j]] for j in (0, 1) for c in range(4)]
    outs = {first[mc.TARGETS[8 * c + j]]: (j, c) for j in (0, 1) for c in range(4)}
    while stack:
        g = stack.pop()
        if g < n or g in anc:
            continue
        anc.add(g)
        stack.extend(gates[g - n])
    G01 = sorted(g for g in anc if mc.blocks(vals[g]) != frozenset([7]))
    name = {g: "g%d" % i for i, g in enumerate(G01)}

    def op(o):
        if o in name:
            return name[o]
        v = vals[o]
        if mc.blocks(v) <= frozenset([7]):
            return "free[%s]" % s(nib(v, 7))
        if o < n:
            return "u(%s,%d)" % ("b" if o % 8 == 0 else "b'" if o % 8 == 1 else "?", o // 8)
        return "?%d" % o

    print(os.path.basename(f), "|G01| =", len(G01))
    print("gate   a(7)  b(0)  b'(1)   operands")
    for g in G01:
        v = vals[g]
        other = [j for j in mc.blocks(v) if j not in (7, 0, 1)]
        a, b = gates[g - n]
        tag = ("  OUT sheet %d c=%d" % outs[g]) if g in outs else ""
        print("%-5s  %s  %s  %s   %s + %s%s%s" % (name[g], s(nib(v, 7)), s(nib(v, 0)), s(nib(v, 1)), op(a), op(b),
                                                   tag, ("  other blocks %s" % other) if other else ""))


if __name__ == "__main__":
    main()
