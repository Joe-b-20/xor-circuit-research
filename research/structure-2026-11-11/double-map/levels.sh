#!/bin/bash
# usage: bash levels.sh     static invariants (delta, delta(T^T), delta_i) of M2 and of the m = 4 classes with eps > delta
cd "$(dirname "$0")"
for t in m2 '1|023|1|1' '123|023|013|012' '12|23|013|012' '1|2|03|12' '1|2|013|12' '1|023|03|012' '12|03|013|012' '12|03|13|02' '12|23|013|02'; do
  python3 geom.py "$t" | grep -E '^T =|rho_4|delta_i'
done
