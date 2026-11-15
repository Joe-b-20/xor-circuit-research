#!/usr/bin/env python3
"""Survey an archive: which circuits have a table dependency among products (dep), or a pair of ANDs with
equal usage sharing a factor (merge).   python3 t_survey.py CAMPAIGN_DIR [front|cells|all]"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X
from boolflux.hub.common import metrics, sbox
from boolflux.hub.archive import Archive
from boolflux import core

ar = Archive(sys.argv[1]); which = sys.argv[2] if len(sys.argv) > 2 else 'front'
if which == 'front': ids = ar.front_ids()
elif which == 'cells': ids = [i for v in ar.cells.values() for i in v[:1]]
else: ids = list(ar.rec)
nd = nm = 0; tot = 0
for i in ids:
    c = ar.circuit(i); m = metrics(c)
    p = X.extract(c); a0 = p.A
    dead = p.remove_dead(); dep = p.remove_dependent()
    u = p.usage(); groups = {}
    for k, s in u.items(): groups.setdefault(s, []).append(k)
    sp = {k: set(X.Prog.span3(*p.ands[k])) for k in p.ands}
    mg = [(a, b) for g in groups.values() if len(g) > 1 for a in g for b in g if a < b and sp[a] & sp[b]]
    ks = sorted(p.ands)
    share = sum(1 for x in range(len(ks)) for y in range(x + 1, len(ks)) if sp[ks[x]] & sp[ks[y]])
    tot += 1
    if dep or mg or dead:
        nd += bool(dep); nm += bool(mg)
        print(i, m, 'dead', dead, 'dep', dep, 'merge pairs', len(mg), 'sharing', share, flush=True)
print('surveyed', tot, 'with dep', nd, 'with merge', nm)
