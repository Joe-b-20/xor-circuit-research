#!/bin/bash
# Copy the minimal push5/push6 tree out of the archive (so its checker cannot modify archive files),
# preserving the relative layout that model_full_cuts.py expects.  The archive copy of the saved
# 75-proof source lacks research_deep/root/certify75.py; the package's certify75.py (same program,
# flattened layout; only old.system / old.direct_exclusion are used) is placed there instead.
set -e
SRC=~/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23
DST=~/xs-campaigns/2026-11-07-sprint/lb76/push6_copy
rm -rf "$DST"; mkdir -p "$DST/push5/global_chronology" "$DST/push6/global_chronology" "$DST/push5/sources/xor/AES_MixColumns_Lower_Bound_75/research_deep/root"
cp "$SRC/push5/global_chronology/model_full_cuts.py" "$SRC/push5/global_chronology/certify75_partial.py" "$SRC/push5/global_chronology/G75_NEW_CUT_PARTIAL_CERTIFICATES.json" "$SRC/push5/global_chronology/SCREEN75_FULL_CUT.json" "$DST/push5/global_chronology/"
cp "$SRC/push6/global_chronology/model_full_cuts.py" "$SRC/push6/global_chronology/certify75_partial.py" "$SRC/push6/global_chronology/G75_NEW_CUT_PARTIAL_CERTIFICATES.json" "$SRC/push6/global_chronology/SCREEN75_FULL_CUT.json" "$DST/push6/global_chronology/"
cp ~/xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks/certify75.py "$DST/push5/sources/xor/AES_MixColumns_Lower_Bound_75/research_deep/root/"
echo "copied:"; du -sh "$DST"
echo "######## head of push6 certify75_partial.py"; head -32 "$DST/push6/global_chronology/certify75_partial.py"
echo "######## head of push5 certify75_partial.py"; head -32 "$DST/push5/global_chronology/certify75_partial.py"
