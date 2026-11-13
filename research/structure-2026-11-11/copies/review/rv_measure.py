"""Machine review of copies/COPIES.md (phase 10): independent re-measurement.

Own code (own MixColumns matrix, own parsers, own measure). Direct evaluation of specified circuits and ordinary
linear algebra on them only. No SAT, no search, no enumeration of circuits or value sets, no least-gate
computation. The only randomness: random node sets A used to evaluate the stated identity of Theorem F.
usage (WSL): python3 rv_measure.py
"""
import json
import os
import random
import re

ST = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ROOT = os.path.abspath(os.path.join(ST, "..", ".."))
KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")


# ---------------------------------------------------------------- linear algebra
def rk(vs):
    b = []
    for v in vs:
        for x in b:
            v = min(v, v ^ x)
        if v:
            b.append(v)
    return len(b)


# ---------------------------------------------------------------- MixColumns (own)
def gmul(a, m):
    r = 0
    for k in range(8):
        if m >> k & 1:
            t = a
            for _ in range(k):
                t <<= 1
                if t & 0x100:
                    t ^= 0x11B
            r ^= t
    return r


def mc():
    C = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
    rows = {}
    for i in range(4):
        for t in range(8):
            m = 0
            for c in range(4):
                for j in range(8):
                    if gmul(1 << j, C[i][c]) >> t & 1:
                        m |= 1 << (8 * c + j)
            rows[(i, t)] = m
    blocks = [sum(1 << (8 * c + j) for c in range(4)) for j in range(8)]
    sheet = {m: t for (i, t), m in rows.items()}
    return rows, blocks, sheet


MCROWS, MCB, MCSHEET = mc()


def read_ncff(path):
    names, pend = {}, []
    for line in open(path):
        line = line.split("%")[0].strip()
        m = re.match(r"^Inputs:\s*([a-z]+)(\d+):[a-z]+(\d+)", line)
        if m:
            for i in range(int(m.group(2)), int(m.group(3)) + 1):
                names[m.group(1) + str(i)] = i - int(m.group(2))
        m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if m:
            pend.append(m.groups())
    gates = []
    while pend:                       # topological resolution (operands may be named later in the file)
        rest = []
        for o, a, b in pend:
            if a in names and b in names:
                gates.append((names[a], names[b]))
                names[o] = 32 + len(gates) - 1
            else:
                rest.append((o, a, b))
        assert len(rest) < len(pend)
        pend = rest
    return gates


def read_kste(fn, line):
    ls = [l for l in open(os.path.join(KSTE, fn)) if l.strip()]
    return [(int(a), int(b)) for a, b in re.findall(r"\((\d+),\s*(\d+)\)", ls[line - 1])]


def evalc(n, gates):
    v = [1 << i for i in range(n)]
    for a, b in gates:
        assert a < len(v) and b < len(v)
        v.append(v[a] ^ v[b])
    return v


