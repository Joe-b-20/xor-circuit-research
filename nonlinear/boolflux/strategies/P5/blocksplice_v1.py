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


def build_block(V, ins, ands, targets, tnames):
    """V: input tables, ins: input names; ands: [(lev, L1, L2)]; returns gate lines and name map."""
    avail = {}                         # table -> (name, complemented?)  (exact tables only)
    for t, nm in zip(V, ins): avail[t] = nm
    out = []; cnt = [0]

    def new(op, a, b, t):
        cnt[0] += 1; nm = 'b%d' % cnt[0]
        out.append((op, nm, [a, b])); avail[t] = nm; return nm

    def try1(f):
        if f in avail: return True
        al = list(avail.items())
        for i, (g, gn) in enumerate(al):
            for h, hn in al[i + 1:]:
                if g ^ h == f: new('XOR', gn, hn, f); return True
                if g ^ h ^ ONES == f: new('XNOR', gn, hn, f); return True
        return False

    def tryn(f):
        """any length: Gaussian elimination over available signals + constant."""
        if try1(f): return True
        al = list(avail.items())
        # find g with f^g one-gate reachable (2 gates total)
        for g, gn in al:
            for h, hn in al:
                if h == g: continue
                for k, kn in al:
                    if k in (g, h): continue
                    if g ^ h ^ k in (f, f ^ ONES):
                        x = new('XOR', gn, hn, g ^ h)
                        if g ^ h ^ k == f: new('XOR', x, kn, f)
                        else: new('XNOR', x, kn, f)
                        return True
        # general: Gaussian elimination, then an XOR chain over the chosen signals
        rows = []                                   # (vector, set of table keys)
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
                acc, accn = terms[0], avail[terms[0]]
                for i, t in enumerate(terms[1:]):
                    last = (i == len(terms) - 2)
                    nt = acc ^ t ^ (ONES if (last and cmp) else 0)
                    accn = new('XNOR' if (last and cmp) else 'XOR', accn, avail[t], nt) \
                        if nt not in avail else avail[nt]
                    acc = nt
                return True
        return False

    pend = list(ands)
    need_t = list(targets)
    while pend:
        lev, L1, L2 = pend[0]
        if L1 in avail and L2 in avail:
            new('AND', avail[L1], avail[L2], L1 & L2); pend.pop(0); continue
        progressed = False
        for L in (L1, L2):
            if L not in avail and try1(L): progressed = True; break
        if not progressed:
            for L in (L1, L2):
                if L not in avail and tryn(L): progressed = True; break
        if not progressed: raise RuntimeError('cannot build operand %04x' % L)
    # targets: one-gate ones first, repeatedly
    rem = list(need_t)
    while rem:
        prog = False
        for f in list(rem):
            if try1(f): rem.remove(f); prog = True
        if not prog:
            f = rem[0]
            if not tryn(f): raise RuntimeError('cannot build target %04x' % f)
            rem.remove(f)
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
    blk, ren = build_block(V, ins, ands, tg, tn)
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
