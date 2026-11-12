"""Reviewer checks for causal/REPORT.md (sections 1-3).  Inspection of recorded circuits and of
randomly constructed based cyclic systems; no search, no SAT.  Nothing here proves a universal claim.

usage: python3 review_causal.py [NRANDOM] [SEED]
"""
import random
import sys
from itertools import combinations

from rp_lib import (ROOT, all_triples, derivations, executable, load_matrix, load_ncff, load_txt,
                    popcount, qm_rows, rank, values)

ROT = ROOT + "/research/structure-2026-11-11/rotation/circuits/"
MC = ROOT + "/circuits/aes-mixcolumns/"


# ------------------------------------------------------------------ models
class Model:
    def __init__(self, name, n, rows, block_of_input, sheet_of_row, nsheets):
        self.name, self.n, self.rows = name, n, rows
        self.nsheets = nsheets
        self.blockmask = [0] * nsheets
        for i in range(n):
            self.blockmask[block_of_input[i]] |= 1 << i
        self.sheet_of_row = sheet_of_row
        # block support of each sheet
        self.supp = []
        for j in range(nsheets):
            s = set()
            for r, row in enumerate(rows):
                if sheet_of_row[r] == j:
                    for k in range(nsheets):
                        if row & self.blockmask[k]:
                            s.add(k)
            self.supp.append(s)

    def blocks_of(self, v):
        return {k for k in range(self.nsheets) if v & self.blockmask[k]}

    def adjacent(self, j, k):
        return j != k and (k in self.supp[j] or j in self.supp[k])

    def independent_families(self):
        out = []
        for size in range(1, self.nsheets + 1):
            for J in combinations(range(self.nsheets), size):
                if all(not self.adjacent(a, b) for a, b in combinations(J, 2)):
                    out.append(J)
        return out


