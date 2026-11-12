"""Item 2: at each cut build a circuit whose near side is (nonunit oms first gates) + one entry per
meeting row, far side computes the labels (s-parts) and the non-meeting rows. Verify it."""
import olib

def gen_transpose(gates, outs, n, m, order="fwd"):
    """circuit over m inputs (input o = original output o); returns gates, tout[i] node for orig input i."""
    L = n + len(gates)
    term = {}
    for o, node in enumerate(outs):
        term.setdefault(node, []).append(o)
    readers = {}
    for gi, (a, b) in enumerate(gates):
        for x in (a, b):
            readers.setdefault(x, []).append(n + gi)
    tg = []; adj = {}
    for v in reversed(range(L)):
        idxs = list(term.get(v, [])) + [adj[r] for r in readers.get(v, []) if adj[r] is not None]
        if not idxs:
            adj[v] = None; continue
        acc = idxs[0]
        for x in idxs[1:]:
            tg.append((acc, x)); acc = m + len(tg) - 1
        adj[v] = acc
    return tg, [adj[i] for i in range(n)]

def build(rows, low, n=32):
    nodes = {1 << i: i for i in range(n)}
    gates = []
    def add(a, b):
        v = vals_of(a) ^ vals_of(b)
        gates.append((a, b)); nodes[v] = n + len(gates) - 1
        return nodes[v]
    vals = [1 << i for i in range(n)]
    def vals_of(i): return vals[i]
    def addv(a, b):
        v = vals[a] ^ vals[b]; gates.append((a, b)); vals.append(v); nodes[v] = len(vals) - 1; return len(vals) - 1
    def far_make(t):          # chain over input bits, reusing existing prefixes
        bitsl = [i for i in range(n) if (t >> i) & 1]
        acc = nodes[1 << bitsl[0]]; cur = 1 << bitsl[0]
        for i in bitsl[1:]:
            cur ^= 1 << i
            acc = nodes[cur] if cur in nodes else addv(acc, nodes[1 << i])
        return acc
    meet = [r for r in rows if r & low]
    far_t = [r & ~low for r in meet] + [r for r in rows if not r & low]
    for t in far_t:
        far_make(t)
    nfar = len(gates)
    oms = sorted(set(r & low for r in meet), key=lambda o: bin(o).count("1"))
    pend = [o for o in oms if o not in nodes]
    while pend:
        for o in pend:
            near = [v for v in nodes if v & low and not v & ~low]
            hit = next(((a, a ^ o) for a in near if (a ^ o) in nodes and (a ^ o) & low and not (a ^ o) & ~low), None)
            if hit:
                addv(nodes[hit[0]], nodes[hit[1]]); pend.remove(o); break
        else:
            raise RuntimeError("near side stuck")
    nf = len(gates) - nfar
    for r in meet:
        addv(nodes[r & low], nodes[r & ~low])
    return gates, nfar, nf

def report(name, gates, rows, low):
    comp, red, info = olib.check(gates, rows)
    vals = olib.values(gates); ops = [(vals[a], vals[b]) for a, b in gates]
    st = olib.split(vals, ops, 32, low)
    W = olib.W_info(rows, low)
    print("%s rows %d dimW %d nonunit_oms %d | built %d gates: f %d h %d e %d N %d x %d sigma %d near %d far %d | computes %s reduced %s" % (
        name, W["rows"], W["dimW"], W["nonunit_oms"], len(gates), st["f"], st["h"], st["e"], st["N"], st["x"],
        st["e"] - W["dimW"], st["near"], st["far"], comp, red))
    return st

for b in range(8):
    g, nfar, nf = build(olib.ROWS, olib.PBLOCK[b])
    report("primal block %d:" % b, g, olib.ROWS, olib.PBLOCK[b])
for k in range(8):
    g, nfar, nf = build(olib.MROWS, olib.MBLOCK[k])
    report("mirror group %d:" % k, g, olib.MROWS, olib.MBLOCK[k])
    vals = olib.values(g); pos = {}
    for i, v in enumerate(vals): pos.setdefault(v, i)
    outs = [pos[r] for r in olib.MROWS]          # mirror output i = primal input i
    tg, tout = gen_transpose(g, outs, 32, 32)
    # transposed: input i = primal input i; output for mirror bit 4j+c = primal output 8c+j
    tv = olib.values(tg)
    ok = all(tv[tout[4 * j + c]] == olib.ROWS[8 * c + j] for c in range(4) for j in range(8))
    comp, red, info = olib.check(tg, olib.ROWS)
    print("    transposed back to primal: %d gates, outputs == MixColumns rows: %s, check %s %s" % (len(tg), ok, comp, info))
