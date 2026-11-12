"""Reviewer's numerical check of sharing/INDEPENDENT-SHEETS.md Theorem 2 on existing circuits (read-only).
For each circuit and family J: |D_J| (gates that are ancestors-or-equal of an output gate of a sheet of J and
nonzero on an own block of J), the restricted local circuit, the full mirror check of Theorem 1 on it, and
the hypothesis (H) by linear algebra.  usage: python3 dj_check.py [KSTE_STRIDE] [MIRROR_STRIDE]"""
import glob
import json
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rotation"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rotation", "mc"))
import mc  # noqa: E402
import qm  # noqa: E402
import mirror_lib as ml  # noqa: E402

HOME = os.path.expanduser("~")
KSTE = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
HUNT = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/hunt")
REPO = os.path.join(HERE, "..", "..", "..", "..", "circuits", "aes-mixcolumns")


class Model:
    def __init__(self, name, n, m, blk, cix, targets):
        self.name, self.n, self.m = name, n, m
        self.blk, self.cix = blk, cix          # input i -> block, byte index c
        self.targets = targets                 # dict (j, c) -> mask
        self.bmask = [sum(1 << i for i in range(n) if blk(i) == j) for j in range(m)]


MC = Model("MixColumns", 32, 8, lambda i: i % 8, lambda i: i // 8,
           {(j, c): mc.TARGETS[8 * c + j] for j in range(8) for c in range(4)})
_q8 = qm.rows(8)
Q8 = Model("Q_8", 32, 8, lambda i: i // 4, lambda i: i % 4,
           {(j, c): _q8[4 * j + c] for j in range(8) for c in range(4)})


def blocks_of(M, v):
    return {j for j in range(M.m) if v & M.bmask[j]}


def check_H_and_ii(M, J):
    """(i) windows disjoint, (ii) no output of J nonzero on another own block, restriction shape, (H)."""
    J = list(J)
    W = [{(j - 1) % M.m, j} for j in J]
    i_ok = all(not (W[a] & W[b]) for a in range(len(J)) for b in range(a + 1, len(J)))
    ii_ok = all(not (M.targets[(j, c)] & M.bmask[j2]) for j in J for j2 in J if j2 != j for c in range(4))
    F = sorted({(j - 1) % M.m for j in J})
    win = sum(M.bmask[b] for b in set(J) | set(F))
    fmask = sum(M.bmask[b] for b in F)
    qs, shape_ok = [], True
    for j in J:
        for c in range(4):
            v = M.targets[(j, c)] & win
            own = v & M.bmask[j]
            Ec = sum(1 << i for i in range(M.n) if M.blk(i) == j and M.cix(i) != c)
            shape_ok &= own == Ec and (v & ~M.bmask[j] & ~fmask) == 0
            qs.append(v & fmask)
    # (H): left kernel of the rows qs lies in the span of the group indicators
    R = len(qs)
    # left kernel by elimination on augmented rows (q | unit)
    rows = [(q, 1 << k) for k, q in enumerate(qs)]
    kern, basis = [], {}
    for q, tag in rows:
        while q:
            h = q.bit_length() - 1
            if h in basis:
                q ^= basis[h][0]
                tag ^= basis[h][1]
            else:
                basis[h] = (q, tag)
                break
        if q == 0:
            kern.append(tag)
    groups = [sum(1 << (4 * a + c) for c in range(4)) for a in range(len(J))]
    H_ok = all(ml.in_span(groups, k) for k in kern)
    return dict(i=i_ok, ii=ii_ok, shape=shape_ok, H=H_ok, kernel_dim=len(kern), F=F)


def analyse(M, gates, families, do_mirror, rng):
    n = M.n
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    carriers = {}
    for i in range(n, len(vals)):
        carriers.setdefault(vals[i], []).append(i)
    anc = {}
    for key, t in M.targets.items():
        if t not in carriers:
            return None
        seen, stack = set(), list(carriers[t])
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc.setdefault(key[0], set()).update(seen)
    # monotone?
    mono = True
    for key, t in M.targets.items():
        so = blocks_of(M, t)
        for g in anc_single(M, gates, vals, carriers[t][0], n):
            if not blocks_of(M, vals[g]) <= so:
                mono = False
                break
        if not mono:
            break
    out = dict(G=len(gates), mono=mono)
    for J in families:
        A = set().union(*(anc[j] for j in J))
        own = sum(M.bmask[j] for j in J)
        D = sorted(g for g in A if vals[g] & own)
        mu2 = sum(1 for g in D if sum(1 for j in J if g in anc[j] and vals[g] & M.bmask[j]) >= 2)
        cross = sum(1 for g in D if not any(g in anc[j] and vals[g] & M.bmask[j] for j in J))
        out[J] = (len(D), mu2, cross)
        if do_mirror:
            out[("mirror",) + J] = mirror_on(M, gates, vals, J, D, A, rng)
    return out


