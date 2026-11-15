"""Fast exact n-block / N-parity / x-junk test for GF(4)-norm member sets (agent H1).

Member m = (z, zeta) (track C's model). Facts used (NOTES section 7):
  [C] coefficient of x^239 (class of x^-1) of member_table = Y = z / zeta (all members, 4 gammas);
  [C] coefficient of x^188 (class 47) = z (sampled members, gamma none and g^17);
  [C, fitted on sampled members] coefficient of x^3 = z^3 zeta, coefficient of x^9 =
      z^9 zeta^3 + gamma^8 Y^128, coefficients of x^5 and (gamma none) x^17 vanish;
  [C, parity.py; = H2 vjunk.py] N-junk of a target combination depends only on its class
      parities, and is free (in span(1, N, n)) iff the parity vector is in Pi(gamma).
Classes outside S1/MID: class 127 and class 47 appear only in members (S1: weight <= 2, MID:
multiples of 17), so per output: sum c Y = b_j, sum c z = 0 are necessary.
Test for a set S: K_Pi = {c in F_2^k : sum c z = 0, parity(c) in Pi}; need Y(K_Pi) = F (8 dims).
x-junk: J(c) = (sum c z^3 zeta, sum c z^9 zeta^3 + gamma^8 (sum c Y)^128) in F^2;
Jx >= dim J(K_Pi) - dim J(ker Y|K_Pi) (exact when the kernel is 0, i.e. excess 0).
usage (selftest): python3 nfast.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, EXP, LOG

MU5 = [EXP[(51 * i) % 255] for i in range(5)]
IDX = {v: i for i, v in enumerate(MU5)}
_PI = {}


def pw(a, e):
    return 0 if a == 0 else EXP[(LOG[a] * e) % 255]


def mul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def pi_basis(gamma):
    """Pi(gamma) as list of 5-bit ints (from parity.txt, recomputed lazily via parity.py)"""
    if gamma not in _PI:
        import parity
        free, _ = parity.pi_space(gamma)
        _PI[gamma] = free
    return _PI[gamma]


def reduce_mod(v, basis_rows):
    for b in basis_rows:
        if v ^ b < v: v ^= b
    return v


def echelon(vs):
    rows = []
    for v in vs:
        for r in rows:
            if v ^ r < v: v ^= r
        if v:
            rows.append(v); rows.sort(reverse=True)
    return rows


def test(members, gamma):
    """members: list of (z, zeta value). Returns dict: ok (n-block + parity), excess, Jlb."""
    k = len(members)
    piv = echelon(pi_basis(gamma))           # subspace of F_2^5
    g8 = 0 if gamma == 'none' else pw(EXP[int(gamma)], 8)
    # per member: first map (z | parity mod Pi) and second map (Y | J3 | J9)
    A = []; B = []
    for z, zt in members:
        i = IDX[zt]
        par = reduce_mod(1 << i, piv)
        A.append(z | (par << 8))
        Y = mul(z, gf.INV[zt])
        j3 = mul(pw(z, 3), zt)
        j9 = mul(pw(z, 9), pw(zt, 3)) ^ mul(g8, pw(Y, 128))
        B.append(Y | (j3 << 8) | (j9 << 16))
    # kernel of A over F_2^k: eliminate with tags
    rows = []                                # (value, tag)
    kern = []
    for m in range(k):
        v, t = A[m], 1 << m
        for rv, rt in rows:
            if v ^ rv < v: v ^= rv; t ^= rt
        if v:
            rows.append((v, t)); rows.sort(reverse=True)
        else:
            kern.append(t)
    def img(t):
        out = 0
        for m in range(k):
            if t >> m & 1: out ^= B[m]
        return out
    KB = [img(t) for t in kern]              # images of a basis of K_Pi
    Yimg = echelon([b & 0xFF for b in KB])
    ok = len(Yimg) == 8
    res = {'k': k, 'dimKPi': len(kern), 'dimY': len(Yimg), 'ok': ok}
    if not ok: return res
    # kernel of Y on K_Pi
    rows = []; ker = []
    for b in KB:
        v, w = b & 0xFF, b >> 8
        for rv, rw in rows:
            if v ^ rv < v: v ^= rv; w ^= rw
        if v:
            rows.append((v, w)); rows.sort(reverse=True)
        else:
            ker.append(w)
    dJ = len(echelon([b >> 8 for b in KB]))
    dJk = len(echelon(ker))
    res.update({'excess': len(kern) - 8, 'Jlb': dJ - dJk, 'Jall': dJ})
    return res


def selftest():
    import json
    L = json.load(open('/home/joebachir20/xs-campaigns/2026-11-15-study/H1/layers.json'))
    for l in L:
        mem = [tuple(m) for m in l['members']]
        print(l['gamma'], l['files'][0][:28], test(mem, l['gamma']))


if __name__ == '__main__':
    selftest()
