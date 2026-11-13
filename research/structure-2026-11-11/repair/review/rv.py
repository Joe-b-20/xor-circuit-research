"""Machine review of repair/REPAIR.md (phase 11): reviewer's own code.

Direct construction and evaluation of specified circuits only. No SAT, no search, no enumeration of circuits,
no least-gate computation. Every repaired circuit is built explicitly and verified (computes the map, has no
whole-block cancellation).

Two repair procedures, written independently of repair.py:
  joint  - Lemma 1 literally: a circuit D of chains over the inputs of every event value (shared prefixes
           reused), placed first; then the non-event gates of C in order, event references pointed into D;
           then normalisation (duplicate reuse incl. input values, dead-gate pruning).
  seq    - Theorem P as stated: repeatedly take the FIRST event of the CURRENT (normalised) circuit, replace it
           in place by the projection gadget (or a direct chain), normalise, and record the per-event
           overhead sigma_e = |after| - |before| next to the Theorem P quantities measured in the current
           circuit before the replacement, under three readings of s_e:
             R1: ancestors incl. inputs, 'present' = value of any node (this is what repair.py computes)
             R2: gate ancestors with P(u) != 0, 'present' = value of a node other than e (REPAIR's prefix text)
             R3: gate ancestors with P(u) != 0, 'present' = value of any node incl. e
usage: python3 rv.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ST, "compose", "compat"))


# ---------------------------------------------------------------- MixColumns, own implementation
def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        b >>= 1
    return r


def mixcolumns_targets():
    """Output (i, t) = bit t of byte i of M x, M circulant (2 3 1 1); input wire 8c + j = bit j of byte c."""
    coef = [2, 3, 1, 1]
    rows = {}
    for i in range(4):
        for t in range(8):
            m = 0
            for c in range(4):
                k = coef[(c - i) % 4]
                for j in range(8):
                    if (gmul(1 << j, k) >> t) & 1:
                        m |= 1 << (8 * c + j)
            rows[(i, t)] = m
    return rows


MC = mixcolumns_targets()
MC_BM = [sum(1 << (8 * c + j) for c in range(4)) for j in range(8)]


# ---------------------------------------------------------------- generic circuit tools
def values(n, gates):
    v = [1 << i for i in range(n)]
    for a, b in gates:
        assert a < len(v) and b < len(v), "not topological"
        v.append(v[a] ^ v[b])
    return v


def cancelled(va, vb, bms):
    return [c for c, m in enumerate(bms) if (va & m) and (va & m) == (vb & m)]


def events(n, gates, bms):
    v = values(n, gates)
    return [n + i for i, (a, b) in enumerate(gates) if cancelled(v[a], v[b], bms)]


def out_nodes(n, gates, targets):
    v = values(n, gates)
    first = {}
    for i, x in enumerate(v):
        first.setdefault(x, i)
    return {first[t] for t in targets}


def is_reduced(n, gates, targets):
    v = values(n, gates)
    gv = v[n:]
    ins = set(v[:n])
    distinct = len(set(gv)) == len(gv) and 0 not in gv and not (set(gv) & ins)
    outs = out_nodes(n, gates, targets)
    live, st = set(), list(outs)
    while st:
        x = st.pop()
        if x < n or x in live:
            continue
        live.add(x)
        st.extend(gates[x - n])
    return distinct, len(live) == len(gates)


def normalise(n, gates, targets):
    """Duplicate reuse (a gate whose value is 0 is an error, an input value or an earlier value is redirected),
    then dead-gate pruning. Returns a new topological gate list."""
    v = [1 << i for i in range(n)]
    where = {x: i for i, x in enumerate(v)}
    m = list(range(n))
    ng = []
    for a, b in gates:
        a2, b2 = m[a], m[b]
        x = v[a2] ^ v[b2]
        assert x != 0, "zero-valued gate"
        if x in where:
            m.append(where[x])
            continue
        ng.append((a2, b2))
        v.append(x)
        where[x] = len(v) - 1
        m.append(len(v) - 1)
    outs = {where[t] for t in targets}
    live, st = set(), list(outs)
    while st:
        x = st.pop()
        if x < n or x in live:
            continue
        live.add(x)
        st.extend(ng[x - n])
    keep = sorted(live)
    ren = {i: i for i in range(n)}
    out = []
    for x in keep:
        a, b = ng[x - n]
        ren[x] = n + len(out)
        out.append((ren[a], ren[b]))
    return out


def verify(n, gates, targets, bms):
    v = values(n, gates)
    assert set(targets) <= set(v), "map not computed"
    assert not events(n, gates, bms), "repaired circuit has an event"
    return len(gates)


def popc(x):
    return bin(x).count("1")


# ---------------------------------------------------------------- Lemma 1 (joint repair), literal
def joint_direct(n, gates, targets, bms):
    v = values(n, gates)
    E = events(n, gates, bms)
    Eset = set(E)
    D, where = [], {1 << i: i for i in range(n)}
    dv = [1 << i for i in range(n)]

    def add(a, b):
        x = dv[a] ^ dv[b]
        if x in where:
            return where[x]
        assert not cancelled(dv[a], dv[b], bms)
        D.append((a, b))
        dv.append(x)
        where[x] = len(dv) - 1
        return len(dv) - 1
    emap = {}
    for e in E:
        bits = [i for i in range(n) if v[e] >> i & 1]
        acc = bits[0]
        for i in bits[1:]:
            acc = add(acc, i)
        emap[e] = acc
    K = len(D)
    m = {i: i for i in range(n)}
    m.update(emap)
    new = list(D)
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        if g in Eset:
            continue
        new.append((m[a], m[b]))
        m[g] = n + len(new) - 1
    raw = len(new)
    assert raw == len(gates) - len(E) + K
    assert not events(n, new, bms)                     # retained gates stay non-events (Lemma 1)
    assert set(targets) <= set(values(n, new))
    fin = normalise(n, new, targets)
    verify(n, fin, targets, bms)
    return len(E), K, raw, len(fin)


# ---------------------------------------------------------------- Theorem P quantities in a given circuit
def theorem_p_quantities(n, gates, targets, bms, e):
    v = values(n, gates)
    a, b = gates[e - n]
    C = cancelled(v[a], v[b], bms)
    Cm = sum(bms[c] for c in C)
    keep = ((1 << n) - 1) ^ Cm
    anc, st = set(), [a, b]
    while st:
        x = st.pop()
        if x in anc:
            continue
        anc.add(x)
        if x >= n:
            st.extend(gates[x - n])
    outs = out_nodes(n, gates, targets)
    N = len(v)
    readers = [[] for _ in range(N)]
    for i, (p, q) in enumerate(gates):
        readers[p].append(n + i)
        readers[q].append(n + i)
    reach = [False] * N                                  # reaches an output on a path avoiding e
    for x in range(N - 1, -1, -1):
        if x == e:
            continue
        reach[x] = x in outs or any(reach[r] for r in readers[x] if r != e)
    allv = set(v)
    other = set(v[:e] + v[e + 1:])
    shared_C = [u for u in anc if v[u] & Cm and reach[u]]
    dom_C = [u for u in anc if v[u] & Cm and not reach[u]]
    R1 = sum(1 for u in shared_C if (v[u] & keep) not in allv)
    R2 = sum(1 for u in shared_C if u >= n and (v[u] & keep) and (v[u] & keep) not in other)
    R3 = sum(1 for u in shared_C if u >= n and (v[u] & keep) and (v[u] & keep) not in allv)
    delta = int(bool(v[a] & keep) and bool(v[b] & keep))
    return dict(C=C, keep=keep, w=popc(v[e]), R1=R1, R2=R2, R3=R3, delta=delta,
                nshared=len(shared_C), ndom=len([u for u in dom_C if u >= n]))


def gadget(n, gates, e, keep, method, bms):
    """Gate list with e replaced in place by a gadget reading only nodes before e."""
    v = values(n, gates)
    pre = list(gates[:e - n])
    pv = v[:e]
    where = {}
    for i, x in enumerate(pv):
        where.setdefault(x, i)

    def add(p, q):
        x = pv[p] ^ pv[q]
        if x in where:
            return where[x]
        assert x != 0 and not cancelled(pv[p], pv[q], bms), "gadget gate is an event"
        pre.append((p, q))
        pv.append(x)
        where[x] = len(pv) - 1
        return len(pv) - 1
    if method == "direct":
        bits = [i for i in range(n) if v[e] >> i & 1]
        r = bits[0]
        for i in bits[1:]:
            r = add(r, i)
    else:
        memo = {}

        def P(u):
            if u in memo:
                return memo[u]
            x = v[u] & keep
            if x == 0:
                r = None
            elif x == v[u]:
                r = u
            elif x in where:
                r = where[x]
            else:
                p1, p2 = P(gates[u - n][0]), P(gates[u - n][1])
                r = p1 if p2 is None else p2 if p1 is None else add(p1, p2)
            memo[u] = r
            return r
        a, b = gates[e - n]
        pa, pb = P(a), P(b)
        r = pa if pb is None else pb if pa is None else add(pa, pb)
    assert pv[r] == v[e]
    k = len(pre) - (e - n)                               # new gadget gates
    # remaining gates, e -> r, later nodes shifted
    shift = len(pre) + n - (e + 1)
    def mp(x):
        return x if x < e else r if x == e else x + shift
    rest = [(mp(p), mp(q)) for p, q in gates[e - n + 1:]]
    return pre + rest, k


def sequential(n, gates, targets, bms, method, log=None):
    cur = normalise(n, gates, targets)
    assert len(cur) == len(gates), "input circuit not reduced"
    total = 0
    while True:
        E = events(n, cur, bms)
        if not E:
            break
        e = E[0]                                         # first event: its ancestors are event-free
        q = theorem_p_quantities(n, cur, targets, bms, e)
        new, k = gadget(n, cur, e, q["keep"], method, bms)
        new = normalise(n, new, targets)
        sig = len(new) - len(cur)
        total += sig
        if log is not None:
            log.append((e, q, k, sig))
        cur = new
    verify(n, cur, targets, bms)
    return cur, total


def report(name, n, gates, targets, bms, base, verbose=True):
    d, r = is_reduced(n, gates, targets)
    assert set(targets) <= set(values(n, gates))
    E = events(n, gates, bms)
    v = values(n, gates)
    ws = sum(popc(v[e]) - 2 for e in E)
    ne, K, raw, jf = joint_direct(n, gates, targets, bms)
    logs = {}
    res = {}
    for meth in ("direct", "projection"):
        logs[meth] = []
        cur, tot = sequential(n, gates, targets, bms, meth, logs[meth])
        res[meth] = len(cur)
    print("%s: G %d, reduced %s, live %s, events %d, sum(w-2) %d | joint Lemma-1 direct: K %d, G-|E|+K %d, "
          "normalised %d (sigma %+d) | sequential direct %d (sigma %+d) | sequential projection %d (sigma %+d) "
          "| bound G >= %d - min sigma = %d"
          % (name, len(gates), d, r, len(E), ws, K, raw, jf, jf - len(gates), res["direct"],
             res["direct"] - len(gates), res["projection"], res["projection"] - len(gates), base,
             base - min(jf, res["direct"], res["projection"]) + len(gates)))
    if verbose:
        viol = {"R1": 0, "R2": 0, "R3": 0}
        for e, q, k, sig in logs["projection"]:
            for R in viol:
                if sig > q[R] + q["delta"] - 1:
                    viol[R] += 1
        summ = [(e, q["w"] - 2, q["R1"] + q["delta"] - 1, q["R2"] + q["delta"] - 1, k, sig)
                for e, q, k, sig in logs["projection"]]
        print("    projection per event (node, w-2, R1 bound, R2 bound, new gates, sigma_e): %s%s"
              % (summ[:8], " ..." if len(summ) > 8 else ""))
        print("    per-event violations of sigma_e <= s_e + delta_e - 1: %s" % viol)
    return E, v


# ---------------------------------------------------------------- section 3: prefix family
def prefix(n):
    N = n + 1                                            # x = 0, y_i = i
    g = [(0, 1)]
    for i in range(2, n + 1):
        g.append((N + i - 2, i))
    g.append((N + n - 1, 0))
    targets = values(N, g)[N:]
    bms = [1 << i for i in range(N)]
    # hand event-free circuit: q_2..q_n, then p_1 = x + y_1, p_i = x + q_i
    h = [(1, 2)]
    for i in range(3, n + 1):
        h.append((N + len(h) - 1, i))
    qidx = {i: N + i - 2 for i in range(2, n + 1)}
    h.append((0, 1))
    for i in range(2, n + 1):
        h.append((0, qidx[i]))
    if n == 2:
        pass
    assert set(targets) <= set(values(N, h)) and not events(N, h, bms) and len(h) == 2 * n - 1
    E = events(N, g, bms)
    assert E == [N + n] and is_reduced(N, g, targets) == (True, True)
    print("prefix n=%d: G %d, events %s, hand event-free circuit %d = 2n-1 gates verified" % (n, len(g), E, len(h)))
    report("  prefix n=%d" % n, N, g, targets, bms, 2 * n - 1)


# ---------------------------------------------------------------- adversarial circuits for Theorem P
def adversarial():
    print("--- adversarial circuits (singleton blocks unless stated) ---")
    # A1: x=0,y=1,z=2. g1=x+y, g2=g1+z, e=g2+x=y+z; outputs g1,g2,e. 3 distinct outputs => any circuit >= 3.
    n, g = 3, [(0, 1), (3, 2), (4, 0)]
    report("A1 (P(a)=val(e), a shared)", n, g, values(n, g)[n:], [1, 2, 4], 3)
    # A2: x, y1..y4. g1..g4 prefix sums with x, e = g4 + x, d3 = e + y4 (event), d2 = d3 + y3 (event).
    n = 5
    g = [(0, 1), (5, 2), (6, 3), (7, 4), (8, 0), (9, 4), (10, 3)]
    report("A2 (projections equal later events' values)", n, g, values(n, g)[n:], [1 << i for i in range(5)], 7)
    # A3: blocks X={x}, Y={y,y'}, Z={z}: wires x=0, y=1, y'=2, z=3. g1=x+y, g2=g1+z, a=g2+y', e=a+x, d=e+y'
    #     (d is NOT an event: Y-parts y+y' vs y'). Outputs g2, a, e, d.
    n = 4
    g = [(0, 1), (4, 3), (5, 2), (6, 0), (7, 2)]
    vv = values(n, g)
    tg = [vv[5], vv[6], vv[7], vv[8]]
    report("A3 (projection equals a later non-event node)", n, g, tg, [1, 6, 8], 4)
    # A4: dominated C-content chain read only through e, plus delta = 1.
    #     x=0 (block X), y=1, z=2, w=3. u=x+y (dominated), a=u+z, b=x+w, e=a+b=y+z+w; outputs e, b+z? keep b shared:
    n = 4
    g = [(0, 1), (4, 2), (0, 3), (5, 6), (6, 2)]        # u, a, b, e, f=b+z (b shared via f)
    vv = values(n, g)
    report("A4 (dominated partner, delta=1)", n, g, [vv[7], vv[8]], [1, 2, 4, 8], 2)
    # A5: two events that interact: e1 cancels x, e2 cancels y, e2 reads e1's ancestors.
    n = 4                                                # x=0,y=1,z=2,w=3
    g = [(0, 1), (4, 2), (5, 3), (6, 0), (7, 1), (5, 0)]  # s1=x+y, s2=s1+z, s3=s2+w, e1=s3+x, e2=e1+y, t=s2+x
    vv = values(n, g)
    report("A5 (interacting events)", n, g, vv[n:], [1, 2, 4, 8], 6)


# ---------------------------------------------------------------- section 8 restriction example
def restriction_example():
    w = lambda c, j: 8 * c + j
    v = [1 << i for i in range(32)]
    gates = []
    where = {x: i for i, x in enumerate(v)}

    def add(a, b, dedupe=True):
        x = v[a] ^ v[b]
        if dedupe and x in where:
            return where[x]
        gates.append((a, b))
        v.append(x)
        where.setdefault(x, len(v) - 1)
        return len(v) - 1
    a = add(w(0, 7), w(1, 0))
    b = add(a, w(2, 0))
    e = add(b, w(0, 7))
    t = add(e, w(3, 0))
    t = add(t, w(0, 7))
    y00 = add(t, w(1, 7))
    assert v[y00] == MC[(0, 0)]
    for k in sorted(MC):
        if k == (0, 0):
            continue
        bits = [i for i in range(32) if MC[k] >> i & 1]
        acc = bits[0]
        for i in bits[1:]:
            acc = add(acc, i)
    n = 32
    targets = list(MC.values())
    red, live = is_reduced(n, gates, targets)
    E = events(n, gates, MC_BM)
    vv = values(n, gates)
    keep = ((1 << 32) - 1) ^ MC_BM[7]
    seen_in = {0} | {(1 << i) & keep for i in range(32)}
    cat = None
    seen = set()
    for i in range(len(gates)):
        im = vv[n + i] & keep
        if n + i == e:
            cat = "Z" if im == 0 else "I" if im in seen_in else "D" if im in seen else "retained"
        seen.add(im)
    print("restriction example: G %d, reduced %s, live %s, events %s (e = %d, cancelled %s), category of e at "
          "block 7: %s; image(e) == image(b): %s; image(a) is input x_(1,0): %s"
          % (len(gates), red, live, E, e, cancelled(vv[gates[e - n][0]], vv[gates[e - n][1]], MC_BM), cat,
             (vv[e] & keep) == (vv[b] & keep), (vv[a] & keep) == 1 << w(1, 0)))


# ---------------------------------------------------------------- MixColumns corpus lines
def sheet_of(val):
    for k, r in MC.items():
        if r == val:
            return k
    return None


def mc_line(spec):
    from clib import load, ROWS
    assert ROWS == MC
    g = [tuple(x) for x in json.load(open(spec))] if spec.endswith(".json") else load(spec)
    E, v = report("MC " + os.path.basename(spec), 32, g, list(MC.values()), MC_BM, 84, verbose=True)
    info = []
    for e in E[:6]:
        a, b = g[e - 32]
        C = cancelled(v[a], v[b], MC_BM)
        Ba = sorted(j for j in range(8) if v[a] & MC_BM[j])
        Bb = sorted(j for j in range(8) if v[b] & MC_BM[j])
        info.append("node %d w %d out %s cancels %s, B(a) %s B(b) %s" % (e, popc(v[e]), sheet_of(v[e]), C, Ba, Bb))
    if info:
        print("    events: " + "; ".join(info) + (" ..." if len(E) > 6 else ""))


def q3():
    ls = [l.split("#")[0].strip() for l in open(os.path.join(ST, "rotation", "circuits", "q3_28.txt"))]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    bit = lambda c, j: 1 << (4 * j + (c % 4))
    tg = []
    for j in range(3):
        for c in range(4):
            Ec = sum(bit(d, j) for d in range(4) if d != c)
            sc = bit(c, (j - 1) % 3) | bit(c + 1, (j - 1) % 3)
            tg.append(Ec | sc)
    report("Q_3 q3_28", n, g, tg, [15 << (4 * j) for j in range(3)], 30)


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    print("MixColumns row weights by sheet:",
          {j: sorted(set(popc(MC[(c, j)]) for c in range(4))) for j in range(8)})
    for n in (2, 3, 5, 8, 12):
        prefix(n)
    adversarial()
    restriction_example()
    q3()
    for s in ["r88", "r89", "circuits_2.txt:783", "circuits_3.txt:7451", "circuits_3.txt:7651",
              "circuits_3.txt:1451", "circuits_3.txt:3001",
              os.path.join(ST, "cancel", "witness", "witness_mc_block.json")]:
        mc_line(s)