# ---------------------------------------------------------------- the measure (COPIES section 2)
def measure(name, n, gates, outs, B, sheet_of=None, ownblock=None, per_sheet=10, quiet=False):
    """outs: list of output values; B: block masks; sheet_of: value -> sheet; ownblock: sheet -> block."""
    val = evalc(n, gates)
    N = len(val)
    assert all(o in val for o in outs), name + " does not compute its outputs"
    reduced = len(set(val)) == N and 0 not in val
    onode = {o: val.index(o) for o in outs}
    outset = set(outs)
    G = len(gates)
    allB = (1 << n) - 1
    pr = lambda v, S: v & sum(B[c] for c in S)
    ev = []                                    # (gate node, a, b, C, copy)
    for i, (a, b) in enumerate(gates):
        e = val[n + i]
        C = [c for c in range(len(B)) if val[a] & B[c] and not e & B[c]]
        if C:
            assert pr(val[a], C) == pr(val[b], C)      # Lemma S1
            ev.append((n + i, a, b, C, pr(val[a], C)))
    copies = [x[4] for x in ev]
    blockcopies = [pr(val[x[1]], [c]) for x in ev for c in x[3]]
    ins = [1 << i for i in range(n)]
    isout = lambda node: val[node] in outset
    Q0 = rk(copies)
    QX = rk(copies + ins) - rk(ins)
    QY = rk(copies + outs) - rk(outs)
    ev2 = [x for x in ev if x[1] >= n and x[2] >= n and not isout(x[1]) and not isout(x[2])]
    Q2 = rk([x[4] for x in ev2])
    nonout = sum(1 for i in range(G) if not isout(n + i))
    byop = {}
    for x in ev:
        for p in (x[1], x[2]):
            byop.setdefault(p, []).append(x[4])
    cap = max([(rk(v), p) for p, v in byop.items()], default=(0, -1))
    res = dict(name=name, G=G, Y=len(outset), reduced=reduced, nonout=nonout, events=len(ev),
               ev_out=sum(isout(x[0]) for x in ev), Q0=Q0, QX=QX, QY=QY, Q2=Q2, ev2=len(ev2), cap=cap,
               Qblock=rk(blockcopies), sumC=sum(len(x[3]) for x in ev),
               Csets=sorted(set(tuple(x[3]) for x in ev)))
    if sheet_of is not None:
        sheets = sorted(set(sheet_of.values()))
        W = {j: [c for c in range(len(B)) if any(o & B[c] for o in outs if sheet_of[o] == j)] for j in sheets}
        readers = [[] for _ in range(N)]
        for i, (a, b) in enumerate(gates):
            readers[a].append(n + i)
            readers[b].append(n + i)
        # anc-or-self of sheet j outputs
        anc = {}
        for j in sheets:
            st, A = [onode[o] for o in outs if sheet_of[o] == j], set()
            while st:
                x = st.pop()
                if x not in A:
                    A.add(x)
                    if x >= n:
                        st.extend(gates[x - n])
            anc[j] = A
        us, best = [], (0, -1)
        for x in range(N):
            js = [j for j in sheets if x in anc[j]]
            if len(js) >= 2:
                ux = [val[x] & ~sum(B[c] for c in W[j]) & allB for j in js]
                ux = [u for u in ux if u]
                us += ux
                best = max(best, (rk(ux), x))
        res["recip"] = (rk(us), best)
        # alternative linear baseline (not in the note): per sheet, copies of events that are anc-or-self of
        # sheet j outputs, modulo the span of the other sheets' outputs
        qo = 0
        for j in sheets:
            oth = [o for o in outs if sheet_of[o] != j]
            cj = [x[4] for x in ev if x[0] in anc[j]]
            qo += rk(cj + oth) - rk(oth)
        res["Qother"] = qo
        # charges (RECORD 7): F_j = anc-or-self of sheet j outputs, gates only, nonzero on own block
        if ownblock is not None:
            F = {j: {g for g in anc[j] if g >= n and val[g] & B[ownblock[j]]} for j in sheets}
            mu = [sum(g in F[j] for j in sheets) for g in range(n, N)]
            res["E"] = sum(len(F[j]) - per_sheet for j in sheets)
            res["R"] = sum(max(m - 1, 0) for m in mu)
            res["U"] = sum(m == 0 for m in mu)
            res["Fj"] = [len(F[j]) for j in sheets]
            res["charged"] = sum(m > 0 for m in mu)
            assert G == per_sheet * len(sheets) + res["E"] - res["R"] + res["U"]
        res["W"] = W
    if not quiet:
        print(fmt(res))
    return res, val, ev


def fmt(r):
    s = ("%s: G %d |Y| %d reduced %s nonout %d | events %d (at outputs %d) Q0 %d QX %d QY %d | Q2 %d (from %d "
         "events) | max partner cap %d (node %d) | per-(event,block) rank %d, sum|C| %d | C-sets %s"
         % (r["name"], r["G"], r["Y"], r["reduced"], r["nonout"], r["events"], r["ev_out"], r["Q0"], r["QX"],
            r["QY"], r["Q2"], r["ev2"], r["cap"][0], r["cap"][1], r["Qblock"], r["sumC"], r["Csets"][:6]))
    if "recip" in r:
        s += " | recipient rank %d, one node %d (node %d) | per-sheet other-outputs baseline %d" % (
            r["recip"][0], r["recip"][1][0], r["recip"][1][1], r["Qother"])
    if "E" in r:
        s += " | E %d R %d U %d charged %d" % (r["E"], r["R"], r["U"], r["charged"])
    return s


# ---------------------------------------------------------------- constructions from the note's text
def sanity():
    # inputs x, y, z, w = 0..3; p = x + y; (x + z) + p = y + z; (y + w) + p = x + w
    g = [(0, 1), (0, 2), (1, 3), (5, 4), (6, 4)]
    return measure("sanity", 4, g, [0b0110, 0b1001], [1 << i for i in range(4)])


