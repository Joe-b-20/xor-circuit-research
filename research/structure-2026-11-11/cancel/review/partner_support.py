"""Support of the off-path operands at needed cancellations (MixColumns sample, every 50th kste line)."""
import os
from collections import Counter
from rev import *
from run_mc import offpath_kinds
KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
M = MC(); h = Counter()
for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
    L = open(os.path.join(KSTE, fn)).read().splitlines()
    for i in range(0, len(L), 50):
        g = read_kste_line(L[i]); r = analyse(M, g)
        if not r["ok"] or not r["R"]:
            continue
        kd, offs = offpath_kinds(r, g)
        h[tuple(sorted(set((tuple(blocks(r["sp"][o])), tuple(M.part(r["val"][o], b) for b in blocks(r["sp"][o]))) for e, o in offs)))] += 1
print(dict(h))
