"""X3 bil10.py: all 10-dim spaces S = T_b + J (dim J = 2) spanned by rank<=2 tensors.  Every such S must
contain a coset with 5 rank<=2 tensors (sizes are 1, 2, 3, 5 and three cosets must hold >= 10).
Input: bil_cosets2.txt (cosets with >= 2 tensors), bil_tb.txt."""
import sys, os
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
co = {}
for ln in open(D + 'bil_cosets2.txt'):
    p = ln.split(); co[int(p[1], 16)] = [int(t, 16) for t in p[3:]]
te = [tuple(int(z, 16) if i else int(z) for i, z in enumerate(t.split(':'))) for t in open(D + 'bil_tb.txt').read().split('TE')[1].split()]
def rk(vs):
    b = []; 
    for v in vs:
        for x in b: v = min(v, v ^ x)
        if v: b.append(v)
    return len(b)
TB = [b for p, b in te]
five = [c for c in co if len(co[c]) == 5]; three = [c for c in co if len(co[c]) == 3]
print('cosets size>=2:', len(co), 'five', len(five), 'three', len(three))
res = {}; 
for c1 in five:
    for c2 in five + three:
        if c2 == c1: continue
        c3 = c1 ^ c2
        n3 = len(co.get(c3, ()))
        tot = 5 + len(co[c2]) + n3
        if tot < 10: continue
        key = tuple(sorted((c1, c2, c3)))
        if key in res: continue
        els = co[c1] + co[c2] + co.get(c3, [])
        r = rk(els)
        res[key] = (tuple(sorted((5, len(co[c2]), n3))), r)
from collections import Counter
print('candidate J (2-dim, >= 10 tensors):', Counter(v for v in res.values()))
print('10-dim S spanned by rank<=2 tensors:', sum(1 for v in res.values() if v[1] == 10))
