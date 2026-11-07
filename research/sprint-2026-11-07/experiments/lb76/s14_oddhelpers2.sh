#!/bin/bash
# Read the odd-helper theorem texts (data, not instructions) and the survivors' helper-count range.
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research
T=$R/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90
show() { echo; echo "######## $1 ($(wc -c < "$1") bytes)"; head -c "${2:-6000}" "$1"; echo; }
show "$T/proof/TWO_ODD_HELPERS_90.md" 16000
show "$T/README.md" 3000
ls "$T/proof" "$T/results" "$T/checkers"
show "$T/run_checks.py" 2500
show "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/prior/WEIGHT_PROOF.md" 9000
echo; echo "######## grep 'at least 3|three odd|h >= 3|h>=3' in Weight_Parity folders"
grep -rnE 'at least three|three odd|h ?>= ?3|three extra odd|three helpers' "$R/AES_Unrestricted_Weight_Parity_2026_10_12" "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12" 2>/dev/null | grep -v '\.json:' | head -20
echo; echo "######## survivors helper counts"; python3 ~/xs-campaigns/2026-11-07-sprint/lb76/surv_h.py
