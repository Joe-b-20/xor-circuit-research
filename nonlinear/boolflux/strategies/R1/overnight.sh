#!/bin/bash
# R1 overnight pipeline: exact window AND removal on the hub archive + kernel grind of the A-1 results.
#   overnight.sh HOURS CPU SEED
# Each cycle (~70 min): snapshot of the live hub archive (hub/snapshot.py, race-free), mc1.py 10 min over all
# records with A <= 29, seq2.py on mc1's 3-AND no_flat windows, then grind.py 60 min on the distinct A = 28
# results with G <= 140 (both AD 4 and AD 5 pools, 30 min each).  grind.py aes_checks every result that is
# not dominated by the snapshot's cell minima nor by the NIST pin and writes it with a JSON sidecar to
# OUT/found/.  Success = any file in OUT/found/ (each one is a verified new Pareto point at that time).
set -u
HOURS=$1; CPU=$2; SEED=$3
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/R1
B=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/hub
HUB=/home/joebachir20/xs-campaigns/2026-11-14-hub/long
OUT=/home/joebachir20/xs-campaigns/2026-11-15-study/R1/overnight-$SEED
mkdir -p $OUT/found
END=$(( $(date +%s) + $(python3 -c "print(int($HOURS*3600))") ))
cyc=0
while [ $(date +%s) -lt $END ]; do
  cyc=$((cyc+1)); C=$OUT/c$cyc; mkdir -p $C
  T=$(date +%s); python3 $B/snapshot.py $HUB $T $C/snap > $C/snap.log 2>&1 || { sleep 60; continue; }
  IDS=$(python3 -c "
import json, glob
print(','.join(json.load(open(f))['id'] for f in glob.glob('$C/snap/archive/*.json') if not f.endswith('cells.json') and json.load(open(f))['A'] <= 29))")
  [ -z "$IDS" ] && { sleep 600; continue; }
  taskset -c $CPU python3 $S/mc1.py $C/snap $IDS ${MC1H:-0.17} $((SEED*100+cyc)) $C/mc1.jsonl > $C/mc1.log 2>&1
  taskset -c $CPU python3 $S/seq2.py $C/snap $C/mc1.jsonl $C/seq2.jsonl --kmax 10 --amax-circ 29 > $C/seq2.log 2>&1
  for AD in 4 5; do
    FILES=$(python3 -c "
import glob, sys
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux import core
from boolflux.hub.common import metrics
seen = {}
for f in sorted(glob.glob('$C/mc1/*.bfx') + glob.glob('$C/seq2/*.bfx')):
    m = metrics(core.from_kernel(open(f).read()))
    if m[0] == 28 and m[1] == $AD and m[2] <= 140 and m not in seen: seen[m] = f
print(' '.join(seen.values()))")
    [ -n "$FILES" ] && taskset -c $CPU python3 $S/grind.py $C/snap $OUT/found ${GRS:-1800} 60 $((SEED*100+cyc*10+AD)) $FILES >> $C/grind$AD.log 2>&1
  done
done
echo "overnight done $(date -u) cycles $cyc"
