"""Review item 1: which MixColumns pairs restrict to the pair problem (against the matrix), and the
section-3 quantities on the pair sub-circuits of recorded circuits.  Reads existing circuits only."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rlib as R  # noqa: E402

mc = R.mc_model()
print("MixColumns: restriction of pair (j, j+1) with block j-1 free")
for j in range(8):
    bad = R.pair_restricts(mc, j)
    print("   pair (%d,%d): %s" % (j, (j + 1) % 8, "pair problem" if not bad else "NOT: %s" % bad[:2]))
for m in (3, 4, 8):
    qm = R.qm_model(m)
    print("Q_%d: all pairs restrict:" % m, all(not R.pair_restricts(qm, j) for j in range(m)))

rng = random.Random(1)
jobs = []
for f in ("aes-mixcolumns-xor88-depth5.circ.txt", "aes-mixcolumns-xor89-depth4.circ.txt",
          "aes-mixcolumns-xor97-depth3.circ.txt"):
    n, g = R.read_ncff(os.path.join(R.MCDIR, f))
    assert R.computes(mc, n, g)
    jobs.append((f, mc, n, g, [j for j in range(8) if not R.pair_restricts(mc, j)]))
for f, m in (("q8_80.txt", 8), ("q3_28.txt", 3), ("q4_40.txt", 4)):
    qm = R.qm_model(m)
    n, g = R.read_qm(os.path.join(R.QDIR, f))
    assert R.computes(qm, n, g)
    jobs.append((f, qm, n, g, list(range(m))))

for f, model, n, g, js in jobs:
    print("%s (G = %d)" % (f, len(g)))
    for j in js:
        lc, tg = R.local_pair(model, n, g, j)
        lc2, tg2 = R.clean(lc, tg)
        out = []
        for order in ("fixed", "level"):
            st = R.tstats(R.mirror(lc2, tg2, order=order))
            out.append(st)
        # random orders: check lemma on each, record ranges
        rs = [R.tstats(R.mirror(lc2, tg2, order="random", rng=rng)) for _ in range(50)]
        rng_txt = " ".join("%s %d-%d" % (k, min(s[k] for s in rs), max(s[k] for s in rs))
                           for k in ("f_w", "D", "N_0", "tau1", "texits"))
        print("   pair (%d,%d) |D| = %d (cleaned %d): fixed %s" % (j, (j + 1) % model["m"], len(lc), len(lc2), R.fmt(out[0])))
        print("        level-order %s" % R.fmt(out[1]))
        print("        50 random orders: %s  [Lemma 3.1 checks passed on all]" % rng_txt)
