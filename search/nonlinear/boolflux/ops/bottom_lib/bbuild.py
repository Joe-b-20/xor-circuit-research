#!/usr/bin/env python3
"""Build a circuit from a bopt.py plan: the source circuit's front (fan-in cones of its four
base Y-forms), Y-sums, x-forms, rank-1 products, output XOR trees (shared pairs first, then
Huffman by level, constant by XNOR).  Checked on all 256 inputs.

    bbuild.py PLAN.json OUT.circ.txt
"""
import json, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import signals as L  # noqa: E402
import bopt  # noqa: E402
from boolflux import aesfn  # noqa: E402
core = L.core
XOR, XNOR, NOT, AND = 6, 9, 3, 8
MODEL = core.Model.load(str(core.MODELS / 'nist.json'))
RNG = None


class Net:
    def __init__(self, c):
        self.n = c.n; self.nodes = {}; self.tab = {}; self.lev = {}
        T, lg, la = L.sim(c)
        for i in range(c.n): self.tab[i] = L.VAR[i]; self.lev[i] = 0
        for j, g in enumerate(c.gates):
            self.nodes[c.n + j] = g; self.tab[c.n + j] = T[c.n + j]; self.lev[c.n + j] = lg[c.n + j]
        self.nid = 100000

    def add(self, op, a, b):
        k = self.nid; self.nid += 1
        self.nodes[k] = (op, a, b)
        self.tab[k] = core.op_apply(op, self.tab[a], self.tab[b], L.ONES)
        self.lev[k] = 1 + max(self.lev[a], self.lev[b])
        return k

    def emit(self, outs, name='p7'):
        n = self.n; order = []; seen = set()
        for o in outs:
            stack = [(o, 0)]
            while stack:
                x, st = stack.pop()
                if x < n: continue
                if st == 0:
                    if x in seen: continue
                    seen.add(x); stack.append((x, 1))
                    op, a, b = self.nodes[x]
                    for y in (b, a):
                        if y >= n and y not in seen: stack.append((y, 0))
                else:
                    order.append(x)
        idx = {i: i for i in range(n)}; gates = []
        for s in order:
            op, a, b = self.nodes[s]
            idx[s] = n + len(gates); gates.append((op, idx[a], idx[b]))
        return core.Circuit(n, 8, gates, [idx[o] for o in outs], name).live()


def huff(levels):
    import heapq
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, 1 + max(a, b))
    return h[0]


def xadd(net, s1, s2):
    pol = (net.tab[s1] ^ net.tab[s2]) & 1
    return net.add(XNOR if pol else XOR, s1, s2)


def bp_synth(net, avail, needx):
    """Boyar-Peralta distance heuristic: add XORs of two available forms until every needed form
    is available; ties broken by the larger Euclidean norm of the distance vector, then by level."""
    needx = set(w for w in needx if w not in avail)
    while needx:
        base = list(avail)
        INF = 99
        d = [INF] * 256
        for m in base: d[m] = 0
        fr = list(base); k = 0
        while fr and k < 8:
            k += 1; nf = []
            for x in fr:
                for m in base:
                    y = x ^ m
                    if y and d[y] == INF: d[y] = k; nf.append(y)
            fr = nf
        tg = sorted(needx)
        # a target at distance 1 is built directly
        direct = [t for t in tg if d[t] == 1]
        if direct:
            t = direct[0]
            best = None
            for m1 in base:
                m2 = t ^ m1
                if m2 in avail:
                    lv = max(net.lev[avail[m1]], net.lev[avail[m2]])
                    if best is None or lv < best[0]: best = (lv, m1, m2)
            avail[t] = xadd(net, avail[best[1]], avail[best[2]]); needx.discard(t); continue
        bestc = None
        for i1 in range(len(base)):
            for i2 in range(i1 + 1, len(base)):
                cnew = base[i1] ^ base[i2]
                if cnew in avail: continue
                dn = [min(d[t], 1 + d[t ^ cnew]) if t != cnew else 0 for t in tg]
                key = (sum(dn), -sum(x * x for x in dn), max(net.lev[avail[base[i1]]], net.lev[avail[base[i2]]]), RNG.random() if RNG else 0)
                if bestc is None or key < bestc[0]: bestc = (key, cnew, base[i1], base[i2])
        _, cnew, m1, m2 = bestc
        avail[cnew] = xadd(net, avail[m1], avail[m2]); needx.discard(cnew)


