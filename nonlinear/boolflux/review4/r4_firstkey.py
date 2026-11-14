"""review4: the kernel's Metropolis/uphill/neutral logic when the first objective key is not cost.

The kernel's step size d = obj(new) - obj(cur) is in weighted units (first key weight 1, second
1e-4, ...), T0 = 0.6, uphill = 1.0 (a COST budget: new gates may cost mffc_cost + 1),
max_excess = 8 (weighted units).  For objective `a,cost` or `gd,cost` a cost-only uphill step has
d = 1e-4 * dcost, accepted with probability exp(-1e-4/0.6) ~ 0.9998; the current state's cost is
bounded only by mbest.obj + 8, i.e. 8e4 cost units.  Meanwhile the cost budget limits A- or
GD-reducing rewrites to new gates of cost <= mffc_cost + 1.

For each target/objective/setting, seeds 1-4, the same start and iteration count:
  final best (first key, cost), and from the per-accepted-move trace the drift of the current
  state's cost above the best's cost (median and max over accepted moves).

usage: r4_firstkey.py TARGET MODEL OBJECTIVE ITERS [name=k=v,k=v ...]
"""
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r4lib as L                                   # noqa: E402
from r4lib import core, objective                   # noqa: E402
from boolflux import cli, targets                   # noqa: E402


def main():
    tgt, mname, spec, iters = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    settings = [('default', {})]
    for a in sys.argv[5:]:
        nm, kv = a.split('=', 1)
        settings.append((nm, dict(x.split('=', 1) for x in kv.split(','))))
    model = core.Model.load(mname)
    start = cli.make_start(tgt, 'anf', model)
    key = objective.KEYS[objective.parse(spec)[0]]
    print('target %s model %s objective %s iters %d; start %s' % (tgt, mname, spec, iters,
          {k: start.metrics(model)[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}))
    for nm, extra in settings:
        rows = []
        for seed in (1, 2, 3, 4):
            wd = L.TMP / 'firstkey' / ('%s-%s-%s-%s-s%d' % (tgt, mname, spec.replace(',', '_'), nm, seed))
            ex = dict(extra); ex['trace'] = str(wd / 'trace.txt')
            log, out = L.kernel(start, model, wd, spec, {}, extra=ex, iters=iters, seed=seed, seconds=600)
            fm = out.metrics(model)
            # trace rows: t it mv cost G A GD AD of the CURRENT state after each accepted move
            best_cost = None; drift = []
            bests = [(int(b['it']), float(b['cost'])) for b in
                     ({t.split()[i]: t.split()[i + 1] for i in range(1, len(t.split()) - 1, 2)}
                      for t in log.splitlines() if t.startswith('best '))]
            bi = 0; bc = float(L.line(log, 'start')['cost'])
            for ln in (wd / 'trace.txt').read_text().split('\n'):
                t = ln.split()
                if not t: continue
                it = int(t[1])
                while bi < len(bests) and bests[bi][0] <= it:
                    bc = bests[bi][1]; bi += 1
                drift.append(float(t[3]) - bc)
            fin = L.line(log, 'final')
            rows.append((fm[key], fm['cost'], st.median(drift) if drift else 0, max(drift) if drift else 0))
        print('  %-10s %s' % (nm, extra))
        print('     final (%s, cost) per seed: %s' % (key, ' '.join('(%g, %g)' % r[:2] for r in rows)))
        print('     current-state cost above best cost: median per seed %s; max per seed %s'
              % (' '.join('%g' % r[2] for r in rows), ' '.join('%g' % r[3] for r in rows)))


if __name__ == '__main__':
    main()
