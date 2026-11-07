#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qhub
until grep -q ALLDONE scan1.log; do sleep 5; done
echo "== circuit check Sat Nov  7 23:38:47 UTC 2026" > scan2.log
nice -n 8 timeout 600 python3 qh_circ.py > qh_circ.log 2>&1; echo "EXIT 0" >> qh_circ.log
echo "== scan GstarN1HUB2DARKMFMPK Sat Nov  7 23:38:48 UTC 2026" >> scan2.log
nice -n 8 timeout 1200 python3 qh_lp.py scan GstarN1HUB2DARKMFMPK 75 >> scan2.log 2>&1; echo "EXIT 0" >> scan2.log
echo "== scan GstarN1HUB2LDARKMFMPK Sat Nov  7 23:38:48 UTC 2026" >> scan2.log
nice -n 8 timeout 1200 python3 qh_lp.py scan GstarN1HUB2LDARKMFMPK 75 >> scan2.log 2>&1; echo "EXIT 0" >> scan2.log
echo "== vertices Sat Nov  7 23:38:48 UTC 2026" >> scan2.log
nice -n 8 timeout 600 python3 - > vertices_hub2.log 2>&1 <<"PYEOF"
import json, subprocess, sys
from collections import Counter
d = json.load(open("scan_GstarN1HUB2DARKMFM_q0_g75.json"))
keys = [tuple(k) for k in d["keys_still_feasible"]]
print("keys:", len(keys)); print(sorted(keys))
surv = d["survivors"]
# key usage by survivors: even and odd side (h,y,F,ori) with (k, ell)
ev = Counter((x["state"][4], x["state"][2], x["state"][3], x["ori"], x["k"]) for x in surv)
od = Counter((x["state"][5], x["state"][3], x["state"][2], ("Mt" if x["ori"]=="M" else "M"), x["ell"]) for x in surv)
print("even-side (h,y,F,ori,k) top:", ev.most_common(15)); print("odd-side (h,y,F,ori,ell) top:", od.most_common(15))
print("shortfall:", Counter(x["shortfall"] for x in surv))
import qh_lp
for key in [(13,4,4,4,1,"M"), (12,5,5,4,1,"M"), (11,5,5,5,0,"Mt"), (10,6,6,6,0,"M"), (10,2,10,8,0,"Mt"), (19,0,0,1,5,"Mt"), (19,0,4,3,3,"M")]:
    if key in keys:
        h,y,F,q,z,ori = key
        qh_lp.vertices(h,y,F,q,z,ori,"GstarN1HUB2DARKMFMPK", n=4)
        sys.stdout.flush()
PYEOF
echo "ALLDONE2 Sat Nov  7 23:38:48 UTC 2026" >> scan2.log
