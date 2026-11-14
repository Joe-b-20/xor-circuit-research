"""Last-layer problems for llay.c and circuit building from table pairs.

usage:
  python3 ll_prob.py make --l1 FILE --inv FILE --k K --out OUT.prob [--wide]
      E = span(1, x, level-1 products of --l1 FILE, middle products (inversion) of --inv FILE)
      O = span(x, N, N^-1) coordinates (16 dims), or with --wide: a basis of E/<1> (all of E)
  python3 ll_prob.py build --l1 FILE --inv FILE --prob OUT.prob --sol SOL --out CIRC.txt
      build the circuit (XOR chains) from a llay solution and write NCFF
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                          # noqa: E402
from core import Circuit, write_ncff               # noqa: E402
from nlbprob import Span, words                    # noqa: E402
from aes_prob import load_circuit, sbox_tables, n_coords   # noqa: E402

ONES = (1 << 256) - 1


def ninv_coords():
    N = [gf.power(p, 17) for p in range(256)]
    n = [gf.INV[v] for v in N]
    sp = gf.Span(); basis = []
    for v in gf.SUB16:
        if v and sp.add(v): basis.append(v)
    return gf.coord_tables(n, basis)


def prefix_pairs(l1file, invfile):
    """(Ltab, Rtab) of the level-1 products of l1file then the middle products of invfile"""
    _, lev1, ands1 = load_circuit(l1file)
    _, lev2, ands2 = load_circuit(invfile)
    top2 = max(lev2)
    pairs = [(A['Ltab'], A['Rtab']) for A in ands1 if A['level'] == 1]
    pairs += [(A['Ltab'], A['Rtab']) for A in ands2 if 1 < A['level'] < top2]
    return pairs


def build_tables(pairs, outs, n=8, name='aes-sbox-G'):
    """circuit from ordered products given by operand tables; operands/outputs by XOR chains over
    [inputs, earlier products] (constant handled by AND op variants / NOT)"""
    X = gf.X
    gates = []
    S = Span()
    S.add(ONES, 0)                       # tag 0 = constant (bit 0 of tags unused)
    sig = {}
    for i in range(n): S.add(X[i], 1 << (1 + i)); sig[1 + i] = i
    tabs = {}

    def chain(t):
        tag = S.express(t)
        neg = False
        if tag is None:
            tag = S.express(t ^ ONES); neg = True
            if tag is None: raise ValueError('not in span')
        # tag bit 0 cannot appear (constant has tag 0); neg tracks the constant
        idx = [j for j in range(1, tag.bit_length()) if (tag >> j) & 1]
        # check: constant offset may be hidden: recompute value
        val = 0
        for j in idx: val ^= tabs_all[j]
        if val != t:
            if val ^ ONES == t: neg = True
            else: raise ValueError('chain mismatch')
        else:
            neg = False
        if not idx: raise ValueError('constant')
        cur = sig[idx[0]]
        for j in idx[1:]:
            gates.append((6, cur, sig[j])); cur = n + len(gates) - 1
        return cur, neg

    tabs_all = {1 + i: X[i] for i in range(n)}
    for k, (ta, tb) in enumerate(pairs):
        # constants in operands are dropped: (l+1)m = lm + m with m in the span, so the span of the
        # products (and every later expression, done on actual tables) is unchanged
        sa, na = chain(ta); sb, nb = chain(tb)
        va = ta ^ (ONES if na else 0); vb = tb ^ (ONES if nb else 0)
        gates.append((8, sa, sb))
        e = 1 + n + k
        sig[e] = n + len(gates) - 1
        tabs_all[e] = va & vb
        if not S.add(va & vb, 1 << e): raise ValueError('dependent product %d' % k)
    osig = []
    for t in outs:
        s, neg = chain(t)
        if neg: gates.append((3, s, s)); s = n + len(gates) - 1
        osig.append(s)
    c = Circuit(n, len(outs), gates, osig, name, ['U%d' % i for i in range(n)], ['S%d' % j for j in range(len(outs))])
    c = c.live()
    assert c.output_tables() == list(outs), 'circuit check failed'
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('--l1'); ap.add_argument('--inv'); ap.add_argument('--k', type=int)
    ap.add_argument('--out'); ap.add_argument('--wide', action='store_true')
    ap.add_argument('--prob'); ap.add_argument('--sol')
    ap.add_argument('--joint', type=int, default=0,
                    help='variable stage 1 with this many level-1 slots (E0 = 1, x, inversion of --inv)')
    ap.add_argument('--drop', default='')
    a = ap.parse_args()
    if a.cmd == 'inits1':
        # level-1 products of --l1 as coefficient vectors over the 8 inputs (constants dropped)
        _, lev, ands = load_circuit(a.l1)
        SX = Span()
        for i, t in enumerate(gf.X): SX.add(t, 1 << i)
        SX.add(ONES, 0)
        drop = [int(v) - 1 for v in a.drop.split(',')] if a.drop else []
        rows = [(SX.express(A['Ltab']), SX.express(A['Rtab'])) for A in ands if A['level'] == 1]
        rows = [r for i, r in enumerate(rows) if i not in drop]
        Path(a.out).write_text('inits1 K %d\n' % len(rows) + ''.join('%x %x\n' % r for r in rows),
                               encoding='utf-8', newline='\n')
        print(json.dumps({'out': a.out, 'nS1': len(rows), 'dropped': [d + 1 for d in drop]}))
        return
    if a.joint:
        _, lev2, ands2 = load_circuit(a.inv)
        top2 = max(lev2)
        pairs = [(A['Ltab'], A['Rtab']) for A in ands2 if 1 < A['level'] < top2]
        E = [ONES] + list(gf.X) + [x & y for x, y in pairs]
        O = list(gf.X) + n_coords() + ninv_coords()
        if a.cmd == 'make':
            T = sbox_tables()
            L = ['4 256', str(len(E))] + [words(t, 4) for t in E]
            L += [str(len(O))] + [words(t, 4) for t in O]
            L += [str(len(T))] + [words(t, 4) for t in T] + [str(a.k)]
            L += [str(a.joint), '8'] + [words(t, 4) for t in gf.X]
            L += ['4'] + [words(t, 4) for t in n_coords()]
            Path(a.out).write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n')
            print(json.dumps({'out': a.out, 'joint': a.joint, 'K': a.k, 'nE0': len(E)}))
            return
        if a.cmd == 'build':
            lines = Path(a.sol).read_text().split('\n')
            K = int(lines[0].split()[lines[0].split().index('K') + 1])
            ns1 = int(lines[0].split()[lines[0].split().index('nS1') + 1])
            def lin(m, basis):
                t = 0
                for i in range(len(basis)):
                    if (m >> i) & 1: t ^= basis[i]
                return t
            s1 = []
            for s in range(ns1):
                x, y = (int(v, 16) for v in lines[1 + K + s].split())
                s1.append((lin(x, gf.X), lin(y, gf.X)))
            last = []
            for k in range(K):
                l, m = (int(v, 16) for v in lines[1 + k].split())
                last.append((lin(l, O), lin(m, O)))
            c = build_tables(s1 + pairs + last, sbox_tables())
            m = c.metrics()
            txt = write_ncff(c, comments=['track G llay joint build: %d level-1 + %d middle + %d last-layer ANDs'
                                          % (ns1, len(pairs), K)])
            Path(a.out).write_text(txt, encoding='utf-8', newline='\n')
            print(json.dumps({'out': a.out, 'A': m['A'], 'G': m['G'], 'AD': m['AD']}))
            return
    pairs = prefix_pairs(a.l1, a.inv)
    E = [ONES] + list(gf.X) + [x & y for x, y in pairs]
    SE = Span()
    for t in E: SE.add(t, 0)
    if a.wide:
        O = list(gf.X) + [x & y for x, y in pairs]
    else:
        O = list(gf.X) + n_coords() + ninv_coords()
    if a.cmd == 'make':
        for t in O:
            assert SE.express(t) is not None or SE.express(t ^ ONES) is not None, 'O not inside E'
        T = sbox_tables()
        L = ['4 256', str(len(E))] + [words(t, 4) for t in E]
        L += [str(len(O))] + [words(t, 4) for t in O]
        L += [str(len(T))] + [words(t, 4) for t in T] + [str(a.k)]
        Path(a.out).write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n')
        # deficit of T mod E
        d = sum(1 for t in T if SE.add(t, 0))
        print(json.dumps({'out': a.out, 'nE': len(E), 'rankE': len(SE.rows) - d, 'nO': len(O), 'deficit_T_mod_E': d, 'K': a.k}))
    elif a.cmd == 'init':
        # last layer of --src FILE as O-coefficient vectors (constants dropped: changes lie in E)
        _, lev, ands = load_circuit(a.sol)
        top = max(lev)
        SO = Span()
        for i, t in enumerate(O): SO.add(t, 1 << i)
        SO.add(ONES, 0)
        rows = []
        for A in ands:
            if A['level'] != top: continue
            cl = SO.express(A['Ltab']); cm = SO.express(A['Rtab'])
            if cl is None or cm is None: raise SystemExit('operand not in O')
            rows.append((cl, cm))
        drop = [int(v) - 1 for v in a.prob.split(',')] if a.prob else []
        rows = [r for i, r in enumerate(rows) if i not in drop]
        Path(a.out).write_text('init K %d\n' % len(rows) + ''.join('%x %x\n' % r for r in rows),
                               encoding='utf-8', newline='\n')
        print(json.dumps({'out': a.out, 'K': len(rows), 'dropped': [d + 1 for d in drop]}))
    elif a.cmd == 'build':
        lines = Path(a.sol).read_text().split('\n')
        K = int(lines[0].split()[lines[0].split().index('K') + 1])
        last = []
        for k in range(K):
            l, m = (int(v, 16) for v in lines[1 + k].split())
            ta = tb = 0
            for i in range(len(O)):
                if (l >> i) & 1: ta ^= O[i]
                if (m >> i) & 1: tb ^= O[i]
            last.append((ta, tb))
        c = build_tables(pairs + last, sbox_tables())
        m = c.metrics()
        txt = write_ncff(c, comments=['track G llay build: %d prefix + %d last-layer ANDs' % (len(pairs), K)])
        Path(a.out).write_text(txt, encoding='utf-8', newline='\n')
        print(json.dumps({'out': a.out, 'A': m['A'], 'G': m['G'], 'AD': m['AD']}))


if __name__ == '__main__':
    main()
