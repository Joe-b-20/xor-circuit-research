"""Checks: matrix = field arithmetic; formula (3.1); restriction of each sheet to blocks (j-1, j)
equals [b: E_c] + [a: s_c]; supports of the sheets; Corollary 7.2 case analysis by brute force;
charges on the recorded circuits."""
import os
from common import *

rows = mixcolumns_rows()
assert rows == read_mat(), "matrix file differs from field arithmetic"
print("matrix file == field arithmetic: OK")


def on_block(j, vec4):  # vec4 bits indexed by byte c
    return sum(1 << (8 * c + j) for c in range(4) if (vec4 >> c) & 1)


def E(c):
    return 0xF ^ (1 << (c % 4))


def s(c):
    return (1 << (c % 4)) | (1 << ((c + 1) % 4))


# (3.1)
for c in range(4):
    for j in range(8):
        exp = on_block(j, E(c)) ^ on_block((j - 1) % 8, s(c))
        if j in (1, 3, 4):
            exp ^= on_block(7, s(c))
        assert rows[8 * c + j] == exp, (c, j)
print("(3.1) holds for all 32 rows")

# restriction and supports
supp = {}
for j in range(8):
    a, b = (j - 1) % 8, j
    keep = BM[a] | BM[b]
    for c in range(4):
        r = rows[8 * c + j]
        assert r & keep == on_block(b, E(c)) ^ on_block(a, s(c)), ("restriction", j, c)
    ss = {blocks_of(rows[8 * c + j]) for c in range(4)}
    assert len(ss) == 1
    supp[j] = next(iter(ss))
    print("sheet", j, "a =", a, "b =", b, "support", sorted(supp[j]))
print("restriction of every sheet to (a, b) is [b:E_c]+[a:s_c]: OK")

# Corollary 7.2: in a block-monotone circuit a gate in A_j and A_j' has blocks within supp j and j';
# mu counts j, j' only if the gate is nonzero on j and j'.  So mu >= 2 needs j in supp j' and j' in supp j.
bad = [(j, k) for j in range(8) for k in range(8) if j != k and j in supp[k] and k in supp[j]]
print("pairs (j, j') with j in supp(j') and j' in supp(j):", bad)

# recorded circuits
d = os.path.join(ROOT, "circuits/aes-mixcolumns")
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".circ.txt"):
        continue
    gates, outname = read_ncff(os.path.join(d, fn))
    v = masks(gates)
    for s_, o in outname.items():
        assert v[s_] == rows[o], (fn, o)
    for mode in ("all", "named"):
        r = charges(gates, rows, mode, outname)
        mu = r["mu"]
        hist = {}
        for g, m in mu.items():
            hist[m] = hist.get(m, 0) + 1
        G = r["G"]
        excess = sum(max(0, m - 1) for m in mu.values())
        zero = hist.get(0, 0)
        print("%s [%s] G=%d D_j=%s sum=%d mu-hist=%s  80-excess+zero=%d  bm_violators=%d"
              % (fn, mode, G, r["D"], sum(r["D"]), dict(sorted(hist.items())),
                 80 - excess + zero, len(r["bm_viol"])))
        if mode == "all":
            z = [g for g, m in mu.items() if m == 0]
            print("   mu=0 gates:", [(g - 32, sorted(blocks_of(r["v"][g])),
                                      [j for j in range(8) if g in r["A"][j]]) for g in z])
            dup = len(v) - len(set(v))
            print("   duplicate masks:", dup, " outputs used as operands:",
                  sum(1 for a, b in gates if a in outname or b in outname))
