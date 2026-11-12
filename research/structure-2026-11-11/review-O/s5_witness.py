import os, olib
K = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor/")
W = [("circuits_2.txt", 1128), ("circuits_1.txt", 26), ("circuits_1.txt", 4), ("circuits_1.txt", 3), ("circuits_1.txt", 2),
     ("circuits_1.txt", 1), ("circuits_1.txt", 9), ("circuits_1.txt", 39), ("circuits_1.txt", 10), ("circuits_1.txt", 22), ("circuits_2.txt", 313), ("circuits_2.txt", 213), ("circuits_3.txt", 13114)]
for fn, ln in W:
    g = olib.parse_pairs(open(K + fn).read().split("\n")[ln - 1])
    out = [fn, ln, len(g), olib.check(g, olib.ROWS)[:2]]
    for order in ("fwd", "rev"):
        Tm, Tops, outs = olib.transpose(g, olib.ROWS, order=order)
        rv, rops, rg = olib.reduce_mirror(Tm, Tops)
        out.append((order, len(rg), olib.check(rg, olib.MROWS)[:2]))
    print(out)
