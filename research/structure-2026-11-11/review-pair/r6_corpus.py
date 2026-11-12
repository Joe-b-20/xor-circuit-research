"""Review item 4: the eleven circuits of REPORT section 6, recomputed with the reviewer's charge code.
kste line numbers are cumulative over non-empty lines of circuits_1..3 (as in corpus_inspect.py)."""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rlib as R  # noqa: E402
from r5_charges import charges  # noqa: E402

KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
HUNT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/hunt")
want = {1, 5, 28, 44, 1511, 2041, 3435, 3658, 3713}
mc = R.mc_model()
nl = 0
for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt"):
    for line in open(os.path.join(KSTE, fn)):
        if not line.strip():
            continue
        nl += 1
        if nl in want:
            g = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", line)]
            c = charges(mc, 32, g)
            print("kste %s line %d: %s  %d = 80 + %d + %d - %d  identity %s" % (fn, nl, c["D"], c["G"], c["over"], c["unch"], c["exc"], c["ok"]))
for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
    if ("d1a7d70c18e1b7cf" in f or "4d178ce621827217" in f) and not f.endswith(".verification.json"):
        g = [tuple(x) for x in json.load(open(f))["gates"]]
        c = charges(mc, 32, g)
        print("hunt %s: %s  %d = 80 + %d + %d - %d  identity %s" % (os.path.basename(f), c["D"], c["G"], c["over"], c["unch"], c["exc"], c["ok"]))
