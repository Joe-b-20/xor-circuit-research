#!/bin/bash
# kernel polish of a sel circuit: polish.sh START OUT SECONDS SEEDS [extra cli args...]
# objective a,ad,cost,gd; caps A and AD of the start (kept); CPUs 2-3
set -e
export BOOLFLUX_CACHE=$HOME/xs-campaigns/2026-11-17-ideas/02/cache
W=$HOME/xcr-idea-02
start=$1; out=$2; secs=$3; seeds=$4; shift 4
read A AD <<<$(cd $W/search/nonlinear && python3 -c "
import sys; from boolflux import core
m = core.read_ncff(sys.argv[1]).metrics(); print(m['A'], m['AD'])" "$start")
cd $W
exec taskset -c 2-3 python3 search/nonlinear/boolflux/cli.py run --target aes-sbox-sel --model nist \
  --start "$start" --objective a,ad,cost,gd --cap-a $A --cap-ad $AD \
  --iters 100000000 --seconds $secs --seeds $seeds --jobs 2 --out "$out" "$@"
