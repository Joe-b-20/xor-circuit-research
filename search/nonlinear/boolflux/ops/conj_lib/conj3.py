#!/usr/bin/env python3
"""Analytic screen of the 2040 conjugates (conj.py) of a circuit: only the two linear layers change.

top:    the forms (over the circuit inputs) of every AND-free signal read by a non-top gate or output;
        conjugate: form f -> f o G (over the new inputs).  Cost = BP heuristic gate count (bp.py
        bp_run, best of --top-runs), weight-1 forms free.
bottom: the outputs as forms over the leaves of the bottom region (linear gates after the last AND
        level); conjugate: new output i = XOR of old outputs per Mout (+ constant, free as XNOR).
        Cost = Paar greedy pair merging (cheap proxy; same proxy for the identity).
Score = top + bottom, compared with the identity conjugate.  OUT/screen3.jsonl.

    conj3.py FILE --out DIR [--top-runs 4]
"""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import conj as CJ  # noqa
import bp  # noqa
import bottom as BT  # noqa


def layers(c):
    n = c.n
    la, lg = BT.and_levels(c)
    AD = max(la[s] for s in c.outputs)
    S = n + len(c.gates)
    form = {}                           # AND-free signals: 9-bit (const + 8 inputs) masks
    for i in range(n): form[i] = 1 << (1 + i)
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in BT.NL or a not in form or b not in form: continue
        f = form[a] ^ form[b]
        if op == CJ.XNOR: f ^= 1
        elif op == CJ.NOT: f = form[a] ^ 1
        form[s] = f
    readers = set()
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if s in form: continue
        for x in (a, b):
            if x in form: readers.add(x)
    for o in c.outputs:
        if o in form: readers.add(o)
    top = sorted(set(form[s] >> 1 for s in readers))
    # bottom region: linear gates whose AND level == AD
    R = [n + j for j, (op, a, b) in enumerate(c.gates) if op not in BT.NL and la[n + j] == AD]
    Rs = set(R)
    leaves = sorted({x for s in R for x in c.gates[s - n][1:] if x not in Rs})
    # an output outside the bottom region that no region gate reads is a leaf of its own (before 2026-11-17:
    # KeyError); appended after the others, so the leaf numbering of every circuit that worked is unchanged
    leaves += sorted({o for o in c.outputs if o not in Rs and o not in set(leaves)})
    li = {x: i for i, x in enumerate(leaves)}
    bf = {}
    for s in R:
        op, a, b = c.gates[s - n]
        fa = bf[a] if a in Rs else 1 << li[a]
        fb = bf[b] if b in Rs else 1 << li[b]
        bf[s] = fa ^ fb if op != CJ.NOT else fa
    outs = [bf[o] if o in Rs else 1 << li[o] for o in c.outputs]
    return top, outs, len(leaves)


def bp_cost(m, tl, runs, rng):
    tl = [t for t in set(tl) if bin(t).count('1') >= 2]
    best = None
    for _ in range(runs):
        g = bp.bp_run(m, tl, rng, 0.5)
        if g is not None and (best is None or len(g) < best): best = len(g)
    return best


def paar(rows):
    # every leaf bit (before 2026-11-17 only bits 0-63 were read; NIST circuits have at most 32 leaves)
    nb = max([64] + [r.bit_length() for r in rows])
    rows = [set(i for i in range(nb) if r >> i & 1) for r in rows]
    nxt = nb; cost = 0
    while True:
        cnt = {}
        for r in rows:
            l = sorted(r)
            for i in range(len(l)):
                for j in range(i + 1, len(l)):
                    cnt[(l[i], l[j])] = cnt.get((l[i], l[j]), 0) + 1
        if not cnt: break
        p, v = max(cnt.items(), key=lambda kv: kv[1])
        if v < 2: break
        cost += 1
        for r in rows:
            if p[0] in r and p[1] in r: r.discard(p[0]); r.discard(p[1]); r.add(nxt)
        nxt += 1
    return cost + sum(len(r) - 1 for r in rows)


def main():
    a = sys.argv[1:]
    f = a[0]; out = Path(a[a.index('--out') + 1]); out.mkdir(parents=True, exist_ok=True)
    runs = int(a[a.index('--top-runs') + 1]) if '--top-runs' in a else 4
    c = CJ.BT.load(f)
    top, outs, nl = layers(c)
    print('top targets', len(top), 'bottom leaves', nl, flush=True)
    log = open(out / 'screen3.jsonl', 'a')
    t0 = time.time(); res = []
    for k in range(8):
        for lam in range(1, 256):
            G = CJ.matrix(lambda z: CJ.gmul(lam, CJ.gpow(z, 1 << k)))
            Gp = CJ.matrix(lambda w: CJ.gpow(CJ.gmul(lam, w), 1 << ((8 - k) % 8)))
            Mout = CJ.matrix(lambda y: CJ.apply(CJ.A, CJ.apply(Gp, CJ.apply(CJ.Ainv, y))))
            # circuit input i = byte bit 7-i; u_i as form over x (bit i of mask = x_i)
            urow = []
            for i in range(8):
                bit = 7 - i
                urow.append(sum(1 << (7 - j) for j in range(8) if G[j] >> bit & 1))
            ntop = []
            for t in top:
                v = 0
                for i in range(8):
                    if t >> i & 1: v ^= urow[i]
                ntop.append(v)
            ct = bp_cost(8, ntop, runs, random.Random(lam * 8 + k))
            nouts = []
            for i in range(8):
                bit = 7 - i
                v = 0
                for j in range(8):
                    if Mout[j] >> bit & 1: v ^= outs[7 - j]
                nouts.append(v)
            cb = paar(nouts)
            rec = {'lam': lam, 'k': k, 'top': ct, 'bot': cb, 'sum': (ct or 99) + cb}
            log.write(json.dumps(rec) + '\n')
            res.append(rec)
        log.flush()
        print('k %d %.0fs' % (k, time.time() - t0), flush=True)
    idr = [r for r in res if r['lam'] == 1 and r['k'] == 0][0]
    res.sort(key=lambda r: r['sum'])
    print('identity', idr)
    print('best', res[:25])


if __name__ == '__main__':
    main()
