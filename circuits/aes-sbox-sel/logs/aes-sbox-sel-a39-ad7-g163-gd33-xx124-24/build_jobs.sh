#!/bin/bash
# G4 stage 1: write the selbuild job list (one line per build: SRC|TOP|BOTTOM|TOPN|RUNS|SEED|TAG)
G=$HOME/xs-campaigns/2026-11-17-push/G4
S=$G/snap/circuits/aes-sbox
I=$G/snap/circuits/aes-invsbox
ID=$HOME/xs-campaigns/2026-11-17-ideas
out=$G/scripts/build.list
: > $out
add() {  # add SRC "modes..." TOPN RUNS SEED
  local src=$1 modes=$2 tn=$3 rn=$4 sd=$5
  for m in $modes; do
    t=${m%/*}; b=${m#*/}
    echo "$src|$t|$b|$tn|$rn|$sd|$(basename $src .circ.txt)-$t-$b-s$sd" >> $out
  done
}
GATE="wrap/wrap bp/wrap"
DEPTH="xdelta/leafg flat/leafg xdelta/flat wrap/leafg"
# A36/6 fewest gates (forward + inverse A28 AD4, published and tonight's)
for f in $S/aes-sbox-a28-ad4-g13{0,1,2,3}-*.circ.txt; do add $f "$GATE" 4 8 2; done
for f in $I/aes-invsbox-a28-ad4-g13{2,3}-*.circ.txt $ID/08/found/aes-invsbox-a28-ad4-*/*.circ.txt; do add $f "$GATE" 3 6 2; done
# A36/6 low GD
for f in $S/aes-sbox-a28-ad4-g135-gd18*.circ.txt $S/aes-sbox-a28-ad4-g138-gd17*.circ.txt $S/aes-sbox-a28-ad4-g174-gd14*.circ.txt; do add $f "$DEPTH" 3 4 2; done
for f in $I/aes-invsbox-a28-ad4-g154-gd15*.circ.txt $I/aes-invsbox-a28-ad4-g143-gd16*.circ.txt $ID/10/found/*/aes-invsbox-a28-ad4-g153-gd15-*.circ.txt; do add $f "xdelta/leafg wrap/leafg xdelta/wrap" 3 4 2; done
# A37/A38 (A29, A30 AD4)
for f in $S/aes-sbox-a29-ad4-g141-gd15*.circ.txt $S/aes-sbox-a29-ad4-g135-gd16*.circ.txt $S/aes-sbox-a30-ad4-g138-gd15*.circ.txt; do add $f "xdelta/leafg" 3 4 2; done
for f in $ID/04/found/aes-sbox-a29-ad4-g127-gd23-acab*/*.circ.txt $ID/04/found/aes-sbox-a29-ad4-g128-*/*.circ.txt; do add $f "wrap/wrap" 3 6 2; done
# A40/A41 (A32, A33 AD4) forward: gates and depth
for f in $S/aes-sbox-a32-ad4-*.circ.txt $S/aes-sbox-a33-ad4-*.circ.txt; do add $f "wrap/wrap bp/wrap xdelta/leafg" 3 6 2; done
for f in $I/aes-invsbox-a32-ad4-*.circ.txt $I/aes-invsbox-a33-ad4-*.circ.txt; do add $f "wrap/wrap xdelta/leafg" 3 6 2; done
# A42 (A34 AD4)
for f in $S/aes-sbox-a34-ad4-*.circ.txt $I/aes-invsbox-a34-ad4-*.circ.txt; do add $f "xdelta/leafg wrap/leafg" 3 4 2; done
# A43/5 (A35 AD3)
for f in $S/aes-sbox-a35-ad3-g1{39,43,47,55,62,65,81}-*.circ.txt; do add $f "xdelta/leafg wrap/leafg" 3 4 2; done
for f in $ID/04/found/aes-sbox-a35-ad3-*/*.circ.txt $ID/08/found/aes-invsbox-a35-ad3-*/*.circ.txt $I/aes-invsbox-a35-ad3-g144-*.circ.txt; do add $f "wrap/wrap" 3 6 2; done
# A39/7, A40/7 (A31, A32 AD5)
for f in $S/aes-sbox-a31-ad5-g11{4,5,6,7}-*.circ.txt $S/aes-sbox-a32-ad5-g10{5,6,8}-*.circ.txt; do add $f "wrap/wrap xdelta/leafg" 3 4 2; done
wc -l $out
