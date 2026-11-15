#!/bin/bash
# P2: T06 front-keep + bottom annealing (P2 copy of P7 bopt with --calib --exact), build, polish.
#   boptjob.sh SEED ITERS BOPT_TIMEOUT POLISH_SECS
set -u
SEED=$1; IT=$2; TO=$3; PS=$4
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2
O=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/bopt
F=/home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a34-ad4-g134-gd13-xx100-43.circ.txt
mkdir -p $O; cd $S
timeout $TO python3 -u bopt.py $F --cap 13 --amax 34 --iters $IT --seed $SEED --calib --exact --out $O/s$SEED.json > $O/s$SEED.log 2>&1
[ -f $O/s$SEED.json ] || { echo "seed $SEED: no plan (timeout)" >> $O/summary.txt; exit 0; }
python3 bbuild.py $O/s$SEED.json $O/s$SEED.circ.txt > $O/s$SEED.build.log 2>&1
echo "seed $SEED: $(grep BEST $O/s$SEED.log) build: $(tail -1 $O/s$SEED.build.log)" >> $O/summary.txt
[ -f $O/s$SEED.circ.txt ] && bash $S/polish2.sh T06 $O/s$SEED.circ.txt 34 13 gate $SEED $PS t06bopt-s$SEED
# compare with the bar too
B=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/t06bopt-s$SEED/best.circ.txt
[ -f $B ] && python3 $S/save.py T06 $B t06bopt-s$SEED-bar --start $O/s$SEED.circ.txt --ref $F --only-better --path-certified true \
  --kernel /home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 --method "boptjob.sh: bopt --calib --exact + bbuild + fdrive_p2 gate" \
  --command "see runs/bopt/s$SEED.log and runs/t06bopt-s$SEED/command.txt" --seed $SEED --elapsed $PS >> $O/summary.txt 2>&1
