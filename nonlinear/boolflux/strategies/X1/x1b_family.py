#!/usr/bin/env python3
"""X1b: AND-structure classification of circuits (A <= 54).

For each circuit: metrics, AND-level profile, and three invariants of its AND structure:
  span   = span{1, x, all AND tables}  (canonical reduced echelon basis -> hash).  Flips / redec keep it
           [C, X1 NOTES 1]; a different span means the circuit is NOT a re-bracketing of the other one's
           products.
  span_L = the same restricted to ANDs of level <= L (per level, hashed; prefix structure).
  mset   = H3 families.py key: the multiset of AND tables reduced mod span{1, x} (finest; flips change it).
and, for each reference circuit, dim(span_i cap span_ref) - 9 (number of shared product dimensions,
0..A).  Groups circuits by span.

    python3 x1b_family.py [--ref FILE]... [--json OUT.json] FILE...
"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X
from boolflux.hub.common import load, metrics
from boolflux import core

ONES = (1 << 256) - 1
AFF = [ONES] + core.input_tables(8)


class Sp:
    def __init__(self, vs=()):
        self.piv = {}
        for v in vs: self.add(v)

    def red(self, t):
        while t:
            h = t.bit_length() - 1
            if h in self.piv: t ^= self.piv[h]
            else: return t
        return 0

    def add(self, t):
        t = self.red(t)
        if t: self.piv[t.bit_length() - 1] = t; return True
        return False

    @property
    def dim(self): return len(self.piv)

    def canon(self):
        # fully reduced echelon form -> canonical
        ks = sorted(self.piv, reverse=True)
        rows = dict(self.piv)
        for k in ks:
            for k2 in ks:
                if k2 != k and (rows[k2] >> k) & 1: rows[k2] ^= rows[k]
        return hashlib.sha1(b''.join(rows[k].to_bytes(32, 'big') for k in sorted(rows))).hexdigest()[:12]


def analyse(f):
    r = analyse_c(load(f)); r['file'] = str(f); r['name'] = Path(f).name
    return r


def analyse_c(c):
    m = metrics(c)
    p = X.extract(c); T, _ = p.tables(); lv = p.and_levels()
    prof = {}
    for k, l in lv.items(): prof[l] = prof.get(l, 0) + 1
    tabs = [T[k] for k in p.ands]
    s = Sp(AFF + tabs)
    perL = []
    for L in sorted(prof):
        perL.append(Sp(AFF + [T[k] for k in p.ands if lv[k] <= L]).canon())
    aff = Sp(AFF)
    mset = hashlib.sha1(repr(sorted(aff.red(t) for t in tabs)).encode()).hexdigest()[:12]
    return {'m': m, 'levels': '|'.join(str(prof[l]) for l in sorted(prof)),
            'A_eff': s.dim - 9, 'span': s.canon(), 'span_L': perL, 'mset': mset, '_sp': s, '_tabs': tabs}


def inter(a, b):
    u = Sp(list(a['_sp'].piv.values()))
    for v in b['_sp'].piv.values(): u.add(v)
    return a['_sp'].dim + b['_sp'].dim - u.dim - 9


def main():
    a = sys.argv[1:]
    refs, files, out = [], [], None
    i = 0
    while i < len(a):
        if a[i] == '--ref': refs.append(a[i + 1]); i += 2
        elif a[i] == '--json': out = a[i + 1]; i += 2
        else: files.append(a[i]); i += 1
    R = [analyse(f) for f in refs]
    rows = []
    for f in files:
        try: r = analyse(f)
        except Exception as e: print('skip', f, e); continue
        r['inter'] = [inter(r, q) for q in R]
        rows.append(r)
    for k, q in enumerate(R):
        print('ref %d %s %s levels %s span %s' % (k, q['name'], q['m'], q['levels'], q['span']))
    groups = {}
    for r in rows: groups.setdefault(r['span'], []).append(r)
    refspan = {q['span']: k for k, q in enumerate(R)}
    print('%d circuits, %d distinct product spans, %d distinct product multisets' % (len(rows), len(groups), len({r['mset'] for r in rows})))
    for sp, g in sorted(groups.items(), key=lambda kv: min(r['m'] for r in kv[1])):
        best = min(g, key=lambda r: r['m'])
        tag = (' = ref %d' % refspan[sp]) if sp in refspan else ''
        print('span %s%s: %d circuits, best %s levels %s A_eff %d, shared dims with refs %s, level-prefix spans %s' % (
            sp, tag, len(g), best['m'], best['levels'], best['A_eff'], best['inter'], best['span_L']))
        for r in sorted(g, key=lambda r: r['m'])[:3]: print('     ', r['name'], r['m'], r['levels'])
    if out:
        Path(out).write_text(json.dumps([{k: v for k, v in r.items() if not k.startswith('_')} for r in rows], indent=0))


if __name__ == '__main__':
    main()
