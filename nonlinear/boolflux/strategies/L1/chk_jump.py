from collections import Counter, defaultdict
from l1_lib import Data, CAMPS, fmt
D = Data()
# pull jobs: result class changes, by target class and lowered cap
C = defaultdict(Counter)
ex = defaultdict(list)
for c in CAMPS:
    for r in D.runs[c]:
        if r["operator"] != "pull" or not r["outcome"]: continue
        tm = r["target_metrics"]; m = r["outcome"][0]["metrics"]; low = r["op_info"].get("lowered")
        k = (low, "A%d AD%d" % (tm[0] if tm[0] < 33 else 33, tm[1]))
        C[k]["jobs"] += 1
        d = (m[0] - tm[0], m[1] - tm[1])
        if d != (0, 0):
            C[k]["A%+d AD%+d" % d] += 1
            ex[k].append("%s->%s %s" % (fmt(tm), fmt(m), r["outcome"][0]["status"][:8]))
for k in sorted(C):
    if len(C[k]) > 1: print(k, dict(C[k])); print("     ", ex[k][:8])
