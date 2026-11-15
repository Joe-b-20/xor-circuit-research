"""X3 s1planes.py CIRCUIT...: operand planes of the level-1 ANDs (rank-2 quadratics l1*l2): ratio class of A1/A2
(Q: GF(4)-line, K: inside a K-line, F: other), and how many semi-members / members have exactly that x-plane
(their x-junk is then that stage-1 product itself, modulo affine)."""
import sys, os
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'H3'))
from wsat import Base
from gfinv import gmul, gpow
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
def tr(z):
    s = 0
    for _ in range(8): s ^= z; z = gmul(z, z, 8)
    return s & 1
A_of = {sum(tr(gmul(A, 1 << i, 8)) << i for i in range(8)): A for A in range(256)}
Kset = {gpow(x, 17, 8) for x in range(256)}; Q = {x for x in Kset if gpow(x, 4, 8) == x}
def cls(r): return 'Q' if r in Q else ('K' if r in Kset else 'F')
planes = Counter()
for ln in open(D + 'semi_members.tsv'):
    if ln[0] == '#': continue
    p = ln.split('\t'); a1, a2 = int(p[3], 16), int(p[4], 16)
    planes[(frozenset((a1, a2, a1 ^ a2)), p[2] == '5')] += 1
for path in sys.argv[1:]:
    b = Base(path); out = []
    # which input ordering: recover x-forms from tables: table of form u is parity(u & x) if b.tab[1+i] is bit i or 7-i
    xt = b.tab[1:9]
    def form_of(tab):   # linear form table -> mask u over integer bits
        u = 0
        for i in range(8):
            if (tab >> (1 << i)) & 1: u |= 1 << i
        return u
    for k in range(b.K):
        if b.level[k] != 1: continue
        f = b.andtab[k]; f0 = f & 1
        fs = set()
        for i in range(8):
            e = 1 << i
            # B(x, e) = f(x+e) + f(x) + f(e) + f(0)
            t = 0
            for x in range(256):
                v = ((f >> (x ^ e)) ^ (f >> x) ^ (f >> e) ^ f0) & 1
                t |= v << x
            if t: fs.add(form_of(t))
        fs.discard(0)
        fs |= {a ^ c for a in fs for c in fs if a != c}
        if len(fs) != 3: out.append((k, 'rank != 2')); continue
        As = sorted(A_of[u] for u in fs)
        c = cls(gmul(As[0], gpow(As[1], 254, 8), 8)); key = frozenset(As)
        out.append((k, c, planes.get((key, True), 0), planes.get((key, False), 0)))
    print(Path(path).name)
    print('   level-1 ANDs: (index, plane class, members with this x-plane, semi-members with this x-plane)')
    print('  ', out)
    print('   classes:', Counter(o[1] for o in out))
