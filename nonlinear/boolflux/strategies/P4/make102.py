"""P4: build 102-gate candidates = 17-gate top (forms + 2 helpers) + the 103's pre-inversion
product-part chain re-injected from the new top values + the 103's inversion and bottom.

    python3 make102.py CIRC OUTDIR [--helpers 18,33] [--k 5] [--limit 2000]
Writes the best (lowest GD) verified circuit per helper set to OUTDIR and prints a JSON summary.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import build
import circ
import reinject
import topenum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('out')
    ap.add_argument('--helpers', default=None, help='comma list of helper masks; default: all 17 two-helper sets')
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--limit', type=int, default=5000)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ref = circ.read(a.circ)
    s = circ.symbolic(ref)
    xs = {f'x{i}' for i in range(8)}
    xm = lambda atoms: sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')
    topn = [o for op, o, ins in ref if op != 'AND' and s[o][0] <= xs]
    forms = {}
    for op, o, ins in ref:
        if op == 'AND':
            for i in ins:
                if s[i][0] <= xs and len(s[i][0]) > 1:
                    forms[xm(s[i][0])] = i
    prod = [f'a{i}' for i in range(1, 10)]
    targets = ['t30', 't31', 't32', 't33']
    achain, P, X = build.pre_extract(ref, s, targets, prod)
    pre_names = [o for op, o, ins in ref if op != 'AND' and o not in topn and s[o][0] <= xs | set(prod)]
    if a.helpers:
        hsets = [tuple(int(t) for t in a.helpers.split(','))]
    else:
        F = set(forms)
        allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
        hsets = []
        for hs in itertools.combinations(allv, 2):
            S = F | set(hs)
            lv = topenum.closure_levels(S)
            if all(t in lv for t in S):
                hsets.append(hs)
    summary = []
    for hs in hsets:
        S = set(forms) | set(hs)
        tg, vn, lvl = build.top_gates(S, dict(forms))
        avail = set(vn)
        sols, byr = reinject.solutions(achain, 9, P, X, avail, a.k, limit=a.limit)
        best = None
        tried = 0
        for B, Sv in sols:
            # every assignment of concrete points to the reach vectors in B
            choices = [byr[r] for r in B]
            for pts in itertools.product(*choices):
                if len(set(pts)) < len(pts):
                    continue
                tried += 1
                inj = list(zip(pts, Sv))
                try:
                    pg = build.pre_gates(achain, 9, P, targets, inj, vn, prod, None)
                except RuntimeError:
                    continue
                g = build.assemble(ref, tg, pg, set(topn) | set(pre_names))
                g = build.set_constants(g, s, set(targets))
                if not circ.correct(g):
                    continue
                m = circ.metrics(g)
                if best is None or (m[2], m[3]) < (best[0][2], best[0][3]):
                    best = (m, g, inj)
                if tried > 20000:
                    break
            if tried > 20000:
                break
        rec = dict(helpers=[build.nm(h) for h in hs], solutions=len(sols), tried=tried,
                   best=best[0] if best else None)
        if best:
            fn = out / f'p4-102-{"-".join(map(str, hs))}-g{best[0][2]}-gd{best[0][3]}.circ.txt'
            circ.write(fn, best[1], fn.stem, comment=[f'P4 make102 helpers {rec["helpers"]} from {a.circ}'])
            rec['file'] = str(fn)
        summary.append(rec)
        print(json.dumps(rec), flush=True)


if __name__ == '__main__':
    main()
