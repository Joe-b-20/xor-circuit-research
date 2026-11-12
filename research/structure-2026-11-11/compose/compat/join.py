"""CHECK: join the near side L_k of circuit A to the far side P of circuit B (exit-free at k for both).

usage: python3 join.py BLOCK SPEC [SPEC...]
For each ordered pair (A, B): missing = labels of A that are not signals of B's far side (far units or
P_B values). Joined circuit = P_B + gates computing the missing labels + L_k(A) (entries rewired to the
same values). Lower bound on the completion: |missing| (each distinct value needs a gate).
Upper bound: greedy (each missing value as a sum of 2, else 3, else 4 available values, adding
intermediates; fallback: weight in far units). The joined circuit is built for the greedy completion and
verified to compute MixColumns.
"""
import itertools
import sys

from clib import ROWS, bm, check, cut, load


def side(spec, k):
    g = load(spec)
    vals, kind, labels = cut(g, k)
    return g, vals, kind, labels


def complete(avail, missing):
    S = set(avail)
    new = []  # list of (a_value, b_value)
    for m in sorted(missing, key=lambda v: bin(v).count("1")):
        if m in S:
            continue
        done = False
        for a in S:
            if (a ^ m) in S:
                new.append((a, a ^ m)); S.add(m); done = True
                break
        if done:
            continue
        L = list(S)
        for a, b in itertools.combinations(L, 2):
            if (a ^ b ^ m) in S:
                new.append((a, b)); S.add(a ^ b)
                new.append((a ^ b, a ^ b ^ m)); S.add(m); done = True
                break
        if not done:
            bits = [1 << i for i in range(32) if m >> i & 1]
            acc = bits[0]
            for x in bits[1:]:
                new.append((acc, x)); acc ^= x; S.add(acc)
    return new


def join(A, B, k):
    gA, vA, kA, labA = A
    gB, vB, kB, labB = B
    low = bm(k)
    if any(kA[x] == "x" for x in kA) or any(kB[x] == "x" for x in kB):
        return None
    farunits = [1 << i for i in range(32) if not (1 << i) & low]
    PB = [x for x in sorted(kB) if kB[x] in "ox"]
    sigB = set(farunits) | {vB[x] for x in PB}
    lam = {vA[a] for _, a in labA}
    missing = lam - sigB
    new = complete(sigB, missing)
    # build the joined circuit explicitly and verify
    idx = {1 << i: i for i in range(32)}
    gates = []

    def add(a, b):
        gates.append((idx[a], idx[b]))
        v = a ^ b
        idx.setdefault(v, 31 + len(gates))
        return v
    for x in PB:
        a, b = gB[x - 32]
        add(vB[a], vB[b])
    for a, b in new:
        add(a, b)
    for x in sorted(kA):
        if kA[x] in "fhe":
            a, b = gA[x - 32]
            add(vA[a], vA[b])
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    ok = all(t in set(vals[32:]) for t in ROWS.values())
    nL = sum(1 for x in kA if kA[x] in "fhe")
    return dict(L=nL, P=len(PB), miss=len(missing), up=len(new), total=len(gates), ok=ok,
                lam=len(lam))


if __name__ == "__main__":
    k = int(sys.argv[1])
    specs = sys.argv[2:]
    S = {s: side(s, k) for s in specs}
    for a in specs:
        for b in specs:
            if a == b:
                continue
            r = join(S[a], S[b], k)
            if r is None:
                print("%s near + %s far: exit at cut, skipped" % (a, b)); continue
            print("near %-22s (|L| %d, %d labels) + far %-22s (|P| %d): missing %d, greedy %d -> %d [lb %d] ok=%s" % (
                a, r["L"], r["lam"], b, r["P"], r["miss"], r["up"], r["total"], r["L"] + r["P"] + r["miss"], r["ok"]))
