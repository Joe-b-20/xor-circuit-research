"""Stress test of the order-free ("cyclic") versions of the general lemmas of PROOF.md.

Usage: python3 cyclic_identities.py [SAMPLES] [SEED]

Objects.  A based cyclic system: variables 0..nv-1 (the first n are inputs), a list of triangles
(3-sets of variables, read as "the three values sum to zero"), a list of output variables; the
triangle matrix restricted to the non-input variables must be invertible, so every value is a
determined vector of F_2^n.  No order of the triangles is used anywhere in this file.

Test systems (all have every input and output of odd weight, in both orientations):
  kind "gadget":    random gates mixed with copies of the 6-triangle feedback gadget of the report
                    (q1 = p1+p2+p3 defined only through a loop), gadget variables used by later gates
                    and as outputs; these are not circuits whatever inputs are chosen among the
                    basis triangles' variables;
  kind "reencoded": a circuit of a random invertible matrix A read from its outputs (a cyclic system
                    for A^-1, usually not a circuit for A^-1).
For each system the script builds the dual system (section 3 of PROOF.md without an order: one
dual variable per triangle, one "star" equation per variable, stars split into trees), in a
canonical and in a random splitting, and checks the statements listed in CHECKS below.
It is a test on random small systems, not a proof.
"""
import random
import sys


def odd(x):
    return bin(x).count("1") & 1


def solve(rows, nunk):
    """rows: (lhs bitmask over unknowns, rhs).  Unique solution as a list, or None."""
    piv = {}
    for lhs, rhs in rows:
        while lhs:
            h = lhs.bit_length() - 1
            if h in piv:
                lhs ^= piv[h][0]
                rhs ^= piv[h][1]
            else:
                piv[h] = (lhs, rhs)
                break
        else:
            if rhs:
                return None
    if len(piv) < nunk:
        return None
    sol = {}
    for h in sorted(piv):
        lhs, rhs = piv[h]
        low = lhs ^ (1 << h)
        while low:
            b = low.bit_length() - 1
            rhs ^= sol[b]
            low ^= 1 << b
        sol[h] = rhs
    return [sol[k] for k in range(nunk)]


class Sys:
    def __init__(self, n, nv, tris, outs):
        self.n, self.nv, self.outs = n, nv, list(outs)
        self.tris = [tuple(t) for t in tris]
        self.G = len(self.tris)
        self.inc = [[] for _ in range(nv)]
        for t, tri in enumerate(self.tris):
            for v in tri:
                self.inc[v].append(t)
        self._vals = self._adj = None

    def values(self):
        if self._vals is None:
            rows = []
            for tri in self.tris:
                lhs = rhs = 0
                for v in tri:
                    if v < self.n:
                        rhs ^= 1 << v
                    else:
                        lhs ^= 1 << (v - self.n)
                rows.append((lhs, rhs))
            sol = solve(rows, self.nv - self.n)
            self._vals = None if sol is None else [1 << i for i in range(self.n)] + sol
        return self._vals

    def adjoints(self):
        """u_t in F_2^m: the unique solution of the star equations at the non-input variables."""
        if self._adj is None:
            outidx = {v: j for j, v in enumerate(self.outs)}
            rows = []
            for v in range(self.n, self.nv):
                lhs = 0
                for t in self.inc[v]:
                    lhs ^= 1 << t
                rows.append((lhs, (1 << outidx[v]) if v in outidx else 0))
            self._adj = solve(rows, self.G)
        return self._adj

    def is_circuit_on_basis(self):
        known = [v < self.n for v in range(self.nv)]
        changed = True
        while changed:
            changed = False
            for tri in self.tris:
                k = [v for v in tri if not known[v]]
                if len(k) == 1:
                    known[k[0]] = True
                    changed = True
        return all(known)


