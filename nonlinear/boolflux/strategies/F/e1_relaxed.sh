#!/usr/bin/env bash
# E1: gate kernel under a hard GD cap from circuits that already meet it (incl. one level lower).
#   usage: e1_relaxed.sh OUTDIR ITERS SEEDS "cap:startfile ..."
set -uo pipefail
OUT=$1; ITERS=$2; SEEDS=$3; SPECS=$4
SNAP=$HOME/xs-campaigns/2026-11-13-aes/F/snap/boolflux
mkdir -p "$OUT"
for spec in $SPECS; do
  d=${spec%%:*}; f=${spec#*:}
  b=gd$d-from-$(basename "$f" .circ.txt)
  [ -f "$OUT/$b/summary.json" ] && continue
  /usr/bin/time -f "%e s wall" taskset -c 1-4 python3 $SNAP/cli.py run --target aes --model nist --start "$f" \
    --objective cost,gd --cap-gd "$d" --cap-ad 4 --iters "$ITERS" --seeds "$SEEDS" --jobs 4 \
    --out "$OUT/$b" > "$OUT/$b.out" 2>&1
  echo "$(date -u +%H:%M:%S) $b $(grep '^best:' "$OUT/$b.out" | sed 's#-> /.*##') $(tail -1 $OUT/$b.out)"
done
