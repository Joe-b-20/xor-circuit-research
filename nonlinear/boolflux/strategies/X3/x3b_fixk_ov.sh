#!/bin/bash
# X3b: OV (aff(x) + all functions of N, 2^24 operands l) 12+1 test, one block of 2^20 (2^21 blocks took
# 106-116 s, too close to the 2-minute cap); $1 = FILE, $2 = DROP, $3 = block 0..15 (units of 2^20)
D=~/xcr-boolflux/nonlinear/boolflux/strategies/X3
A=$(( $3 * 1048576 )); B=$(( A + 1048576 ))
bash $D/x3b_fixk.sh $1 $2 OV $A:$B | grep -o '"drop[^]]*\]\|"chunk[^]]*\]\|"reached": [0-9]*\|"secs": [0-9.]*\|CANDIDATE' | tr '\n' ' '; echo
