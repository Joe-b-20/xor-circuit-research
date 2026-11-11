#!/bin/bash
# usage: bash m2_exhaustive.sh A|B|R [maxnodes]
# Exhaustive checks that M2 has no circuit with 25 gates (9 non-output gates), by final partition:
#   A : final partition with 8 blocks (171 valid ones); any 9 extras, at most one of them odd or dependent
#   B : final partition with 7 blocks (4786 valid ones); then all 9 extras are independent even signals
#   R : residual case of Theorem D only: 8 independent even signals and one helper u3+w7, v3+w7, u3+w2 or v3+w2
# A and B together cover every circuit with at most 25 gates (Lemma A: at most 8 blocks; 9 extras: at least 7).
cd "$(dirname "$0")"
ulimit -v 8000000
gcc -O2 -o exh_part exh_part.c || exit 1
MAXNODES="${2:-0}"
ROWS=$(python3 partitions.py m2 8 --dump parts_m2_8.txt | grep '^rows:' | cut -d: -f2)
python3 - <<'EOF'
# 7-block file: only the partitions with exactly 7 blocks
import geom, partitions
vp = [bl for c, bl in partitions.valid_partitions(geom.m2_T(), 7) if c == 7]
with open("parts_m2_7only.txt", "w", newline="\n") as f:
    f.write(f"{len(vp)} 16\n")
    for bl in vp:
        f.write(" ".join(map(str, bl)) + "\n")
EOF
export EXH_PROGRESS=1
case "$1" in
  A) /usr/bin/time -f "cpu %U s" ./exh_part 8 9 parts_m2_8.txt "$MAXNODES" $ROWS ;;
  B) EXH_NODEP=1 EXH_HELPERS=0 /usr/bin/time -f "cpu %U s" ./exh_part 8 9 parts_m2_7only.txt "$MAXNODES" $ROWS ;;
  R) EXH_NODEP=1 EXH_HELPERS=32904,34944,1036,3076 /usr/bin/time -f "cpu %U s" ./exh_part 8 9 parts_m2_8.txt "$MAXNODES" $ROWS ;;
esac
