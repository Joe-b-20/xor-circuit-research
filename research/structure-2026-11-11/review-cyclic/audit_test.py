"""Reviewer's own numerical test of the order-free versions of PROOF.md lemmas on MINIMUM based cyclic
systems that are not circuits (n = 7 test matrices with L_cyc < L, boundary all odd in both orientations).
usage: python3 audit_test.py SEED BASES_PER_SET  row1 ... row7   (rows as ints, bit i = coeff of e_(i+1))
"""
import sys, random, subprocess, os, itertools
HERE = os.path.dirname(os.path.abspath(__file__))

def par(v): return bin(v).count('1') & 1
def rank_f2(rows):
    basis = {}; r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; r += 1; break
    return r
def triples(S):
    S = sorted(S); Ss = set(S); out = []
    for i, a in enumerate(S):
        for b in S[i + 1:]:
            c = a ^ b
            if c in Ss and c > b: out.append((a, b, c))
    return out

class Fail(Exception): pass
def check(cond, msg):
    if not cond: raise Fail(msg)

class Based:
    """based cyclic system: n inputs (units), rows (outputs) list, S values, T triples (tuples of values)"""
    def __init__(self, n, rows, S, T):
        self.n, self.rows, self.S, self.T = n, list(rows), list(S), [tuple(t) for t in T]
        self.m = len(rows)
        self.units = [1 << i for i in range(n)]
        self.unitset = set(self.units)
        self.G = len(self.T)
        self.memb = {v: [] for v in self.S}
        for k, t in enumerate(self.T):
            check(len(set(t)) == 3 and t[0] ^ t[1] ^ t[2] == 0, "bad triple")
            for p in t: self.memb[p].append(k)
        self.rowidx = {}
        for j, r in enumerate(self.rows): self.rowidx.setdefault(r, []).append(j)
        self.bnd = self.unitset | set(self.rows)
    def validate(self):
        S = self.S
        check(len(set(S)) == len(S) and 0 not in S, "values not distinct nonzero")
        check(self.unitset <= set(S) and set(self.rows) <= set(S), "missing units/rows")
        check(self.G == len(S) - self.n, "size mismatch")
        ix = {v: i for i, v in enumerate(S)}
        check(rank_f2([sum(1 << ix[p] for p in t) for t in self.T]) == self.G, "T not independent")
    def D(self, v):
        return len(self.memb[v]) + (v in self.unitset) + len(self.rowidx.get(v, []))
    def adjoint(self):
        """u_k in F_2^m solving the star equations at the non-inputs; o_i at inputs"""
        G = self.G
        eqs = []
        for v in self.S:
            if v in self.unitset: continue
            coef = sum(1 << k for k in self.memb[v])
            rhs = sum(1 << j for j in self.rowidx.get(v, []))
            eqs.append([coef, rhs])
        check(len(eqs) == G, "square")
        piv = {}
        for e in eqs:
            for k, pe in piv.items():
                if (e[0] >> k) & 1: e[0] ^= pe[0]; e[1] ^= pe[1]
            check(e[0] != 0, "star system singular")
            k = e[0].bit_length() - 1
            for kk, pe in piv.items():
                if (pe[0] >> k) & 1: pe[0] ^= e[0]; pe[1] ^= e[1]
            piv[k] = e
        u = [None] * G
        for k, pe in piv.items():
            check(pe[0] == 1 << k, "not reduced")
            u[k] = pe[1]
        o = []
        for i in range(self.n):
            v = 1 << i
            x = 0
            for k in self.memb[v]: x ^= u[k]
            for j in self.rowidx.get(v, []): x ^= 1 << j
            o.append(x)
        return u, o
    def stats(self, u=None):
        if u is None: u, _ = self.adjoint()
        S = self.S
        even = [v for v in S if not par(v)]
        y = sum(1 for t in self.T if all(not par(p) for p in t))
        x = len(even) - y
        h = sum(1 for v in S if par(v) and v not in self.bnd)
        Q = sum(1 for k in range(self.G) if par(u[k]))
        e1 = sum(1 for k, t in enumerate(self.T) if par(u[k]) and all(not par(p) for p in t))
        K = {}
        f = {}
        for v in S:
            Kv = sum(1 for k in self.memb[v] if par(u[k])) + len(self.rowidx.get(v, []))  # z_j odd
            if v in self.unitset:
                _, o = (None, None)
            K[v] = Kv
        _, o = self.adjoint()
        for i in range(self.n):
            K[1 << i] += par(o[i])
        for v in S:
            check(K[v] % 2 == 0, "K odd")
            f[v] = max(0, self.D(v) - 2 - K[v] // 2)
        F = sum(f.values())
        FH = sum(f[v] for v in S if par(v) and v not in self.bnd)
        return dict(x=x, y=y, h=h, Q=Q, e1=e1, K=K, f=f, F=F, FH=FH, u=u, o=o)

def dual(C, split, rng):
    """dual (raw transpose) of a based system; split 'canonical' or 'random'. Returns Based + origins."""
    u, o = C.adjoint()
    n, m, G = C.n, C.m, C.G
    val = {}
    for k in range(G): val[('u', k)] = u[k]
    for j in range(m): val[('z', j)] = 1 << j
    for i in range(n): val[('o', i)] = o[i]
    parent = {}
    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b): parent[find(a)] = find(b)
    tids, origins = [], []
    ndeg2 = 0
    for v in C.S:
        terms = [('u', k) for k in C.memb[v]] + [('z', j) for j in C.rowidx.get(v, [])]
        if v in C.unitset: terms.append(('o', v.bit_length() - 1))
        D = len(terms)
        check(D >= 2, "star with < 2 terms")
        if D == 2:
            check(val[terms[0]] == val[terms[1]], "D=2 values differ"); union(terms[0], terms[1]); ndeg2 += 1; continue
        items = terms[:]
        for step in range(D - 2):
            last = (step == D - 3)
            if split == 'canonical':
                odds = [t for t in items if par(val[t])]
                if len(odds) >= 2: a, b = odds[0], odds[1]
                else:
                    evs = [t for t in items if not par(val[t])]; a, b = evs[0], evs[1]
            else:
                a, b = rng.sample(items, 2)
            items.remove(a); items.remove(b)
            if last:
                c = items[0]
                check(val[a] ^ val[b] == val[c], "star does not sum to zero")
            else:
                c = ('w', v, step); val[c] = val[a] ^ val[b]; items.append(c)
            tids.append((a, b, c)); origins.append(v)
    # classes
    classval = {}
    for vid, vv in val.items():
        r = find(vid)
        if r in classval: check(classval[r] == vv, "merged values differ")
        else: classval[r] = vv
    vals = list(classval.values())
    check(len(vals) == len(set(vals)), "dual values not distinct (not normalized)")
    check(0 not in vals, "zero dual value")
    check(len(vals) == m + G, "dual variable count != m + G")
    T2 = []
    for (a, b, c) in tids:
        ra, rb, rc = find(a), find(b), find(c)
        check(len({ra, rb, rc}) == 3, "cancellation in a dual triple")
        T2.append((classval[ra], classval[rb], classval[rc]))
    Dd = Based(m, o, vals, T2)
    Dd.validate()
    return Dd, origins, ndeg2

