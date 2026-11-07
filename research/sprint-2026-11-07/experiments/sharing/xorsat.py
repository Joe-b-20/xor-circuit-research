"""Generic exact XOR-circuit SAT: n inputs, target masks (ints over n bits), m gates.
Value-set encoding (same as sat/sat87.py, generalised to any n/targets, no kept set).
Sound and complete for the question "is there a circuit with <= m XOR gates computing all targets"
(distinctness is only a pruning constraint: if a circuit with <= m gates exists, one with exactly m
distinct non-input values exists unless INPUTS u V would be XOR-closed, i.e. a whole subspace, which
needs 2^n - 1 - n values; we always have m < 2^n - 1 - n).

Run as a child:  python3 xorsat.py req.json   -> prints one json line.
"""
import json
import sys
import time


def encode(n, targets, m, distinct=True, symbreak=True):
    const = [1 << j for j in range(n)]
    nc = n
    tset = set(targets)
    need = [t for t in sorted(tset) if t not in set(const)]
    nv = [0]

    def new():
        nv[0] += 1
        return nv[0]

    cl = []
    bit, A, B, C = [], [], [], []
    for j in range(m):
        w = nc + j
        a = [new() for _ in range(w)]
        b = [new() for _ in range(w)]
        c = [new() for _ in range(w)]
        A.append(a); B.append(b); C.append(c)
        for sel in (a, b):
            cl.append(sel[:])
            for x in range(w):
                for y in range(x + 1, w):
                    cl.append([-sel[x], -sel[y]])
        cl.append([-c[0], a[0]]); cl.append([c[0], -a[0]])
        for u in range(1, w):
            cl.append([-c[u], c[u - 1], a[u]])
            cl.append([c[u], -c[u - 1]])
            cl.append([c[u], -a[u]])
        cl.append([-b[0]])
        for u in range(1, w):
            cl.append([-b[u], c[u - 1]])
        g = [new() for _ in range(n)]
        bit.append(g)
        for i in range(n):
            Ai, Bi = new(), new()
            for sel, X in ((a, Ai), (b, Bi)):
                terms = []
                for u in range(w):
                    if u < nc:
                        if (const[u] >> i) & 1:
                            terms.append(sel[u])
                    else:
                        t = new()
                        bu = bit[u - nc][i]
                        cl += [[-t, sel[u]], [-t, bu], [t, -sel[u], -bu]]
                        terms.append(t)
                cl.append([-X] + terms)
                for t in terms:
                    cl.append([X, -t])
            cl += [[-g[i], Ai, Bi], [-g[i], -Ai, -Bi], [g[i], -Ai, Bi], [g[i], Ai, -Bi]]
        if distinct:
            for u in range(w):
                if u < nc:
                    v = const[u]
                    cl.append([(-g[i] if (v >> i) & 1 else g[i]) for i in range(n)])
                else:
                    diff = []
                    for i in range(n):
                        d = new()
                        bu = bit[u - nc][i]
                        cl += [[-d, g[i], bu], [-d, -g[i], -bu]]
                        diff.append(d)
                    cl.append(diff)
            # also: no gate equals 0 (would be a == b); already excluded by a != b via first<second
        if symbreak and j > 0:
            wprev = nc + j - 1
            for u in range(wprev):
                cl.append([b[wprev], -c[u], C[j - 1][u]])
    for t in need:
        es = []
        for j in range(m):
            e = new()
            for i in range(n):
                cl.append([-e, bit[j][i] if (t >> i) & 1 else -bit[j][i]])
            es.append(e)
        cl.append(es)
    meta = {"n": n, "m": m, "A": A, "B": B, "bit": bit, "const": const}
    return cl, nv[0], meta


def decode(model, meta):
    ms = set(x for x in model if x > 0)
    vals = list(meta["const"])
    order = []
    for j in range(meta["m"]):
        a = [u for u in range(len(meta["A"][j])) if meta["A"][j][u] in ms]
        b = [u for u in range(len(meta["B"][j])) if meta["B"][j][u] in ms]
        assert len(a) == 1 and len(b) == 1
        va, vb = vals[a[0]], vals[b[0]]
        v = sum(1 << i for i in range(meta["n"]) if meta["bit"][j][i] in ms)
        assert v == va ^ vb
        order.append((v, va, vb))
        vals.append(v)
    return order


def verify(n, targets, order):
    avail = set(1 << j for j in range(n))
    for v, a, b in order:
        assert a in avail and b in avail and a != b and a ^ b == v
        avail.add(v)
    for t in targets:
        assert t in avail
    return True


if __name__ == "__main__":
    req = json.load(open(sys.argv[1]))
    from pysat.solvers import Solver
    t0 = time.time()
    cl, nv, meta = encode(req["n"], req["targets"], req["m"], req.get("distinct", True), req.get("symbreak", True))
    t1 = time.time()
    s = Solver(name=req.get("solver", "cadical195"), bootstrap_with=cl)
    r = s.solve()
    t2 = time.time()
    out = {"result": "SAT" if r else "UNSAT", "nvars": nv, "nclauses": len(cl),
           "enc_secs": round(t1 - t0, 2), "solve_secs": round(t2 - t1, 2)}
    if r:
        order = decode(s.get_model(), meta)
        verify(req["n"], req["targets"], order)
        out["gates"] = order
    print(json.dumps(out))
