#!/bin/bash
# Fourth archive pass: the 2026-10-08 bound75 push (first G=75 frontier scan) and its exclusions.
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research
B=$R/AES_Full_Neighborhood_Checkpoint_2026_10_09/aes_unrestricted_push_2026_10_08/bound75
show() { echo; echo "######## $1 ($(wc -c < "$1") bytes)"; head -c "${2:-6000}" "$1"; echo; }
show "$B/README.txt" 5000
show "$B/frontier_G74.json" 500
show "$B/packing_exclusion_proof.txt" 3000
show "$B/VERIFICATION.json" 1000
show "$B/integer_witness.json" 500
echo "######## frontier_G75.json keys / summary (first 1500 bytes)"
head -c 1500 "$B/frontier_G75.json"; echo
echo "######## SUMMARY.json (first 4000 bytes)"
head -c 4000 "$B/SUMMARY.json"; echo
ls "$B/premises" "$B/premises"/* 2>/dev/null | head -30
