#!/usr/bin/env python3
"""Structure of a circuit for window selection: levels, consumers, closures and their output rank."""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wsat import Base  # noqa: E402

for path in sys.argv[1:]:
    b = Base(path)
    print('==', Path(path).name, 'K', b.K)
    prof = {}
    for lv in b.level: prof[lv] = prof.get(lv, 0) + 1
    print('levels', '|'.join(str(prof[k]) for k in sorted(prof)))
    sinks = [k for k in range(b.K) if not b.cons[k]]
    print('sinks (no AND consumer):', len(sinks), 'rank of all sinks:', b.rank_mod(set(sinks)))
    for j in range(b.K):
        U = b.closure({j})
        print('  g%-2d lv%d cons %-14s closure %2d rank %d slack %d' % (
            j, b.level[j], sorted(b.cons[j]), len(U), b.rank_mod(U), len(U) - b.rank_mod(U)))
    # minimal dependent subsets of sinks (slack >= 1) up to size 9
    cnt = {}
    found = []
    for s in range(2, 10):
        c = 0
        for S in itertools.combinations(sinks, s):
            if any(set(f) <= set(S) for f in found): continue
            if b.rank_mod(set(S)) < s:
                found.append(S); c += 1
        cnt[s] = c
        if s >= 6 and sum(cnt.values()) > 200: break
    print('minimal dependent sink sets by size:', cnt)
    for S in found[:20]: print('   ', S, [b.level[k] for k in S])
