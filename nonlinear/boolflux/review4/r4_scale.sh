#!/bin/bash
# review4 M1: the kernel's T0 / uphill / max_excess are absolute numbers in cost units.
# Same PRESENT ANF start, objective cost,gd, 30000 iterations, seeds 1-4:
#   bgc (all gates 1), bgc x10 (all gates 10: the same ranking of every circuit), bgc x0.1,
#   and bgc x10 with T0, uphill, max_excess also x10.
# ~2 min on 2 CPUs; run with xsrun:
#   ~/xs-campaigns/guard/xsrun main 18,19 r4-scale $PWD/nonlinear/boolflux/review4/tmp/scale.out -- bash $PWD/nonlinear/boolflux/review4/r4_scale.sh
cd ~/xcr-boolflux
P=nonlinear/boolflux/review4/r4_firstkey.py
T=nonlinear/boolflux/review4/tmp; mkdir -p $T
echo '{"name": "bgc10", "gates": {"AND": 10, "OR": 10, "XOR": 10, "NOT": 10}}' > $T/bgc10.json
echo '{"name": "bgc01", "gates": {"AND": 0.1, "OR": 0.1, "XOR": 0.1, "NOT": 0.1}}' > $T/bgc01.json
for m in bgc $T/bgc10.json $T/bgc01.json; do python3 $P present $m cost,gd 30000; done
python3 $P present $T/bgc10.json cost,gd 30000 scaled=T0=6,uphill=10,max_excess=80
echo DONE
