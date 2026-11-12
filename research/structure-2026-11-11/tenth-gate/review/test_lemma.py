"""Reviewer's tests of tenth-gate/PROOF.md and sharing/INDEPENDENT-SHEETS.md Theorem 1 on given and on
randomly CONSTRUCTED local circuits (no search, no enumeration).  usage: python3 test_lemma.py [NRAND]"""
import json
import os
import random
import sys
from collections import Counter

import mirror_lib as ml

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMES = os.path.join(HERE, "..", "..", "rotation", "circuits", "schemes.json")
VEC = {"s0": 0b0011, "s1": 0b0110, "s2": 0b1100, "s3": 0b1001, "d0": 0b0101, "d1": 0b1010, "t": 0b1111}


def E(c):
    return 15 ^ (1 << c)


def s(c):
    return (1 << c) | (1 << ((c + 1) % 4))


def sheet_targets():
    return [E(c) | (s(c) << 4) for c in range(4)]


def scheme_local(sc):
    P = [VEC[x] for x in sc["P"]]
    def op(i, nb=11):
        if i < 4:
            return ('F', 1 << i)
        if i < 8:
            return ('U', i - 4)
        if i < nb:
            return ('F', P[i - 8])
        return ('G', i - nb)
    return [(op(a), op(b)) for a, b in sc["gates"]]


def random_local(targets, nown, rng, free_sampler, n_noise, split=None):
    """split(v): free base vectors summing to v (default [v]); for models where not every free-part
    vector is a base signal (three-term model)."""
    gates, vals = [], []
    ownmask = (1 << nown) - 1
    if split is None:
        split = lambda v: [v]

    def add0(a, b):
        gates.append((a, b))
        vals.append(ml.op_value(a, vals, nown) ^ ml.op_value(b, vals, nown))
        return len(gates) - 1

    def add(a, b):
        if b[0] == 'F' and len(split(b[1])) > 1:
            parts = split(b[1])
            i = add0(a, ('F', parts[0]))
            for q in parts[1:]:
                i = add0(('G', i), ('F', q))
            return i
        return add0(a, b)

    def rand_op():
        r = rng.random()
        if r < 0.3:
            return ('F', free_sampler())
        if r < 0.6 or not gates:
            return ('U', rng.randrange(nown))
        return ('G', rng.randrange(len(gates)))

    for _ in range(n_noise):
        a = rand_op()
        b = a if rng.random() < 0.05 else rand_op()
        add(a, b)
    order = list(range(len(targets)))
    rng.shuffle(order)
    for ti in order:
        t = targets[ti]
        if t in vals and rng.random() < 0.7:
            continue
        if rng.random() < 0.4:
            cands = []
            for i, v in enumerate(vals):
                d = t ^ v
                if d & ownmask == 0:
                    cands.append((('G', i), ('F', d >> nown)))
                elif ml.popcount(d) == 1:
                    cands.append((('G', i), ('U', d.bit_length() - 1)))
            pos = {v: i for i, v in enumerate(vals)}
            for i, v in enumerate(vals):
                if (t ^ v) in pos and pos[t ^ v] != i:
                    cands.append((('G', i), ('G', pos[t ^ v])))
            if cands:
                add(*rng.choice(cands))
                continue
        if gates and rng.random() < 0.6:
            cur = ('G', rng.randrange(len(gates)))
        else:
            cur = ('U', rng.randrange(nown))
        curv = ml.op_value(cur, vals, nown)
        for _ in range(60):
            d = t ^ curv
            if d == 0 and cur[0] == 'G':
                break
            if d & ownmask == 0:
                add(cur, ('F', d >> nown))
                break
            ownd = d & ownmask
            better = [i for i, v in enumerate(vals) if ml.popcount((d ^ v) & ownmask) < ml.popcount(ownd)]
            if rng.random() < 0.12:
                o = ('F', free_sampler())
            elif better and rng.random() < 0.5:
                o = ('G', rng.choice(better))
            else:
                o = ('U', rng.choice([i for i in range(nown) if ownd >> i & 1]))
            idx = add(cur, o)
            cur, curv = ('G', idx), vals[idx]
        else:
            raise RuntimeError("chain did not finish")
    assert all(t in vals for t in targets)
    return gates


