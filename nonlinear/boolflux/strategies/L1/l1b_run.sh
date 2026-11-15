#!/bin/bash
# L1b: one short guarded step on CPU 12 (under 2 minutes).  l1b_run.sh tonight|score [args]
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/L1 || exit 2
what=$1; shift
case $what in
  tonight) exec timeout 115 taskset -c 12 python3 tonight.py --budget 75 "$@" ;;
  score)   exec timeout 115 taskset -c 12 python3 l1b_score.py --budget 60 "$@" ;;
  check)   cd /home/joebachir20/xcr-boolflux && exec timeout 115 taskset -c 12 python3 nonlinear/boolflux/campaigns/aes_check.py "$@" ;;
  *) echo "unknown step $what"; exit 2 ;;
esac
