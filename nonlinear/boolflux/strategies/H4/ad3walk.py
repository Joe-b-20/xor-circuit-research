"""Plateau walk over level-2 member states with junk J <= JMAX (no level 1 fixed), starting from
a zero-deficit record; every new junk space V_N + U (mod free = M & X2) gets the exact level-1
cover test for l1 <= MAXL1 (cover lemma, s <= 2).  A success means an AD3 circuit with
l1 + k + p + 12 ANDs.
usage: ad3walk.py JSONL INDEX --seconds S --jmax J --maxl1 L --seed S --out JSONL"""
import argparse
import json
import random
import time

import cover1
import cover_exact
import cover_s2
import ad3mem as A
from ad3sat import NT
from ad3fix import GOOD


def vec_of(m):
    return cover1.reduce(A.nprod(m[1], m[2]) if m[0] == 'n' else A.member(m[1], tuple(m[2])), A.E0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jsonl'); ap.add_argument('index', type=int)
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--jmax', type=int, default=5)
    ap.add_argument('--maxl1', type=int, default=10); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None); ap.add_argument('--grow', type=int, default=0,
                    help='add this many extra member slots to the start state')
    ap.add_argument('--addn', type=int, default=0, help='add this many N-product slots')
    ap.add_argument('--drop', type=int, default=0, help='remove this many members from the start')
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    r = json.loads(open(a.jsonl).read().splitlines()[a.index])
    if 'state' not in r:     # an ad3mem.py record
        r['state'] = [['m', l, g] for l, g in r['lams']] + [['n', x, y] for x, y in r['npairs']]
    state = [tuple(m) if m[0] == 'n' else ('m', m[1], tuple(m[2])) for m in r['state'] if m[0] != 'x']
    for _ in range(a.grow): state.insert(0, ('m', rnd.randrange(1, 256), rnd.choice(GOOD)))
    for _ in range(a.drop): state.pop(0)
    for _ in range(a.addn):
        x, y = rnd.sample(range(1, 16), 2); state.append(('n', x, y))
    k = sum(1 for m in state if m[0] == 'm'); p = len(state) - k
    VN = [A.to_wedge(t) for t in NT if t]
    cache = {}

    def vecs(st):
        out = []
        for m in st:
            if m not in cache: cache[m] = vec_of(m)
            out.append(cache[m])
        return out
    inf, J = A.junk(vecs(state))
    seen = {}; best = None; t0 = time.time(); steps = acc = 0
    hist = {}
    while time.time() - t0 < a.seconds:
        steps += 1
        ns = list(state); j = rnd.randrange(len(ns)); m = ns[j]
        if m[0] == 'n':
            x, y = rnd.sample(range(1, 16), 2); ns[j] = ('n', x, y)
        else:
            u = rnd.random()
            if u < 0.5: ns[j] = ('m', (m[1] ^ (1 << rnd.randrange(8))) or 1, m[2])
            elif u < 0.7: ns[j] = ('m', m[1], rnd.choice(GOOD))
            else: ns[j] = ('m', rnd.randrange(1, 256), m[2])
        v = vecs(ns)
        i2, J2 = A.junk(v)
        if inf or J > a.jmax:
            if (i2, J2) <= (inf, J) or rnd.random() < 0.02: state, inf, J = ns, i2, J2
            continue
        if i2 or J2 > a.jmax: continue
        state, J = ns, J2; acc += 1
        U = A.junk_space(v)
        Uw = [A.to_wedge(u) for u in U]
        Fw = [A.to_wedge(f) for f in A.m_cap_x2(v)]
        Fr = cover1.rowspace(Fw)
        key = (tuple(sorted(cover1.rowspace([cover1.reduce(x, Fr) for x in VN + Uw]).values())),
               tuple(sorted(Fr.values())))
        if key in seen: continue
        d = len(key[0])
        res = None
        for l1 in range(max(9, d), min(d + 2, a.maxl1) + 1):
            if l1 - d == 2: c, _ = cover_s2.cover2(VN + Uw, free=Fw)
            else: c = cover_exact.cover(VN + Uw, l1, free=Fw)
            if c is not None: res = (l1, c); break
        seen[key] = res
        hist[(J, d)] = hist.get((J, d), 0) + 1
        if res:
            rec = {'k': k, 'p': p, 'J': J, 'd': d, 'l1': res[0], 'L1': res[1], 'state': state,
                   'total': res[0] + k + p + 12}
            print('FOUND', json.dumps(rec), flush=True)
            if a.out:
                with open(a.out, 'a') as fh: fh.write(json.dumps(rec) + chr(10))
            if best is None or rec['total'] < best: best = rec['total']
    print(json.dumps({'steps': steps, 'accepted': acc, 'distinct_U': len(seen),
                      'hist_J_d': {str(k): v for k, v in sorted(hist.items())}, 'best_total': best,
                      'k': k, 'p': p}), flush=True)


if __name__ == '__main__':
    main()