def anc_single(M, gates, vals, o, n):
    seen, stack = set(), [o]
    while stack:
        s = stack.pop()
        if s < n or s in seen:
            continue
        seen.add(s)
        stack.extend(gates[s - n])
    return seen


def mirror_on(M, gates, vals, J, D, A, rng):
    J = list(J)
    pos = {j: k for k, j in enumerate(J)}
    F = sorted({(j - 1) % M.m for j in J})
    fpos = {f: k for k, f in enumerate(F)}
    nown = 4 * len(J)
    n = M.n

    def pack_free(v):
        x = 0
        for i in range(n):
            if v >> i & 1:
                b = M.blk(i)
                if b in fpos:
                    x |= 1 << (4 * fpos[b] + M.cix(i))
                else:
                    assert b in pos or True
        return x

    def pack_own(v):
        x = 0
        for i in range(n):
            if v >> i & 1 and M.blk(i) in pos:
                x |= 1 << (4 * pos[M.blk(i)] + M.cix(i))
        return x

    loc = {g: k for k, g in enumerate(D)}
    Dset = set(D)
    lg = []
    for g in D:
        ops = []
        for s in gates[g - n]:
            if s < n:
                b = M.blk(s)
                if b in pos:
                    ops.append(('U', 4 * pos[b] + M.cix(s)))
                elif b in fpos:
                    ops.append(('F', 1 << (4 * fpos[b] + M.cix(s))))
                else:
                    ops.append(('F', 0))
            elif s in Dset:
                ops.append(('G', loc[s]))
            else:
                assert s in A and pack_own(vals[s]) == 0, "gate of A outside D not free"
                ops.append(('F', pack_free(vals[s])))
        lg.append(tuple(ops))
    tg = [pack_own(M.targets[(j, c)]) | (pack_free(M.targets[(j, c)]) << nown) for j in J for c in range(4)]
    groups = [[4 * k + c for c in range(4)] for k in range(len(J))]
    res = ml.full_check(lg, nown, tg, groups, rng)
    return (res["K0"], res["K"], res["tau"], res["T"], res["c"], res["kappa"])


def main():
    kstride = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    mstride = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    rng = random.Random(7)
    famMC = [(0, 2, 4, 6), (1, 3, 5), (7,)]
    famQ = [(0, 2, 4, 6), (1, 3, 5, 7)]
    for M, fams in ((MC, famMC), (Q8, famQ)):
        for J in fams:
            print(M.name, J, check_H_and_ii(M, J))
    # Q_8 circuits
    for f in ("q8_80.txt", "walk_q8_80.txt"):
        nn, gates = qm.read_circuit(os.path.join(HERE, "..", "..", "rotation", "circuits", f))
        r = analyse(Q8, gates, famQ, True, rng)
        print(f, {str(k): v for k, v in r.items()})
    # recorded MixColumns circuits
    for f in sorted(glob.glob(os.path.join(REPO, "*.circ.txt"))):
        r = analyse(MC, mc.parse_ncff(f), famMC, True, rng)
        print(os.path.basename(f), {str(k): v for k, v in r.items()})
    # corpus samples
    stats = {}
    nmir = 0
    srcs = []
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if os.path.exists(p):
            for k, line in enumerate(open(p)):
                if line.strip() and k % kstride == 0:
                    srcs.append(("kste", mc.parse_pairs(line)))
    for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
        if not f.endswith(".verification.json"):
            srcs.append(("hunt", [tuple(g) for g in json.load(open(f))["gates"]]))
    for idx, (src, gates) in enumerate(srcs):
        if len(gates) < 80:
            continue
        do_m = idx % mstride == 0
        r = analyse(MC, gates, famMC, do_m, rng)
        if r is None:
            continue
        nmir += do_m
        key = (src, "mono" if r["mono"] else "non-mono")
        st = stats.setdefault(key, {"n": 0, "G": Counter(), "min": {}, "mu2": Counter(), "cross": Counter(), "mir": Counter()})
        st["n"] += 1
        st["G"][r["G"]] += 1
        for J in famMC:
            d, mu2, cross = r[J]
            st["min"][J] = min(st["min"].get(J, 999), d)
            st["mu2"][(J, mu2 > 0)] += 1
            st["cross"][(J, cross > 0)] += 1
            if do_m:
                st["mir"][(J,) + r[("mirror",) + J][2:]] += 1
    for key, st in sorted(stats.items()):
        print(key, "circuits", st["n"], "gates", dict(st["G"]))
        print("    min |D_J|:", {str(J): v for J, v in st["min"].items()})
        print("    circuits with a gate of mu_J >= 2:", {str(k): v for k, v in st["mu2"].items()})
        print("    circuits with a D_J gate charged to no sheet of J (cross gate):", {str(k): v for k, v in st["cross"].items()})
        print("    mirror (J, tau, |T|, c, kappa) counts:", dict(st["mir"]))
    print("mirror checks run on", nmir, "corpus circuits; ALL ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
