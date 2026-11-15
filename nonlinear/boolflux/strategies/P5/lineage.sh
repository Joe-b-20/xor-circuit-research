#!/bin/bash
# lineage.sh START CAPAD TAG N SEED0 [GDCAP_GATE GDCAP_MIX]: N rounds of (gate cap GATE 300 s, mix cap MIX
# 400 s), each round starting from the lowest-G (then GD) verified circuit found so far in this lineage.
P5=/home/joebachir20/xs-campaigns/2026-11-15-targets/P5
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P5
CUR=$1; AD=$2; TAG=$3; N=$4; SEED=$5; GG=${6:-30}; GM=${7:-26}
for r in $(seq 1 $N); do
  for st in "gate $GG 300" "mix $GM 400"; do
    set -- $st
    T=$TAG-r$r-$1$2
    $S/cjob.sh $CUR $AD $2 $1 $SEED $3 $T
    SEED=$((SEED + 1))
    B=$(python3 - $P5/runs/$T <<'EOF'
import sys, glob
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux import core
m = core.Model.load('nist'); best = None
for f in glob.glob(sys.argv[1] + '/best.circ.txt') + glob.glob(sys.argv[1] + '/pareto/*.circ.txt'):
    c = core.read_ncff(f); x = c.metrics(m)
    if x['A'] > 32: continue
    k = (x['G'], x['GD'])
    if best is None or k < best[0]: best = (k, f)
print(best[1] if best else '')
EOF
)
    echo "$(date -u +%T) $T: best $B"
    [ -n "$B" ] && { cp $B $P5/runs/$T/next.circ.txt; CUR=$P5/runs/$T/next.circ.txt; }
  done
done
echo DONE $(date -u +%T)
