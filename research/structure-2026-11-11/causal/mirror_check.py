"""Instance check of the algebra used in the proof of the joint local lemma (report section 2).

usage: python3 mirror_check.py M FILE J        e.g.  python3 mirror_check.py 8 ../rotation/circuits/q8_80.txt 0,2,4,6

Takes a recorded circuit for Q_M and a family J of pairwise non-adjacent sheets, forms the local system of
the proof of the joint charge theorem (restriction to the blocks j-1, j for j in J; unknowns = the gates
that are ancestors of the outputs of J and nonzero on a block of J), and then follows the proof step by
step, asserting every identity and inequality it uses on this instance:
  step 0  cleaning;   step 1  formal inputs z_i for the tau entry equations;
  step 2  the vectors zeta_i span all vectors that are even on every quad;
  step 3  dual system: star identities, number of three-variable equations = K - tau,
          the set S* of distinct nonzero dual values is cyclic and |S*| - 4k <= K - tau;
  step 4  parity blocks of S*: every quad meets at most two blocks; span(even elements) = within-block
          even space;  dim X >= 3k - |I|,  tau >= 3k + |I|,  K >= 10k.
This verifies the bookkeeping of the proof on one object.  It proves nothing universal and searches nothing.
"""
import os
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402


def rank(vecs):
    return qm.rank(list(vecs))


def in_span(basis_vecs, v):
    return rank(list(basis_vecs) + [v]) == rank(basis_vecs)


