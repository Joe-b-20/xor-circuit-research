#!/usr/bin/env python3
"""P1 depth-aware linear re-synthesis around a fixed AND skeleton (timing-driven Paar).

Keeps the AND functions of a circuit (boolflux.skeleton.extract: each AND as two affine forms over
the inputs and earlier ANDs; outputs as affine forms), so A and AD are those of the start, and
rebuilds every XOR/XNOR/NOT gate:
  1. ASAP level of every AND (Huffman over its operands' term levels; F's skeleton bound).
  2. Planned AND levels for gate-depth cap D: reverse order, each AND as late as all forms that read
     it still meet their deadlines (Kraft/Huffman test), scaled back toward ASAP by a random slack
     factor u (u = 1: as late as possible = most room for sharing).
  3. Timing-driven Paar: every target (AND operand with deadline = planned level - 1, output with
     deadline D) is a cover of signals; repeatedly create the XOR of the signal pair shared by the
     most targets whose deadlines still hold after the replacement (ties: lower level, random); when
     no pair is shared by >= 2 targets, one Huffman step on the most urgent ready target.  An AND is
     created as soon as both operands are done; constants become a dedicated XNOR at the last step
     or a NOT.
Result: same A, AD; GD <= D whenever D >= the skeleton bound.  Gates are not minimal: the gate
kernel polishes afterwards under the hard caps.

    python3 p1synth.py START --cap D [--seed K] [--slack 1.0] [--out OUT.circ.txt]
"""
import argparse
import heapq
import random
import sys
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets, skeleton as SK   # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3


def huff(levels, const=False):
    if not levels:
        return 0
    if len(levels) == 1:
        return levels[0] + (1 if const else 0)
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, max(a, b) + 1)
    return h[0]


def bits(f):
    return [p for p in range(1, f.bit_length()) if (f >> p) & 1]


def plan(sk, D, rng, slack):
    n = sk['n']; K = len(sk['ands'])
    lv = {p: 0 for p in range(1, n + 1)}
    for k, (L, R) in enumerate(sk['ands']):
        p = n + 1 + k
        lv[p] = 1 + max(huff([lv[q] for q in bits(L)], L & 1), huff([lv[q] for q in bits(R)], R & 1))
    asap = dict(lv)
    for F in sk['outputs']:
        if huff([lv[q] for q in bits(F)], F & 1) > D:
            return None, asap
    # consumers of each AND position: (form, deadline-owner) ; deadline of operand of AND q = t_q - 1
    cons = {p: [] for p in range(n + 1, n + K + 1)}
    for k, (L, R) in enumerate(sk['ands']):
        q = n + 1 + k
        for F in (L, R):
            for p in bits(F):
                if p > n: cons[p].append((F, q))
    for F in sk['outputs']:
        for p in bits(F):
            if p > n: cons[p].append((F, None))
    t = dict(asap)

    def ok(F, owner):
        dl = D if owner is None else t[owner] - 1
        return huff([t[q] for q in bits(F)], F & 1) <= dl
    for k in range(K - 1, -1, -1):
        p = n + 1 + k
        lo = asap[p]; best = lo
        for cand in range(lo + 1, D + 1):
            t[p] = cand
            if all(ok(F, o) for F, o in cons[p]): best = cand
            else: break
        u = slack if slack is not None else rng.choice([1.0, 1.0, 0.75, 0.5])
        t[p] = lo + int(round(u * (best - lo)))
    return t, asap


