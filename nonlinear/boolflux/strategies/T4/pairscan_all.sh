#!/bin/bash
# T4: pairscan over all GD<=11 AD4 archive circuits (list file), summary per circuit
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/T4
while read f; do
  echo "== $f $(python3 -c "
import sys; sys.path.insert(0,'../../..')
from boolflux import core
c=core.from_kernel(open('$f').read()); m=c.metrics(); print(m['A'],m['AD'],m['G'],m['GD'])")"
  timeout 120 python3 pairscan.py "$f" 2>&1 | grep -v '^affine' | tail -12
done < ~/xs-campaigns/2026-11-15-study/T4/gd11list.txt
