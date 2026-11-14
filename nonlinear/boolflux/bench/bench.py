"""Matched-budget benchmark runs for BoolFlux (and XORFlux on linear maps).

    python3 nonlinear/boolflux/bench/bench.py PLAN.json OUTDIR [--cpus 0,2,4,...]

PLAN.json: {"tasks": [task, ...]}; a task is a list of runs executed back to back on one pinned
CPU (so the runs of a comparison pair share hardware).  A run is a dict:
  tool      'boolflux' | 'xorflux'
  config    boolflux: 'gate' (gate kernel only) or 'full' (skeleton + seeded rebuild + gate,
            alternating), plus kernel settings in 'set' (ablations) and 'skel_set'; the loop is
            workflow.search (the same code as `cli.py flow`)
  target, model, objective, caps {GD, AD, A}, start ('anf' | NCFF path | XORFlux JSON path),
  seconds (wall budget for the search, rebuild included), seed, label
Each run writes OUTDIR/<label>.json: trajectory [[t, cost, G, A, GD, AD], ...] (t = wall seconds
since the search started; for XORFlux the worker's own clock), final metrics, verification of
the final circuit by both verifiers (outside the budget), peak RSS of the search process(es),
overhead (start construction, extraction, skeleton kernel, synthesis, kernel start-up), CPU.
"""
import json
import os
import re
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))
import cli                                         # noqa: E402
from boolflux import core, workflow   # noqa: E402

if os.environ.get('BFXBENCH_BIN'):                     # worker: binaries built by the parent
    BIN = Path(os.environ['BFXBENCH_BIN'])
else:
    BIN = Path(tempfile.mkdtemp(prefix='bfxbench-'))
    for b in ('bfx', 'skel'):
        subprocess.run(['gcc', '-O2', '-o', str(BIN / b), str(PKG / 'kernel' / (b + '.c')), '-lm'], check=True)


timed = workflow.timed
load_start = workflow.load_start


def to_xorflux_json(c, name, path):
    assert all(op == 6 for op, a, b in c.gates)
    path.write_text(json.dumps({'benchmark': name, 'inputCount': c.n, 'gates': [[a, b] for _, a, b in c.gates],
                                'outputSignals': c.outputs}) + '\n')


def run_boolflux(run, cpu, wd):
    """The search loop lives in workflow.py (also behind `cli.py flow`)."""
    r = workflow.search(run, BIN, wd, cpu)
    return r['circuit'], r['trajectory'], r['rss'], r['overhead'], r['search_s']


def run_xorflux(run, cpu, wd):
    model = core.Model.load('xor')
    t0 = time.time(); start = load_start(run, model); t_start = time.time() - t0
    sp = wd / 'start.json'; to_xorflux_json(start, run['target'][4:], sp)
    out = wd / 'xf'
    cmd = [sys.executable, str(REPO / 'search' / 'xorflux'), 'quick', run['target'][4:], '--seconds', str(run['seconds']),
           '--seed', str(run['seed']), '--seeds', str(sp), '--out', str(out)]
    cap = (run.get('caps') or {}).get('GD')
    if cap is not None: cmd += ['--depth-cap', str(cap)]
    T0 = time.time()
    so, se, r_, wall, rc = timed(cmd, cpu)
    if rc != 0: raise RuntimeError('xorflux failed: ' + (so + se)[-800:])
    sm = start.metrics(model)
    traj = [[0.0, sm['G'], sm['G'], 0, sm['GD'], 0]]
    best = None; bestfile = None
    recs = [json.loads(l) for l in (out / 'workers' / 'quick-00' / 'records.jsonl').read_text().splitlines() if l.strip()]
    for rec in recs:
        if cap is not None and rec['depth'] > cap: continue
        if best is None or (rec['gates'], rec['depth']) < best:
            best = (rec['gates'], rec['depth']); bestfile = out / rec['path']
            traj.append([round(rec['t'], 3), rec['gates'], rec['gates'], 0, rec['depth'], 0])
    c = None
    if bestfile:
        d = json.loads(bestfile.read_text())
        c = core.Circuit(d.get('inputCount', start.n), len(d['outputSignals']), [(6, a, b) for a, b in d['gates']],
                         list(d['outputSignals'])).live()
    return c, traj, [r_], {'start_s': round(t_start, 4), 'xorflux_startup_s': round(wall - run['seconds'], 3)}, wall


