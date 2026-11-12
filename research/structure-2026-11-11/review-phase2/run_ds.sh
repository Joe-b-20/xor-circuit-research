#!/bin/bash
cd "$(dirname "$0")"
ulimit -v 8000000
for s in 1 2 3; do python3 ds_check.py 3000 $s; done 2>&1 | tee ds_check_out.txt
