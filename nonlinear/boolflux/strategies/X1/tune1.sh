#!/bin/bash
# walk parameter grid on BP32 (a32-ad5-g104): best A and time per setting
S=~/xs-campaigns/2026-11-15-study/X1; N=~/xcr-boolflux/nonlinear/nist/aes-sbox
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/X1
F=${F:-$N/aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt}
T=${T:-60}
k=0
for cfg in "1 0.02 20000 0.2" "2 0.02 20000 0.2" "2 0.05 5000 0.2" "3 0.02 20000 0.2" "1 0.005 100000 0.2" "2 0.02 200000 0.5" "1 0.02 2000 0.2" "3 0.1 3000 0.3"; do
  set -- $cfg; k=$((k+1))
  for seed in 1 2; do
    echo "== cfg plus=$1 psplit=$2 horizon=$3 redec=$4 seed=$seed"
    python3 x1walkc.py $F $S/${OUT:-tune1}/c$k --seconds $T --seed $seed --plus $1 --psplit $2 --horizon $3 --redec $4 2>&1 | grep -v "^start"
  done
done
echo ALLDONE
