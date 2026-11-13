"""CHECK (phase 12, main agent): visible cancellations, output windows, and explicit off-family repairs.

Direct evaluation of specified objects only: the eight MixColumns output windows (a given 8-vertex graph), the
specified circuits named below, and explicit constructions. No SAT, no search, no enumeration of circuits, no
least-gate computation. Definitions and proofs are in VISIBLE.md; this program supports them, it does not
replace them.

For a circuit C: an event is a gate a + b with a block c such that pi_c(a) = pi_c(b) != 0. J(v) is the set of
sheets having a designated output reachable from v along a path whose nodes after v are not events. F = events
with J nonempty (visible), E \\ F the hidden events, R = non-event gates with J nonempty (retained), Q = the
other non-event gates. The repair: direct chains for F (block pieces, off-own part first), then R in order.
usage: python3 visible.py [KSTE_FILE:LINE ...]
"""
import json
import os
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ST, "compose", "compat"))
from clib import ROWS, bm, load  # noqa: E402

BM = [bm(j) for j in range(8)]
SHEET = {v: j for (c, j), v in ROWS.items()}
W = {}


def blocks(v):
    return frozenset(j for j in range(8) if v & BM[j])


def wt(v):
    return bin(v).count("1")


def cancelled(va, vb):
    return [c for c in range(8) if va & BM[c] and (va & BM[c]) == (vb & BM[c])]


def windows():
    for j in range(8):
        sups = {blocks(ROWS[(c, j)]) for c in range(4)}
        assert len(sups) == 1
        W[j] = sups.pop()
    print("windows:", {j: sorted(W[j]) for j in range(8)})
    print("row weights per block (block: weights over the four rows):",
          {j: {b: sorted(wt(ROWS[(c, j)] & BM[b]) for c in range(4)) for b in sorted(W[j])} for j in range(8)})
    adj = {a: set() for a in range(8)}
    for j in range(8):
        for a, b in combinations(sorted(W[j]), 2):
            adj[a].add(b)
            adj[b].add(a)
    print("co-occurrence graph:", sorted((a, b) for a in adj for b in adj[a] if a < b))
    for j in range(8):
        ext = [c for c in range(8) if c not in W[j] and W[j] <= adj[c]]
        print("  W_%d %s: %s" % (j, sorted(W[j]), "maximal clique" if not ext else "extends to a clique by %s" % ext))
    cliques = [{0, 1, 7}, {1, 2, 7}, {2, 3, 7}, {3, 4, 7}, {4, 5}, {5, 6}, {6, 7}]   # listed by hand (VISIBLE 2)
    for K in cliques:
        assert all(b in adj[a] for a, b in combinations(sorted(K), 2))
        assert not [c for c in range(8) if c not in K and K <= adj[c]]
    assert all(any(e <= K for K in cliques) for a in adj for b in adj[a] for e in [{a, b}])
    print("  hand-listed maximal cliques verified (cliques, maximal, covering every edge):", [sorted(K) for K in cliques])
    inter = {(j, k): sorted(W[j] & W[k]) for j, k in combinations(range(8), 2) if W[j] & W[k]}
    print("pairwise window intersections:", inter, "| largest", max(len(v) for v in inter.values()))
    tri = {tuple(t): sorted(W[t[0]] & W[t[1]] & W[t[2]]) for t in combinations(range(8), 3)
           if W[t[0]] & W[t[1]] & W[t[2]]}
    assert all(v == [7] for v in tri.values())
    print("nonempty triple intersections are all {7}:", len(tri), "triples")
    assert not any(j in W[k] and k in W[j] for j, k in combinations(range(8), 2))
    print("own-block property: no two sheets j != k with j in W_k and k in W_j (checked)")
    return adj


def kappa_plan(v, Jf):
    """in-family gate count of the chain for v and the plan (A, t, pieces)."""
    B = blocks(v)
    A = [j for j in sorted(Jf) if j in B]
    assert len(A) <= 1
    t = 3 in Jf and 2 in B and 7 in B
    wA = wt(v & BM[A[0]]) if A else 0
    wO = wt(v) - wA
    if t:
        inf = wA + 1 if wA else 1
    elif wA:
        inf = wA if wO else wA - 1
    else:
        inf = 0
    return inf, A, t


