#!/usr/bin/env python3
"""Finite fact: how many FULL helpers can a normalized circuit have?

A full value (PROOF.md F3/F4) is an even... no: an odd value h with three distinct boundary-triple representations
h = XOR(T1) = XOR(T2) = XOR(T3).  A full helper (r = 3) carries the three relations H + T1, H + T2, H + T3, and by
Lemma 4.4 ALL represented relations of a circuit are linearly independent.  Pivoting H + T1 at each full helper
leaves the two six-set vectors T1+T2, T1+T3 (in R6), so a set S of full helpers is possible only if the 2|S|
six-set vectors are independent: dim(sum_{s in S} V_s) = 2|S| with V_s = span(T1+T2, T1+T3).

This is a linear matroid parity problem (lines V_s in R6).  We compute
  (a) greedy / randomized lower bounds (explicit sets),
  (b) Lovasz's formula nu = rank(sum_s x_s (a_s b_s^T + b_s a_s^T)) / 2 over GF(2^32) with random x_s
      (a random substitution can only lower the rank: rank(random) <= 2 nu always; equality w.h.p., so the
      value is an upper bound only with probability >= 1 - 64/2^32 per run; several seeds are tried),
  (c) an exact depth-first search with rank pruning, with a time cap, for a rigorous maximum when it finishes.
Also: the histogram of pairwise compatibility and the max over sets that additionally avoid F4/F8 (implied anyway).
"""
import sys, time, random, itertools
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402

def rank2(vectors):
    piv = {}
    for v in vectors:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return len(piv)

class Basis:
    def __init__(self): self.piv = {}
    def reduce(self, v):
        while v:
            h = v.bit_length() - 1
            if h in self.piv: v ^= self.piv[h]
            else: return v
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
    def copy(self):
        b = Basis(); b.piv = dict(self.piv); return b
    def dim(self): return len(self.piv)

# ---- GF(2^32) ----
POLY = (1 << 32) | (1 << 22) | (1 << 2) | (1 << 1) | 1     # x^32 + x^22 + x^2 + x + 1 (checked irreducible below)
def gf_mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1
        a <<= 1
        if a >> 32: a ^= POLY
    return r
def gf_pow(a, e):
    r = 1
    while e:
        if e & 1: r = gf_mul(r, a)
        a = gf_mul(a, a); e >>= 1
    return r
def gf_inv(a): return gf_pow(a, (1 << 32) - 2)
def poly_irreducible_deg32(P):
    # Rabin: x^(2^32) = x mod P and gcd(x^(2^(32/p)) - x, P) = 1 for prime p | 32 (p = 2 -> 2^16)
    def pmod_mul(a, b):
        r = 0
        while b:
            if b & 1: r ^= a
            b >>= 1; a <<= 1
            if a >> 32: a ^= P
        return r
    def frob(a, k):   # a^(2^k) mod P
        for _ in range(k): a = pmod_mul(a, a)
        return a
    def pgcd(a, b):
        while b:
            while a.bit_length() >= b.bit_length() and a:
                a ^= b << (a.bit_length() - b.bit_length())
            a, b = b, a
        return a
    x = 2
    if frob(x, 32) != x: return False
    return pgcd(P, frob(x, 16) ^ x) == 1
assert poly_irreducible_deg32(POLY)

def gf_rank(M):
    """rank of a matrix over GF(2^32), rows as lists."""
    M = [row[:] for row in M]; n = len(M); m = len(M[0]) if M else 0
    r = 0
    for c in range(m):
        p = next((i for i in range(r, n) if M[i][c]), None)
        if p is None: continue
        M[r], M[p] = M[p], M[r]
        inv = gf_inv(M[r][c])
        M[r] = [gf_mul(inv, v) for v in M[r]]
        for i in range(n):
            if i != r and M[i][c]:
                f = M[i][c]
                M[i] = [vi ^ gf_mul(f, vr) for vi, vr in zip(M[i], M[r])]
        r += 1
        if r == n: break
    return r

def bits(v): return [i for i in range(64) if (v >> i) & 1]

def lovasz_rank(lines, seed):
    """rank of sum_s x_s (a b^T + b a^T) over GF(2^32), vectors a, b in F_2^64 (as 64-bit ints)."""
    rng = random.Random(seed)
    Y = [[0] * 64 for _ in range(64)]
    for a, b in lines:
        x = rng.getrandbits(32) or 1
        A, Bb = bits(a), bits(b)
        for i in A:
            for j in Bb:
                Y[i][j] ^= x; Y[j][i] ^= x
    return gf_rank(Y)

