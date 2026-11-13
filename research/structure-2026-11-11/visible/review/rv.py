"""Independent re-check of visible/VISIBLE.md (phase 12) by the machine reviewer.

Direct evaluation of specified circuits and explicit constructions only: no SAT, no search, no enumeration of
circuits, no least-gate computation. Does not import visible.py. Uses compose/compat/clib.py only for the
MixColumns rows and for loading the corpus lines named in VISIBLE.md.
usage: python3 rv.py > rv_out.txt
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ST, "compose", "compat"))
from clib import ROWS, load  # noqa: E402

NIN = 32
MASK = [sum(1 << (8 * c + k) for c in range(4)) for k in range(8)]
ROWSHEET = {}
for (c, j), v in ROWS.items():
    ROWSHEET[v] = j


def sup(v):
    return frozenset(k for k in range(8) if v & MASK[k])


def w(v):
    return bin(v).count("1")


def canc(a, b):
    return frozenset(k for k in range(8) if (a & MASK[k]) and (a & MASK[k]) == (b & MASK[k]))


# ---------------------------------------------------------------- windows, graph, own blocks
WIN = {}
for j in range(8):
    ss = {sup(ROWS[(c, j)]) for c in range(4)}
    assert len(ss) == 1
    WIN[j] = next(iter(ss))
ADJ = {k: set() for k in range(8)}
for j in range(8):
    for a in WIN[j]:
        for b in WIN[j]:
            if a != b:
                ADJ[a].add(b)


def adj(a, b):
    return b in ADJ[a]


def inwin(s):
    return any(s <= WIN[j] for j in range(8))


def section_windows():
    print("== windows ==")
    print("W:", {j: sorted(WIN[j]) for j in range(8)})
    claimed = {0: {7, 0}, 1: {0, 1, 7}, 2: {1, 2}, 3: {2, 3, 7}, 4: {3, 4, 7}, 5: {4, 5}, 6: {5, 6}, 7: {6, 7}}
    assert all(WIN[j] == claimed[j] for j in range(8))
    for j in range(8):
        for c in range(4):
            r = ROWS[(c, j)]
            assert w(r & MASK[j]) == 3 and all(w(r & MASK[k]) == 2 for k in WIN[j] if k != j)
            assert w(r) in (5, 7)
    print("row weights: 3 on own block, 2 on each other window block: ok")
    pairs = {(j, k): sorted(WIN[j] & WIN[k]) for j in range(8) for k in range(j + 1, 8) if WIN[j] & WIN[k]}
    big = {p: v for p, v in pairs.items() if len(v) == 2}
    print("pairwise intersections with 2 blocks:", big, "max", max(len(v) for v in pairs.values()))
    trip = set()
    for i in range(8):
        for j in range(i + 1, 8):
            for k in range(j + 1, 8):
                s = WIN[i] & WIN[j] & WIN[k]
                if s:
                    trip.add(frozenset(s))
    print("nonempty triple intersections:", [sorted(s) for s in trip])
    own = [(j, k) for j in range(8) for k in range(8) if j != k and j in WIN[k] and k in WIN[j]]
    print("own-block violations (j in W_k and k in W_j):", own)
    edges = sorted((a, b) for a in range(8) for b in ADJ[a] if a < b)
    print("co-occurrence edges:", edges)
    cl = [{0, 1, 7}, {1, 2, 7}, {2, 3, 7}, {3, 4, 7}, {4, 5}, {5, 6}, {6, 7}]
    for K in cl:
        assert all(adj(a, b) for a in K for b in K if a != b)
        assert not [c for c in range(8) if c not in K and all(adj(c, a) for a in K)]
    assert all(any({a, b} <= K for K in cl) for a, b in edges)
    print("listed cliques are cliques, maximal, cover all edges: ok")
    for j in range(8):
        ext = [c for c in range(8) if c not in WIN[j] and all(adj(c, a) for a in WIN[j])]
        print("  W_%d extends by %s" % (j, ext))
    print()


# ---------------------------------------------------------------- the chain construction of VISIBLE 5.2
def plan_counts(v, Jf):
    """Hand formulas for in(f) and x(f) from weights (independent of the builder)."""
    B = sup(v)
    own = [j for j in Jf if j in B]
    A = own[0] if own else None
    t = 3 in Jf and 2 in B and 7 in B
    wb = {k: w(v & MASK[k]) for k in range(8)}
    if t:
        inn = wb[3] + 1 if wb[3] else 1
    elif A is not None:
        inn = wb[A] if w(v) > wb[A] else wb[A] - 1
    else:
        inn = 0
    borrower = 1 in Jf and 0 not in Jf and 0 in B
    x = (wb[0] - 1 + (1 if wb[7] else 0)) if borrower else 0
    return dict(A=A, t=t, inn=inn, kappa=inn - 1, x=x, borrower=borrower, own=own)


class Builder:
    def __init__(self):
        self.g, self.v = [], [1 << i for i in range(NIN)]
        self.owner = {}

    def add(self, a, b, f=None):
        self.g.append((a, b))
        self.v.append(self.v[a] ^ self.v[b])
        node = len(self.v) - 1
        if f is not None:
            self.owner[node] = f
        return node

    def piece(self, v, k, f):
        bits = [i for i in range(NIN) if (v >> i) & 1 and (MASK[k] >> i) & 1]
        node = bits[0]
        for i in bits[1:]:
            node = self.add(node, i, f)
        return node

    def chain(self, v, Jf, f):
        p = plan_counts(v, Jf)
        B = sup(v)
        if p["t"]:
            n2, n7 = self.piece(v, 2, f), self.piece(v, 7, f)
            if v & MASK[3]:
                n2 = self.add(self.piece(v, 3, f), n2, f)
            return self.add(n2, n7, f)
        offb = sorted(B - ({p["A"]} if p["A"] is not None else set()))
        off = None
        for k in offb:
            q = self.piece(v, k, f)
            off = q if off is None else self.add(off, q, f)
        if p["A"] is None:
            return off
        a = self.piece(v, p["A"], f)
        return a if off is None else self.add(off, a, f)


# ---------------------------------------------------------------- analysis of one circuit
def values(gates):
    v = [1 << i for i in range(NIN)]
    for a, b in gates:
        v.append(v[a] ^ v[b])
    return v


def analyse(name, gates, desig=None, verbose=True):
    vals = values(gates)
    N, G = len(vals), len(gates)
    assert set(ROWS.values()) <= set(vals[NIN:]), name
    reduced = len(set(vals)) == N and 0 not in vals
    if desig is None:   # designated output: first gate node with the row value
        desig = {}
        for x in range(NIN, N):
            if vals[x] in ROWSHEET and vals[x] not in desig:
                desig[vals[x]] = x
    dnode = {x: ROWSHEET[r] for r, x in desig.items()}
    isev = [False] * N
    for i, (a, b) in enumerate(gates):
        isev[NIN + i] = bool(canc(vals[a], vals[b]))
    rd = [[] for _ in range(N)]
    for i, (a, b) in enumerate(gates):
        rd[a].append(NIN + i)
        if b != a:
            rd[b].append(NIN + i)
    J = [frozenset()] * N
    for x in range(N - 1, -1, -1):
        s = {dnode[x]} if x in dnode else set()
        for y in rd[x]:
            if not isev[y]:
                s |= J[y]
        J[x] = frozenset(s)
    gl = range(NIN, N)
    F = [x for x in gl if isev[x] and J[x]]
    EH = [x for x in gl if isev[x] and not J[x]]
    R = [x for x in gl if not isev[x] and J[x]]
    Q = [x for x in gl if not isev[x] and not J[x]]
    cls = {}
    for nm, S in (("F", F), ("Eh", EH), ("R", R), ("Q", Q)):
        for x in S:
            cls[x] = nm
    for i in range(NIN):
        cls[i] = "in"
    # backward traversal from outputs, stopping at events, reaches exactly F and R
    seen, st = set(), list(dnode)
    while st:
        x = st.pop()
        if x < NIN or x in seen:
            continue
        seen.add(x)
        if not isev[x]:
            st.extend(gates[x - NIN])
    assert seen == set(F) | set(R), name
    # separation: no edge from (Eh u Q) into R; hidden part reaches outputs only through F
    for x in R:
        for y in gates[x - NIN]:
            assert cls[y] in ("in", "R", "F"), (name, x, y, cls[y])
    # Lemma S
    for x in F + R:
        for j in J[x]:
            assert sup(vals[x]) <= WIN[j], name
    # Lemma W1 and anchored events
    credit = set()
    w1_cases = 0
    for f in F:
        a, b = gates[f - NIN]
        C, B = canc(vals[a], vals[b]), sup(vals[f])
        for c in C:
            for bb in B:
                if not adj(c, bb):
                    w1_cases += 1
                    ops = [o for o in (a, b) if vals[o] & MASK[bb]]
                    for o in ops:
                        assert vals[o] & MASK[c] and not inwin(sup(vals[o])) and cls[o] in ("Eh", "Q"), name
        for o in (a, b):
            if cls[o] in ("Eh", "Q") and not inwin(sup(vals[o])):
                credit.add(o)
        if all(cls[o] in ("in", "R") for o in (a, b)):
            K = B | C
            assert all(adj(p, q) for p in K for q in K if p != q), name
        if len(B) == 3:
            assert any(cls[o] in ("Eh", "Q") for o in (a, b)), name
    # ---- the repair C' (D = chains, then R in order)
    bd = Builder()
    img = {i: i for i in range(NIN)}
    plans = {}
    K = 0
    for f in F:
        plans[f] = plan_counts(vals[f], J[f])
        assert len(plans[f]["own"]) <= 1
        node = bd.chain(vals[f], J[f], f)
        assert bd.v[node] == vals[f]
        img[f] = node
        K += w(vals[f]) - 1
    nchain = len(bd.g)
    assert nchain == K
    for x in R:
        a, b = gates[x - NIN]
        img[x] = bd.add(img[a], img[b])
    Gp = len(bd.g)
    assert Gp == G - (len(F) + len(EH)) - len(Q) + K
    cv = bd.v
    for a, b in bd.g:
        assert not canc(cv[a], cv[b]), name + ": event in C'"
    cdes = {img[x]: j for x, j in dnode.items()}
    assert len(cdes) == 32 and all(ROWSHEET.get(cv[y]) == j for y, j in cdes.items())
    # descendants: which sheets' designated outputs each node reaches in C'
    crd = [[] for _ in range(len(cv))]
    for i, (a, b) in enumerate(bd.g):
        crd[a].append(NIN + i)
        crd[b].append(NIN + i)
    reach = [frozenset()] * len(cv)
    for y in range(len(cv) - 1, -1, -1):
        s = {cdes[y]} if y in cdes else set()
        for z in crd[y]:
            s |= reach[z]
        reach[y] = frozenset(s)
    # Lemma V1: a chain gate of f reaches exactly the sheets J(f)
    for y, f in bd.owner.items():
        assert reach[y] == J[f], (name, y, f, reach[y], J[f])
    # retained images reach exactly J of the retained gate
    for x in R:
        assert reach[img[x]] == J[x]
    fam = {}
    for j in range(8):
        fam[j] = {y for y in range(NIN, len(cv)) if j in reach[y] and cv[y] & MASK[j]}
    fam[3] |= {y for y in range(NIN, len(cv)) if 3 in reach[y] and cv[y] & MASK[2] and cv[y] & MASK[7]}
    for j in range(8):
        for k in range(j + 1, 8):
            assert not fam[j] & fam[k], name
    sizes = [len(fam[j]) for j in range(8)]
    assert all(s >= 10 for s in sizes) and sizes[3] >= 13
    union = set().union(*fam.values())
    U = Gp - len(union)
    # chain gates in families: count and home family
    infam = {}
    for f in F:
        mine = {y for y, o in bd.owner.items() if o == f}
        assert len(mine) == w(vals[f]) - 1
        infam[f] = len(mine & union)
        assert infam[f] == plans[f]["inn"], (name, f, infam[f], plans[f])
        home = 3 if plans[f]["t"] else plans[f]["A"]
        for j in range(8):
            if j != home:
                assert not mine & fam[j]
    # per-sheet form against R_j computed in C
    for j in range(8):
        Rj = {x for x in R if j in J[x] and vals[x] & MASK[j]}
        if j == 3:
            Rj |= {x for x in R if 3 in J[x] and vals[x] & MASK[2] and vals[x] & MASK[7]}
        chains_home = sum(plans[f]["inn"] for f in F if (3 if plans[f]["t"] else plans[f]["A"]) == j)
        assert len(Rj) + chains_home == sizes[j], (name, j)
    # 84 form ingredients
    L01 = {y for y in range(NIN, len(cv)) if (reach[y] & {0, 1}) and cv[y] & (MASK[0] | MASK[1])}
    X = {y for y in range(NIN, len(cv)) if cv[y] & MASK[0] and not cv[y] & MASK[1]
         and 1 in reach[y] and 0 not in reach[y]}
    assert L01 == fam[0] | fam[1] | X and not X & union
    assert len(L01) >= 21 and Gp >= 84 + U - len(X)
    xcount = {}
    for f in F:
        mine = {y for y, o in bd.owner.items() if o == f}
        xcount[f] = len(mine & X)
        assert xcount[f] == plans[f]["x"], (name, f, xcount[f], plans[f])
    kap = sum(plans[f]["kappa"] for f in F)
    hid = len(EH) + len(Q)
    bV = 83 + hid - kap
    b84 = 84 + hid - kap - sum(xcount.values())
    bdir = 84 + hid - sum(w(vals[f]) - 2 for f in F)
    bcirc = 83 + U + len(F) + len(EH) + len(Q) - K
    assert G >= bV and G >= b84 and G >= bcirc
    assert len(R) + sum(infam.values()) >= 83
    # kappa range
    for f in F:
        k = plans[f]["kappa"]
        assert -1 <= k <= min(4, w(vals[f]) - 2)
    if verbose:
        print("%s: G %d reduced %s | F %d, hidden events %d, R %d, Q %d | credit operands (no window, in Eh u Q) %d | "
              "W1 non-adjacent pairs %d" % (name, G, reduced, len(F), len(EH), len(R), len(Q), len(credit), w1_cases))
        ks = sorted(plans[f]["kappa"] for f in F)
        for f in F[:6]:
            a, b = gates[f - NIN]
            p = plans[f]
            print("   f=%d %s w=%d B=%s C=%s J=%s A=%s t=%d in=%d kappa=%d x=%d ops=%s/%s" % (
                f, "out" if f in dnode else "int", w(vals[f]), sorted(sup(vals[f])), sorted(canc(vals[a], vals[b])),
                sorted(J[f]), p["A"], p["t"], p["inn"], p["kappa"], p["x"], cls[a], cls[b]))
        if len(F) > 6:
            print("   ... kappa multiset:", {k: ks.count(k) for k in set(ks)}, "sum in", sum(infam.values()),
                  "x total", sum(xcount.values()))
        print("   C': %d gates (K %d), event-free, outputs ok; families %s sum %d; U %d (chain gates in no family %d); "
              "|L01| %d, |X| %d" % (Gp, K, sizes, sum(sizes), U, nchain - sum(infam.values()), len(L01), len(X)))
        print("   bounds: direct(84-sum(w-2)) %d | Theorem V (83) %d | 84 form %d | this circuit 83+U+|E|+|Q|-K %d" % (
            bdir, bV, b84, bcirc))
    return dict(F=F, EH=EH, R=R, Q=Q, plans=plans, vals=vals, J=J, gates=gates, credit=credit)


# ---------------------------------------------------------------- general-map tail family
def tail(n):
    # inputs: x = 0, y_i = i (1..n), z = n + 1; each its own block. Event = shared input (singleton blocks).
    N = n + 2
    vals = [1 << i for i in range(N)]
    gates = []

    def add(a, b):
        gates.append((a, b))
        vals.append(vals[a] ^ vals[b])
        return len(vals) - 1
    p = [None, add(0, 1)]
    for i in range(2, n + 1):
        p.append(add(p[-1], i))
    u = add(p[n], n + 1)
    T = add(u, 0)
    outs = [vals[p[i]] for i in range(1, n + 1)] + [vals[T]]
    ev = [N + i for i, (a, b) in enumerate(gates) if vals[a] & vals[b]]
    assert ev == [T] and len(gates) == n + 2 and len(set(vals)) == len(vals)
    wins = [frozenset(i for i in range(N) if o >> i & 1) for o in outs]
    sT = frozenset(i for i in range(N) if vals[T] >> i & 1)
    su = frozenset(i for i in range(N) if vals[u] >> i & 1)
    assert not any(su <= W for W in wins)          # u lies in no window: J(u) empty, u in Q
    assert not any({0, n + 1} <= W for W in wins)   # x, z never co-occur: T's support is a maximal clique
    # explicit event-free circuit with 2n gates
    hv = [1 << i for i in range(N)]
    h = []

    def hadd(a, b):
        assert not hv[a] & hv[b]
        h.append((a, b))
        hv.append(hv[a] ^ hv[b])
        return len(hv) - 1
    q = {1: 1}
    for i in range(2, n + 1):
        q[i] = hadd(q[i - 1], i)
    hadd(q[n], n + 1)
    for i in range(1, n + 1):
        hadd(0, q[i])
    assert set(outs) <= set(hv) and len(h) == 2 * n
    print("tail n=%d: G %d, single event T (w %d), u private (no window); event-free circuit %d gates; "
          "Theorem W bound 2n-(w-3) = %d = G" % (n, len(gates), w(vals[T]), len(h), 2 * n - (w(vals[T]) - 3)))


# ---------------------------------------------------------------- constructions on r88
def insert_before(gates, pos, newgates_fn):
    """Return a gate list where newgates_fn(base) (gates reading inputs or nodes < NIN+pos, written with
    absolute indices starting at base = NIN+pos) is inserted before old gate index pos; later references shift."""
    new = newgates_fn(NIN + pos)
    k = len(new)
    out = list(gates[:pos]) + new
    for a, b in gates[pos:]:
        sh = lambda z: z + k if z >= NIN + pos else z
        out.append((sh(a), sh(b)))
    return out, k


def converse_example(r88):
    """Block-monotone circuit with an event: o = a + b with B(a) < B(o); insert n1 = a + x, n2 = n1 + x (event),
    o := n2 + b."""
    vals = values(r88)
    for pos, (a, b) in enumerate(r88):
        o = NIN + pos
        if vals[o] not in ROWSHEET:
            continue
        for aa, bb in ((a, b), (b, a)):
            miss = sup(vals[o]) - sup(vals[aa])
            if miss:
                c = min(miss)
                xb = min(i for i in range(NIN) if (MASK[c] >> i) & 1 and not (vals[aa] >> i) & 1)

                def mk(base, aa=aa, xb=xb):
                    return [(aa, xb), (base, xb)]
                g2, k = insert_before(r88, pos, mk)
                g2[pos + 2] = (NIN + pos + 1, bb)
                v2 = values(g2)
                assert set(ROWS.values()) <= set(v2[NIN:])
                evs = [NIN + i for i, (p, q) in enumerate(g2) if canc(v2[p], v2[q])]
                # block-monotone: every ancestor of every output gate has support inside the output's support
                rdr = [[] for _ in range(len(v2))]
                for i, (p, q) in enumerate(g2):
                    rdr[p].append(NIN + i)
                    rdr[q].append(NIN + i)
                ok = True
                for y in range(NIN, len(v2)):
                    if v2[y] not in ROWSHEET:
                        continue
                    st, an = [y], set()
                    while st:
                        z = st.pop()
                        if z < NIN or z in an:
                            continue
                        an.add(z)
                        st.extend(g2[z - NIN])
                    ok &= all(sup(v2[z]) <= sup(v2[y]) for z in an)
                print("converse: r88 with output gate %d rewritten through an event: events %s (cancel %s), "
                      "block-monotone %s, reduced %s" % (o, evs, [sorted(canc(v2[p], v2[q])) for p, q in
                                                                    [g2[e - NIN] for e in evs]], ok,
                                                         len(set(v2)) == len(v2)))
                return


def kappa_counterexample(r88):
    """Visible event f on blocks {2,7} feeding a sheet-3 output only (J(f) = {3}), with a hidden event behind it.
    Row o = (0,3). New gates (inputs only): a1 = [2: s], u = a1 + x, v = x + w1, h = u + v (hidden event, cancels
    3), k1 = h + x, k2 = x + w2, f = k1 + k2 (visible event, cancels 3, value [2: s] + [7: s]), e3 = [3: E],
    o = f + e3 replaces r88's gate for that row."""
    vals = values(r88)
    row = ROWS[(0, 3)]
    pos = vals.index(row, NIN) - NIN
    b2 = [i for i in range(NIN) if (row & MASK[2]) >> i & 1]
    b3 = [i for i in range(NIN) if (row & MASK[3]) >> i & 1]
    b7 = [i for i in range(NIN) if (row & MASK[7]) >> i & 1]
    x = b3[0]
    assert len(b2) == 2 and len(b7) == 2 and len(b3) == 3

    def mk(base):
        g = []
        idx = lambda: base + len(g)
        g.append((b2[0], b2[1])); a1 = idx() - 1
        g.append((a1, x)); u = idx() - 1
        g.append((x, b7[0])); v = idx() - 1
        g.append((u, v)); h = idx() - 1
        g.append((h, x)); k1 = idx() - 1
        g.append((x, b7[1])); k2 = idx() - 1
        g.append((k1, k2)); f = idx() - 1
        g.append((b3[0], b3[1])); e = idx() - 1
        g.append((e, b3[2])); e3 = idx() - 1
        g.append((f, e3))   # the new output; it replaces the old gate at pos
        return g
    g2, k = insert_before(r88, pos, mk)
    # remove the old output gate (now at pos + k), redirect its readers to the new output (pos + k - 1)
    old, newo = NIN + pos + k, NIN + pos + k - 1
    g3 = []
    for i, (a, b) in enumerate(g2):
        if NIN + i == old:
            continue
        fix = lambda z: newo if z == old else (z - 1 if z > old else z)
        g3.append((fix(a), fix(b)))
    v3 = values(g3)
    assert v3[newo] == row
    print("kappa counterexample circuit: G %d (r88 + %d - 1), reduced %s" % (len(g3), k, len(set(v3)) == len(v3)))
    res = analyse("r88+{2,7}-event", g3)
    fnode = NIN + pos + 6
    p = res["plans"][fnode]
    print("   the event f=%d: B=%s, J=%s, own blocks of J in B: %s -> support avoids own blocks; t=%d, kappa=%d "
          "(VISIBLE 5.3 says -1)" % (fnode, sorted(sup(res["vals"][fnode])), sorted(res["J"][fnode]), p["own"], p["t"],
                                    p["kappa"]))
    return g3


