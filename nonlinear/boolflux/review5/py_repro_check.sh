#!/bin/bash
# Review 5 (P24): re-run the winning job of the 28/4/133/20 entry and of 4 sampled deterministic
# entries, with the run's own binary (snapshot) and with the current code (head).
# Output: review5/py_repro_check.txt and results/REPRO-CHECK.json.  About 5 CPU-minutes.
cd ~/xcr-review5 || exit 1
O=nonlinear/boolflux/review5/py_repro_check.txt
G="$HOME/xs-campaigns/guard/xsfg H -- taskset -c 12"
{
  date -u
  $G python3 nonlinear/boolflux/campaigns/manifest.py --check-repro 1 --only g133-a28-gd20 --mode both
  echo "exit status $?"
  $G python3 nonlinear/boolflux/campaigns/manifest.py --check-repro 4 --seed 1 --mode both
  echo "exit status $?"
  date -u
} > $O 2>&1