def analyse(name):
    B = BOUNDARY[name]
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    rep = {v: ts for v, ts in trip.items() if len(ts) >= 2}
    six = set()
    for ts in rep.values():
        for a, b in itertools.combinations(ts, 2): six.add(a | b)
    rho6 = rank2(list(six))
    print(f'{name}: full values {len(full)}, repeated {len(rep)}, six-sets {len(six)}, rho6 {rho6}')
    vals = sorted(full)
    lines = [(full[v][0] ^ full[v][1], full[v][0] ^ full[v][2]) for v in vals]
    # all three six-sets of a full value have rank 2
    assert all(rank2([a, b, a ^ b]) == 2 for a, b in lines)
    # span of all full lines
    allrank = rank2([x for ab in lines for x in ab])
    print(f'{name}: rank of the span of all full-value six-sets = {allrank} (so n3 <= {allrank//2} trivially)')
    # pairwise compatibility (independence of the 4 vectors)
    pairs_ok = 0; pairs_bad = 0; pairvals = {B[i] ^ B[j] for i, j in itertools.combinations(range(64), 2)}
    adj = 0
    for (i, (a, b)), (j, (c, d)) in itertools.combinations(enumerate(lines), 2):
        if rank2([a, b, c, d]) == 4: pairs_ok += 1
        else: pairs_bad += 1
        if (vals[i] ^ vals[j]) in pairvals: adj += 1
    print(f'{name}: pairs of full values: independent {pairs_ok}, dependent {pairs_bad} (F4 adjacent pairs: {adj})')
    # (a) randomized greedy lower bound
    best = []; t0 = time.time(); rng = random.Random(0)
    for it in range(4000):
        order = list(range(len(vals))); rng.shuffle(order)
        bs = Basis(); S = []
        for i in order:
            a, b = lines[i]
            t = bs.copy()
            if t.add(a) and t.add(b): bs = t; S.append(i)
        if len(S) > len(best): best = S
    print(f'{name}: randomized greedy best = {len(best)} full helpers (values {[hex(vals[i]) for i in best]}) in {time.time()-t0:.1f}s')
    # (b) Lovasz generic rank with random substitutions
    for seed in (1, 2, 3):
        r = lovasz_rank(lines, seed)
        print(f'{name}: Lovasz alternating-matrix rank (seed {seed}) = {r}  ->  nu = {r//2}')
    # (c) exact DFS with pruning (time-capped)
    N = len(vals); best_exact = [len(best)]; nodes = [0]; deadline = time.time() + float(sys.argv[2]) if len(sys.argv) > 2 else time.time() + 600
    timed_out = [False]
    def dfs(idx, bs, chosen, cands):
        nodes[0] += 1
        if time.time() > deadline: timed_out[0] = True; return
        # candidates still independent of the current span
        newc = []
        for i in cands:
            if i < idx: continue
            a, b = lines[i]
            t = bs.copy()
            if t.add(a) and t.add(b): newc.append(i)
        # upper bound: dimension of span(current + candidate lines) limits the number of further lines
        if not newc:
            if len(chosen) > best_exact[0]: best_exact[0] = len(chosen); print(f'   new best {len(chosen)}', flush=True)
            return
        t = bs.copy()
        for i in newc: t.add(lines[i][0]); t.add(lines[i][1])
        ub = len(chosen) + min(len(newc), (t.dim() - bs.dim()) // 2)
        if ub <= best_exact[0]: return
        for k, i in enumerate(newc):
            a, b = lines[i]
            t = bs.copy(); t.add(a); t.add(b)
            dfs(i + 1, t, chosen + [i], newc[k + 1:])
            if timed_out[0]: return
        if len(chosen) > best_exact[0]: best_exact[0] = len(chosen)
    t0 = time.time()
    dfs(0, Basis(), [], list(range(N)))
    status = 'TIMED OUT (lower bound only)' if timed_out[0] else 'COMPLETE (exact maximum)'
    print(f'{name}: exact DFS: max independent full set = {best_exact[0]}, {nodes[0]} nodes, {time.time()-t0:.0f}s, {status}')
    return dict(name=name, full=len(full), rho6=rho6, allrank=allrank, greedy=len(best), greedy_set=[vals[i] for i in best],
                dfs_max=best_exact[0], dfs_complete=not timed_out[0])

if __name__ == '__main__':
    import json
    names = sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']
    out = [analyse(n) for n in names]
    json.dump(out, open(Path.home()/'xs-campaigns/2026-11-07-sprint/qbound'/f'full_helpers_{"_".join(names)}.json', 'w'), indent=1)
