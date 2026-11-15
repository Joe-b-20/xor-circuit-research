#!/usr/bin/env python3
"""P7: exact (SAT) layered synthesis of the GD10 inversion sub-problem.

Inputs: four N-coordinates f0..f3 (gate level 4; complement twins ~f_k cost one gate each, at the same
level).  Gates of the NIST library (AND, XOR, XNOR).  Layer 1 reads literals, layer 2 reads literals and
layer 1, the four outputs (layer 3, = gate level 7) read anything below.  Outputs = the four base
Y-forms of the circuit with their exact polarity.  Question: is there a circuit with K1 + K2 + 4 +
(twins used) <= BUDGET gates?

    invsat.py SUB.json K1 K2 [--twins MAX] [--timeout S]
SUB.json: {"Y": [16-bit tables over (f0..f3) row index r = sum f_k(r) << k]}
"""
import itertools, json, sys, time
from pysat.solvers import Cadical153
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool


def main():
    sub = json.load(open(sys.argv[1])); K1 = int(sys.argv[2]); K2 = int(sys.argv[3])
    maxtw = 4; tmo = 600
    if '--twins' in sys.argv: maxtw = int(sys.argv[sys.argv.index('--twins') + 1])
    if '--timeout' in sys.argv: tmo = float(sys.argv[sys.argv.index('--timeout') + 1])
    Y = sub['Y']
    R = 16
    pool = IDPool(); cl = []
    # signals: 0..3 = f_k, 4..7 = ~f_k (constant tables), then slots
    lit_t = [[(r >> k) & 1 for r in range(R)] for k in range(4)] + [[1 - ((r >> k) & 1) for r in range(R)] for k in range(4)]
    slots = [('L1', g) for g in range(K1)] + [('L2', g) for g in range(K2)] + [('O', k) for k in range(4)]
    nsig = 8 + len(slots)
    def tv(s, r):
        return pool.id(('t', s, r))
    # literal tables are constants: represent with fixed units
    for s in range(8):
        for r in range(R):
            cl.append([tv(s, r)] if lit_t[s][r] else [-tv(s, r)])
    twin = [pool.id(('tw', k)) for k in range(4)]
    for idx, (lay, g) in enumerate(slots):
        s = 8 + idx
        if lay == 'L1': cand = list(range(8))
        elif lay == 'L2': cand = list(range(8 + K1))
        else: cand = list(range(8 + K1 + K2))
        pairs = [(i, j) for i, j in itertools.combinations(cand, 2) if not (i < 8 and j < 8 and (i % 4) == (j % 4))]
        sel = [pool.id(('s', s, i, j)) for (i, j) in pairs]
        enc = CardEnc.equals(lits=sel, bound=1, vpool=pool, encoding=EncType.seqcounter)
        cl.extend(enc.clauses)
        opA = pool.id(('opA', s)); opX = pool.id(('opX', s))   # AND / XOR / XNOR (neither -> XNOR)
        cl.append([-opA, -opX])
        for (i, j), v in zip(pairs, sel):
            for k in (i, j):
                if 4 <= k < 8: cl.append([-v, twin[k - 4]])
            for r in range(R):
                a = tv(i, r); b = tv(j, r); t = tv(s, r)
                # AND
                cl += [[-v, -opA, -t, a], [-v, -opA, -t, b], [-v, -opA, t, -a, -b]]
                # XOR
                cl += [[-v, -opX, -t, a, b], [-v, -opX, -t, -a, -b], [-v, -opX, t, -a, b], [-v, -opX, t, a, -b]]
                # XNOR (opA = opX = 0)
                cl += [[-v, opA, opX, t, a, b], [-v, opA, opX, t, -a, -b], [-v, opA, opX, -t, -a, b], [-v, opA, opX, -t, a, -b]]
        if lay == 'O':
            for r in range(R):
                cl.append([tv(s, r)] if (Y[g] >> r) & 1 else [-tv(s, r)])
    # every layer-1/2 slot must be used (else a smaller K would do): skip (minimality via iteration)
    enc = CardEnc.atmost(lits=twin, bound=maxtw, vpool=pool, encoding=EncType.seqcounter)
    cl.extend(enc.clauses)
    # symmetry: layer slots distinct functions (lexicographic order would be stronger; skip)
    t0 = time.time()
    with Cadical153(bootstrap_with=cl) as S:
        res = S.solve()
        el = time.time() - t0
        print('K1 %d K2 %d twins<=%d: %s in %.1f s (vars %d, clauses %d)' % (K1, K2, maxtw, 'SAT' if res else 'UNSAT', el, pool.top, len(cl)))
        if res:
            m = set(x for x in S.get_model() if x > 0)
            names = ['f%d' % k for k in range(4)] + ['~f%d' % k for k in range(4)] + ['%s%d' % sl for sl in slots]
            for idx, (lay, g) in enumerate(slots):
                s = 8 + idx
                for key, v in list(pool.obj2id.items()):
                    if isinstance(key, tuple) and key[0] == 's' and key[1] == s and v in m:
                        op = 'AND' if pool.id(('opA', s)) in m else 'XOR' if pool.id(('opX', s)) in m else 'XNOR'
                        print('  %s = %s(%s, %s)' % (names[s], op, names[key[2]], names[key[3]]))
            print('  twins used:', [k for k in range(4) if twin[k] in m])


if __name__ == '__main__':
    main()
