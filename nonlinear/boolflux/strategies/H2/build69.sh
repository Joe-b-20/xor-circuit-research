#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/real
L=~/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt
# skip already listed ones: rvd rebuilds the same files (same names); only new names are appended
H2_BUILDLIST=$D/build69.new python3 rvd.py $D/ad4a-g1 $D/ad4a-g1.K14.gsol 69 > $D/ad4a-g1.build69.log 2>&1 &
P=$!
touch $D/build69.new
while kill -0 $P 2>/dev/null; do
  sort -u $D/build69.new | while read f; do grep -qxF "$f" $L || echo "$f" >> $L; done
  sleep 20
done
sort -u $D/build69.new | while read f; do grep -qxF "$f" $L || echo "$f" >> $L; done
