#!/bin/bash
# review3 M4: cli.py run_skel (line 331) picks the synthesis variant by cost alone and always
# replaces the job's input with it, ignoring caps and the objective (bench.py v3 ranks by
# (feasible, objective) and keeps the input when it is better).  With --cap-gd 4 on GF(2^4) mult,
# the seeded rebuild (34 gates, GD 4, feasible) is available but the Paar variant (31, GD 6) is taken.
set -e
cd ~/xcr-boolflux
R=nonlinear/boolflux/review3/tmp/m4
rm -rf $R; mkdir -p $R
echo "== synthesis variants of the unchanged skeleton (what run_skel chooses from)"
python3 - <<'EOF'
import sys; sys.path.insert(0, 'nonlinear')
from boolflux import core, starts, targets, skeleton
m = core.Model.load('xag'); n, mm, tab, _ = targets.load('gf16-mul'); c = starts.anf(n, mm, tab, m.ops())
sk = skeleton.extract(c)
vs = [('seeded', skeleton.synthesize(sk, m.ops(), parent=c))] + [('forms paar=%d out=%d' % (a, b),
      skeleton.synthesize(sk, m.ops(), use_paar=a, paar_outputs=b)) for a, b in ((0, 0), (1, 0), (1, 1))]
for nm, v in vs:
    mt = v.metrics(m); print('   %-20s cost %g A %d GD %d %s' % (nm, mt['cost'], mt['A'], mt['GD'], 'feasible' if mt['GD'] <= 4 else 'violates GD<=4'))
pick = min((v for _, v in vs), key=lambda v: v.metrics(m)['cost'])     # cli.py:331
print('   cli.py:331 picks: cost %g GD %d' % (pick.metrics(m)['cost'], pick.metrics(m)['GD']))
EOF
echo "== pipe --cap-gd 4 --skel-iters 0 --skel-share 1 (every job rebuilds)"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py pipe --target gf16-mul --model xag --objective cost --cap-gd 4 \
   --iters 300 --skel-iters 0 --skel-share 1 --seeds 1-2 --jobs 2 --rounds 1 --out $R/pipe 2>&1 | tail -2
python3 -c "
import json; s = json.load(open('$R/pipe/summary.json'))
for r in s['runs']:
    print('   job %s: from GD %d -> synth cost %g GD %d -> gate result cost %g GD %d feasible %s' % (r['tag'], r['from']['GD'],
          r['synth']['cost'], r['synth']['GD'], r['metrics']['cost'], r['metrics']['GD'], r['feasible']))
print('   reported best from job', s['best']['job'], {k: s['best']['metrics'][k] for k in ('cost', 'GD')})"
