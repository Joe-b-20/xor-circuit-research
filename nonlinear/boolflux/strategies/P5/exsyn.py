"""SAT exact synthesis of a small multi-output block over {AND, XOR, XNOR} (track P5).

Question answered: is there a circuit of exactly R gates (AND / XOR / XNOR, two inputs each), with
at most MAXA ANDs, computing every target table, where each target meets its AND-level (and
optionally gate-level) deadline?  Levels are relative: each input has an arrival AND level and
gate level (default 0).  Every gate must be used (by a later gate or as a target), so a SAT
answer at R means a circuit of R gates; UNSAT at R is exact for R gates within this library
(NOT gates are never needed in a minimum circuit with XNOR available except for a negated
input, which this encoding does not model: [C] only for the stated library {AND, XOR, XNOR}).

Spec file (JSON):
  {"k": 4,                         # number of variables (tables have 2^k bits)
   "inputs": [{"name": "v0", "table": "0xaaaa", "al": 0, "gl": 0}, ...],
   "targets": [{"name": "t36", "table": "0xb4cc", "al": 4, "gl": 99}, ...]}
usage: python3 exsyn.py SPEC --gates R --maxa 5 [--solver cd15] [--out FILE] [--time S]
Prints SAT + the circuit (name = op a b) or UNSAT.
"""
import argparse, json, sys, time
from itertools import combinations
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver


