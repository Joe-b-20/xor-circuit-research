#!/usr/bin/env python3
"""Positive control for pairgen/r1enum: window U = {k} (one sink AND, m = 1): the AND itself must be
found.  Prints the Gray-code index (hex) of an element of span{a, b} with top bit 0 (a, b = operands
of AND k in the V coordinates used by pairgen).  usage: pairctl.py CIRCUIT k"""
import sys, os
sys.path.insert(0, os.path.expanduser("~/xcr-boolflux/nonlinear/boolflux/strategies/H3"))
from wsat import Base
b = Base(sys.argv[1]); k = int(sys.argv[2]); n = b.n
R = [j for j in range(b.K) if j != k]


def vec(form):
    v = 0
    for i in range(n):
        if (form >> (1 + i)) & 1: v |= 1 << i
    for j in range(b.K):
        if (form >> (1 + n + j)) & 1: v |= 1 << (n + R.index(j))
    return v


L, Rf = b.sk["ands"][k]
a, c = vec(L), vec(Rf); nv = n + len(R)
for x in (a, c, a ^ c):
    if not (x >> (nv - 1)) & 1:
        g = x; i = 0
        while g:
            i ^= g; g >>= 1
        print("%x" % i); break
