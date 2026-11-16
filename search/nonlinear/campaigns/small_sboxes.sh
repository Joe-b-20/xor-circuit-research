#!/usr/bin/env bash
# Small S-boxes from naive ANF starts under several models.
#   usage: small_sboxes.sh OUTDIR JOBS [names...]
set -euo pipefail
OUT=$1; JOBS=$2; shift 2
cd "$(dirname "$0")/../../.."
NAMES=${*:-"present gift skinny64 prince midori_sb0 midori_sb1 piccolo rectangle klein noekeon pride serpent_s0 serpent_s1 serpent_s2 serpent_s3 serpent_s4 serpent_s5 serpent_s6 serpent_s7 printcipher chi3 ascon keccak_chi5"}
mkdir -p "$OUT"
for t in $NAMES; do
  for cfg in ${CONFIGS:-"bgc:cost" "gc6:cost" "nist:a,cost" "bgc:gd,cost"}; do
    model=${cfg%%:*}; obj=${cfg#*:}
    d="$OUT/$t-$model-${obj//,/_}"
    [ -f "$d/summary.json" ] && continue
    python3 search/nonlinear/boolflux/cli.py pipe --target $t --model $model --objective $obj \
      --iters 100000 --skel-iters 2000 --seeds 1-8 --rounds 3 --jobs "$JOBS" --out "$d" > "$d.out" 2>&1 \
      || echo "FAILED $d" >> "$OUT/FAILED"
    echo "$t $model $obj $(tail -1 "$d.out")"
  done
done
