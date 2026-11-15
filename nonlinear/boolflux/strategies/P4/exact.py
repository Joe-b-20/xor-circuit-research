"""P4: exact multi-output synthesis over {AND, XOR, XNOR} by SAT (pysat CaDiCaL).

synth(n, targets, steps, amax, amin=0, budget=None, levels=None)
  n        number of inputs (truth tables over 2^n rows; inputs are the n projections)
  targets  list of truth tables (ints over 2^n bits); each must equal an input or a step's value
           (exactly, no free complement)
  steps    number of gates
  amax     at most amax AND gates (amin at least)
  levels   optional (in_arrival list, out_deadline list, max_level) for gate-depth constraints
Returns (status, chain) with chain = list of (op, j, k) over node indices (0..n-1 inputs).
NOT gates are not in the encoding (a stated restriction of the case: NOT costs a gate in NIST counting).
"""
import itertools
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver


def synth(n, targets, steps, amax, amin=0, budget=None, levels=None, solver='cadical153', sym=True,
          time_limit=None, verbose=False):
    R = 1 << n
    pool = IDPool()
    cls = []
    N = n + steps
    v = lambda i, t: pool.id(('v', i, t))       # value of node i at row t
    sel = lambda i, j, k: pool.id(('s', i, j, k))
    isand = lambda i: pool.id(('a', i))
    cx = lambda i: pool.id(('c', i))            # XNOR flag
    # inputs: fixed values
    for i in range(n):
        for t in range(R):
            cls.append([v(i, t)] if (t >> i) & 1 else [-v(i, t)])
    for i in range(n, N):
        pairs = [(j, k) for j in range(i) for k in range(j + 1, i)]
        sv = [sel(i, j, k) for j, k in pairs]
        cls.append(sv)
        for a, b in itertools.combinations(sv, 2):
            cls.append([-a, -b])
        # AND gates have no complement flag
        cls.append([-isand(i), -cx(i)])
        for (j, k) in pairs:
            s = sel(i, j, k)
            for t in range(R):
                x, a, b = v(i, t), v(j, t), v(k, t)
                # AND: x = a & b
                cls += [[-s, -isand(i), -x, a], [-s, -isand(i), -x, b], [-s, -isand(i), x, -a, -b]]
                # XOR/XNOR: x = a ^ b ^ c
                c = cx(i)
                for aa in (0, 1):
                    for bb in (0, 1):
                        for cc in (0, 1):
                            r = aa ^ bb ^ cc
                            cls.append([-s, isand(i), (a if aa == 0 else -a), (b if bb == 0 else -b),
                                        (c if cc == 0 else -c), (x if r else -x)])
        # every step used (by a later step or an output) is implied by minimality; enforce anyway
    # outputs
    for o, tt in enumerate(targets):
        cand = []
        for i in range(N):
            if i < n:
                inp = sum(1 << t for t in range(R) if (t >> i) & 1)
                if inp == tt:
                    cand = None
                    break
                continue
            m = pool.id(('o', o, i))
            cand.append(m)
            for t in range(R):
                cls.append([-m, v(i, t)] if (tt >> t) & 1 else [-m, -v(i, t)])
        if cand is None:
            continue
        cls.append(cand)
    # every step is read (no dead steps): a step is used by a later step or is an output
    for i in range(n, N):
        users = [sel(l, j, k) for l in range(i + 1, N) for j in range(l) for k in range(j + 1, l) if i in (j, k)]
        users += [pool.id(('o', o, i)) for o in range(len(targets))]
        cls.append(users)
    # AND count
    ands = [isand(i) for i in range(n, N)]
    if amax is not None and amax < steps:
        enc = CardEnc.atmost(ands, bound=amax, vpool=pool, encoding=EncType.seqcounter)
        cls += enc.clauses
    if amin:
        enc = CardEnc.atleast(ands, bound=amin, vpool=pool, encoding=EncType.seqcounter)
        cls += enc.clauses
    # symmetry: if step i+1 does not read step i, then (j,k) of step i <= (j,k) of step i+1 (colex)
    if sym:
        for i in range(n, N - 1):
            pi = [(j, k) for j in range(i) for k in range(j + 1, i)]
            pn = [(j, k) for j in range(i + 1) for k in range(j + 1, i + 1) if i not in (j, k)]
            key = lambda p: (p[1], p[0])
            for (j, k) in pi:
                for (j2, k2) in pn:
                    if key((j2, k2)) < key((j, k)):
                        cls.append([-sel(i, j, k), -sel(i + 1, j2, k2)])
    # levels
    if levels is not None:
        arr, dead, L = levels
        lv = lambda i, l: pool.id(('L', i, l))   # node i has level >= l  (order encoding)
        for i in range(N):
            for l in range(2, L + 1):
                cls.append([-lv(i, l), lv(i, l - 1)])
            if i < n:
                for l in range(1, L + 1):
                    cls.append([lv(i, l)] if arr[i] >= l else [-lv(i, l)])
            else:
                cls.append([lv(i, 1)])
                cls.append([-lv(i, L + 1)] if False else [lv(i, 1)])
                for j in range(i):
                    for k in range(j + 1, i):
                        s = sel(i, j, k)
                        for l in range(1, L):
                            cls.append([-s, -lv(j, l), lv(i, l + 1)])
                            cls.append([-s, -lv(k, l), lv(i, l + 1)])
                        cls.append([-s, -lv(j, L)])
                        cls.append([-s, -lv(k, L)])
        for o, d in enumerate(dead):
            for i in range(n, N):
                m = pool.id(('o', o, i))
                if d < L:
                    cls.append([-m, -lv(i, d + 1)])
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
        for j in range(i):
            for k in range(j + 1, i):
                if sel(i, j, k) in model:
                    op = 'AND' if isand(i) in model else ('XNOR' if cx(i) in model else 'XOR')
                    chain.append((op, j, k))
    outs = []
    for o, tt in enumerate(targets):
        hit = None
        for i in range(N):
            if pool.obj2id.get(('o', o, i)) and pool.id(('o', o, i)) in model:
                hit = i
                break
        if hit is None:
            for i in range(n):
                if sum(1 << t for t in range(R) if (t >> i) & 1) == tt:
                    hit = i
        outs.append(hit)
    return 'sat', (chain, outs), el


def evaluate(n, chain):
    R = 1 << n
    M = (1 << R) - 1
    vals = [sum(1 << t for t in range(R) if (t >> i) & 1) for i in range(n)]
    for op, j, k in chain:
        a, b = vals[j], vals[k]
        vals.append(a & b if op == 'AND' else (a ^ b if op == 'XOR' else (a ^ b) ^ M))
    return vals
