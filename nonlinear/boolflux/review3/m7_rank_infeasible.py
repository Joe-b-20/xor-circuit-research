"""review3 M7: bench.py v3 ranks synthesis variants by (feasible?, objective) (bench.py:141-145).
Among infeasible circuits the amount of cap violation is ignored, so during depth repair a rebuilt
circuit that is cheaper but much deeper replaces the repair progress ("keep repair progress",
bench.py:179, then continues from it).  The kernel itself ranks infeasible states by a violation
penalty (bfx.c:156-157).  Example: PRESENT (bgc), cap GD <= 5, ANF start (GD 6, one level over).

    python3 nonlinear/boolflux/review3/m7_rank_infeasible.py      (from ~/xcr-boolflux)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1])); sys.path.insert(0, str(HERE.parent))
from boolflux import core, skeleton, starts, targets  # noqa: E402
import cli  # noqa: E402

run = {'objective': 'cost', 'caps': {'GD': 5}}
model = core.Model.load('bgc'); n, m, table, _ = targets.load('present')
cand = starts.anf(n, m, table, model.ops())
# verbatim from bench.run_boolflux
feas = lambda x: all(c is None or x[k] <= c for k, c in (run.get('caps') or {}).items())
obj_w = cli.objective_weights(run.get('objective', 'cost'))
obj = lambda x: obj_w['w.cost'] * x['cost'] + obj_w['w.g'] * x['G'] + obj_w['w.a'] * x['A'] + obj_w['w.gd'] * x['GD'] + obj_w['w.ad'] * x['AD']
rank = lambda c: (0 if feas(c.metrics(model)) else 1, obj(c.metrics(model)))
sk2 = skeleton.extract(cand)
vs = [skeleton.synthesize(sk2, model.ops(), parent=cand)]
vs += [skeleton.synthesize(sk2, model.ops(), use_paar=a, paar_outputs=b) for a, b in ((0, 0), (1, 0), (1, 1))]
show = lambda c: '%s rank %s' % ({k: c.metrics(model)[k] for k in ('cost', 'GD')}, rank(c))
print('input      ', show(cand))
for v in vs: print('variant    ', show(v))
best_v = min(vs, key=rank); synth_gain = rank(best_v) < rank(cand)
print('chosen     ', show(best_v if synth_gain else cand), ' synth_gain', synth_gain)
print('GD excess: input %d -> chosen %d' % (cand.metrics(model)['GD'] - 5, (best_v if synth_gain else cand).metrics(model)['GD'] - 5))
