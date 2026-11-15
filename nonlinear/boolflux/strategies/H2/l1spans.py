"""Distinct level-1 spans (mod affine) of circuits with exactly 9 / 10 level-1 products."""
import sys, glob, os
from h2lib import Basis
import a28parse as AP
files = sorted(glob.glob('../../../nist/aes-sbox/aes-sbox-a2*.circ.txt')) + sorted(glob.glob('../../../nist/aes-sbox/aes-sbox-a3[0-2]*.circ.txt')) + \
        sorted(glob.glob(os.path.expanduser('~/xs-campaigns/2026-11-14-hub/best/*.circ.txt')))
aff = Basis()
for v in [AP.ONE] + AP.BITS: aff.add(v)
seen = {}
for f in files:
    try: _, A = AP.load(f)
    except Exception as e: continue
    L = [a['out'] for a in A if a['stage'] == 'L']
    B = Basis()
    for o in L: B.add(aff.full_reduce(o)[0])
    vs = sorted(r[0] for r in B.rows.values())
    piv = [v.bit_length() - 1 for v in vs]
    for i in range(len(vs)):
        for j in range(len(vs)):
            if i != j and (vs[j] >> piv[i]) & 1: vs[j] ^= vs[i]
    k = (len(L), tuple(sorted(vs)))
    seen.setdefault(k, []).append(os.path.abspath(f))
for (n, _), fs in sorted(seen.items(), key=lambda t: t[0][0]):
    print(n, len(fs), fs[0])
