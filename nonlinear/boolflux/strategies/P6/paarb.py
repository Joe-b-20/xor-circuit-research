#!/usr/bin/env python3
"""P6: depth-constrained shared synthesis (Paar per layer, every target kept Kraft-feasible).

    python3 paarb.py FILE --cap 12 --out DIR [--n K] [--seed S] [--slack 0]

FILE = parent AD3 circuit; its level-3 classes are re-based (botbasis feasible triples, max Kraft <= 1
at the cap), then the whole skeleton is synthesised level by level: each layer's targets (operands of
the ANDs of that level, then the outputs) get deadlines = their Huffman-earliest level (+ slack), are
covered by existing signals, then the most frequent piece pair that keeps every target it enters
Kraft-feasible is created (Paar), until no pair is shared; the rest are Huffman trees.
"""
import sys, random, argparse, json, heapq
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                 # noqa: E402
from boolflux.hub.common import verify, metrics, clean      # noqa: E402
import botbasis as BB                                       # noqa: E402
from rebase import Builder, popc, new_skeleton, feasible_triples, XOR, XNOR, NOT, AND   # noqa: E402


def cover(B, F, r):
    f = F & ~1; cap = 2 ** r
    terms = [p for p in BB.bits(f) if p]
    base_k = {p: 2 ** B.lv[B.term_sig(p)] for p in terms}
    s = B.by.get(f)
    if s is not None and B.lv[s] <= r - ((B.form[s] & 1) != (F & 1)):
        return [s]
    cands = [(popc(key), key, s) for key, s in B.by.items()
             if key & ~f == 0 and popc(key) >= 2 and B.lv[s] <= r - 1]
    cands.sort(key=lambda t: (-t[0], B.lv[t[2]]))
    rem = f; pieces = []; used = 0
    for pc, key, s in cands:
        if key & ~rem: continue
        k2 = used + 2 ** B.lv[s] + sum(base_k[p] for p in BB.bits(rem ^ key) if p)
        if k2 <= cap:
            pieces.append(s); used += 2 ** B.lv[s]; rem ^= key
            if rem == 0: break
    pieces += [B.term_sig(p) for p in BB.bits(rem) if p]
    return pieces


def cover2(B, F, r, triples=True):
    """pieces for form F at deadline r: exact 1/2/3-signal resubstitution first (Kraft-feasible),
    then greedy overlapping cover (piece maximising the drop in remaining terms), rest basis terms."""
    f = F & ~1; cap = 2 ** r
    def tk(p): return 2 ** B.lv[B.term_sig(p)]
    s = B.by.get(f)
    if s is not None and B.lv[s] <= r - ((B.form[s] & 1) != (F & 1)):
        return [s]
    S = [(key, sg, B.lv[sg]) for key, sg in B.by.items() if B.lv[sg] <= r - 1]
    best = None
    for key, sg, l in S:
        t = B.by.get(f ^ key)
        if t is not None and t != sg and B.lv[t] <= r - 1:
            return [sg, t]
    if triples:
        Sx = [x for x in S if x[2] <= r - 2] if len(S) > 0 else S
        for i in range(len(S)):
            k1, s1, l1 = S[i]
            for j in range(i + 1, len(S)):
                k2, s2, l2 = S[j]
                t = B.by.get(f ^ k1 ^ k2)
                if t is None or t in (s1, s2): continue
                if 2 ** l1 + 2 ** l2 + 2 ** B.lv[t] <= cap:
                    return [s1, s2, t]
    rem = f; pieces = []; used = 0
    def rest(m): return sum(tk(p) for p in BB.bits(m) if p)
    while rem:
        bestg = 0; bp = None
        pr = popc(rem)
        for key, sg, l in S:
            g = pr - popc(rem ^ key) - 1
            if g <= bestg: continue
            if used + 2 ** l + rest(rem ^ key) <= cap:
                bestg = g; bp = (key, sg, l)
        if bp is None: break
        pieces.append(bp[1]); used += 2 ** bp[2]; rem ^= bp[0]
    pieces += [B.term_sig(p) for p in BB.bits(rem) if p]
    # cancel duplicates (a piece used twice XORs to nothing)
    out = []
    for x in pieces:
        if x in out: out.remove(x)
        else: out.append(x)
    return out


def finish(B, F, pieces):
    par = (F & 1) ^ (sum(B.form[s] & 1 for s in pieces) & 1)
    if len(pieces) == 1:
        s = pieces[0]
        return B.new(NOT, s, s) if par else s
    h = [(B.lv[s], i, s) for i, s in enumerate(pieces)]; heapq.heapify(h); cnt = len(h)
    while len(h) > 1:
        l1, _, a = heapq.heappop(h); l2, _, b = heapq.heappop(h)
        op = XNOR if (len(h) == 0 and par) else XOR
        key = (B.form[a] ^ B.form[b]) & ~1
        ex = B.by.get(key)
        if op == XOR and ex is not None and B.lv[ex] <= max(l1, l2) + 1 and ((B.form[ex] ^ B.form[a] ^ B.form[b]) & 1) == 0:
            s = ex
        else:
            s = B.new(op, a, b)
        cnt += 1; heapq.heappush(h, (B.lv[s], cnt, s))
    return h[0][2]


COVER = cover2