def run_sheet_tests(nrand, rng):
    tg = sheet_targets()
    groups = [[0, 1, 2, 3]]
    out = Counter()
    sch = json.load(open(SCHEMES))
    for key, sc in sch.items():
        g = scheme_local(sc)
        for seed in range(20):
            res = ml.full_check(g, 4, tg, groups, random.Random(seed))
            out[("scheme", res["K"], res["tau"], res["T"], res["c"], res["kappa"])] += 1
    # the trivial 6 + 4 circuit
    naive = [(('U', 0), ('U', 1)), (('U', 2), ('U', 3)),
             (('U', 1), ('G', 1)), (('U', 0), ('G', 1)), (('G', 0), ('U', 3)), (('G', 0), ('U', 2))]
    # gates 2..5 carry E_0..E_3
    for c in range(4):
        naive.append((('G', 2 + c), ('F', s(c))))
    assert all(t in ml.evaluate(naive, 4) for t in tg)
    for seed in range(20):
        res = ml.full_check(naive, 4, tg, groups, random.Random(seed))
        out[("naive", res["K"], res["tau"], res["T"], res["c"], res["kappa"])] += 1
    # random constructed circuits
    pool = [rng.randrange(16) for _ in range(3)]

    def fs():
        r = rng.random()
        if r < 0.2:
            return 0
        if r < 0.5:
            return rng.choice(pool)
        return rng.randrange(16)

    Kmin = 99
    for it in range(nrand):
        g = random_local(tg, 4, rng, fs, rng.randrange(0, 14))
        res = ml.full_check(g, 4, tg, groups, rng)
        Kmin = min(Kmin, res["K"])
        out[("random", "tau", res["tau"])] += 1
        out[("random", "kappa", res["kappa"])] += 1
    print("ten-gate tests:", sorted(out.items(), key=str))
    print("   min cleaned K over random circuits:", Kmin)


def rand_invertible(n, rng):
    while True:
        rows = [rng.randrange(1, 1 << n) for _ in range(n)]
        if ml.rank(rows) == n:
            return rows


def apply(rows, v):
    """rows[i] = image of unit i."""
    x = 0
    for i, r in enumerate(rows):
        if v >> i & 1:
            x ^= r
    return x


def run_family_tests(r, nfreeblocks, nrand, rng):
    """r own blocks, free part of 4*nfreeblocks bits, q_(j,c) = M(s_c on free block j), M invertible."""
    nown = 4 * r
    nf = 4 * nfreeblocks
    M = rand_invertible(nf, rng)
    tg, groups = [], []
    for j in range(r):
        grp = []
        for c in range(4):
            q = apply(M, s(c) << (4 * j))
            tg.append((E(c) << (4 * j)) | (q << nown))
            grp.append(len(tg) - 1)
        groups.append(grp)
    pool = [rng.randrange(1 << nf) for _ in range(3)]

    def fs():
        x = rng.random()
        if x < 0.15:
            return 0
        if x < 0.45:
            return rng.choice(pool)
        if x < 0.75:
            return apply(M, rng.randrange(1 << nf))
        return rng.randrange(1 << nf)

    out = Counter()
    Kmin = 999
    for it in range(nrand):
        g = random_local(tg, nown, rng, fs, rng.randrange(0, 10 * r))
        res = ml.full_check(g, nown, tg, groups, rng)
        Kmin = min(Kmin, res["K"])
        out[(res["c"], res["kappa"])] += 1
    print(f"family r={r}, free bits={nf}: {nrand} circuits, (c, kappa) counts {dict(out)}, min K {Kmin}")


def run_shared_sheet_tests(nrand, rng):
    """r = 2 built from two recorded schemes on disjoint blocks with a COMMON free part, plus random cross
    gates (a gate reading both sheets' gates), to exercise Theorem 1 near its bound."""
    sch = list(json.load(open(SCHEMES)).values())
    out = Counter()
    for it in range(nrand):
        A, B = rng.choice(sch), rng.choice(sch)
        # own: block 0 bits 0..3, block 1 bits 4..7; free: blocks a0 (bits 0..3), a1 (4..7) of free part
        gates = []
        for j, sc in enumerate((A, B)):
            P = [VEC[x] for x in sc["P"]]
            base = len(gates)
            def op(i):
                if i < 4:
                    return ('F', 1 << (i + 4 * j))
                if i < 8:
                    return ('U', i - 4 + 4 * j)
                if i < 11:
                    return ('F', P[i - 8] << (4 * j))
                return ('G', base + i - 11)
            for a, b in sc["gates"]:
                gates.append((op(a), op(b)))
        tg = []
        for j in range(2):
            for c in range(4):
                tg.append((E(c) << (4 * j)) | ((s(c) << (4 * j)) << 8))
        # random extra noise gates mixing the two halves
        for _ in range(rng.randrange(0, 4)):
            gates.append((('G', rng.randrange(len(gates))), ('G', rng.randrange(len(gates)))))
        res = ml.full_check(gates, 8, tg, [[0, 1, 2, 3], [4, 5, 6, 7]], rng)
        out[(res["K"], res["tau"], res["T"], res["c"], res["kappa"])] += 1
    print("two schemes side by side:", dict(out))


