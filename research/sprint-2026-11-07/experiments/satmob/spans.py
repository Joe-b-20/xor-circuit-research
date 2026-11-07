import json, sys, itertools, collections
import mob, sat87
for cid in sys.argv[1:]:
    order = mob.load(cid)
    info = json.load(open("comp_%s.json" % cid.replace(":", "_")))
    comps = info["components"]
    singles = {i: mob.describe(order, comps, [i]) for i in range(len(comps))}
    dims = []
    for i, j in itertools.combinations(range(len(comps)), 2):
        Li = singles[i][2]["leaves"]; Lj = singles[j][2]["leaves"]
        di = len(mob.span_basis(Li)); dj = len(mob.span_basis(Lj)); dij = len(mob.span_basis(Li + Lj))
        inter = di + dj - dij
        shared_leaves = len(set(Li) & set(Lj))
        dims.append((i, j, inter, shared_leaves))
    c = collections.Counter(d[2] for d in dims)
    print(cid, "pairs:", len(dims), "dim(span Li ^ span Lj) histogram", sorted(c.items()),
          "pairs sharing a leaf:", sum(1 for d in dims if d[3] > 0),
          "pairs with intersection beyond shared leaves:", sum(1 for d in dims if d[2] > len(mob.span_basis([l for l in singles[d[0]][2]["leaves"] if l in set(singles[d[1]][2]["leaves"])]))))
    print("   ", [(i, j, inter, sl) for i, j, inter, sl in dims if inter > 0])
