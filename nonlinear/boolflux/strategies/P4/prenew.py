"""P4: exact pre-inversion over a NEW top layer (forms + given helpers), by SAT (linslp2), then
splice: new top + new pre + the reference's inversion and bottom; verify on all 256 inputs.

    python3 prenew.py CIRC OUT.circ.txt --helpers 18,33 --steps 15 [--gd 32] [--budget N]
With --gd, gate levels are constrained: base arrivals = levels in the new top / reference ANDs
(level-1 ANDs re-timed on the new top), target deadlines = required times of t30..t33 in the
reference at that GD.
"""
import argparse
import json
import sys

import block
import build
import circ
import linslp2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('out')
    ap.add_argument('--helpers', required=True)
    ap.add_argument('--steps', type=int, default=15)
    ap.add_argument('--gd', type=int, default=None)
    ap.add_argument('--budget', type=int, default=None)
    a = ap.parse_args()
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
    hs = [int(t) for t in a.helpers.split(',')]
    S = set(forms) | set(hs)
    tg, vn, lvl = build.top_gates(S, dict(forms))
    prod = [f'a{i}' for i in range(1, 10)]
    targets = ['t30', 't31', 't32', 't33']
    pre_names = [o for op, o, ins in ref if op != 'AND' and o not in topn and s[o][0] <= xs | set(prod)]
    # vectors: bits 0..8 = a1..a9, bits 9..16 = x0..x7
    vec = lambda atoms: sum(1 << prod.index(t) for t in atoms if t in prod) | (xm(atoms) << 9)
    base, bnames = [], []
    for i, p in enumerate(prod):
        base.append(1 << i)
        bnames.append(p)
    for v, n in vn.items():
        base.append(v << 9)
        bnames.append(n)
    T = [vec(s[t][0]) for t in targets]
    arr = dl = None
    if a.gd:
        # levels: new top levels; level-1 ANDs = 1 + max operand level in the new top
        L = {n: lvl[v] for v, n in vn.items()}
        for op, o, ins in ref:
            if o in prod:
                L[o] = 1 + max(L[i] for i in ins)
        arr = [L[n] for n in bnames]
        req = block.required([g for g in ref if g[1] not in set(topn) | set(pre_names)], a.gd)
        dl = [req[t] for t in targets]
        print('arrivals', dict(zip(bnames, arr)), 'deadlines', dl, file=sys.stderr)
    st, ch, el = linslp2.slp(17, base, T, a.steps, budget=a.budget, arrivals=arr, deadlines=dl)
    info = dict(status=st, steps=a.steps, helpers=[build.nm(h) for h in hs], elapsed=round(el, 1), gd=a.gd)
    if st == 'sat':
        vals = linslp2.values(base, ch)
        names = list(bnames)
        pg = []
        for k, (j, kk) in enumerate(ch):
            pg.append(['XOR', f'q{k + 1}', (names[j], names[kk])])
            names.append(f'q{k + 1}')
        ren = {}
        for t, tv in zip(targets, T):
            i = vals.index(tv, len(base))
            ren[names[i]] = t
        pg = [[op, ren.get(o, o), tuple(ren.get(i, i) for i in ins)] for op, o, ins in pg]
        g = build.assemble(ref, tg, pg, set(topn) | set(pre_names))
        g = build.set_constants(g, s, set(targets))
        ok = circ.correct(g)
        info['correct'] = ok
        info['metrics'] = circ.metrics(g)
        if ok:
            circ.write(a.out, g, 'p4-prenew', comment=[f'P4 prenew helpers {info["helpers"]} steps {a.steps} from {a.circ}'])
            info['file'] = a.out
    print(json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
