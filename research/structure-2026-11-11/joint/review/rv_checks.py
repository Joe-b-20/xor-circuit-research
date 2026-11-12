"""Reviewer's checks (machine review, phase 7): J1, J3 fibre formula, J2, J4, J6, J7, J8, J9 on explicit circuits,
sharing census, nonlocal / dead counts. Read-only corpus scan by stride; no search.
usage: python3 rv_checks.py STRIDE
"""
import itertools
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import (BLK, KSTE, REC, ROWS, RKEYS, SHEETMASK, WIN, D_formula, ancestors_of_rows, check, colmask,  # noqa
                   gf2rank, keepmask, kste_count, load_kste, load_ncff, nib, pure_block, restrict, rho_all, supp, values)


def specs(stride):
    out = []
    for nm in ("xor88-depth5", "xor89-depth4", "xor97-depth3"):
        out.append(("rec", os.path.join(REC, "aes-mixcolumns-%s.circ.txt" % nm)))
    for fn in sorted(os.listdir(KSTE)):
        if fn.startswith("circuits_"):
            for i in range(1, kste_count(fn) + 1, stride):
                out.append(("kste", (fn, i)))
    return out


def get(spec):
    kind, x = spec
    if kind == "rec":
        g, outs = load_ncff(x)
        v = values(g)
        for k, s in outs.items():  # y_(8b+r) = bit r of byte b
            assert v[s] == ROWS[(k // 8, k % 8)], ("output label", x, k)
        return os.path.basename(x).split("-")[2], g
    return "%s:%d" % x, load_kste(*x)


def windows_check():
    """J8 window computation: all 28 pairs and all 56 triples, from our own matrix."""
    big = []
    for j, k in itertools.combinations(range(8), 2):
        I = WIN[j] & WIN[k]
        if len(I) >= 2:
            big.append(((j, k), sorted(I)))
    tri = [t for t in itertools.combinations(range(8), 3) if len(WIN[t[0]] & WIN[t[1]] & WIN[t[2]]) >= 2]
    return big, tri


def analyse(g):
    v = values(g)
    G = len(g)
    n = len(v)
    res = {"G": G}
    # J1 (all |B| <= 2) and J3 fibre formula (all pairs)
    D = {}
    for size in (1, 2):
        for B in itertools.combinations(range(8), size):
            rem, use = restrict(g, v, B)
            assert len(rem) == D_formula(v, B), ("J1", B)
            D[B] = (rem, use)
    for b, c in itertools.combinations(range(8), 2):
        keep = keepmask((b, c))
        fib = defaultdict(set)
        for x in set([0] + v):
            fib[x & keep].add(x)
        O = sum(len(F) - len({x & BLK[b] for x in F}) - len({x & BLK[c] for x in F}) + 1 for F in fib.values())
        assert O == len(D[(b,)][0]) + len(D[(c,)][0]) - len(D[(b, c)][0]), ("J3", b, c)
    # J2, lambda
    pb = [pure_block(x) for x in v]
    lam = Counter()
    Lsets = defaultdict(set)
    for k, (a, c) in enumerate(g):
        x = 32 + k
        L = set()
        if pb[x] is not None:
            L.add(pb[x])
        for o in (a, c):
            if pb[o] is not None and pb[o] != pb[x]:
                L.add(pb[o])
        if pb[x] is None:
            assert not (pb[a] is not None and pb[a] == pb[c]), "reader with two block-b operands"
        lam[len(L)] += 1
        for b in L:
            Lsets[b].add(x)
    assert max(lam) <= 2
    N = 0
    for b in range(8):
        rem = D[(b,)][0]
        assert Lsets[b] <= rem, ("J2", b)
        N += len(rem) - len(Lsets[b])
    sumD = sum(len(D[(b,)][0]) for b in range(8))
    dead = sum(G - len(D[(b,)][0]) - len(D[(b,)][1]) for b in range(8))
    sumU = sum(len(D[(b,)][1]) for b in range(8))
    assert sumD == G + lam[2] - lam[0] + N, "J4a"
    assert 7 * G == sumU + lam[2] - lam[0] + N + dead, "J4b"
    res.update(N=N, dead=dead, sumDmG=sumD - G, lam0=lam[0], lam2=lam[2])
    # J6, J7
    rho = rho_all(g, v)
    deliv = set()
    j7slack = []
    for b in range(8):
        om = {8 * k + b: 1 << k for k in range(4)}
        R = []
        for k, (a, c) in enumerate(g):
            x = 32 + k
            if pb[x] == b:
                om[x] = (om[a] if pb[a] == b else 0) ^ (om[c] if pb[c] == b else 0)
            elif pb[a] == b or pb[c] == b:
                R.append((x, a if pb[a] == b else c))
        for k in range(4):
            s = 0
            for x, p in R:
                if om[p] >> k & 1:
                    s ^= rho[x]
            assert s == colmask(k, b), ("J6", b, k)
        sh = [j for j in range(8) if any(ROWS[(i, j)] & BLK[b] for i in range(4))]
        rk = sum(gf2rank([sum(((ROWS[(i, j)] >> (8 * k + b)) & 1) << i for i in range(4)) for k in range(4)]) for j in sh)
        X = 0
        for x, p in R:
            met = tuple(j for j in sh if rho[x] & SHEETMASK[j])
            if len(met) > 1:
                X += len(met) - 1
                deliv.add((b, met))
        assert len(R) >= rk - X, "J7"
        j7slack.append((b, len(R), rk))
    res["deliv"] = deliv
    res["sheetrank"] = sum(r[2] for r in j7slack)
    res["R"] = [r[1] for r in j7slack]
    # census (J8/J9)
    anc = ancestors_of_rows(g, v)
    mono = all(supp(v[32 + k]) == supp(v[a]) | supp(v[c]) for k, (a, c) in enumerate(g))
    cen = Counter()
    for x in range(32, n):
        S = supp(v[x])
        if len(S) < 2:
            continue
        sh = tuple(j for j in range(8) if x in anc[j])
        if len(sh) < 2:
            continue
        inter = set.intersection(*[set(WIN[j]) for j in sh])
        inside = S <= inter
        cen[(tuple(sorted(S)), sh, inside)] += 1
        if mono:
            assert inside and (tuple(sorted(S)), sh) in (((0, 7), (0, 1)), ((3, 7), (3, 4))), "J8"
        if not inside:
            # J9: for each sheet j served and each c in S outside window(j): no path from x to a sheet-j row
            # avoiding exit gates at c (gate w, c not in B(w), both operands nonzero on c)
            rd = None
            for j in sh:
                for c in S - WIN[j]:
                    rows = {v.index(ROWS[(i, j)], 32) for i in range(4)}
                    if rd is None:
                        rd = defaultdict(list)
                        for k, (a, cc) in enumerate(g):
                            rd[a].append(32 + k)
                            rd[cc].append(32 + k)
                    st, seen = [x], set()
                    while st:
                        s = st.pop()
                        if s in seen:
                            continue
                        seen.add(s)
                        assert s not in rows, ("J9", x, j, c)
                        for w in rd[s]:
                            a, cc = g[w - 32]
                            if not (v[w] & BLK[c]) and (v[a] & BLK[c]) and (v[cc] & BLK[c]):
                                continue  # exit at c: path is cut here
                            st.append(w)
    res["mono"] = mono
    res["cen"] = cen
    return res


def main():
    stride = int(sys.argv[1])
    big, tri = windows_check()
    print("windows:", {j: sorted(WIN[j]) for j in range(8)})
    print("pairs of windows meeting in >= 2 blocks:", big, " triples:", tri)
    tot = Counter()
    agg = defaultdict(Counter)
    census = {True: Counter(), False: Counter()}
    nonmono_pattern = Counter()
    delivtypes = Counter()
    gates = Counter()
    for sp in specs(stride):
        name, g = get(sp)
        ok, red = check(g)
        if not (ok and red):
            tot["invalid"] += 1
            continue
        r = analyse(g)
        tot["circuits"] += 1
        tot["mono" if r["mono"] else "nonmono"] += 1
        gates[r["G"]] += 1
        for k in ("N", "dead", "sumDmG"):
            agg[k][r[k]] += 1
        census[r["mono"]].update(set(r["cen"]))
        out = tuple(sorted((k, c) for k, c in r["cen"].items() if not k[2]))
        if r["mono"]:
            has = {(k[0], k[1]) for k in r["cen"]}
            agg["mono_uses_both"][((0, 7), (0, 1)) in has and ((3, 7), (3, 4)) in has] += 1
        else:
            nonmono_pattern[out] += 1
        delivtypes.update(r["deliv"])
        if name.startswith("xor"):
            print(name, {k: r[k] for k in ("G", "N", "dead", "sumDmG", "lam0", "lam2", "mono")}, "sum|R_b|", sum(r["R"]),
                  "sheet-rank total", r["sheetrank"])
    print("totals:", dict(tot), " gate counts:", dict(sorted(gates.items())))
    print("J1 (all |B|<=2), J3 fibre formula, J2, lambda<=2, J4 (both), J6 (all b, k), J7, J8 (mono), J9 (outside): all asserted")
    for k in ("N", "dead", "sumDmG", "mono_uses_both"):
        print("  %s distribution:" % k, dict(sorted(agg[k].items())))
    for mono in (True, False):
        print("census, block-monotone=%s: (support, sheets, inside) -> #circuits containing" % mono)
        for k, c in sorted(census[mono].items(), key=lambda kv: (not kv[0][2], -kv[1])):
            print("    ", k, c)
    print("non-monotone circuits by multiset of outside-shared gates:")
    for k, c in nonmono_pattern.most_common():
        print("    ", c, k)
    print("multi-sheet reader (shared delivery) types (block, sheets met by rho) -> #circuits:")
    for k, c in sorted(delivtypes.items()):
        print("    ", k, c)


if __name__ == "__main__":
    main()
