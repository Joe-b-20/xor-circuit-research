#!/usr/bin/env python3
"""Group circuits by AND structure: two circuits whose windows are the same problem have the same
set of AND functions modulo span(1, x) step by step; we compare (a) the span of all AND tables with
1, x and (b) the multiset of AND tables up to adding affine functions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from wsat import Base, Span, ONES

groups = {}
for p in sys.argv[1:]:
    try: b = Base(p)
    except Exception as e:
        print('skip', p, e); continue
    aff = Span([ONES] + b.tab[1:1 + b.n])
    key = tuple(sorted(aff.reduce(t) for t in b.andtab))
    prof = {}
    for lv in b.level: prof[lv] = prof.get(lv, 0) + 1
    groups.setdefault(key, []).append((Path(p).name, '|'.join(str(prof[k]) for k in sorted(prof))))
for i, (k, v) in enumerate(groups.items()):
    print('family %d (%d ANDs):' % (i, len(k)))
    for name, prof in v: print('   ', name, prof)
