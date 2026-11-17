#!/bin/bash
# after phase B round 3: A43 AD5 builds from A35 AD3 sources, then B2.list GD-capped polishes
export BOOLFLUX_CACHE=<campaign archive>/2026-11-17-ideas/02/cache
cd ~/xcr-idea-02
S=circuits/aes-sbox
taskset -c 2 python3 search/nonlinear/boolflux/ops/selbuild.py --in $S/aes-sbox-a35-ad3-g137-gd28-xx102-47.circ.txt --top 2 --runs 4 --top-mode wrap --bottom-mode wrap --out <campaign archive>/2026-11-17-ideas/02/C/a35-g137-wrap-wrap > <campaign archive>/2026-11-17-ideas/02/C/a35-g137.log 2>&1 &
taskset -c 3 python3 search/nonlinear/boolflux/ops/selbuild.py --in $S/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt --top 2 --runs 4 --top-mode xdelta --bottom-mode leafg --out <campaign archive>/2026-11-17-ideas/02/C/a35-g141-xdelta-leafg > <campaign archive>/2026-11-17-ideas/02/C/a35-g141.log 2>&1 &
wait
<campaign archive>/2026-11-17-ideas/02/scripts/phaseB.sh <campaign archive>/2026-11-17-ideas/02/B2.list