def analyse(name, gates, adj):
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    N, G = len(vals), len(gates)
    assert all(r in vals[n:] for r in ROWS.values()), name
    reduced = len(set(vals)) == N and 0 not in vals
    outnode = {v: vals.index(v, n) for v in ROWS.values()}
    desig = {o: SHEET[v] for v, o in outnode.items()}
    ev = {n + i for i, (a, b) in enumerate(gates) if cancelled(vals[a], vals[b])}
    readers = [[] for _ in range(N)]
    for i, (a, b) in enumerate(gates):
        readers[a].append(n + i)
        readers[b].append(n + i)
    J = [set() for _ in range(N)]
    for v in range(N - 1, -1, -1):
        s = {desig[v]} if v in desig else set()
        for g in readers[v]:
            if g not in ev:
                s |= J[g]
        J[v] = s
    ids = range(n, N)
    F = [g for g in ids if g in ev and J[g]]
    Eh = [g for g in ids if g in ev and not J[g]]
    R = [g for g in ids if g not in ev and J[g]]
    Q = [g for g in ids if g not in ev and not J[g]]
    live = set()
    st = list(outnode.values())
    while st:
        x = st.pop()
        if x < n or x in live:
            continue
        live.add(x)
        st.extend(gates[x - n])
    # Lemma S: support of a visible event or retained gate lies in the window of every sheet it reaches
    assert all(blocks(vals[v]) <= W[j] for v in F + R for j in J[v]), name
    # window credit: operands of visible events whose support lies in no window
    inwin = lambda v: any(blocks(v) <= W[j] for j in range(8))
    Nset = set()
    for f in F:
        for op in gates[f - n]:
            if not inwin(vals[op]):
                assert op >= n and (op in Q or op in Eh), name
                Nset.add(op)
    three = [f for f in F if len(blocks(vals[f])) == 3]
    assert all(any(not inwin(vals[op]) for op in gates[f - n]) for f in three), name
    # explicit repair: chains for F (off-own pieces first), then R in original order; no normalisation
    new, nv = [], [1 << i for i in range(n)]
    owner = {}

    def add(a, b, f=None):
        new.append((a, b))
        nv.append(nv[a] ^ nv[b])
        if f is not None:
            owner[len(nv) - 1] = f
        return len(nv) - 1

    def piece(v, b, f):
        bits = [i for i in range(n) if (v >> i) & 1 and (1 << i) & BM[b]]
        acc = bits[0]
        for i in bits[1:]:
            acc = add(acc, i, f)
        return acc
    m, kap, K = {i: i for i in range(n)}, {}, 0
    for f in F:
        v = vals[f]
        inf, A, t = kappa_plan(v, J[f])
        kap[f] = inf - 1
        K += wt(v) - 1
        Bf = blocks(v)
        if t:
            p2, p7 = piece(v, 2, f), piece(v, 7, f)
            node = add(add(piece(v, 3, f), p2, f), p7, f) if A else add(p2, p7, f)
        else:
            off = None
            for b in sorted(Bf - set(A)):
                p = piece(v, b, f)
                off = p if off is None else add(off, p, f)
            if A:
                own = piece(v, A[0], f)
                node = own if off is None else add(off, own, f)
            else:
                node = off
        assert nv[node] == v
        m[f] = node
    for g in R:
        a, b = gates[g - n]
        m[g] = add(m[a], m[b])
    Gp = len(new)
    assert Gp == G - len(ev) - len(Q) + K, name
    nout = {m[o]: SHEET[v] for v, o in outnode.items()}
    assert all(nv[o] in SHEET and SHEET[nv[o]] == j for o, j in nout.items()) and len(nout) == 32
    assert not any(cancelled(nv[a], nv[b]) for a, b in new), name + ": repaired circuit has an event"
    anc = {j: set() for j in range(8)}
    for o, j in nout.items():
        st = [o]
        while st:
            x = st.pop()
            if x < n or x in anc[j]:
                continue
            anc[j].add(x)
            st.extend(new[x - n])
    fam = {j: {g for g in anc[j] if nv[g] & BM[j]} for j in range(8)}
    fam[3] |= {g for g in anc[3] if nv[g] & BM[2] and nv[g] & BM[7]}
    assert all(not (fam[j] & fam[k]) for j, k in combinations(range(8), 2)), name + ": families overlap"
    sizes = [len(fam[j]) for j in range(8)]
    union = set().union(*fam.values())
    U = Gp - len(union)
    assert sum(sizes) >= 83 and all(s >= 10 for s in sizes) and sizes[3] >= 13
    for f in F:
        mine = [x for x, o in owner.items() if o == f]
        assert len(mine) == wt(vals[f]) - 1
        assert sum(1 for x in mine if x in union) == kap[f] + 1, (name, f)
    rowvalued = sum(1 for x in owner if nv[x] in SHEET and x not in nout)
    persheet = [(len(fam[j] - set(owner)), len(fam[j] & set(owner))) for j in range(8)]
    for f in F:   # the in-family chain gates of f lie in the single family of its own block (F_3 when t)
        inf, A, t = kappa_plan(vals[f], J[f])
        home = 3 if t else (A[0] if A else None)
        mine = {x for x, o in owner.items() if o == f}
        assert all((mine & fam[j]) == set() for j in range(8) if j != home)
    b84 = 84 + len(Eh) + len(Q) - sum(wt(vals[f]) - 2 for f in F)
    b83 = 83 + len(Eh) + len(Q) - sum(kap.values())
    bU = 83 + U + len(ev) + len(Q) - K
    print("%s: G %d, reduced %s, fully live %s | events %d: visible F %d, hidden %d | R %d, Q %d | "
          "window-credit operands %d" % (name, G, reduced, len(live) == G, len(ev), len(F), len(Eh), len(R), len(Q),
                                          len(Nset)))
    for f in F[:8]:
        a, b = gates[f - n]
        print("    f=%d %s w=%d B=%s C=%s J=%s kappa=%d operands in %s" % (
            f, "output" if f in desig else "internal", wt(vals[f]), sorted(blocks(vals[f])),
            cancelled(vals[a], vals[b]), sorted(J[f]), kap[f],
            ["R" if x in R else "Q" if x in Q else "Eh" if x in Eh else "F" if x in F else "in" for x in (a, b)]))
    if len(F) > 8:
        print("    ... %d visible events, kappa values %s" % (len(F), sorted(kap.values())))
    print("    repaired: G' %d = G - |E| - |Q| + K (K %d), event-free; families %s (sum %d), gates in no family "
          "U %d (of them chain gates %d); chain gates with a row value but not designated: %d" % (
              Gp, K, sizes, sum(sizes), U, sum(1 for x in owner if x not in union), rowvalued))
    L01 = {g for g in anc[0] | anc[1] if nv[g] & (BM[0] | BM[1])}
    X = L01 - fam[0] - fam[1]
    assert not (X & union) and len(L01) >= 21 and Gp >= 84 + (U - len(X))
    xf = {f: sum(1 for x, o in owner.items() if o == f and x in X) for f in F}
    b84V = 84 + len(Eh) + len(Q) - sum(kap[f] + xf[f] for f in F)
    assert G >= b84V
    print("    84 form: |L_01| %d, X %d (chain gates in X %d), G' >= 84 + |U \\ X| = %d; class-form bound %d" % (
        len(L01), len(X), sum(xf.values()), 84 + U - len(X), b84V))
    if F:
        print("    per family (retained gates, chain gates):", persheet)
    print("    class-form bounds: 84-form %d, 83-form %d | this circuit: G >= 83 + U + |E| + |Q| - K = %d" % (
        b84, b83, bU))
    assert G >= max(b84, b83, bU)


