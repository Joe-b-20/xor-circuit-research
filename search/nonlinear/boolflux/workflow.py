"""Time-sliced search workflows, shared by `cli.py flow` and the benchmark driver (bench/bench.py).

A run is a dict:
  target, model, objective ('cost,gd', ...), caps {GD, AD, A}, start ('anf' | NCFF path |
  XORFlux JSON path | a core.Circuit), seconds (wall budget, rebuild included), seed,
  seed_scheme (default 'v2'; 'legacy-flow' = the kernel seeds of runs before 2026-11-14),
  config  'gate'    one gate-kernel run for the whole budget
          'full'    rounds of round_s seconds: skeleton stage (skel_set; iters 0 = rebuild only)
                    -> rebuild variants -> gate stage, alternating, incumbent kept
  adaptive  (full) the skeleton slice halves after every round whose rebuilt circuit was not
            better than its input (feasibility first), min 0.5 s; the gate stage gets the rest
  seeded / unseeded  which rebuild variants to build (seeded with the parent circuit; from forms
            with greedy / Paar per level / Paar also for the outputs)
  set, skel_set  kernel settings (ablations); linear (XOR-only models: exact n+1-pattern mode,
            default on)

Ranking everywhere is objective.rank: feasible first, then total cap excess, then the keys in
order.  The incumbent is the best-ranked circuit seen (start, every rebuilt candidate, every
kernel result), so repair progress under caps is kept between rounds, and a rebuilt candidate is
compared with the incumbent as soon as it is built.  The trajectory has a row for every new
feasible incumbent, wherever it came from (kernel improvement, the kernel's cleaned start, or a
rebuild), timed in wall seconds since the search started.
"""
import json
import time
from pathlib import Path

from boolflux import core, objective, runlog, skeleton, starts, targets

# ---- kernel seeds ------------------------------------------------------------------------------
# Review 5: cli.py run/pipe used seed + 1000 x round, so (seed 1, round 1) and (seed 1001, round 0)
# ran with the same kernel seed; flow and the benchmark (this module) used seed x 1000 + round,
# so (seed 1, round 1000) = (seed 2, round 0).  Both now use kernel_seed(seed, round, 'v2'):
# seed + round x 2^32, one-to-one for 0 <= seed, round < 2^32 (the kernel seed is a u64), and equal
# to the seed in round 0, so single-round `cli.py run` commands give the kernel seeds they gave
# before.  The old formulas stay reachable (`--seed-scheme legacy`, run['seed_scheme']), so a
# command recorded before 2026-11-14 is replayed with the seeds it used; every summary.json records
# the kernel seed of each job and, from 2026-11-14 on, the scheme.
SEED_SCHEMES = {
    'v2': 'seed + round x 2^32 (from 2026-11-14; cli.py run/pipe/flow and the benchmark)',
    'legacy-run': 'seed + 1000 x round (cli.py run and pipe before 2026-11-14)',
    'legacy-flow': 'seed x 1000 + round (cli.py flow and bench/bench.py before 2026-11-14)',
}
SEED_SPAN = 1 << 32


def kernel_seed(seed, rnd, scheme='v2'):
    """Kernel seed of job `seed` in round `rnd` (see SEED_SCHEMES)."""
    seed = int(seed); rnd = int(rnd)
    if scheme == 'v2':
        if not (0 <= seed < SEED_SPAN and 0 <= rnd < SEED_SPAN):
            raise ValueError('seed %d / round %d outside 0..2^32-1 (seed scheme v2)' % (seed, rnd))
        return seed + rnd * SEED_SPAN
    if scheme == 'legacy-run':
        return seed + 1000 * rnd
    if scheme == 'legacy-flow':
        return seed * 1000 + rnd
    raise ValueError('unknown seed scheme %r (%s)' % (scheme, ', '.join(SEED_SCHEMES)))

DEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
            'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
            'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
