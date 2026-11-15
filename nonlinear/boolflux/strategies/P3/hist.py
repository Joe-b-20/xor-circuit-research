#!/usr/bin/env python3
"""Histogram of built (G, GD) along a plain qflip walk at rank <= R.  hist.py REF START STEPS EVERY SEED [R]"""
import collections, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, build as BD  # noqa

ref, start, steps, every, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
R = int(sys.argv[6]) if len(sys.argv) > 6 else 17
rc, Yt = FL.ref_basis(ref)
c = BT.load(start)
st = QF.State(*QF.decompose(c, Yt)); st.reduce()
rng = random.Random(seed)
H = collections.Counter(); moves = collections.Counter()
for it in range(steps):
    prev = (list(st.free), list(st.fixed), list(st.lin))
    mv = QF.step(st, rng, R + 1, 0.01); st.reduce()
    if st.rank() == 0: st.free, st.fixed, st.lin = prev; continue
    moves[mv] += 1
    if st.rank() <= R and it % every == 0:
        cc = BD.build(c, Yt, st.free, st.fixed, st.lin, random.Random(it))
        m = cc.metrics(BD.MODEL)
        H[(m['G'], m['GD'])] += 1
print(sorted(H.items())); print(moves)
