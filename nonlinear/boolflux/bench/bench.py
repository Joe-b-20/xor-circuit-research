"""Matched-budget benchmark runs for BoolFlux (and XORFlux on linear maps).

    python3 nonlinear/boolflux/bench/bench.py PLAN.json OUTDIR [--cpus 0,2,4,...]

PLAN.json: {"tasks": [task, ...]}; a task is a list of runs executed back to back on one pinned
CPU (so the runs of a comparison pair share hardware).  A run is a dict:
  tool      'boolflux' | 'xorflux'
  config    boolflux: 'gate' (gate kernel only) or 'full' (skeleton + seeded rebuild + gate,
            alternating), plus kernel settings in 'set' (ablations) and 'skel_set'
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
from boolflux import core, skeleton, starts, targets   # noqa: E402

if os.environ.get('BFXBENCH_BIN'):                     # worker: binaries built by the parent
    BIN = Path(os.environ['BFXBENCH_BIN'])
else:
    BIN = Path(tempfile.mkdtemp(prefix='bfxbench-'))
    for b in ('bfx', 'skel'):
        subprocess.run(['gcc', '-O2', '-o', str(BIN / b), str(PKG / 'kernel' / (b + '.c')), '-lm'], check=True)


def timed(cmd, cpu):
    """Run pinned under /usr/bin/time -v; return (stdout+stderr, peak RSS kB, wall s)."""
    t0 = time.time()
    r = subprocess.run(['taskset', '-c', str(cpu), '/usr/bin/time', '-v'] + cmd, capture_output=True, text=True)
    m = re.search(r'Maximum resident set size \(kbytes\): (\d+)', r.stderr)
    return r.stdout, r.stderr, int(m.group(1)) if m else None, time.time() - t0, r.returncode


def load_start(run, model):
    n, m, table, _ = targets.load(run['target'])
    st = run['start']
    if st == 'anf':
        return starts.anf(n, m, table, model.ops())
    if st.endswith('.json'):                        # XORFlux seed circuit
        d = json.loads(Path(st).read_text())
        nn = d['inputCount']
        return core.Circuit(nn, len(d['outputSignals']), [(6, a, b) for a, b in d['gates']],
                            list(d['outputSignals'])).live()
    return core.read_ncff(st)


def to_xorflux_json(c, name, path):
    assert all(op == 6 for op, a, b in c.gates)
    path.write_text(json.dumps({'benchmark': name, 'inputCount': c.n, 'gates': [[a, b] for _, a, b in c.gates],
                                'outputSignals': c.outputs}) + '\n')


def kernel_cfg(path, start_path, out_path, model, run, seconds, seed, extra):
    cfg = dict(cli.DEFAULTS); cfg.update(cli.objective_weights(run.get('objective', 'cost')))
    for op, c in model.cost.items(): cfg['cost.%d' % op] = c
    caps = run.get('caps') or {}
    for k, key in (('GD', 'cap.gd'), ('AD', 'cap.ad'), ('A', 'cap.a')):
        if caps.get(k) is not None: cfg[key] = caps[k]
    if all(not (op in core.NONLINEAR_OPS) for op in model.ops()): cfg['linear'] = run.get('linear', 1)
    cfg.update(extra)
    cfg.update({'in': start_path, 'out': out_path, 'seed': seed, 'seconds': seconds, 'iters': 10 ** 15})
    path.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))


def parse_bests(log, t_offset):
    out = []
    for ln in log.splitlines():
        t = ln.split()
        if t and t[0] == 'best':
            d = {t[i]: t[i + 1] for i in range(1, len(t) - 1, 2)}
            out.append([round(float(d['t']) + t_offset, 3), float(d['cost']), int(d['G']), int(d['A']), int(d['GD']), int(d['AD'])])
    return out


def run_boolflux(run, cpu, wd):
    model = core.Model.load(run['model'])
    n, m, table, _ = targets.load(run['target'])
    t0 = time.time(); start = load_start(run, model); t_start = time.time() - t0
    sm = start.metrics(model)
    traj = [[0.0, sm['cost'], sm['G'], sm['A'], sm['GD'], sm['AD']]]
    feas = lambda x: all(c is None or x[k] <= c for k, c in (run.get('caps') or {}).items())
    obj_w = cli.objective_weights(run.get('objective', 'cost'))
    obj = lambda x: obj_w['w.cost'] * x['cost'] + obj_w['w.g'] * x['G'] + obj_w['w.a'] * x['A'] + obj_w['w.gd'] * x['GD'] + obj_w['w.ad'] * x['AD']
    overhead = {'start_s': round(t_start, 4), 'extract_s': 0, 'skel_s': 0, 'synth_s': 0, 'kernel_startup_s': 0}
    rss = []; budget = run['seconds']; T0 = time.time()
    best_c = start; best_m = sm
    cur = start; rnd = 0; skel_share = 0.2
    while True:
        el = time.time() - T0
        if el >= budget - 0.05: break
        if run['config'] == 'gate':
            stages = [('gate', budget - el)]
        else:
            R = run.get('round_s', 10.0)
            # adaptive (v3): the skeleton slice halves after every round in which the skeleton-derived
            # candidate did not end the round better than the incoming best (minimum 0.5 s)
            share = skel_share if run.get('adaptive') else 0.2
            stages = [('skel', min(R * share, budget - el)), ('gate', None)]
            synth_gain = False
        cand = cur
        for kind, secs in stages:
            el = time.time() - T0
            if el >= budget - 0.05: break
            if kind == 'skel':
                ts = time.time(); sk = skeleton.extract(cand); overhead['extract_s'] += time.time() - ts
                outs = core.tables_from_values(n, m, table)
                (wd / 'sk.in').write_text(skeleton.write_skel(sk, outs))
                scfg = dict(cli.SKEL_DEFAULTS); scfg.update(run.get('skel_set', {}))
                if (run.get('caps') or {}).get('AD') is not None: scfg['cap.ad'] = run['caps']['AD']
                scfg.update({'in': wd / 'sk.in', 'out': wd / 'sk.out', 'seed': run['seed'] * 1000 + rnd,
                             'iters': 10 ** 15, 'seconds': secs})
                if 'iters' in run.get('skel_set', {}): scfg['iters'] = run['skel_set']['iters']   # 0: rebuild only
                (wd / 'sk.cfg').write_text(''.join('%s %s\n' % kv for kv in scfg.items()))
                ts = time.time()
                so, se, r_, wall, rc = timed([str(BIN / 'skel'), str(wd / 'sk.cfg')], cpu)
                overhead['skel_s'] += time.time() - ts; rss.append(r_)
                if rc != 0: raise RuntimeError('skel failed: ' + se[-500:])
                sk2 = skeleton.read_skel((wd / 'sk.out').read_text())
                ts = time.time()
                vs = []
                if run.get('seeded', True): vs.append(skeleton.synthesize(sk2, model.ops(), parent=cand))
                if run.get('unseeded', True):
                    vs += [skeleton.synthesize(sk2, model.ops(), use_paar=a, paar_outputs=b) for a, b in ((0, 0), (1, 0), (1, 1))]
                cin = obj(dict(cand.metrics(model)))
                cand = min(vs, key=lambda c: c.metrics(model)['cost'])
                synth_gain = obj(dict(cand.metrics(model))) < cin - 1e-12
                overhead['synth_s'] += time.time() - ts
                assert cand.value_table() == list(table)
            else:
                secs = secs if secs is not None else max(0.5, budget - (time.time() - T0)) if run['config'] == 'gate' else min(run.get('round_s', 10.0) * 0.8, budget - (time.time() - T0))
                (wd / 'g.in').write_text(core.to_kernel(cand))
                kernel_cfg(wd / 'g.cfg', wd / 'g.in', wd / 'g.out', model, run, secs, run['seed'] * 1000 + rnd, run.get('set', {}))
                t_launch = time.time() - T0
                so, se, r_, wall, rc = timed([str(BIN / 'bfx'), str(wd / 'g.cfg')], cpu)
                rss.append(r_)
                if rc != 0: raise RuntimeError('bfx failed: ' + (so + se)[-800:])
                ks = re.search(r'seconds ([\d.]+)', so.split('final')[-1])
                overhead['kernel_startup_s'] += max(0.0, wall - (float(ks.group(1)) if ks else wall))
                for row in parse_bests(so, t_launch):
                    mt = {'cost': row[1], 'G': row[2], 'A': row[3], 'GD': row[4], 'AD': row[5]}
                    if feas(mt) and (not feas(best_m) or obj(mt) < obj(best_m) - 1e-12):
                        best_m = mt; traj.append(row)
                cand = core.from_kernel((wd / 'g.out').read_text())
                cm = cand.metrics(model)
                if feas(cm) and (not feas(best_m) or obj(cm) <= obj(best_m) + 1e-12):
                    best_c = cand; best_m = {k: cm[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}
        if run['config'] != 'gate' and run.get('adaptive'):
            # the skeleton stage earns its slice only if its rebuilt candidate was already cheaper
            # than the circuit that went in
            gained = synth_gain
            skel_share = 0.2 if gained else max(0.5 / run.get('round_s', 10.0), skel_share / 2)
        cur = best_c; rnd += 1
        if run['config'] == 'gate': break
    search_s = time.time() - T0
    return best_c, traj, rss, overhead, search_s


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


def execute(run, cpu, outdir):
    wd = Path(tempfile.mkdtemp(prefix='run-', dir=outdir))
    t0 = time.time()
    try:
        if run['tool'] == 'xorflux': c, traj, rss, ov, search_s = run_xorflux(run, cpu, wd)
        else: c, traj, rss, ov, search_s = run_boolflux(run, cpu, wd)
        err = None
    except Exception as e:                           # recorded, not hidden
        c, traj, rss, ov, search_s, err = None, [], [], {}, None, repr(e)
    res = {'run': run, 'cpu': cpu, 'error': err, 'trajectory': traj, 'peak_rss_kb': max([r for r in rss if r] or [0]),
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
