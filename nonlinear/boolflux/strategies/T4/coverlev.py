#!/usr/bin/env python3
"""T4: distribution of stage-1 product levels over all images g(C) of the known 9-cover classes
(each product at its least level: operands = 2 lowest-weight vectors of its 2-dim space).
    python3 coverlev.py COVER_SOURCE_DIR..."""
import sys, glob, os, json
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load  # noqa
from covers import covers_of, canon, GROUP, act_key  # noqa
from coversearch import lev, wt  # noqa
files = []
for d in sys.argv[1:]:
    files += sorted(glob.glob(os.path.join(d, '*.bfx'))) + sorted(glob.glob(os.path.join(d, '*.circ.txt')))
raw = set()
for f in files:
    try: cc = load(f)
    except Exception: continue
    for cov in covers_of(cc): raw.add(cov)
classes = {}
for cov in raw: classes.setdefault(canon(cov), cov)
print('files', len(files), 'raw', len(raw), 'classes', len(classes), flush=True)
def plev(key):
    vs = sorted(key, key=lambda l: (lev(l), wt(l)))
    return 1 + max(lev(vs[0]), lev(vs[1]))
tot = Counter(); best = []
for ci, cov in enumerate(classes.values()):
    for g in GROUP:
        pl = sorted(plev(act_key(x, g)) for x in cov)
        tot[tuple(pl)] += 1
        best.append((sum(pl), max(pl), ci, g))
best.sort()
print('best (sum levels, max level, class, g):', best[:10])
for k, v in sorted(tot.items())[:15]: print(k, v)
print('covers with all products at level <= 2:', sum(v for k, v in tot.items() if max(k) <= 2))
