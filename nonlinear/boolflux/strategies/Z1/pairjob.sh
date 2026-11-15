#!/bin/bash
# pairjob.sh INPUT LO HI OUT
#   One Gray-index range of H3's r1enum_v5 over a pairgen.py input (pair -> 1 AND, full operand
#   space).  Hits ("H a ...") would be 27-AND candidates; post-process with H3's pair_post.py logic.
H3=~/xcr-boolflux/nonlinear/boolflux/strategies/H3
IN=$1; LO=$2; HI=$3; OUT=$4
echo "$(date -u +%FT%T) start $IN $LO $HI" > $OUT
$H3/r1enum_v5 $LO $HI 100000 < $IN >> $OUT
echo "$(date -u +%FT%T) end rc=$?" >> $OUT