def peel_and_W(C):
    """Theorem W: peel; if stuck, F_3 weights with zero column sums on the stuck block must make N_w singular."""
    rem_rows = set(range(C.G)); rem_cols = set(v for v in C.S if v not in C.unitset)
    while True:
        leaf = None
        for v in rem_cols:
            ks = [k for k in C.memb[v] if k in rem_rows]
            if len(ks) == 1: leaf = (v, ks[0]); break
        if leaf is None: break
        rem_cols.discard(leaf[0]); rem_rows.discard(leaf[1])
    if not rem_rows: return 'circuit', None
    cols = sorted(v for v in C.S if v not in C.unitset)
    ci = {v: i for i, v in enumerate(cols)}
    W = [[0] * len(cols) for _ in range(C.G)]
    for k, t in enumerate(C.T):
        for p in t:
            if p in ci: W[k][ci[p]] = 1
    for v in rem_cols:
        ks = [k for k in C.memb[v] if k in rem_rows]
        c = len(ks)
        if c == 0: continue
        check(c >= 2, "stuck block column with one entry")
        ws = [1, 1, 1] + [1 + (i % 2) for i in range(c - 3)] if c % 2 else [1 + (i % 2) for i in range(c)]
        for k, w in zip(ks, ws): W[k][ci[v]] = w
    def rank3(rows):
        rows = [r[:] for r in rows]; r = 0
        for col in range(len(rows[0])):
            p = next((i for i in range(r, len(rows)) if rows[i][col] % 3), None)
            if p is None: continue
            rows[r], rows[p] = rows[p], rows[r]
            inv = 1 if rows[r][col] % 3 == 1 else 2
            rows[r] = [(x * inv) % 3 for x in rows[r]]
            for i in range(len(rows)):
                if i != r and rows[i][col] % 3:
                    fct = rows[i][col]; rows[i] = [(x - fct * y) % 3 for x, y in zip(rows[i], rows[r])]
            r += 1
        return r
    return 'noncircuit', rank3(W)

