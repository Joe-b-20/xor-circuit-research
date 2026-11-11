"""10m-gate circuits for every Q_m, m >= 4, by chaining sheet schemes along closed walks.

usage: python3 walks.py [MMAX]            (default 40; writes circuits/schemes.json and circuits/walk_qM_G.txt
                                           for M = 4, 5, 6, 8, 9, 11, 16)

A sheet scheme P -> O (scheme_sat.py) is a list of 10 gates over the inputs of two blocks a, b and
three even vectors P of block a, computing the four outputs of the sheet and three even vectors O of
block b.  The schemes used here are "pure": the gates computing O depend only on the inputs of block b.
Given a cyclic sequence of bases S_0, ..., S_(m-1) and a pure scheme S_(j-1) -> S_j for every j, the
union of the m schemes (sheet j on blocks j-1, j, its P-signals being the O-gates of sheet j-1) is a
circuit for Q_m with 10m gates: first all pure gates, then the remaining gates sheet by sheet.

Closed walks (bases written with the names of scheme_sat.py):
  W4 = (s1 d1 t, s0 d0 d1, s1 s3 d0, s0 s3 t)                 the 40-gate circuit of Q_4
  W5 = (s1 d1 t, s0 d0 d1, s1 s3 d0, s1 s3 d1, s0 s3 t)       the 50-gate circuit of Q_5
  W6 = (s1 s3 d1, s1 s2 t, s3 d1 t, s2 d0 d1, s0 s2 d0, s0 d1 t)   the 60-gate circuit of Q_6
W4 and W5 share the base "s0 s3 t", W5 and W6 share "s1 s3 d1"; so every m = 4a + 5b (a + b >= 1) and
every m = 4a + 5b + 6c with b >= 1, and m = 6c, has a closed walk: all m >= 4 except 7.  (For m = 7 see
circuits/q7_70.txt.)  The script solves the twelve transitions by SAT (cached), checks purity, builds the
circuit for every 4 <= m <= MMAX, m != 7, and verifies it against Q_m.
"""
import json
import os
import sys

import qm
import scheme_sat as ss

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "circuits", "schemes.json")

W4 = ["s1,d1,t", "s0,d0,d1", "s1,s3,d0", "s0,s3,t"]
W5 = ["s1,d1,t", "s0,d0,d1", "s1,s3,d0", "s1,s3,d1", "s0,s3,t"]
W6 = ["s1,s3,d1", "s1,s2,t", "s3,d1,t", "s2,d0,d1", "s0,s2,d0", "s0,d1,t"]


def transitions():
    T = set()
    for W in (W4, W5, W6):
        for j in range(len(W)):
            T.add((W[j - 1], W[j]))
    return sorted(T)


def pure_ok(base, gates, vals, O):
    """The gates carrying the O vectors (on block b) depend only on inputs of block b."""
    nb = len(base)
    dep_ok = [False] * (nb + len(gates))
    for i in range(nb):
        dep_ok[i] = 4 <= i < 8
    for gi, (a, b) in enumerate(gates):
        dep_ok[nb + gi] = dep_ok[a] and dep_ok[b]
    for o in O:
        idx = next(i for i in range(nb, nb + len(gates)) if vals[i] == o << 4)
        if not dep_ok[idx]:
            return False
    return True


def solve_pure(P, O, k=10):
    """Scheme with the O-gates among the first gates, which use only block-b inputs (no symmetry breaking)."""
    from pysat.solvers import Solver
    base = [1 << i for i in range(8)] + list(P)
    targets = ss.targets_out() + [o << 4 for o in O]
    nb = len(base)
    for kp in (3, 4, 5):
        cl, A, B = ss.encode(base, targets, k)
        # drop nothing from the encoding; add: gates 0..kp-1 use only block-b inputs or earlier pure gates
        for g in range(nb, nb + kp):
            for s in list(range(0, 4)) + list(range(8, nb)):
                cl.append([-A[g][s]])
                cl.append([-B[g][s]])
        with Solver(name="cadical153", bootstrap_with=cl) as S:
            if not S.solve():
                continue
            model = set(x for x in S.get_model() if x > 0)
        gates = []
        for g in range(nb, nb + k):
            a = next(i for i in range(g) if A[g][i] in model)
            b = next(i for i in range(g) if B[g][i] in model)
            gates.append((a, b))
        vals = list(base)
        for a, b in gates:
            vals.append(vals[a] ^ vals[b])
        if pure_ok(base, gates, vals, O):
            return base, gates, vals
    return None


