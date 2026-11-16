#!/usr/bin/env bash
# AES S-box from starting implementations, NIST model, objective G:
#   - the naive ANF circuit (no structure), gate search only;
#   - Boyar-Peralta's 113-gate circuit (NIST old-2020 file), uncapped and at its own AND depth 6
#     and gate depth 27.
#   usage: aes_starts.sh OUTDIR ITERS SEEDS JOBS ROUNDS
set -euo pipefail
OUT=$1; ITERS=$2; SEEDS=$3; JOBS=$4; ROUNDS=$5
cd "$(dirname "$0")/../../.."
mkdir -p "$OUT"
BP=search/nonlinear/seeds/old-2020/aes-sbox-fwd-g113-a32-d27-ad6.slp
run() { local name=$1; shift
  [ -f "$OUT/$name/summary.json" ] && return 0
  python3 search/nonlinear/boolflux/cli.py run --target aes --model nist --objective cost,gd --iters "$ITERS" \
    --seeds "$SEEDS" --jobs "$JOBS" --rounds "$ROUNDS" --out "$OUT/$name" "$@" > "$OUT/$name.out" 2>&1 || true
  echo "$name $(tail -1 "$OUT/$name.out" | sed 's#-> /.*##')"; }
run anf --start anf
run bp113 --start "$BP"
run bp113-caps --start "$BP" --cap-ad 6 --cap-gd 27