def build(plan):
    c = L.load(plan['circuit']); n = c.n; cap = plan['cap']
    T, lg, la, base = bopt.base_front(c)
    net = Net(c)
    Ysig = {}; Yneg = {}
    for i, (lv, t, s, pol) in enumerate(base):
        if pol:
            Yneg[1 << i] = s
            op, a, b = c.gates[s - n]
            s = net.add(XNOR if op == XOR else XOR, a, b) if op in (XOR, XNOR) else net.add(NOT, s, s)
        Ysig[1 << i] = s
    choice = [[tuple(p) for p in S] for S in plan['choice']]
    P = sorted({p for S in choice for p in S})
    junk = [(cj[1], cj[2]) for cj in plan['C']]        # per output (v: x-form, yt: Y-sum) fixed extra terms (affine junk)
    # Y-sums
    need = sorted({a & 15 for a, w in P if a & 15 and (a & 15) not in Ysig} | {yt for v, yt in junk if yt and yt not in Ysig},
                  key=lambda a: bin(a).count('1'))
    nat = plan.get('nat')     # absorb5 plans: Y-sums from the base Y-forms' own signals (polarity by XNOR, no NOT level)
    Ys_ = {1 << i: b[2] for i, b in enumerate(base)} if nat else Ysig

    def yadd(s1, s2):
        return xadd(net, s1, s2) if nat else net.add(XOR, s1, s2)
    for a in need:
        best = None
        for b1 in list(Ys_):
            b2 = a ^ b1
            if b2 in Ys_ and b1 < b2:
                lv = max(net.lev[Ys_[b1]], net.lev[Ys_[b2]])
                if best is None or lv < best[0]: best = (lv, b1, b2)
        if best is None:
            bits = [1 << i for i in range(4) if (a >> i) & 1]
            s = Ys_[bits[0]]
            acc = bits[0]
            for bt in bits[1:]:
                acc |= bt
                if acc in Ys_: s = Ys_[acc]; continue
                s = yadd(s, Ys_[bt]); Ys_[acc] = s
        else:
            Ys_[a] = yadd(Ys_[best[1]], Ys_[best[2]])
    if nat:
        for a, sg in Ys_.items():
            if bin(a).count('1') > 1: Ysig[a] = sg
    # x-forms: available forms = inputs + top-layer gates of the front cone
    avail = {1 << i: i for i in range(n)}
    cone = set(); st = [b[2] for b in base]
    while st:
        x = st.pop()
        if x < n or x in cone: continue
        cone.add(x); op, a, b = c.gates[x - n]; st += [a, b]
    allow_old = plan.get('reuse_old', False)
    for s in range(n, n + len(c.gates)):
        if c.gates[s - n][0] not in core.NONLINEAR_OPS and la[s] == 0 and (allow_old or s in cone):
            m = bopt.mask_of(T[s])
            if m is not None and (m not in avail or (T[s] & 1 == 0 and net.tab[avail[m]] & 1)):
                avail[m] = s
    k0 = net.nid
    ONE = bopt.ONE        # affine plans (ops/bottom.py --junk absorb): bit 8 of w = complemented x-form; w == ONE: bare Y-form
    lins = {w & 255 for a, w in P if w != ONE}
    needx = {m for m in lins if m not in avail} | {v for v, yt in junk if v and v not in avail}
    bp_synth(net, avail, needx)
    k1 = net.nid
    poss = {w for a, w in P if not w & ONE} | {v for v, yt in junk if v}
    negs = {w & 255 for a, w in P if w & ONE and w != ONE}
    neg = {}
    for m in negs:                 # complemented twin (XNOR of the same operands, or NOT of an input / a gate of another type)
        sg = avail[m]
        if net.tab[sg] & 1: neg[m] = sg; continue
        op, a, b = net.nodes[sg] if sg >= n else (None, None, None)
        neg[m] = net.add(XNOR if op == XOR else XOR, a, b) if op in (XOR, XNOR) else net.add(NOT, sg, sg)
    for w in poss:
        sg = avail[w]
        if net.tab[sg] & 1:            # complemented form: positive twin
            op, a, b = net.nodes[sg]
            avail[w] = net.add(XNOR if op == XOR else XOR, a, b) if op in (XOR, XNOR) else net.add(NOT, sg, sg)
    CY = bopt.CY          # absorb5 plans: bit CY of alpha = complemented Y operand; alpha == CY: bare x-form (w == ONE: constant)
    for a in sorted({a & 15 for a, w in P if a & CY and a & 15}):
        if a in Yneg: continue
        sg = Ysig[a]
        op, x1, x2 = net.nodes[sg] if sg >= n else (None, None, None)
        Yneg[a] = net.add(XNOR if op == XOR else XOR, x1, x2) if op in (XOR, XNOR) else net.add(NOT, sg, sg)

    def ysg(a):
        return Yneg[a & 15] if a & CY else Ysig[a]

    def xsg(w):
        return neg[w & 255] if w & ONE else avail[w]
    Psig = {}
    for p in P:
        a, w = p
        if not a & 15: Psig[p] = None if w == ONE else xsg(w)
        elif w == ONE: Psig[p] = ysg(a)
        else: Psig[p] = net.add(AND, ysg(a), xsg(w))
    # outputs: shared pairs first
    items = [list(S) for S in choice]
    terms = [[Psig[p] for p in S if Psig[p] is not None] + ([Ysig[yt]] if yt else []) + ([avail[v]] if v else [])
             for S, (v, yt) in zip(choice, junk)]
    while True:
        cnt = Counter()
        for tl in terms:
            for i1 in range(len(tl)):
                for i2 in range(i1 + 1, len(tl)):
                    cnt[tuple(sorted((tl[i1], tl[i2])))] += 1
        pairs = [(k, v) for k, v in cnt.items() if v >= 2]
        pairs.sort(key=lambda kv: (-kv[1], max(net.lev[kv[0][0]], net.lev[kv[0][1]]), RNG.random() if RNG else 0))
        pick = None
        for (s1, s2), v in pairs:
            lv = 1 + max(net.lev[s1], net.lev[s2])
            ok = True
            for tl in terms:
                if s1 in tl and s2 in tl:
                    rest = [net.lev[t] for t in tl if t not in (s1, s2)] + [lv]
                    if huff(rest) > cap: ok = False; break
            if ok: pick = (s1, s2); break
        if pick is None: break
        s1, s2 = pick
        x = net.add(XOR, s1, s2)
        for tl in terms:
            if s1 in tl and s2 in tl:
                tl.remove(s1); tl.remove(s2); tl.append(x)
    k2 = net.nid
    outs = []
    for j, tl in enumerate(terms):
        tl = list(tl)
        while len(tl) > 1:
            tl.sort(key=lambda s: net.lev[s])
            a = tl.pop(0); b = tl.pop(0)
            tl.append(net.add(XOR, a, b))
        s = tl[0]
        cst = plan['C'][j][0]
        if (net.tab[s] ^ T[c.outputs[j]]) == L.ONES:
            op, a, b = net.nodes[s]
            net.nodes[s] = (XNOR if op == XOR else XOR, a, b); net.tab[s] ^= L.ONES
        assert net.tab[s] == T[c.outputs[j]], 'output %d wrong' % j
        outs.append(s)
    k3 = net.nid
    print('phases: ysum %d, xforms %d, ands+pairs %d, out trees %d' % (k0 - 100000, k1 - k0, k2 - k1, k3 - k2))
    global LAST_PHASES
    LAST_PHASES = {'ysum': k0 - 100000, 'xforms': k1 - k0, 'ands_pairs': k2 - k1, 'out_trees': k3 - k2}   # instrumentation
    return net.emit(outs)


def main():
    global RNG
    import random
    plan = json.load(open(sys.argv[1]))
    nc = build(plan)
    tries = int(sys.argv[sys.argv.index('--tries') + 1]) if '--tries' in sys.argv else 0
    for t in range(tries):          # randomised tie-breaks (BP choices, shared pairs); keep the fewest gates
        RNG = random.Random(t + 1)
        c2 = build(plan)
        if tuple(c2.value_table()) == aesfn.table() and c2.metrics(MODEL)['GD'] <= plan['cap'] and len(c2.gates) < len(nc.gates):
            nc = c2
    RNG = None
    assert tuple(nc.value_table()) == aesfn.table(), 'wrong function'
    m = nc.metrics(MODEL)
    print('A AD G GD = %d %d %d %d' % (m['A'], m['AD'], m['G'], m['GD']), m['counts'])
    Path(sys.argv[2]).write_text(core.write_ncff(nc, MODEL, comments=['bbuild.py from plan %s (front %s)' % (sys.argv[1], plan['circuit'])]))


if __name__ == '__main__':
    main()
