#!/bin/bash
# multibatch.sh LISTFILE : each line "SPEC TAG K"; runs genbatch over all 16 gamma
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
while read spec tag K; do
  [ -z "$spec" ] && continue
  ./genbatch.sh $spec $tag $K 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
done < $1