def chain(n):
    g = [(0, 1)]
    for i in range(2, n):
        g.append((n + len(g) - 1, i))
    S = n + len(g) - 1
    for i in range(n - 1):     # S + x_i, i = 1..n-1 (1-based); S + x_n is the prefix P_(n-1)
        if i == n - 2 and False:
            pass
        g.append((S, i))
    val = evalc(n, g)
    outs = val[n:]
    # S + x_(n-1) (0-based i = n-2) is NOT a prefix; S + x_n would be. The note: S + x_i for i < n (1-based)
    return measure("chain n=%d" % n, n, g, outs, [1 << i for i in range(n)])


def pairs(k):
    P = [(i, j) for i in range(k) for j in range(i + 1, k)]
    n = len(P)
    g, outs, anode = [], [], {}
    for i in range(k):
        mine = [t for t, p in enumerate(P) if i in p]
        acc = mine[1]
        for t in mine[2:]:                 # v_i chain: prefixes declared outputs
            g.append((acc, t))
            acc = n + len(g) - 1
            outs.append(acc)
        g.append((mine[0], acc))           # a_i = x_first + v_i
        anode[i] = n + len(g) - 1
    for i in range(k):
        for j in range(i + 1, k):
            g.append((anode[i], anode[j]))
            outs.append(n + len(g) - 1)
    val = evalc(n, g)
    return measure("pairs k=%d" % k, n, g, [val[o] for o in outs], [1 << i for i in range(n)])


def q3_rows(m=3):
    E = lambda c: 15 ^ (1 << c)
    s = lambda c: (1 << c) | (1 << ((c + 1) % 4))
    rows = {}
    for j in range(m):
        for c in range(4):
            rows[(E(c) << (4 * j)) | (s(c) << (4 * ((j - 1) % m)))] = j
    return rows


def q3():
    ls = [l.split("#")[0].strip() for l in open(os.path.join(ST, "rotation", "circuits", "q3_28.txt"))]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    rows = q3_rows()
    return measure("Q_3 q3_28", n, g, list(rows), [15 << (4 * j) for j in range(3)], rows,
                   ownblock={j: j for j in range(3)})


def mcm(name, g, quiet=False):
    return measure(name, 32, g, list(MCROWS.values()), MCB, MCSHEET, ownblock={j: j for j in range(8)},
                   quiet=quiet)


# ---------------------------------------------------------------- Theorem F, general A
def theoremF(name, n, gates, outs, B, trials=300, seed=1):
    val = evalc(n, gates)
    N = len(val)
    onode = [val.index(o) if o in val else None for o in outs]
    readers = [[] for _ in range(N)]
    for i, (a, b) in enumerate(gates):
        readers[a].append(n + i)
        readers[b].append(n + i)
    rho = [0] * N
    outbits = {}
    for r, o in enumerate(onode):
        outbits[o] = outbits.get(o, 0) | (1 << r)
    for v in range(N - 1, -1, -1):
        acc = outbits.get(v, 0)
        for g in readers[v]:
            acc ^= rho[g]
        rho[v] = acc
    rnd = random.Random(seed)
    fails = 0
    kinds = []
    for b in range(len(B)):                    # J6 case: A = pure-b signals, K = block b
        A = {x for x in range(N) if val[x] and val[x] & ~B[b] == 0}
        kinds.append(("pure", A, B[b]))
    for t in range(trials):                    # random A, not ancestor-closed, K random union of blocks
        Ks = [c for c in range(len(B)) if rnd.random() < 0.4] or [0]
        K = sum(B[c] for c in Ks)
        p = rnd.random()
        A = {x for x in range(N) if (x < n and (1 << x) & K) or rnd.random() < p}
        kinds.append(("rand", A, K))
    for kind, A, K in kinds:
        vA = [0] * N
        for x in range(N):
            if x not in A:
                continue
            if x < n:
                vA[x] = 1 << x
            else:
                a, b = gates[x - n]
                vA[x] = (vA[a] if a in A else 0) ^ (vA[b] if b in A else 0)
        rhs = [0] * len(outs)
        for i, (a, b) in enumerate(gates):
            gnode = n + i
            if gnode in A:
                continue
            for p_ in (a, b):
                if p_ in A:
                    for r in range(len(outs)):
                        if rho[gnode] >> r & 1:
                            rhs[r] ^= vA[p_] & K
        for r, o in enumerate(onode):
            if o in A:
                rhs[r] ^= vA[o] & K
        fails += sum(rhs[r] != outs[r] & K for r in range(len(outs)))
    print("Theorem F, %s: %d node sets (%d pure-block J6 cases, %d random non-closed), failures %d"
          % (name, len(kinds), len(B), trials, fails))