def three_term_check(gates, rng):
    """Reviewer's mirror proof of the 13-gate three-term lemma (Theorem 9.1): free = on a alone or k alone.
    own b = bits 0..3; free part bits: a = 0..3, k = 4..7."""
    tg = [E(c) | ((s(c) | (s(c) << 4)) << 4) for c in range(4)]
    is_free = lambda v: (v & 0xF0) == 0 or (v & 0x0F) == 0
    cg, gc = ml.clean(gates, 4, tg, rng, is_free)
    K = len(cg)
    C, zphi, N = ml.build_C(cg, 4)
    tau = len(zphi)
    fm = ml.formal_masks(C, N)
    l = [fm[N + g] >> 4 for g in gc]
    zeta = [sum(((l[c] >> i) & 1) << c for c in range(4)) for i in range(tau)]
    Ia = [i for i in range(tau) if zphi[i] & 0xF0 == 0]
    Ik = [i for i in range(tau) if zphi[i] & 0xF0]
    assert all(zphi[i] & 0x0F == 0 for i in Ik)
    even = [0b0011, 0b0110, 0b1100]
    assert all(ml.in_span([zeta[i] for i in Ia], e) for e in even)
    assert all(ml.in_span([zeta[i] for i in Ik], e) for e in even)
    T, adj, readers, term = ml.transpose(C, N, [N + g for g in gc], 4, rng)
    assert len(T) == K - tau
    tv = ml.sim(T, 4)
    for i in range(tau):
        assert tv[adj[4 + i]] == zeta[i]
    assert len(Ia) >= 3 and len(Ik) >= 3 and len(T) >= 6
    if tau == 6:
        assert ml.rank([zeta[i] for i in Ia]) == 3 and len(T) >= 7
    assert K >= 13
    nM = sum(1 for a, b in cg if a[0] == 'F' and b[0] == 'F')
    return K, tau, len(T), len(Ia), len(Ik), nM


def run_three_term(nrand, rng):
    S = VEC
    # the recorded 13-gate circuit of rotation/mc/three_term.py, with its wiring
    F = lambda x: ('F', S[x] | (S[x] << 4))
    g = []
    def add(a, b):
        g.append((a, b)); return ('G', len(g) - 1)
    # D_x = [a:x] + [k:x] as an M-gate (two free operands of different type)
    D = {x: add(('F', S[x]), ('F', S[x] << 4)) for x in ("s1", "d1", "t")}
    U = lambda c: ('U', c)
    s0b = add(U(0), U(1)); d0b = add(U(0), U(2)); d1b = add(U(1), U(3))
    h1 = add(U(3), D["s1"]); v = add(D["d1"], s0b); o1 = add(d0b, h1); o2 = add(h1, v)
    h2 = add(D["t"], o1); o3 = add(d1b, h2); o0 = add(v, h2)
    out = Counter()
    for seed in range(10):
        out[("recorded",) + three_term_check(g, random.Random(seed))] += 1
    def fs():
        x = rng.random()
        if x < 0.1:
            return 0
        v = rng.randrange(1, 16)
        return v if x < 0.55 else v << 4
    tg = [E(c) | ((s(c) | (s(c) << 4)) << 4) for c in range(4)]
    Kmin = 99
    for it in range(nrand):
        split = lambda v: [v] if (v & 0xF0 == 0 or v & 0x0F == 0) else [v & 0x0F, v & 0xF0]
        gg = random_local(tg, 4, rng, fs, rng.randrange(0, 14), split)
        if rng.random() < 0.5:          # sometimes add M-gates (a-vector + k-vector) and route entries through them
            m = rng.randrange(1, 16)
            gg.append((('F', m), ('F', m << 4)))
            gg.append((('G', len(gg) - 1), ('G', rng.randrange(len(gg) - 1))))
        res = three_term_check(gg, rng)
        Kmin = min(Kmin, res[0])
        out[("random", "tau", res[1])] += 1
    # lift sheet-model circuits (schemes and random ones) to the three-term model: every free operand v
    # (on a) becomes either a shared M-gate [a:v]+[k:v] or two consecutive entries (+[a:v], then +[k:v])
    sch = list(json.load(open(SCHEMES)).values())
    pool = [rng.randrange(16) for _ in range(3)]
    fs1 = lambda: rng.choice(pool) if rng.random() < 0.4 else rng.randrange(16)
    Kmin2 = 99
    for it in range(nrand):
        base = scheme_local(rng.choice(sch)) if it % 3 == 0 else random_local(sheet_targets(), 4, rng, fs1, rng.randrange(0, 10))
        new, mp, Mg = [], {}, {}
        for gi, (a, b) in enumerate(base):
            ops, late = [], None
            for op in (a, b):
                if op[0] == 'G':
                    ops.append(('G', mp[op[1]]))
                elif op[0] == 'U':
                    ops.append(op)
                else:
                    v = op[1]
                    if v == 0 or rng.random() < 0.5:
                        if v not in Mg:
                            new.append((('F', v), ('F', v << 4)))
                            Mg[v] = len(new) - 1
                        ops.append(('G', Mg[v]))
                    else:
                        ops.append(('F', v))
                        late = v
            if ops[0][0] == 'F' and ops[1][0] == 'F':
                # both free in the sheet model: lift each operand to its M-gate
                for k2 in range(2):
                    v = ops[k2][1]
                    if v not in Mg:
                        new.append((('F', v), ('F', v << 4)))
                        Mg[v] = len(new) - 1
                    ops[k2] = ('G', Mg[v])
                late = None
            new.append(tuple(ops))
            if late is not None:
                new.append((('G', len(new) - 1), ('F', late << 4)))
            mp[gi] = len(new) - 1
        assert all(t in ml.evaluate(new, 4) for t in tg)
        res = three_term_check(new, rng)
        Kmin2 = min(Kmin2, res[0])
        out[("lifted", "K", res[0], "tau", res[1], "nM", res[5])] += 1
    print("three-term mirror:", sorted(out.items(), key=str), " min K random:", Kmin, " min K lifted:", Kmin2)


