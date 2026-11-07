#!/bin/bash
# The original author's own G=75 steady-scan traces, kept in the saved 75-proof source inside the archive (data).
ROOT=~/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push5/sources/xor/AES_MixColumns_Lower_Bound_75/research_deep/root
ls -la "$ROOT"
echo "######## steady_scan.py (head)"; head -c 3500 "$ROOT/steady_scan.py"; echo
echo "######## steady75_lp.log (head and tail)"; head -c 1500 "$ROOT/steady75_lp.log"; echo ...; tail -c 2500 "$ROOT/steady75_lp.log"; echo
echo "######## STEADY_G75_BEFORE_HH_PACKING.json (head)"; head -c 1500 "$ROOT/STEADY_G75_BEFORE_HH_PACKING.json"; echo
echo "######## STEADY_G75_Q1_I0_D3_N1_P1.json (head)"; head -c 1500 "$ROOT/STEADY_G75_Q1_I0_D3_N1_P1.json"; echo
echo "######## research_deep listing"; ls "$ROOT/.."; ls "$ROOT/../labels" | head -30
for f in "$ROOT/../START_HERE.md" "$ROOT/../../START_HERE.md"; do [ -f "$f" ] && { echo "######## $f"; head -c 3000 "$f"; echo; }; done
