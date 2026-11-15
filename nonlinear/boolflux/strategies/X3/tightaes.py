#!/usr/bin/env python3
"""X3: 'tight top' test on AES prefixes, using H3's exact chain BFS (strategies/H3/chain.py).
Prefix E = all non-sink ANDs of a known circuit (U = all sinks removed).  Question: is there a chain of
exactly r = dim(outputs mod span(1,x,E)) new ANDs (operands: x, E and earlier new ANDs; chains allowed),
i.e. a circuit with |E| + r ANDs?  With r = m every new AND must lie in span(1,x,E) + T (Lemma 1 of H3).
usage: tightaes.py CIRCUIT LOG [extra U members ...]"""
import sys
from pathlib import Path
H3 = Path(__file__).resolve().parent.parent / 'H3'
sys.path.insert(0, str(H3))
import chain
from wsat import Base, mklog
b = Base(sys.argv[1]); log = mklog(sys.argv[2])
U = {k for k in range(b.K) if not b.cons[k]} | {int(t) for t in sys.argv[3:]}
U = b.closure(U)
R = [k for k in range(b.K) if k not in U]
from wsat import Span, ONES
ST = Span([ONES] + b.tab[1:1 + b.n] + [b.andtab[k] for k in R]); r = 0
for y in b.out: r += 1 if ST.add(y) else 0
rec = {'method': 'x3-tighttop', 'src': Path(sys.argv[1]).name, 'U': sorted(U), 'E': len(R), 'r': r}
print('K', b.K, '|U|', len(U), '|E|', len(R), 'r', r, 'total if SAT', len(R) + r, flush=True)
res = chain.solve_window(b, U, None, log, rec, maxstates=5000, dm=len(U) - r, target='outputs')
print(res.get('result'), {k: res[k] for k in ('enums', 'states', 'time') if k in res})
