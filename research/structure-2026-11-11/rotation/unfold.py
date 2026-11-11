"""Unfold a circuit for Q_p into a periodic circuit for Q_(p*k) (period p blocks).

usage: python3 unfold.py p FILE k1,k2,... [--save PREFIX]

Every signal of the Q_p circuit gets a "line mask" (a map block index in Z -> 4-bit pattern): inputs
of block j sit at block j, and for a gate with operands u, v the script looks for period shifts
(ku, kv) in {-1,0,1}^2 such that  shift(u, p*ku) + shift(v, p*kv)  is supported on at most two adjacent
blocks of the line; the gate is then re-based so that its leftmost block lies in 0..p-1.  If this
succeeds for every gate and the line masks of the outputs are the line outputs
E_c(j) + s_c(j-1), then for every k >= 1 the pattern "gate (g, t) = (u, t + ku) + (v, t + kv), t in Z_k"
is a circuit for Q_(p*k) with k times as many gates (fold the line modulo p*k).  The script prints
whether the lifting succeeded and verifies the unfolded circuits for the listed k directly.
"""
import json
import sys

import qm


def load(path):
    if path.endswith(".json"):
        return [tuple(g) for g in json.load(open(path))["gates"]]
    return qm.read_circuit(path)[1]


def shift(mask, d):
    return {b + d: v for b, v in mask.items()}


def add(m1, m2):
    out = dict(m1)
    for b, v in m2.items():
        nv = out.get(b, 0) ^ v
        if nv:
            out[b] = nv
        else:
            out.pop(b, None)
    return out


def main():
    p = int(sys.argv[1])
    gates = load(sys.argv[2])
    ks = [int(x) for x in sys.argv[3].split(",")]
    n = 4 * p
    line = [{i // 4: 1 << (i % 4)} for i in range(n)]
    refs = []
    ok = True
    for gi, (a, b) in enumerate(gates):
        found = None
        for ka in (0, -1, 1):
            for kb in (0, -1, 1):
                msk = add(shift(line[a], p * ka), shift(line[b], p * kb))
                if not msk:
                    continue
                lo, hi = min(msk), max(msk)
                if hi - lo <= 1:
                    found = (ka, kb, msk)
                    break
            if found:
                break
        if not found:
            print(f"gate {gi}: no compact lift")
            ok = False
            break
        ka, kb, msk = found
        base = min(msk) // p          # re-base so that the leftmost block is in 0..p-1
        msk = shift(msk, -p * base)
        refs.append((a, ka - base, b, kb - base))
        line.append(msk)
    if not ok:
        sys.exit(1)
    # line outputs: E_c on block j, s_c on block j-1 (for j = 0 the re-based copy sits on blocks p-1, p)
    got = {tuple(sorted(mk.items())) for mk in line[n:]}
    missing = 0
    for j in range(p):
        for c in range(4):
            E = 15 ^ (1 << c)
            s = (1 << c) | (1 << ((c + 1) % 4))
            cands = [tuple(sorted({j - 1 + p * base: s, j + p * base: E}.items())) for base in (0, 1)]
            if not any(cd in got for cd in cands):
                missing += 1
    print(f"lifting succeeded for all {len(gates)} gates; line outputs missing: {missing}")
    for k in ks:
        M = p * k
        N = 4 * M
        G = len(gates)
        big = []

        def ref(sidx, t):
            if sidx < n:
                return 4 * ((sidx // 4 + p * t) % M) + sidx % 4
            return N + (sidx - n) * k + (t % k)

        for gi, (a, ka, b, kb) in enumerate(refs):
            for t in range(k):
                big.append((ref(a, t + ka), ref(b, t + kb)))
        good = qm.computes(N, big, qm.rows(M))
        print(f"   k = {k}: Q_{M} with {len(big)} gates: {'VERIFIED' if good else 'FAILED'}")
        if good and "--save" in sys.argv:
            pref = sys.argv[sys.argv.index("--save") + 1]
            qm.write_circuit(f"{pref}{M}_{len(big)}.txt", N, big, f"Q_{M}: {len(big)} gates; period-{p} unfolding (k = {k}) of {sys.argv[2]}; verified by unfold.py")


if __name__ == "__main__":
    main()
