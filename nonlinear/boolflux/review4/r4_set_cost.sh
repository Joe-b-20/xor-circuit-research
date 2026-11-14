#!/bin/bash
# review4: `--set cost.*` (and other objective keys) reach the kernel but not the Python ranking.
# (a) --set cost.6=4 with model bgc: the kernel minimises XOR-heavy cost, cli ranks/reports bgc cost;
#     `run` compares only job results (never the start), so a circuit worse than the start under the
#     reported cost is saved as best.
# (b) --set cost.14=1 with model xag: OR is added to the kernel library; the jobs' Python cost is NaN,
#     the NaN rank tuples are sorted, and the run fails only at the end (library check).
set -u
cd ~/xcr-boolflux
R=nonlinear/boolflux/review4/tmp/set_cost
rm -rf $R; mkdir -p $R
S=nonlinear/boolflux/results/present/present-bgc-cost-nocap-g14-a4-gd12-ad4.circ.txt
echo "== (a) start: $S"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py verify $S --target present --model bgc | cut -c1-200
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run --target present --model bgc --start $S --objective cost \
    --iters 4000 --seeds 1-2 --jobs 2 --set cost.6=4 --out $R/a 2>&1 | tail -3
echo "-- kernel's own final lines (cost under the --set costs):"
grep -h '^final' $R/a/r0-s1.log $R/a/r0-s2.log | cut -c1-80
python3 - $R/a <<'EOF'
import json, sys
d = json.load(open(sys.argv[1] + '/summary.json'))
print('-- summary.json best metrics (cost under model bgc):', {k: d['best']['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')},
      'start_metrics cost', d['start_metrics']['cost'], 'settings cost.6 =', d['settings'].get('cost.6'))
EOF
echo
echo "== (b) model xag + --set cost.14=1 (OR is not in xag)"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run --target present --model xag --objective cost \
    --iters 4000 --seeds 1-2 --jobs 2 --set cost.14=1 --out $R/b 2>&1 | tail -3 | cut -c1-300
python3 - $R/b <<'EOF'
import json, sys
d = json.load(open(sys.argv[1] + '/summary.json'))
print('-- per-job Python cost:', [r['metrics']['cost'] for r in d['runs'] if 'metrics' in r],
      ' counts:', [r['metrics']['counts'] for r in d['runs'] if 'metrics' in r][:1])
EOF
