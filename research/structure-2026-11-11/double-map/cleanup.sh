#!/bin/bash
# usage: bash cleanup.sh    removes binaries and regenerable intermediate files in this directory
cd "$(dirname "$0")"
rm -rf __pycache__ exh exh_part parts_*.txt batch_tables.log batch_tables.done nohup.out
rm -f recheck.py batch_m5.sh status.sh m2_exh_B.txt
ls -la
