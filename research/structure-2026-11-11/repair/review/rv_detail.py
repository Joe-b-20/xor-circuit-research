"""Detail of the Theorem P quantities for the triangle event of circuits_2.txt:783 and the A1/A2 examples.
Direct evaluation only. usage: python3 rv_detail.py"""
import sys
from rv import values, cancelled, out_nodes, MC, MC_BM, popc, sheet_of
sys.path.insert(0, __import__("rv").os.path.join(__import__("rv").ST, "compose", "compat"))
from clib import load, desc


def detail(name, n, g, targets, bms, e, fmt):
    v = values(n, g)
    a, b = g[e - n]
    C = cancelled(v[a], v[b], bms)
    Cm = sum(bms[c] for c in C)
    keep = ((1 << n) - 1) ^ Cm
    anc, st = set(), [a, b]
    while st:
        x = st.pop()
        if x not in anc:
            anc.add(x)
            if x >= n:
                st.extend(g[x - n])
    outs = out_nodes(n, g, targets)
    readers = [[] for _ in v]
    for i, (p, q) in enumerate(g):
        readers[p].append(n + i)
        readers[q].append(n + i)
    reach = [False] * len(v)
    for x in range(len(v) - 1, -1, -1):
        if x != e:
            reach[x] = x in outs or any(reach[r] for r in readers[x] if r != e)
    pos = {}
    for i, x in enumerate(v):
        pos.setdefault(x, i)
    print("%s: e = %d = %s + %s, cancels %s, val(e) %s" % (name, e, a, b, C, fmt(v[e])))
    for u in sorted(anc):
        if not v[u] & Cm:
            continue
        p = v[u] & keep
        where = pos.get(p)
        tag = "0" if p == 0 else ("node %d%s" % (where, " (=e)" if where == e else " (after e)" if where > e else "")
                                   if where is not None else "absent")
        print("   %s %3d %-40s shared %-5s P(u) -> %s" % ("in " if u < n else "gate", u, fmt(v[u]), reach[u], tag))


if __name__ == "__main__":
    g = load("circuits_2.txt:783")
    detail("783", 32, g, list(MC.values()), MC_BM, 78, desc)
    bin_ = lambda x: format(x, "b")
    g = [(0, 1), (3, 2), (4, 0)]
    detail("A1", 3, g, values(3, g)[3:], [1, 2, 4], 5, bin_)
    g = [(0, 1), (5, 2), (6, 3), (7, 4), (8, 0), (9, 4), (10, 3)]
    detail("A2", 5, g, values(5, g)[5:], [1 << i for i in range(5)], 9, bin_)
