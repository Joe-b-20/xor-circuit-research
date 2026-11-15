#!/bin/bash
# X2: final A/B evaluation (goal distance + L1's eval_run measures) of the four arms
X=/home/joebachir20/xs-campaigns/2026-11-15-study/X2; S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies
cd $X
python3 $S/X2/ab_compare.py snap0 gen1 goal1 goal2 gen2 --json $X/ab_final.json > $X/ab_final.txt 2>&1
mkdir -p $X/l1eval
( cd $S/L1 && L1_OUT=$X/l1eval python3 l1_load.py gen1=$X/gen1 goal1=$X/goal1 goal2=$X/goal2 gen2=$X/gen2 && L1_OUT=$X/l1eval python3 eval_run.py ) > $X/ab_final_l1eval.txt 2>&1
for a in gen1 goal1 goal2 gen2; do python3 $S/X2/retro.py $X/$a > $X/retro_$a.txt 2>&1; done
echo done
