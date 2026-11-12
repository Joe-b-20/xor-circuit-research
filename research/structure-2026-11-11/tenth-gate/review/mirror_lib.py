"""Reviewer's library: the mirror (transposition) construction of tenth-gate/PROOF.md and
sharing/INDEPENDENT-SHEETS.md, applied to GIVEN local circuits.  Nothing here searches circuits.

Local circuit: own bits 0..nown-1 (units are base signals), free bits above (packed value = own | free << nown).
Operands: ('U', k) own unit k, ('F', v) free vector v (on the free part), ('G', i) earlier gate i.
"""
import random


def popcount(x):
    return bin(x).count("1")


def rank(vecs):
    basis = {}
    r = 0
    for v in vecs:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                r += 1
                break
    return r


def in_span(vecs, x):
    vecs = list(vecs)
    return rank(vecs + [x]) == rank(vecs)


def op_value(op, vals, nown):
    t, x = op
    if t == 'U':
        return 1 << x
    if t == 'F':
        return x << nown
    return vals[x]


def evaluate(gates, nown):
    vals = []
    for a, b in gates:
        vals.append(op_value(a, vals, nown) ^ op_value(b, vals, nown))
    return vals


def clean(gates, nown, targets, rng=None, is_free=None):
    """Step 0.  Returns (cleaned gates, index of the chosen carrier of each target)."""
    vals = evaluate(gates, nown)
    carriers = [[i for i, v in enumerate(vals) if v == t] for t in targets]
    assert all(carriers), "a target is not carried"
    choice = [rng.choice(cs) if rng else cs[0] for cs in carriers]
    assert len(set(choice)) == len(choice)
    keep, stack = set(), list(choice)
    while stack:
        g = stack.pop()
        if g in keep:
            continue
        keep.add(g)
        for op in gates[g]:
            if op[0] == 'G':
                stack.append(op[1])
    newmap, out = {}, []
    for i, (a, b) in enumerate(gates):
        if i not in keep:
            continue
        ops = [newmap[op[1]] if op[0] == 'G' else op for op in (a, b)]
        if ops[0][0] == 'F' and ops[1][0] == 'F':
            v = ops[0][1] ^ ops[1][1]
            if is_free is None or is_free(v):
                assert i not in choice, "a target gate would be deleted"
                newmap[i] = ('F', v)
                continue
        newmap[i] = ('G', len(out))
        out.append(tuple(ops))
    gc = [newmap[g][1] for g in choice]
    # every remaining gate is a target or is read
    read = set()
    for a, b in out:
        for op in (a, b):
            if op[0] == 'G':
                read.add(op[1])
    assert all(i in read or i in gc for i in range(len(out)))
    # values preserved
    v2 = evaluate(out, nown)
    assert [v2[g] for g in gc] == list(targets)
    return out, gc


def build_C(gates, nown):
    """Step 1: every free operand use becomes a fresh formal input z.  Signals: own units 0..nown-1,
    z's nown..N-1, gates N..N+K-1."""
    zphi, tmp = [], []
    for a, b in gates:
        ops = []
        for op in (a, b):
            if op[0] == 'F':
                zphi.append(op[1])
                ops.append(('Z', len(zphi) - 1))
            else:
                ops.append(op)
        tmp.append(ops)
    N = nown + len(zphi)

    def sig(op):
        t, x = op
        return x if t == 'U' else (nown + x if t == 'Z' else N + x)

    C = [(sig(a), sig(b)) for a, b in tmp]
    return C, zphi, N


def formal_masks(C, N):
    vals = [1 << i for i in range(N)]
    for a, b in C:
        vals.append(vals[a] ^ vals[b])
    return vals


def transpose(C, N, outs, R, rng):
    """Lemma 3.1 construction.  outs[c] = signal carrying output c (terminal use w_c).  Returns the
    transposed gates (signals 0..R-1 = inputs w, then gates) and adj[v] = T-signal holding a(v)."""
    S = N + len(C)
    readers = [[] for _ in range(S)]
    for gi, (a, b) in enumerate(C):
        readers[a].append(N + gi)
        readers[b].append(N + gi)
    term = [[] for _ in range(S)]
    for c, s in enumerate(outs):
        term[s].append(c)
    T, adj = [], [None] * S
    for v in list(range(S - 1, N - 1, -1)) + list(range(N)):
        items = [adj[r] for r in readers[v]] + list(term[v])
        if not items:
            raise ValueError(f"d_v = 0 at signal {v}")
        while len(items) > 1:
            i, j = rng.sample(range(len(items)), 2)
            T.append((items[i], items[j]))
            new = R + len(T) - 1
            items = [it for k, it in enumerate(items) if k not in (i, j)] + [new]
        adj[v] = items[0]
    return T, adj, readers, term


def path_adjoint(C, N, readers, term):
    """Independent computation of a(v) as an R-bit mask (paths to terminal uses, mod 2)."""
    S = N + len(C)
    p = [0] * S
    for v in list(range(S - 1, N - 1, -1)) + list(range(N)):
        x = 0
        for r in readers[v]:
            x ^= p[r]
        for c in term[v]:
            x ^= 1 << c
        p[v] = x
    return p


def sim(T, R):
    vals = [1 << i for i in range(R)]
    for a, b in T:
        vals.append(vals[a] ^ vals[b])
    return vals


