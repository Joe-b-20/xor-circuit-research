#!/bin/bash
# js2.sh G EARLY LATE E TAG "EXTRA ARGS" K [K ...]
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
G=$1; EARLY=$2; LATE=$3; E=$4; TAG=$5; EXTRA=$6; shift 6
for K in "$@"; do
  echo "== gamma=$G early=$EARLY late=$LATE E=$E K=$K extra=$EXTRA"
  timeout 1500 python3 -u jsat.py --gamma $G --early $EARLY --late $LATE --E $E --K $K $EXTRA --out ~/xs-campaigns/2026-11-15-study/H2/jsat/$EARLY-$LATE-g$G-E$E-K$K$TAG.json | grep -v "^early\|^late"
  echo "exit ${PIPESTATUS[0]}"
done
