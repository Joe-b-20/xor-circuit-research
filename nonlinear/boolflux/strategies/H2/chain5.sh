#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/d13
R=~/xs-campaigns/2026-11-15-study/H2/real
N=/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox
export H2_BUILDLIST=~/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt
bash ./rbatch.sh $D/list2v.txt 1
bash ./rbatch.sh $D/list4.txt 0 1 4 5 6 7
# semi-members over the AD4 span (closest to 13: it has 69 14-member layers), member-seeded, gammas 1 6
for g in 1 6; do
  P=$R/ad4a-semi-g$g
  [ -f $P.img ] || python3 rprep.py file:$N/aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt $g $P semi > $P.prep 2>&1
  timeout 2400 ./gen13 13 $(cat $P.n0) < $P.img > $P.K13.gsol 2> $P.K13.gerr
  echo "ad4a semi gamma=$g K=13 member-seeded: $(tail -1 $P.K13.gerr) | $(python3 fastrank.py $P $P.K13.gsol)"
  if [ -s $P.K13.gsol.cov ]; then python3 rvd.py $P $P.K13.gsol.cov 4 | tail -3; fi
done
bash ./rbatch.sh $D/list3.txt 0 1 4 5 6 7
bash ./rbatch.sh $D/list2a.txt 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
