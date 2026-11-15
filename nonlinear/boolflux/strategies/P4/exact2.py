"""P4: exact multi-output synthesis over {AND, XOR, XNOR}, operand-wise one-hot SAT encoding.

synth(n, targets, steps, amax, amin=0, budget=None, outs_any_complement=False)
  Inputs are the n projections over 2^n rows.  Each target must equal an input or a step exactly.
  Step i: left operand j, right operand k (j < k < i), type AND or XOR, XNOR flag for XOR.
  Restrictions of the case: no NOT gates; no dead steps; every step distinct from its operands.
"""
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver


def synth(n, targets, steps, amax, amin=0, budget=None, sym=True, solver='cadical153', and_positions=None):
    R = 1 << n
    pool = IDPool()
    cls = []
    N = n + steps
    v = lambda i, t: pool.id(('v', i, t))
    L = lambda i, j: pool.id(('l', i, j))
    Rr = lambda i, k: pool.id(('r', i, k))
    a_ = lambda i, t: pool.id(('A', i, t))
    b_ = lambda i, t: pool.id(('B', i, t))
    isand = lambda i: pool.id(('and', i))
    cx = lambda i: pool.id(('cx', i))
    for i in range(n):
        for t in range(R):
            cls.append([v(i, t)] if (t >> i) & 1 else [-v(i, t)])
    for i in range(n, N):
        ls = [L(i, j) for j in range(i - 1)]
        rs = [Rr(i, k) for k in range(1, i)]
        cls += CardEnc.equals(ls, 1, vpool=pool, encoding=EncType.seqcounter).clauses
        cls += CardEnc.equals(rs, 1, vpool=pool, encoding=EncType.seqcounter).clauses
        for j in range(i - 1):
            for k in range(1, j + 1):
                cls.append([-L(i, j), -Rr(i, k)])
        for j in range(i - 1):
            for t in range(R):
                cls.append([-L(i, j), -v(j, t), a_(i, t)])
                cls.append([-L(i, j), v(j, t), -a_(i, t)])
        for k in range(1, i):
            for t in range(R):
                cls.append([-Rr(i, k), -v(k, t), b_(i, t)])
                cls.append([-Rr(i, k), v(k, t), -b_(i, t)])
        cls.append([-isand(i), -cx(i)])
        for t in range(R):
            x, a, b, g, c = v(i, t), a_(i, t), b_(i, t), isand(i), cx(i)
            # AND
            cls += [[-g, -x, a], [-g, -x, b], [-g, x, -a, -b]]
            # XOR ^ c
            for aa in (0, 1):
                for bb in (0, 1):
                    for cc in (0, 1):
                        r = aa ^ bb ^ cc
                        cls.append([g, (a if aa == 0 else -a), (b if bb == 0 else -b), (c if cc == 0 else -c),
                                    (x if r else -x)])
        if and_positions is not None:
            cls.append([isand(i)] if (i - n) in and_positions else [-isand(i)])
    om = {}
    inputs_tt = [sum(1 << t for t in range(R) if (t >> i) & 1) for i in range(n)]
    for o, tt in enumerate(targets):
        if tt in inputs_tt:
            continue
        cand = []
        for i in range(n, N):
            m = pool.id(('o', o, i))
            om[(o, i)] = m
            cand.append(m)
            for t in range(R):
                cls.append([-m, v(i, t)] if (tt >> t) & 1 else [-m, -v(i, t)])
        cls.append(cand)
    for i in range(n, N):
        users = [L(l, i) for l in range(i + 2, N)] + [Rr(l, i) for l in range(i + 1, N)]
        users += [om[(o, i)] for o in range(len(targets)) if (o, i) in om]
        cls.append(users)
    ands = [isand(i) for i in range(n, N)]
    if amax is not None and amax < steps and and_positions is None:
        cls += CardEnc.atmost(ands, bound=amax, vpool=pool, encoding=EncType.seqcounter).clauses
    if amin and and_positions is None:
        cls += CardEnc.atleast(ands, bound=amin, vpool=pool, encoding=EncType.seqcounter).clauses
    if sym and and_positions is None:
        for i in range(n, N - 1):
            i2 = i + 1
            for k in range(1, i):
                for k2 in range(1, k):
                    cls.append([-Rr(i, k), -Rr(i2, k2)])
                for j in range(k):
                    for j2 in range(j):
                        cls.append([-Rr(i, k), -L(i, j), -Rr(i2, k), -L(i2, j2)])
    S = Solver(name=solver, bootstrap_with=cls)
    t0 = time.time()
    if budget:
        S.conf_budget(budget)
        res = S.solve_limited()
    else:
        res = S.solve()
    el = time.time() - t0
    if res is None:
        return 'unknown', None, el
    if not res:
        return 'unsat', None, el
    model = set(l for l in S.get_model() if l > 0)
    chain = []
    for i in range(n, N):
        j = next(j for j in range(i - 1) if L(i, j) in model)
        k = next(k for k in range(1, i) if Rr(i, k) in model)
        op = 'AND' if isand(i) in model else ('XNOR' if cx(i) in model else 'XOR')
        chain.append((op, j, k))
    return 'sat', chain, el
