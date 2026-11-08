"""Write D.txt (candidate D gate list, named) and P18.txt (18-pair foundation state), with checks."""
import json, os, sys
from common import *
import sat87
tidx = {t: i for i, t in enumerate(TARGETS)}
order, missing, prof = load_deep("b87_most_exact", 87)
vals = sat87.values_of(order)
dep = depth_of(order); users = sat87.dependents(order)
r = [x["actual"] for x in prof["rows"] if x["residual"]][0]
nm = {1 << j: "x%d" % j for j in range(32)}
ti = 0
lines = []
for v, a, b in order:
    if v in tidx:
        nm[v] = "y%d" % tidx[v]
    elif v == r:
        nm[v] = "r"
    else:
        ti += 1; nm[v] = "t%d" % ti
    lines.append("%-4s = %-4s ^ %-4s  %08x  d%d u%d" % (nm[v], nm[a], nm[b], v, dep[v], len(users[v])))
mat_ok = all(t in vals for i, t in enumerate(TARGETS) if i != 19) and TARGETS[19] not in vals
hdr = ["Candidate D = first 87 gates of b87_most_exact.known_completion.json (signals 32..118); the 88th gate of that file",
       "(r ^ x11 = y19) is the archive completion.  31 targets equal the matrix rows of aes-mixcolumns.mat.txt: %s" % mat_ok,
       "missing: y19 = %08x; r = %08x = y19 ^ x11 is a dead gate (no users).  depth %d (over the 31 outputs: %d), 87 distinct values, %d helpers (incl. r), %d input-pair gates."
       % (TARGETS[19], r, max(dep.values()), max(dep[t] for t in TARGETS if t in vals), sum(1 for v in vals if v not in TSET), sum(1 for v, a, b in order if a in INPUTS and b in INPUTS)),
       "name = parentA ^ parentB  mask  depth users", ""]
open("D.txt", "w").write("\n".join(hdr + lines) + "\n")
print("\n".join(hdr))
# 18-pair
o88, K84, miss, pv, rich = foundation18()
w = sat87.wiring_from_values(K84)
dep2 = depth_of(w)
nm2 = {1 << j: "x%d" % j for j in range(32)}
ti = 0; L = []
for v, a, b in w:
    nm2[v] = ("y%d" % tidx[v]) if v in tidx else ("p%d" % (ti := ti + 1) if v in pv else "t%d" % (ti := ti + 1))
    L.append("%-4s = %-4s ^ %-4s  %08x  d%d%s" % (nm2[v], nm2[a], nm2[b], v, dep2[v], "  PAIR" if v in pv else ""))
hdr2 = ["18-pair foundation state (archive 18_pair_87_checkpoint.txt, Sep 9), reconstructed from the 19-pair 88 of",
        "mixcolumns_88_19_primitive_pairs.txt (88 gates, depth 6, 19 input pairs, 69 rich values; checked: all 32 outputs exact).",
        "Drop the pair x1^x17; any-pair closure of 18 pairs + 69 rich values regenerates %d values; missing exactly %s" % (len(K84), ",".join("y%d" % tidx[v] for v in miss)),
        "(the checkpoint says 84 = 18 + 66, missing o9, o10, o18; its o10 support list omits bit 10, a typo: o18^o10 = [9,10,18,25] as it states).",
        "Greedy wiring of the 84 values (one of many; the instances use only the value set):", ""]
open("P18.txt", "w").write("\n".join(hdr2 + L) + "\n")
print("\n".join(hdr2))
