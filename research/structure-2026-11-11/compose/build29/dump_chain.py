"""Dump the local chain-of-three circuit of a recorded Q_m circuit (run j, j+1, j+2; block j-1 free)
in vchain.py text format.  usage: python3 dump_chain.py q4_40.txt 4 j"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "review-pair"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "chain"))
import rlib as R  # noqa: E402
import chain3 as C  # noqa: E402

fn, m, j = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
model = R.qm_model(m)
n, g = R.read_qm(os.path.join(R.QDIR, fn))
lc, tg = C.local_chain(model, n, g, j)
lc, tg = R.clean(lc, tg)


def nm(o):
    if o[0] == "u":
        return "x%d%d" % (o[1] // 4 + 1, o[1] % 4)
    if o[0] == "f":
        return "f" + "".join(str((o[1] >> i) & 1) for i in range(4))
    return "g%d" % o[1]


for i, (a, b) in enumerate(lc):
    print("g%d = %s + %s" % (i, nm(a), nm(b)))
