"""Splice an inversion-block skeleton (from invskel.py) into a base NCFF circuit (track P5).

The base circuit's middle gates (--middle names) are removed; the block is rebuilt from the
skeleton: ANDs in order, each operand / target affine form built with XOR/XNOR gates from
available signals (one gate when the form is the sum of two available signals, else a short
chain).  Bottom references to the targets are renamed to the new signals.  Writes NCFF.

usage: python3 blocksplice.py BASE.circ.txt SPEC.json SKEL.json --rank I --middle a10,t34,...
          --ins t30,t31,t32,t33 --out OUT.circ.txt
"""
import argparse, json, sys
from itertools import combinations
from pathlib import Path

ONES = 0xffff


def parse(path):
    txt = Path(path).read_text()
    body = txt.split('begin SLP')[1].split('end SLP')[0]
    lines = []
    for line in body.splitlines():
        line = line.split('%')[0].strip()
        if not line: continue
        p = line.split()
        lines.append((p[0], p[1], p[2:]))
    return lines


def build_block(V, ins, ands, targets, tnames, bound=(), U=(), paid=()):
    """Staged build (same rule as invskel.closure_cost): stage l emits the ANDs of level l, then
    builds every pending form allowed at level >= l from signals of level <= l, one XOR/XNOR
    each while possible; forms due at stage l that are still missing get a short chain."""
    avail = {}; lev = {}
    for t, nm in zip(V, ins):
        if t not in paid: avail[t] = nm; lev[t] = 0
    btab = {}
    for t, op, x, y in bound: btab[t] = ('XOR', x, y); btab[t ^ ONES] = ('XNOR', x, y)
    out = []; cnt = [0]
    D = max([l for l, x, y in ands] + [0])

    def new(op, a, b, t, l):
        cnt[0] += 1; nm = 'b%d' % cnt[0]
        out.append((op, nm, [a, b])); avail[t] = nm; lev[t] = l; return nm

    def al_at(st):
        return [(g, gn) for g, gn in avail.items() if lev[g] <= st]

    def try1(f, st):
        if f in avail: return True
        if f in btab:
            op, x, y = btab[f]; new(op, x, y, f, 0); return True
        al = al_at(st); d = {g: gn for g, gn in al}
        for g, gn in al:
            h = f ^ g
            if h in d and h != g: new('XOR', gn, d[h], f, st); return True
            h = f ^ g ^ ONES
            if h in d and h != g: new('XNOR', gn, d[h], f, st); return True
        return False

    def chain(f, st):
        al = al_at(st)
        rows = []
        for g, gn in al:
            v, comb = g, {g}
            for rv, rc in rows:
                if v ^ rv < v: v ^= rv; comb = comb ^ rc
            if v: rows.append((v, comb)); rows.sort(reverse=True)
        for target, cmp in ((f, False), (f ^ ONES, True)):
            v, comb = target, set()
            for rv, rc in rows:
                if v ^ rv < v: v ^= rv; comb = comb ^ rc
            if v == 0 and comb:
                terms = sorted(comb)
                acc = terms[0]
                for i, t in enumerate(terms[1:]):
                    last = (i == len(terms) - 2)
                    nt = acc ^ t ^ (ONES if (last and cmp) else 0)
                    if nt not in avail:
                        new('XNOR' if (last and cmp) else 'XOR', avail[acc], avail[t], nt, st)
                    acc = nt
                return True
        raise RuntimeError('form %x not in span at stage %d' % (f, st))

    for u in U:
        if u not in avail:
            op, x, y = btab[u]; new(op, x, y, u, 0)
    flev = {}
    for l, x, y in ands:
        for L in (x, y): flev[L] = min(flev.get(L, D), l - 1)
    for t in targets: flev.setdefault(t, D)
    Dall = max(D, max(flev.values()))
    for st in range(0, Dall + 1):
        for l, x, y in ands:
            if l == st:
                new('AND', avail[x], avail[y], x & y, st)
        changed = True
        while changed:
            changed = False
            for f in [f for f, l in flev.items() if l >= st and f not in avail]:
                if try1(f, st): changed = True
        for f in [f for f, l in flev.items() if l == st and f not in avail]:
            chain(f, st)
    names = {nm: avail[t] for nm, t in zip(tnames, targets)}
    return out, names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base'); ap.add_argument('spec'); ap.add_argument('skel')
    ap.add_argument('--rank', type=int, default=0)
    ap.add_argument('--middle', required=True); ap.add_argument('--ins', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    global ONES
    ONES = (1 << (1 << spec["k"])) - 1
    V = [int(i['table'], 16) for i in spec['inputs']]
    tg = [int(t['table'], 16) for t in spec['targets']]
    tn = [t['name'] for t in spec['targets']]
    sk = json.load(open(a.skel))[a.rank]
    ands = [(l, int(x, 16), int(y, 16)) for l, x, y in sk['ands']]
    ins = a.ins.split(',')
    mid = set(a.middle.split(','))
    bound = [(int(b['table'], 16), b.get('op', 'XOR'), b['a'], b['b']) for b in spec.get('boundary', [])]
    paid = {int(i['table'], 16) for i in spec['inputs'] if i.get('paid')}
    best = None
    for msk in range(1 << len(bound)):
        U = [bound[i][0] for i in range(len(bound)) if msk >> i & 1]
        try:
            r = build_block(V, ins, ands, tg, tn, bound, U, paid)
        except RuntimeError:
            continue
        if best is None or len(r[0]) < len(best[0]): best = r
    blk, ren = best
    base = parse(a.base)
    res = []; done = False
    for op, o, args in base:
        if o in mid:
            if not done: res.extend(blk); done = True
            continue
        res.append((op, o, [ren.get(x, x) for x in args]))
    # rename outputs if a target is an output (not expected)
    nA = sum(1 for g in res if g[0] == 'AND')
    lines = ['begin circuit spliced', 'Inputs: x0:x7', 'Outputs: y0:y7',
             'Internal: ' + ' '.join(g[1] for g in res if not g[1].startswith('y')),
             'GateSyntax: GateName Output Inputs', 'begin SLP']
    lines += ['%s %s %s' % (op, o, ' '.join(args)) for op, o, args in res]
    lines += ['end SLP', 'end circuit']
    Path(a.out).write_text('\n'.join(lines) + '\n')
    print('block gates %d (AND %d), total gates %d, AND %d' %
          (len(blk), sum(1 for g in blk if g[0] == 'AND'), len(res), nA))
    return 0


if __name__ == '__main__':
    sys.exit(main())
