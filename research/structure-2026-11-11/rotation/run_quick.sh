#!/bin/bash
# Heuristic upper bound with the repository's search engine (one worker, one core):
#   bash run_quick.sh m SECONDS TAG [SEED] [j:k,...]
# writes mats/qM[-TAG].mat.txt and the run directory runs/qM-TAG inside this directory.
set -e
ulimit -v 8000000
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
M="$1"; SECS="$2"; TAG="$3"; SEED="${4:-0}"; EXTRA="$5"
mkdir -p "$HERE/mats" "$HERE/runs"
MAT="$HERE/mats/q$M.mat.txt"
if [ -n "$EXTRA" ]; then
  MAT="$HERE/mats/q$M-$TAG.mat.txt"
  (cd "$HERE" && python3 gen_mat.py "$M" "$MAT" "$EXTRA")
else
  (cd "$HERE" && python3 gen_mat.py "$M" "$MAT")
fi
cd "$ROOT"
python3 search/xorflux quick "$MAT" --seconds "$SECS" --seed "$SEED" --seeds root --out "$HERE/runs/q$M-$TAG" 2>&1 | tail -n 15
ls "$HERE/runs/q$M-$TAG"
