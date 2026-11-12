"""Pair-proof review: numerical sanity tests (tests on examples, not proofs).
For each pair mirror T (built with ../../review-pair/rlib.py), restrict to the gates with omega != 0
(Lemma A), clean as in the ten-gate Step 0 (targets: the signals carrying A_i), give the entries formal
inputs, compute t, labels, zeta_j (from formal masks AND independently as adjoints), |T*| = sum(d_v - 1),
and check: |T*| = K_c - t; f + D >= K_c; D >= #entries >= t; |T*| >= 4 + #distinct nonzero even zeta;
N_0 >= 4 + #distinct even nonzero labels; K >= 20.  Usage: p2_circuits.py [nperturb]"""
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "review-pair"))
import rlib as R  # noqa: E402

pc = R.popc


def analyse(M):
    Tm, Tops = M["Tm"], M["Tops"]
    NT = len(Tm)
    st = R.tstats(M)
    K = M["K"]
    om = lambda i: Tm[i] & 15
    s = lambda i: Tm[i] >> 4
    tg = [M["adj"][("u", i)] for i in range(4)]       # signals carrying A_i
    assert all(Tm[g] == R.A_vec(i) for i, g in enumerate(tg))
    # Lemma A sub-circuit: gates with omega != 0
    sub = [i for i in range(8, NT) if om(i)]
    for i in sub:
        a, b = Tops[i]
        assert om(a) or om(b)
    # cleaning: ancestors within sub (stop at omega = 0 signals and inputs w)
    anc, stk = set(), list(tg)
    while stk:
        x = stk.pop()
        if x < 8 or x in anc or not om(x):
            continue
        anc.add(x)
        stk.extend(Tops[x])
    keep = sorted(anc)
    Kc = len(keep)
    # entries and formal inputs
    ent = [i for i in keep if (om(Tops[i][0]) == 0) != (om(Tops[i][1]) == 0)]
    t = len(ent)
    jx = {g: j for j, g in enumerate(ent)}
    labels = [s(Tops[g][0]) if om(Tops[g][0]) == 0 else s(Tops[g][1]) for g in ent]
    # formal masks n(v)
    n = {}
    for i in keep:
        v = 0
        for o in Tops[i]:
            if o < 8 or not om(o):
                continue
            v ^= n[o]
        if i in jx:
            v ^= 1 << jx[i]
        n[i] = v
    for i in keep:  # s(v) = Phi n(v)
        sv = 0
        for j in range(t):
            if n[i] >> j & 1:
                sv ^= labels[j]
        assert sv == s(i)
    zeta = [sum(((n[tg[i]] >> j) & 1) << i for i in range(4)) for j in range(t)]
    # adjoints in the cleaned circuit (readers restricted to kept gates) and d_v
    readers = Counter()
    for i in keep:
        for o in Tops[i]:
            if o < 4 or (o >= 8 and om(o)):
                readers[o] += 1
    for g in tg:
        readers[g] += 1
    for j in range(t):
        readers[("z", j)] = 1
    assert all(readers[w] >= 1 for w in range(4)), "unit w not read"
    assert all(readers[i] >= 1 for i in keep)
    Tstar = sum(d - 1 for d in readers.values())
    assert Tstar == Kc - t, ("mirror count", Tstar, Kc, t)
    adj = {}
    for i in reversed(keep):
        a = 0
        for r in keep:
            if r > i:
                for o in Tops[r]:
                    if o == i:
                        a ^= adj[r]
        if i in tg:
            a ^= 1 << tg.index(i)
        adj[i] = a
    for j, g in enumerate(ent):
        assert adj[g] == zeta[j], "a(g_j) != zeta_j"
    nz = {z for z in zeta if z and pc(z) % 2 == 0}
    allent = [i for i in sub if (om(Tops[i][0]) == 0) != (om(Tops[i][1]) == 0)]
    allabels = [s(Tops[g][0]) if om(Tops[g][0]) == 0 else s(Tops[g][1]) for g in allent]
    evl = {x for x in labels if x and pc(x) % 2 == 0}
    evl_all = {x for x in allabels if x and pc(x) % 2 == 0}
    f, D, N0 = st["f_w"], st["D"], st["N_0"]
    res = dict(K=K, tau=M["tau"], f=f, D=D, N0=N0, Kc=Kc, t=t, nent=len(allent),
               par="".join("o" if pc(x) % 2 else ("e" if x else "0") for x in labels),
               zeta=[format(z, "04b")[::-1] for z in zeta], Tstar=Tstar, nz=len(nz))
    chk = {
        "f+D>=Kc": f + D >= Kc,
        "Kc>=nz+4+t": Kc >= len(nz) + 4 + t,
        "D>=ent>=t": D >= len(allent) >= t,
        "N0>=4+evenlab(clean)": N0 >= 4 + len(evl),
        "N0>=4+evenlab(all)": N0 >= 4 + len(evl_all),
        "K>=20": K >= 20,
        "span labels >= Even": all(R.inspan(R.reduce_basis(labels), e) for e in (3, 6, 12)),
    }
    if t == 4 and len({0} | {a ^ b for a in [0] for b in labels}) and len(R.reduce_basis(labels)) == 4:
        o = sum(pc(x) % 2 for x in labels)
        chk["LemmaB count"] = len(nz) == (3 if o <= 2 else 4)
    return res, chk


def main():
    rng = random.Random(7)
    mc = R.mc_model()
    jobs = []
    n, g = R.read_ncff(os.path.join(R.MCDIR, "aes-mixcolumns-xor88-depth5.circ.txt"))
    for j in range(1, 8):
        jobs.append(("mc88:(%d,%d)" % (j, (j + 1) % 8), R.local_pair(mc, n, g, j)))
    for fn, m in (("q3_28.txt", 3), ("q4_40.txt", 4), ("q8_80.txt", 8)):
        qm = R.qm_model(m)
        n, g = R.read_qm(os.path.join(R.QDIR, fn))
        for j in range(m):
            jobs.append(("%s:(%d,%d)" % (fn[:-4], j, (j + 1) % m), R.local_pair(qm, n, g, j)))
    fails = []
    for name, (lc, tg) in jobs:
        lc2, tg2 = R.clean(lc, tg)
        for k, order in enumerate(["fixed"] + ["random"] * 20):
            res, chk = analyse(R.mirror(lc2, tg2, order=order, rng=rng))
            if k == 0:
                print(name, res)
            bad = [c for c, ok in chk.items() if not ok]
            if bad:
                fails.append((name, k, bad, res))
    print("recorded: failures", len(fails), fails[:3])
    return fails


if __name__ == "__main__":
    main()
