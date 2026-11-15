#!/bin/bash
# calibration 2: can the walk do the known 29 -> 28 step?  300 s per run
S=~/xs-campaigns/2026-11-15-study/X1; N=~/xcr-boolflux/nonlinear/nist/aes-sbox
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/X1
while systemctl --user is-active -q xs-H-x1-tune1; do sleep 3; done
k=0
for f in aes-sbox-a29-ad5-g137-gd32-xx108-22 aes-sbox-a29-ad5-g139-gd35-xx110-20 aes-sbox-a32-ad5-g104-gd30-xx72-5 aes-sbox-a30-ad4-g147-gd36-xx117-13; do
  for cfg in "2 0.05 5000 0.2" "1 0.02 20000 0.2" "3 0.05 20000 0.3"; do
    set -- $cfg; k=$((k+1))
    echo "== $f plus=$1 psplit=$2 horizon=$3 redec=$4 $(date -u +%H:%M:%S)"
    python3 x1walkc.py $N/$f.circ.txt $S/calib2/k$k --seconds 300 --seed 11 --plus $1 --psplit $2 --horizon $3 --redec $4 --dump 20 2>&1 | grep -v "^start"
  done
done
echo ALLDONE $(date -u)
