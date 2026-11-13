"""Independent review code (machine reviewer). Own MixColumns matrix, own construction, own transposition.
Direct evaluation of specified circuits only (no search, no enumeration of circuits).
usage: python3 rev.py
"""
import json, os, random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WIT = os.path.dirname(HERE)


def gmul(a, k):
    r = 0
    while k:
        if k & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        k >>= 1
    return r


def mixcolumns():
    """rows[(c,j)] = 32-bit mask over inputs 8k+b (bit b of byte k): out_c = 2a_c + 3a_{c+1} + a_{c+2} + a_{c+3}."""
    coef = {0: 2, 1: 3, 2: 1, 3: 1}
    rows = {}
    for c in range(4):
        for j in range(8):
            m = 0
            for k in range(4):
                for b in range(8):
                    if (gmul(1 << b, coef[(k - c) % 4]) >> j) & 1:
                        m |= 1 << (8 * k + b)
            rows[(c, j)] = m
    return rows


def qrows(m):
    """Q_m: unit c (0..3), block j (0..m-1), wire c*m + j; row (c,j) = E_c on block j + S_c on block j-1."""
    rows = {}
    for c in range(4):
        E = 15 ^ (1 << c)
        S = (1 << c) | (1 << ((c + 1) % 4))
        for j in range(m):
            v = 0
            for u in range(4):
                if E >> u & 1:
                    v |= 1 << (u * m + j)
                if S >> u & 1:
                    v |= 1 << (u * m + (j - 1) % m)
            rows[(c, j)] = v
    return rows


def evaluate(n, gates):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    return vals


def analyse(n, gates, rows, bmask, given=None):
    """rows: {(c,j): mask}; sheet j = rows (.,j); bmask[j] = mask of block j."""
    vals = evaluate(n, gates)
    G = len(gates)
    pos = {}
    for i, v in enumerate(vals):
        pos.setdefault(v, i)
    rep = {"G": G}
    outnode = {}
    for key, r in rows.items():
        if given is not None:
            outnode[key] = given[key]
            assert vals[given[key]] == r
        else:
            assert r in pos, ("missing output", key)
            outnode[key] = pos[r]
    gv = vals[n:]
    rep["distinct"] = len(set(gv)) == G
    rep["nonzero"] = all(v for v in gv)
    rep["not_input"] = all(bin(v).count("1") >= 2 for v in gv)
    rep["dup_values"] = G - len(set(gv))
    rep["zero_values"] = sum(1 for v in gv if v == 0)
    # ancestors
    def anc(node):
        seen, st = set(), [node]
        while st:
            x = st.pop()
            if x < n or x in seen:
                continue
            seen.add(x)
            a, b = gates[x - n]
            st += [a, b]
        return seen
    live = set()
    for nd in outnode.values():
        live |= anc(nd)
    rep["fully_live"] = len(live) == G
    sheets = sorted(set(j for _, j in rows))
    F = {}
    for j in sheets:
        A = set()
        for (c, jj), nd in outnode.items():
            if jj == j:
                A |= anc(nd)
        F[j] = {g for g in A if vals[g] & bmask[j]}
    cnt = Counter(g for j in sheets for g in F[j])
    U_ = set().union(*F.values())
    rep["Fj"] = [len(F[j]) for j in sheets]
    rep["union"] = len(U_)
    rep["E"] = sum(len(F[j]) - 10 for j in sheets)
    rep["R"] = sum(max(m - 1, 0) for m in cnt.values())
    rep["U"] = G - len(U_)
    outs = set(outnode.values())
    rep["charged_outputs"] = len(U_ & outs)
    rep["charged_nonoutputs"] = len(U_ - outs)
    readers = Counter()
    for a, b in gates:
        readers[a] += 1
        readers[b] += 1
    rep["output_fanout_max"] = max(readers[o] for o in outs)
    return rep, vals, outnode, F


