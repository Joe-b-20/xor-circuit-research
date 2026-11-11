"""delta(T) versus delta(T^T) (L(D_T) = L(D_(T^T)) by transposition, so eps is the same for both).

usage: python3 transpose_check.py table_m4.txt      (reads the T column of a run_exh.py table)
       python3 transpose_check.py all m             (all reduced zero-diagonal T of size m, m <= 5)
"""
import re
import sys

import dmap
import geom
from delta_vs_forest import delta_formula


def main():
    if sys.argv[1] == "all":
        m = int(sys.argv[2])
        offdiag = [(j, k) for j in range(m) for k in range(m) if j != k]
        diff = 0
        tot = 0
        hist = {}
        ex = []
        for bits in range(1 << len(offdiag)):
            T = [0] * m
            for idx, (j, k) in enumerate(offdiag):
                if (bits >> idx) & 1:
                    T[j] |= 1 << k
            T = tuple(T)
            if not dmap.reduced(T):
                continue
            tot += 1
            a, b = delta_formula(T), delta_formula(dmap.transpose(T))
            hist[(min(a, b), max(a, b))] = hist.get((min(a, b), max(a, b)), 0) + 1
            if a != b:
                diff += 1
                if len(ex) < 8:
                    ex.append((dmap.tstr(T), a, b))
        print(f"m={m}: reduced matrices {tot}, with delta(T) != delta(T^T): {diff}")
        print("histogram of (min, max) of the two deltas:", dict(sorted(hist.items())))
        for e in ex:
            print("   ", e)
        return
    for line in open(sys.argv[1]):
        mm = re.match(r"(\S+)\s+rk=(\d+) delta=(\d+) F=(\d) eps=(\S+)", line)
        if not mm:
            continue
        T = dmap.parse_t(mm.group(1))
        Tt = dmap.transpose(T)
        d, dt = geom.delta(T), geom.delta(Tt)
        flag = "" if d == dt else "   <-- differ"
        e = mm.group(5)
        if e.isdigit() and int(e) < max(d, dt):
            flag += "   <-- eps < max(delta)"
        print(f"{mm.group(1):<22} delta={d} delta(T^T)={dt} eps={e}{flag}")


if __name__ == "__main__":
    main()
