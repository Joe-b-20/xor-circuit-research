"""Exact local search for the last layer: minimise cost(S) = |S| + J(S) over sets S of
GF(4)-norm members (NOTES.md sections 5-6).

E_min = span(1, x, N coords, n coords, inversion ANDs of the AD5 file); JX = all x-quadratic
functions; G0 = all functions of N (grade-0 residue treated as free: optimistic).
S is feasible iff the 8 bits of x^-1 lie in span(S) + E_min + JX + G0.  J(S) = least dimension of
the x-quadratic junk the 8 outputs need (over all choices of output combinations), computed
exactly as rank(residuals + junk(K0)) - rank(junk(K0)), K0 = combinations with zero hard part.
A 27-AND design in this family needs cost <= 17 (total >= 5 + J + 5 + k).

usage: python3 kj_search.py [--gamma E|none] [--iters N] [--seed S] [--start a28|random]
       [--members gf4|wfree] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time

import gf
import qmc
from exp_stage3 import tables_of
from fam_check import tr_tab, trK, OMEGA, gp
from structure import analyse

AD5 = '/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'
N = [gf.power(p, 17) for p in range(256)]
n = [gf.INV[v] for v in N]


def kbasis():
    sp = gf.Span(); kb = []
    for v in gf.SUB16:
        if v and sp.add(v): kb.append(v)
    return kb


class Model:
    def __init__(self, gamma, g0='free'):
        kb = kbasis()
        Nt = gf.coord_tables(N, kb); nt = gf.coord_tables(n, kb)
        _, inv = tables_of(AD5)
        Emin = [gf.ONES] + gf.X + Nt + nt + inv
        JX = [a & b for i, a in enumerate(gf.X) for b in gf.X[i + 1:]]
        G0 = []
        for v in gf.SUB16:
            t = 0
            for p in range(256):
                if N[p] == v: t |= 1 << p
            G0.append(t)
        self.Emin, self.JX = Emin, JX
        if g0 == 'free':
            self.hard = qmc.Normal(Emin + JX + G0)
            self.soft = qmc.Normal(Emin + G0)
        else:
            self.hard = qmc.Normal(Emin + JX)
            self.soft = qmc.Normal(Emin)
        self.T = [gf.bit_table(gf.INV, k) for k in range(8)]
        self.hT = [self.hard.nf(t) for t in self.T]
        self.jT = [self.soft.nf(t) for t in self.T]
        self.gamma = gamma
        self.w = [n[p] ^ (gf.mul(gamma, N[p]) if gamma else 0) for p in range(256)]

    def member(self, A, s, t=None):
        w2 = gf.mul(OMEGA, OMEGA)
        if t is None:
            l = tr_tab(A) ^ trK(s, self.w)
            m = tr_tab(gf.mul(OMEGA, A)) ^ trK(gf.mul(w2, s), self.w)
        else:   # independent n- and N-parts
            l = tr_tab(A) ^ trK(s, n) ^ trK(t, N)
            m = tr_tab(gf.mul(OMEGA, A)) ^ trK(gf.mul(w2, s), n) ^ trK(gf.mul(w2, t), N)
        P = l & m
        return self.hard.nf(P), self.soft.nf(P)

    def cost(self, H, Jv):
        """H, Jv: lists of hard / soft vectors of the members. Returns (feasible, J, deficit)."""
        k = len(H)
        # eliminate members, tracking combinations
        piv = {}
        kernel = []
        for j in range(k):
            v, tag = H[j], 1 << j
            while v:
                h = v.bit_length() - 1
                if h not in piv: break
                pv, pt = piv[h]; v ^= pv; tag ^= pt
            if v: piv[v.bit_length() - 1] = (v, tag)
            else: kernel.append(tag)
        res = []; deficit = 0
        for o in range(8):
            v, tag = self.hT[o], 0
            while v:
                h = v.bit_length() - 1
                if h not in piv: break
                pv, pt = piv[h]; v ^= pv; tag ^= pt
            if v:
                deficit += 1; continue
            r = self.jT[o]
            for j in range(k):
                if (tag >> j) & 1: r ^= Jv[j]
            res.append(r)
        if deficit:
            # deficit measured as rank increase
            sp = gf.Span(H)
            d0 = sp.dim(); d = sum(1 for t in self.hT if sp.add(t))
            return False, None, d
        kj = []
        for tag in kernel:
            r = 0
            for j in range(k):
                if (tag >> j) & 1: r ^= Jv[j]
            kj.append(r)
        sk = gf.Span(kj); base = sk.dim()
        for r in res: sk.add(r)
        return True, sk.dim() - base, 0


def a28_members(model):
    c, ands, outs, tabs = analyse(AD5)
    top = max(A['level'] for A in ands)
    return [(model.hard.nf(A['tab']), model.soft.nf(A['tab'])) for A in ands if A['level'] == top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--iters', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--start', default='a28')
    ap.add_argument('--members', default='gf4')
    ap.add_argument('--temp', type=float, default=0.6)
    ap.add_argument('--out', default=None)
    ap.add_argument('--g0', default='free')
    ap.add_argument('--dump', default=None, help='JSONL file for visited sets with cost<=dumpcost')
    ap.add_argument('--dumpcost', type=int, default=16)
    ap.add_argument('--dumpk', type=int, default=13)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    gamma = None if a.gamma == 'none' else gp(int(a.gamma))
    t0 = time.time()
    M = Model(gamma, a.g0)
    # member pool: (A, s) modulo (A, s) ~ (wA, w^2 s): take s from a transversal of K*/GF(4)*
    pool = []; seen = set()
    svals = [v for v in gf.SUB16 if v]
    for A in range(1, 256):
        for s in svals:
            if a.members == 'gf4':
                hv, jv = M.member(A, s)
                key = (hv, jv)
                if key in seen: continue
                seen.add(key); pool.append((('gf4', A, s), hv, jv))
    if a.members == 'wfree':
        for A in range(1, 256):
            for s in [0] + svals:
                for tt in [0] + svals:
                    if s == 0 and tt == 0: continue
                    hv, jv = M.member(A, s, tt)
                    key = (hv, jv)
                    if key in seen: continue
                    seen.add(key); pool.append((('wfree', A, s, tt), hv, jv))
    print(json.dumps({'event': 'pool', 'size': len(pool), 'secs': round(time.time() - t0, 1),
                      'gamma': a.gamma, 'members': a.members}), flush=True)
    a28 = a28_members(M)
    ok, J, d = M.cost([h for h, _ in a28], [j for _, j in a28])
    print(json.dumps({'event': 'a28', 'feasible': ok, 'k': len(a28), 'J': J,
                      'cost': len(a28) + J if ok else None}), flush=True)
    # map a28 members into pool indices when present
    idx = {(h, j): i for i, (_, h, j) in enumerate(pool)}
    if a.start == 'a28':
        S = [idx[(h, j)] for h, j in a28 if (h, j) in idx]
        if len(S) < len(a28):
            print(json.dumps({'event': 'warn', 'a28_in_pool': len(S)}), flush=True)
    else:
        S = rnd.sample(range(len(pool)), 14)

    def evalS(S):
        ok, J, d = M.cost([pool[i][1] for i in S], [pool[i][2] for i in S])
        return (len(S) + J) if ok else (len(S) + 8 + 3 * d)

    cur = evalS(S); best = cur; bestS = list(S)
    hist = {}
    dumped = set()
    for it in range(a.iters):
        mv = rnd.random()
        T = list(S)
        if mv < 0.35 and len(T) > 9:
            T.pop(rnd.randrange(len(T)))
        elif mv < 0.6:
            T.append(rnd.randrange(len(pool)))
        else:
            T[rnd.randrange(len(T))] = rnd.randrange(len(pool))
        if len(set(T)) < len(T): continue
        c = evalS(T)
        if c <= cur or rnd.random() < math.exp(-(c - cur) / a.temp):
            S, cur = T, c
            if c < best or (c == best and len(T) < len(bestS)):
                best, bestS = c, list(T)
                print(json.dumps({'event': 'best', 'it': it, 'cost': best, 'k': len(T),
                                  'members': [pool[i][0] for i in T],
                                  'secs': round(time.time() - t0, 1)}), flush=True)
        if c <= 18:
            hist[(c, len(T))] = hist.get((c, len(T)), 0) + 1
        if a.dump and c <= a.dumpcost and len(T) <= a.dumpk and c == cur:
            key = tuple(sorted(T))
            if key not in dumped:
                dumped.add(key)
                with open(a.dump, 'a') as fh:
                    fh.write(json.dumps({'cost': c, 'k': len(T), 'members': [pool[i][0] for i in key]}) + '\n')
        if it % 2000 == 0:
            print(json.dumps({'event': 'tick', 'it': it, 'cur': cur, 'k': len(S), 'best': best,
                              'secs': round(time.time() - t0, 1)}), flush=True)
    out = {'event': 'done', 'best': best, 'bestS': [pool[i][0] for i in bestS],
           'visits_cost<=18': {'%d/%d' % kk: v for kk, v in sorted(hist.items())},
           'secs': round(time.time() - t0, 1)}
    print(json.dumps(out), flush=True)
    if a.out: open(a.out, 'w').write(json.dumps(out))


if __name__ == '__main__':
    main()
