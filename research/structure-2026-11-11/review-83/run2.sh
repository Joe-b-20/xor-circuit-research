#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-83
ulimit -v 8000000
python3 families.py > families_out.txt 2>&1
echo exit $? >> families_out.txt
