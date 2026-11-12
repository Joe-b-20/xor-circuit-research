"""Reviewer's own evaluator (a check, not a search).  Independent of mcheck.py.
Vectors as Python ints; group k (1-based) unit c at bit 4*(k-1)+c.
Prints required-vector check, reducedness, export span, cut-1 classification, exits with their
s-part, and the labels available (entries placed before) with exact least gate count (BFS)."""
import sys, itertools

def tri(c):  # E_c: all units but c
    return 0xF & ~(1 << c)

def pair(c):  # p_c = u_(c-1) + u_c
    return (1 << ((c + 3) % 4)) | (1 << c)

def spanset(vs):
    s = {0}
    for v in vs:
        s = s | {x ^ v for x in s}
    return s

def least(target, avail, lim=5):
    base = frozenset(a for a in avail if a)
    if target in base:
        return 0
    layer = {base}
    for d in range(1, lim + 1):
        new = set()
        for st in layer:
            L = sorted(st)
            for i in range(len(L)):
                for j in range(i + 1, len(L)):
                    v = L[i] ^ L[j]
                    if v == target:
                        return d
                    if v and v not in st:
                        new.add(st | {v})
        layer = new
    return None

def run(L, path):
    sig = {}
    for k in range(L):
        for c in range(4):
            sig["g%d_%d" % (k + 1, c)] = 1 << (4 * k + c)
    gates, exports = [], []
    for raw in open(path):
        ln = raw.split("#")[0].strip()
        if not ln:
            continue
        if ln.startswith("export"):
            exports += ln.split()[1:]
            continue
        n, r = ln.split("=")
        a, b = r.split("+")
        n, a, b = n.strip(), a.strip(), b.strip()
        if n in sig:
            raise SystemExit("redefined " + n)
        sig[n] = sig[a] ^ sig[b]
        gates.append((n, a, b))
    vals = list(sig.values())
    print("gates", len(gates), "tau", len(exports), "cost", len(gates) + len(exports))
    print("reduced (distinct, nonzero):", len(set(vals)) == len(vals) and 0 not in vals)
    need = []
    for k in range(L):
        for c in range(4):
            v = tri(c) << (4 * k)
            if k < L - 1:
                v |= pair(c) << (4 * (k + 1))
            need.append(v)
    print("all required present:", all(v in vals for v in need))
    sp = spanset([sig[e] for e in exports])
    ev = [tri(0) ^ tri(c) for c in range(1, 4)]
    print("export span contains Even(w1)+0:", all(e in sp for e in ev))
    w1 = lambda v: v & 0xF
    seen = {1, 2, 4, 8}
    f1 = h1 = far = 0
    labels = []
    for n, a, b in gates:
        va, vb, v = sig[a], sig[b], sig[n]
        if w1(v):
            if w1(va) and w1(vb):
                if w1(v) in seen:
                    h1 += 1; print("  dup", n)
                else:
                    f1 += 1; seen.add(w1(v))
            else:
                lab = (vb if w1(va) else va) >> 4
                labels.append(lab); print("  entry", n, "label", bin(lab))
        else:
            far += 1
            if w1(va) and w1(vb):
                s = v >> 4
                print("  EXIT", n, "value", bin(s), "labels before", [bin(x) for x in labels],
                      "least gates", least(s, labels))
    tau = len(exports)
    print("f1", f1, "h1", h1, "near1", f1 + h1 + tau, "e1", len(labels), "|P|", far,
          "far1", far + len(labels))

if __name__ == "__main__":
    run(int(sys.argv[1]), sys.argv[2])
