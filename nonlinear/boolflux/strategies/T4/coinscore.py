#!/usr/bin/env python3
"""T4: score coincov hits: best set of per-output rank-2 designs (each output at most one) using
shared x-junk classes; savings = saved products - x-junk ANDs (one representative per class) -
d-junk ANDs (non-free Y-pairs, shared over outputs).  Depth is NOT checked here.
    python3 coinscore.py HITS.jsonl [TOP]"""
import sys, json, itertools
DES = [('p3', (a, b)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
def pairs_of(d): return [tuple(d[1])] if d[0] == 'p3' else [tuple(p) for p in d[1]]
FREE = {(0, 3), (1, 3)}     # d-free Y-pairs of the 48 front (also the p2 sum {(0,2),(1,2)} is free)

def best_saving(hits):
    # members: (k, di) pairs that coincide with at least one other output; group by connectivity
    import collections
    adj = collections.defaultdict(set)
    for k, kind, dk, l, dl, fk, fl in hits:
        adj[(k, dk)].add((l, dl)); adj[(l, dl)].add((k, dk))
    nodes = list(adj)
    # classes = connected components (equal residues are transitive)
    comp = {}; cid = 0
    for v in nodes:
        if v in comp: continue
        st = [v]; comp[v] = cid
        while st:
            u = st.pop()
            for w in adj[u]:
                if w not in comp: comp[w] = cid; st.append(w)
        cid += 1
    classes = collections.defaultdict(list)
    for v, c in comp.items(): classes[c].append(v)
    # exhaustive over choice per output among its options (<= few)
    opts = collections.defaultdict(list)
    for v in nodes: opts[v[0]].append(v)
    outs = sorted(opts)
    best = (0, None)
    def rec(i, chosen):
        nonlocal best
        if i == len(outs):
            if not chosen: return
            sav = 0; cls = collections.defaultdict(list); dpairs = set()
            for (k, di) in chosen:
                d = DES[di]; sav += 1 if d[0] == 'p3' else 2
                cls[comp[(k, di)]].append((k, di))
                for p in pairs_of(d):
                    if p not in FREE: dpairs.add(p)
            cost = 0
            for c, L in cls.items():
                if len(L) < 2: cost += 99           # x-junk not shared
                else: cost += min(len(pairs_of(DES[di])) for k, di in L)
            # p2 sum {(0,2),(1,2)} free together
            if (0, 2) in dpairs and (1, 2) in dpairs: dpairs -= {(0, 2), (1, 2)}
            cost += len(dpairs)
            net = sav - cost
            if net > best[0]: best = (net, list(chosen))
            return
        rec(i + 1, chosen)
        for v in opts[outs[i]]:
            rec(i + 1, chosen + [v])
    if len(outs) <= 8 and sum(len(opts[o]) + 1 for o in outs) < 40: rec(0, [])
    return best

if __name__ == '__main__':
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    res = []
    for ln in open(sys.argv[1]):
        r = json.loads(ln)
        net, ch = best_saving(r['hits'])
        if net > 0: res.append((net, r['class'], r['g'], ch, r['n']))
    res.sort(key=lambda z: -z[0])
    from collections import Counter
    print('net saving histogram', Counter(z[0] for z in res))
    for z in res[:top]:
        print(json.dumps({'net': z[0], 'class': z[1], 'g': z[2], 'choice': [(k, DES[di]) for k, di in z[3]], 'nhits': z[4]}))
