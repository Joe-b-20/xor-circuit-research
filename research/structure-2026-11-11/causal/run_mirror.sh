#!/bin/bash
# usage: bash run_mirror.sh    (instance checks of the proof bookkeeping on recorded circuits; no search)
ulimit -v 8000000
cd "$(dirname "$0")"
R=../rotation/circuits
{
python3 mirror_check.py 3 $R/q3_28.txt 0
python3 mirror_check.py 3 $R/q3_28.txt 1
python3 mirror_check.py 3 $R/q3_28.txt 2
python3 mirror_check.py 4 $R/q4_40.txt 0
python3 mirror_check.py 4 $R/q4_40.txt 0,2
python3 mirror_check.py 4 $R/q4_40.txt 1,3
python3 mirror_check.py 4 $R/walk_q4_40.txt 0,2
python3 mirror_check.py 5 $R/q5_50.txt 1,3
python3 mirror_check.py 6 $R/q6_60.txt 0,2,4
python3 mirror_check.py 7 $R/q7_70.txt 1,3,6
python3 mirror_check.py 8 $R/q8_80.txt 0,2,4,6
python3 mirror_check.py 8 $R/q8_80.txt 1,3,5,7
python3 mirror_check.py 8 $R/walk_q8_80.txt 0,2,4,6
python3 mirror_check.py 12 $R/q12_120.txt 0,2,4,6,8,10
python3 mirror_check.py 20 $R/q20_200.txt 1,4,7,10,13,16,19
} > mirror_check_out.txt 2>&1
echo "exit $?"
cat mirror_check_out.txt
