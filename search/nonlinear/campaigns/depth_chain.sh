#!/usr/bin/env bash
# Depth chain: start at a circuit with gate depth D, search under GD <= D-1, then start the
# next step from that step's best, down to GD <= LAST.
#   usage: depth_chain.sh OUTDIR START.circ.txt D LAST ITERS SEEDS JOBS ROUNDS
set -euo pipefail
OUT=$1; START=$2; D=$3; LAST=$4; ITERS=$5; SEEDS=$6; JOBS=$7; ROUNDS=$8
cd "$(dirname "$0")/../../.."
mkdir -p "$OUT"
cur=$START
for ((d = D - 1; d >= LAST; d--)); do
  b=gd$d-chain
  if [ ! -f "$OUT/$b/summary.json" ]; then
    python3 search/nonlinear/boolflux/cli.py run --target aes --model nist --start "$cur" --objective cost,gd \
      --cap-gd "$d" --iters "$ITERS" --seeds "$SEEDS" --jobs "$JOBS" --rounds "$ROUNDS" \
      --out "$OUT/$b" > "$OUT/$b.out" 2>&1 || { echo "$b $(tail -1 "$OUT/$b.out")"; exit 0; }
  fi
  echo "$b $(tail -1 "$OUT/$b.out" | sed 's#-> /.*##')"
  cur=$OUT/$b/best.circ.txt
done
