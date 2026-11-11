#!/bin/bash
# Usage: bash run_enum5.sh      (a few CPU-minutes, 4 threads, about 300 MB)
set -e
cd "$(dirname "$0")"
ulimit -v 8000000
gcc -O2 -fopenmp -o enum5.bin enum5.c
export OMP_NUM_THREADS=4
( time ./enum5.bin n5_noncircuit_small.txt ) > enum5.out 2> enum5.time
cat enum5.out
cat enum5.time
rm -f enum5.bin
