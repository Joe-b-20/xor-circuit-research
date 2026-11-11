#!/bin/bash
# usage: bash batch_tables.sh      regenerates table_m3.txt, table_m4.txt, table_m5.txt (about 20 CPU-minutes)
cd "$(dirname "$0")"
ulimit -v 8000000
gcc -O2 -o exh exh.c || exit 1
python3 run_exh.py all 3 2 > table_m3.txt 2>&1
python3 run_exh.py all 4 3 2500000000 > table_m4.txt 2>&1
python3 run_exh.py file list_m5.txt 1 2500000000 > table_m5.txt 2>&1
