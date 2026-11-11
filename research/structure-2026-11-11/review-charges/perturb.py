"""Random function-preserving perturbations of the recorded MixColumns circuits; on each result
check the conclusion of Theorem 7.1 (every sheet has >= 10 gates in D_j) and the formula
G >= 80 - sum (mu-1)+ + #{mu = 0}, under both readings of 'output gate' (every carrier / one
designated carrier).  Usage: python3 perturb.py SEED N"""
import os
import random
import sys
from common import *

rows = mixcolumns_rows()
rowset = set(rows)
seed, N = int(sys.argv[1]), int(sys.argv[2])
rnd = random.Random(seed)

base = []
d = os.path.join(ROOT, "circuits/aes-mixcolumns")
for fn in sorted(os.listdir(d)):
    if fn.endswith(".circ.txt"):
        g, on = read_ncff(os.path.join(d, fn))
        base.append((fn, g))


class Circ:
    def __init__(self, gates):
        self.op = {}
        self.order = []
        for k, (a, b) in enumerate(gates):
            self.op[32 + k] = (a, b)
            self.order.append(32 + k)
        self.nxt = 32 + len(gates)

    def new(self, a, b, before):
        i = self.nxt
        self.nxt += 1
        self.op[i] = (a, b)
        self.order.insert(self.order.index(before) if before is not None else len(self.order), i)
        return i

    def earlier(self, g):
        """signals available strictly before gate g"""
        pos = self.order.index(g) if g is not None else len(self.order)
        return list(range(32)) + self.order[:pos]

    def to_gates(self):
        idx = {i: i for i in range(32)}
        out = []
        for k, g in enumerate(self.order):
            idx[g] = 32 + k
        for g in self.order:
            a, b = self.op[g]
            out.append((idx[a], idx[b]))
        return out

    def vals(self):
        v = {i: 1 << i for i in range(32)}
        for g in self.order:
            a, b = self.op[g]
            v[g] = v[a] ^ v[b]
        return v


def consumers(c, s):
    return [g for g in c.order if s in c.op[g]]


def mutate(c):
    kind = rnd.choice(["dead", "reassoc", "split", "split_far", "dupout", "shuffle", "redirect"])
    v = c.vals()
    g = rnd.choice(c.order)
    a, b = c.op[g]
    if kind == "dead":
        pos = rnd.choice(c.order + [None])
        ear = c.earlier(pos)
        c.new(rnd.choice(ear), rnd.choice(ear), pos)
    elif kind == "reassoc":
        # g = x + y with y = u + w  ->  g = (x + u) + w
        x, y = (a, b) if rnd.random() < 0.5 else (b, a)
        if y >= 32:
            u, w = c.op[y]
            if rnd.random() < 0.5:
                u, w = w, u
            t = c.new(x, u, g)
            c.op[g] = (t, w)
    elif kind in ("split", "split_far"):
        # g = x + y  ->  g = (x + z) + (y + z)
        ear = c.earlier(g)
        if kind == "split_far":
            jb = blocks_of(v[g])
            far = [s for s in ear if not (blocks_of(v[s]) & jb)]
            z = rnd.choice(far) if far else rnd.choice(ear)
        else:
            z = rnd.choice(ear)
        w1 = c.new(a, z, g)
        w2 = c.new(b, z, g)
        c.op[g] = (w1, w2)
    elif kind == "dupout":
        # second carrier of an output value built by a split, and redirect some uses to it
        outs = [s for s in c.order if v[s] in rowset]
        o = rnd.choice(outs)
        x, y = c.op[o]
        ear = c.earlier(o)
        z = rnd.choice(ear)
        w1 = c.new(x, z, None)
        w2 = c.new(y, z, None)
        o2 = c.new(w1, w2, None)
        # move the three new gates right after o, then redirect later consumers randomly
        for t in (w1, w2, o2):
            c.order.remove(t)
        pos = c.order.index(o) + 1
        c.order[pos:pos] = [w1, w2, o2]
        for h in consumers(c, o):
            if c.order.index(h) > c.order.index(o2) and rnd.random() < 0.5:
                p, q = c.op[h]
                c.op[h] = (o2 if p == o else p, o2 if q == o else q)
    elif kind == "shuffle":
        # random topological reorder
        placed, order, rest = set(range(32)), [], list(c.order)
        while rest:
            ready = [h for h in rest if c.op[h][0] in placed and c.op[h][1] in placed]
            h = rnd.choice(ready)
            order.append(h)
            placed.add(h)
            rest.remove(h)
        c.order = order
    elif kind == "redirect":
        # redirect an operand to another (earlier) signal with the same mask, if any
        ear = c.earlier(g)
        same = [s for s in ear if v[s] == v[a] and s != a]
        if same:
            c.op[g] = (rnd.choice(same), b)


stats = dict(circs=0, mu2=0, nonbm=0, minD=99, maxexcess=0)
for it in range(N):
    fn, g0 = rnd.choice(base)
    c = Circ(g0)
    for _ in range(rnd.randint(1, 25)):
        mutate(c)
    gates = c.to_gates()
    vv = masks(gates)
    assert rowset <= set(vv), "perturbation broke the function"
    for mode in ("all", "first"):
        if mode == "all":
            r = charges(gates, rows, "all")
        else:
            # designate the first carrier of each row as the output gate
            first = {}
            for k in range(len(gates)):
                if vv[32 + k] in rowset and vv[32 + k] not in first:
                    first[vv[32 + k]] = 32 + k
            outname = {s: rows.index(m) for m, s in first.items()}
            r = charges(gates, rows, "named", outname)
        mu = r["mu"]
        excess = sum(max(0, m - 1) for m in mu.values())
        zero = sum(1 for m in mu.values() if m == 0)
        assert min(r["D"]) >= 10, ("VIOLATION", fn, r["D"], gates)
        assert r["G"] >= 80 - excess + zero
        assert sum(r["D"]) == sum(mu.values())
        stats["minD"] = min(stats["minD"], min(r["D"]))
        stats["maxexcess"] = max(stats["maxexcess"], excess)
        if mode == "all":
            stats["circs"] += 1
            stats["mu2"] += excess > 0
            stats["nonbm"] += len(r["bm_viol"]) > 0
print("seed", seed, stats)