# ---------------------------------------------------------------- sole-event tables (formulas on output rows)
def tables():
    print("== sole event at an output: kappa, credit, x from the row values ==")
    for j in range(8):
        v = ROWS[(0, j)]
        Jf = {j}
        if j == 0:
            Jf2 = {0, 1}     # a sheet-0 output may also reach sheet 1 (W_0 inside W_1)
            assert plan_counts(v, Jf2)["kappa"] == plan_counts(v, Jf)["kappa"] and plan_counts(v, Jf2)["x"] == 0
        p = plan_counts(v, Jf)
        B = sup(v)
        ext = [c for c in range(8) if c not in B and all(adj(c, b) for b in B)]
        # credit forced unless every cancelled block is in ext
        bV = 83 - p["kappa"] + 1
        b84 = 84 - p["kappa"] - p["x"] + 1
        line = "sheet %d: w %d kappa %d x %d | with credit: 83-form %d 84-form %d best %d" % (
            j, w(v), p["kappa"], p["x"], bV, b84, max(bV, b84))
        if ext:
            line += " | C inside %s (no forced credit): 83-form %d 84-form %d best %d" % (
                ext, bV - 1, b84 - 1, max(bV, b84) - 1)
        print(line)
    print()


def main():
    section_windows()
    tables()
    for n in (3, 5, 8):
        tail(n)
    print()
    r88 = load("r88")
    specs = ["r88", "r89", "circuits_2.txt:783", "circuits_3.txt:7451", "circuits_3.txt:7651",
             "circuits_3.txt:1451", "circuits_3.txt:3001"]
    for s in specs:
        analyse(s, load(s))
    wit = [tuple(x) for x in json.load(open(os.path.join(ST, "cancel", "witness", "witness_mc_block.json")))]
    res = analyse("witness_mc_block", wit)
    allops = {o for f in res["F"] for o in res["gates"][f - NIN] if o >= NIN}
    print("   witness: distinct operands of visible events %d, of them in Q %d; outputs all events: %s" % (
        len(allops), sum(1 for o in allops if o in set(res["Q"])),
        all(f in res["F"] for f in res["F"]) and len(res["F"]) == 32 and not res["R"]))
    print()
    converse_example(r88)
    kappa_counterexample(r88)


if __name__ == "__main__":
    main()
