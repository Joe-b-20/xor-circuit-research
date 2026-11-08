#!/usr/bin/env python3
"""qcert2 smoke test of gen_certs2: row counts, known killed / surviving keys, timing of one certificate tree."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'xs-campaigns/2026-11-07-sprint/qcert2'))
import gen_certs2 as g

for key in [(12, 5, 5, 'M', 2, 3), (10, 6, 6, 'M', 6, 0), (11, 5, 5, 'Mt', 5, 0), (19, 0, 0, 'Mt', 1, 5), (12, 4, 4, 'Mt', 5, 1)]:
    h, y, F, ori, q, z = key
    for hub, dark in [(None, None), (('eq', 5) if q >= 5 else None, 2 if q >= 2 else 0), (('le', 4) if q >= 5 else None, None)]:
        types, aux, A, B, names, n_pkg, n_b1 = g.ext_system(key, hub, dark)
        print(key, hub, dark, 'types', len(types), 'aux', aux, 'rows', len(A), 'pkg', n_pkg, 'b1', n_b1, 'case rows', len(A) - n_pkg - n_b1)
    t0 = time.time()
    fb = g.feasible_b1(key); ff = g.feasible_full(key)
    t1 = time.time()
    print('   feasible batch-1', fb, 'full', ff, f'{t1-t0:.2f}s; hub cases', g.hub_cases(q), 'dark cases', len(g.dark_cases(q)))
    if fb and not ff:
        kind, certs, problem = g.certify_key(key)
        print('   certify_key:', kind, 'certs', len(certs), 'problem', problem, f'{time.time()-t1:.2f}s',
              'cases:', [(hub, dark) for hub, dark, ints in certs][:12], 'max rhs', max(sum(w * b for w, b in zip(ints, g.ext_system(key, hub, dark)[3])) for hub, dark, ints in certs))
print('names of a dark case system (Mt, q=5, d=2):')
types, aux, A, B, names, n_pkg, n_b1 = g.ext_system((11, 5, 5, 'Mt', 5, 0), ('eq', 5), 2)
for n, b in zip(names[n_pkg:], B[n_pkg:]): print('  ', n, '<=', b)
