"""CHECK (reviewer, independent code): re-evaluate Obstruction O witnesses at a primal single-block cut.

usage: python3 witness.py FILE LINE BLOCK      (LINE = 1-based line within FILE)
       python3 witness.py --cum LINE BLOCK      (LINE = cumulative line over circuits_1,2,3,depth5)
Own MixColumns matrix (AES, poly 0x11b, wire 8c+j = bit j of byte c, bit 0 = LSB).
Block j = wires {8c + j}. Classification at block k: omega = block-k part.
 far ordinary: both operands omega 0; exit: omega 0 but an operand omega != 0;
 entry: exactly one operand with omega 0 (gate is level-1); first: level-1, new omega (inputs units count as
 existing omegas); h: other level-1. near = f + h, far = ordinary + exits + entries.
Also: does the circuit compute MixColumns, is it reduced, block-monotone (no gate cancels a block)?
"""
import os
import re
import sys

D = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
FILES = ["circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"]


def xt(b):
    b <<= 1
    return (b ^ 0x11b) if b & 0x100 else b


def mul(a, m):
    return {1: a, 2: xt(a), 3: xt(a) ^ a}[m]


def mc_targets():
    # output bit (i, t) as a mask over 32 input wires
    outs = []
    for i in range(4):
        for t in range(8):
            mask = 0
            for c in range(4):
                m = [2, 3, 1, 1][(c - i) % 4]
                for j in range(8):
                    if (mul(1 << j, m) >> t) & 1:
                        mask |= 1 << (8 * c + j)
            outs.append(mask)
    return outs


def blockmask(k):
    return sum(1 << (8 * c + k) for c in range(4))


def blocks(v):
    return {j for j in range(8) if v & blockmask(j)}


def load(args):
    if args[0] == "--cum":
        n = int(args[1])
        for fn in FILES:
            ls = [l for l in open(os.path.join(D, fn)) if l.strip()]
            if n <= len(ls):
                return fn, n, ls[n - 1]
            n -= len(ls)
        raise SystemExit("out of range")
    fn, n = args[0], int(args[1])
    ls = [l for l in open(os.path.join(D, fn)) if l.strip()]
    return fn, n, ls[n - 1]


def main():
    if sys.argv[1] == "--cum":
        fn, n, line = load(sys.argv[1:3])
        ks = sys.argv[3:]
    else:
        fn, n, line = load(sys.argv[1:3])
        ks = sys.argv[3:]
    gates = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", line)]
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    T = mc_targets()
    gv = vals[32:]
    ok = all(t in set(gv) or t in set(vals[:32]) for t in T)
    reduced = len(set(vals)) == len(vals) and 0 not in vals
    cancels = [gi for gi, (a, b) in enumerate(gates) if blocks(vals[32 + gi]) != blocks(vals[a]) | blocks(vals[b])]
    print("%s line %d: gates %d, computes MC %s, reduced %s, block-monotone %s" % (
        fn, n, len(gates), ok, reduced, not cancels))
    for k in map(int, ks):
        low = blockmask(k)
        omegas = {1 << i for i in range(32) if (1 << i) & low}
        f = h = e = ordn = ex = 0
        for gi, (a, b) in enumerate(gates):
            v, oa, ob = vals[32 + gi] & low, vals[a] & low, vals[b] & low
            if v == 0:
                if oa or ob:
                    ex += 1
                else:
                    ordn += 1
            elif (oa == 0) != (ob == 0):
                e += 1
            elif v in omegas:
                h += 1
            else:
                omegas.add(v)
                f += 1
        print("  block %d: f %d h %d near %d | ordinary far %d exits %d entries %d far %d | total %d" % (
            k, f, h, f + h, ordn, ex, e, ordn + ex + e, f + h + ordn + ex + e))


if __name__ == "__main__":
    main()