def main():
    m = int(sys.argv[1])
    path = sys.argv[2]
    J = [int(x) for x in sys.argv[3].split(",")]
    k = len(J)
    for a, b in combinations(J, 2):
        assert (a - b) % m not in (1, m - 1), "J must not contain adjacent sheets"
    n, gates = qm.read_circuit(path)
    targets = qm.rows(m)
    vals = qm.masks(n, gates)
    G = len(gates)
    first = {}
    for i in range(n, n + G):
        first.setdefault(vals[i], i)
    bmask = 0                       # coordinates of the own blocks (b-blocks) of J
    amask = 0
    for j in J:
        bmask |= 15 << (4 * j)
        amask |= 15 << (4 * ((j - 1) % m))
    keep = bmask | amask
    rv = [v & keep for v in vals]   # restricted values
    tl = [(j, c) for j in J for c in range(4)]
    carrier = [first[targets[4 * j + c]] for j, c in tl]
    # ancestors of the outputs of J
    anc = set()
    stack = list(carrier)
    while stack:
        s = stack.pop()
        if s < n or s in anc:
            continue
        anc.add(s)
        stack.extend(gates[s - n])
    D = sorted(g for g in anc if rv[g] & bmask)
    Dset = set(D)
    # formal local system: equation = (set of variables, phi).  variables: b-units (inputs in bmask) and D gates
    def nonfree(s):
        return (s < n and (vals[s] & bmask)) or (s in Dset)

    eqs = []
    for g in D:
        var = {g}
        phi = 0
        for s in gates[g - n]:
            if nonfree(s):
                var ^= {s}
            else:
                assert rv[s] & bmask == 0
                phi ^= rv[s]
        eqs.append((frozenset(var), phi, g))
    K0 = len(eqs)
    tset = set(carrier)
    assert tset <= Dset
    # step 0: cleaning
    changed = True
    removed = set()
    while changed:
        changed = False
        for e in list(eqs):
            var, phi, g = e
            unk = [v for v in var if v >= n]
            if len(var) == 1 and unk:                      # (i) a single variable: its value is free
                y = unk[0]
                assert y not in tset
                eqs.remove(e)
                eqs = [((v2 - {y}), p2 ^ (phi if y in v2 else 0), g2) for v2, p2, g2 in eqs]
                removed.add(y)
                changed = True
                break
        if changed:
            continue
        occ = {}
        for var, phi, g in eqs:
            for v in var:
                if v >= n:
                    occ.setdefault(v, []).append((var, phi, g))
        for y, lst in occ.items():
            if y not in tset and len(lst) == 1:            # (ii) a non-target unknown in exactly one equation
                eqs.remove(lst[0])
                removed.add(y)
                changed = True
                break
    K = len(eqs)
    unknowns = sorted({v for var, _, _ in eqs for v in var if v >= n})
    assert len(unknowns) == K, (len(unknowns), K)
    assert all(2 <= len(var) <= 3 for var, _, _ in eqs)
    assert all(phi == 0 for var, phi, _ in eqs if len(var) == 3)
    # step 1: formal inputs
    entries = [i for i, (var, _, _) in enumerate(eqs) if len(var) == 2]
    tau = len(entries)
    zidx = {ei: z for z, ei in enumerate(entries)}
    # formal values (beta | n): solve the triangular system in circuit order (each equation is owned by its gate g)
    bunits = sorted(i for i in range(n) if vals[i] & bmask)
    bpos = {b: i for i, b in enumerate(bunits)}
    fval = {b: (1 << bpos[b], 0) for b in bunits}
    own = {}
    for i, (var, phi, g) in enumerate(eqs):
        own[g] = i
    assert set(own) == set(unknowns)
    for g in unknowns:                                        # increasing index = creation order
        i = own[g]
        var, phi, _ = eqs[i]
        be, ne = 0, 0
        for v in var:
            if v != g:
                be ^= fval[v][0]
                ne ^= fval[v][1]
        if i in zidx:
            ne ^= 1 << zidx[i]
        fval[g] = (be, ne)
    # Phi n = a-part, beta = b-part
    for g in unknowns:
        be, ne = fval[g]
        b_true = sum(1 << bpos[b] for b in bunits if rv[g] & vals[b])
        assert be == b_true
        a = 0
        for i in entries:
            if (ne >> zidx[i]) & 1:
                a ^= eqs[i][1]
        assert a == rv[g] & amask, "Phi n(g) must be the a-part"
    # step 2
    zeta = [0] * tau
    for ti, cg in enumerate(carrier):
        ne = fval[cg][1]
        for z in range(tau):
            if (ne >> z) & 1:
                zeta[z] |= 1 << ti
    quads = [sum(1 << (4 * q + c) for c in range(4)) for q in range(k)]
    even_basis = []
    for q in range(k):
        for c in range(3):
            even_basis.append((1 << (4 * q + c)) | (1 << (4 * q + c + 1)))
    assert all(in_span(zeta, v) for v in even_basis), "span(zeta) must contain every vector even on each quad"
    # step 3: dual solution u_t (bitmask over the 4k targets), by reverse order
    u = {}
    for g in reversed(unknowns):
        x = 0
        for var, _, g2 in eqs:
            if g in var and g2 != g:
                x ^= u[g2]
        if g in tset:
            x ^= 1 << carrier.index(g)
        u[g] = x                                             # u of the equation owned by g
    for b in bunits:                                         # star at a b-unit: column of the beta matrix
        x = 0
        for var, _, g2 in eqs:
            if b in var:
                x ^= u[g2]
        col = sum(1 << ti for ti, cg in enumerate(carrier) if fval[cg][0] >> bpos[b] & 1)
        assert x == col
        q = [qq for qq in range(k) if col & quads[qq]]
        assert len(q) == 1 and bin(col).count("1") == 3
    for i in entries:
        assert u[eqs[i][2]] == zeta[zidx[i]]
    # stars, splitting into three-variable equations (chain), dual values
    dual_vals = set()
    three = 0
    stars = []
    for y in unknowns:
        terms = [u[g2] for var, _, g2 in eqs if y in var]
        if y in tset:
            terms.append(1 << carrier.index(y))
        stars.append(terms)
    for b in bunits:
        terms = [u[g2] for var, _, g2 in eqs if b in var]
        out = 0
        for t in terms:
            out ^= t
        terms.append(out)
        stars.append(terms)
    for terms in stars:
        Dv = len(terms)
        assert Dv >= 2
        x = 0
        for t in terms:
            x ^= t
        assert x == 0
        dual_vals.update(terms)
        if Dv >= 3:
            three += Dv - 2
            acc = terms[0]
            for t in terms[1:-2]:
                acc ^= t
                dual_vals.add(acc)                           # auxiliary variables of the chain
    assert three == K - tau, (three, K, tau)
    units = [1 << i for i in range(4 * k)]
    Sstar = set(units) | {v for v in dual_vals if v}
    size = len(Sstar) - 4 * k
    assert size <= K - tau
    lst = sorted(Sstar)
    pos = {v: i for i, v in enumerate(lst)}
    tri = []
    for a, b in combinations(lst, 2):
        c = a ^ b
        if c in pos and c > b:
            tri.append((1 << pos[a]) | (1 << pos[b]) | (1 << pos[c]))
    assert rank(tri) == size, "S* must be cyclic"
    # step 4: parity blocks
    odd = [v for v in lst if bin(v).count("1") & 1]
    even = [v for v in lst if not bin(v).count("1") & 1]
    parent = {v: v for v in odd}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in combinations(odd, 2):
        if (a ^ b) in pos:
            parent[find(a)] = find(b)
    comps = {}
    for uu in units:
        comps.setdefault(find(uu), []).append(uu)
    blocks = [sum(v) for v in comps.values()]
    assert len({find(v) for v in odd}) == len(blocks), "every component contains an input"
    for q in quads:
        assert sum(1 for B in blocks if B & q) <= 2
    w0 = []
    for B in blocks:
        bits = [1 << i for i in range(4 * k) if (B >> i) & 1]
        w0 += [bits[0] ^ x for x in bits[1:]]
    assert rank(even) == rank(w0) == rank(even + w0) == 4 * k - len(blocks)
    tgt = set()
    for b in bunits:
        tgt.add(sum(1 << ti for ti, cg in enumerate(carrier) if fval[cg][0] >> bpos[b] & 1))
    helpers = [v for v in odd if v not in units and v not in tgt]
    free_odd = [z for z in zeta if z and (z in units or z in tgt)]
    I = {q for q in range(k) for z in free_odd if z & quads[q]}
    X = even + [z for z in zeta if z in helpers]
    assert rank(X) >= 3 * k - len(I)
    assert tau >= 3 * k + len(I)
    assert len(even) + len(helpers) >= rank(X)
    assert K >= tau + 4 * k + len(even) + len(helpers) >= 10 * k
    print(f"{os.path.basename(path)} J={J}: local gates {K0}, after cleaning K = {K}, tau = {tau}, "
          f"dual three-variable equations = {three} = K - tau, |S*| - 4k = {size} "
          f"(targets {4 * k}, even {len(even)}, helpers {len(helpers)}), parity blocks {len(blocks)}, "
          f"|I| = {len(I)}, dim X = {rank(X)}; all identities of the proof hold; 10k = {10 * k}")


if __name__ == "__main__":
    main()
