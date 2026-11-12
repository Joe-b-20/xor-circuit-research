"""Reviewer's checks on the explicit large circuits (machine review, phase 7): all identities of rv_checks.analyse on
lw0..lw7, W*, and the reviewer's carrier constructions for |B| = 1, 2; plus the lw7 / lw4 statements of ACCOUNT.
usage: python3 rv_constructions.py
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import BLK, COMPAT, JOINT, WIN, ancestors_of_rows, check, load_json, restrict, rho_all, values, nib  # noqa
from rv_checks import analyse  # noqa
from rv_caps import carrier_build  # noqa


def main():
    circs = [("lw%d" % k, load_json(os.path.join(COMPAT, "lw%d.json" % k))) for k in range(8)]
    circs.append(("W*", load_json(os.path.join(JOINT, "wstar.json"))))
    for size in (1, 2):
        for B in itertools.combinations(range(8), size):
            circs.append(("cB" + "".join(map(str, B)), carrier_build(B)))
    for name, g in circs:
        assert all(check(g)), name
        r = analyse(g)  # asserts J1 (|B|<=2), J3, J2, J4, J6, J7, J8/J9
        if not name.startswith("cB") or name in ("cB7", "cB45"):
            v = values(g)
            Db = [len(restrict(g, v, (b,))[0]) for b in range(8)]
            print("%-5s G=%d mono=%s D_b=%s lam0=%d lam2=%d N=%d dead=%d" % (name, len(g), r["mono"], Db, r["lam0"],
                                                                              r["lam2"], r["N"], r["dead"]))
    print("all identities hold on", len(circs), "explicit circuits")
    g = dict(circs)["lw7"]
    v = values(g)
    anc = ancestors_of_rows(g, v)
    diag = [x for x in range(32, len(v)) if v[x] & ~(BLK[2] | BLK[7]) == 0 and nib(v[x], 2) == nib(v[x], 7)
            and bin(nib(v[x], 2)).count("1") == 1]
    for x in diag:
        print("lw7 diagonal unit g%d [2:%s 7:%s] sheets served %s" % (x, format(nib(v[x], 2), "04b")[::-1],
                                                                        format(nib(v[x], 7), "04b")[::-1],
                                                                        [j for j in range(8) if x in anc[j]]))
    for name in ("lw4",):
        g = dict(circs)[name]
        v = values(g)
        anc = ancestors_of_rows(g, v)
        rem = {b: restrict(g, v, (b,))[0] for b in range(8)}
        print(name, "charged F_j removed at j / |F_j|:",
              [(j, len({x for x in anc[j] if v[x] & BLK[j]} & rem[j]), len({x for x in anc[j] if v[x] & BLK[j]}))
               for j in range(8)])


if __name__ == "__main__":
    main()
