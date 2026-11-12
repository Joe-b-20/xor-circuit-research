"""Check of ONE hand-written formal near circuit (first sheet) -- a check, not a search.

File lines: "name = a + b" over inputs w0..w3 (sheet units) and z1..zt (formal labels, each read once);
"targets A0 A1 A2 A3"; "exports n1 n2 ..." (signals whose w-parts must span Even(w)); "exit x y" (pairs
to use as exits, in time order, placed after the later of x, y) -- if no exit lines, all same-fibre pairs
are listed.  Reports masks, fibre classes (first/entry/h), the formal targets l_c, zeta_j, the label
parity pattern forced by Lemma B (o), |T*| = K_c - t, and for the chosen exits the joint formal L_near
(exact Dijkstra over sets of computed vectors; labels = formal units, available once their entry exists).
usage: python3 ncheck.py file
"""
import heapq
import itertools
import sys

W = 4


def E(c):
    return 15 ^ (1 << c)


def main(path):
    val, pos, gates, targets, exports, exits = {}, {}, [], [], [], []
    t = 0
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("targets"):
            targets = line.split()[1:]
            continue
        if line.startswith("exports"):
            exports = line.split()[1:]
            continue
        if line.startswith("exit"):
            exits.append(tuple(line.split()[1:3]))
            continue
        lhs, rhs = [s.strip() for s in line.split("=")]
        a, b = [s.strip() for s in rhs.split("+")]
        for x in (a, b):
            if x not in val:
                if x[0] == "w":
                    val[x] = 1 << int(x[1:])
                    pos[x] = -1
                elif x[0] == "z":
                    j = int(x[1:])
                    t = max(t, j)
                    val[x] = 1 << (W + j - 1)
                    pos[x] = -1
                else:
                    raise SystemExit("unknown " + x)
        val[lhs] = val[a] ^ val[b]
        pos[lhs] = len(gates)
        gates.append((lhs, a, b))
    om = lambda v: v & 15
    fm = lambda v: v >> W
    fs = lambda v: "".join("1" if v >> (W + j) & 1 else "." for j in range(t))
    zreads = {}
    for g, a, b in gates:
        for x in (a, b):
            if x[0] == "z":
                zreads[x] = zreads.get(x, 0) + 1
    assert all(v == 1 for v in zreads.values()), ("z read more than once", zreads)
    allv = [val[n] for n in val]
    print("reduced (formal):", len(set(allv)) == len(allv) and 0 not in allv)
    for c, A in enumerate(targets):
        assert om(val[A]) == E(c), ("target", c, A)
    l = [fm(val[A]) for A in targets]
    zeta = [sum(((l[c] >> j) & 1) << c for c in range(4)) for j in range(t)]
    print("l_c:", [fs(val[A]) for A in targets], " zeta:", [format(z, "04b")[::-1] for z in zeta])
    # classes
    seen = {1, 2, 4, 8}
    f1 = h1 = e1 = 0
    entry_of = {}
    for g, a, b in gates:
        va, vb = val[a], val[b]
        if om(va) and om(vb):
            if om(val[g]) == 0:
                raise SystemExit("gate %s is an exit inside the near circuit" % g)
            if om(val[g]) in seen:
                h1 += 1
                kind = "h"
            else:
                f1 += 1
                seen.add(om(val[g]))
                kind = "first"
        else:
            e1 += 1
            kind = "entry(%s)" % (b if om(va) else a)
            entry_of[g] = (b if om(va) else a)
        print("  %-5s = %-5s + %-5s  omega %s  formal %s  %s" % (g, a, b, format(om(val[g]), "04b")[::-1],
                                                              fs(val[g]), kind))
    # cleanliness: ancestors of targets
    anc = set()
    stack = list(targets)
    ops = {g: (a, b) for g, a, b in gates}
    while stack:
        x = stack.pop()
        if x in anc or x not in ops:
            continue
        anc.add(x)
        stack += list(ops[x])
    unclean = [g for g, _, _ in gates if g not in anc]
    tau = len(exports)
    ev = [E(0) ^ E(c) for c in range(1, 4)]
    sp = {0}
    for x in exports:
        sp |= {s ^ om(val[x]) for s in sp}
    print("f1 %d h1 %d e1 %d tau %d near1 %d unclean %s exports-ok %s  K_c-t = |T*| = %d" %
          (f1, h1, e1, tau, f1 + h1 + tau, unclean, all(e in sp for e in ev),
           len(gates) - len(unclean) - sum(1 for g in entry_of if g not in unclean)))
    sigs = ["w0", "w1", "w2", "w3"] + [g for g, _, _ in gates]
    if not exits:
        pairs = []
        for x, y in itertools.combinations(sigs, 2):
            if om(val[x]) == om(val[y]):
                d = fm(val[x] ^ val[y])
                pairs.append((bin(d).count("1"), x, y, fs(val[x] ^ val[y])))
        pairs.sort(reverse=True)
        for p in pairs:
            print("  same fibre: %s ~ %s  diff %s (weight %d)" % (p[1], p[2], p[3], p[0]))
        return
    # joint L_near over formal vectors
    entries_time = sorted((pos[g], 1 << int(entry_of[g][1:]) - 1) for g in entry_of)
    phases = []
    for x, y in exits:
        tm = max(pos[x], pos[y])
        avail = frozenset(m for p, m in entries_time if p <= tm)
        s = fm(val[x] ^ val[y])
        phases.append((s, avail))
        print("  exit %s + %s value %s, labels before: %d" % (x, y, format(s, "b")[::-1], len(avail)))
    start = (0, frozenset())
    dist = {start: 0}
    pq = [(0, 0, ())]
    best = None
    while pq:
        d, k, st = heapq.heappop(pq)
        st = frozenset(st)
        if dist.get((k, st), 99) < d:
            continue
        if k == len(phases):
            best = d
            break
        s, avail = phases[k]
        if s in st:
            nk = (k + 1, st)
            if dist.get(nk, 99) > d:
                dist[nk] = d
                heapq.heappush(pq, (d, k + 1, tuple(st)))
            continue
        pool = st | avail
        for a, b in itertools.combinations(sorted(pool), 2):
            v = a ^ b
            if v and v not in pool:
                ns = st | {v}
                if dist.get((k, ns), 99) > d + 1:
                    dist[(k, ns)] = d + 1
                    heapq.heappush(pq, (d + 1, k, tuple(ns)))
    print("joint L_near %s  |S| %d  beta %s" % (best, len(exits), None if best is None else best - len(exits)))


if __name__ == "__main__":
    main(sys.argv[1])
