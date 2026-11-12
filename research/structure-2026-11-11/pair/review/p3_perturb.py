"""Pair-proof review: the p2 checks on randomly perturbed valid pair circuits (moves of
../../review-pair/r2_perturb.py, reused by executing that file's definitions only).  A test, not a proof.
Usage: p3_perturb.py N"""
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(HERE, "..", "..", "review-pair")
sys.path.insert(0, RP)
sys.path.insert(0, HERE)
import rlib as R  # noqa: E402
import p2_circuits as P2  # noqa: E402

src = open(os.path.join(RP, "r2_perturb.py")).read()
src = src[:src.index("bases = []")]
ns = {"__file__": os.path.join(RP, "r2_perturb.py")}
exec(compile(src, "r2_perturb_defs", "exec"), ns)
ns["rng"] = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 99)
rng = ns["rng"]

bases = []
mc = R.mc_model()
for f in ("aes-mixcolumns-xor88-depth5.circ.txt",):
    n, g = R.read_ncff(os.path.join(R.MCDIR, f))
    for j in range(1, 8):
        bases.append(("mc88:%d" % j,) + R.local_pair(mc, n, g, j))
for f, m in (("q8_80.txt", 8), ("q3_28.txt", 3), ("q4_40.txt", 4)):
    qm = R.qm_model(m)
    n, g = R.read_qm(os.path.join(R.QDIR, f))
    for j in range(m):
        bases.append(("%s:%d" % (f, j),) + R.local_pair(qm, n, g, j))

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
fails, other = [], []
hist = Counter()
minK = 99
for trial in range(N):
    name, lc, tg = rng.choice(bases)
    nodes = ns["to_nodes"](lc)
    tg_ids = list(tg)
    nxt = len(nodes)
    for _ in range(rng.randint(1, 8)):
        kind, nxt = ns["move"](nodes, tg_ids, nxt)
    lc2, tg2 = ns["from_nodes"](nodes, tg_ids)
    v = R.lval(lc2)
    assert [v[t] for t in tg2] == R.pair_targets_local()
    lc3, tg3 = R.clean(lc2, tg2)
    try:
        res, chk = P2.analyse(R.mirror(lc3, tg3, order="random", rng=rng))
    except AssertionError as e:
        other.append((trial, name, repr(e)))
        continue
    hist[(res["t"], res["par"].count("o"), res["N0"])] += 1
    minK = min(minK, res["K"])
    bad = [c for c, ok in chk.items() if not ok]
    if bad:
        fails.append((trial, name, bad, res, len(lc3)))
print("perturbed:", N, " check failures:", len(fails), " assertion errors:", len(other))
for x in fails[:5]:
    print("   FAIL", x)
for x in other[:5]:
    print("   ERR", x)
print("min K:", minK)
print("(t, #odd clean labels, N_0) histogram:", sorted(hist.items()))
