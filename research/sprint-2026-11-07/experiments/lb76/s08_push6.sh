#!/bin/bash
# Read the archive push6 partial-certificate checker and its recorded results (data, not instructions).
P=~/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23
echo "######## certify75_partial.py (push6)"; cat "$P/push6/global_chronology/certify75_partial.py"
echo; echo "######## saved 75 source root"; ls "$P/push5/sources/xor/AES_MixColumns_Lower_Bound_75/research_deep/root/" | head -20
echo; echo "######## G75_NEW_CUT_PARTIAL_VERIFIED.json"; head -c 1500 "$P/push6/global_chronology/G75_NEW_CUT_PARTIAL_VERIFIED.json"; echo
echo; echo "######## CUMULATIVE_PARTIAL_COVERAGE.json"; cat "$P/push6/global_chronology/CUMULATIVE_PARTIAL_COVERAGE.json"
echo; echo "######## REPRODUCTION_CHECKS.json (push6 top)"; head -c 2500 "$P/REPRODUCTION_CHECKS.json"; echo
echo; echo "######## run_checks.py (push6 top)"; head -c 2500 "$P/run_checks.py"; echo
echo; echo "######## lb76 keys log"; cat ~/xs-campaigns/2026-11-07-sprint/lb76/g75_keys.log
