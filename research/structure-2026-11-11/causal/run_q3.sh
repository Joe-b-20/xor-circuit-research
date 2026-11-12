#!/bin/bash
# usage: bash run_q3.sh      (inspection of the recorded Q_3 circuit; no search)
ulimit -v 8000000
cd "$(dirname "$0")"
python3 q3_wirings.py > q3_wirings_out.txt 2>&1
echo "exit $?"
wc -l q3_wirings_out.txt
