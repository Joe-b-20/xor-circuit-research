#!/usr/bin/env python3
"""Is the stage-1 span of circuit A the image of the stage-1 span of circuit B under a field map
x -> c * x^(2^i) (c in GF(256)*, AES polynomial)?  span = span(1, x, stage-L products) (H2 stages).
usage: spaneq.py A B [contain]  (contain: image of span(B) inside span(A))"""
import sys, os
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/H2'))
import a28parse as AP
from h2lib import gmul, gpow


def span_of(f):
    _, ANDS = AP.load(f)
    return [AP.ONE] + AP.BITS + [A['out'] for A in ANDS if A['stage'] == 'L']


def rref(vs):
    rows = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in rows: v ^= rows[h]
            else: rows[h] = v; break
    for h in sorted(rows):
        for k in rows:
            if k != h and (rows[k] >> h) & 1: rows[k] ^= rows[h]
    return frozenset(rows.values())


CONTAIN = len(sys.argv) > 3
A = rref(span_of(sys.argv[1])); Bv = span_of(sys.argv[2])
hits = []
for i in range(8):
    for c in range(1, 256):
        perm = [gmul(c, gpow(x, 1 << i)) for x in range(256)]
        img = []
        for t in Bv:
            u = 0
            for x in range(256):
                if (t >> perm[x]) & 1: u |= 1 << x
            img.append(u)
        if rref(img) == A or (CONTAIN and len(rref(list(A) + img)) == len(A)): hits.append((i, c))
print('dimA', len(A), 'maps x -> c x^(2^i) taking span(B) to span(A):', len(hits), hits[:8])