def driver_hwm_reset():
    try: Path('/proc/self/clear_refs').write_text('5')     # resets VmHWM (Linux >= 4.0)
    except OSError: pass


def driver_hwm_kb():
    for ln in Path('/proc/self/status').read_text().splitlines():
        if ln.startswith('VmHWM:'): return int(ln.split()[1])
    return None


def execute(run, cpu, outdir):
    wd = Path(tempfile.mkdtemp(prefix='run-', dir=outdir))
    t0 = time.time(); driver_hwm_reset()
    try:
        if run['tool'] == 'xorflux': c, traj, rss, ov, search_s = run_xorflux(run, cpu, wd)
        else: c, traj, rss, ov, search_s = run_boolflux(run, cpu, wd)
        err = None
    except Exception as e:                           # recorded, not hidden
        c, traj, rss, ov, search_s, err = None, [], [], {}, None, repr(e)
    res = {'run': run, 'cpu': cpu, 'error': err, 'trajectory': traj, 'peak_rss_kb': max([r for r in rss if r] or [0]),
           'driver_rss_kb': driver_hwm_kb() if run['tool'] == 'boolflux' else None,
           'overhead': {k: round(v, 4) for k, v in ov.items()}, 'search_wall_s': search_s}
    if c is not None:
        model = core.Model.load(run['model'] if run['tool'] == 'boolflux' else 'xor')
        c.in_names = ['x%d' % i for i in range(c.n)]; c.out_names = ['y%d' % j for j in range(c.m)]
        f = wd / 'final.circ.txt'; f.write_text(core.write_ncff(c, model))
        tv = time.time()
        v = cli.verify_file(f, run['target'], model.name, run.get('caps') or {})
        res['verify_s'] = round(time.time() - tv, 3)
        res['final'] = {k: v['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')}
        res['final_counts'] = v['metrics']['counts']
        res['verified'] = bool(v['core_ok'] and v['independent_ok'] and v['library_ok'])
        res['feasible'] = all(c is None or v['metrics'][k] <= c for k, c in (run.get('caps') or {}).items())
        res['final_file'] = str(f)
    (outdir / (run['label'] + '.json')).write_text(json.dumps(res) + '\n')
    return res


def worker(plan_path, outdir, cpu, idx):
    """One pinned process: run the given tasks sequentially on one CPU (Python work included)."""
    os.sched_setaffinity(0, {cpu})
    plan = json.loads(Path(plan_path).read_text())
    for i in idx:
        for r in plan['tasks'][i]:
            if (outdir / (r['label'] + '.json')).exists(): continue
            res = execute(r, cpu, outdir)
            print('%s cpu%d %s %s %s' % (time.strftime('%H:%M:%S'), cpu, r['label'], res.get('final'),
                                         res.get('error') or ''), flush=True)


def main():
    plan_path = sys.argv[1]; outdir = Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    cpus = [int(x) for x in sys.argv[sys.argv.index('--cpus') + 1].split(',')] if '--cpus' in sys.argv else [0, 2, 4, 6, 8, 10, 12, 14]
    if '--worker' in sys.argv:
        cpu = int(sys.argv[sys.argv.index('--worker') + 1])
        idx = [int(x) for x in sys.argv[sys.argv.index('--tasks') + 1].split(',') if x]
        worker(plan_path, outdir, cpu, idx); return
    plan = json.loads(Path(plan_path).read_text())
    todo = [i for i, t in enumerate(plan['tasks']) if not all((outdir / (r['label'] + '.json')).exists() for r in t)]
    # balance by budget: longest tasks first onto the least loaded CPU
    load = {c: 0.0 for c in cpus}; assign = {c: [] for c in cpus}
    for i in sorted(todo, key=lambda i: -sum(r['seconds'] for r in plan['tasks'][i])):
        c = min(cpus, key=lambda c: load[c]); assign[c].append(i)
        load[c] += sum(r['seconds'] for r in plan['tasks'][i])
    env = dict(os.environ, BFXBENCH_BIN=str(BIN))
    procs = [subprocess.Popen([sys.executable, __file__, plan_path, str(outdir), '--worker', str(c),
                               '--tasks', ','.join(map(str, assign[c]))], env=env) for c in cpus if assign[c]]
    print('workers:', {c: len(assign[c]) for c in cpus}, 'max budget per CPU %.0f s' % max(load.values()), flush=True)
    for p in procs: p.wait()


if __name__ == '__main__':
    main()