def build(spec, R, maxa, use_gl=False, sym=True):
    k = spec['k']; N = 1 << k
    ins = spec['inputs']; tg = spec['targets']
    n = len(ins); S = n + R
    pool = IDPool(); cl = []
    X = lambda i, b: pool.id(('x', i, b))
    sel = {}
    for i in range(n, S):
        for j, kk in combinations(range(i), 2):
            sel[(i, j, kk)] = pool.id(('s', i, j, kk))
    isA = {i: pool.id(('A', i)) for i in range(n, S)}
    neg = {i: pool.id(('N', i)) for i in range(n, S)}
    # inputs fixed
    for v, inp in enumerate(ins):
        t = int(inp['table'], 16)
        for b in range(N):
            cl.append([X(v, b) if (t >> b) & 1 else -X(v, b)])
    for i in range(n, S):
        ps = [sel[(i, j, kk)] for j, kk in combinations(range(i), 2)]
        cl.append(ps)
        cl.extend(CardEnc.atmost(ps, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
        cl.append([-isA[i], -neg[i]])          # AND is never complemented
        for j, kk in combinations(range(i), 2):
            s = sel[(i, j, kk)]
            for b in range(N):
                xi, xj, xk = X(i, b), X(j, b), X(kk, b)
                # AND
                cl.append([-s, -isA[i], -xi, xj]); cl.append([-s, -isA[i], -xi, xk])
                cl.append([-s, -isA[i], xi, -xj, -xk])
                # XOR ^ neg
                ng = neg[i]
                for aj in (0, 1):
                    for ak in (0, 1):
                        for an in (0, 1):
                            val = aj ^ ak ^ an
                            c = [-s, isA[i], (-xj if aj else xj), (-xk if ak else xk),
                                 (-ng if an else ng), (xi if val else -xi)]
                            cl.append(c)
    # AND count
    cl.extend(CardEnc.atmost([isA[i] for i in range(n, S)], maxa, vpool=pool,
                             encoding=EncType.seqcounter).clauses)
    # targets
    out = {}
    for ti, t in enumerate(tg):
        tab = int(t['table'], 16)
        lits = []
        for i in range(n, S):
            o = pool.id(('o', ti, i)); out[(ti, i)] = o; lits.append(o)
            for b in range(N):
                cl.append([-o, X(i, b) if (tab >> b) & 1 else -X(i, b)])
        cl.append(lits)
    # every gate used
    for i in range(n, S):
        users = [sel[(u, j, kk)] for u in range(i + 1, S) for j, kk in combinations(range(u), 2)
                 if i in (j, kk)]
        users += [out[(ti, i)] for ti in range(len(tg))]
        cl.append(users)
    # levels
    def levels(key, inlev, isinc, cap):
        L = lambda i, l: pool.id((key, i, l))       # level(i) >= l, l = 1..cap+1
        for v, inp in enumerate(ins):
            for l in range(1, cap + 2):
                cl.append([L(v, l)] if inp[inlev] >= l else [-L(v, l)])
        for i in range(n, S):
            cl.append([-L(i, cap + 1)])
            inc = isinc(i)                           # literal or True
            if inc is True: cl.append([L(i, 1)])
            else: cl.append([-inc, L(i, 1)])
            for j, kk in combinations(range(i), 2):
                s = sel[(i, j, kk)]
                for src in (j, kk):
                    for l in range(1, cap + 1):
                        cl.append([-s, -L(src, l), L(i, l)])
                        if inc is True: cl.append([-s, -L(src, l), L(i, l + 1)])
                        else: cl.append([-s, -inc, -L(src, l), L(i, l + 1)])
        for ti, t in enumerate(tg):
            d = t[inlev]
            if d >= cap: continue
            for i in range(n, S):
                cl.append([-out[(ti, i)], -L(i, d + 1)])
    capa = max(t['al'] for t in tg)
    levels('la', 'al', lambda i: isA[i], capa)
    if use_gl:
        capg = max(t['gl'] for t in tg)
        levels('lg', 'gl', lambda i: True, capg)
    if sym:
        # gate i+1 uses gate i or gates are in colex order of operand pairs (standard rule):
        # if gate i+1 does not use gate i, then pair(i) <= pair(i+1) in a fixed order
        for i in range(n, S - 1):
            pairs_i = list(combinations(range(i), 2))
            order = {p: r for r, p in enumerate(sorted(pairs_i, key=lambda p: (p[1], p[0])))}
            for p in pairs_i:
                for q in combinations(range(i), 2):     # pairs of i+1 not using i
                    if order[q] < order[p]:
                        cl.append([-sel[(i, p[0], p[1])], -sel[(i + 1, q[0], q[1])]])
    return pool, cl, sel, isA, neg, out


def decode(spec, R, model, pool, sel, isA, neg, out):
    ms = set(l for l in model if l > 0)
    n = len(spec['inputs'])
    names = [inp['name'] for inp in spec['inputs']] + ['g%d' % i for i in range(R)]
    lines = []
    for (i, j, kk), s in sel.items():
        if s in ms:
            op = 'AND' if isA[i] in ms else ('XNOR' if neg[i] in ms else 'XOR')
            lines.append((i, '%s = %s %s %s' % (names[i], op, names[j], names[kk])))
    lines.sort()
    tnames = {}
    for (ti, i), o in out.items():
        if o in ms: tnames.setdefault(i, []).append(spec['targets'][ti]['name'])
    return [l + ('   -> ' + ','.join(tnames[i]) if i in tnames else '') for i, l in lines]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec'); ap.add_argument('--gates', type=int, required=True)
    ap.add_argument('--maxa', type=int, required=True)
    ap.add_argument('--solver', default='cd15'); ap.add_argument('--gl', action='store_true')
    ap.add_argument('--nosym', action='store_true')
    ap.add_argument('--out')
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    t0 = time.time()
    pool, cl, sel, isA, neg, out = build(spec, a.gates, a.maxa, a.gl, not a.nosym)
    print('vars %d clauses %d build %.1fs' % (pool.top, len(cl), time.time() - t0), flush=True)
    with Solver(name=a.solver, bootstrap_with=cl) as s:
        ok = s.solve()
        el = time.time() - t0
        if ok:
            lines = decode(spec, a.gates, s.get_model(), pool, sel, isA, neg, out)
            print('SAT gates=%d maxa=%d %.1fs' % (a.gates, a.maxa, el))
            print('\n'.join(lines))
            if a.out: open(a.out, 'w').write('\n'.join(lines) + '\n')
        else:
            print('UNSAT gates=%d maxa=%d %.1fs' % (a.gates, a.maxa, el))
    return 0


if __name__ == '__main__':
    sys.exit(main())