def synth(sk, D, rng, slack=None):
    n = sk['n']; K = len(sk['ands'])
    t, asap = plan(sk, D, rng, slack)
    if t is None:
        return None
    gates = []; lvl = [0] * n; form = [1 << (1 + i) for i in range(n)]
    memo = {form[i]: i for i in range(n)}          # pure or complemented form -> signal (lowest level)
    possig = {1 + i: i for i in range(n)}          # basis position -> signal

    def gate(op, a, b, f):
        gates.append((op, a, b)); s = n + len(gates) - 1
        lvl.append(1 + max(lvl[a], lvl[b])); form.append(f)
        if f not in memo or lvl[memo[f]] > lvl[s]: memo[f] = s
        return s
    # targets: cover = list of items; item = ('s', sig) or ('p', pos) (pending AND)
    T = []
    for k, (L, R) in enumerate(sk['ands']):
        for side, F in ((0, L), (1, R)):
            T.append({'f': F, 'c': F & 1, 'own': n + 1 + k, 'side': side, 'done': None,
                      'cov': [('s', possig[p]) if p <= n else ('p', p) for p in bits(F)]})
    for j, F in enumerate(sk['outputs']):
        T.append({'f': F, 'c': F & 1, 'own': None, 'side': j, 'done': None,
                  'cov': [('s', possig[p]) if p <= n else ('p', p) for p in bits(F)]})

    def dl(tg):
        return D if tg['own'] is None else t[tg['own']] - 1

    def ilev(it):
        return lvl[it[1]] if it[0] == 's' else t[it[1]]
    andsig = {}
    opsig = {}

    def finish(tg, s):
        """target tg is the single pure signal s (const not yet applied)"""
        if tg['c']:
            f1 = form[s] ^ 1
            if f1 in memo and lvl[memo[f1]] <= lvl[s] + 1: s = memo[f1]
            else: s = gate(NOT, s, s, f1)
        tg['done'] = s
        if tg['own'] is not None:
            opsig[(tg['own'], tg['side'])] = s

    def resolve_items():
        changed = True
        while changed:
            changed = False
            for k in range(K):
                p = n + 1 + k
                if p in andsig: continue
                if (p, 0) in opsig and (p, 1) in opsig:
                    s = gate(AND, opsig[(p, 0)], opsig[(p, 1)], 1 << p)
                    andsig[p] = s; changed = True
                    for tg in T:
                        if tg['done'] is None:
                            tg['cov'] = [('s', s) if it == ('p', p) else it for it in tg['cov']]
            for tg in T:
                if tg['done'] is None and len(tg['cov']) == 1 and tg['cov'][0][0] == 's':
                    s = tg['cov'][0][1]
                    finish(tg, s); changed = True
    # trivial targets first (single input terms etc.)
    resolve_items()
    guard = 0
    while any(tg['done'] is None for tg in T):
        guard += 1
        if guard > 5000: raise RuntimeError('no progress')
        pend = [tg for tg in T if tg['done'] is None]
        cnt = {}
        for ti, tg in enumerate(pend):
            av = sorted({it[1] for it in tg['cov'] if it[0] == 's'})
            if len(av) < 2: continue
            levs = [ilev(it) for it in tg['cov']]
            D_ = dl(tg)
            for x in range(len(av)):
                for y in range(x + 1, len(av)):
                    a, b = av[x], av[y]
                    nl = max(lvl[a], lvl[b]) + 1
                    rest = [ilev(it) for it in tg['cov'] if not (it[0] == 's' and it[1] in (a, b))]
                    if huff(rest + [nl], tg['c']) > D_: continue
                    cnt.setdefault((a, b), []).append(tg)
        best = None
        for (a, b), tgs in cnt.items():
            if len(tgs) < 2: continue
            nl = max(lvl[a], lvl[b]) + 1
            key = (len(tgs), -nl, rng.random())
            if best is None or key > best[0]: best = (key, a, b, tgs)
        if best is not None:
            _, a, b, tgs = best
            f = form[a] ^ form[b]
            s = memo[f] if f in memo and lvl[memo[f]] <= max(lvl[a], lvl[b]) + 1 else gate(XOR, a, b, f)
            for tg in tgs:
                tg['cov'] = [it for it in tg['cov'] if not (it[0] == 's' and it[1] in (a, b))] + [('s', s)]
            resolve_items()
            continue
        # one Huffman step on the most urgent ready target
        ready = [tg for tg in pend if all(it[0] == 's' for it in tg['cov'])]
        if not ready:
            raise RuntimeError('deadlock: no ready target')
        tg = min(ready, key=lambda x: (dl(x), rng.random()))
        cov = sorted(tg['cov'], key=lambda it: (lvl[it[1]], rng.random()))
        a, b = cov[0][1], cov[1][1]
        f = form[a] ^ form[b]
        if len(cov) == 2 and tg['c']:
            f1 = f ^ 1
            s = memo[f1] if f1 in memo and lvl[memo[f1]] <= max(lvl[a], lvl[b]) + 1 else gate(XNOR, a, b, f1)
            tg['done'] = s
            if tg['own'] is not None: opsig[(tg['own'], tg['side'])] = s
            resolve_items()
            continue
        s = memo[f] if f in memo and lvl[memo[f]] <= max(lvl[a], lvl[b]) + 1 else gate(XOR, a, b, f)
        tg['cov'] = cov[2:] + [('s', s)]
        resolve_items()
    outs = [tg['done'] for tg in T if tg['own'] is None]
    c = core.Circuit(n, len(outs), gates, outs, 'p1synth').live()
    return c


def rebuild(c, D, seed=1, slack=None):
    rng = random.Random(seed)
    sk = SK.extract(c)
    r = synth(sk, D, rng, slack)
    if r is None:
        return None
    assert tuple(r.value_table()) == tuple(targets.aes_sbox()), 'p1synth: wrong function'
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('start'); ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--slack', type=float, default=None)
    ap.add_argument('--out')
    a = ap.parse_args()
    t = Path(a.start).read_text()
    c = core.from_kernel(t) if a.start.endswith('.bfx') else core.read_ncff(t)
    M = core.Model.load('nist')
    r = rebuild(c, a.cap, a.seed, a.slack)
    m0 = c.metrics(M); m = r.metrics(M) if r else None
    print('start', [m0[k] for k in ('A', 'AD', 'G', 'GD')], 'rebuilt', [m[k] for k in ('A', 'AD', 'G', 'GD')] if m else None)
    if a.out and r:
        Path(a.out).write_text(core.write_ncff(r, M, comments=['P1 p1synth cap %d seed %d of %s' % (a.cap, a.seed, a.start)]))


if __name__ == '__main__':
    main()