# ---------------------------------------------------------------- zero-block restriction (ACCOUNT J1 rule)
def removed_at(n, gates, Bmask):
    """ACCOUNT section 1: zero the blocks in Bmask; return the set of removed gate nodes."""
    val = evalc(n, gates)
    keep = ~Bmask
    seen = {0} | {(1 << i) & keep for i in range(n)}
    rem = set()
    for i in range(len(gates)):
        im = val[n + i] & keep
        if im in seen:
            rem.add(n + i)
        seen.add(im)
    return rem


def event_removal(name, n, gates, ev, B):
    tot = lost_zero = lost_keep = 0
    for (e, a, b, C, k) in ev:
        for c in C:
            tot += 1
            lost_zero += e in removed_at(n, gates, B[c])
            lost_keep += e in removed_at(n, gates, ((1 << n) - 1) & ~B[c])
    print("%s: (event, cancelled block c) pairs %d; event removed when ZEROING c (D_c, ACCOUNT J2): %d; "
          "removed when KEEPING only c: %d" % (name, tot, lost_zero, lost_keep))


# ---------------------------------------------------------------- block-monotone (RECORD 7 sense) with Q2 > 0
def record_monotone(n, gates, outs):
    val = evalc(n, gates)
    N = len(val)
    blk = lambda v: {j for j in range(8) if v & MCB[j]}
    onodes = [val.index(o) for o in outs]
    for o in onodes:
        st, A = [o], set()
        while st:
            x = st.pop()
            if x not in A:
                A.add(x)
                if x >= n:
                    st.extend(gates[x - n])
        for g in A:
            if g >= n and not blk(val[g]) <= blk(val[o]):
                return False
    return True


