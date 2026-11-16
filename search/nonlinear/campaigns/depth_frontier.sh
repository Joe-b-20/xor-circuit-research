#!/usr/bin/env bash
# G at a gate-depth cap only (A and AD free): the published best G at GD <= d, against
# searches started from published circuits at depth d and d+1 (the deeper one is first
# repaired to depth d by the kernel's penalty).
#   usage: depth_frontier.sh OUTDIR ITERS SEEDS JOBS "d:startfile ..." [extra cli args]
set -euo pipefail
OUT=$1; ITERS=$2; SEEDS=$3; JOBS=$4; SPECS=$5; shift 5
cd "$(dirname "$0")/../../.."
mkdir -p "$OUT"
for spec in $SPECS; do
  d=${spec%%:*}; f=${spec#*:}
  b=gd$d-from-$(basename "$f" .circ.txt)
  [ -f "$OUT/$b/summary.json" ] && continue
  python3 search/nonlinear/boolflux/cli.py run --target aes --model nist --start "search/nonlinear/seeds/aes-sbox/$f.circ.txt" \
    --objective cost,gd --cap-gd "$d" --iters "$ITERS" --seeds "$SEEDS" --jobs "$JOBS" \
    --out "$OUT/$b" "$@" > "$OUT/$b.out" 2>&1 || echo "FAILED $b" >> "$OUT/FAILED"
  echo "$b $(tail -1 "$OUT/$b.out" | sed 's#-> /.*##')"
done
