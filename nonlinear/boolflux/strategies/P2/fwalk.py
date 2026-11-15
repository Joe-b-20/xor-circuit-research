#!/usr/bin/env python3
"""P2: flip-graph walk on rank-1 bottom decompositions (model M) towards per-output Kraft <= 1.

State: products (alpha, g, w) with sum_j Y_alpha g w = x^-1 (exact tensor identity).
Flips (rank-preserving, exact; Kauers-Moosbauer style):
  same alpha:  a(x)b_i(x)c_i + a(x)b_j(x)c_j = a(x)(b_i+b_j)(x)c_i + a(x)b_j(x)(c_i+c_j)
  same g:      (a_i+a_j)(x)b(x)c_i + a_j(x)b(x)(c_i+c_j)
  same w:      (a_i+a_j)(x)b_i(x)c + a_j(x)(b_i+b_j)(x)c
Two products sharing two factors merge (rank drops) - reported.
Objective at depth D with the front's Y-form level table: excess = sum_k max(0, K_k - 1),
K_k = sum_{j in output k} 2^(1 + lev(alpha_j) - D); then total K.

    python3 fwalk.py FRONT D OUT.jsonl --bottoms B1 ... [--seconds T] [--seed S] [--temp T0]
"""
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import orbit as O   # noqa: E402
import orbsearch as OS   # noqa: E402

LV = OS.LV
MUL = OS.MUL
POP = [bin(i).count('1') for i in range(256)]


OBJ = 'kraft'


def score(dec, W, D):
    ks = [0.0] * 8
    inc = 0
    for al, g, w in dec:
        lv = LV[w]; wt = W[al]
        inc += POP[lv]
        for k in range(8):
            if (lv >> (7 - k)) & 1: ks[k] += wt
    exc = sum(max(0.0, x - 1.0) for x in ks)
    if OBJ == 'inc':
        # bottom gate estimate: output XORs + g-form XORs + distinct Y-forms
        gs = set(g for al, g, w in dec); als = set(al for al, g, w in dec)
        est = inc - 8 + sum(POP[g] - 1 for g in gs) * 0.5 + 2 * len(als)
        return exc, est, ks
    return exc, sum(ks), ks


def merge(dec):
    """merge products sharing two factors; drop zero products."""
    changed = True
    while changed:
        changed = False
        for i in range(len(dec)):
            for j in range(i + 1, len(dec)):
                a1, g1, w1 = dec[i]; a2, g2, w2 = dec[j]
                new = None
                if a1 == a2 and g1 == g2: new = (a1, g1, w1 ^ w2)
                elif a1 == a2 and w1 == w2: new = (a1, g1 ^ g2, w1)
                elif g1 == g2 and w1 == w2: new = (a1 ^ a2, g1, w1)
                if new is not None:
                    dec = [d for k, d in enumerate(dec) if k not in (i, j)]
                    if new[0] and new[1] and new[2]: dec.append(new)
                    changed = True; break
            if changed: break
    return dec


def flips(dec):
    """list of candidate flipped decompositions (index pairs and kind)."""
    P = len(dec); out = []
    for i in range(P):
        for j in range(P):
            if i == j: continue
            a1, g1, w1 = dec[i]; a2, g2, w2 = dec[j]
            if a1 == a2: out.append(('a', i, j))
            if g1 == g2: out.append(('g', i, j))
            if w1 == w2: out.append(('w', i, j))
    return out