def get_schemes():
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    for ps, os_ in transitions():
        key = ps + " -> " + os_
        if key in cache:
            continue
        P, O = ss.parse(ps), ss.parse(os_)
        res = ss.solve(P, O)
        assert res is not None, key
        base, gates, vals = res
        if not pure_ok(base, gates, vals, O):
            res = solve_pure(P, O)
            assert res is not None, "no pure scheme for " + key
            base, gates, vals = res
        cache[key] = {"P": ps.split(","), "O": os_.split(","), "gates": gates}
        print("scheme", key, "found", flush=True)
        json.dump(cache, open(CACHE, "w"), indent=1)
    return cache


def check_scheme(sc):
    P = [ss.VEC[x] for x in sc["P"]]
    O = [ss.VEC[x] for x in sc["O"]]
    base = [1 << i for i in range(8)] + P
    vals = list(base)
    for a, b in sc["gates"]:
        vals.append(vals[a] ^ vals[b])
    ok = len(sc["gates"]) == 10 and all(t in vals[11:] for t in ss.targets_out() + [o << 4 for o in O])
    return ok and pure_ok(base, [tuple(g) for g in sc["gates"]], vals, O)


def build(walk, schemes):
    m = len(walk)
    n = 4 * m
    gates = []
    sig = {}        # (sheet j, local signal index >= 11) -> global index
    oname = {}      # (block j, vector name) -> global index of the pure gate carrying it
    plan = []
    for j in range(m):
        sc = schemes[walk[j - 1] + " -> " + walk[j]]
        P = [ss.VEC[x] for x in sc["P"]]
        base = [1 << i for i in range(8)] + P
        vals = list(base)
        pure = [False] * 11
        for i in range(4, 8):
            pure[i] = True
        for a, b in sc["gates"]:
            vals.append(vals[a] ^ vals[b])
            pure.append(pure[a] and pure[b])
        plan.append((sc, vals, pure))

    def ref(j, sc, s):
        if s < 4:
            return 4 * ((j - 1) % m) + s
        if s < 8:
            return 4 * j + (s - 4)
        if s < 11:
            return oname[((j - 1) % m, sc["P"][s - 8])]
        return sig[(j, s)]

    for phase in (True, False):
        for j in range(m):
            sc, vals, pure = plan[j]
            for gi, (a, b) in enumerate(sc["gates"]):
                s = 11 + gi
                if pure[s] != phase:
                    continue
                gates.append((ref(j, sc, a), ref(j, sc, b)))
                sig[(j, s)] = n + len(gates) - 1
                if phase:
                    for nm in sc["O"]:
                        if vals[s] == ss.VEC[nm] << 4 and (j, nm) not in oname:
                            oname[(j, nm)] = sig[(j, s)]
    return n, gates


def walk_for(m):
    if m % 6 == 0 and m % 4 and m % 5:
        return W6 * (m // 6)
    for c in range(0, m // 6 + 1):
        for b in range(0, (m - 6 * c) // 5 + 1):
            rest = m - 6 * c - 5 * b
            if rest % 4 == 0 and (c == 0 or b >= 1):
                a = rest // 4
                w = W4 * a
                if b >= 1:
                    first = W5[:4] + W6[1:] * c + ([W6[0]] if c else []) + W5[4:]
                    # W5 = (.., s1 s3 d0, s1 s3 d1, s0 s3 t): insert c copies of W6 at "s1 s3 d1"
                    first = W5[:4] + (W6[1:] + [W6[0]]) * c + W5[4:]
                    w = w + first + W5 * (b - 1)
                return w
    return None


def main():
    mmax = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    schemes = get_schemes()
    print("schemes:", len(schemes), " all verified and pure:", all(check_scheme(sc) for sc in schemes.values()))
    bad = []
    for m in range(4, mmax + 1):
        w = walk_for(m)
        if w is None:
            print(f"m = {m}: no walk of this length (use the direct circuit)")
            continue
        assert len(w) == m
        n, gates = build(w, schemes)
        ok = len(gates) == 10 * m and qm.computes(n, gates, qm.rows(m))
        if not ok:
            bad.append(m)
        if m in (4, 5, 6, 8, 9, 11, 16) and ok:
            qm.write_circuit(os.path.join(HERE, "circuits", f"walk_q{m}_{len(gates)}.txt"), n, gates,
                             f"Q_{m}: {len(gates)} gates; chained sheet schemes along the closed walk\n" + " | ".join(w)
                             + "\nbuilt and verified by walks.py")
    print(f"m = 4..{mmax} (except 7): circuits with 10m gates verified for all m:", not bad, bad)


if __name__ == "__main__":
    main()
