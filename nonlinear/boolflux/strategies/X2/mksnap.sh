#!/bin/bash
# X2: snapshot of the stopped hub long archive at time T (default now) into DST, plus the kernel bin dir
set -e
SRC=/home/joebachir20/xs-campaigns/2026-11-14-hub/long
DST=$1; T=${2:-$(date +%s)}
cd /home/joebachir20/xcr-boolflux
python3 nonlinear/boolflux/hub/snapshot.py $SRC $T $DST
mkdir -p $DST/bin && cp -n $SRC/bin/* $DST/bin/ 2>/dev/null || true
echo "$T" > $DST/SNAPSHOT_T
