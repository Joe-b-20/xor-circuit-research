"""X3 semi_mod.py: cosets of semi-members modulo M8 = the 8-dim space formed by the 255 member cosets (and 0).
A semi-member can enter an output combination only through a relation among cosets; this lists the short ones."""
import os
from collections import Counter, defaultdict
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
cos = defaultdict(list)
for ln in open(D + 'semi_members.tsv'):
    if ln[0] == '#': continue
    p = ln.rstrip('\n').split('\t'); cos[int(p[1], 16)].append((int(p[2]), p[7] + p[8]))
mem = [c for c, v in cos.items() if v[0][0] == 5]
b = {}
def red(v):
    while v:
        h = v.bit_length() - 1
        if h not in b: return v
        v ^= b[h]
    return 0
for c in mem:
    r = red(c)
    if r: b[r.bit_length() - 1] = r
print('dim M8 =', len(b), '(member cosets', len(mem), ')')
semi = [c for c in cos if cos[c][0][0] != 5]
cl = defaultdict(list)
for c in semi: cl[red(c)].append(c)
print('semi cosets', len(semi), 'in M8:', len(cl.get(0, [])), 'classes mod M8:', len(cl))
print('class size histogram (number of semi cosets per class mod M8):', sorted(Counter(len(v) for v in cl.values()).items()))
# rank of semi classes mod M8
b2 = dict(b); rk = 0
for c in semi:
    v = c
    while v:
        h = v.bit_length() - 1
        if h not in b2: b2[h] = v; rk += 1; break
        v ^= b2[h]
print('rank of semi cosets mod M8:', rk, '(quotient has dim', 24 - len(b), ')')
# composition of one class
k = max(cl, key=lambda z: len(cl[z]))
print('largest class: types', Counter((cos[c][0][0], tuple(sorted(t for _, t in cos[c]))) for c in cl[k]))
with open(D + 'semi_classes.tsv', 'w') as f:
    f.write('# coset(hex)\tclass_mod_M8(hex, 0 = member coset)\tcoset_size\n')
    for c in sorted(cos): f.write('%x\t%x\t%d\n' % (c, red(c), cos[c][0][0]))
