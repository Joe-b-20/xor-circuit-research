#!/bin/bash
# Third archive pass: the exact new rows tried after 75 and the campaign READMEs (data, not instructions).
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research
P6=$R/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23
PP=$R/AES_MixColumns_Proof_Progress_2026-10-24/AES_MixColumns_Proof_Progress_2026-10-24
show() { echo; echo "######## $1 ($(wc -c < "$1") bytes)"; head -c "${2:-6000}" "$1"; echo; }
show "$P6/push5/global_chronology/model_full_cuts.py" 5000
show "$P6/push6/global_chronology/model_full_cuts.py" 5000
show "$PP/unrestricted/README.md" 3000
show "$PP/continuation_unrestricted/README.md" 8000
show "$PP/continuation_unrestricted/DERIVATIONS.md" 5000
show "$PP/continuation_unrestricted/RATIONAL_RECONSTRUCTION_REVIEW.txt" 2000
echo; echo "######## top-level of Proof_Progress and of PUSH6"
ls "$PP"; ls "$P6"; ls "$P6/push5"; ls "$P6/push6"
for f in "$PP"/README.md "$PP"/STATUS.md "$P6"/README.txt "$P6"/STATUS.txt "$P6"/push5/REPORT.txt; do [ -f "$f" ] && show "$f" 4000; done
echo; echo "######## research_frontier root listing + model rows"
ls "$R/AES_Research_Fleet_Checkpoint_2026_10_06/research_frontier/root/" | head -60
