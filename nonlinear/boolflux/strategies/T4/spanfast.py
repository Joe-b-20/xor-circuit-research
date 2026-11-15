#!/usr/bin/env python3
"""T4: spanscore with fast residue arithmetic: basis sets B = any choice of p2 designs on any subset
of outputs (4^8 cases), plus mixed p2/p3 bases up to size MIXB; all other outputs take their best
design whose x-junk residue (mod stage-1 span) lies in the span of B's constituent residues.
    python3 spanfast.py FILE [MIXB] [TOP]"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red  # noqa

DES = [('p3', ((a, b),)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
SAVE = {'p3': 1, 'p2': 2}


def span_add(piv, v):
    for h in sorted(piv, reverse=True):
        if (v >> h) & 1: v ^= piv[h]
    if v: piv[v.bit_length() - 1] = v; return True
    return False


def in_span(piv, v):
    for h in sorted(piv, reverse=True):
        if (v >> h) & 1: v ^= piv[h]
    return v == 0


if __name__ == '__main__':
    c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
    mixb = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    outs = decompose(c, T, la, ba, 4)
    ys = sorted({y for d in outs for y in d})
    S1 = Red([qform(T[s]) for s in fa if la[s] == 1])
    pfree = {pr: ((ys[pr[0]] & ys[pr[1]]) in V) for pr in itertools.combinations(range(4), 2)}
    dsum = {}
    for di, d in enumerate(DES):
        s = 0
        for a, b in d[1]: s ^= ys[a] & ys[b]
        dsum[di] = s in V
    cons = {}; res = {}
    for k in range(8):
        w = [lin(outs[k].get(y, 0)) for y in ys]
        for di, d in enumerate(DES):
            cs = [S1.red(wedge(w[a], w[b])) for a, b in d[1]]
            cons[(k, di)] = cs
            r = 0
            for x in cs: r ^= x
            res[(k, di)] = r
    items = sorted(res)
    p2items = [it for it in items if DES[it[1]][0] == 'p2']

    def evaluate(B):
        piv = {}
        cost = 0
        for it in B:
            for x in cons[it]:
                if span_add(piv, x): cost += 1      # only independent junk ANDs are built
        chosen = list(B); used = {it[0] for it in B}
        for k in range(8):
            if k in used: continue
            opts = [it for it in items if it[0] == k and in_span(piv, res[it])]
            if opts: chosen.append(max(opts, key=lambda it: SAVE[DES[it[1]][0]]))
        sav = sum(SAVE[DES[di][0]] for k, di in chosen)
        dp = set()
        for k, di in chosen:
            if dsum[di]: continue
            for pr in DES[di][1]:
                if not pfree[pr]: dp.add(pr)
        return sav - cost - len(dp), chosen, cost, len(dp)
    results = []
    # all-p2 bases
    for mask in itertools.product(range(4), repeat=8):
        B = [(k, 6 + m - 1) for k, m in enumerate(mask) if m]       # m in 1..3 -> p2 index 6..8
        if not B: continue
        results.append(evaluate(B))
    # mixed small bases
    for nb in range(1, mixb + 1):
        for B in itertools.combinations(items, nb):
            if len({it[0] for it in B}) < nb: continue
            if all(DES[it[1]][0] == 'p2' for it in B): continue
            results.append(evaluate(list(B)))
    results.sort(key=lambda z: -z[0])
    seen = set(); n = 0
    for net, chosen, cost, dj in results:
        key = tuple(sorted(chosen))
        if key in seen: continue
        seen.add(key); n += 1
        print(json.dumps({'net': net, 'A': 48 - net, 'choice': [(k, DES[di]) for k, di in chosen], 'xjunk': cost, 'djunk': dj}))
        if n >= top: break