def profile(S):
    """Order-free counts of PROOF.md sections 1-4 for a system whose boundary is odd."""
    vals = S.values()
    par = [odd(x) for x in vals]
    bnd = set(range(S.n)) | set(S.outs)
    assert all(par[v] for v in bnd)
    y = 0
    edges = []
    for t, tri in enumerate(S.tris):
        o = [v for v in tri if par[v]]
        assert len(o) in (0, 2)
        if o:
            lab = [v for v in tri if not par[v]][0]
            edges.append((o[0], o[1], lab, t))
        else:
            y += 1
    even = sum(1 for v in range(S.nv) if not par[v])
    h = sum(1 for v in range(S.nv) if par[v] and v not in bnd)
    return dict(par=par, bnd=bnd, y=y, x=even - y, h=h, edges=edges)


def dual(S, mode, rng):
    """Dual system.  Returns (D, origin list, id of each wire, wire values) or None if degenerate."""
    u = S.adjoints()
    if u is None:
        return None
    n, m = S.n, len(S.outs)
    outidx = {v: j for j, v in enumerate(S.outs)}
    val = {}
    for t in range(S.G):
        val[("u", t)] = u[t]
    for j in range(m):
        val[("z", j)] = 1 << j
    for i in range(n):
        x = 0
        for t in S.inc[i]:
            x ^= u[t]
        val[("o", i)] = x
    parent = {}

    def find(w):
        parent.setdefault(w, w)
        while parent[w] != w:
            parent[w] = parent[parent[w]]
            w = parent[w]
        return w

    dtris, stars = [], []
    naux = 0
    for v in range(S.nv):
        ws = [("u", t) for t in S.inc[v]]
        if v in outidx:
            ws.append(("z", outidx[v]))
        if v < n:
            ws.append(("o", v))
        D = len(ws)
        K = sum(odd(val[w]) for w in ws)
        tot = 0
        for w in ws:
            tot ^= val[w]
        assert tot == 0 and K % 2 == 0
        stars.append((D, K))
        if D < 2:
            return None
        if D == 2:
            a, b = find(ws[0]), find(ws[1])
            if a == b:
                return None
            parent[a] = b
            continue
        L = list(ws)
        while len(L) > 3:
            if mode == "canonical":
                odds = [w for w in L if odd(val[w])]
                pool = odds if len(odds) >= 2 else [w for w in L if not odd(val[w])]
            else:
                pool = L
            a, b = rng.sample(pool, 2)
            c = ("a", naux)
            naux += 1
            val[c] = val[a] ^ val[b]
            dtris.append(((a, b, c), v))
            L.remove(a)
            L.remove(b)
            L.append(c)
        dtris.append((tuple(L), v))
    ids = {}
    for j in range(m):
        r = find(("z", j))
        if r in ids:
            return None
        ids[r] = j
    for w in list(val):
        r = find(w)
        if r not in ids:
            ids[r] = len(ids)
    wid = {w: ids[find(w)] for w in val}
    outs = [wid[("o", i)] for i in range(n)]
    if any(o < m for o in outs) or len(set(outs)) < n:
        return None
    tris = []
    for (a, b, c), v in dtris:
        t = (wid[a], wid[b], wid[c])
        if len(set(t)) < 3:
            return None
        tris.append(t)
    D = Sys(m, len(ids), tris, outs)
    return D, [v for _, v in dtris], wid, val, stars


