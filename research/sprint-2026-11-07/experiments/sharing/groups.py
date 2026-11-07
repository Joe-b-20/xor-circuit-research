"""Task 1a: verify the group structure from the matrix: supports, weights, isomorphism types,
pairwise support overlaps.  Prints a json summary."""
import json
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import lib

out = {}
for g in range(8):
    rows = lib.GROUPS[g]
    ts = lib.GROUP_TARGETS[g]
    sup = lib.group_support(g)
    bits_in_byte = sorted(set(j % 8 for j in sup))
    out[g] = {
        "rows": rows,
        "row_weights": [bin(t).count("1") for t in ts],
        "support": sup,
        "support_size": len(sup),
        "bit_positions_per_byte": bits_in_byte,
        "row_supports": [lib.support(t) for t in ts],
    }
    print(f"group {g}: rows {rows} weights {out[g]['row_weights']} |supp|={len(sup)} bit positions {bits_in_byte}")
    for i, t in zip(rows, ts):
        print(f"   y{i:2d} = " + " + ".join(f"x{j}" for j in lib.support(t)))

# transposed columns (as 4-bit masks over the group's 4 outputs), distinct nonbasis columns
print()
for g in range(8):
    ts = lib.GROUP_TARGETS[g]
    cols = {}
    for j in lib.group_support(g):
        cm = sum(((ts[r] >> j) & 1) << r for r in range(4))
        cols.setdefault(cm, []).append(j)
    nonbasis = [c for c in cols if bin(c).count("1") >= 2]
    print(f"group {g}: {len(cols)} distinct columns, {len(nonbasis)} distinct nonbasis columns: "
          + ", ".join(f"{c:04b}x{len(cols[c])}" for c in sorted(cols)))

# pairwise support overlaps
print()
print("pairwise |supp(g) & supp(h)|:")
for g in range(8):
    print(" ".join(f"{len(set(lib.group_support(g)) & set(lib.group_support(h))):3d}" for h in range(8)))

# isomorphism check: group 0 vs 2,5,6,7 and group 1 vs 3,4 via bit-position relabeling
def relabeled_rows(g, perm):
    # perm: dict bit-position(0..7) -> bit-position; byte structure kept
    res = []
    for t in lib.GROUP_TARGETS[g]:
        m = 0
        for j in lib.support(t):
            b, r = divmod(j, 8)
            m |= 1 << (8 * b + perm[r])
        res.append(m)
    return sorted(res)

# type A: positions (p, q) with p = j-1 mod 8 (feedback-free) ; group 0 uses (7, 0)
for g in (2, 5, 6, 7):
    perm = {7: g - 1, 0: g}
    perm.update({r: r for r in range(8) if r not in perm})
    # careful: perm must be a bijection on 0..7 -> build one explicitly
    perm = {}
    perm[7] = g - 1; perm[0] = g
    free_src = [r for r in range(8) if r not in (7, 0)]
    free_dst = [r for r in range(8) if r not in (g - 1, g)]
    for s_, d_ in zip(free_src, free_dst):
        perm[s_] = d_
    ok = relabeled_rows(0, perm) == sorted(lib.GROUP_TARGETS[g])
    print(f"group 0 ~ group {g} under bit relabeling 7->{g-1}, 0->{g}: {ok}")
for g in (3, 4):
    perm = {0: g - 1, 1: g, 7: 7}
    free_src = [r for r in range(8) if r not in perm]
    free_dst = [r for r in range(8) if r not in perm.values()]
    for s_, d_ in zip(free_src, free_dst):
        perm[s_] = d_
    ok = relabeled_rows(1, perm) == sorted(lib.GROUP_TARGETS[g])
    print(f"group 1 ~ group {g} under bit relabeling 0->{g-1}, 1->{g}, 7->7: {ok}")

json.dump(out, open(__file__.rsplit("/", 1)[0] + "/groups.json", "w"), indent=1)
