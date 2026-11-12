"""CHECK: near/far costs at single-group cuts, mirror (fwd, rev) and primal, over recorded + sampled kste.

usage: python3 far_mc.py STRIDE
Prints per cut k: min/max near (f+h), min far (|P| + e), and the near histogram.
"""
import os
import sys
from collections import Counter, defaultdict

from mirror_mc import mirror, split, mc
from corpus_mc import KSTE, primal_split

REC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "circuits", "aes-mixcolumns")


def circuits(stride):
    for c in ("xor88-depth5", "xor89-depth4", "xor97-depth3"):
        yield "rec" + c, mc.parse_ncff(os.path.join(REC, "aes-mixcolumns-%s.circ.txt" % c))
    nl = 0
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if not os.path.exists(p):
            continue
        for line in open(p):
            if not line.strip():
                continue
            nl += 1
            if nl % stride == 0:
                yield "%s:%d" % (fn, nl), mc.parse_pairs(line)


def main():
    stride = int(sys.argv[1])
    near = defaultdict(Counter)
    far = defaultdict(lambda: 10 ** 9)
    farwho = {}
    for name, gates in circuits(stride):
        r = mc.analyse(gates)
        if r is None or r["distinct"] != len(gates) or r["dead"]:
            continue
        G = len(gates)
        for order in ("fwd", "rev"):
            tot, red, _ = mirror(gates, order)
            for k in range(8):
                st, _, _, _ = split(red, [k])
                key = ("mirror", k)
                near[key][st["near"]] += 1
                fr = st["far"]
                if fr < far[key]:
                    far[key], farwho[key] = fr, (name, order, G, st["near"], st["far"])
        for k in range(8):
            vals, st, labels, exits = primal_split(gates, k)
            key = ("primal", k)
            nr = st["f"] + st["h"]
            near[key][nr] += 1
            fr = st["N"] + len(exits) + st["e"]
            if fr < far[key]:
                far[key], farwho[key] = fr, (name, "-", G, nr, st["N"] + len(exits) + st["e"])
    for key in sorted(near):
        print("%s cut %d: near hist %s; min far (absolute instance cost) %d from %s" % (
            key[0], key[1], dict(sorted(near[key].items())), far[key], farwho[key]))


if __name__ == "__main__":
    main()
