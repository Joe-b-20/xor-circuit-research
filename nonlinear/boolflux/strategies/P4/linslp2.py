"""P4: exact linear SLP by SAT, operand-wise one-hot encoding (smaller than the pair encoding of
linslp.py).  Same interface: slp(dim, base, targets, steps, budget, arrivals, deadlines).

Step i (node nb+i) reads left node j and right node k, j < k < node; value = v_j xor v_k.
Constants are free (XNOR = XOR cost), so vectors carry no constant.
Restrictions of the case: XOR gates only, each step distinct by minimality (not enforced),
every step read by a later step or a target (no dead steps).
"""
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver


def slp(dim, base, targets, steps, budget=None, arrivals=None, deadlines=None, sym=True,
        solver='cadical153', time_limit=None, build_only=False):
    pool = IDPool()
    cls = []
    nb = len(base)
    N = nb + steps
    tg = []
    dlist = []
    for idx, t in enumerate(targets):
        if t in base:
            continue
        if t in tg:
            continue
        tg.append(t)
        if deadlines is not None:
            dlist.append(deadlines[idx])
    v = lambda i, d: pool.id(('v', i, d))
    L = lambda i, j: pool.id(('l', i, j))
    Rr = lambda i, k: pool.id(('r', i, k))
    lv_ = lambda i, d: pool.id(('Lv', i, d))
    rv_ = lambda i, d: pool.id(('Rv', i, d))
    for i in range(nb):
        for d in range(dim):
            cls.append([v(i, d)] if (base[i] >> d) & 1 else [-v(i, d)])
    for i in range(nb, N):
        ls = [L(i, j) for j in range(i - 1)]
        rs = [Rr(i, k) for k in range(1, i)]
        cls += CardEnc.equals(ls, 1, vpool=pool, encoding=EncType.seqcounter).clauses
        cls += CardEnc.equals(rs, 1, vpool=pool, encoding=EncType.seqcounter).clauses
        for j in range(i - 1):
            for k in range(1, j + 1):
                cls.append([-L(i, j), -Rr(i, k)])
        for j in range(i - 1):
            for d in range(dim):
                cls.append([-L(i, j), -v(j, d), lv_(i, d)])
                cls.append([-L(i, j), v(j, d), -lv_(i, d)])
        for k in range(1, i):
            for d in range(dim):
                cls.append([-Rr(i, k), -v(k, d), rv_(i, d)])
                cls.append([-Rr(i, k), v(k, d), -rv_(i, d)])
        for d in range(dim):
            x, a, b = v(i, d), lv_(i, d), rv_(i, d)
            cls += [[-x, a, b], [-x, -a, -b], [x, -a, b], [x, a, -b]]
        # value must be nonzero and different from every base vector (minimality, sound)
        cls.append([v(i, d) for d in range(dim)])
    om = {}
    for o, tt in enumerate(tg):
        cand = []
        for i in range(nb, N):
            m = pool.id(('o', o, i))
            om[(o, i)] = m
            cand.append(m)
            for d in range(dim):
                cls.append([-m, v(i, d)] if (tt >> d) & 1 else [-m, -v(i, d)])
        cls.append(cand)
    # no dead steps
    for i in range(nb, N):
        users = [L(l, i) for l in range(i + 1, N) if i < l - 1] + [Rr(l, i) for l in range(i + 1, N)]
        users += [om[(o, i)] for o in range(len(tg))]
        cls.append(users)
    if sym:
        # consecutive independent steps in colex order of (k, j)
        for i in range(nb, N - 1):
            i2 = i + 1
            for k in range(1, i):
                for k2 in range(1, k):
                    # step i2 has right operand k2 < k (and does not read i): forbidden
                    cls.append([-Rr(i, k), -Rr(i2, k2)])
                for j in range(k):
                    for j2 in range(j):
                        cls.append([-Rr(i, k), -L(i, j), -Rr(i2, k), -L(i2, j2)])
    if arrivals is not None:
        Lmax = max(dlist)
        lvl = lambda i, l: pool.id(('lev', i, l))  # level(i) >= l
        for i in range(N):
            for l in range(2, Lmax + 1):
                cls.append([-lvl(i, l), lvl(i, l - 1)])
        for i in range(nb):
            for l in range(1, Lmax + 1):
                cls.append([lvl(i, l)] if arrivals[i] >= l else [-lvl(i, l)])
        for i in range(nb, N):
            cls.append([lvl(i, 1)])
            for j in range(i):
                sj = []
                if j < i - 1:
                    sj.append(L(i, j))
                if j >= 1:
                    sj.append(Rr(i, j))
                for s in sj:
                    for l in range(1, Lmax):
                        cls.append([-s, -lvl(j, l), lvl(i, l + 1)])
                    if j < nb and arrivals[j] >= Lmax:
                        cls.append([-s])
                    else:
                        cls.append([-s, -lvl(j, Lmax)])
        for o in range(len(tg)):
            d = dlist[o]
            for i in range(nb, N):
                if d < Lmax:
                    cls.append([-om[(o, i)], -lvl(i, d + 1)])
                if d < 1:
                    cls.append([-om[(o, i)]])
    if build_only:
        return cls, pool
    S = Solver(name=solver, bootstrap_with=cls)
    t0 = time.time()
    if budget:
        S.conf_budget(budget)
        res = S.solve_limited()
    else:
        res = S.solve()
    el = time.time() - t0
    if res is None:
        S.delete()
        return 'unknown', None, el
    if not res:
        S.delete()
        return 'unsat', None, el
    model = set(l for l in S.get_model() if l > 0)
    chain = []
    for i in range(nb, N):
        j = next(j for j in range(i - 1) if L(i, j) in model)
        k = next(k for k in range(1, i) if Rr(i, k) in model)
        chain.append((j, k))
    S.delete()
    return 'sat', chain, el


def values(base, chain):
    vals = list(base)
    for j, k in chain:
        vals.append(vals[j] ^ vals[k])
    return vals


def build(dim, base, targets, steps, sym=True):
    return slp(dim, base, targets, steps, sym=sym, build_only=True)
