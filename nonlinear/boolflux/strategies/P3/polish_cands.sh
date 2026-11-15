#!/bin/bash
# Kernel-polish the best built candidates of a qanneal run: job.sh (pdrive gate mode) on each.
#   polish_cands.sh CANDDIR CAPGD SECS MAXN TAGPREFIX
# Candidates are taken in order of (G, GD) from their names g<G>-gd<GD>-<k>.circ.txt.
set -u
D=$1; CAP=$2; SECS=$3; MAXN=$4; PFX=$5
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
ls $D | grep circ.txt | sed 's/^g\([0-9]*\)-gd\([0-9]*\)-\(.*\)$/\1 \2 &/' | sort -n -k1 -k2 | head -$MAXN | \
while read G GD F; do
  echo "$(date -u +%T) polish $F"
  $S/job.sh $D/$F gate $CAP 1 $SECS $PFX-$(basename $F .circ.txt)
  cat /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/$PFX-$(basename $F .circ.txt)/record.txt 2>/dev/null | head -1
done
