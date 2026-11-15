"""P4: exact linear SLP by SAT (XOR gates over GF(2), cancellation allowed; constants are free
because XNOR costs the same as XOR, so vectors are compared without constants).

slp(dim, base, targets, steps, ...)
  base     list of int bit-vectors (free signals, available at no cost)
  targets  list of int bit-vectors; each must equal a base vector or a step
  arrivals optional list of levels of the base signals; deadlines optional per target; then
           the gate level of each step is constrained (order encoding).
Returns (status, chain, elapsed); chain = list of (j, k) node pairs (nodes 0..len(base)-1 are base).
"""
import itertools
import time

from pysat.formula import IDPool
from pysat.solvers import Solver


def slp(dim, base, targets, steps, budget=None, arrivals=None, deadlines=None, sym=True,
        solver='cadical153', allow_unused=False, assumptions_only=False):
    pool = IDPool()
    cls = []
    nb = len(base)
    N = nb + steps
    v = lambda i, d: pool.id(('v', i, d))
    sel = lambda i, j, k: pool.id(('s', i, j, k))
    tg = [t for t in targets if t not in base]
    for i in range(nb):
        for d in range(dim):
            cls.append([v(i, d)] if (base[i] >> d) & 1 else [-v(i, d)])
    for i in range(nb, N):
        pairs = [(j, k) for j in range(i) for k in range(j + 1, i)]
        sv = [sel(i, j, k) for j, k in pairs]
        cls.append(sv)
        # at most one (sequential/commander is overkill here: use pairwise only when small)
        if len(sv) <= 60:
            for a, b in itertools.combinations(sv, 2):
                cls.append([-a, -b])
        else:
            from pysat.card import CardEnc, EncType
            cls += CardEnc.atmost(sv, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses
        for (j, k) in pairs:
            s = sel(i, j, k)
            for d in range(dim):
                x, a, b = v(i, d), v(j, d), v(k, d)
                cls += [[-s, -x, a, b], [-s, -x, -a, -b], [-s, x, -a, b], [-s, x, a, -b]]
    # no step equals a base vector or another step's value is not enforced (minimality does it)
    om = {}
    for o, tt in enumerate(tg):
        cand = []
        for i in range(nb, N):
            m = pool.id(('o', o, i))
            cand.append(m)
            om[(o, i)] = m
            for d in range(dim):
                cls.append([-m, v(i, d)] if (tt >> d) & 1 else [-m, -v(i, d)])
        cls.append(cand)
    if not allow_unused:
        for i in range(nb, N):
            users = [sel(l, j, k) for l in range(i + 1, N) for j in range(l) for k in range(j + 1, l) if i in (j, k)]
            users += [om[(o, i)] for o in range(len(tg))]
            cls.append(users)
    if sym:
        for i in range(nb, N - 1):
            pi = [(j, k) for j in range(i) for k in range(j + 1, i)]
            pn = [(j, k) for j in range(i + 1) for k in range(j + 1, i + 1) if i not in (j, k)]
            key = lambda p: (p[1], p[0])
            for (j, k) in pi:
                kk = key((j, k))
                for (j2, k2) in pn:
                    if key((j2, k2)) < kk:
                        cls.append([-sel(i, j, k), -sel(i + 1, j2, k2)])
    if arrivals is not None:
        L = max(deadlines.values()) if isinstance(deadlines, dict) else max(deadlines)
        lv = lambda i, l: pool.id(('L', i, l))  # level(i) >= l
        for i in range(N):
            for l in range(2, L + 1):
                cls.append([-lv(i, l), lv(i, l - 1)])
        for i in range(nb):
            for l in range(1, L + 1):
                cls.append([lv(i, l)] if arrivals[i] >= l else [-lv(i, l)])
            if arrivals[i] > L:
                pass
        for i in range(nb, N):
            cls.append([lv(i, 1)])
            for j in range(i):
                for k in range(j + 1, i):
                    s = sel(i, j, k)
                    for l in range(1, L):
                        cls.append([-s, -lv(j, l), lv(i, l + 1)])
                        cls.append([-s, -lv(k, l), lv(i, l + 1)])
                    cls.append([-s, -lv(j, L)])
                    cls.append([-s, -lv(k, L)])
                    # base signals that arrive later than L cannot be read
                    if j < nb and arrivals[j] >= L:
                        cls.append([-s])
                    if k < nb and arrivals[k] >= L:
                        cls.append([-s])
        dl = deadlines if not isinstance(deadlines, dict) else [deadlines[t] for t in tg]
        for o in range(len(tg)):
            d = dl[o]
            for i in range(nb, N):
                if d < L:
                    cls.append([-om[(o, i)], -lv(i, d + 1)])
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
    for i in range(nb, N):
        for j in range(i):
            for k in range(j + 1, i):
                if sel(i, j, k) in model:
                    chain.append((j, k))
    S.delete()
    return 'sat', chain, el


def values(base, chain):
    vals = list(base)
    for j, k in chain:
        vals.append(vals[j] ^ vals[k])
    return vals
