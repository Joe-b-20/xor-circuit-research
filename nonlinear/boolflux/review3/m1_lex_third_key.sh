#!/bin/bash
# review3 M1: cli.py `run` ranks jobs by the kernel's printed `final ... obj %.6f`; with three
# objective keys (weights 1, 1e-4, 1e-8) the third key is below the printed precision, so jobs that
# differ only in the third key tie and the tie is broken by seed number.
set -e
cd ~/xcr-boolflux
R=nonlinear/boolflux/review3/tmp/m1
rm -rf $R; mkdir -p $R
echo "== step 1: real cli run, objective a,gd,cost (third key = cost)"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run --target present --model bgc --objective a,gd,cost \
    --iters 3000 --seeds 1-8 --jobs 2 --out $R/run > /dev/null
grep -h '^final' $R/run/r0-s1.log $R/run/r0-s6.log
echo "   (seed 1: cost 17, seed 6: cost 18, same A and GD -> identical printed obj)"
echo "== step 2: cli's own ranking code on the two circuits with the seed labels swapped"
taskset -c 18,19 python3 - "$R" <<'EOF'
import sys, subprocess, argparse
from pathlib import Path
R = Path(sys.argv[1]); sys.path.insert(0, 'nonlinear')
from boolflux import cli, core
model = core.Model.load('bgc')
args = argparse.Namespace(objective='a,gd,cost', cap_gd=None, cap_ad=None, cap_a=None, seconds=10, iters=0)
results = []
# worse circuit (cost 18) gets the smaller seed number
for seed, src in ((1, R / 'run/r0-s6.best.bfx'), (2, R / 'run/r0-s1.best.bfx')):
    cp = R / ('s%d.cfg' % seed); bp = R / ('s%d.out.bfx' % seed)
    cli.kernel_config(cp, str(src), str(bp), model, args, seed, {})
    log = subprocess.run([str(R / 'run/bin/bfx'), str(cp)], capture_output=True, text=True).stdout
    final, _, _ = cli.parse_kernel_log(log)
    c = core.from_kernel(bp.read_text())
    results.append({'final': final, 'seed': seed, 'metrics': c.metrics(model)})
key = lambda r: (r['final'].get('obj', 1e18), r['seed'])      # cli.py:256, verbatim
results.sort(key=key)
for r in results:
    m = r['metrics']; print('   seed %d obj %r  A %d GD %d cost %g' % (r['seed'], r['final']['obj'], m['A'], m['GD'], m['cost']))
b = results[0]['metrics']
print('   cli picks seed %d: cost %g (the lexicographic best has cost 17)' % (results[0]['seed'], b['cost']))
EOF