def tail_family(n):
    """General map (singleton blocks): x = 0, y_i = i (1..n), z = n + 1. Outputs p_i = x + y_1..y_i,
    T = y_1 + ... + y_n + z. Circuit: p chain, u = p_n + z, T = u + x (n + 2 gates)."""
    N = n + 2
    g = [(0, 1)] + [(N + i - 2, i) for i in range(2, n + 1)]
    g.append((N + n - 1, n + 1))
    g.append((N + n, 0))
    vals = [1 << i for i in range(N)]
    for a, b in g:
        vals.append(vals[a] ^ vals[b])
    rows = [vals[N + i] for i in range(n)] + [vals[-1]]
    assert len(set(vals)) == len(vals) and vals[-1] == sum(1 << i for i in range(1, n + 2))
    ev = [N + i for i, (a, b) in enumerate(g) if vals[a] & vals[b]]
    assert ev == [N + n + 1]                      # singleton blocks: an event is a shared input
    # explicit event-free circuit with 2n gates: q chain on y, T = q_n + z, p_1 = x + y_1, p_i = x + q_i
    h, hv = [], [1 << i for i in range(N)]

    def add(a, b):
        assert not (hv[a] & hv[b])
        h.append((a, b))
        hv.append(hv[a] ^ hv[b])
        return len(hv) - 1
    q = {1: 1}
    for i in range(2, n + 1):
        q[i] = add(q[i - 1], i)
    add(q[n], n + 1)
    for i in range(1, n + 1):
        add(0, q[i])
    assert set(rows) <= set(hv) and len(h) == 2 * n
    print("tail family n=%d: %d gates, one event (T, w = %d), private operand u = p_n + z; explicit event-free "
          "circuit %d gates; saving %d = w - 3" % (n, len(g), n + 1, len(h), len(h) - len(g)))


def q3_windows():
    E = lambda c: 15 ^ (1 << c)
    S = lambda c: (1 << c) | (1 << ((c + 1) % 4))
    rows = [(E(c) << (4 * j)) | (S(c) << (4 * ((j - 1) % 3))) for j in range(3) for c in range(4)]
    sup = sorted({tuple(b for b in range(3) if r >> (4 * b) & 15) for r in rows})
    print("Q_3 windows:", sup, "| every pair of the three blocks co-occurs: the graph is complete, so no event "
          "support plus cancelled block is ever separated (no window credit)")


if __name__ == "__main__":
    adj = windows()
    for n in (3, 5, 8):
        tail_family(n)
    q3_windows()
    specs = ["r88", "r89", "circuits_2.txt:783", "circuits_3.txt:7451", "circuits_3.txt:7651",
             "circuits_3.txt:1451", "circuits_3.txt:3001",
             os.path.join(ST, "cancel", "witness", "witness_mc_block.json")] + sys.argv[1:]
    for s in specs:
        g = [tuple(x) for x in json.load(open(s))] if s.endswith(".json") else load(s)
        analyse(os.path.basename(s), g, adj)
