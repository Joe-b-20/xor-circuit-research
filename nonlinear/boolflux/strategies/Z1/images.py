#!/usr/bin/env python3
"""Image arrangement of a sink last layer: columns of a parity-check matrix H of the output-usage
code (= images of the last products in V/(T + free), up to a basis change of that quotient).
Prints the columns, repeated images, and 3-term relations (img_a + img_b + img_c = 0).
usage: images.py FILE..."""
import sys, os
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import staircode as SC

for f in sys.argv[1:]:
    r = SC.core_and_code(f)
    L, cols = r['Lidx'], r['cols']
    K = len(L)
    # code words (length K) = c -> (<c, col_j>)_j ; dual = vectors y in F2^K with sum_j y_j col_j = 0
    # basis of dual: kernel of the 8 x K matrix M
    rows = []  # each row of M as K-bit int
    for b in range(8):
        rows.append(sum(1 << j for j, v in enumerate(cols) if (v >> b) & 1))
    # kernel of M (vectors y with M y = 0)
    piv = {}
    for v in rows:
        for h, w in piv.items():
            if (v >> h) & 1: v ^= w
        if v:
            h = v.bit_length() - 1
            for k in list(piv):
                if (piv[k] >> h) & 1: piv[k] ^= v
            piv[h] = v
    free = [j for j in range(K) if j not in piv]
    ker = []
    for fj in free:
        y = 1 << fj
        for h, w in piv.items():
            if (w >> fj) & 1: y |= 1 << h
        ker.append(y)
    D = len(ker)
    img = [sum(((ker[i] >> j) & 1) << i for i in range(D)) for j in range(K)]
    print(os.path.basename(f), 'K', K, 'D', D)
    groups = {}
    for j, v in enumerate(img):
        groups.setdefault(v, []).append(L[j])
    print('   distinct images', len(groups), 'repeats', [g for g in groups.values() if len(g) > 1])
    tri = [(L[a], L[b], L[c]) for a, b, c in combinations(range(K), 3) if img[a] ^ img[b] ^ img[c] == 0
           and img[a] != img[b]]
    print('   3-term relations', len(tri), tri[:12])
