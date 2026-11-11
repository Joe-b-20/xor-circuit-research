"""Exhaustive 'split' neighbourhood: for every gate g = x + y and every signal z before g, rewrite
g = (x + z) + (y + z), normalise (duplicates redirected, dead gates removed), and record G and the
excess sum (mu - 1)+.  Reports the smallest G of a normalised circuit that keeps a gate with mu >= 2,
and checks min D_j >= 10 throughout."""
import os
import sys
from common import *

rows = mixcolumns_rows()
rowset = set(rows)


def prune(gates):
    v = masks(gates)
    n = 32
    need, first = set(), {}
    for k in range(len(gates)):
        if v[n + k] in rowset and v[n + k] not in first:
            first[v[n + k]] = n + k
    stack = list(first.values())
    while stack:
        s = stack.pop()
        if s < n or s in need:
            continue
        need.add(s)
        stack.extend(gates[s - n])
    keep = [k for k in range(len(gates)) if n + k in need]
    newidx = {i: i for i in range(n)}
    out = []
    for k in keep:
        newidx[n + k] = n + len(out)
        a, b = gates[k]
        out.append((newidx[a], newidx[b]))
    return out


def normalise(gates):
    v = masks(gates)
    firstof, redirect = {}, {}
    for s in range(len(v)):
        if v[s] in firstof:
            redirect[s] = firstof[v[s]]
        else:
            firstof[v[s]] = s
    return prune([(redirect.get(a, a), redirect.get(b, b)) for a, b in gates])


def info(gates):
    r = charges(gates, rows, "all")
    return r, sum(max(0, x - 1) for x in r["mu"].values())

d = os.path.join(ROOT, "circuits/aes-mixcolumns")
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".circ.txt"):
        continue
    g0, _ = read_ncff(os.path.join(d, fn))
    g0 = normalise(g0)
    n = 32
    hist = {}
    best = None
    for k in range(len(g0)):
        x, y = g0[k]
        for z in range(n + k):
            if z in (x, y):
                continue
            # new gates appended before k: rebuild list with two inserted gates
            g1 = []
            idx = {i: i for i in range(n)}
            for kk in range(len(g0)):
                a, b = g0[kk]
                if kk == k:
                    w1 = n + len(g1)
                    g1.append((idx[x], idx[z]))
                    w2 = n + len(g1)
                    g1.append((idx[y], idx[z]))
                    idx[n + kk] = n + len(g1)
                    g1.append((w1, w2))
                else:
                    idx[n + kk] = n + len(g1)
                    g1.append((idx[a], idx[b]))
            g1 = normalise(g1)
            assert rowset <= set(masks(g1))
            r, exc = info(g1)
            assert min(r["D"]) >= 10
            if exc > 0:
                key = len(g1) - len(g0)
                hist[key] = hist.get(key, 0) + 1
                if best is None or len(g1) < best[0]:
                    best = (len(g1), exc, k, z, r["D"])
    print(fn, "G0", len(g0), "normalised splits keeping mu>=2, by gate increase:", dict(sorted(hist.items())),
          "best", best, flush=True)
