#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-cyclic || exit 1
ulimit -v 8000000
gcc -O2 -o lmin lmin.c || exit 1
for e in "$@"; do
  /usr/bin/time -f "example $e: %U s user" python3 examples.py $e > examples_$e.out 2>&1
done
cat examples_*.out
