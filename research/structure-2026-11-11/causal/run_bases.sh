#!/bin/bash
# usage: bash run_bases.sh    (dual charge inequalities on random triple bases of fixed recorded value sets)
ulimit -v 8000000
cd "$(dirname "$0")"
R=../rotation/circuits
C=../../../circuits
{
python3 cyclic_bases_check.py q 3 $R/q3_28.txt 5 1
python3 cyclic_bases_check.py q 4 $R/q4_40.txt 300 1
python3 cyclic_bases_check.py q 4 $R/walk_q4_40.txt 300 2
python3 cyclic_bases_check.py q 5 $R/q5_50.txt 200 3
python3 cyclic_bases_check.py q 6 $R/q6_60.txt 200 4
python3 cyclic_bases_check.py q 8 $R/q8_80.txt 150 5
python3 cyclic_bases_check.py mc $C/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt 100 6
python3 cyclic_bases_check.py mc $C/aes-mixcolumns/aes-mixcolumns-xor97-depth3.circ.txt 100 7
} > cyclic_bases_out.txt 2>&1
echo "exit $?"
cat cyclic_bases_out.txt
