#!/bin/bash
# usage: bash run_triples.sh    (triple counts of the value sets of recorded circuits; inspection only)
ulimit -v 8000000
cd "$(dirname "$0")"
R=../rotation/circuits
C=../../../circuits
python3 triple_count.py $R/q2_16.txt $R/q3_28.txt $R/q4_40.txt $R/walk_q4_40.txt $R/q4-x11_40.txt $R/q4-x12_42.txt \
  $R/q4-x13_42.txt $R/q5_50.txt $R/walk_q5_50.txt $R/q6_60.txt $R/q6-x20_62.txt $R/q7_70.txt $R/q8_80.txt \
  $R/walk_q8_80.txt $R/q8-x17_82.txt $R/q8-x17x37_85.txt $R/q12_120.txt $R/q20_200.txt \
  $C/aes-mixcolumns/*.circ.txt $C/aes-invmixcolumns/*.circ.txt > triple_count_out.txt 2>&1
echo "exit $?"
cat triple_count_out.txt
