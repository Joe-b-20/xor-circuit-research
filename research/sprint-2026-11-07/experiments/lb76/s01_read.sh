#!/bin/bash
# Read the scalar checkers and inspect the certificate file; environment check.
CH=~/xor-circuit-research/lower-bound-proofs/mixcolumns-lb75/source/lower_bounds/checks
cd "$CH" || exit 1
echo "===== check72.py"; cat check72.py
echo "===== check73.py"; cat check73.py
echo "===== check73_drift.py"; cat check73_drift.py
echo "===== CERTIFICATES75.json head"; head -c 1200 CERTIFICATES75.json; echo
echo "===== env"
python3 --version
python3 -c 'import scipy, numpy; print("scipy", scipy.__version__, "numpy", numpy.__version__)' 2>&1
nproc; uptime
echo "===== archive grep for G=75 attempts"
cd ~/xs-campaigns/2026-11-07-sprint/import/zip/research/ || exit 1
grep -rlE 'G75_survivors|lp_regen_75|run\(75\)|G=75|G = 75|75-gate optimum|excluding 75|exclude 75' --include='*.py' --include='*.md' --include='*.json' --include='*.txt' . 2>/dev/null | head -60
echo "===== lineage folders"
for d in AES_Deep_Repair_75_76_Profiles_2026_10_02 AES_Fixed_Budget_Reconstruction_60_76_2026_10_02 AES_MixColumns_Unrestricted_Lower_Bound_75 AES_Unrestricted_Weight_Parity_2026_10_12 AES_Weight_Parity_Joint_Accounting_2026_10_12 AES_Joint_Accounting_Case_Bounds_2026_10_12 AES_Multi_Helper_Proof_Continuation_2026_10_12 AES_Output_Distance_Accounting_2026_10_10 AES_Overlapping_Group_Accounting_2026_10_10 AES_MixColumns_Lower_Bound_71 AES_Three_Helper_Obstruction_2026_10_02 AES_Gate_By_Gate_Ladder_2026_10_02 AES_Residual_Inference_2026_10_02; do
  echo "--- $d"; find "$d" -maxdepth 3 -type f | head -40
done
