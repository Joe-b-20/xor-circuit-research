"""CHECK (phase 11, main agent): explicit repairs of whole-block cancellations, and the specified examples.

Direct construction and evaluation of specified circuits only: no SAT, no search, no enumeration of circuits,
no least-gate computation. Every repaired circuit is built explicitly and verified (computes the map, has no
whole-block cancellation). Definitions are in REPAIR.md.

An *event* is a gate a + b with a block c such that pi_c(a) = pi_c(b) != 0 (the block is cancelled whole).
Sequential repair: process the original gates in order; a non-event gate is copied with its operands mapped
(a value already present is reused); an event e is replaced by a gadget that computes val(e) without events
from nodes already present:
  direct     - a chain over the inputs of val(e), each step adding a new input (prefixes reused if present);
  projection - P = zero the cancelled blocks C(e); build P(u) for the ancestors u of e's operands
               recursively (P(u) = u when u has no content on C(e); reuse when the value is present; drop
               zero), then val(e) = P(a) + P(b);
  best       - per event, the gadget with fewer new gates.
At the end dead gates (not ancestors of an output) are pruned. Reported: G, events, G' and the overhead
sigma = G' - G, so that G >= B - sigma for the event-free baseline B (84 for MixColumns, 30 for Q_3).
usage: python3 repair.py [KSTE_FILE:LINE ...]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ST, "compose", "compat"))


def values(n, gates):
    v = [1 << i for i in range(n)]
    for a, b in gates:
        v.append(v[a] ^ v[b])
    return v


def cancelled(va, vb, bmasks):
    return [c for c, m in enumerate(bmasks) if va & m and (va & m) == (vb & m)]


class Builder:
    def __init__(self, n, bmasks):
        self.n, self.bm = n, bmasks
        self.gates, self.vals = [], [1 << i for i in range(n)]
        self.where = {v: i for i, v in enumerate(self.vals)}
        self.ops = {}

    def add(self, a, b):
        v = self.vals[a] ^ self.vals[b]
        if v in self.where:
            return self.where[v], 0
        assert v != 0
        assert not cancelled(self.vals[a], self.vals[b], self.bm), "gadget gate is an event"
        self.gates.append((a, b))
        self.vals.append(v)
        idx = len(self.vals) - 1
        self.where[v] = idx
        self.ops[idx] = (a, b)
        return idx, 1

    def direct(self, target):
        bits = [i for i in range(self.n) if target >> i & 1]
        acc, cost = bits[0], 0
        for i in bits[1:]:
            acc, c = self.add(acc, i)
            cost += c
        return acc, cost

    def projection(self, a, b, keep):
        memo, cost = {}, [0]

        def proj(u):
            if u in memo:
                return memo[u]
            pv = self.vals[u] & keep
            if pv == 0:
                r = None
            elif pv == self.vals[u]:
                r = u
            elif pv in self.where:
                r = self.where[pv]
            else:
                p1, p2 = (proj(x) for x in self.ops[u])
                if p1 is None or p2 is None:
                    r = p1 if p2 is None else p2
                else:
                    r, c = self.add(p1, p2)
                    cost[0] += c
            memo[u] = r
            return r
        pa, pb = proj(a), proj(b)
        if pa is None or pb is None:
            return (pa if pb is None else pb), cost[0]
        r, c = self.add(pa, pb)
        return r, cost[0] + c


def trial(n, bmasks, gates, method):
    """Gadget costs need a scratch builder to compare; rebuild deterministically per choice."""
    vals = values(n, gates)
    B = Builder(n, bmasks)
    m = {i: i for i in range(n)}
    events, wsum = 0, 0
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        C = cancelled(vals[a], vals[b], bmasks)
        if not C:
            m[g], _ = B.add(m[a], m[b])
            continue
        events += 1
        wsum += bin(vals[g]).count("1") - 2
        keep = ((1 << n) - 1) ^ sum(bmasks[c] for c in C)
        if method == "direct":
            m[g], _ = B.direct(vals[g])
        elif method == "projection":
            m[g], _ = B.projection(m[a], m[b], keep)
        else:
            import copy
            B1 = copy.deepcopy(B)
            _, c1 = B1.direct(vals[g])
            B2 = copy.deepcopy(B)
            _, c2 = B2.projection(m[a], m[b], keep)
            m[g], _ = (B.direct(vals[g]) if c1 <= c2 else B.projection(m[a], m[b], keep))
        assert B.vals[m[g]] == vals[g]
    return B, events, wsum


def finish(B, rows):
    keep, st = set(), [B.where[r] for r in rows]
    while st:
        x = st.pop()
        if x < B.n or x in keep:
            continue
        keep.add(x)
        st.extend(B.ops[x])
    for x in keep:
        a, b = B.ops[x]
        assert not cancelled(B.vals[a], B.vals[b], B.bm)
    return len(keep)


def shared_cone(n, gates, rows, bmasks):
    """Theorem P quantities for each event whose ancestors contain no event: s_e = gate ancestors u of e carrying
    content on C(e), not dominated by e (a path from u to an output avoids e), whose projection is nonzero and
    is not the value of any node other than e (definition R2 of review/REVIEW.md); delta_e = 1 if both operands have content off C(e). Returns [(e, w(e)-2, s_e+delta_e-1)]."""
    vals = values(n, gates)
    N = len(vals)
    present = set(vals)
    isev = {n + i for i, (a, b) in enumerate(gates) if cancelled(vals[a], vals[b], bmasks)}
    readers = [[] for _ in range(N)]
    for i, (a, b) in enumerate(gates):
        readers[a].append(n + i)
        readers[b].append(n + i)
    outs = {vals.index(r, n) for r in rows}
    res = []
    for e in sorted(isev):
        anc, st = set(), list(gates[e - n])
        while st:
            x = st.pop()
            if x in anc:
                continue
            anc.add(x)
            if x >= n:
                st.extend(gates[x - n])
        if anc & isev:
            continue
        a, b = gates[e - n]
        Cm = sum(bmasks[c] for c in cancelled(vals[a], vals[b], bmasks))
        keep = ((1 << n) - 1) ^ Cm
        ok = {}                      # reaches an output without passing through e

        def reach(v):
            if v in ok:
                return ok[v]
            ok[v] = False
            r = v != e and (v in outs or any(reach(g) for g in readers[v] if g != e))
            ok[v] = r
            return r
        sys.setrecursionlimit(100000)
        others = present - {vals[e]}                     # reading R2 of the review: val(e) is not "present"
        s = sum(1 for u in anc if u >= n and vals[u] & Cm and reach(u) and (vals[u] & keep)
                and (vals[u] & keep) not in others)
        d = int(bool(vals[a] & keep) and bool(vals[b] & keep))
        res.append((e, bin(vals[e]).count("1") - 2, s + d - 1))
    return res


def report(name, n, gates, rows, bmasks, base):
    vals = values(n, gates)
    assert all(r in vals[n:] for r in rows), name
    out, sig = [], []
    for method in ("direct", "projection", "best"):
        B, ev, wsum = trial(n, bmasks, gates, method)
        Gp = finish(B, rows)
        sig.append(Gp - len(gates))
        out.append("%s %d (sigma %+d)" % (method, Gp, Gp - len(gates)))
    best = min(sig)
    sc = shared_cone(n, gates, rows, bmasks)
    print("%s: G %d, events %d, sum(w-2) %d | %s | so G >= %d - min sigma = %d (event-free baseline %d)"
          % (name, len(gates), ev, wsum, ", ".join(out), base, base - best, base))
    if ev and len(sc) == ev:
        print("    Theorem P per event (node, w-2, s+delta-1): %s; sum of min = %d >= measured projection sigma %d"
              % (sc, sum(min(w, t) for _, w, t in sc), sig[1]))
    elif sc:
        print("    Theorem P for the %d events with event-free ancestry (node, w-2, s+delta-1): %s" % (len(sc), sc[:6]))


def prefix_family(n):
    # inputs x = 0, y_i = i; p_i = x + y_1 + ... + y_i; T = p_n + x
    g = [(0, 1)]
    for i in range(2, n + 1):
        g.append((n + i - 1, i))
    g.append((n + n, 0))
    N = n + 1
    vals = values(N, g)
    rows = vals[N:]
    assert len(set(vals)) == len(vals)
    report("prefix family n=%d (singleton blocks)" % n, N, g, rows, [1 << i for i in range(N)], 2 * n - 1)


def mc_restriction_example():
    """User's example: x = x_(0,7), y = x_(1,0), z = x_(2,0); a = x+y, b = a+z, e = b+x = y+z; e feeds output
    (0,0) = e + x_(3,0) + x_(0,7) + x_(1,7); the other outputs by direct chains (values reused)."""
    from clib import ROWS, bm
    w = lambda c, j: 8 * c + j
    B = Builder(32, [bm(j) for j in range(8)])
    B.bm = []                                  # allow the event in this specified circuit
    a, _ = B.add(w(0, 7), w(1, 0))
    b, _ = B.add(a, w(2, 0))
    e, _ = B.add(b, w(0, 7))
    t, _ = B.add(e, w(3, 0))
    t, _ = B.add(t, w(0, 7))
    y00, _ = B.add(t, w(1, 7))
    assert B.vals[y00] == ROWS[(0, 0)]
    for k in sorted(ROWS):
        if k != (0, 0):
            B.direct(ROWS[k])
    rows = list(ROWS.values())
    n, gates = 32, B.gates
    vals = values(n, gates)
    assert all(r in vals[n:] for r in rows) and len(set(vals)) == len(vals) and 0 not in vals
    live, st = set(), [vals.index(r, n) for r in rows]
    while st:
        x = st.pop()
        if x < n or x in live:
            continue
        live.add(x)
        st.extend(gates[x - n])
    bmasks = [bm(j) for j in range(8)]
    evs = [n + i for i, (p, q) in enumerate(gates) if cancelled(vals[p], vals[q], bmasks)]
    # ACCOUNT section 1: zero block 7, process in order, removed if image is 0, an input image, or earlier image
    keep = ((1 << 32) - 1) ^ bm(7)
    seen = {0} | {(1 << i) & keep for i in range(32)}
    removed_e = None
    for i in range(len(gates)):
        im = vals[n + i] & keep
        if n + i == e:
            removed_e = im in seen
        seen.add(im)
    print("MixColumns restriction example: G %d, reduced, fully live %s, events %s (e = node %d, value %s), "
          "e removed when block 7 is zeroed: %s (its image equals the image of b = node %d: %s)"
          % (len(gates), len(live) == len(gates), evs, e, "x_(1,0)+x_(2,0)" if vals[e] == (1 << w(1, 0)) | (1 << w(2, 0)) else "?",
             removed_e, b, (vals[b] & keep) == (vals[e] & keep)))


def weights():
    from clib import ROWS
    from collections import Counter
    print("MixColumns row weights by sheet:", {j: sorted(Counter(bin(ROWS[(c, j)]).count("1") for c in range(4)).items())
                                              for j in range(8)})


def mc(spec):
    from clib import ROWS, bm, load
    g = [tuple(x) for x in json.load(open(spec))] if spec.endswith(".json") else load(spec)
    report("MixColumns " + os.path.basename(spec), 32, g, list(ROWS.values()), [bm(j) for j in range(8)], 84)


def q3():
    ls = [l.split("#")[0].strip() for l in open(os.path.join(ST, "rotation", "circuits", "q3_28.txt"))]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    E = lambda c: 15 ^ (1 << c)
    S = lambda c: (1 << c) | (1 << ((c + 1) % 4))
    rows = [(E(c) << (4 * j)) | (S(c) << (4 * ((j - 1) % 3))) for j in range(3) for c in range(4)]
    report("Q_3 (q3_28)", n, g, rows, [15 << (4 * j) for j in range(3)], 30)


if __name__ == "__main__":
    weights()
    for n in (2, 3, 5, 8, 12):
        prefix_family(n)
    mc_restriction_example()
    q3()
    for s in ["r88", "r89", os.path.join(ST, "cancel", "witness", "witness_mc_block.json")] + sys.argv[1:]:
        mc(s)
