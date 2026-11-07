#!/bin/bash
# Copy the archive's h=2 package into oddh/ (read-only on the archive) and compile the three checkers.
set -e
A=~/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90
D=~/xs-campaigns/2026-11-07-sprint/oddh
mkdir -p "$D/archive_copy" "$D/run"
cp -r "$A/checkers" "$A/results" "$A/run_checks.py" "$A/proof" "$A/README.md" "$A/START_HERE.md" "$D/archive_copy/"
echo "== archive top level =="; ls "$A"
echo "== recovered_originals present? =="; ls -d "$A/recovered_originals" 2>&1 || true
echo "== expected primary.json =="; head -c 1200 "$A/results/reproduction/primary.json"; echo
echo "== expected triangles.json =="; cat "$A/results/reproduction/triangles.json"; echo
echo "== expected independent_audit.json =="; cat "$A/results/independent_audit.json"; echo
echo "== compile =="
cd "$D/run"
for s in verify_two_helpers_primary verify_two_helpers_triangles independent_two_helper_audit; do
  /usr/bin/time -f "compile $s: %es" nice -n 8 g++ -O2 -std=c++17 "$D/archive_copy/checkers/$s.cpp" -o "$D/run/$s"
done
ls -la "$D/run"
