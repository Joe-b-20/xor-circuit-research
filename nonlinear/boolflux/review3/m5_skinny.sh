#!/bin/bash
# review3 M5 on a repository target: map:skinny has 4 weight-1 rows (outputs that are inputs).
# The correct 12-XOR circuit is written with 4 BUF lines and cli run reports VERIFICATION FAILED.
cd ~/xcr-boolflux
R=nonlinear/boolflux/review3/tmp/m5-skinny; rm -rf $R
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run --target map:skinny --model xor --set linear=1 \
    --iters 200 --seeds 1 --jobs 1 --out $R 2>&1 | tail -2
echo "BUF lines: $(grep -c "^BUF" $R/best.circ.txt)"
python3 -c "
import json; b = json.load(open(\"$R/summary.json\"))[\"best\"]
print(\"core_ok\", b[\"core_ok\"], \"independent_ok\", b[\"independent_ok\"], \"core counts\", b[\"metrics\"][\"counts\"], \"independent counts\", b[\"independent_metrics\"][\"counts\"])"
