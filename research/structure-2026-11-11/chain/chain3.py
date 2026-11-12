"""Chain of three sheets: mirror form and the two peelings, checked on recorded circuits.

No search.  Reads recorded Q_m circuits (m >= 4), cuts out the local circuit of the run of sheets
j, j+1, j+2 with block j-1 free and all other blocks set to zero, cleans it, transposes it (formal
inputs for the entries), and checks on the resulting T:
  (M)  |T| = K - tau; the adjoints of the own units are A_i = (E_i | p_i | 0), B_i = (0 | E_i | p_i),
       C_i = (0 | 0 | E_i); the exports span a space containing Even(w^1) + 0 + 0.
  (P3) peeling the LAST group (fibres of the part on groups 1, 2), on T with zero gates and repeated
       values removed:  f12 + tau >= 20,  D + N >= 9,  entries >= 3, labels span all s-parts.
  (P1) peeling the FIRST group:  f1 + tau >= 10;  if there is no level-1 exit, D1 + N0 >= 20.
A test on existing circuits; it proves nothing universal.  Standard library only.

usage: python3 chain3.py
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "review-pair"))
import rlib as R  # noqa: E402

L = 3
NU = 4 * L


def local_chain(model, n, gates, j):
    m = model["m"]
    assert m >= L + 1
    a = (j - 1) % m
    own = [(j + i) % m for i in range(L)]
    vals = R.values(n, gates)

    def loc(v):
        x = R.nib(model, v, a)
        for i, b in enumerate(own):
            x |= R.nib(model, v, b) << (4 * (i + 1))
        return x
    lv = [loc(v) for v in vals]
    tv = [model["rows"][(c, own[k])] for k in range(L) for c in range(4)]
    want = [(R.E4(c) << (4 * (k + 1))) | (R.S4(c) << (4 * k)) for k in range(L) for c in range(4)]
    assert [loc(t) for t in tv] == want, "restriction is not the chain problem"
    outg = [min(i for i in range(n, len(vals)) if vals[i] == t) for t in tv]
    anc, st = set(), list(outg)
    while st:
        s = st.pop()
        if s < n or s in anc:
            continue
        anc.add(s)
        st.extend(gates[s - n])
    D = sorted(g for g in anc if lv[g] >> 4)
    pos = {g: i for i, g in enumerate(D)}
    unit = {}
    for k in range(L):
        for c in range(4):
            unit[model["idx"](c, own[k])] = 4 * k + c
    lc = []
    for g in D:
        ops = []
        for o in gates[g - n]:
            if o in pos:
                ops.append(("g", pos[o]))
            elif o < n and o in unit:
                ops.append(("u", unit[o]))
            else:
                assert lv[o] >> 4 == 0
                ops.append(("f", lv[o] & 15))
        lc.append(tuple(ops))
    tg = [pos[t] for t in outg]
    assert [R.lval(lc)[t] for t in tg] == want
    return lc, tg


def mirror(lc, tg, rng=None):
    K = len(lc)
    phi, fops = [], []
    for a, b in lc:
        ops = [a, b]
        nf = sum(1 for o in ops if o[0] == "f")
        assert nf <= 1
        if nf == 1:
            p = 0 if ops[0][0] == "f" else 1
            phi.append(ops[p][1])
            ops[p] = ("z", len(phi) - 1)
        fops.append(tuple(ops))
    tau = len(phi)
    readers = {}
    for i, ops in enumerate(fops):
        for o in ops:
            readers.setdefault(o, []).append(i)
    term = {}
    for t, g in enumerate(tg):
        term.setdefault(("g", g), []).append(t)
    Tm = [1 << i for i in range(NU)]
    Tops = [None] * NU
    adj = {}
    keys = [("g", i) for i in reversed(range(K))] + [("z", t) for t in range(tau)] + [("u", u) for u in range(NU)]
    for key in keys:
        c = list(term.get(key, [])) + [adj[("g", r)] for r in readers.get(key, [])]
        assert c, ("signal never read", key)
        if rng is not None:
            rng.shuffle(c)
        acc = c[0]
        for x in c[1:]:
            Tm.append(Tm[acc] ^ Tm[x])
            Tops.append((acc, x))
            acc = len(Tm) - 1
        adj[key] = acc
    return dict(K=K, tau=tau, Tm=Tm, Tops=Tops, adj=adj)


def check_mirror_form(M):
    Tm, K, tau = M["Tm"], M["K"], M["tau"]
    assert len(Tm) - NU == K - tau, "|T| = K - tau"
    for k in range(L):
        for i in range(4):
            exp = R.E4(i) << (4 * k)
            if k + 1 < L:
                exp |= ((1 << ((i - 1) % 4)) | (1 << i)) << (4 * (k + 1))
            assert Tm[M["adj"][("u", 4 * k + i)]] == exp, "adjoint of a unit"
    zetas = [Tm[M["adj"][("z", t)]] for t in range(tau)]
    zb = R.reduce_basis(zetas)
    assert all(R.inspan(zb, e) for e in (0b0011, 0b0110, 0b1100)), "exports"
    return zetas


def reduce_T(Tm, Tops):
    seen = set(1 << i for i in range(NU))
    red = []
    for i in range(NU, len(Tm)):
        v = Tm[i]
        if v == 0 or v in seen:
            continue
        seen.add(v)
        red.append((v, Tm[Tops[i][0]], Tm[Tops[i][1]]))
    return red


def peel(red, low, shift):
    """Fibres of the part omega = v & low; s = v >> shift."""
    first = set((1 << i) for i in range(NU) if (1 << i) & low)
    f = D = N = exits = nonentry = 0
    labels, sparts = [], []
    for v, a, b in red:
        om, oa, ob = v & low, a & low, b & low
        if om == 0:
            N += 1
            if oa:
                assert oa == ob
                exits += 1
        elif om in first:
            D += 1
            if (oa == 0) != (ob == 0):
                labels.append((a if oa == 0 else b) >> shift)
            else:
                nonentry += 1
        else:
            assert oa and ob and oa != ob, "first gate"
            first.add(om)
            f += 1
        if om:
            sparts.append(v >> shift)
    Pi = R.reduce_basis(labels)
    assert all(R.inspan(Pi, s) for s in sparts), "s-parts in the span of the labels"
    return dict(f=f, D=D, N=N, e=len(labels), exits=exits, nonentry=nonentry,
                odd=sum(1 for x in labels if R.popc(x) & 1))


def stats(M):
    zetas = check_mirror_form(M)
    red = reduce_T(M["Tm"], M["Tops"])
    tau = len(set(z for z in zetas if z))
    p3 = peel(red, 0xFF, 8)
    p1 = peel(red, 0x0F, 4)
    assert len(red) == p3["f"] + p3["D"] + p3["N"] == p1["f"] + p1["D"] + p1["N"]
    assert p3["f"] + tau >= 20, "f12 + tau >= 20"
    assert p3["D"] + p3["N"] >= 9 and p3["e"] >= 3, "D + N >= 9"
    assert p1["f"] + tau >= 10, "f1 + tau >= 10"
    if p1["exits"] == 0:
        assert p1["D"] + p1["N"] >= 20, "no level-1 exit: D1 + N0 >= 20"
    assert len(red) + tau >= 29, "29"
    return dict(K=M["K"], tau=M["tau"], T=len(M["Tm"]) - NU, red=len(red), tau_red=tau, p3=p3, p1=p1)


def line(s):
    p3, p1 = s["p3"], s["p1"]
    return ("K %d tau %d |T| %d (reduced %d + %d) | last: f12 %d D %d N %d entries %d (odd %d) exits %d nonentry %d"
            " | first: f1 %d D1 %d N0 %d exits %d" % (
                s["K"], s["tau"], s["T"], s["red"], s["tau_red"], p3["f"], p3["D"], p3["N"], p3["e"], p3["odd"],
                p3["exits"], p3["nonentry"], p1["f"], p1["D"], p1["N"], p1["exits"]))


def main():
    rng = random.Random(7)
    files = [("q4_40.txt", 4), ("q5_50.txt", 5), ("q6_60.txt", 6), ("q7_70.txt", 7), ("q8_80.txt", 8),
             ("q12_120.txt", 12), ("q4-x11_40.txt", 4), ("q4-x12_42.txt", 4), ("q4-x13_42.txt", 4),
             ("q6-x20_62.txt", 6), ("q8-x17_82.txt", 8), ("q8-x17x37_85.txt", 8),
             ("walk_q4_40.txt", 4), ("walk_q5_50.txt", 5), ("walk_q6_60.txt", 6), ("walk_q8_80.txt", 8),
             ("walk_q9_90.txt", 9), ("walk_q11_110.txt", 11), ("walk_q16_160.txt", 16)]
    total = 0
    worst = None
    for fn, m in files:
        path = os.path.join(R.QDIR, fn)
        if not os.path.exists(path):
            print("%s: missing" % fn)
            continue
        model = R.qm_model(m)
        n, g = R.read_qm(path)
        if not R.computes(model, n, g):
            print("%s: does not compute Q_%d under this reading; skipped" % (fn, m))
            continue
        print("%s (G = %d)" % (fn, len(g)))
        for j in range(m):
            lc, tg = local_chain(model, n, g, j)
            lc2, tg2 = R.clean(lc, tg)
            s = stats(mirror(lc2, tg2))
            ks = [s["red"] + s["tau_red"]]
            for _ in range(30):
                t = stats(mirror(lc2, tg2, rng))
                ks.append(t["red"] + t["tau_red"])
                total += 1
            total += 1
            if worst is None or min(ks) < worst:
                worst = min(ks)
            print("   run %d..%d: |D| %d; %s; reduced |T|+tau over 31 orders: %d-%d" % (
                j, (j + 2) % m, len(lc), line(s), min(ks), max(ks)))
    print("all checks passed on %d mirrors; smallest reduced |T| + tau seen: %s" % (total, worst))


if __name__ == "__main__":
    main()
