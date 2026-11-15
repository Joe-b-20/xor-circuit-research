#!/usr/bin/env python3
"""Static survey: product program of each circuit, dependencies, usage-column rank, shared factors,
round trip through materialise.   python3 t_static.py FILE..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X
from boolflux.hub.common import load, metrics, sbox, verify
from boolflux import core

TARGET = core.tables_from_values(8, 8, list(sbox()))


def colrank(p):
    forms = list(p.forms()); ks = sorted(p.ands)
    cols = []
    for k in ks:
        v = 0
        for idx, f in enumerate(forms):
            if (f >> k) & 1: v |= 1 << idx
        cols.append(v)
    piv = []; r = 0
    for v in cols:
        for pp, pv in piv:
            if (v >> pp) & 1: v ^= pv
        if v: piv.append((v.bit_length() - 1, v)); r += 1
    return r


def survey(f):
    c = load(f); m0 = metrics(c)
    p = X.extract(c)
    assert X.check(p, TARGET)
    a0 = p.A
    red = p.reduce()
    u = p.usage()
    groups = {}
    for k, s in u.items(): groups.setdefault(s, []).append(k)
    eq = [g for g in groups.values() if len(g) > 1]
    sp = {k: set(X.Prog.span3(*p.ands[k])) for k in p.ands}
    ks = sorted(p.ands)
    share = sum(1 for x in range(len(ks)) for y in range(x + 1, len(ks)) if sp[ks[x]] & sp[ks[y]])
    eqshare = [(i, j) for g in eq for i in g for j in g if i < j and sp[i] & sp[j]]
    lv = p.and_levels(); prof = {}
    for k, l in lv.items(): prof[l] = prof.get(l, 0) + 1
    c2 = X.materialise(p)
    ok = tuple(c2.value_table()) == sbox()
    print('%s  %s  A %d dep/dead-removed %d  usage-col rank %d/%d  equal-usage groups %s  factor-sharing pairs %d  mergeable %s  levels %s  rebuilt %s ok=%s'
          % (Path(f).name[:44], m0, a0, red, colrank(p), p.A, [len(g) for g in eq], share, eqshare,
             '|'.join(str(prof[l]) for l in sorted(prof)), metrics(c2), ok))
    return p


if __name__ == '__main__':
    for f in sys.argv[1:]:
        survey(f)
