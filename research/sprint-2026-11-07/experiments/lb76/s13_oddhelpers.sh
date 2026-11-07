#!/bin/bash
# Locate the odd-helper parity theorems (h=0 => G>=92, h=2 => G>=88, 3<=h<=31 for G<=87) and their proofs (data).
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research
show() { echo; echo "######## $1 ($(wc -c < "$1") bytes)"; head -c "${2:-6000}" "$1"; echo; }
echo "######## grep for the odd-helper statements"
grep -rlE 'no odd helper|zero odd helper|two odd helper|exactly two|at least three odd|>= ?92|92 gates|at least 92' "$R/AES_Unrestricted_Weight_Parity_2026_10_12" "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12" "$R/AES_Joint_Accounting_Case_Bounds_2026_10_12" "$R/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90" "$R/AES_Three_Helper_Obstruction_2026_10_02" 2>/dev/null | head -30
echo; echo "######## grep -n context (first 60 lines)"
grep -rnE 'no odd helper|zero odd helper|two odd helper|exactly two odd|at least three|>= ?92|92 gates|h ?= ?0|h ?= ?2\b' "$R/AES_Unrestricted_Weight_Parity_2026_10_12" "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/PROOF.md" "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/prior" "$R/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90" 2>/dev/null | grep -v '\.json:' | head -60
ls "$R/AES_Unrestricted_Weight_Parity_2026_10_12/aes_weight_parity_2026_10_12/" "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/prior/" "$R/AES_Joint_Accounting_Case_Bounds_2026_10_12/aes_joint_accounting_case_bounds_2026_10_12/" "$R/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90/" "$R/AES_Three_Helper_Obstruction_2026_10_02/aes_helper_bound/" 2>&1
show "$R/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90/START_HERE.md" 7000
show "$R/AES_Unrestricted_Weight_Parity_2026_10_12/aes_weight_parity_2026_10_12/CHANGELOG.md" 5000
show "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/PROOF.md" 14000
show "$R/AES_Joint_Accounting_Case_Bounds_2026_10_12/aes_joint_accounting_case_bounds_2026_10_12/MANIFEST.json" 3000
show "$R/AES_Three_Helper_Obstruction_2026_10_02/aes_helper_bound/MANIFEST_SHA256.json" 3000
show "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/prior/WEIGHT_RESULTS.json" 2500
