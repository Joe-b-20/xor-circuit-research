#!/bin/bash
# usage: bash run_loops.sh   (test of the cyclic charge inequalities on non-executable based systems; no search)
ulimit -v 8000000
cd "$(dirname "$0")"
R=../rotation/circuits
C=../../../circuits
{
python3 cyclic_loop_check.py q 3 $R/q3_28.txt 60 20 1
python3 cyclic_loop_check.py q 4 $R/q4_40.txt 60 20 2
python3 cyclic_loop_check.py q 6 $R/q6_60.txt 40 15 3
python3 cyclic_loop_check.py q 8 $R/q8_80.txt 30 10 4
python3 cyclic_loop_check.py mc $C/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt 30 10 5
} > cyclic_loop_out.txt 2>&1
echo "exit $?"
cat cyclic_loop_out.txt