def monotone_with_event(g88):
    val = evalc(32, g88)
    blk = lambda v: {j for j in range(8) if v & MCB[j]}
    # an output of sheet 2 (window {1, 2})
    o_val = [m for (i, t), m in MCROWS.items() if t == 2][0]
    onode = val.index(o_val)
    p, q = g88[onode - 32]
    w = lambda c, j: 8 * c + j
    x02, x01, x11 = w(0, 2), w(0, 1), w(1, 1)
    pos = onode - 32
    new = []
    base = 32 + pos
    # t1 = p + x01, t2 = t1 + x11, d = t2 + q, a = x02 + x01, bb = x02 + x11, e = a + bb, o = d + e
    new = [(p, x01), (base, x11), (base + 1, q), (x02, x01), (x02, x11), (base + 3, base + 4), (base + 2, base + 5)]
    shift = len(new) - 1

    def rem(x):
        if x < onode:
            return x
        if x == onode:
            return base + 6
        return x + shift
    g = list(g88[:pos]) + new + [(rem(a), rem(b)) for a, b in g88[pos + 1:]]
    r, v2, ev = measure("r88 modified (sheet-2 output rebuilt through a block-2 cancellation)", 32, g,
                        list(MCROWS.values()), MCB, MCSHEET, ownblock={j: j for j in range(8)})
    print("   RECORD-7 block-monotone:", record_monotone(32, g, list(MCROWS.values())),
          "| J8 block-monotone (no event):", r["events"] == 0)


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    print("== MixColumns windows (own matrix):",
          {j: [c for c in range(8) if any(m & MCB[c] for m, t in MCSHEET.items() if t == j)] for j in range(8)})
    sanity()
    for n in (3, 4, 8):
        chain(n)
    try:
        chain(2)
    except AssertionError as ex:
        print("chain n=2: fails (", ex, ")")
    for k in (5, 6, 8):
        pairs(k)
    try:
        pairs(4)
    except AssertionError as ex:
        print("pairs k=4: fails")
    rq, vq, evq = q3()
    g88 = read_ncff(os.path.join(ROOT, "circuits", "aes-mixcolumns", "aes-mixcolumns-xor88-depth5.circ.txt"))
    g89 = read_ncff(os.path.join(ROOT, "circuits", "aes-mixcolumns", "aes-mixcolumns-xor89-depth4.circ.txt"))
    r88, v88, e88 = mcm("MC r88", g88)
    mcm("MC r89", g89)
    W = {}
    for nm in ("block", "wire"):
        gw = [tuple(x) for x in json.load(open(os.path.join(ST, "cancel", "witness", "witness_mc_%s.json" % nm)))]
        W[nm] = (gw,) + mcm("MC witness " + nm, gw)
    tri = {}
    for fn, ln in (("circuits_3.txt", 1451), ("circuits_3.txt", 3001), ("circuits_3.txt", 7451),
                   ("circuits_3.txt", 7651), ("circuits_2.txt", 783)):
        gt = read_kste(fn, ln)
        tri[(fn, ln)] = (gt,) + mcm("MC %s:%d" % (fn, ln), gt)

    print("\n== witness details (block order)")
    gw, rw, vw, ew = W["block"]
    H = {}
    for c in range(4):     # H_c = parity of the three other bytes
        H[c] = sum(1 << (8 * cc + j) for cc in range(4) if cc != c for j in range(8))
    Hnode = {c: vw.index(H[c]) for c in range(4)}
    print("H_c nodes:", Hnode)
    ok = all(vw[e] in MCROWS.values() and (vw[a] in H.values() or vw[b] in H.values()) for e, a, b, C, k in ew)
    print("every event is an output gate y = H_c + r:", ok, "| C-set sizes:", sorted(set(len(x[3]) for x in ew)))
    for c in range(4):
        us = [H[c] & ~sum(MCB[b] for b in rw["W"][j]) for j in range(8)]
        print("  H_%d: outside-window parts rank %d, block counts %s" % (
            c, rk(us), sorted(set(sum(1 for b in range(8) if u & MCB[b]) for u in us))))
    rblocks = set()
    for (c, j), y in MCROWS.items():
        rr = y ^ H[c]
        rblocks.add(sum(1 for b in range(8) if rr & MCB[b]))
    print("  full remainders r = H_c + y occupy block counts:", sorted(rblocks))
    # H_c restricted to {j-1, j} minus row restricted: is it supported on block j-1 only? (relative charge test)
    okfree = True
    for (c, j), y in MCROWS.items():
        a = (j - 1) % 8
        mask = MCB[j] | MCB[a]
        d = (y ^ H[c]) & mask
        okfree &= d & MCB[j] == 0
    print("  for every row (c, j): (row + H_c) restricted to blocks {j-1, j} has zero block-j part:", okfree)

    print("\n== event removal under ACCOUNT's zero-one-block restriction (COPIES section 6 claim)")
    event_removal("witness block", 32, gw, ew, MCB)
    for key, (gt, rt, vt, et) in tri.items():
        event_removal("%s:%d" % key, 32, gt, et, MCB)
    event_removal("Q_3", 12, [tuple(map(int, l.split()[:2])) for l in
                              [l.split("#")[0].strip() for l in open(os.path.join(ST, "rotation", "circuits", "q3_28.txt"))
                               if l.split("#")[0].strip()][1:29]], evq, [15 << (4 * j) for j in range(3)])

    print("\n== Theorem F (first-exit identity) for general node sets A")
    theoremF("r88", 32, g88, list(MCROWS.values()), MCB)
    theoremF("witness block", 32, gw, list(MCROWS.values()), MCB, trials=60)
    for key, (gt, rt, vt, et) in list(tri.items())[:2]:
        theoremF("%s:%d" % key, 32, gt, list(MCROWS.values()), MCB, trials=150)
    gq = [tuple(map(int, l.split()[:2])) for l in
          [l.split("#")[0].strip() for l in open(os.path.join(ST, "rotation", "circuits", "q3_28.txt"))
           if l.split("#")[0].strip()][1:29]]
    theoremF("Q_3", 12, gq, list(q3_rows()), [15 << (4 * j) for j in range(3)])
    # outputs with readers, and an input that is also an output
    n = 8
    g = [(0, 1)]
    for i in range(2, n):
        g.append((n + len(g) - 1, i))
    for i in range(n - 1):
        g.append((n + 6, i))
    v = evalc(n, g)
    theoremF("chain n=8 + input x_3 as an output", n, g, v[n:] + [1 << 3], [1 << i for i in range(n)])

    print("\n== a block-monotone (RECORD 7 sense) MixColumns circuit with Q2 > 0")
    monotone_with_event(g88)