def layer_build(B, targets, rng=None, use_cover=True):
    T = []
    for F, r in targets:
        pcs = COVER(B, F, r) if use_cover else [B.term_sig(p) for p in BB.bits(F & ~1) if p]
        T.append([F, r, set(pcs)])
    def kraft(ps):
        return sum(2 ** B.lv[s] for s in ps)
    while True:
        cnt = {}
        for F, r, ps in T:
            if len(ps) < 3: continue
            L = sorted(ps); kp = kraft(ps)
            for i in range(len(L)):
                for j in range(i + 1, len(L)):
                    a, b = L[i], L[j]
                    nl = 1 + max(B.lv[a], B.lv[b])
                    if kp - 2 ** B.lv[a] - 2 ** B.lv[b] + 2 ** nl <= 2 ** r:
                        cnt[(a, b)] = cnt.get((a, b), 0) + 1
        if not cnt: break
        best = max(cnt.values())
        if best < 2: break
        top = [k for k, v in cnt.items() if v == best]
        lvmin = min(max(B.lv[k[0]], B.lv[k[1]]) for k in top)
        top = sorted(k for k in top if max(B.lv[k[0]], B.lv[k[1]]) == lvmin)
        a, b = (rng.choice(top) if rng else top[0])
        key = (B.form[a] ^ B.form[b]) & ~1
        ex = B.by.get(key)
        if ex is not None and B.lv[ex] <= 1 + max(B.lv[a], B.lv[b]) and ((B.form[ex] ^ B.form[a] ^ B.form[b]) & 1) == 0:
            s = ex
        else:
            s = B.new(XOR, a, b)
        for t in T:
            F, r, ps = t
            if a in ps and b in ps:
                kp = kraft(ps)
                if kp - 2 ** B.lv[a] - 2 ** B.lv[b] + 2 ** B.lv[s] <= 2 ** r:
                    if len(ps) == 2 and ((B.form[s] ^ F) & 1) and B.lv[s] + 1 > r:
                        continue          # would need a NOT beyond the deadline
                    ps.discard(a); ps.discard(b); ps.add(s)
    return [finish(B, F, sorted(ps)) for F, r, ps in T]


def paar_build(sk, cap, rng=None, slack=0):
    n = sk['n']
    class FB(Builder):
        def __init__(s):
            s.n = n; s.gates = []; s.form = [1 << (1 + i) for i in range(n)]; s.lv = [0] * n
            s.kind = ['x'] * n; s.by = {s.form[i]: i for i in range(n)}
    B = FB()
    nb = 1 + n + len(sk['ands'])
    arr = [0] * nb; alv = [0] * nb
    for k, (L, R) in enumerate(sk['ands']):
        alv[1 + n + k] = 1 + max([alv[p] for p in list(BB.bits(L)) + list(BB.bits(R)) if p] + [0])
    for lev in sorted(set(alv[1 + n:])):
        ks = [k for k in range(len(sk['ands'])) if alv[1 + n + k] == lev]
        tg = []
        for k in ks:
            L, R = sk['ands'][k]
            hl = BB.huff([arr[p] for p in BB.bits(L) if p], L & 1)
            hr = BB.huff([arr[p] for p in BB.bits(R) if p], R & 1)
            d = max(hl, hr) + (slack if lev < 3 else 0)
            tg += [(L, d), (R, d)]
        sigs = layer_build(B, tg, rng)
        for i, k in enumerate(ks):
            s = B.new(AND, sigs[2 * i], sigs[2 * i + 1]); B.kind[-1] = 'and'
            p = 1 + n + k; B.form[s] = 1 << p; B.by[1 << p] = s; arr[p] = B.lv[s]
    outs = layer_build(B, [(F, cap) for F in sk['outputs']], rng)
    nc = core.Circuit(n, sk['m'], B.gates, outs, 'paar')
    return clean(nc.live())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--n', type=int, default=1); ap.add_argument('--slack', type=int, default=0)
    a = ap.parse_args()
    c = BB.load(a.file)
    res = BB.analyse(a.file, a.cap, verbose=False)
    T = feasible_triples(res)
    print('feasible triples (Pareto reps):', len(T), 'best max Kraft', res['best'], flush=True)
    rng = random.Random(a.seed)
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    rows = []; best = None
    for it in range(a.n):
        tri = T[it] if it < len(T) else rng.choice(T)
        sk = new_skeleton(c, res, tri)
        nc = paar_build(sk, a.cap, rng if it >= len(T) else None, a.slack)
        ok, inf = verify(nc); m = metrics(nc)
        rows.append({'it': it, 'ok': ok, 'm': m, 'triple': tri})
        if ok and m[3] <= a.cap and (best is None or m[2] < best[0][2]):
            best = (m, nc, it)
            p = outdir / ('pb-a%d-ad%d-g%d-gd%d-s%d-%d.bfx' % (m[0], m[1], m[2], m[3], a.seed, it))
            p.write_text(core.to_kernel(nc)); rows[-1]['file'] = str(p)
            print(it, ok, m, tri, p.name, flush=True)
    json.dump({'parent': str(Path(a.file).resolve()), 'seed': a.seed, 'slack': a.slack, 'rows': rows},
              open(outdir / ('paar-s%d.json' % a.seed), 'w'), indent=1)
    if rows:
        gs = sorted(r['m'][2] for r in rows if r['ok'] and r['m'][3] <= a.cap)
        print('GD<=cap builds', len(gs), 'G min/median', gs[0] if gs else None, gs[len(gs) // 2] if gs else None)


if __name__ == '__main__':
    main()
