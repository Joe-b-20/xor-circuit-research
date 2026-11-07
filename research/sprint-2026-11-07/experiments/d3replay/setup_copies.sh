#!/bin/bash
# Copy packages A and B into d3replay (read-only on repo and archive).
set -e
D=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay
SRC_A=/home/joebachir20/xor-circuit-research/lower-bound-proofs/mixcolumns-lb93-depth3
SRC_B=/home/joebachir20/xs-campaigns/2026-11-07-sprint/import/zip/research/MixColumns_Ordinary_Union_Checkpoint
mkdir -p "$D/A/lb93" "$D/B/ckpt_raw" "$D/logs"
cp -a "$SRC_A/." "$D/A/lb93/"
cp -a "$SRC_B/." "$D/B/ckpt_raw/"
du -sh "$D/A/lb93" "$D/B/ckpt_raw"
find "$D/A/lb93" -type f | wc -l
find "$D/B/ckpt_raw" -type f | wc -l
echo setup done
