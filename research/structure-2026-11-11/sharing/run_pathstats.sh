#!/bin/bash
# path statistics on the recorded rotation circuits (read-only)
ulimit -v 8000000
cd "$(dirname "$0")"
C=../rotation/circuits
python3 pathstats.py 4 $C/walk_q4_40.txt 2
python3 pathstats.py 4 $C/q4_40.txt 2
python3 pathstats.py 4 $C/walk_q4_40.txt 3
python3 pathstats.py 5 $C/q5_50.txt 2
python3 pathstats.py 7 $C/q7_70.txt 2
python3 pathstats.py 8 $C/q8_80.txt 4
python3 pathstats.py 8 $C/q8_80.txt 7
python3 pathstats.py 3 $C/q3_28.txt 2
python3 pathstats.py 3 $C/q3_28.txt 1
