"""P4: exact best timing of the 18-gate inversion-block skeletons (m18 result) inside the 103.

For a skeleton (5 ANDs with operand tables over the block inputs v0..v3 = t30..t33), the block's
value set is fixed: inputs, AND outputs, the required forms (AND operands that are not inputs or ANDs,
and the 9 outputs).  In an 18-gate realisation each form is ONE XOR/XNOR of two values of the set
(cost model of invskel), so the earliest level of every value is the closure fixpoint
  level(form) = 1 + min over (a, form ^ a [or its complement]) in the set of max(levels),
  level(AND)  = 1 + max(level(L1), level(L2)),
which is exact for that value set (order-independent, as for the top layer).  The block inputs arrive
at the 103's levels of t30..t33; output products f * g then arrive at 1 + max(level f, level g), and
the best bottom timing comes from rebottom.py's exhaustive realisations.  Prints, per skeleton, the
block output levels and the best possible GD of the whole circuit with the 103's top and pre.

    python3 blocktime.py CIRC SKEL.json
"""
import json
import sys

import block
import circ
import rebottom

ONES = 0xffff
INS = ['t30', 't31', 't32', 't33']
OUTS = ['t36', 't39', 't40', 't43', 't41', 't42', 't44', 't45', 't46']


def key(t):
    return min(t, t ^ ONES)


def main():
    path, skf = sys.argv[1], sys.argv[2]
    ref = circ.read(path)
    s = circ.symbolic(ref)
    L = block.levels_of(ref)
    # block truth tables of the outputs
    tts, blk = block.block_tables(ref, INS, OUTS)
    V = [0xaaaa, 0xcccc, 0xf0f0, 0xff00]
    import os
    al = [int(t) for t in os.environ["P4_ARR"].split(",")] if os.environ.get("P4_ARR") else [L[n] for n in INS]
    arr_in = {key(V[i]): al[i] for i in range(4)}
    sk = json.load(open(skf))
    # output products: AND gates of the 103 that read a block output
    outname = {o: tt for o, tt in zip(OUTS, tts)}
    prods = []
    for op, o, ins in ref:
        if op == "AND" and sum(i in OUTS for i in ins) == 1:
            f = [i for i in ins if i in OUTS][0]
            g = [i for i in ins if i not in OUTS][0]
            prods.append((o, f, g))
    used = set()
    for op, o, ins in ref:
        if op == 'AND':
            for i in ins:
                used |= s[i][0]
    outprod = [o for op, o, ins in ref if op == 'AND' and o not in used]
    ys = [f'y{j}' for j in range(8)]
    col = {p: sum(1 << j for j, y in enumerate(ys) if p in s[y][0]) for p in outprod}
    values = sorted({c for c in col.values() if c & (c - 1)})
    units = [1 << j for j in range(8)]
    H, hsets = rebottom.min_helper_sets(values, units)
    prods_at = {}
    for p, c in col.items():
        prods_at.setdefault(c, []).append(p)
    res = []
    for r, ent in enumerate(sk):
        ands = [(l, int(x, 16), int(y, 16)) for l, x, y in ent['ands']]
        lev = dict(arr_in)
        andv = [(x & y, x, y) for l, x, y in ands]
        forms = set()
        for pv, x, y in andv:
            for t in (x, y):
                if key(t) not in arr_in and key(t) not in {key(p) for p, _, _ in andv}:
                    forms.add(key(t))
        for t in tts:
            forms.add(key(t))
        vals = set(arr_in) | {key(p) for p, _, _ in andv} | forms
        INF = 99
        for v in vals:
            lev.setdefault(v, INF)
        lev[key(0)] = 0
        changed = True
        while changed:
            changed = False
            for pv, x, y in andv:
                l = 1 + max(lev.get(key(x), INF), lev.get(key(y), INF))
                if l < lev[key(pv)]:
                    lev[key(pv)] = l
                    changed = True
            for f in forms:
                if f in arr_in:
                    continue
                best = lev[f]
                for a in vals:
                    if a == f or lev[a] >= INF:
                        continue
                    b = key(f ^ a)
                    if b in vals and b != f and lev[b] < INF:
                        best = min(best, 1 + max(lev[a], lev[b]))
                if best < lev[f]:
                    lev[f] = best
                    changed = True
        out_lev = {o: lev[key(outname[o])] for o in OUTS}
        arr = {}
        for o, f, g in prods:
            arr[o] = 1 + max(out_lev[f], L[g])
        best = None
        for hs in hsets:
            Vv = values + list(hs)
            for dep in rebottom.realisations(Vv, units):
                g, outl = rebottom.build(dep, Vv, units, prods_at, arr, ys, None)
                k = (max(outl), sum(outl))
                if best is None or k < best[0]:
                    best = (k, outl)
        rec = dict(rank=r, block_out_levels=out_lev, best_GD=best[0][0], out_levels=best[1])
        res.append(rec)
        print(json.dumps(rec), flush=True)
    print(json.dumps(dict(best_GD_over_skeletons=min(x['best_GD'] for x in res))))


if __name__ == '__main__':
    main()
