"""CHECK / explicit construction (phase 7, main agent): MixColumns circuits with few gates removed when a whole
SET B of blocks is zeroed (generalising compose/compat/lowwaste.py from one block to several).

Construction for B with carriers beta_b (distinct blocks outside B, one per b in B):
  lambda^b_c = input of byte c at block beta_b;  g^b_c = u_{b,c} + lambda^b_c  (u = block-b input);
  per block b the eight required block-b parts w (E_c, s_c) are built from the g^b on the "diagonal"
  (block-b part w, carrier part lambda^b(w)); a row meeting B gets the sum of its per-block diagonal signals
  plus y_r = (row outside B) + (its carrier parts), y_r and the rows not meeting B built by chains of inputs
  (values already present are reused). Every row is verified; the circuit is verified reduced.
Reports, for each B, the gate count, D_B (gates removed when B is zeroed), and the caps
  cap_B = min U_B over the explicit circuits of caps.py + min D_B over all explicit circuits incl. these.
usage: python3 lowwasteB.py STRIDE MAXSIZE
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from caps import UD, wstar  # noqa: E402
from jstats import get  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import KSTE, ROWS, bm, check, values  # noqa: E402


def build(B):
    rest = [k for k in range(8) if k not in B]
    if len(rest) < len(B):
        return None
    carrier = {b: rest[i] for i, b in enumerate(B)}
    idx = {1 << i: i for i in range(32)}
    gates = []

    def add(a, b):
        v = a ^ b
        if v in idx:
            return v
        gates.append((idx[a], idx[b]))
        idx[v] = 31 + len(gates)
        return v

    def chain(v):
        if v in idx:
            return v
        bits = [1 << i for i in range(32) if v >> i & 1]
        acc = bits[0]
        for x in bits[1:]:
            acc = add(acc, x)
        return acc

    lowB = sum(bm(b) for b in B)
    lam = {b: [1 << (8 * c + carrier[b]) for c in range(4)] for b in B}
    u = {b: [1 << (8 * c + b) for c in range(4)] for b in B}
    om = lambda r, b: [c for c in range(4) if r >> (8 * c + b) & 1]
    for r in ROWS.values():
        if not r & lowB:
            chain(r)
    Y = {}
    for r in ROWS.values():
        if r & lowB:
            y = r & ~lowB
            for b in B:
                for c in om(r, b):
                    y ^= lam[b][c]
            Y[r] = chain(y)
    diag = {}
    for b in B:
        g = [add(u[b][c], lam[b][c]) for c in range(4)]
        s = {c: add(g[c], g[(c + 1) % 4]) for c in range(4)}
        for c in range(4):
            diag[(b, (1 << c) | (1 << ((c + 1) % 4)))] = s[c]
            e = add(s[(c + 1) % 4], g[(c + 3) % 4])
            diag[(b, 15 ^ (1 << c))] = e
    for r in ROWS.values():
        if not r & lowB:
            continue
        parts = [diag[(b, sum(1 << c for c in om(r, b)))] for b in B if om(r, b)]
        acc = parts[0]
        for p in parts[1:]:
            acc = add(acc, p)
        add(acc, Y[r])
    return gates


def main():
    stride, maxsize = int(sys.argv[1]), int(sys.argv[2])
    specs = ["r88", "r89", "r97"]
    for fn in sorted(os.listdir(KSTE)):
        if fn.startswith("circuits_"):
            m = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
            specs += ["%s:%d" % (fn, i) for i in range(1, m + 1, stride)]
    lw = [os.path.join(HERE, "..", "review-compat", "lw%d.json" % k) for k in range(8)]
    circs = []
    for s in specs + lw:
        g = get(s)
        if all(check(g)):
            circs.append((s, g, values(g)))
    W = wstar()
    circs.append(("W*", W, values(W)))
    built = {}
    for size in range(1, maxsize + 1):
        for B in itertools.combinations(range(8), size):
            g = build(B)
            if g is None:
                continue
            ok, red = check(g)
            assert ok and red, B
            built[B] = g
            circs.append(("lwB%s" % "".join(map(str, B)), g, values(g)))
    print("explicit circuits:", len(circs), "(constructed:", len(built), ")")
    for size in range(1, maxsize + 1):
        rows = []
        for B in itertools.combinations(range(8), size):
            bu, bd = (10 ** 9, ""), (10 ** 9, "")
            for name, g, vals in circs:
                U, D = UD(g, vals, B)
                if U < bu[0]:
                    bu = (U, name)
                if D < bd[0]:
                    bd = (D, name)
            own = None
            if B in built:
                g = built[B]
                own = (len(g), UD(g, values(g), B)[1])
            rows.append((bu[0] + bd[0], B, bu, bd, own))
        rows.sort(reverse=True)
        print("|B|=%d max cap %d, min cap %d, all < 88: %s" % (size, rows[0][0], rows[-1][0], all(r[0] < 88 for r in rows)))
        for r in rows[:3]:
            print("    cap %d B=%s minU %s minD %s own construction (gates, D_B) %s" % r)
        print("    own-construction D_B range:", min(r[4][1] for r in rows if r[4]), "-", max(r[4][1] for r in rows if r[4]),
              " gates:", min(r[4][0] for r in rows if r[4]), "-", max(r[4][0] for r in rows if r[4]))


if __name__ == "__main__":
    main()