def partition_of(T, R):
    """Lemma 2.1 of PROOF for T: even span, blocks, x = number of odd+odd gates."""
    vals = sim(T, R)
    par = [popcount(v) & 1 for v in vals]
    even = [v for v in vals if popcount(v) % 2 == 0]
    rE = rank(even)
    parent = list(range(R))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(R):
        for j in range(i + 1, R):
            if in_span(even, (1 << i) | (1 << j)):
                parent[find(i)] = find(j)
    blocks = {}
    for i in range(R):
        blocks.setdefault(find(i), []).append(i)
    blist = list(blocks.values())
    c = len(blist)
    assert rE == R - c, "Lemma 2.1: even span is not the within-block even space"
    blk = [None] * R
    for bi, bl in enumerate(blist):
        for i in bl:
            blk[i] = bi
    x = sum(1 for (a, b) in T if par[a] and par[b])
    return vals, blist, blk, c, x


def block_parity(v, blist):
    return sum((popcount(sum(1 << i for i in bl) & v) & 1) << bi for bi, bl in enumerate(blist))


def full_check(gates, nown, targets, groups, rng, is_free=None, nfree_bits=None, expect_lemma=None):
    """Run Steps 0-5 of both proofs on a given local circuit.  groups[j] = list of target indices of group j
    (each group: targets with own part E_0..E_3 on own block j, in order c = 0..3).  Returns a dict and
    raises AssertionError on any discrepancy with a claim of the proofs."""
    K0 = len(gates)
    cg, gc = clean(gates, nown, targets, rng, is_free)
    K = len(cg)
    C, zphi, N = build_C(cg, nown)
    tau = len(zphi)
    fm = formal_masks(C, N)
    vals = evaluate(cg, nown)
    ownmask = (1 << nown) - 1
    # Step 1: value = (beta | Phi n)
    for gi in range(K):
        f = fm[N + gi]
        beta, n = f & ownmask, f >> nown
        ph = 0
        for i in range(tau):
            if n >> i & 1:
                ph ^= zphi[i]
        assert vals[gi] == beta | (ph << nown), "Step 1 value formula"
    R = len(targets)
    l = [fm[N + g] >> nown for g in gc]
    zeta = [sum(((l[c] >> i) & 1) << c for c in range(R)) for i in range(tau)]
    # Step 2 (*): span(zeta) contains DE
    DE = []
    for grp in groups:
        for k in range(3):
            DE.append((1 << grp[k]) | (1 << grp[k + 1]))
    star = all(in_span(zeta, d) for d in DE)
    assert star, "(*) fails"
    # Step 3
    outs = [N + g for g in gc]
    T, adj, readers, term = transpose(C, N, outs, R, rng)
    assert all(len(readers[v]) + len(term[v]) >= 1 for v in range(N + K))
    assert len(T) == K + R - N, "transposition count"
    if nown == R:
        assert len(T) == K - tau
    tv = sim(T, R)
    p = path_adjoint(C, N, readers, term)
    for v in range(N + K):
        assert tv[adj[v]] == p[v], "adjoint signal value"
    for k in range(nown):
        want = sum(1 << c for c in range(R) if (targets[c] >> k) & 1)
        assert tv[adj[k]] == want
    for i in range(tau):
        assert tv[adj[nown + i]] == zeta[i], "a(z_i) != zeta_i"
        (rd,) = readers[nown + i]
        assert adj[nown + i] == adj[rd], "a(z_i) is not the signal a(eps_i)"
    res = dict(K0=K0, K=K, tau=tau, T=len(T))
    # PROOF Steps 4-5 (r = 1 only)
    if len(groups) == 1 and nown == 4:
        E = [tv[adj[k]] for k in range(4)]
        assert sorted(E) == sorted([15 ^ (1 << c) for c in range(4)])
        assert len(T) >= 6
        assert tau >= 3
        if tau == 3:
            assert rank(zeta) == 3 and all(popcount(z) % 2 == 0 for z in zeta)
            gate_vals = set(tv[R:])
            assert set(E) <= gate_vals and set(zeta) <= gate_vals
            assert len(T) >= 7
        assert K >= 10
    # INDEPENDENT-SHEETS Step 4
    tvals, blist, blk, c, x = partition_of(T, R)
    r = len(groups)
    odd_gates = sum(1 for v in tvals[R:] if popcount(v) & 1)
    assert odd_gates >= R and x >= R - c
    assert len(T) >= 8 * r - c, "(1)"
    shapes, edges, unsplit = [], [], 0
    for grp in groups:
        cnt = {}
        for t in grp:
            cnt[blk[t]] = cnt.get(blk[t], 0) + 1
        sh = tuple(sorted(cnt.values(), reverse=True))
        shapes.append(sh)
        assert sh in ((4,), (2, 2), (3, 1)), f"shape {sh}"
        if len(cnt) == 2:
            edges.append(tuple(cnt.keys()))
        else:
            unsplit += 1
    V = sorted({b for e in edges for b in e})
    par = {b: b for b in V}

    def f2(b):
        while par[b] != b:
            b = par[b]
        return b

    for u, v in edges:
        par[f2(u)] = f2(v)
    kappa = len({f2(b) for b in V})
    sigma = len(edges)
    assert len(V) <= sigma + kappa
    assert c <= len(V) + (r - sigma) <= r + kappa, "(2)"
    bDE = [block_parity(d, blist) for d in DE]
    assert rank(bDE) == len(V) - kappa
    ob = set()
    for z in zeta:
        if popcount(z) & 1:
            bp = block_parity(z, blist)
            assert popcount(bp) == 1
            ob.add(bp.bit_length() - 1)
        else:
            assert block_parity(z, blist) == 0
    o = len(ob)
    assert set(V) <= ob, "o >= |V| (every block of V carries an odd export)"
    dz = rank(zeta)
    assert tau >= dz >= 3 * r + kappa, "(3)"
    assert K >= 10 * r
    res.update(c=c, kappa=kappa, o=o, dimZ=dz, shapes=tuple(shapes), x=x)
    return res
