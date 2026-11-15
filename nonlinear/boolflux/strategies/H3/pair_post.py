#!/usr/bin/env python3
"""Post-process split r1enum runs of a slack-1 window with m = 1 (dependent pair U -> 1 AND).
Every hit a gives b with a*b in W + T \\ W; T is 1-dim, so a*b is the missing class: build the circuit
(kept ANDs + the new AND), aes_check it.  Usage: pair_post.py CIRCUIT "i,j" OUT1 [OUT2 ...]"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chain  # noqa: E402
from wsat import Base, Span, ONES, finish, save_circuit  # noqa: E402

b = Base(sys.argv[1]); U = {int(t) for t in sys.argv[2].split(',')}
hits = []
for f in sys.argv[3:]:
    for ln in open(f):
        if ln.startswith('H '): hits.append(int(ln.split()[1], 16))
        if ln.startswith('DONE'): print(f, ln.strip())
print('hits', len(hits))
if not hits: sys.exit(0)
n = b.n
R = [k for k in range(b.K) if k not in U]
W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
Trep = []; ST = Span(W)
for y in b.out:
    if ST.add(y): Trep.append(y)
HT = chain.checks_of(W + Trep); comp = chain.comp_checks(W, Trep)
Vb = b.tab[1:1 + n] + [b.andtab[k] for k in R]
GH = [chain.Gmat(h, Vb) for h in HT]; GC = [chain.Gmat(h, Vb) for h in comp]
for a in hits[:5]:
    kb = chain.kernel([chain.evalrow(G, a) for G in GH], len(Vb))
    for bv in kb:
        if sum(chain.par(chain.evalrow(G, a) & bv) << c for c, G in enumerate(GC)):
            wits = [(chain.vtab(a, Vb) & chain.vtab(bv, Vb), a, bv, len(Vb))]
            rec = {'src': Path(sys.argv[1]).name, 'U': sorted(U), 'tag': 'pair-%s' % '-'.join(map(str, sorted(U)))}
            chain.build(b, R, R, wits, rec, lambda r: None, 1, 0.0, 1)
            pr = subprocess.run([sys.executable, str(HERE.parents[1] / 'campaigns' / 'aes_check.py'), rec['file']],
                                capture_output=True, text=True)
            print(rec, pr.stdout[:300])
            sys.exit(0)
