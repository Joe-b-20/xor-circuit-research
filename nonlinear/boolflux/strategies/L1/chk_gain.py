from collections import Counter
from l1_lib import Data, CAMPS, fmt
D = Data()
C = Counter(); C2 = Counter()
for c in CAMPS:
    for r in D.runs[c]:
        for oc in r["outcome"]:
            if oc["status"] == "admitted":
                g = oc["gain"]; v = (c, oc["id"]) in D.val
                C[(g, "L1 front adm" if v else "not")] += 1
print(sorted(C.items()))
# recorded gain 8 admissions: what did they improve in the cap box
for c in CAMPS:
    for r in D.runs[c]:
        for oc in r["outcome"]:
            if oc["status"] == "admitted" and oc["gain"] >= 4 and (c, oc["id"]) not in D.val:
                print("gain", oc["gain"], "but dominated by archive+published at admit:", c, fmt(oc["metrics"]), r["operator"])
