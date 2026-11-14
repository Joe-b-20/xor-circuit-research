#!/bin/bash
# review4 m1: Metropolis / max_excess when the first objective key is A or GD (weights 1, 1e-4):
# drift of the current state's cost above the best's cost, a,cost vs cost,a and gd,cost vs cost,gd,
# plus uphill=4/8 and w.cost=1 variants.  ~2 min on 2 CPUs; run with xsrun:
#   ~/xs-campaigns/guard/xsrun main 18,19 r4-drift $PWD/nonlinear/boolflux/review4/tmp/firstkey.out -- bash $PWD/nonlinear/boolflux/review4/r4_drift.sh
cd ~/xcr-boolflux
P=nonlinear/boolflux/review4/r4_firstkey.py
python3 $P gf16-mul xag a,cost 30000 up4=uphill=4 up8=uphill=8 wcost=w.cost=1
python3 $P gf16-mul xag cost,a 30000
python3 $P present bgc gd,cost 30000 up4=uphill=4 wcost=w.cost=1
python3 $P present bgc cost,gd 30000
echo DONE
