#!/usr/bin/env python3
"""P7: SAT synthesis of the GD10 inversion sub-problem, layer 1 as a subset of candidate functions.

Layer 1 (gate level 5): any subset of the 36 functions AND(lit, lit) (distinct variables, literals
f_k / ~f_k), XOR(f_a, f_b), XNOR(f_a, f_b); each chosen one costs 1, each twin ~f_k used costs 1.
Layer 2 (gate level 6): K2 generic gates (AND/XOR/XNOR) over literals and chosen layer-1 functions,
ordered (symmetry breaking).  Outputs (gate level 7): four generic gates over everything, equal to the
four base Y-forms.  Total = |L1| + twins + K2 + 4 <= BUDGET.

    invsat2.py SUB.json K2 BUDGET
"""
import itertools, json, sys, time
from pysat.solvers import Cadical153
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

R = 16


def main():
    sub = json.load(open(sys.argv[1])); K2 = int(sys.argv[2]); BUD = int(sys.argv[3])
    Y = sub['Y']
    lit = [sum(((r >> k) & 1) << r for r in range(R)) for k in range(4)]
    ONES = (1 << R) - 1
    lit += [l ^ ONES for l in lit]
    L1 = []    # (table, twins needed set, name)
    for a, b in itertools.combinations(range(4), 2):
        for pa in (0, 1):
            for pb in (0, 1):
                t = lit[a + 4 * pa] & lit[b + 4 * pb]
                tw = set(([a] if pa else []) + ([b] if pb else []))
                L1.append((t, tw, 'AND(%sf%d,%sf%d)' % ('~' if pa else '', a, '~' if pb else '', b)))
        L1.append((lit[a] ^ lit[b], set(), 'XOR(f%d,f%d)' % (a, b)))
        L1.append((lit[a] ^ lit[b] ^ ONES, set(), 'XNOR(f%d,f%d)' % (a, b)))
    pool = IDPool(); cl = []
    nl = len(L1)
    ch = [pool.id(('c', m)) for m in range(nl)]
    tw = [pool.id(('tw', k)) for k in range(4)]
    # signal list: 8 literals (constant tables), nl candidates (constant tables, usable iff chosen), K2 slots, 4 outputs
    const_tab = lit + [t for t, _, _ in L1]
    avail = [None] * 4 + [tw[k] for k in range(4)] + ch       # literal f_k always available
    for m, (t, s, _) in enumerate(L1):
        for k in s: cl.append([-ch[m], tw[k]])
    def tv(s, r): return pool.id(('t', s, r))
    nconst = len(const_tab)
    slot_ids = list(range(nconst, nconst + K2 + 4))
    prev_sel = None
    for idx, s in enumerate(slot_ids):
        isout = idx >= K2
        cand = list(range(nconst)) + (slot_ids[:K2] if isout else slot_ids[:idx])
        pairs = [(i, j) for i, j in itertools.combinations(cand, 2)]
        sel = [pool.id(('s', s, i, j)) for (i, j) in pairs]
        cl.extend(CardEnc.equals(lits=sel, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses)
        opA = pool.id(('opA', s)); opX = pool.id(('opX', s)); cl.append([-opA, -opX])
        for (i, j), v in zip(pairs, sel):
            for k in (i, j):
                if k < nconst and avail[k] is not None: cl.append([-v, avail[k]])
            for r in range(R):
                t = tv(s, r)
                def val(k):
                    return ('c', (const_tab[k] >> r) & 1) if k < nconst else ('v', tv(k, r))
                A = val(i); B = val(j)
                # build clauses with constants folded
                for opname, ctrl in (('AND', [-v, -opA]), ('XOR', [-v, -opX]), ('XNOR', [-v, opA, opX])):
                    for va in (0, 1):
                        for vb in (0, 1):
                            out = (va & vb) if opname == 'AND' else (va ^ vb) if opname == 'XOR' else 1 - (va ^ vb)
                            c = list(ctrl)
                            ok = True
                            for X, vx in ((A, va), (B, vb)):
                                if X[0] == 'c':
                                    if X[1] != vx: ok = False
                                else:
                                    c.append(-X[1] if vx else X[1])
                            if not ok: continue
                            c.append(t if out else -t)
                            cl.append(c)
        if isout:
            g = idx - K2
            for r in range(R): cl.append([tv(s, r)] if (Y[g] >> r) & 1 else [-tv(s, r)])
        else:
            # symmetry: slot idx selects a pair index >= the previous slot's
            if False and prev_sel is not None:
                pp, ps = prev_sel
                pos = {p: q for q, p in enumerate(pairs)}
                for q1, p1 in enumerate(pp):
                    for q2, p2 in enumerate(pairs):
                        if p2 in pos and pos.get(p2, 0) < (pos.get(p1, -1)):
                            cl.append([-ps[q1], -sel[q2]])
            prev_sel = (pairs, sel)
    cost = ch + tw
    cl.extend(CardEnc.atmost(lits=cost, bound=BUD - K2 - 4, vpool=pool, encoding=EncType.seqcounter).clauses)
    t0 = time.time()
    with Cadical153(bootstrap_with=cl) as S:
        res = S.solve()
        print('K2 %d budget %d: %s in %.1f s (vars %d clauses %d)' % (K2, BUD, 'SAT' if res else 'UNSAT', time.time() - t0, pool.top, len(cl)), flush=True)
        if res:
            m = set(x for x in S.get_model() if x > 0)
            print('  L1:', [L1[k][2] for k in range(nl) if ch[k] in m], 'twins', [k for k in range(4) if tw[k] in m])
            names = ['f%d' % k for k in range(4)] + ['~f%d' % k for k in range(4)] + [x[2] for x in L1] + ['g%d' % i for i in range(K2)] + ['Y%d' % i for i in range(4)]
            for s in slot_ids:
                for key, v in pool.obj2id.items():
                    if isinstance(key, tuple) and key[0] == 's' and key[1] == s and v in m:
                        op = 'AND' if pool.id(('opA', s)) in m else 'XOR' if pool.id(('opX', s)) in m else 'XNOR'
                        print('  %s = %s(%s, %s)' % (names[s], op, names[key[2]], names[key[3]]))


if __name__ == '__main__':
    main()
