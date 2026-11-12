"""Check of ONE explicit near side of problem (N) with concrete labels -- a check, not a search.

Usage: python3 sbcheck.py circuit.txt
circuit.txt: as for ncheck.py (gates over w0..w3, z1..zt; "targets", "exports", "exit x y"), plus
"label zj <w2 bits> <w3 bits>" lines giving the far label lambda_j (bit strings, unit 0 first).
Checks: each target = (E_c(w^1) | p_c(w^2), 0 on w^3) in actual values; exports pure even spanning
Even(w^1); all actual near values + label values distinct and nonzero; exit values new; then
L_near (exact Dijkstra, labels available once their entry exists, joint over exits), beta, tau_min,
sigma, near1, and whether SB' (near1 - 10 >= beta - sigma) holds.
"""
import heapq
import itertools
import sys


def bits(s):
    return sum(1 << i for i, ch in enumerate(s) if ch == "1")


def span(vs):
    s = {0}
    for v in vs:
        s |= {x ^ v for x in s}
    return s


def main(path):
    lab, gates, targets, exports, exits = {}, [], [], [], []
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        tok = line.split()
        if tok[0] == "label":
            lab[tok[1]] = bits(tok[2]) | (bits(tok[3]) << 4)
        elif tok[0] == "targets":
            targets = tok[1:]
        elif tok[0] == "exports":
            exports = tok[1:]
        elif tok[0] == "exit":
            exits.append((tok[1], tok[2]))
        else:
            lhs, rhs = [s.strip() for s in line.split("=")]
            a, b = [s.strip() for s in rhs.split("+")]
            gates.append((lhs, a, b))
    # actual values: (w1 part 4 bits) | (U part 8 bits) << 4
    val, pos = {}, {}
    for c in range(4):
        val["w%d" % c] = 1 << c
        pos["w%d" % c] = -1
    for z, v in lab.items():
        val[z] = v << 4
        pos[z] = -1
    entry_time = {}
    for i, (g, a, b) in enumerate(gates):
        val[g] = val[a] ^ val[b]
        pos[g] = i
        for x in (a, b):
            if x in lab:
                entry_time[x] = i
    E = lambda c: 15 ^ (1 << c)
    P = lambda c: (1 << ((c - 1) % 4)) | (1 << c)
    ok = all(val[A] == (E(c) | (P(c) << 4)) for c, A in enumerate(targets))
    print("targets correct:", ok)
    om = lambda v: v & 15
    ev = [E(0) ^ E(c) for c in range(1, 4)]
    sp = span([val[x] for x in exports])
    print("exports pure even, span Even(w^1)+0:", all(e in sp for e in ev) and all(val[x] >> 4 == 0 for x in exports))
    near = [val["w%d" % c] for c in range(4)] + [val[g] for g, _, _ in gates]
    labs = [v << 4 for v in lab.values()]
    allv = near + labs
    print("near values + label signals distinct and nonzero:", len(set(allv)) == len(allv) and 0 not in allv)
    seen = {1, 2, 4, 8}
    f1 = h1 = 0
    for g, a, b in gates:
        if a in lab or b in lab:
            continue
        if om(val[g]) in seen:
            h1 += 1
        else:
            f1 += 1
            seen.add(om(val[g]))
    tau = len(exports)
    near1 = f1 + h1 + tau
    e1 = len(entry_time)
    U = [v for v in lab.values()]
    ev2 = [P(c) for c in range(1, 4)]
    tmin = next(r for r in range(1, e1 + 1)
                if any(all(e in span(sub) for e in ev2) for sub in itertools.combinations(U, r)))
    sigma = e1 - tmin
    phases = []
    for x, y in exits:
        assert om(val[x]) == om(val[y]) and om(val[x]), "not an exit"
        s = (val[x] ^ val[y]) >> 4
        assert s << 4 not in allv, "exit value repeats a signal"
        tm = max(pos[x], pos[y])
        avail = frozenset(lab[z] for z, t in entry_time.items() if t <= tm)
        phases.append((s, avail))
        print("exit %s + %s value w2:%s w3:%s" % (x, y, format(s & 15, "04b")[::-1], format(s >> 4, "04b")[::-1]))
    dist = {(0, frozenset()): 0}
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
            if dist.get((k + 1, st), 99) > d:
                dist[(k + 1, st)] = d
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
    beta = best - len(exits)
    print("f1 %d h1 %d tau %d near1 %d e1 %d tau_min %d sigma %d L_near %d |S| %d beta %d"
          % (f1, h1, tau, near1, e1, tmin, sigma, best, len(exits), beta))
    print("SB' (near1-10 >= beta-sigma):", near1 - 10 >= beta - sigma)


if __name__ == "__main__":
    main(sys.argv[1])
