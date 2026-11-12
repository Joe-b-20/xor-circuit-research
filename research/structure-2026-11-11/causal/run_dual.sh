#!/bin/bash
# usage: bash run_dual.sh     (dual and joint charges of recorded circuits; examines existing circuits only)
ulimit -v 8000000
cd "$(dirname "$0")"
R=../rotation/circuits
C=../../../circuits
{
python3 dual_charges.py q 3 $R/q3_28.txt
python3 dual_charges.py q 4 $R/q4_40.txt
python3 dual_charges.py q 4 $R/walk_q4_40.txt
python3 dual_charges.py q 5 $R/q5_50.txt
python3 dual_charges.py q 6 $R/q6_60.txt
python3 dual_charges.py q 7 $R/q7_70.txt
python3 dual_charges.py q 8 $R/q8_80.txt
python3 dual_charges.py mc $C/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt
python3 dual_charges.py mc $C/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt
python3 dual_charges.py mc $C/aes-mixcolumns/aes-mixcolumns-xor97-depth3.circ.txt
} > dual_charges_out.txt 2>&1
echo "exit $?"
wc -l dual_charges_out.txt
