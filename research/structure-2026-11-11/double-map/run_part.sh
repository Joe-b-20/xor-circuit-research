#!/bin/bash
# usage: bash run_part.sh T N [maxnodes]     e.g.  bash run_part.sh m2 9 6000000000
# Exhaustive search with partition pruning (exh_part.c): is there a circuit for D_T with 2m + N gates?
cd "$(dirname "$0")"
ulimit -v 8000000
[ -x ./exh_part ] || gcc -O2 -o exh_part exh_part.c
T="$1"; N="$2"; MAXNODES="${3:-0}"
M=$(python3 -c "import geom,dmap,sys; t=sys.argv[1]; print(len(geom.m2_T() if t=='m2' else dmap.parse_t(t)))" "$T")
MINB=$((2*M-N)); if [ "$MINB" -lt 1 ]; then MINB=1; fi
TAG=$(echo "$T" | tr '|' '_')
PF="parts_${TAG}_${MINB}.txt"
ROWS=$(python3 partitions.py "$T" "$MINB" --dump "$PF" | grep '^rows:' | cut -d: -f2)
echo "T=$T m=$M N=$N min_blocks=$MINB partitions=$(head -1 $PF | cut -d' ' -f1)"
/usr/bin/time -f "cpu %U s" ./exh_part "$M" "$N" "$PF" "$MAXNODES" $ROWS
