#!/bin/bash
# qcert2 step 0: copy what is needed (read-only sources) into qcert2/ and inspect the input files
set -e
Q=~/xs-campaigns/2026-11-07-sprint/qcert2
S=~/xs-campaigns/2026-11-07-sprint
cp -n $S/lb76/pkg_copy/source/lower_bounds/checks/stress.py $Q/stress_pkg.py
cp -n $S/bridge/profile_real.py $Q/profile_real_copy.py
cp -n $S/qreal/hub_cap_M.json $S/qreal/hub_cap_Mt.json $Q/
ls -la $Q
python3 - <<'EOF'
import json
from pathlib import Path
S = Path.home() / 'xs-campaigns/2026-11-07-sprint'
d = json.load(open(S / 'qreal/hub_cap_M.json')); print('hub_cap_M', list(d.keys()), d['kappa0'], d['kappa1'], len(d['cap']))
d = json.load(open(S / 'qbound/scan_GstarN1_q0_g75.json')); print('qbound GstarN1: keys', len(d['keys_still_feasible']), 'survivors', len(d['survivors']))
d = json.load(open(S / 'qcert/scan_ext75.json')); print('qcert scan', list(d.keys()), len(d['ext_survivors']), d['claims'][0])
d = json.load(open(S / 'qreal/scan_GstarN1HUBDARKM_q0_g75.json')); print('qreal final: keys', len(d['keys_still_feasible']), 'survivors', len(d['survivors']))
EOF
