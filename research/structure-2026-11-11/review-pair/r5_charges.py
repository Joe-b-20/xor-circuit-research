"""Review item 4: G = sum lambda + over + unch - excess on q3_28 and the three recorded MixColumns circuits;
the Q_3 details of REPORT section 2 and the (W1) claim of section 4.  Definitions of RECORD section 7
(output gate = any gate whose mask is a row; also the variant with only the first such gate)."""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rlib as R  # noqa: E402


def charges(model, n, gates, firstonly=False):
    m = model["m"]
    vals = R.values(n, gates)
    sup = [R.support(model, v) for v in vals]
    rowsheet = {}
    for (c, j), v in model["rows"].items():
        rowsheet.setdefault(v, set()).add(j)
    seen = set()
    anc = [set() for _ in range(m)]
    for i in range(n, len(vals)):
        if vals[i] not in rowsheet or (firstonly and vals[i] in seen):
            continue
        seen.add(vals[i])
        for j in rowsheet[vals[i]]:
            st = [i]
            while st:
                s = st.pop()
                if s < n or s in anc[j]:
                    continue
                anc[j].add(s)
                st.extend(gates[s - n])
    mu = {i: [j for j in range(m) if j in sup[i] and i in anc[j]] for i in range(n, len(vals))}
    D = [sum(1 for i in mu if j in mu[i]) for j in range(m)]
    over = sum(d - 10 for d in D)
    unch = sum(1 for i in mu if not mu[i])
    exc = sum(max(0, len(mu[i]) - 1) for i in mu)
    return dict(G=len(gates), D=D, over=over, unch=unch, exc=exc, mu=mu, sup=sup, vals=vals, anc=anc,
                ok=len(gates) == 10 * m + over + unch - exc)


mc = R.mc_model()
for f in ("aes-mixcolumns-xor88-depth5.circ.txt", "aes-mixcolumns-xor89-depth4.circ.txt",
          "aes-mixcolumns-xor97-depth3.circ.txt"):
    n, g = R.read_ncff(os.path.join(R.MCDIR, f))
    for fo in (False, True):
        c = charges(mc, n, g, fo)
        print("%s%s: charges %s  -> %d = 80 + %d + %d - %d  identity %s" % (
            f, " (first output gates only)" if fo else "", c["D"], c["G"], c["over"], c["unch"], c["exc"], c["ok"]))

Q = R.qm_model(3)
n, g = R.read_qm(os.path.join(R.QDIR, "q3_28.txt"))
c = charges(Q, n, g)
print("q3_28: |D_j| %s -> %d = 30 + %d + %d - %d  identity %s" % (c["D"], c["G"], c["over"], c["unch"], c["exc"], c["ok"]))
sup, vals = c["sup"], c["vals"]
print("   supports:", dict(sorted(Counter(tuple(sorted(sup[i])) for i in range(n, n + len(g))).items())))
print("   mu >= 2:", sorted((i - n, tuple(c["mu"][i])) for i in c["mu"] if len(c["mu"][i]) >= 2))
for j in range(3):
    own = frozenset({(j - 1) % 3, j})
    Dj = [i for i in c["mu"] if j in c["mu"][i]]
    print("   sheet %d: |D| = %d = own window %d + single %d + borrowed %d" % (
        j, len(Dj), sum(sup[i] == own for i in Dj), sum(sup[i] == frozenset({j}) for i in Dj),
        sum(sup[i] == frozenset({j, (j + 1) % 3}) for i in Dj)))
win = [frozenset({(j - 1) % 3, j}) for j in range(3)]
canc, w1 = [], []
for i, (a, b) in enumerate(g):
    if (sup[a] & sup[b]) - sup[n + i]:
        canc.append((i, sorted(sup[a] | sup[b]), sorted((sup[a] & sup[b]) - sup[n + i])))
    if not any((sup[a] | sup[b]) <= w for w in win):
        w1.append(i)
print("   whole-block cancelling gates (gate, operand union, cancelled):", canc)
print("   (W1) violations:", w1, " equal to the cancelling triangle gates:", sorted(w1) == sorted(x[0] for x in canc if len(x[1]) == 3))
