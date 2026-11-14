#!/usr/bin/env bash
# Cap repair baseline (track F): rebuild-only workflow (Paar rebuild of the unchanged skeleton +
# gate kernel, penalised repair, adaptive rounds) = bench "rebuild" configuration via cli.py flow
# at repo HEAD.  One seed per run, runs sequential on the unit's CPU.
#   usage: repair.sh OUTDIR CPU SECONDS "cap:start ..." SEED_FROM SEED_TO
set -uo pipefail
OUT=$1; CPU=$2; SECS=$3; SPECS=$4; S0=$5; S1=$6
REPO=$HOME/xcr-boolflux
mkdir -p "$OUT"
for ((s = S0; s <= S1; s++)); do
  for spec in $SPECS; do
    d=${spec%%:*}; f=${spec#*:}
    b=gd$d-$(basename "$f" .circ.txt)-s$s
    [ -f "$OUT/$b/summary.json" ] && continue
    t0=$(date +%s)
    ( cd $REPO && python3 nonlinear/boolflux/cli.py flow --target aes --model nist --start "$f" \
        --objective cost,gd --cap-gd "$d" --config full --skel-set iters=0 --adaptive --round-s 30 \
        --seconds "$SECS" --seeds "$s" --jobs 1 --cpus "$CPU" --out "$OUT/$b" > "$OUT/$b.out" 2>&1 )
    echo "$(date -u +%H:%M:%S) $b $(( $(date +%s) - t0 )) s: $(grep -m1 '^best' "$OUT/$b.out" | cut -c1-150)"
  done
done
