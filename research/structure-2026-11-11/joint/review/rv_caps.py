"""Reviewer's caps check (machine review, phase 7). Explicit circuits only; no search.
cap_B = min over circuits of U_B + min over circuits of D_B (U_B = useful gates after zeroing B, D_B = removed).
Circuits: recorded 88/89/97, every STRIDE-th kste line, review-compat lw0..lw7, W* (loaded from joint/wstar.json),
and the reviewer's own rebuild of the lowwasteB carrier construction from its written description.
Also: the circuits_2.txt line 20 charge numbers used in ACCOUNT section 6.
usage: python3 rv_caps.py STRIDE MAXSIZE
"""
import itertools
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import (BLK, COMPAT, JOINT, ROWS, ancestors_of_rows, check, load_json, load_kste, pure_block,  # noqa
                   restrict, values)
from rv_checks import get, specs  # noqa


def carrier_build(B):
    """Construction described in joint/lowwasteB.py docstring, written independently."""
    rest = [k for k in range(8) if k not in B]
    if len(rest) < len(B):
        return None
    car = dict(zip(B, rest))
    where = {1 << i: i for i in range(32)}
    g = []

    def xor(a, b):
        w = a ^ b
        if w not in where:
            g.append((where[a], where[b]))
            where[w] = 31 + len(g)
        return w

    def chain(w):
        bits = [1 << i for i in range(32) if w >> i & 1]
        acc = bits[0]
        for x in bits[1:]:
            acc = xor(acc, x)
        return acc

    lowB = sum(BLK[b] for b in B)
    unit = lambda c, j: 1 << (8 * c + j)
    pat = lambda r, b: [c for c in range(4) if r >> (8 * c + b) & 1]
    for r in ROWS.values():
        if not r & lowB:
            chain(r)
    Y = {}
    for r in ROWS.values():
        if r & lowB:
            y = r & ~lowB
            for b in B:
                for c in pat(r, b):
                    y ^= unit(c, car[b])
            Y[r] = chain(y)
    diag = {}
    for b in B:
        gg = [xor(unit(c, b), unit(c, car[b])) for c in range(4)]
        s = [xor(gg[c], gg[(c + 1) % 4]) for c in range(4)]
        for c in range(4):
            diag[(b, frozenset((c, (c + 1) % 4)))] = s[c]
            diag[(b, frozenset(k for k in range(4) if k != c))] = xor(s[(c + 1) % 4], gg[(c + 3) % 4])
    for r in ROWS.values():
        if r & lowB:
            parts = [diag[(b, frozenset(pat(r, b)))] for b in B if pat(r, b)]
            acc = parts[0]
            for p in parts[1:]:
                acc = xor(acc, p)
            xor(acc, Y[r])
    return g


def charge_numbers(g):
    v = values(g)
    anc = ancestors_of_rows(g, v)
    F = {j: {x for x in anc[j] if v[x] & BLK[j]} for j in range(8)}
    m = Counter()
    for j in range(8):
        for x in F[j]:
            m[x] += 1
    charged = set(m)
    P12 = {x for x in anc[1] | anc[2] if v[x] & (BLK[1] | BLK[2])}
    return ([len(F[j]) for j in range(8)], sum(c - 1 for c in m.values() if c > 1), len(g) - len(charged),
            len(charged), len(P12), sorted(F[1] & F[2]))


def lam(g):
    v = values(g)
    pb = [pure_block(x) for x in v]
    c = Counter()
    for k, (a, b) in enumerate(g):
        x = 32 + k
        L = ({pb[x]} if pb[x] is not None else set()) | {pb[o] for o in (a, b) if pb[o] is not None and pb[o] != pb[x]}
        c[len(L)] += 1
    return c


def main():
    stride, maxsize = int(sys.argv[1]), int(sys.argv[2])
    circs = []
    for sp in specs(stride):
        name, g = get(sp)
        if all(check(g)):
            circs.append((name, g))
    ncorp = len(circs)
    for k in range(8):
        circs.append(("lw%d" % k, load_json(os.path.join(COMPAT, "lw%d.json" % k))))
    W = load_json(os.path.join(JOINT, "wstar.json"))
    circs.append(("W*", W))
    for name, g in circs[ncorp:]:
        assert all(check(g)), name
    lw = lam(W)
    print("W*: %d gates, valid+reduced %s, lambda counts %s" % (len(W), all(check(W)), dict(sorted(lw.items()))))
    built = {}
    for size in range(1, maxsize + 1):
        for B in itertools.combinations(range(8), size):
            g = carrier_build(B)
            if g is None:
                continue
            assert all(check(g)), ("construction invalid", B)
            built[B] = g
            circs.append(("cB" + "".join(map(str, B)), g))
    print("circuits: %d corpus/recorded, %d other explicit, %d constructions (all valid and reduced)" % (
        ncorp, len(circs) - ncorp - len(built), len(built)))
    vals = [(nm, g, values(g)) for nm, g in circs]
    for size in range(1, maxsize + 1):
        rows = []
        ownD = []
        for B in itertools.combinations(range(8), size):
            bu, bd = (10 ** 9, ""), (10 ** 9, "")
            for nm, g, v in vals:
                rem, use = restrict(g, v, B)
                if len(use) < bu[0]:
                    bu = (len(use), nm)
                if len(rem) < bd[0]:
                    bd = (len(rem), nm)
            if B in built:
                rem, _ = restrict(built[B], values(built[B]), B)
                ownD.append((len(rem), len(built[B])))
            rows.append((bu[0] + bd[0], B, bu, bd))
        rows.sort(reverse=True)
        print("|B|=%d: max cap %d at %s (minU %s, minD %s); min cap %d; all < 88: %s" % (
            size, rows[0][0], rows[0][1], rows[0][2], rows[0][3], rows[-1][0], all(r[0] < 88 for r in rows)))
        for r in rows[1:4]:
            print("      next:", r)
        if ownD:
            print("      own constructions: D_B %d-%d, gates %d-%d" % (min(d for d, _ in ownD), max(d for d, _ in ownD),
                                                                    min(n for _, n in ownD), max(n for _, n in ownD)))
        wit = Counter(r[3][1][:2] for r in rows)
        print("      min-D witnesses by kind:", dict(wit))
    g = load_kste("circuits_2.txt", 20)
    assert all(check(g))
    Fs, dbl, unch, nch, p12, ov = charge_numbers(g)
    print("circuits_2.txt:20: G=%d |F_j|=%s over-charges |F_j|-10=%s double charges sum(m-1)^+=%d uncharged=%d "
          "distinct charged=%d |P(1,2)|=%d F1nF2=%s" % (len(g), Fs, [f - 10 for f in Fs], dbl, unch, nch, p12, ov))
    r88 = [c for n, c in circs if n == "xor88"][0]
    Fs, dbl, unch, nch, p12, ov = charge_numbers(r88)
    print("recorded 88: |F_j|=%s double=%d uncharged=%d distinct charged=%d" % (Fs, dbl, unch, nch))
    # conjecture formula vs words on the sample
    mn = Counter()
    for nm, g in circs[:ncorp]:
        Fs, dbl, unch, nch, p12, ov = charge_numbers(g)
        mn[(nch >= 80, sum(f - 10 for f in Fs) + unch >= dbl, min(Fs) >= 10)] += 1
    print("sample: (distinct charged >= 80, formula holds, all |F_j| >= 10) ->", dict(mn))
    mins = min(charge_numbers(g)[3] for nm, g in circs[:ncorp])
    print("sample: least number of distinct charged gates:", mins)


if __name__ == "__main__":
    main()