def construct(n, unit_of, block_of, rows, order):
    """Section-1 construction. order(key, wires) -> list of wires for the remainder chain of row key."""
    idx = {1 << w: w for w in range(n)}
    gates = []
    targets = set(rows.values())
    hits = []

    def add(a, b, tag):
        v = a ^ b
        if v in idx:
            return v
        if v in targets and tag != "out":
            hits.append(tag)
        gates.append((idx[a], idx[b]))
        idx[v] = n + len(gates) - 1
        return v

    z = []
    for c in range(4):
        ws = [w for w in range(n) if unit_of(w) == c]
        acc = 1 << ws[0]
        for w in ws[1:]:
            acc = add(acc, 1 << w, "z")
        z.append(acc)
    a = add(z[0], z[1], "H"); b = add(z[2], z[3], "H")
    H = [add(z[1], b, "H"), add(z[0], b, "H"), add(a, z[3], "H"), add(a, z[2], "H")]
    nglob = len(gates)
    for key in sorted(rows):
        c, j = key
        r = H[c] ^ rows[key]
        ws = order(key, [w for w in range(n) if r >> w & 1])
        acc = 1 << ws[0]
        for w in ws[1:]:
            acc = add(acc, 1 << w, "rem")
        add(H[c], acc, "out")
    return gates, nglob, hits


def transpose(n, gates, outnode_list, policy, rng=None):
    """Transpose: C^T inputs = outputs of C (index = position in outnode_list), C^T outputs = inputs of C.
    For each node v with d(v) terms (readers + output port) build a chain of d(v)-1 gates; policy orders terms."""
    N = n + len(gates)
    readers = [[] for _ in range(N)]
    for t, (a, b) in enumerate(gates):
        readers[a].append(n + t)
        readers[b].append(n + t)
    outport = {nd: i for i, nd in enumerate(outnode_list)}
    m = len(outnode_list)
    tg = []          # transposed gates over C^T node ids (inputs 0..m-1)
    tnode = [None] * N
    for v in range(N - 1, -1, -1):
        terms = [("r", w) for w in readers[v]]
        if v in outport:
            terms.append(("o", outport[v]))
        if policy == "reader":
            pass
        elif policy == "reverse":
            terms = terms[::-1]
        elif policy == "outfirst":
            terms = sorted(terms, key=lambda t: (t[0] != "o", t[1]))
        else:
            rng.shuffle(terms)
        ids = [tnode[t[1]] if t[0] == "r" else t[1] for t in terms]
        assert ids, "dead node"
        acc = ids[0]
        for x in ids[1:]:
            tg.append((acc, x))
            acc = m + len(tg) - 1
        tnode[v] = acc
    return tg, [tnode[i] for i in range(n)]


def report(name, rep):
    keys = ["G", "distinct", "nonzero", "not_input", "fully_live", "union", "charged_nonoutputs",
            "charged_outputs", "E", "R", "U", "Fj", "output_fanout_max", "dup_values", "zero_values"]
    print(name, {k: rep[k] for k in keys})