SKEL_DEFAULTS = {'w.a': 1, 'w.lin': 0.02, 'T0': 0.3, 'Tperiod_it': 4000, 'mv.swap': 4, 'mv.merge': 3,
                 'mv.split': 1, 'mv.perturb': 1, 'pairs': 60000, 'fext': 400}


def timed(cmd, cpu=None):
    """Run (pinned to `cpu` if given); (stdout, stderr, peak RSS kB, wall s, rc).  GNU time -v when it
    is on PATH, else Python's own measurement (runlog.measured); taskset, else os.sched_setaffinity."""
    return runlog.measured(cmd, cpu)


def load_start(run, model):
    n, m, table, _ = targets.load(run['target'])
    st = run['start']
    if isinstance(st, core.Circuit):
        return st
    if st == 'anf':
        return starts.anf(n, m, table, model.ops())
    if str(st).endswith('.json'):                    # XORFlux seed circuit
        d = json.loads(Path(st).read_text())
        return core.Circuit(d['inputCount'], len(d['outputSignals']), [(6, a, b) for a, b in d['gates']],
                            list(d['outputSignals'])).live()
    return core.read_ncff(st)


# settings that would make the kernel rank or count differently from the Python side
# (costs, depth weights, caps, objective order, weights) must come from --model / --cap-* /
# --objective, never from --set.
FORBIDDEN_SET = ('cost.', 'gdw.', 'cap.', 'w.', 'lex', 'in', 'out', 'seed', 'iters', 'seconds')


def check_sets(extra):
    bad = sorted(k for k in extra if k.startswith(FORBIDDEN_SET[:4]) or k in FORBIDDEN_SET[4:])
    if bad:
        raise SystemExit('--set %s not allowed: costs come from --model, caps from --cap-*, the objective '
                         'from --objective, run controls from their own options' % ', '.join(bad))
    return extra


def is_linear(model):
    return all(op not in core.NONLINEAR_OPS for op in model.ops())


def kernel_cfg(path, start_path, out_path, model, run, seconds, seed, extra, iters=None):
    cfg = dict(DEFAULTS); cfg.update(objective.weights(run.get('objective', 'cost')))
    for op, c in model.cost.items(): cfg['cost.%d' % op] = c
    caps = run.get('caps') or {}
    for k, key in (('GD', 'cap.gd'), ('AD', 'cap.ad'), ('A', 'cap.a')):
        if caps.get(k) is not None: cfg[key] = caps[k]
    if is_linear(model): cfg['linear'] = run.get('linear', 1)
    cfg.update(check_sets(dict(extra)))
    cfg.update({'in': start_path, 'out': out_path, 'seed': seed, 'seconds': seconds,
                'iters': iters if iters is not None else 10 ** 15})
    Path(path).write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    return cfg


def parse_kernel(log, t_offset):
    """(best rows [[t, cost, G, A, GD, AD]], cleaned start metrics or None, final dict)."""
    rows, start, final = [], None, {}
    for ln in log.splitlines():
        t = ln.split()
        if not t: continue
        if t[0] in ('best', 'start', 'final'):
            d = {t[i]: t[i + 1] for i in range(1, len(t) - 1, 2)}
            mt = {'cost': float(d['cost']), 'G': int(d['G']), 'A': int(d['A']), 'GD': int(d['GD']), 'AD': int(d['AD'])}
            if t[0] == 'best':
                rows.append([round(float(d['t']) + t_offset, 3), mt['cost'], mt['G'], mt['A'], mt['GD'], mt['AD']])
            elif t[0] == 'start':
                start = mt
            else:
                final = {k: float(v) for k, v in d.items()}
    return rows, start, final


def metrics5(c, model, caps=None):
    m = objective.measure(c, model, caps)
    return {k: m[k] for k in ('cost', 'G', 'A', 'GD', 'AD', 'VSUM') if k in m}


