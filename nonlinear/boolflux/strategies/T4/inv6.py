#!/usr/bin/env python3
"""T4: GF(16) inversion components at depth 3 (levels: AND | AND | XOR), exhaustive in the model

  level 1 (gate level 6): A2 = AND of two affine functions of d (all affine functions of d are
          assumed available at level 0 = gate level 5, i.e. the inversion input level)
  level 2 (gate level 7): A3 = AND of two level-1 signals (A2 outputs or affine functions);
          XOR of two level-1 signals
  level 3 (gate level 8): Y-form = XOR of two level-2 signals, required to equal Tr(alpha d^-1) + c

Y-form shapes allowed by this schedule: A3 + A3', A3 + A2 + A2', A3 + A2 + aff, A3 + aff.
Fact used: Tr(alpha d^-1) is homogeneous cubic (exponents 14, 13, 11, 7), so k independent Y-forms
need k A3 gates with independent cubic parts; with one A2 the cubic parts span <= 2 dims.
This program: for k2 = 2 A2 gates (all pairs, up to d -> c d^(2^i)), which target classes can be
realised directly (A3 + residual), and the rank of the realised set.
    python3 inv6.py [k2]
"""
import sys, itertools, json
def m256(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11b
        b >>= 1
    return r
def p256(a, e):
    r = 1
    while e:
        if e & 1: r = m256(r, a)
        a = m256(a, a); e >>= 1
    return r
SUB = sorted({p256(a, 17) for a in range(256)})
assert len(SUB) == 16
IDX = {z: i for i, z in enumerate(SUB)}
def tr16(z):
    t = 0; s = z
    for _ in range(4): t ^= s; s = m256(s, s)
    return t  # 0 or 1
def tab(fn):
    return sum((fn(z) & 1) << i for i, z in enumerate(SUB))
ONE = 0xFFFF
LIN = {g: tab(lambda z, g=g: tr16(m256(g, z))) for g in SUB}          # g=0 -> 0
AFF = sorted({LIN[g] ^ c for g in SUB for c in (0, ONE)})
NONC = [f for f in AFF if f not in (0, ONE)]
def inv(z): return p256(z, 254) if z else 0
TGT = {}
for al in SUB:
    if al == 0: continue
    t = tab(lambda z, al=al: tr16(m256(al, inv(z))))
    TGT[t] = al; TGT[t ^ ONE] = al
# group d -> c d^(2^i)
PERMS = []
for c in SUB:
    if c == 0: continue
    for i in range(4):
        PERMS.append([IDX[m256(c, p256(z, 1 << i))] for z in SUB])
def apply(f, P):
    g = 0
    for i in range(16):
        if (f >> i) & 1: g |= 1 << P[i]
    return g
def rank(vs):
    piv = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return len(piv)
A2C = sorted({a & b for a in NONC for b in NONC if (a & b) not in AFF})
print('affine', len(AFF), 'A2 candidates', len(A2C), 'targets', len(TGT) // 2, flush=True)

def analyse(qs):
    L6 = set(AFF) | set(qs) | {q ^ ONE for q in qs}
    L6 = sorted(L6)
    R0 = set(AFF)
    for q in qs:
        for a in AFF: R0.add(q ^ a)
    for q1, q2 in itertools.combinations(qs, 2):
        R0.add(q1 ^ q2); R0.add(q1 ^ q2 ^ ONE)
    real = {}
    for p, r in itertools.combinations_with_replacement(L6, 2):
        a = p & r
        for t in TGT:
            if (t ^ a) in R0:
                real.setdefault(TGT[t], []).append((p, r, t ^ a))
    alphas = sorted(real)
    # rank of realised targets (as functions): use Tr(alpha Y) tables
    tabs = [next(t for t in TGT if TGT[t] == al and not (t & 1)) for al in alphas]
    return rank(tabs), alphas, real

def pairs_rank(qs, k3):
    """best rank with k3 A3 gates when Y-forms may be direct (A3 + residual) or A3 + A3'"""
    L6 = sorted(set(AFF) | set(qs) | {q ^ ONE for q in qs})
    R0 = set(AFF)
    for q in qs:
        for a in AFF: R0.add(q ^ a)
    for q1, q2 in itertools.combinations(qs, 2):
        R0.add(q1 ^ q2); R0.add(q1 ^ q2 ^ ONE)
    P = sorted({p & r for p, r in itertools.combinations_with_replacement(L6, 2)} - set(AFF))
    direct = {}
    for a in P:
        for t in TGT:
            if (t ^ a) in R0: direct.setdefault(a, set()).add(TGT[t])
    edges = {}
    Pset = set(P)
    for a in P:
        for t in TGT:
            b = a ^ t
            if b in Pset and b > a: edges.setdefault(a, []).append((b, TGT[t]))
    cand = sorted(set(direct) | set(edges) | {b for L in edges.values() for b, _ in L})
    tabof = {al: next(t for t in TGT if TGT[t] == al and not (t & 1)) for al in set(TGT.values())}
    best = 0
    if len(cand) > 70: cand = cand[:70]
    cs = set(cand)
    for S in itertools.combinations(cand, k3):
        als = set()
        for a in S: als |= direct.get(a, set())
        for a in S:
            for b, al in edges.get(a, []):
                if b in S: als.add(al)
        if len(als) < 4: continue
        r = rank([tabof[al] for al in als])
        if r > best: best = r
        if best == 4: break
    return best, len(cand)

if __name__ == '__main__':
    k2 = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    mode = sys.argv[2] if len(sys.argv) > 2 else 'direct'
    seen = set(); best = 0; hist = {}
    examples = []
    IDXA = {q: i for i, q in enumerate(A2C)}
    PM = [[IDXA[apply(q, P)] for q in A2C] for P in PERMS]
    for qi in itertools.combinations(range(len(A2C)), k2):
        key = min(tuple(sorted(pm[i] for i in qi)) for pm in PM)
        if key in seen: continue
        seen.add(key)
        qs = [A2C[i] for i in qi]
        if mode == 'pairs':
            r, nc = pairs_rank(qs, 4)
            hist[r] = hist.get(r, 0) + 1
            continue
        r, alphas, real = analyse(list(qs))
        hist[r] = hist.get(r, 0) + 1
        if r >= 4 and len(examples) < 20:
            examples.append({'A2': [hex(q) for q in qs], 'alphas': alphas, 'n_alpha': len(alphas)})
    print(json.dumps({'k2': k2, 'orbits': len(seen), 'rank_hist': hist}), flush=True)
    for e in examples[:20]: print(json.dumps(e))
