#!/usr/bin/env bash
# For every NIST AES (inverse) S-box circuit: search under that circuit's own metrics as caps
# (A <= A0, AD <= AD0, GD <= GD0), minimising G then GD.  A result with G < G0 dominates the
# published circuit at its own point.
#   usage: nist_frontier.sh OUTDIR DIR(aes-sbox|aes-invsbox) ITERS SEEDS JOBS [extra cli args]
set -euo pipefail
OUT=$1; DIR=$2; ITERS=$3; SEEDS=$4; JOBS=$5; shift 5
cd "$(dirname "$0")/../../.."
TARGET=aes; [ "$DIR" = aes-invsbox ] && TARGET=aes-inv
mkdir -p "$OUT"
for f in nonlinear/nist/$DIR/*.circ.txt; do
  b=$(basename "$f" .circ.txt)
  A=$(echo "$b" | sed -E 's/.*-a([0-9]+)-ad.*/\1/'); AD=$(echo "$b" | sed -E 's/.*-ad([0-9]+)-g.*/\1/')
  GD=$(echo "$b" | sed -E 's/.*-gd([0-9]+)-xx.*/\1/')
  [ -f "$OUT/$b/summary.json" ] && continue
  python3 nonlinear/boolflux/cli.py run --target $TARGET --model nist --start "$f" --objective cost,gd \
    --cap-a "$A" --cap-ad "$AD" --cap-gd "$GD" --iters "$ITERS" --seeds "$SEEDS" --jobs "$JOBS" \
    --out "$OUT/$b" "$@" > "$OUT/$b.out" 2>&1 || echo "FAILED $b" >> "$OUT/FAILED"
  echo "$b $(tail -1 "$OUT/$b.out")"
done
