#!/bin/bash
# calibration 2b (trimmed calib2: CPU 10 is shared by three jobs): 300 s per run
S=~/xs-campaigns/2026-11-15-study/X1; N=~/xcr-boolflux/nonlinear/nist/aes-sbox
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/X1
k=20
while read f p1 p2 p3 p4; do
  k=$((k+1))
  echo "== $f plus=$p1 psplit=$p2 horizon=$p3 redec=$p4 $(date -u +%H:%M:%S)"
  python3 x1walkc.py $N/$f.circ.txt $S/calib2/k$k --seconds 300 --seed 11 --plus $p1 --psplit $p2 --horizon $p3 --redec $p4 --dump 20 2>&1 | grep -v "^start"
done <<LIST
aes-sbox-a29-ad5-g137-gd32-xx108-22 3 0.05 20000 0.3
aes-sbox-a32-ad5-g104-gd30-xx72-5 2 0.05 5000 0.2
aes-sbox-a30-ad4-g147-gd36-xx117-13 2 0.05 5000 0.2
aes-sbox-a29-ad5-g139-gd35-xx110-20 2 0.05 5000 0.2
LIST
echo ALLDONE $(date -u)
