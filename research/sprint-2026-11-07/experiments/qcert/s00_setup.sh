#!/bin/bash
# qcert step 0: copy what is needed into qcert/ and reconcile the survivor data files
set -e
Q=~/xs-campaigns/2026-11-07-sprint/qcert
S=~/xs-campaigns/2026-11-07-sprint
cp $S/lb76/pkg_copy/source/lower_bounds/checks/stress.py $Q/stress_pkg.py
cp $S/bridge/profile_real.py $Q/profile_real_copy.py
ls -la $Q
cd $S
python3 - <<'EOF'
import json
b=json.load(open("qbound/scan_base_q0_g75.json")); e=json.load(open("qbound/scan_GstarN1_q0_g75.json"))
print("base survivors",len(b["survivors"]),"ext survivors",len(e["survivors"]))
sb={(tuple(s["state"]),s["ori"]) for s in b["survivors"]}; se={(tuple(s["state"]),s["ori"]) for s in e["survivors"]}
print("ext subset of base:", se<=sb, "excluded:", len(sb-se))
print("sample survivor record:", b["survivors"][0])
kb={tuple(k) for k in b["keys_still_feasible"]}; ke={tuple(k) for k in e["keys_still_feasible"]}
print("keys base",len(kb),"ext",len(ke),"killed",len(kb-ke))
g=json.load(open("lb76/g75_keys.json")); print("g75 feasible == base keys:", {tuple(k) for k in g["feasible"]}==kb)
EOF
grep -n "^def \|^import\|^from" $Q/profile_real_copy.py | head -30
file $Q/s00_setup.sh
