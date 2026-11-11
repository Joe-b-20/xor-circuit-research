#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-charges
ulimit -v 8000000
for K in 6 7 8 10; do timeout 600 python3 lemma_sat.py $K; done
for K in 8 10; do timeout 600 python3 lemma_sat.py $K --sym; done
