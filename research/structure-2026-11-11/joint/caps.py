"""CHECK (phase 7, main agent): caps of the restriction form "G >= K_B + delta_B" for block sets B, |B| <= 3.

The form: delta_B a lower bound on D_B valid for EVERY MixColumns circuit; then L >= K_B + delta_B, where
K_B = L(MixColumns with the blocks of B zeroed). Any such bound is at most
    cap_B = min_C U_B(C) + min_W D_B(W)
over explicit circuits C, W (U_B(C) >= K_B is the number of gates useful after zeroing B; D_B(W) >= delta_B).
Explicit circuits used: the recorded 88/89/97, every STRIDE-th kste circuit, the review-compat low-waste
circuits lw0..lw7, and one constructed circuit W* (prefix chain y_i = x_0 + ... + x_i over the 32 inputs in
wire order, then each output as the XOR of the y_i at the boundaries of its support, reusing existing
values): built here, verified to compute MixColumns and to be reduced. Explicit constructions; no search.
usage: python3 caps.py STRIDE
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jclass import restrict  # noqa: E402
from jstats import get, zero_mask  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import KSTE, ROWS, check, values  # noqa: E402


def wstar():
    gates, vals = [], [1 << i for i in range(32)]
    pos = {}
    for i, v in enumerate(vals):
        pos[v] = i
    y = [0]
    for i in range(1, 32):
        a = y[-1]
        gates.append((a, i))
        vals.append(vals[a] ^ vals[i])
        pos[vals[-1]] = len(vals) - 1
        y.append(len(vals) - 1)
    for r in sorted(ROWS):
        m = ROWS[r]
        s = [(m >> i) & 1 for i in range(32)] + [0]
        terms = [y[i] for i in range(32) if s[i] != s[i + 1]]
        cur = terms[0]
        for t in terms[1:]:
            v = vals[cur] ^ vals[t]
            if v in pos:
                cur = pos[v]
                continue
            gates.append((cur, t))
            vals.append(v)
            pos[v] = len(vals) - 1
            cur = len(vals) - 1
    return gates


def removal_sets(g):
    vals = values(g)
    return vals


def UD(g, vals, B):
    keep = zero_mask(B)
    rep = {}
    for i in range(32):
        rep.setdefault((1 << i) & keep, i)
    rep.setdefault(0, -1)
    first = {}
    D = 0
    for gi, (a, c) in enumerate(g):
        x = 32 + gi
        p = vals[x] & keep
        if p in rep:
            D += 1
        else:
            rep[p] = x
            first[x] = (a, c)
    cls = lambda s: rep[vals[s] & keep] if s >= 0 else -1
    roots = {rep[r & keep] for r in ROWS.values()}
    useful, st = set(), [r for r in roots if r >= 32]
    while st:
        s = st.pop()
        if s in useful:
            continue
        useful.add(s)
        for o in first[s]:
            co = cls(o)
            if co >= 32:
                st.append(co)
    return len(useful), D


def main():
    stride = int(sys.argv[1])
    W = wstar()
    ok, red = check(W)
    print("W*: %d gates, computes MixColumns: %s, reduced: %s" % (len(W), ok, red))
    assert ok and red
    json.dump(W, open(os.path.join(HERE, "wstar.json"), "w"))
    specs = ["r88", "r89", "r97"]
    for fn in sorted(os.listdir(KSTE)):
        if fn.startswith("circuits_"):
            m = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
            specs += ["%s:%d" % (fn, i) for i in range(1, m + 1, stride)]
    lw = [os.path.join(HERE, "..", "review-compat", "lw%d.json" % k) for k in range(8)]
    circs = []
    for s in specs + lw:
        g = get(s)
        ok, red = check(g)
        if ok and red:
            circs.append((s, g, values(g)))
    circs.append(("W*", W, values(W)))
    print("circuits used:", len(circs))
    for size in (1, 2, 3):
        rows = []
        for B in itertools.combinations(range(8), size):
            bestU, bestD = (10 ** 9, None), (10 ** 9, None)
            for name, g, vals in circs:
                U, D = UD(g, vals, B)
                if U < bestU[0]:
                    bestU = (U, name)
                if D < bestD[0]:
                    bestD = (D, name)
            rows.append((bestU[0] + bestD[0], B, bestU, bestD))
        rows.sort(reverse=True)
        print("|B| = %d: largest caps (cap, B, min U_B [circuit], min D_B [witness]):" % size)
        for r in rows[:6]:
            print("   ", r)
        print("   smallest cap:", rows[-1])
        print("   all caps < 88:", all(r[0] < 88 for r in rows), " max cap:", rows[0][0])


if __name__ == "__main__":
    main()