CHECKS = [
    "1.2  G = m + x + y + h with y = #EEE triangles, x = #even variables - y",
    "2.1  every component of the odd graph contains an input; the input blocks of the components are the "
    "partition: a variable has odd weight on block K iff it is odd and lies in component K; x >= n - c",
    "3.1  the dual has G + m - n triangles, as many non-input variables, is uniquely solvable, computes M^T",
    "3.2  #EEE triangles of the dual <= F = sum_v max(0, D_v - 2 - K_v/2), equality for the canonical splitting",
    "6.1  Q = 2 x(dual) for every splitting (Q = triangles with odd adjoint)",
    "6.2  weighted degree = K_v at helpers, K_v - 1 (odd) at boundary vertices; sum = 2(Q - e1); (A); (B)",
    "7.1  the adjoint in the dual of a dual triangle equals the value of its origin",
    "7.2  Q(dual) = 2 x(C)",
    "7.3  F(dual) >= y(C); the canonical double dual has y = F(dual), x = x(C) and computes M",
    "7.4  canonical dual: every odd non-boundary variable lies in >= 3 triangles",
    "8.1  e(canonical dual) = sum of f_v over odd v",
]


def check_system(S, rng, stats):
    vals = S.values()
    n, m = S.n, len(S.outs)
    assert vals is not None and len(set(vals)) == S.nv and 0 not in vals
    M = [vals[o] for o in S.outs]
    P = profile(S)
    par, x, y, h = P["par"], P["x"], P["y"], P["h"]
    # 1.2
    assert S.G == S.nv - n == m + x + y + h
    # 2.1
    comp = list(range(S.nv))

    def find(a):
        while comp[a] != a:
            comp[a] = comp[comp[a]]
            a = comp[a]
        return a

    for p, q, lab, t in P["edges"]:
        comp[find(p)] = find(q)
    roots = sorted(set(find(v) for v in range(S.nv) if par[v]))
    blocks = {r: 0 for r in roots}
    for i in range(n):
        blocks[find(i)] |= 1 << i
    assert all(blocks[r] for r in roots)
    for v in range(S.nv):
        for r in roots:
            assert odd(vals[v] & blocks[r]) == (1 if (par[v] and find(v) == r) else 0)
    assert x >= n - len(roots)
    # duals
    res_c = dual(S, "canonical", rng)
    res_r = dual(S, "random", rng)
    if res_c is None or res_r is None:
        stats["degenerate dual (skipped)"] += 1
        return
    u = S.adjoints()
    Q = sum(odd(a) for a in u)
    e1 = sum(1 for t, tri in enumerate(S.tris) if odd(u[t]) and not any(par[v] for v in tri))
    stars = res_c[4]
    f = [max(0, D - 2 - K // 2) for D, K in stars]
    F = sum(f)
    FH = sum(f[v] for v in range(S.nv) if par[v] and v not in P["bnd"])
    MT = [sum(((M[j] >> i) & 1) << j for j in range(m)) for i in range(n)]
    for kind, res in (("canonical", res_c), ("random", res_r)):
        D, origin, wid, wval, _ = res
        dv = D.values()
        # 3.1
        assert D.G == S.G + m - n == D.nv - m and dv is not None
        assert all(dv[wid[w]] == wval[w] for w in wval)
        assert [dv[o] for o in D.outs] == MT
        PD = profile(D)
        # 3.2
        assert PD["y"] <= F and (kind != "canonical" or PD["y"] == F)
        # 6.1
        assert Q == 2 * PD["x"]
        # 7.1, 7.2
        U = D.adjoints()
        assert all(U[t] == vals[origin[t]] for t in range(D.G))
        assert sum(odd(a) for a in U) == 2 * x
        reduced = len(set(dv)) == D.nv and 0 not in dv
        stats["dual reduced" if reduced else "dual not reduced"] += 1
        if kind == "canonical":
            # 7.4
            for w in range(D.nv):
                if PD["par"][w] and w not in PD["bnd"]:
                    assert len(D.inc[w]) >= 3
            # 8.1
            eD = sum(1 for t, tri in enumerate(D.tris) if odd(U[t]) and not any(PD["par"][v] for v in tri))
            assert eD == sum(f[v] for v in range(S.nv) if par[v])
            # 7.3
            rc = dual(D, "canonical", rng)
            if rc is not None:
                DD, _, _, _, stars2 = rc
                F2 = sum(max(0, d - 2 - k // 2) for d, k in stars2)
                assert F2 >= y
                PDD = profile(DD)
                ddv = DD.values()
                assert PDD["y"] == F2 and PDD["x"] == x and [ddv[o] for o in DD.outs] == M
                stats["double duals built"] += 1
    # 6.2
    wdeg = [0] * S.nv
    for p, q, lab, t in P["edges"]:
        if odd(u[t]):
            wdeg[p] += 1
            wdeg[q] += 1
    sumH = 0
    for v in range(S.nv):
        if not par[v]:
            continue
        D_, K = stars[v]
        if v in P["bnd"]:
            assert wdeg[v] == K - 1 and wdeg[v] % 2 == 1
        else:
            assert wdeg[v] == K
            sumH += K // 2
    assert sum(wdeg) == 2 * (Q - e1)
    assert Q - e1 >= (n + m) // 2 + sumH                                   # (A)
    bb = sum(1 for p, q, lab, t in P["edges"] if p in P["bnd"] and q in P["bnd"])
    z = sum(1 for p, q, lab, t in P["edges"] if p not in P["bnd"] and q not in P["bnd"])
    qq = x + y - bb
    assert Q + h + y + FH >= (n + m) + qq + z + e1                          # (B)
    stats["systems fully checked"] += 1
    if not S.is_circuit_on_basis():
        stats["  of which not a circuit on its basis triangles"] += 1


def prune(n, vals, tris, outs):
    tris = list(tris)
    keep = set(range(len(vals)))
    bnd = set(range(n)) | set(outs)
    while True:
        cnt = {}
        for tri in tris:
            for v in tri:
                cnt[v] = cnt.get(v, 0) + 1
        dead = [v for v in keep if v not in bnd and cnt.get(v, 0) < 2]
        if not dead:
            break
        d = set(dead)
        keep -= d
        tris = [tri for tri in tris if not (set(tri) & d)]
    order = sorted(keep)
    new = {v: i for i, v in enumerate(order)}
    return Sys(n, len(order), [tuple(new[v] for v in tri) for tri in tris], [new[o] for o in outs])


def gen_gadget(rng, n):
    vals = [1 << i for i in range(n)]
    exist = set(vals)
    tris = []

    def gate(a, b):
        v = vals[a] ^ vals[b]
        if v == 0 or v in exist:
            return None
        vals.append(v)
        exist.add(v)
        tris.append((a, b, len(vals) - 1))
        return len(vals) - 1

    def rgates(k, recent=None):
        tries = 0
        while k > 0 and tries < 1000:
            tries += 1
            a = rng.choice(recent) if recent and rng.random() < 0.6 else rng.randrange(len(vals))
            b = rng.randrange(len(vals))
            if a != b and gate(a, b) is not None:
                k -= 1

    def gadget():
        for _ in range(200):
            p = rng.sample(range(len(vals)), 5)
            q1 = vals[p[0]] ^ vals[p[1]] ^ vals[p[2]]
            a = q1 ^ vals[p[3]]
            b = a ^ vals[p[4]]
            c = b ^ vals[p[0]]
            q2 = c ^ vals[p[1]]
            q3 = b ^ vals[p[2]]
            new = [q1, a, b, c, q2, q3]
            if len(set(new)) < 6 or 0 in new or any(v in exist for v in new):
                continue
            base = len(vals)
            vals.extend(new)
            exist.update(new)
            Q1, A, B, C, Q2, Q3 = range(base, base + 6)
            tris.extend([(p[3], Q1, A), (p[4], A, B), (p[0], B, C), (p[1], C, Q2), (p[2], B, Q3), (Q1, Q2, Q3)])
            return list(range(base, base + 6))
        return None

    rgates(rng.randint(n // 2, n))
    gad = []
    for _ in range(rng.randint(1, 2)):
        g = gadget()
        if g is None:
            return None
        gad += g
        rgates(rng.randint(4, 8), recent=g)
    rgates(rng.randint(n // 2, n), recent=gad)
    used = set()
    for a, b, c in tris:
        used.add(a)
        used.add(b)
    cands = [v for v in range(n, len(vals)) if odd(vals[v])]
    if len(cands) < n - 1:
        return None
    sinks = [v for v in cands if v not in used or v in gad]
    rng.shuffle(sinks)
    rest = [v for v in cands if v not in sinks]
    rng.shuffle(rest)
    outs = (sinks + rest)[: n - 1]
    t = (1 << n) - 1
    for o in outs:
        t ^= vals[o]
    if t == 0 or t & (t - 1) == 0 or any(vals[o] == t for o in outs):
        return None
    sup = [i for i in range(n) if (t >> i) & 1]
    cur = sup[0]
    index = {v: i for i, v in enumerate(vals)}
    for i in sup[1:]:
        nvl = vals[cur] ^ (1 << i)
        if nvl in exist:
            cur = index[nvl]
        else:
            cur = gate(cur, i)
            index[nvl] = cur
    if cur in outs or cur < n:
        return None
    outs.append(cur)
    return prune(n, vals, tris, outs)


def gen_reencoded(rng, n):
    while True:
        rows = [sum(1 << j for j in rng.sample(range(n), rng.choice([3, 3, 5]))) for _ in range(n)]
        if len(set(rows)) < n:
            continue
        if any(sum((r >> j) & 1 for r in rows) % 2 == 0 for j in range(n)):
            continue
        # invertible?
        if solve([(r, 0) for r in rows], n) is not None:
            break
    vals = [1 << i for i in range(n)]
    index = {v: i for i, v in enumerate(vals)}
    tris = []
    outs = []
    for r in rows:
        sup = [i for i in range(n) if (r >> i) & 1]
        rng.shuffle(sup)
        cur = sup[0]
        for i in sup[1:]:
            nvl = vals[cur] ^ (1 << i)
            if nvl in index:
                cur = index[nvl]
            else:
                vals.append(nvl)
                index[nvl] = len(vals) - 1
                tris.append((cur, i, len(vals) - 1))
                cur = len(vals) - 1
        outs.append(cur)
    C = prune(n, vals, tris, outs)
    # read from the outputs: new inputs = old outputs, new outputs = old inputs
    perm = {}
    for j, o in enumerate(C.outs):
        perm[o] = j
    nxt = n
    for v in range(C.nv):
        if v not in perm:
            perm[v] = nxt
            nxt += 1
    return Sys(n, C.nv, [tuple(perm[v] for v in tri) for tri in C.tris], [perm[i] for i in range(n)])


def main():
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    for kind, gen in (("gadget", gen_gadget), ("reencoded", gen_reencoded)):
        stats = {k: 0 for k in ["systems fully checked", "  of which not a circuit on its basis triangles",
                                "degenerate dual (skipped)", "dual reduced", "dual not reduced",
                                "double duals built"]}
        done = tried = 0
        sizes = []
        while done < samples and tried < 50 * samples:
            tried += 1
            n = rng.choice([6, 8, 10]) if kind == "gadget" else rng.choice([6, 7, 8, 9])
            S = gen(rng, n)
            if S is None or S.values() is None:
                continue
            v = S.values()
            if len(set(v)) < S.nv or 0 in v or not all(odd(v[o]) for o in S.outs):
                continue
            before = stats["systems fully checked"]
            check_system(S, rng, stats)
            if stats["systems fully checked"] > before:
                done += 1
                sizes.append(S.G)
        print("kind %-9s: generated %d, triangles per system %d..%d" % (kind, tried, min(sizes), max(sizes)))
        for k, v in stats.items():
            print("    %-48s %d" % (k, v))
    print("all assertions passed; statements checked:")
    for c in CHECKS:
        print("   ", c)


if __name__ == "__main__":
    main()
