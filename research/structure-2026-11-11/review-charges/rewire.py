"""Equal-cost rewiring neighbourhood of the recorded MixColumns circuits.
Move: pick gate h, replace its operands by any pair of signals (x', y') available before h (in the
current order) with mask(x') ^ mask(y') = mask(h); then delete gates that are no longer ancestors of
an output carrier.  G never increases.  We look for circuits with a gate of mu >= 2 (cross-sheet
sharing that survives normalisation) and record the smallest G seen among them.
Then a random plateau walk of such moves (plus topological reshuffles to expose new pairs).
Usage: python3 rewire.py SEED STEPS"""
import os
import random
import sys
from common import *

rows = mixcolumns_rows()
rowset = set(rows)
seed, STEPS = int(sys.argv[1]), int(sys.argv[2])
rnd = random.Random(seed)


def prune(gates):
    v = masks(gates)
    n = 32
    need = set()
    first = {}
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
    # also: redirect duplicate masks to the first carrier
    keep = [k for k in range(len(gates)) if n + k in need]
    newidx = {i: i for i in range(n)}
    out = []
    for k in keep:
        newidx[n + k] = n + len(out)
        a, b = gates[k]
        out.append((newidx[a], newidx[b]))
    return out


def normalise(gates):
    """remove duplicate-mask gates (redirect to first occurrence) and dead gates"""
    v = masks(gates)
    n = 32
    firstof = {}
    redirect = {}
    for s in range(len(v)):
        if v[s] in firstof:
            redirect[s] = firstof[v[s]]
        else:
            firstof[v[s]] = s
    g2 = []
    for a, b in gates:
        g2.append((redirect.get(a, a), redirect.get(b, b)))
    return prune(g2)


def info(gates):
    r = charges(gates, rows, "all")
    exc = sum(max(0, x - 1) for x in r["mu"].values())
    return r, exc


d = os.path.join(ROOT, "circuits/aes-mixcolumns")
results = []
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".circ.txt"):
        continue
    g0, _ = read_ncff(os.path.join(d, fn))
    g0 = normalise(g0)
    v = masks(g0)
    n = 32
    nmoves = nmu2 = 0
    best = None
    for k in range(len(g0)):
        h = n + k
        pos = {}
        for s in range(h):
            pos.setdefault(v[s], []).append(s)
        for x in range(h):
            y_mask = v[x] ^ v[h]
            for y in pos.get(y_mask, []):
                if y <= x or {x, y} == set(g0[k]):
                    continue
                g1 = list(g0)
                g1[k] = (x, y)
                g1 = normalise(g1)
                assert rowset <= set(masks(g1))
                nmoves += 1
                r, exc = info(g1)
                if exc > 0:
                    nmu2 += 1
                    if best is None or len(g1) < best[0]:
                        best = (len(g1), exc, k, (x, y))
                if len(g1) < len(g0):
                    print("  !! smaller circuit found", fn, len(g1))
    print(fn, "G", len(g0), "single rewires", nmoves, "with mu>=2 after normalisation", nmu2,
          "smallest such (G, excess, gate, ops)", best, flush=True)
    results.append((fn, g0))

# plateau walk
for fn, g0 in results:
    cur = g0
    seen_mu2 = 0
    minG_mu2 = None
    for step in range(STEPS):
        v = masks(cur)
        k = rnd.randrange(len(cur))
        h = 32 + k
        pos = {}
        for s in range(h):
            pos.setdefault(v[s], []).append(s)
        alts = [(x, y) for x in range(h) for y in pos.get(v[x] ^ v[h], []) if y > x and {x, y} != set(cur[k])]
        if alts:
            g1 = list(cur)
            g1[k] = rnd.choice(alts)
            g1 = normalise(g1)
            r, exc = info(g1)
            assert min(r["D"]) >= 10
            if len(g1) <= len(cur):
                cur = g1
                if exc > 0:
                    seen_mu2 += 1
                    minG_mu2 = len(g1) if minG_mu2 is None else min(minG_mu2, len(g1))
        # reshuffle order (topological) to expose other pairs
        if step % 5 == 0:
            placed, order, rest = set(range(32)), [], list(range(32, 32 + len(cur)))
            while rest:
                ready = [s for s in rest if cur[s - 32][0] in placed and cur[s - 32][1] in placed]
                s = rnd.choice(ready)
                order.append(s)
                placed.add(s)
                rest.remove(s)
            idx = {i: i for i in range(32)}
            for t, s in enumerate(order):
                idx[s] = 32 + t
            cur = [(idx[cur[s - 32][0]], idx[cur[s - 32][1]]) for s in order]
    r, exc = info(cur)
    print("walk", fn, "final G", len(cur), "excess", exc, "steps in mu>=2 states", seen_mu2,
          "min G among them", minG_mu2, "D_j", r["D"], flush=True)
