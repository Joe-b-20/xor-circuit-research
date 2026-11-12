"""Check of hand-built mirror-chain circuits (MC_l) and their cut-1 accounting.  A check, not a search.

Circuit file: lines "name = a + b"; inputs gK_C = unit C of group w^K (K = 1..l, C = 0..3);
"export name" lines list the export signals (tau = their number).
Vectors: group K occupies bits 4(K-1)..4(K-1)+3.
Reports: required vectors R^k_i present, export span contains Even(w^1)+0, reducedness, cost,
cut-1 classes (first gates f1, entries e1 with labels in time order, non-entry duplicates h1, exits,
ordinary far gates), near1 = f1+h1+tau, far1 = |P|+e1, each exit value with L_near (least number of XOR
gates computing it from the labels of entries placed before the exit, exact by breadth-first closure,
single exit), tau_min (least number of labels whose span contains Even(w^2)+0) and sigma = e1 - tau_min.
usage: python3 mcheck.py L circuit.txt
"""
import itertools
import sys


def E(c):
    return 15 ^ (1 << c)


def P(c):
    return (1 << ((c - 1) % 4)) | (1 << c)


def span(vs):
    s = {0}
    for v in vs:
        s |= {x ^ v for x in s}
    return s


def rank(vs):
    return len(span(vs)).bit_length() - 1


def lnear(target, labels, limit=4):
    """least number of gates producing `target` from the label set (exact, gates <= limit)."""
    base = frozenset(labels)
    if target in base:
        return 0
    frontier = {base}
    for d in range(1, limit + 1):
        nxt = set()
        for st in frontier:
            for a, b in itertools.combinations(sorted(st), 2):
                v = a ^ b
                if v == target:
                    return d
                if v and v not in st:
                    nxt.add(st | {v})
        frontier = nxt
    return None


def main(L, path):
    val, order, kind, exports = {}, [], {}, []
    for k in range(1, L + 1):
        for c in range(4):
            val["g%d_%d" % (k, c)] = 1 << (4 * (k - 1) + c)
    gates = []
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("export"):
            exports += line.split()[1:]
            continue
        lhs, rhs = [t.strip() for t in line.split("=")]
        a, b = [t.strip() for t in rhs.split("+")]
        assert a in val and b in val, line
        val[lhs] = val[a] ^ val[b]
        gates.append((lhs, a, b))
    allv = list(val.values())
    reduced = len(set(allv)) == len(allv) and 0 not in allv
    req = []
    for k in range(1, L + 1):
        for c in range(4):
            v = E(c) << (4 * (k - 1))
            if k < L:
                v |= P(c) << (4 * k)
            req.append(v)
    missing = [hex(v) for v in req if v not in allv]
    ev1 = [E(c) ^ E(0) for c in range(1, 4)]  # basis of Even(w^1)
    sp = span([val[x] for x in exports])
    exp_ok = all(e in sp for e in ev1)
    tau = len(exports)
    print("gates", len(gates), "tau", tau, "cost", len(gates) + tau, "reduced", reduced,
          "missing", missing, "exports span Even(w^1)+0:", exp_ok)
    om = lambda v: v & 15
    seen = set(om(val["g1_%d" % c]) for c in range(4))
    f1 = h1 = 0
    labels, exits, far = [], [], 0
    for name, a, b in gates:
        va, vb, v = val[a], val[b], val[name]
        if om(v):
            if om(va) and om(vb):
                if om(v) in seen:
                    h1 += 1
                    print("  h  ", name)
                else:
                    f1 += 1
                    seen.add(om(v))
            else:
                pi = vb if om(va) else va
                labels.append(pi >> 4)
                print("  entry %-6s label %s" % (name, format(pi >> 4, "0%db" % (4 * (L - 1)))[::-1]))
        else:
            far += 1
            if om(va) and om(vb):
                s = v >> 4
                ln = lnear(s, labels)
                exits.append((name, s, ln))
                print("  exit %-6s value %s  L_near %s  (labels before: %d)"
                      % (name, format(s, "0%db" % (4 * (L - 1)))[::-1], ln, len(labels)))
    e1 = len(labels)
    near1, far1 = f1 + h1 + tau, far + e1
    ev2 = [(E(c) ^ E(0)) for c in range(1, 4)]  # Even(w^2)+0 basis, in label coordinates
    tmin = None
    for r in range(1, e1 + 1):
        if any(all(e in span(sub) for e in ev2) for sub in itertools.combinations(labels, r)):
            tmin = r
            break
    print("f1 %d h1 %d tau %d near1 %d | e1 %d |P| %d far1 %d | sum %d" %
          (f1, h1, tau, near1, e1, far, far1, near1 + far1))
    beta = sum(x[2] for x in exits) - len(exits) if exits else 0
    print("exits %d  beta(sum of single L_near - |S|) %d  tau_min %s sigma %s" %
          (len(exits), beta, tmin, None if tmin is None else e1 - tmin))
    print("SB (near1-10 >= beta):", near1 - 10 >= beta,
          "| SB' (near1-10 >= beta - sigma):", None if tmin is None else near1 - 10 >= beta - (e1 - tmin))


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
