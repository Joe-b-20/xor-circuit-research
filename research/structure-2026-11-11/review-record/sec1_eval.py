"""Section 1 test: evaluation at a point, on every recorded circuit.

For each circuit and each test point x (all-ones, every unit vector for n <= 32, every 1 + e_i for
n <= 32, and random points of several densities) we compute, from the definitions:
  E      = span of the masks dead at x (dead inputs and dead gates), built gate by gate;
  blocks = classes of supp(x) under i ~ j iff e_i + e_j in E (union-find along the live+live gates,
           then checked against E);
and verify exactly:
  (a) dim E only grows at live+live gates, by at most one;
  (b) E is exactly the space 'even on every block, free outside supp(x)' (containment + dimension);
  (c) every live signal is odd on exactly one block (= congruent to some e_i, i in supp(x));
  (d) dead gates >= wt(x) - c and live gates >= wt(Mx) (live outputs = wt(Mx) distinct gates);
  (e) the words (b_C, M b_C) are nonzero, pairwise disjoint and sum to (x, Mx).
Usage: python3 sec1_eval.py [points_per_circuit]
"""
import random
import sys

from lib import all_circuits, load, par, wt, Span

random.seed(20261111)
PTS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
TIGHT = [0, 0]


def test_point(n, gates, outs, vals, rows, x):
    full = (1 << n) - 1
    E = Span()
    for i in range(n):
        if not (x >> i) & 1:
            E.add(1 << i)
    dim0 = E.dim()
    live = lambda v: par(v & x)
    # union-find on supp(x); every live signal carries a representative input index
    parent = {i: i for i in range(n) if (x >> i) & 1}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    gate_names = {g[0] for g in gates}
    rep = {}
    for k, v in vals.items():
        if k not in gate_names:  # an input: mask is a unit vector
            i = v.bit_length() - 1
            if (x >> i) & 1:
                rep[k] = i
    dead_g = live_g = 0
    grow_bad = 0
    pairs = []
    for o, a, b in gates:
        v = vals[o]
        la, lb = live(vals[a]), live(vals[b])
        before = E.dim()
        if live(v):
            live_g += 1
            rep[o] = rep[a] if la else rep[b]
        else:
            dead_g += 1
            E.add(v)
            if la and lb:
                i, j = rep[a], rep[b]
                pairs.append((i, j))
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
        if E.dim() - before > (1 if (la and lb) else 0):
            grow_bad += 1
    blocks = {}
    for i in parent:
        blocks.setdefault(find(i), []).append(i)
    blocks = list(blocks.values())
    c = len(blocks)
    bmask = [sum(1 << i for i in B) for B in blocks]
    errs = []
    if grow_bad:
        errs.append("a")
    # (b) E contains block differences and is even on every block, dim = n - c
    ok_b = E.dim() == n - c
    for B in blocks:
        for i in B[1:]:
            if ((1 << i) ^ (1 << B[0])) not in E:
                ok_b = False
    for v in E.basis.values():
        if any(par(v & m) for m in bmask):
            ok_b = False
    if not ok_b:
        errs.append("b")
    # (c) live signals odd on exactly one block
    for k, v in vals.items():
        if live(v) and sum(par(v & m) for m in bmask) != 1:
            errs.append("c")
            break
    Mx = [par(r & x) for r in rows]
    wMx = sum(Mx)
    live_out_gates = len({vals[o] for o, r in zip(outs, rows) if par(r & x)} & {vals[g[0]] for g in gates})
    if dead_g < wt(x) - c or live_g < wMx or E.dim() - dim0 != wt(x) - c:
        errs.append("d")
    # (e) block words
    images = []
    for m in bmask:
        images.append(sum(par(r & m) << o for o, r in enumerate(rows)))
    union = 0
    for m, im in zip(bmask, images):
        if m == 0 or (union & im):
            errs.append("e")
            break
        union |= im
    if sum(bmask) != x or union != sum(b << o for o, b in enumerate(Mx)):
        errs.append("e")
    return errs, dead_g, live_g, c, wMx, live_out_gates


def main():
    tot = bad = 0
    hyp = []
    slack_min = {}
    for mapname, mat, circs in all_circuits():
        for circ in circs:
            n, gates, outs, vals, rows = load(circ, mat)
            distinct = len(set(rows)) == len(rows)
            nonunit = all(wt(r) != 1 for r in rows)
            if not (distinct and nonunit):
                hyp.append((circ.name, distinct, nonunit))
            full = (1 << n) - 1
            pts = [full]
            if n <= 32:
                pts += [1 << i for i in range(n)] + [full ^ (1 << i) for i in range(n)]
            for _ in range(PTS):
                dens = random.choice([0.1, 0.3, 0.5, 0.7, 0.9])
                x = sum(1 << i for i in range(n) if random.random() < dens) or 1
                pts.append(x)
            for x in pts:
                errs, dg, lg, c, wMx, lo = test_point(n, gates, outs, vals, rows, x)
                tot += 1
                TIGHT[0] += dg == wt(x) - c
                TIGHT[1] += lg == wMx
                if errs:
                    bad += 1
                    print("VIOLATION", circ.name, hex(x), errs, dg, lg, c, wMx)
                if distinct and nonunit and lo != wMx:
                    print("live-output count mismatch", circ.name, hex(x), lo, wMx)
            print(f"{circ.name}: {len(pts)} points ok" if not bad else f"{circ.name}: done")
    print(f"TOTAL points tested {tot}, violating {bad}")
    print(f"equality cases: dead == wt(x)-c at {TIGHT[0]} points, live == wt(Mx) at {TIGHT[1]} points")
    print("circuits whose matrix has repeated or unit rows:", hyp if hyp else "none")


if __name__ == "__main__":
    main()