def corollary():
    """8-gate circuit for the transpose of the 8-input sheet map, transposed back."""
    R = 4
    D = []
    for k in range(4):                      # p_k = w_k + w_(k-1), signals 4..7
        D.append((k, (k - 1) % 4))
    for k in range(4):                      # E_k(w) = p_(k+2) + w_(k+3), signals 8..11
        D.append((4 + (k + 2) % 4, (k + 3) % 4))
    vals = ml.sim(D, R)
    assert [vals[8 + k] for k in range(4)] == [15 ^ (1 << k) for k in range(4)]
    assert [vals[4 + k] for k in range(4)] == [(1 << k) | (1 << ((k - 1) % 4)) for k in range(4)]
    # outputs of D: column of b_k = E_k(w) (signal 8+k), column of a_k = w_k + w_(k-1) (signal 4+k)
    # order the 8 outputs as inputs of the transpose: b_0..b_3 (bits 0..3), a_0..a_3 (bits 4..7)
    outs = [8 + k for k in range(4)] + [4 + k for k in range(4)]
    T, adj, readers, term = ml.transpose(D, R, outs, 8, random.Random(1))
    tv = ml.sim(T, 8)
    rows = [tv[adj[c]] for c in range(4)]
    want = [E(c) | (s(c) << 4) for c in range(4)]
    print(f"corollary: transposed circuit has {len(T)} gates; computes (E_c | s_c): {rows == want}")
    for i, (a, b) in enumerate(T):
        pass
    return len(T), rows == want


def duality_counterexample():
    """|B| = 1, r = 2: targets b0 + a0, b0 + a1 (free side A = {a0, a1})."""
    gates = [(('U', 0), ('F', 1)), (('U', 0), ('F', 2))]
    tg = [1 | (1 << 1), 1 | (2 << 1)]
    cg, gc = ml.clean(gates, 1, tg)
    C, zphi, N = ml.build_C(cg, 1)
    T, adj, readers, term = ml.transpose(C, N, [N + g for g in gc], 2, random.Random(0))
    print(f"duality form with |B|=1, r=2: local circuit K = {len(cg)}, tau = {len(zphi)}, mirrored |T| = {len(T)};"
          f" |T| + tau = {len(T) + len(zphi)} > K; true relation K = |T| + tau + |B| - r = {len(T) + len(zphi) + 1 - 2}")


def main():
    nrand = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    rng = random.Random(20261111)
    run_sheet_tests(nrand, rng)
    run_family_tests(1, 2, nrand // 3, rng)
    run_family_tests(2, 2, nrand // 3, rng)
    run_family_tests(3, 3, nrand // 5, rng)
    run_shared_sheet_tests(200, rng)
    run_three_term(nrand, rng)
    corollary()
    duality_counterexample()
    print("ALL ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
