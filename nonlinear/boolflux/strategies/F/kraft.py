#!/usr/bin/env python3
"""Skeleton-level Kraft analysis for a gate-depth cap D (track F).

For a form with terms of arrival levels a_i, an XOR tree of depth <= d exists iff
sum 2^(a_i - d) <= 1 (plus one level if the form is a lone term with a constant).
ASAP arrivals come from skeldepth.bound; required levels are propagated backwards
(ALAP) from the outputs at D.  Prints every form whose Kraft sum at its required level
exceeds 1 (the places that must change for cap D), with its terms grouped by kind.

    python3 kraft.py FILE --cap D
"""
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core, skeleton   # noqa: E402
from skeldepth import huff, terms      # noqa: E402


def analyse(c, D):
    sk = skeleton.extract(c); ands = sk['ands']; outf = sk['outputs']
    n = c.n; nb = 1 + n + len(ands)
    arr = [0] * nb; adl = [0] * nb
    for k, (L, R) in enumerate(ands):
        tl, cl = terms(L, nb); tr, cr = terms(R, nb)
        arr[1 + n + k] = 1 + max(huff([arr[p] for p in tl], cl), huff([arr[p] for p in tr], cr))
        adl[1 + n + k] = 1 + max([adl[p] for p in tl + tr] or [0])
    name = lambda p: ('x%d' % (p - 1)) if p <= n else ('a%d(L%d,AD%d)' % (p - n, arr[p], adl[p]))
    forms = []   # (label, form, required)
    for j, f in enumerate(outf): forms.append(('S%d' % j, f, D))
    # backward required levels for ANDs: req(and) = min over forms containing it of (req(form) - depth needed)
    # simple version: required of AND k = min over consumers ... computed iteratively from Kraft-free bound:
    # a term with arrival a in a form required at r needs a <= r - 1 (if form has >1 term)
    req = [10 ** 9] * nb
    def push(f, r):
        t, cst = terms(f, nb)
        for p in t:
            rr = r - (1 if (len(t) > 1 or cst) else 0)
            req[p] = min(req[p], rr)
    for lab, f, r in forms: push(f, r)
    for k in range(len(ands) - 1, -1, -1):
        p = 1 + n + k
        if req[p] < 10 ** 9:
            for f in ands[k]: push(f, req[p] - 1)
    rows = []
    allforms = [(lab, f, r) for lab, f, r in forms]
    for k, (L, R) in enumerate(ands):
        p = 1 + n + k
        allforms.append(('a%d.L' % (k + 1), L, req[p] - 1)); allforms.append(('a%d.R' % (k + 1), R, req[p] - 1))
    for lab, f, r in allforms:
        t, cst = terms(f, nb)
        if not t: continue
        ks = sum(Fraction(2) ** (arr[p] - r) for p in t)
        need = huff([arr[p] for p in t], cst)
        if need > r:
            rows.append((lab, r, need, ks, sorted(((arr[p], name(p)) for p in t), reverse=True)))
    return arr, rows


if __name__ == '__main__':
    args = sys.argv[1:]; D = int(args[args.index('--cap') + 1]); f = args[0]
    c = core.read_ncff(f)
    arr, rows = analyse(c, D)
    print('%s: %d forms cannot meet cap %d with the present skeleton' % (Path(f).name, len(rows), D))
    for lab, r, need, ks, ts in rows:
        print('  %-7s required %2d, best %2d, Kraft %.3f, %d terms: %s' % (lab, r, need, float(ks), len(ts), ' '.join('%s' % nm for a, nm in ts)))