def main():
    M = mixcolumns()
    # sanity: own-block part of row (c,j) is E_c
    for (c, j), v in M.items():
        own = sum(1 << k for k in range(4) if v >> (8 * k + j) & 1)
        assert own == 15 ^ (1 << c)
    bm = {j: sum(1 << (8 * k + j) for k in range(4)) for j in range(8)}
    wins = {j: [b for b in range(8) if M[(0, j)] & bm[b]] for j in range(8)}
    print("MC windows", wins)
    print("== task 1: witness files")
    for fn in ["witness_mc_wire.json", "witness_mc_block.json"]:
        gates = [tuple(g) for g in json.load(open(os.path.join(WIT, fn)))]
        rep, vals, outnode, F = analyse(32, gates, M, bm)
        report(fn, rep)
        # globals reading pattern: does any non-global gate read a global other than via the output step?
    print("== task 1: own rebuild, several remainder orders")
    unit = lambda w: w // 8
    blk = lambda w: w % 8
    orders = {"wire": lambda k, ws: sorted(ws), "block": lambda k, ws: sorted(ws, key=lambda w: (w % 8, w // 8)),
              "rev-wire": lambda k, ws: sorted(ws, reverse=True)}
    for s in range(5):
        rr = random.Random(100 + s)
        orders["rand%d-per-row" % s] = (lambda rr: lambda k, ws: rr.sample(ws, len(ws)))(rr)
        perm = list(range(32)); random.Random(200 + s).shuffle(perm)
        orders["rand%d-global" % s] = (lambda p: lambda k, ws: sorted(ws, key=lambda w: p[w]))(perm)
    built = {}
    for nm, od in orders.items():
        gates, ng, hits = construct(32, unit, blk, M, od)
        rep, *_ = analyse(32, gates, M, bm)
        built[nm] = gates
        print(nm, "globals", ng, "target-hits", len(hits), {k: rep[k] for k in
              ["G", "distinct", "fully_live", "union", "charged_nonoutputs", "E", "R", "U"]})
    # can a remainder prefix equal an output for SOME order? support inclusion check (32 x 32)
    zc = [sum(1 << (8 * c + j) for j in range(8)) for c in range(4)]
    H = [zc[(c + 1) % 4] ^ zc[(c + 2) % 4] ^ zc[(c + 3) % 4] for c in range(4)]
    inc = [(k, kk) for k in M for kk in M if k != kk and (M[kk] & ~(H[k[0]] ^ M[k])) == 0]
    print("pairs (row y', remainder r) with supp(y') inside supp(r):", len(inc), inc[:4])
    print("remainder weights", sorted(set(bin(H[c] ^ M[(c, j)]).count("1") for (c, j) in M)))
    # blocks of r
    print("B(r) sizes", sorted(set(sum(1 for b in range(8) if (H[c] ^ M[(c, j)]) & bm[b]) for (c, j) in M)))
    print("== task 3: Q_m")
    for m in [4, 5, 6, 8]:
        Q = qrows(m)
        bq = {j: sum(1 << (u * m + j) for u in range(4)) for j in range(m)}
        gates, ng, hits = construct(4 * m, lambda w: w // m, lambda w: w % m, Q,
                                    lambda k, ws: sorted(ws, key=lambda w: (w % m, w // m)))
        rep, *_ = analyse(4 * m, gates, Q, bq)
        print("Q_%d" % m, "8m+2=", 8 * m + 2, "hits", len(hits), {k: rep[k] for k in
              ["G", "distinct", "nonzero", "not_input", "fully_live", "union", "charged_nonoutputs", "E", "R", "U", "Fj"]})
    print("== task 4: transposes (M^T sheets: rows x_(k,b), sheet b, own block b)")
    MT = {}
    for k in range(4):
        for b in range(8):
            i = 8 * k + b
            MT[(k, b)] = sum(1 << (8 * c + j) for (c, j) in M if M[(c, j)] >> i & 1)
    winsT = {b: [x for x in range(8) if MT[(0, b)] & bm[x]] for b in range(8)}
    print("M^T windows", winsT)
    keys = sorted(M)
    for fn in ["witness_mc_block.json", "witness_mc_wire.json"]:
        gates = [tuple(g) for g in json.load(open(os.path.join(WIT, fn)))]
        rep, vals, outnode, F = analyse(32, gates, M, bm)
        onl = [outnode[k] for k in keys]   # C^T input index p = position in keys = 8c + j
        assert all(keys[p] == (p // 8, p % 8) for p in range(32))
        res = []
        for pol in ["reader", "reverse", "outfirst"] + ["rand%d" % s for s in range(6)]:
            rng = random.Random(int(pol[4:]) + 31) if pol.startswith("rand") else None
            tg, tout = transpose(32, gates, onl, pol, rng)
            tv = evaluate(32, tg)
            assert all(tv[tout[8 * k + b]] == MT[(k, b)] for k in range(4) for b in range(8))
            # analyse needs output nodes found by value; rows of M^T
            rT, *_ = analyse(32, tg, MT, bm, given={(k, b): tout[8 * k + b] for k in range(4) for b in range(8)})
            res.append((pol, rT["G"], rT["union"], rT["E"], rT["R"], rT["U"], rT["dup_values"], rT["zero_values"],
                        rT["fully_live"]))
        print(fn, "transpose (policy, G, union, E, R, U, dup, zero, live):")
        for r in res:
            print("   ", r)
    # dual test: see rev2.py (needs pruning of dead gates first)
    # dual identity on the witnesses
    for fn in ["witness_mc_wire.json", "witness_mc_block.json"]:
        gates = [tuple(g) for g in json.load(open(os.path.join(WIT, fn)))]
        rep, vals, outnode, F = analyse(32, gates, M, bm)
        d = Counter()
        for a, b in gates:
            d[a] += 1; d[b] += 1
        for nd in outnode.values():
            d[nd] += 1
        N = 32 + len(gates)
        print(fn, "sum(d-1) =", sum(d[v] - 1 for v in range(N)), "G =", len(gates),
              "min d =", min(d[v] for v in range(N)), "max input fanout =", max(d[v] for v in range(32)))


if __name__ == "__main__":
    main()
