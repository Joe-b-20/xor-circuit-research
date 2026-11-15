#!/usr/bin/env python3
"""T4: which AES output-bit functionals are GF(16)-proportional (intrinsic sharing structure of the
bottom bilinear layer S_k = Tr16(Y * R_k(a)), R_k = Tr_{256/16}(theta_k * conj(a)))."""
def mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11b
        b >>= 1
    return r
def pw(a, e):
    r = 1
    while e:
        if e & 1: r = mul(r, a)
        a = mul(a, a); e >>= 1
    return r
def inv(a): return pw(a, 254) if a else 0
def tr(z):
    t = 0; s = z
    for _ in range(8): t ^= s; s = mul(s, s)
    return t & 1
# AES affine: b_i' = b_i ^ b_{i+4} ^ b_{i+5} ^ b_{i+6} ^ b_{i+7} ^ c_i  (bit i of byte)
def sbox(a):
    z = inv(a); r = 0
    for i in range(8):
        b = ((z >> i) ^ (z >> ((i+4) % 8)) ^ (z >> ((i+5) % 8)) ^ (z >> ((i+6) % 8)) ^ (z >> ((i+7) % 8))) & 1
        r |= b << i
    return r ^ 0x63
# functional for output bit i: f_i(z) = bit i of A z (linear part); find theta_i with Tr(theta z) = f_i(z)
def Alin(z):
    r = 0
    for i in range(8):
        b = ((z >> i) ^ (z >> ((i+4) % 8)) ^ (z >> ((i+5) % 8)) ^ (z >> ((i+6) % 8)) ^ (z >> ((i+7) % 8))) & 1
        r |= b << i
    return r
th = []
for i in range(8):
    for t in range(1, 256):
        if all(tr(mul(t, z)) == (Alin(z) >> i) & 1 for z in range(256)):
            th.append(t); break
print('theta', [hex(t) for t in th])
gf16 = [z for z in range(256) if pw(z, 16) == z]
def coset(t):  # canonical rep: min of t*GF16*
    return min(mul(t, g) for g in gf16 if g)
cs = [coset(t) for t in th]
print('coset reps', [hex(c) for c in cs])
from collections import Counter
print('coset multiplicities', Counter(cs))
# also: output bits in NIST order y0 = msb (bit 7)
