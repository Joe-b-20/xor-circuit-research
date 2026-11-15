#!/usr/bin/env python3
"""P2: stage-1 basis swap for AD4 circuits whose forms use stage 1 beyond N (the A28 family).

Q = span(1, x, stage-1 product tables) (dimension 1 + 8 + 9).  Every form above stage 1 (AND
operands of AND level >= 2, outputs) uses stage 1 only through Q, so stage 1 can be replaced by
ANY 9 products (L + a)(R + b) of affine forms whose tables, with 1 and x, span Q; each form's
stage-1 part is re-expressed in the new basis (the affine remainder goes into the form's input /
constant bits).  Same AND count, same AND functions above stage 1 (as functions).  We enumerate all
rank-1 products in Q, choose bases (greedy by level + random restarts) and compute the AND-skeleton
depth bound (F's Huffman bound) of the new skeleton.

    python3 cover28.py CIRCUIT OUT.json [--tries N] [--seed S] [--maxterms T]
"""
import heapq
import itertools
import json
import random
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton   # noqa: E402

ONES = (1 << 256) - 1
POP = [bin(i).count('1') for i in range(256)]


def lin(mask):
    return sum((POP[mask & x] & 1) << x for x in range(256))


LIN = [lin(m) for m in range(256)]


def huff(levels, const=False):
    if not levels: return 0
    if len(levels) == 1: return levels[0] + (1 if const else 0)
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, max(a, b) + 1)
    return h[0]


def bound(ands, outs, n):
    nb = 1 + n + len(ands); arr = [0] * nb
    for k, (L, R) in enumerate(ands):
        tl = [arr[p] for p in range(1, nb) if (L >> p) & 1]; tr = [arr[p] for p in range(1, nb) if (R >> p) & 1]
        arr[1 + n + k] = 1 + max(huff(tl, L & 1), huff(tr, R & 1))
    ol = [huff([arr[p] for p in range(1, nb) if (F >> p) & 1], F & 1) for F in outs]
    return max(ol), arr, ol


class Elim:
    def __init__(self):
        self.rows = []   # (pivot, vec, tag)

    def reduce(self, v):
        t = 0
        for pb, rv, rt in self.rows:
            if (v >> pb) & 1: v ^= rv; t ^= rt
        return v, t

    def add(self, v, tag):
        v, t = self.reduce(v)
        if v == 0: return False
        self.rows.append((v.bit_length() - 1, v, t ^ tag)); return True


def main():
    f = sys.argv[1]; outp = sys.argv[2]
    tries = int(sys.argv[sys.argv.index('--tries') + 1]) if '--tries' in sys.argv else 2000
    seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 1
    maxterms = int(sys.argv[sys.argv.index('--maxterms') + 1]) if '--maxterms' in sys.argv else 5
    rng = random.Random(seed)
    c = core.read_ncff(f) if f.endswith('.txt') else core.from_kernel(open(f).read())
    n = c.n; T = c.tables()
    la = [0] * n
    for op, a, b in c.gates: la.append((1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]))
    sk = skeleton.extract(c); ands = list(sk['ands']); outs = list(sk['outputs'])
    sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    st1 = [k for k, s in enumerate(sig) if la[s] == 1]
    b0, _, ol0 = bound(ands, outs, n)
    print('original skeleton bound', b0, ol0, 'stage-1 idx', st1, flush=True)
    # Q basis: 1, x_i, stage-1 tables
    E = Elim()
    E.add(ONES, 0)
    for i in range(n): E.add(T[i], 0)
    for k in st1:
        assert E.add(T[sig[k]], 0), 'stage-1 products dependent'
    # candidate products in Q: L, R linear masks (input mask convention: x_i is bit 7-i of t)
    cands = []
    for L in range(1, 256):
        if POP[L] > maxterms: continue
        for R in range(L + 1, 256):
            if POP[R] > maxterms: continue
            t = LIN[L] & LIN[R]
            v, _ = E.reduce(t)
            if v: continue
            cands.append((L, R))
    print('rank-1 products in Q with <= %d terms per operand:' % maxterms, len(cands), flush=True)
    # operand level for linear mask m with const choice: terms = POP; level = huff of zeros
    def oplev(m): return 0 if POP[m] <= 1 else (POP[m] - 1).bit_length()
    cands.sort(key=lambda lr: (max(oplev(lr[0]), oplev(lr[1])), POP[lr[0]] + POP[lr[1]]))

    def mask_to_form(m):     # input mask -> skeleton positions 1 + i for x_i
        F = 0
        for i in range(n):
            if (m >> (n - 1 - i)) & 1: F |= 1 << (1 + i)
        return F

    def evaluate(basis):
        # basis: 9 (L, R) with consts (a, b): product table P = (L+a)(R+b)
        E2 = Elim()
        E2.add(ONES, 1 << 0)
        for i in range(n): E2.add(T[i], 1 << (1 + i))
        for idx, (L, R, a_, b_) in zip(st1, basis):
            P = (LIN[L] ^ (ONES if a_ else 0)) & (LIN[R] ^ (ONES if b_ else 0))
            if not E2.add(P, 1 << (1 + n + idx)): return None
        new_ands = list(ands)
        for idx, (L, R, a_, b_) in zip(st1, basis):
            new_ands[idx] = (mask_to_form(L) | a_, mask_to_form(R) | b_)
        st1mask = 0
        for k in st1: st1mask |= 1 << (1 + n + k)
        def rewrite(F):
            part = 0
            for k in st1:
                if (F >> (1 + n + k)) & 1: part ^= T[sig[k]]
            if not part and not (F & st1mask): return F
            v, tag = E2.reduce(part)
            assert v == 0
            return (F & ~st1mask) ^ tag
        for k in range(len(ands)):
            if k in st1: continue
            L, R = new_ands[k]; new_ands[k] = (rewrite(L), rewrite(R))
        new_outs = [rewrite(F) for F in outs]
        b, arr, ol = bound(new_ands, new_outs, n)
        return b, ol, new_ands, new_outs

    best = None; res = []
    for tr in range(tries):
        # randomized greedy basis: shuffle within level classes
        order = list(cands)
        if tr:
            order.sort(key=lambda lr: (max(oplev(lr[0]), oplev(lr[1])) + rng.random() * 1.5))
        E3 = Elim()
        E3.add(ONES, 0)
        for i in range(n): E3.add(T[i], 0)
        basis = []
        for L, R in order:
            if E3.add(LIN[L] & LIN[R], 0):
                basis.append((L, R, rng.randrange(2) if tr else 0, rng.randrange(2) if tr else 0))
                if len(basis) == len(st1): break
        if len(basis) < len(st1):
            print('no basis of rank-1 products spans Q with these operand sizes'); break
        r = evaluate(basis)
        if r is None: continue
        b, ol, na, no = r
        key = (b, sum(ol))
        if best is None or key < best[0]:
            best = (key, basis, na, no)
            print('try %d bound %d outputs %s basis levels %s' % (tr, b, ol, [1 + max(oplev(L), oplev(R)) for L, R, _, _ in basis]), flush=True)
    json.dump({'circuit': f, 'orig_bound': b0, 'best': best[0], 'basis': best[1],
               'ands': [[hex(L), hex(R)] for L, R in best[2]], 'outputs': [hex(F) for F in best[3]]},
              open(outp, 'w'))


if __name__ == '__main__':
    main()
