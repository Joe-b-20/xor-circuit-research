#!/usr/bin/env python3
"""T4: explicit depth-3 GF(16) inversion designs with 3 A2 gates (the rank-4 orbits of inv6.py and
all their images under d -> c d^(2^i)), the Y-form set they can provide, and the best product sharing
between the two GF(16)-proportional AES outputs (bits 1 and 2 = NIST y6, y5).
Each Y-form: Tr(alpha d^-1) + c = A3 + residual, residual in {aff, A2 + aff, A2 + A2'};
a 5th Y-form may be the XOR of two Y-forms whose residuals agree (A3 + A3', 7-AND inversion).
    python3 invdesign.py  -> JSON lines of designs (best sharing first) to stdout
"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import inv6 as I  # noqa  (module-level code of inv6 runs only under __main__? no: guard below)

SUB, ONE, AFF, NONC, TGT, PERMS = I.SUB, I.ONE, I.AFF, I.NONC, I.TGT, I.PERMS
m, p = I.m256, I.p256
def inv(z): return p(z, 254) if z else 0
def tr16(z): return I.tr16(z)
# AES output functionals theta (bit i of A z = Tr256(theta_i z))
def tr256(z):
    t = 0; s = z
    for _ in range(8): t ^= s; s = m(s, s)
    return t & 1
def Alin(z):
    r = 0
    for i in range(8):
        b = ((z >> i) ^ (z >> ((i + 4) % 8)) ^ (z >> ((i + 5) % 8)) ^ (z >> ((i + 6) % 8)) ^ (z >> ((i + 7) % 8))) & 1
        r |= b << i
    return r
TH = []
for i in range(8):
    for t in range(1, 256):
        if all(tr256(m(t, z)) == (Alin(z) >> i) & 1 for z in range(256)):
            TH.append(t); break
GAMMA = m(TH[1], inv(TH[2]))          # theta_bit1 = GAMMA * theta_bit2
assert p(GAMMA, 16) == GAMMA
def dual(B):
    out = []
    for i in range(4):
        c = [z for z in SUB if z and all(tr16(m(z, B[j])) == (1 if j == i else 0) for j in range(4))]
        assert len(c) == 1; out.append(c[0])
    return out
def indep(B):
    s = {0}
    for b in B: s |= {x ^ b for x in s}
    return len(s) == 1 << len(B)
def best_share(L):
    """max shared products between y5 (theta_bit2) and y6 (theta_bit1 = GAMMA theta_bit2)"""
    best = (0, None, None)
    bases = [B for B in itertools.combinations(sorted(L), 4) if indep(B)]
    for A in bases:
        dA = dict(zip(A, dual(A)))
        for A2 in bases:
            dB = dict(zip(A2, dual(A2)))
            s = sum(1 for a in A if a in dB and dA[a] == m(GAMMA, dB[a]))
            if s > best[0]: best = (s, A, A2)
    return best

def realise(qs):
    """direct Y-form realisations: alpha -> list of (A3 operands (p, r), residual description)"""
    L6 = sorted(set(AFF) | set(qs) | {q ^ ONE for q in qs})
    R0 = {}
    for a in AFF: R0.setdefault(a, ('aff', a))
    for i, q in enumerate(qs):
        for a in AFF: R0.setdefault(q ^ a, ('A2+aff', i, a))
    for (i, q1), (j, q2) in itertools.combinations(enumerate(qs), 2):
        R0.setdefault(q1 ^ q2, ('A2+A2', i, j, 0)); R0.setdefault(q1 ^ q2 ^ ONE, ('A2+A2', i, j, ONE))
    out = {}
    for pp, rr in itertools.combinations_with_replacement(L6, 2):
        a = pp & rr
        if a in AFF: continue
        for t, al in TGT.items():
            if (t ^ a) in R0:
                out.setdefault(al, []).append({'p': pp, 'r': rr, 'a3': a, 't': t, 'res': R0[t ^ a]})
    return out

def design_for(qs):
    real = realise(qs)
    als = sorted(real)
    if len(als) < 4: return None
    tabs = [next(t for t in TGT if TGT[t] == al and not (t & 1)) for al in als]
    if I.rank(tabs) < 4: return None
    res = []
    for four in itertools.combinations(als, 4):
        if not indep(four): continue
        L = set(four)
        fifth = []
        for x, y in itertools.combinations(four, 2):
            rx = {json.dumps(d['res']) for d in real[x]}; ry = {json.dumps(d['res']) for d in real[y]}
            if rx & ry: fifth.append(x ^ y)
        s4 = best_share(L)
        s5 = max([best_share(L | {f}) + (f,) for f in fifth], key=lambda z: z[0], default=(0, None, None, None))
        res.append({'four': four, 'share4': s4[0], 'fifth_opts': fifth, 'share5': s5[0], 'fifth': s5[3] if s5[0] else None,
                    'A_y5': s5[1] or s4[1], 'A_y6': s5[2] or s4[2]})
    best8 = best_share(set(als)) if len(als) >= 5 else (0,)
    res.sort(key=lambda r: (-r['share5'], -r['share4']))
    return {'A2': qs, 'alphas': als, 'best7': res[0] if res else None, 'all7': res, 'share8_all_direct': best8[0]}

REPS = [[0x3c, 0xa0a, 0x9600], [0x3c, 0x1284, 0x8822], [0x3c, 0x2288, 0x9090]]

if __name__ == '__main__':
    seen = set()
    for rep in REPS:
        for P in PERMS:
            qs = sorted(I.apply(q, P) for q in rep)
            if tuple(qs) in seen: continue
            seen.add(tuple(qs))
            d = design_for(qs)
            if d: print(json.dumps(d), flush=True)
