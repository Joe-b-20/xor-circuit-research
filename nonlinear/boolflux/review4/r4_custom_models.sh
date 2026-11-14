#!/bin/bash
# review4: custom cost models end to end through `cli.py run` (kernel -> core -> verify.py).
# (a) fractional / zero / large costs: kernel, core and verify.py costs must agree (expected: ok).
# (b) not_as XNOR0 with cost[NOT] != cost[XNOR] (NOT 0.5, XNOR 5): core costs a NOT at cost[NOT], the written file has
#     `XNOR t a 0`, verify.py costs it at cost[XNOR] -> metrics disagree -> VERIFICATION FAILED.
set -u
cd ~/xcr-boolflux
R=nonlinear/boolflux/review4/tmp/custom
rm -rf $R; mkdir -p $R
printf '{"name": "r4frac", "gates": {"AND": 1.37, "OR": 2.5, "XOR": 0.333, "XNOR": 0.71, "NAND": 1000, "NOR": 3.25, "ANDN": 0.05, "ORN": 7.5, "NOT": 0}}\n' > $R/frac.json
printf '{"name": "r4x0", "gates": {"AND": 1, "XOR": 1, "XNOR": 5, "NOT": 0.5}, "not_as": "XNOR0"}\n' > $R/x0.json
echo "== (a) fractional/zero/large costs, present, objective cost,gd"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run --target present --model $R/frac.json --objective cost,gd \
    --iters 4000 --seeds 1-2 --jobs 2 --out $R/a 2>&1 | tail -1 | cut -c1-250
grep -h '^final' $R/a/r0-s*.log | cut -c1-60
python3 -c "
import json; d=json.load(open('$R/a/summary.json')); b=d['best']
print('core cost', b['metrics']['cost'], 'verify.py cost', b['independent_metrics']['cost'], 'independent_ok', b['independent_ok'])"
echo
echo "== (b) not_as XNOR0 with NOT 0.5, XNOR 5"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run --target present --model $R/x0.json --objective cost \
    --iters 4000 --seeds 1-2 --jobs 2 --out $R/b 2>&1 | tail -2 | cut -c1-250
python3 -c "
import json; d=json.load(open('$R/b/summary.json')); b=d['best']
print('core cost', b['metrics']['cost'], 'counts', b['metrics']['counts'], '| verify.py cost', b['independent_metrics']['cost'], 'counts', b['independent_metrics']['counts'])"
