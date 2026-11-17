#!/bin/bash
# ab.sh FN TAG BUDGET : paired simultaneous planned (CPU 4) vs blind (CPU 5) arms on the same pool
source $HOME/xs-campaigns/2026-11-17-ideas/03/env.sh
fn=$1; tag=$2; budget=$3; short=$4
G=$HOME/xs-campaigns/guard/xsrun
cd $D
$G main 4 i03-$tag-p $D/runs/$tag-p.log -- $D/py.sh 4 -m boolflux.hub.planexec --function $fn --pool $D/pool-$short.pkl --plan $D/plan-$short/plan.jsonl --out $D/runs/$tag-p --budget $budget --polish 45 --pull 30 --per-class 3 --seed $SEED $5
$G main 5 i03-$tag-b $D/runs/$tag-b.log -- $D/py.sh 5 -m boolflux.hub.planexec --function $fn --pool $D/pool-$short.pkl --blind --join-seconds 120 --out $D/runs/$tag-b --budget $budget --polish 45 --pull 30 --seed $SEED
