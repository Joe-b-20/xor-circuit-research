"""CHECK (phase 9, main agent): double transposition (C^T)^T, same size, for MixColumns circuits.

A hypothesis tested here and REFUTED by its output: that double transposition yields fan-out <= 2. It does not
(the witnesses keep fan-out 22; the 88s keep 5), because a transposed node is read by the chains of all of its
operands' readers' structure, not only twice. Kept as the record of that negative check.
This script builds (C^T)^T for given circuits of MixColumns, verifies it, and reports max fan-out, G and the
charged families. Direct construction and evaluation only; no search.
usage: python3 fanout2.py SPEC [SPEC ...]
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_witness import mc_rows, stats  # noqa: E402
from dual_test import transpose  # noqa: E402
from transpose_charges import load  # noqa: E402


def fanout(gates, n=32):
    c = Counter()
    for a, b in gates:
        c[a] += 1
        c[b] += 1
    return max(c.values())


def main():
    M = mc_rows()
    MT = {}
    for w in range(32):
        MT[(w // 8, w % 8)] = sum(1 << (8 * c + j) for (c, j) in M if M[(c, j)] >> w & 1)
    bm = lambda j: sum(1 << (8 * c + j) for c in range(4))
    for spec in sys.argv[1:]:
        C = load(spec)
        CT = transpose(C, M)
        CTT = transpose(CT, MT)
        s0, s2 = stats(32, C, M, bm, 8), stats(32, CTT, M, bm, 8)
        print("%s: C G=%d fanout %d |union F|=%d U=%d | (C^T)^T G=%d fanout %d computes %s reduced %s live %s "
              "|union F|=%d U=%d E=%d R=%d" % (os.path.basename(spec), s0["G"], fanout(C), s0["distinct_charged"],
              s0["U"], s2["G"], fanout(CTT), s2["computes"], s2["reduced"], s2["live"], s2["distinct_charged"],
              s2["U"], s2["E"], s2["R"]))


if __name__ == "__main__":
    main()