def apply_flip(dec, f):
    kind, i, j = f
    d = list(dec)
    a1, g1, w1 = d[i]; a2, g2, w2 = d[j]
    if kind == 'a':   # a (b_i+b_j) c_i + a b_j (c_i+c_j)
        d[i] = (a1, g1 ^ g2, w1); d[j] = (a2, g2, w1 ^ w2)
    elif kind == 'g':  # (a_i+a_j) b c_i + a_j b (c_i+c_j)
        d[i] = (a1 ^ a2, g1, w1); d[j] = (a2, g2, w1 ^ w2)
    else:              # (a_i+a_j) b_i c + a_j (b_i+b_j) c
        d[i] = (a1 ^ a2, g1, w1); d[j] = (a2, g1 ^ g2, w2)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front'); ap.add_argument('D', type=int); ap.add_argument('out')
    ap.add_argument('--bottoms', nargs='+', required=True)
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--temp', type=float, default=0.3); ap.add_argument('--restart', type=int, default=200000)
    ap.add_argument('--maxlev', type=int, default=99)
    ap.add_argument('--obj', default='kraft'); ap.add_argument('--samples', type=int, default=200)
    a = ap.parse_args()
    global OBJ
    OBJ = a.obj
    rng = random.Random(a.seed)
    F = ylev.front(ylev.load(a.front))
    lev = {bil.ALPHA[v]: F['levels'][v][0] for v in range(1, 16)}
    W = {al: (2.0 ** (1 + lev[al] - a.D) if lev[al] <= a.maxlev else 8.0) for al in lev}
    print('front', a.front, 'levels', sorted((lev[al], al) for al in lev), flush=True)
    bases = []
    for b in a.bottoms:
        d = O.extract(ylev.load(b))
        if d is not None and O.check(d): bases.append(d)
    print('bases', len(bases), flush=True)
    out = open(a.out, 'a')
    T0 = time.time(); best_overall = None; it = 0; seen_feas = set()
    while time.time() - T0 < a.seconds:
        # start: random base, random orbit image
        cands = []
        for _s in range(a.samples):
            base = rng.choice(bases)
            A_, B_, F_ = (rng.choice([z for z in O.I.SUB if z]), rng.randrange(1, 256), rng.randrange(8))
            b17i = OS.INV[O.p256(B_, 17)]
            d2 = [(MUL[al][b17i], OS.gmap_fast(g, MUL[B_]), MUL[w][B_]) for al, g, w in base]
            for _ in range(F_):
                d2 = [(OS.P8[al], OS.gmap_fast(g, OS.SQ), OS.P128[w]) for al, g, w in d2]
            d2 = [(MUL[al][A_], g, MUL[w][OS.INV[A_]]) for al, g, w in d2]
            e_, t_, k_ = score(d2, W, a.D)
            cands.append(((e_, t_), d2))
        cands.sort(key=lambda z: z[0])
        cur = cands[0][1]
        assert O.check(cur)
        cur = merge(cur)
        ce, ct, ck = score(cur, W, a.D)
        best = (ce, ct)
        for step in range(a.restart):
            it += 1
            fl = flips(cur)
            if not fl: break
            f = rng.choice(fl)
            nd = merge(apply_flip(cur, f))
            ne, nt, nk = score(nd, W, a.D)
            dE = (ne - ce) * 10 + (nt - ct) * (0.5 if OBJ == 'kraft' else 0.2) + (len(nd) - len(cur)) * 5
            T = a.temp
            if dE <= 0 or rng.random() < math.exp(-dE / T):
                cur, ce, ct, ck = nd, ne, nt, nk
                if len(cur) < 18:
                    print('RANK DROP to %d at %.1fs' % (len(cur), time.time() - T0), flush=True)
                    ok = O.check(cur)
                    out.write(json.dumps({'kind': 'rankdrop', 'P': len(cur), 'check': ok, 'dec': cur, 'ks': ck}) + '\n'); out.flush()
                if (ce, ct) < best: best = (ce, ct)
                if best_overall is None or (ce, ct) < best_overall[:2]:
                    best_overall = (ce, ct, ck, len(cur))
                    print('%.1fs it %d best excess %.3f total %.3f P %d ks %s' % (time.time() - T0, it, ce, ct, len(cur), [round(x, 3) for x in ck]), flush=True)
                if ce <= 1e-9:
                    key = tuple(sorted(cur))
                    if key not in seen_feas:
                        seen_feas.add(key)
                        ok = O.check(cur)
                        print('FEASIBLE D=%d P=%d check %s ks %s' % (a.D, len(cur), ok, [round(x, 3) for x in ck]), flush=True)
                        out.write(json.dumps({'kind': 'feasible', 'D': a.D, 'P': len(cur), 'check': ok, 'dec': cur, 'ks': ck,
                                              'front': a.front, 'seed': a.seed, 't': time.time() - T0}) + '\n'); out.flush()
            if time.time() - T0 > a.seconds: break
    print('end', best_overall, 'feasible distinct', len(seen_feas), flush=True)


if __name__ == '__main__':
    main()