def test_system(C, rng, counters):
    C.validate()
    n = C.n
    st = C.stats()
    # 1.1: every star has >= 2 terms
    check(all(C.D(v) >= 2 for v in C.S), "1.1 D_v >= 2")
    # (3.1)
    check(sum(C.D(v) - 2 for v in C.S) == C.G, "(3.1)")
    # 1.2
    check(C.G == n + st['x'] + st['y'] + st['h'], "1.2")
    # 2.1: odd-graph components contain inputs, dim span(even) = n - c, x >= n - c
    odd = [v for v in C.S if par(v)]
    parent = {v: v for v in odd}
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for t in C.T:
        op = [p for p in t if par(p)]
        if len(op) == 2: parent[find(op[0])] = find(op[1])
    comps = {}
    for v in odd: comps.setdefault(find(v), []).append(v)
    c = len(comps)
    check(all(any(v in C.unitset for v in comp) for comp in comps.values()), "2.1 component without input")
    even = [v for v in C.S if not par(v)]
    check(rank_f2(even) == n - c, "2.1 dim span(even) != n - c")
    check(st['x'] >= n - c, "2.1 x >= n - c")
    # 6.2 (i)-(iii)
    u = st['u']
    wdeg = {v: 0 for v in odd}
    for k, t in enumerate(C.T):
        op = [p for p in t if par(p)]
        if len(op) == 2 and par(u[k]):
            for p in op: wdeg[p] += 1
    for v in odd:
        if v in C.bnd: check(wdeg[v] % 2 == 1, "6.2(ii)")
        else: check(wdeg[v] == st['K'][v], "6.2(i)")
    check(sum(wdeg.values()) == 2 * (st['Q'] - st['e1']), "6.2(iii)")
    check(st['Q'] % 2 == 0, "Q even")
    xprime = st['Q'] // 2
    H = [v for v in odd if v not in C.bnd]
    check(2 * xprime >= n + sum(st['K'][v] // 2 for v in H) + st['e1'], "6.2(A)")
    check(2 * xprime >= n + sum(C.D(v) - 2 - st['f'][v] for v in H) + st['e1'], "6.2(B) before (4.1)")
    # Theorem W
    kind, r3 = peel_and_W(C)
    if kind == 'noncircuit':
        counters['noncircuit_bases'] += 1
        check(r3 < C.G, "Theorem W: F_3 weighted matrix nonsingular for a non-circuit basis")
    # duals
    for split in ['canonical', 'random', 'random']:
        Dd, origins, nd2 = dual(C, split, rng)
        counters['deg2_stars'] += nd2
        sd = Dd.stats()
        check(Dd.G == C.G, "3.1 dual size")
        check(sd['x'] == st['Q'] // 2, "6.1 x(dual) = Q/2")
        if split == 'canonical': check(sd['y'] == st['F'], "(3.3) y(canonical dual) = F")
        else: check(sd['y'] <= st['F'], "3.2 y(dual) <= F")
        # 7.1: adjoint (in the dual's dual) of a dual triple = origin
        ud = sd['u']
        for k, v in enumerate(origins):
            check(ud[k] == v, "7.1 origin identity")
        if split != 'canonical':
            counters['random_dual_odd_fanout1'] = counters.get('random_dual_odd_fanout1', 0) + sum(
                1 for w in Dd.S if par(w) and w not in Dd.bnd and len(Dd.memb[w]) == 2)
            counters['random_dual_y_below_F'] = counters.get('random_dual_y_below_F', 0) + (sd['y'] < st['F'])
        if split == 'canonical':
            # 7.4: odd helpers of a canonical dual lie in >= 3 members
            for w in Dd.S:
                if par(w) and w not in Dd.bnd:
                    check(len(Dd.memb[w]) >= 3, "7.4 odd helper with fan-out 1")
            # 8.1: e(T(C)) = sum_{v odd} f_v
            eT = sum(1 for k, t in enumerate(Dd.T) if par(ud[k]) and all(not par(p) for p in t))
            check(eT == sum(st['f'][v] for v in C.S if par(v)), "8.1")
        # 7.2 and 7.3 through the double dual
        for split2 in ['canonical', 'random']:
            DD, _, _ = dual(Dd, split2, rng)
            sdd = DD.stats()
            check(sdd['x'] == st['x'], "7.2 x(TT) = x")
            if split2 == 'canonical': check(sdd['y'] >= st['y'], "7.3 y(TT) >= y")
            counters['double_duals'] += 1
        counters['duals'] += 1
    counters['systems'] += 1
    return st

def orbit(C, rng, steps=12, counters=None):
    ys, xs = [], []
    cur = C
    for j in range(steps):
        s = cur.stats(); ys.append(s['y']); xs.append(s['x'])
        if counters is not None and j > 0 and j < 6:
            test_system(cur, rng, counters)
        cur, _, _ = dual(cur, 'canonical', rng)
    for j in range(steps - 2):
        check(ys[j + 2] >= ys[j], "orbit y(C_j+2) >= y(C_j)")
    for j in range(2, steps):
        check(xs[j] == xs[j - 2], "orbit x alternates")
    return ys, xs

def random_bases(S, n, count, rng):
    Ts = triples(S)
    ix = {v: i for i, v in enumerate(S)}
    G = len(S) - n
    out = set()
    for _ in range(count * 5):
        rng.shuffle(Ts)
        basis, vecs = [], []
        for t in Ts:
            vv = sum(1 << ix[p] for p in t)
            if rank_f2(vecs + [vv]) > len(vecs):
                vecs.append(vv); basis.append(t)
            if len(basis) == G: break
        if len(basis) == G: out.add(tuple(sorted(basis)))
        if len(out) >= count: break
    return [list(b) for b in out]

def min_cyclic_sets(n, rows):
    exe = os.path.join(HERE, 'lmin')
    # find minimal k first
    out = subprocess.run([exe, str(n), '4', '-1'] + [str(r) for r in rows], capture_output=True, text=True).stdout
    kmin = None
    for line in out.splitlines():
        if line.startswith('k='):
            d = dict(kv.split('=') for kv in line.split())
            if int(d['cyclic']) > 0: kmin = int(d['k']); break
    out = subprocess.run([exe, str(n), str(kmin), str(kmin)] + [str(r) for r in rows], capture_output=True, text=True).stdout
    sets = []
    for line in out.splitlines():
        if line.startswith('C'):
            parts = line.split()
            extras = [int(p) for p in parts[1:-1]]
            sets.append((extras, parts[-1]))
    return kmin, sets

if __name__ == '__main__':
    seed = int(sys.argv[1]); per = int(sys.argv[2]); rows = [int(a) for a in sys.argv[3:]]
    n = len(rows)
    rng = random.Random(seed)
    RT = [sum(((rows[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
    counters = dict(systems=0, duals=0, double_duals=0, noncircuit_bases=0, deg2_stars=0)
    for name, R in [('X', rows), ('X^T', RT)]:
        kmin, sets = min_cyclic_sets(n, R)
        print(f"{name}: minimum cyclic sets: {len(sets)} of size {len(set(R) - {1 << i for i in range(n)}) + kmin}; "
              f"circuit sets among them: {sum(1 for _, k in sets if k == 'circ')}", flush=True)
        for extras, kind in sets:
            S = sorted(set([1 << i for i in range(n)] + R + extras))
            for T in random_bases(S, n, per, rng):
                C = Based(n, R, S, T)
                try:
                    test_system(C, rng, counters)
                    orbit(C, rng)
                except Fail as e:
                    print("FAIL", name, extras, e); raise
    print("all checks passed;", counters)
