#!/bin/bash
# X3b daytime sweep: pair windows (k <= 2) of all 9+5+14 files, O2, stage 1 free; $1 = shard of 20
python3 ~/xcr-boolflux/nonlinear/boolflux/strategies/X3/x3b_night.py $1 20 --kmax 2 --tag day-pairs \
  | grep "^#\|drop\|->\|COVER\|BUILT\|TIMEOUT" | cut -c1-220
