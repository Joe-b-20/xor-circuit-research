#!/bin/bash
# P2 overnight T06 sweep: rank-1 bottom resynthesis at GD 13 (A34 front kept), then trb polish of
# each start under caps GD13 AD4 A34 (fdrive_p2: repair_keep 1, kernel bfx-94a75e2c18).
#   overnight_t06.sh FRONT TAG SECS_PER_START
# Results: verified circuits better than the bar file (34/4/134/13) land in P2/found/ with sidecars.
set -u
FRONT=$1; TAG=$2; SECS=${3:-1500}
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2
R=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/$TAG
BAR=/home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a34-ad4-g134-gd13-xx100-43.circ.txt
mkdir -p $R
cd $S
python3 orbsearch.py 13 $R/orb.json --fronts $FRONT --bottoms $(cat /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/bottoms.txt) > $R/orb.log 2>&1
python3 resyn.py $FRONT $R/orb.json $R/resyn --D 13 --keep 40 > $R/resyn.log 2>&1
i=0
for f in $(ls $R/resyn/c*.circ.txt | grep -v /c0000-); do
  i=$((i+1))
  bash $S/polish2.sh T06 $f 34 13 trb $((900+i)) $SECS $TAG-p$i
  # save against the bar, not only the start
  python3 $S/save.py T06 /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/$TAG-p$i/best.circ.txt $TAG-p$i-bar \
    --start $f --ref $BAR --only-better --path-certified true --kernel /home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 \
    --method "overnight_t06.sh: resyn start + fdrive_p2 trb" --command "see runs/$TAG-p$i/command.txt" --seed $((900+i)) --elapsed $SECS \
    >> $R/bar.txt 2>&1
done