def qm_model(m):
    n = 4 * m
    return Model("Q%d" % m, n, qm_rows(m), [i // 4 for i in range(n)], [r // 4 for r in range(4 * m)], m)


def mc_model():
    rows = load_matrix(MC + "aes-mixcolumns.mat.txt")
    # output y_(8c+j): sheet j = bit position; input x_(8c+j): block j
    return Model("MC", 32, rows, [i % 8 for i in range(32)], [r % 8 for r in range(32)], 8)


# ------------------------------------------------------------------ based system helpers
def based_from_circuit(n, gates):
    S = values(n, gates)
    assert len(set(S)) == len(S) and 0 not in S, "values not distinct nonzero"
    T = [tuple(sorted((n + gi, a, b))) for gi, (a, b) in enumerate(gates)]
    return S, T


def output_index(S, rows):
    pos = {v: i for i, v in enumerate(S)}
    return [pos[r] for r in rows]


def lam(model, S, T, n, outs, deriv, J):
    """Lam_J: triples in T_o for an output o of a sheet in J, live on the own blocks of J."""
    own = 0
    for j in J:
        own |= model.blockmask[j]
    inT = 0
    for r, o in enumerate(outs):
        if model.sheet_of_row[r] in J:
            inT |= deriv[o]
    res = []
    for ti, t in enumerate(T):
        if (inT >> ti) & 1 and sum(1 for x in t if S[x] & own) >= 2:
            res.append(ti)
    return res, own


def projection_check(model, S, T, n, outs, deriv, J):
    """Naive projection: equations Lam_J, unknowns = non-input members nonzero on own blocks.
    Returns (|Lam_J|, |U'|, rank of incidence) and the result of the repaired construction."""
    L, own = lam(model, S, T, n, outs, deriv, J)
    targets = [o for r, o in enumerate(outs) if model.sheet_of_row[r] in J]
    U = sorted({x for ti in L for x in T[ti] if x >= n and S[x] & own} | set(targets))
    col = {x: k for k, x in enumerate(U)}
    N = []
    for ti in L:
        v = 0
        for x in T[ti]:
            if x in col:
                v |= 1 << col[x]
        N.append(v)
    rk = rank(N)
    # ---- repaired construction: row basis Lam', column basis U* containing the targets
    basis_rows, bas = [], {}
    for ti, v in zip(L, N):
        w = v
        while w:
            h = w.bit_length() - 1
            if h in bas:
                w ^= bas[h]
            else:
                bas[h] = w
                basis_rows.append((ti, v))
                break
    rowspace = [v for _, v in basis_rows]
    # choose columns: start with targets, extend greedily so that the projection of the row space is injective
    # (column set C is independent in the column matroid iff the coordinate projection of the row space onto C is onto)
    chosen = []

    def proj_rank(cols):
        mask = sum(1 << col[c] for c in cols)
        return rank([v & mask for v in rowspace])

    for c in targets:
        chosen.append(c)
    assert proj_rank(chosen) == len(chosen), "targets not independent in column matroid"
    for c in U:
        if len(chosen) == len(rowspace):
            break
        if c in chosen:
            continue
        if proj_rank(chosen + [c]) == len(chosen) + 1:
            chosen.append(c)
    assert len(chosen) == len(rowspace)
    cmask = sum(1 << col[c] for c in chosen)
    # local system: unknowns = chosen; equation for each row of Lam': sum of chosen members = c_t
    # c_t = sum of values of members not in U' (base units and free members); off-U* unknowns dropped (set 0)
    eqs = []
    for ti, _ in basis_rows:
        unk = [x for x in T[ti] if x in col and col[x] in [col[c] for c in chosen]]
        known = [x for x in T[ti] if x not in col]
        cval = 0
        for x in known:
            cval ^= S[x]
        eqs.append((unk, cval))
    # solve
    idx = {c: k for k, c in enumerate(chosen)}
    rows = []
    for unk, cval in eqs:
        m = 0
        for x in unk:
            m |= 1 << idx[x]
        rows.append([m, cval])
    K = len(rows)
    for colk in range(K):
        p = next((i for i in range(colk, K) if (rows[i][0] >> colk) & 1), None)
        if p is None:
            return len(L), len(U), rk, ("SINGULAR", None)
        rows[colk], rows[p] = rows[p], rows[colk]
        for i in range(K):
            if i != colk and (rows[i][0] >> colk) & 1:
                rows[i][0] ^= rows[colk][0]
                rows[i][1] ^= rows[colk][1]
    sol = {chosen[k]: rows[k][1] for k in range(K)}
    ok = all(sol[o] == S[o] for o in targets)
    # sanity of the local-system form: every equation has <= 3 variables (unknowns + base units), phi free
    form_ok = True
    for ti, _ in basis_rows:
        t = T[ti]
        nonzero_own = [x for x in t if S[x] & own]
        free = [x for x in t if not (S[x] & own)]
        if len(free) > 1:
            form_ok = False
    return len(L), len(U), rk, (K, ok and form_ok)


def wire_charges(model, n, gates, S, outs, j):
    """D_j: gates that are ancestors-or-equal of an output gate of sheet j and nonzero on block j."""
    anc = set()
    stack = [o for r, o in enumerate(outs) if model.sheet_of_row[r] == j]
    while stack:
        v = stack.pop()
        if v in anc or v < n:
            continue
        anc.add(v)
        a, b = gates[v - n]
        stack += [a, b]
    return {g for g in anc if S[g] & model.blockmask[j]}


def path_parity_check(n, gates, S, outs, deriv):
    """In a circuit, t in T_o iff the number of wire paths from the result of t to o is odd."""
    G = len(gates)
    readers = {}
    for gi, (a, b) in enumerate(gates):
        readers.setdefault(a, []).append(n + gi)
        readers.setdefault(b, []).append(n + gi)
    for o in outs:
        P = {}
        for v in range(n + G - 1, n - 1, -1):
            p = 1 if v == o else 0
            for r in readers.get(v, []):
                p ^= P[r]
            P[v] = p
        # gate triple index of gate v is v - n
        mask = sum(1 << (v - n) for v in range(n, n + G) if P[v])
        if mask != deriv[o]:
            return False
    return True


def block_monotone(model, n, gates, S, outs):
    viol = 0
    for r, o in enumerate(outs):
        anc, stack = set(), [o]
        while stack:
            v = stack.pop()
            if v in anc or v < n:
                continue
            anc.add(v)
            stack += list(gates[v - n])
        for g in anc:
            if S[g] & ~S[o] and any((S[g] & model.blockmask[k]) and not (S[o] & model.blockmask[k])
                                    for k in range(model.nsheets)):
                viol += 1
                break
    return viol == 0


def lemma23_check(model, S, T, n, outs, deriv, J):
    """Build the repaired local system for family J, then run Lemma 2.3's construction on it
    (Step 0 cleaning, formal inputs, dual, S*) and test (1)-(3) and the intermediate claims of
    Theorem 2.4's proof.  Returns a dict of results."""
    L, own = lam(model, S, T, n, outs, deriv, J)
    targets = [o for r, o in enumerate(outs) if model.sheet_of_row[r] in J]
    U = sorted({x for ti in L for x in T[ti] if x >= n and S[x] & own} | set(targets))
    col = {x: k for k, x in enumerate(U)}
    N = []
    for ti in L:
        v = 0
        for x in T[ti]:
            if x in col:
                v |= 1 << col[x]
        N.append(v)
    basis_rows, bas = [], {}
    for ti, v in zip(L, N):
        w = v
        while w:
            h = w.bit_length() - 1
            if h in bas:
                w ^= bas[h]
            else:
                bas[h] = w
                basis_rows.append((ti, v))
                break
    rowspace = [v for _, v in basis_rows]

    def proj_rank(cols):
        mask = sum(1 << col[c] for c in cols)
        return rank([v & mask for v in rowspace])

    chosen = list(targets)
    for c in U:
        if len(chosen) == len(rowspace):
            break
        if c not in chosen and proj_rank(chosen + [c]) == len(chosen) + 1:
            chosen.append(c)
    chosen_set = set(chosen)
    # equations as (list of variables, phi); variables: ('y', idx) unknown, ('b', input index) own unit
    eqs = []
    for ti, _ in basis_rows:
        vars_, phi = [], 0
        for x in T[ti]:
            if x in chosen_set:
                vars_.append(("y", x))
            elif x < n and S[x] & own:
                vars_.append(("b", x))
            elif S[x] & own:
                pass  # dropped unknown (set to 0)
            else:
                phi ^= S[x]
        eqs.append([vars_, phi])
    unknowns = set(("y", x) for x in chosen)
    tgt = set(("y", o) for o in targets)
    K0 = len(eqs)
    # ---- Step 0
    changed = True
    while changed:
        changed = False
        for e in list(eqs):
            ys = [v for v in e[0] if v[0] == "y"]
            if len(e[0]) == 1 and ys:
                y = ys[0]
                if y in tgt:
                    return {"error": "target with free value"}
                val = e[1]
                eqs.remove(e)
                unknowns.discard(y)
                for f in eqs:
                    if y in f[0]:
                        f[0].remove(y)
                        f[1] ^= val
                changed = True
                break
        if changed:
            continue
        cnt = {}
        for e in eqs:
            for v in e[0]:
                if v[0] == "y":
                    cnt[v] = cnt.get(v, 0) + 1
        for y in list(unknowns):
            if y not in tgt and cnt.get(y, 0) == 1:
                e = next(f for f in eqs if y in f[0])
                eqs.remove(e)
                unknowns.discard(y)
                changed = True
                break
    K = len(eqs)
    assert len(unknowns) == K
    # ---- Step 1: formal inputs on two-variable equations
    base_list = sorted({v[1] for e in eqs for v in e[0] if v[0] == "b"})
    bpos = {b: i for i, b in enumerate(base_list)}
    two = [i for i, e in enumerate(eqs) if len(e[0]) == 2]
    tau = len(two)
    zpos = {ei: i for i, ei in enumerate(two)}
    p = len(base_list)
    ulist = sorted(unknowns)
    upos = {y: i for i, y in enumerate(ulist)}
    # equation rows over unknowns, rhs formal mask over (base | z)
    rows = []
    for ei, e in enumerate(eqs):
        m, rhs = 0, 0
        for v in e[0]:
            if v[0] == "y":
                m |= 1 << upos[v]
            else:
                rhs |= 1 << bpos[v[1]]
        if ei in zpos:
            rhs |= 1 << (p + zpos[ei])
        rows.append([m, rhs, 1 << ei])
    # Gauss-Jordan: formal masks of unknowns and combination giving each unit
    R = [list(r) for r in rows]
    piv = {}
    used = [False] * K
    for c in range(K):
        pr = next((i for i in range(K) if not used[i] and (R[i][0] >> c) & 1), None)
        if pr is None:
            return {"error": "singular after cleaning"}
        used[pr] = True
        for i in range(K):
            if i != pr and (R[i][0] >> c) & 1:
                for k in range(3):
                    R[i][k] ^= R[pr][k]
        piv[c] = pr
    formal = {ulist[c]: R[piv[c]][1] for c in range(K)}
    combo = {ulist[c]: R[piv[c]][2] for c in range(K)}
    tg = [("y", o) for o in targets]
    r = len(tg)
    # check beta of targets: formal base part = E_c pattern, and Phi n = alpha
    # dual: u_e in F2^r, bit c = [e in combo(target c)]
    u = [0] * K
    for c, y in enumerate(tg):
        cm = combo[y]
        for ei in range(K):
            if (cm >> ei) & 1:
                u[ei] |= 1 << c
    # P columns: o_i = sum of u over equations containing base i
    Pcol = [0] * p
    for ei, e in enumerate(eqs):
        for v in e[0]:
            if v[0] == "b":
                Pcol[bpos[v[1]]] ^= u[ei]
    # check P column = targets containing base i (formal base masks)
    pcheck = all(Pcol[i] == sum(((formal[y] >> i) & 1) << c for c, y in enumerate(tg)) for i in range(p))
    zeta = [u[ei] for ei in two]
    # stars and splitting values
    vals = set()
    n3 = 0
    p2 = 0
    for y in ulist:
        terms = [u[ei] for ei, e in enumerate(eqs) if y in e[0]]
        if y in tg:
            terms.append(1 << tg.index(y))
        D = len(terms)
        assert D >= 2
        if D >= 3:
            n3 += D - 2
            acc = terms[0]
            for t in terms[1:-2]:
                acc ^= t
                vals.add(acc)
        for t in terms:
            vals.add(t)
    for b in base_list:
        terms = [u[ei] for ei, e in enumerate(eqs) if ("b", b) in e[0]]
        terms.append(Pcol[bpos[b]])
        D = len(terms)
        p2 += 1
        if D >= 3:
            n3 += D - 2
            acc = terms[0]
            for t in terms[1:-2]:
                acc ^= t
                vals.add(acc)
        for t in terms:
            vals.add(t)
    units = [1 << c for c in range(r)]
    Sstar = sorted(set(units) | {v for v in vals if v})
    Sstar = units + [v for v in Sstar if v not in units]
    # cyclicity of S*
    tri = all_triples(Sstar)
    relrows = []
    for t in tri:
        relrows.append(sum(1 << x for x in t))
    cyc = rank(relrows) == len(Sstar) - rank(Sstar)
    pprime = sum(1 for c in Pcol if c)
    count_formula = K - tau + r - p2
    # (1)
    c1 = all((c in Sstar) for c in Pcol if c)
    # (2): columns of alpha matrix in span(zeta)
    alphas = []
    for y in tg:
        o = y[1]
        alphas.append(S[o] & ~own)
    freebits = 0
    for a in alphas:
        freebits |= a
    from rp_lib import in_span
    c2 = True
    k = freebits
    while k:
        hb = k.bit_length() - 1
        k ^= 1 << hb
        colv = sum(((alphas[c] >> hb) & 1) << c for c in range(r))
        if colv and not in_span(zeta, colv):
            c2 = False
    c3 = K >= tau + (len(Sstar) - r) + (pprime - r)
    res = dict(K0=K0, K=K, tau=tau, r=r, Sstar=len(Sstar), n3=n3, formula=count_formula, cyclic=cyc,
               c1=c1, c2=c2, c3=c3, pcheck=pcheck, lam=len(L))
    # ---- Theorem 2.4 intermediate claims (quads = targets grouped by sheet)
    quads = {}
    for c, y in enumerate(tg):
        rr = outs.index(y[1])
        quads.setdefault(model.sheet_of_row[rr], []).append(c)
    qmask = {j: sum(1 << c for c in cs) for j, cs in quads.items()}
    kq = len(quads)
    # Lemma 2.2 partition: join odd elements whose sum is in S*
    Sset = set(Sstar)
    odd = [v for v in Sstar if popcount(v) % 2]
    parent = {v: v for v in odd}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in combinations(odd, 2):
        if (a ^ b) in Sset:
            parent[find(a)] = find(b)
    blk = {}
    for c in range(r):
        blk.setdefault(find(1 << c), []).append(c)
    blocks = list(blk.values())
    bm = [sum(1 << c for c in b) for b in blocks]
    quad_ok = all(sum(1 for b in bm if b & qm_) <= 2 for qm_ in qmask.values())
    targets_dual = {Pcol[i] for i in range(p) if Pcol[i]}
    ev = [v for v in Sstar if popcount(v) % 2 == 0]
    helpers = [v for v in Sstar if popcount(v) % 2 and v not in units and v not in targets_dual]
    pure_odd = set(units) | targets_dual
    I = set()
    for z in zeta:
        if z and z in pure_odd:
            for j, qm_ in qmask.items():
                if z & qm_:
                    I.add(j)
    a_ok = tau >= 3 * kq + len(I)
    b_ok = len(ev) + len(helpers) >= 3 * kq - len(I)
    res.update(quads=kq, quad_le2=quad_ok, I=len(I), a_ok=a_ok, b_ok=b_ok, ten=K >= 10 * kq,
               dual_targets=len(targets_dual))
    return res


def analyse_circuit(model, path, families="singles"):
    if path.endswith(".circ.txt"):
        n, gates, _ = load_ncff(path)
    else:
        n, gates = load_txt(path)
    S, T = based_from_circuit(n, gates)
    G = len(gates)
    outs = output_index(S, model.rows)
    tri = all_triples(S)
    print(f"== {path.split('/')[-1]}: n={n} G={G} |S|-n={len(S)-n} collinear triples={len(tri)} "
          f"(gate triples are {len(set(T) & set(tri))} of them)")
    deriv = derivations(S, n, T)
    print(f"   T_o equals odd-path-parity set for every output: {path_parity_check(n, gates, S, outs, deriv)}")
    print(f"   block-monotone: {block_monotone(model, n, gates, S, outs)}")
    D = [wire_charges(model, n, gates, S, outs, j) for j in range(model.nsheets)]
    mu = {}
    for j in range(model.nsheets):
        for g in D[j]:
            mu[g] = mu.get(g, 0) + 1
    lams = [lam(model, S, T, n, outs, deriv, (j,))[0] for j in range(model.nsheets)]
    print(f"   wire charges |D_j| = {[len(d) for d in D]} sum {sum(len(d) for d in D)}; "
          f"#mu=2: {sum(1 for v in mu.values() if v == 2)}, #mu>=3: {sum(1 for v in mu.values() if v >= 3)}")
    print(f"   dual charges |Lam_j| = {[len(l) for l in lams]} sum {sum(len(l) for l in lams)}")
    fams = [(j,) for j in range(model.nsheets)]
    if families == "all":
        fams = model.independent_families()
    bad = []
    for J in fams:
        nl, nu, rk, (K, ok) = projection_check(model, S, T, n, outs, deriv, J)
        if not (nl == nu == rk):
            bad.append((J, nl, nu, rk))
        if not ok:
            print(f"   REPAIRED CONSTRUCTION FAILED for J={J}")
    print(f"   families tested: {len(fams)}; naive projection (Lam_J x U') not square-invertible for "
          f"{len(bad)}: {bad[:6]}")
    return n, gates, S, T, outs, deriv, tri


def q3_details(model, n, gates, S, T, outs):
    def show(v):
        parts = []
        for k in range(model.nsheets):
            b = (v & model.blockmask[k]) >> (4 * k)
            if b:
                parts.append(f"{k}:{b:04b}"[::-1] if False else f"{k}:{''.join(str((b >> c) & 1) for c in range(4))}")
        return "[" + " ".join(parts) + "]"

    o12 = outs[4 * 2 + 1]
    print(f"   OUT(1,2) = {show(S[o12])}; triples of S containing it:")
    for t in all_triples(S):
        if o12 in t:
            print("     ", [("in%d" % x if x < n else "g%d" % (x - n)) + show(S[x]) for x in t])


def random_cyclic(model, n, gates, S0, rng, ntrials, families, label):
    """Add a random vector (sum of 2 random elements, not already present) to a circuit value set, take
    random triple bases, keep the cyclic ones; test Lam_J >= 10|J|, naive projection, repaired
    construction and Lemma 2.3 on them, separately for executable and non-executable bases."""
    stats = dict(systems=0, nonexec=0, lam_viol=0, naive_bad=0, naive_bad_nonexec=0, rep_fail=0, l23_fail=0,
                 l23_runs=0)
    rowsset = set(model.rows)
    example = None
    for trial in range(ntrials):
        a, b = rng.sample(range(len(S0)), 2)
        v = S0[a] ^ S0[b] ^ (S0[rng.randrange(len(S0))] if rng.random() < 0.5 else 0)
        if v == 0 or v in S0:
            continue
        S = S0 + [v]
        tri = all_triples(S)
        G = len(S) - n
        for _ in range(4):
            rng.shuffle(tri)
            chosen, bas = [], {}
            for t in tri:
                w = sum(1 << (x - n) for x in t if x >= n)
                ww = w
                while ww:
                    h = ww.bit_length() - 1
                    if h in bas:
                        ww ^= bas[h]
                    else:
                        bas[h] = ww
                        chosen.append(t)
                        break
                if len(chosen) == G:
                    break
            if len(chosen) < G:
                break  # not cyclic
            T = chosen
            deriv = derivations(S, n, T)
            outs = output_index(S, model.rows)
            ex = executable(S, n, T)
            stats["systems"] += 1
            if not ex:
                stats["nonexec"] += 1
            for J in families:
                L, _ = lam(model, S, T, n, outs, deriv, J)
                if len(L) < 10 * len(J):
                    stats["lam_viol"] += 1
                nl, nu, rk, (K, ok) = projection_check(model, S, T, n, outs, deriv, J)
                if not (nl == nu == rk):
                    stats["naive_bad"] += 1
                    if not ex:
                        stats["naive_bad_nonexec"] += 1
                        if example is None:
                            example = (J, nl, nu, rk)
                if not ok:
                    stats["rep_fail"] += 1
                if not ex or rng.random() < 0.1:
                    res = lemma23_check(model, S, T, n, outs, deriv, J)
                    stats["l23_runs"] += 1
                    if "error" in res or not (res["cyclic"] and res["c1"] and res["c2"] and res["c3"]
                                              and res["pcheck"] and res["n3"] == res["formula"]
                                              and res["quad_le2"] and res["a_ok"] and res["b_ok"]
                                              and res["ten"]):
                        stats["l23_fail"] += 1
                        print("     lemma 2.3 check failed:", J, res)
    print(f"   random cyclic systems from {label}: {stats}; first non-executable naive failure: {example}")


def main():
    nrand = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    q3 = qm_model(3)
    n, gates, S, T, outs, deriv, tri = analyse_circuit(q3, ROT + "q3_28.txt")
    q3_details(q3, n, gates, S, T, outs)
    for J in [(0,), (1,), (2,)]:
        print("   lemma 2.3 on repaired local system, J =", J, lemma23_check(q3, S, T, n, outs, deriv, J))
    random_cyclic(q3, n, gates, S, rng, nrand, [(0,), (1,), (2,)], "Q3 28")

    q4 = qm_model(4)
    n4, g4, S4, T4, o4, d4, _ = analyse_circuit(q4, ROT + "q4_40.txt", "all")
    for J in [(0, 2), (1, 3)]:
        print("   lemma 2.3, J =", J, lemma23_check(q4, S4, T4, n4, o4, d4, J))
    analyse_circuit(qm_model(8), ROT + "q8_80.txt", "all")

    mc = mc_model()
    fam = mc.independent_families()
    print(f"MixColumns: adjacency supports {mc.supp}; independent families (nonempty): {len(fam)}; "
          f"largest: {[J for J in fam if len(J) == max(len(x) for x in fam)]}")
    nm, gm, Sm, Tm, om, dm, _ = analyse_circuit(mc, MC + "aes-mixcolumns-xor88-depth5.circ.txt", "all")
    for J in [(0, 2, 4, 6), (1, 3, 5), (1, 4, 6), (7,)]:
        print("   lemma 2.3, J =", J, lemma23_check(mc, Sm, Tm, nm, om, dm, J))
    random_cyclic(mc, nm, gm, Sm, rng, nrand // 3, [(0, 2, 4, 6), (1, 3, 5), (3,), (1, 4, 6)], "MC 88")
    analyse_circuit(mc, MC + "aes-mixcolumns-xor89-depth4.circ.txt", "all")


if __name__ == "__main__":
    main()
