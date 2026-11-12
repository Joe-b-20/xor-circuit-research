"""CHECK (not a proof): classify the block-2-cancelling gate in non-monotone kste circuits.

usage: python3 scan_tri.py STRIDE
Line numbers are each file's OWN line numbers (1-based), not a cumulative counter.
For each circuit with a gate whose value is zero on block 2 and whose operands are nonzero on block 2:
operand supports, value support, whether the value is a target (which) or a target minus its block-0 part.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rotation", "mc"))
import mc  # noqa: E402

KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
FILES = ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt")
B = mc.BLOCKMASK
TIDX = {t: i for i, t in enumerate(mc.TARGETS)}


def pat(v):
    return "".join(map(str, sorted(mc.blocks(v))))


def classify(gates):
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    out = []
    for gi, (a, b) in enumerate(gates):
        v = vals[32 + gi]
        if v and not (v & B[2]) and (vals[a] & B[2]):
            if v in TIDX:
                kind = "target(%d,%d)" % divmod(TIDX[v], 8)
            else:
                kind = "other"
                for i, t in enumerate(mc.TARGETS):
                    if v == t & ~B[0]:
                        kind = "target(%d,%d)-blk0" % divmod(i, 8)
            out.append((gi, pat(vals[a]) + "+" + pat(vals[b]), pat(v), kind))
    return out


def main():
    stride = int(sys.argv[1])
    cnt = Counter()
    ex = {}
    for fn in FILES:
        for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
            if ln % stride:
                continue
            gates = mc.parse_pairs(line)
            r = mc.analyse(gates)
            if r is None or r["monotone"]:
                continue
            cl = classify(gates)
            key = (len(cl),) + tuple((o, v, k.split("(")[0] + k.partition(")")[2]) for _, o, v, k in cl)
            cnt[key] += 1
            ex.setdefault(key, []).append((fn, ln, [k for *_, k in cl]))
    for k, n in cnt.most_common(15):
        print(n, k, ex[k][:3])


if __name__ == "__main__":
    main()
