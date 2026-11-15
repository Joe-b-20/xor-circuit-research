#!/usr/bin/env python3
"""Count / list all slack-1 sets of last-level ANDs (rank of outputs mod span(rest) = |S| - 1),
minimal or not.  Works in the quotient by W0 = span(1, x, non-last-level ANDs), where the sink
classes are independent coordinates e_s and the outputs are vectors in F2^q.
Usage: slack1sets.py CIRCUIT [maxsize] [--list]"""
import itertools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from wsat import Base, Span, ONES

b = Base(sys.argv[1]); mx = int(sys.argv[2]) if len(sys.argv) > 2 else 9
sinks = [k for k in range(b.K) if not b.cons[k]]
inner = [k for k in range(b.K) if b.cons[k]]
# output coordinates over sinks: solve y = w0 + sum c_s sink_s
W0 = [ONES] + b.tab[1:1 + b.n] + [b.andtab[k] for k in inner]
piv = {}
for pos, t in enumerate(W0 + [b.andtab[s] for s in sinks]):
    v, f = t, 1 << pos
    while v:
        h = v.bit_length() - 1
        if h in piv: v ^= piv[h][0]; f ^= piv[h][1]
        else: piv[h] = (v, f); break
    assert v, 'dependent basis'
nb = len(W0)
Y = []
for y in b.out:
    v, f = y, 0
    while v:
        h = v.bit_length() - 1
        v ^= piv[h][0]; f ^= piv[h][1]
    Y.append(f >> nb)          # coordinates over sinks (bit i = sinks[i])
q = len(sinks)


def rank(vs):
    return len(Span(vs))


by = {}
for s in range(2, mx + 1):
    for S in itertools.combinations(range(q), s):
        mask = sum(1 << i for i in S)
        # outputs mod span(other sinks): drop coordinates outside S
        r = rank([y & mask for y in Y])
        if r == s - 1: by.setdefault(s, []).append([sinks[i] for i in S])
print({s: len(v) for s, v in by.items()}, flush=True)
if '--list' in sys.argv:
    for s, v in by.items():
        for S in v: print(','.join(map(str, S)))
