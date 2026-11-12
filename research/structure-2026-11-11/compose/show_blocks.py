"""Print a recorded Q_m circuit gate by gate in block coordinates (one 4-bit nibble per block,
bit c = byte c). Read-only inspection of a given circuit; proves nothing.

usage: python3 show_blocks.py ../rotation/circuits/q4_40.txt 4
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "review-pair"))
import rlib as R  # noqa: E402


def nibs(model, v):
    return " ".join("%s" % format(R.nib(model, v, j), "04b")[::-1] for j in range(model["m"]))


def main():
    path, m = sys.argv[1], int(sys.argv[2])
    model = R.qm_model(m)
    n, gates = R.read_qm(path)
    vals = R.values(n, gates)
    outs = {v: k for k, v in model["rows"].items()}
    for i, (a, b) in enumerate(gates):
        g = n + i
        v = vals[g]
        tag = ""
        if v in outs:
            tag = " OUT(c=%d, sheet %d)" % outs[v]
        name = lambda o: ("x%d.%d" % (o % 4, o // 4)) if o < n else ("g%d" % o)
        print("g%-3d = %-6s + %-6s : %s  supp %s%s" % (g, name(a), name(b), nibs(model, v),
              sorted(R.support(model, v)), tag))


if __name__ == "__main__":
    main()