def search(run, bindir, wd, cpu=None, log=None):
    """Run one workflow; returns a dict with the incumbent circuit (best-ranked, possibly
    infeasible if nothing met the caps), its metrics, trajectory, RSS list, overhead, timing.
    log: a runlog.RunLog; every trajectory point is an 'improvement' event (source: start, rebuild,
    kernel-start, kernel) and every kernel process a 'kernel' event (round, stage, kernel seed,
    seconds, wall, RSS, exit code), each with the job's seed."""
    ev = (lambda kind, **kw: log.event(kind, seed=run['seed'], **kw)) if log is not None else (lambda kind, **kw: None)
    bindir, wd = Path(bindir), Path(wd); wd.mkdir(parents=True, exist_ok=True)
    model = core.Model.load(run['model'])
    n, m, table, _ = targets.load(run['target'])
    caps = run.get('caps') or {}; spec = run.get('objective', 'cost')
    R = lambda mt: objective.rank(mt, caps, spec)
    feas = lambda mt: objective.feasible(mt, caps)
    t0 = time.time(); start = load_start(run, model); t_start = time.time() - t0
    sm = metrics5(start, model, caps)
    traj = [[0.0, sm['cost'], sm['G'], sm['A'], sm['GD'], sm['AD']]]
    traj_best = sm if feas(sm) else None             # last feasible trajectory point

    def offer_traj(mt, t, src):
        nonlocal traj_best
        if feas(mt) and (traj_best is None or R(mt) < R(traj_best)):
            traj_best = dict(mt); traj.append([round(t, 3), mt['cost'], mt['G'], mt['A'], mt['GD'], mt['AD']])
            ev('improvement', t_search=round(t, 3), metrics={k: mt[k] for k in ('cost', 'G', 'A', 'GD', 'AD')},
               operator=src)

    overhead = {'start_s': round(t_start, 4), 'extract_s': 0, 'skel_s': 0, 'synth_s': 0, 'kernel_startup_s': 0}
    rss = []; budget = run['seconds']; T0 = time.time()
    if traj_best is not None:
        ev('improvement', t_search=0.0, metrics={k: sm[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}, operator='start')
    best_c, best_m = start, sm
    cur = start; rnd = 0; skel_share = 0.2; R_s = run.get('round_s', 10.0)
    rounds = []
    while True:
        el = time.time() - T0
        if el >= budget - 0.05: break
        if run['config'] == 'gate':
            stages = [('gate', budget - el)]
        else:
            share = skel_share if run.get('adaptive') else 0.2
            stages = [('skel', min(R_s * share, budget - el)), ('gate', None)]
        synth_gain = False; round_t0 = time.time(); cand = cur; rec = {'round': rnd}
        for kind, secs in stages:
            el = time.time() - T0
            if el >= budget - 0.05: break
            if kind == 'skel':
                ts = time.time(); sk = skeleton.extract(cand); overhead['extract_s'] += time.time() - ts
                outs = core.tables_from_values(n, m, table)
                (wd / 'sk.in').write_text(skeleton.write_skel(sk, outs))
                scfg = dict(SKEL_DEFAULTS)
                if caps.get('AD') is not None: scfg['cap.ad'] = caps['AD']
                scfg.update({'in': wd / 'sk.in', 'out': wd / 'sk.out', 'seed': kernel_seed(run['seed'], rnd, run.get('seed_scheme', 'v2')),
                             'iters': 10 ** 15, 'seconds': secs})
                scfg.update(run.get('skel_set', {}))     # skel_set wins (iters 0 = rebuild only)
                (wd / 'sk.cfg').write_text(''.join('%s %s\n' % kv for kv in scfg.items()))
                ts = time.time()
                so, se, r_, wall, rc = timed([str(bindir / 'skel'), str(wd / 'sk.cfg')], cpu)
                overhead['skel_s'] += time.time() - ts; rss.append(r_)
                ev('kernel', kernel='skel', round=rnd, kernel_seed=scfg['seed'], seconds=secs, wall_s=round(wall, 3),
                   rss_kb=r_, rc=rc)
                if rc != 0: raise RuntimeError('skel failed: ' + se[-500:])
                sk2 = skeleton.read_skel((wd / 'sk.out').read_text())
                ts = time.time(); vs = []
                if run.get('seeded', True): vs.append(skeleton.synthesize(sk2, model.ops(), parent=cand))
                if run.get('unseeded', True):
                    vs += [skeleton.synthesize(sk2, model.ops(), use_paar=a, paar_outputs=b) for a, b in ((0, 0), (1, 0), (1, 1))]
                if not vs: raise RuntimeError('no rebuild variant selected (seeded and unseeded both off)')
                best_v = min(vs, key=lambda c: R(metrics5(c, model, caps)))
                overhead['synth_s'] += time.time() - ts
                if best_v.value_table() != list(table):
                    raise RuntimeError('rebuilt circuit does not compute the target')
                bvm = metrics5(best_v, model, caps)
                rec['rebuilt'] = bvm
                synth_gain = R(bvm) < R(metrics5(cand, model, caps))
                if synth_gain: cand = best_v                   # keep the input unless the rebuild is better
                if R(bvm) < R(best_m):                         # incumbent, at once (end of budget too)
                    best_c, best_m = best_v, bvm
                offer_traj(bvm, time.time() - T0, 'rebuild')
            else:
                if secs is None:
                    rem = budget - (time.time() - T0)
                    secs = min(max(0.5, R_s - (time.time() - round_t0)), rem) if run.get('adaptive') else min(R_s * 0.8, rem)
                (wd / 'g.in').write_text(core.to_kernel(cand))
                ks = kernel_seed(run['seed'], rnd, run.get('seed_scheme', 'v2'))
                kernel_cfg(wd / 'g.cfg', wd / 'g.in', wd / 'g.out', model, run, secs, ks, run.get('set', {}))
                t_launch = time.time() - T0
                so, se, r_, wall, rc = timed([str(bindir / 'bfx'), str(wd / 'g.cfg')], cpu)
                rss.append(r_)
                ev('kernel', kernel='bfx', round=rnd, kernel_seed=ks, seconds=secs, wall_s=round(wall, 3), rss_kb=r_, rc=rc)
                if rc != 0: raise RuntimeError('bfx failed: ' + (so + se)[-800:])
                startup = max(0.0, wall - parse_kernel(so, 0)[2].get('seconds', wall))
                # kernel times count from its own clock, which starts after reading and the start
                # clean-up; shift them by the measured start-up so they are wall time since T0
                rows, kstart, final = parse_kernel(so, t_launch + startup)
                overhead['kernel_startup_s'] += startup
                if kstart: offer_traj(kstart, t_launch + startup, 'kernel-start')   # the kernel's cleaned start
                for row in rows:
                    offer_traj({'cost': row[1], 'G': row[2], 'A': row[3], 'GD': row[4], 'AD': row[5]}, row[0], 'kernel')
                cand = core.from_kernel((wd / 'g.out').read_text())
                cm = metrics5(cand, model, caps); rec['gate'] = cm
                if R(cm) <= R(best_m):
                    best_c, best_m = cand, cm
        if run['config'] != 'gate' and run.get('adaptive'):
            skel_share = 0.2 if synth_gain else max(0.5 / R_s, skel_share / 2)
        rec['synth_gain'] = synth_gain; rounds.append(rec)
        cur = best_c                                       # repair progress kept (rank includes excess)
        rnd += 1
        if run['config'] == 'gate': break
    return {'circuit': best_c, 'metrics': best_m, 'feasible': feas(best_m), 'trajectory': traj, 'rss': rss,
            'rss_source': runlog.timing(), 'pinning': runlog.pinning() if cpu is not None else 'none',
            'overhead': overhead, 'search_s': time.time() - T0, 'rounds': rounds}
