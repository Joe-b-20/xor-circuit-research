"""BoolFlux command line: run searches, verify circuits, build starting circuits.

    python3 nonlinear/boolflux/cli.py run --target present --model bgc --start anf \\
        --objective cost,gd --iters 200000 --seeds 1-8 --out nonlinear/boolflux/runs/present-bgc
    python3 nonlinear/boolflux/cli.py verify FILE.circ.txt --target present --model bgc
    python3 nonlinear/boolflux/cli.py start --target aes --start anf --model nist --out start.circ.txt

Every saved circuit is verified twice before it is reported: by core.Circuit evaluation
(bitsliced, against targets.py) and by the independent verifier
(independent/verify.py, exhaustive per-input evaluation, its own AES and table code).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from boolflux import core, starts, targets, skeleton   # noqa: E402
from concurrent.futures import ThreadPoolExecutor   # noqa: E402

KDIR = HERE / 'kernel'
KBIN = KDIR / 'bfx'
SBIN = KDIR / 'skel'
INDEP = HERE / 'independent' / 'verify.py'
REPO = HERE.parents[1]


def build_kernel():
    for b, src in ((KBIN, KDIR / 'bfx.c'), (SBIN, KDIR / 'skel.c')):
        if not b.exists() or b.stat().st_mtime < src.stat().st_mtime:
            subprocess.run(['gcc', '-O2', '-o', str(b), str(src), '-lm'], check=True)
    return KBIN


def snapshot(out):
    """Copy the sources into OUT/src and build private kernel binaries OUT/bin/{bfx,skel}, so
    a run keeps using the code it started with and records exactly what ran."""
    import shutil
    src = Path(out) / 'src'; bindir = Path(out) / 'bin'
    if not (bindir / 'bfx').exists():
        src.mkdir(parents=True, exist_ok=True); bindir.mkdir(parents=True, exist_ok=True)
        for f in ('kernel/bfx.c', 'kernel/skel.c', 'cli.py', 'core.py', 'skeleton.py', 'starts.py', 'targets.py'):
            shutil.copy(HERE / f, src / Path(f).name)
        for b in ('bfx', 'skel'):
            subprocess.run(['gcc', '-O2', '-o', str(bindir / b), str(src / (b + '.c')), '-lm'], check=True)
    global KBIN, SBIN
    KBIN = bindir / 'bfx'; SBIN = bindir / 'skel'
    h = hashlib.sha256()
    for f in sorted(src.iterdir()):
        h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:12]


def kernel_hash():
    """Hash of every source file that can change a result (kernels and the Python side)."""
    h = hashlib.sha256()
    for f in ('kernel/bfx.c', 'kernel/skel.c', 'cli.py', 'core.py', 'skeleton.py', 'starts.py', 'targets.py'):
        h.update((HERE / f).read_bytes())
    return h.hexdigest()[:12]


# ---- verification -----------------------------------------------------------------------------
def verify_core(c: core.Circuit, table):
    return c.value_table() == list(table)


def verify_independent(path, target, model_path, caps=None):
    if target == 'aes': fn = ['--aes']
    elif target == 'aes-inv': fn = ['--aes-inv']
    elif target in targets.names() and target not in targets.BUILTIN:
        fn = ['--table', str(targets.SBOX_FILE), '--name', target]   # the spec table itself
    else:
        n, m, table, _ = targets.load(target)
        fj = Path(path).with_suffix('.fn.json')
        fj.write_text(json.dumps({'n': n, 'm': m, 'table': table}) + '\n', encoding='utf-8')
        fn = ['--fn', str(fj)]
    cmd = [sys.executable, str(INDEP), str(path)] + fn + ['--json']
    if model_path: cmd += ['--model', str(model_path)]
    for k, v in (caps or {}).items():
        if v is not None: cmd += ['--max-%s' % k, str(v)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        res = json.loads(r.stdout)[0]
    except Exception:
        return {'ok': False, 'error': (r.stdout + r.stderr)[-2000:]}
    res['ok'] = (r.returncode == 0) and bool(res.get('ok', res.get('pass', False)))
    return res


def verify_file(path, target, model_name, caps=None):
    """Both verifiers; the independent one also checks the caps, and its metrics must equal
    core's (G, A, GD, AD, cost, counts), else independent_ok is False."""
    model = core.Model.load(model_name)
    n, m, table, _ = targets.load(target)
    c = core.read_ncff(str(path))
    lib_ok = {g[0] for g in c.gates} <= model.ops()
    ok1 = verify_core(c, table)
    mpath = Path(model_name) if Path(model_name).exists() else core.MODELS / ('%s.json' % model.name)
    ind = verify_independent(path, target, mpath, caps)
    mt = c.metrics(model) if lib_ok else c.metrics()
    im = ind.get('metrics') or {}
    counts = dict(mt['counts'])
    if model.not_as == 'XNOR0' and 'NOT' in counts:     # written as XNOR t a 0 in the file
        counts['XNOR'] = counts.get('XNOR', 0) + counts.pop('NOT')
    agree = all(im.get(k) == mt[k] for k in ('G', 'A', 'GD', 'AD')) and im.get('counts') == dict(sorted(counts.items()))
    if lib_ok and ind.get('ok'):
        agree = agree and abs(float(im.get('cost', -1)) - mt['cost']) < 1e-6
    return {'file': str(path), 'core_ok': ok1, 'library_ok': lib_ok,
            'independent_ok': bool(ind.get('ok')) and agree, 'metrics_agree': agree,
            'metrics': mt, 'independent': ind}


# ---- starting circuits ------------------------------------------------------------------------
def make_start(target, start, model):
    n, m, table, _ = targets.load(target)
    if start == 'anf':
        c = starts.anf(n, m, table, model.ops(), name='%s-anf' % target)
    else:
        c = core.read_ncff(start)
        if 'NOT' not in model.gates and any(g[0] == 3 for g in c.gates):
            raise SystemExit('start uses NOT but the model has no NOT')
    if not verify_core(c, table):
        raise SystemExit('start circuit does not compute %s' % target)
    bad = {g[0] for g in c.gates} - model.ops()
    if bad:
        raise SystemExit('start circuit uses gates outside model %s: %s'
                         % (model.name, sorted(core.OPNAME.get(b, b) for b in bad)))
    return c


OBJ_KEYS = {'cost': 'w.cost', 'g': 'w.g', 'a': 'w.a', 'gd': 'w.gd', 'ad': 'w.ad'}


def objective_weights(spec):
    """'a,cost,gd' -> lexicographic weights 1, 1e-4, 1e-8."""
    w = {v: 0.0 for v in OBJ_KEYS.values()}
    if len(spec.split(',')) > 3:
        raise SystemExit('at most three objective keys')
    for i, k in enumerate(spec.split(',')):
        w[OBJ_KEYS[k.strip()]] += 10.0 ** (-4 * i)
    return w


DEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
            'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
            'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}


def kernel_config(path, start_path, out_path, model, args, seed, extra):
    cfg = dict(DEFAULTS)
    cfg.update(objective_weights(args.objective))
    for op, c in model.cost.items(): cfg['cost.%d' % op] = c
    if args.cap_gd is not None: cfg['cap.gd'] = args.cap_gd
    if args.cap_ad is not None: cfg['cap.ad'] = args.cap_ad
    if args.cap_a is not None: cfg['cap.a'] = args.cap_a
    cfg.update(extra)
    cfg.update({'in': start_path, 'out': out_path, 'seed': seed, 'seconds': args.seconds,
                'iters': args.iters})
    path.write_text(''.join('%s %s\n' % kv for kv in cfg.items()), encoding='utf-8')
    return cfg


def parse_seeds(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def parse_sets(items):
    d = {}
    for it in items or []:
        k, v = it.split('=', 1); d[k] = v
    return d


def parse_kernel_log(text):
    final = {}; bests = []; moves = {}
    for ln in text.splitlines():
        t = ln.split()
        if not t: continue
        if t[0] == 'final':
            final = {t[i]: float(t[i + 1]) for i in range(1, len(t) - 1, 2)}
        elif t[0] == 'best':
            d = {t[i]: t[i + 1] for i in range(1, len(t) - 1, 2)}
            bests.append({'t': float(d['t']), 'it': int(d['it']), 'mv': d['mv'], 'cost': float(d['cost']),
                          'G': int(d['G']), 'A': int(d['A']), 'GD': int(d['GD']), 'AD': int(d['AD'])})
        elif t[0] == 'move':
            moves[t[1]] = {t[i]: float(t[i + 1]) for i in range(2, len(t) - 1, 2)}
    return final, bests, moves


def cmd_run(args):
    model = core.Model.load(args.model)
    n, m, table, desc = targets.load(args.target)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    code_hash = snapshot(out)
    start = make_start(args.target, args.start, model)
    extra = parse_sets(args.set)
    seeds = parse_seeds(args.seeds)
    pool = [start]
    summary = {'target': args.target, 'target_description': desc, 'model': model.name,
               'model_gates': model.gates, 'objective': args.objective, 'caps':
               {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a},
               'start': args.start, 'start_metrics': start.metrics(model), 'seeds': seeds,
               'iters': args.iters, 'seconds_cap': args.seconds, 'rounds': args.rounds,
               'code_sha256_12': code_hash, 'code_snapshot': str(Path(args.out) / 'src'), 'settings': {**DEFAULTS, **extra},
               'command': ' '.join(['python3', 'nonlinear/boolflux/cli.py'] + sys.argv[1:]),
               'runs': []}
    t_all = time.time()
    for rnd in range(args.rounds):
        procs = []
        for i, seed in enumerate(seeds):
            st = pool[i % len(pool)]
            tag = 'r%d-s%d' % (rnd, seed)
            sp = out / ('%s.start.bfx' % tag); sp.write_text(core.to_kernel(st), encoding='utf-8')
            bp = out / ('%s.best.bfx' % tag); cp = out / ('%s.cfg' % tag)
            kernel_config(cp, str(sp), str(bp), model, args, seed + 1000 * rnd, extra)
            procs.append((tag, seed, cp, bp))
        running = []; results = []
        queue = list(procs)
        jobs = args.jobs or os.cpu_count()
        while queue or running:
            while queue and len(running) < jobs:
                tag, seed, cp, bp = queue.pop(0)
                lf = open(out / ('%s.log' % tag), 'w')
                p = subprocess.Popen([str(KBIN), str(cp)], stdout=lf, stderr=subprocess.STDOUT)
                running.append((p, lf, tag, seed, bp, time.time()))
            time.sleep(0.05)
            for r in list(running):
                p, lf, tag, seed, bp, t0 = r
                if p.poll() is not None:
                    lf.close(); running.remove(r)
                    log = (out / ('%s.log' % tag)).read_text()
                    final, bests, moves = parse_kernel_log(log)
                    c = core.from_kernel(bp.read_text(), '%s-%s' % (args.target, tag))
                    c.in_names = ['x%d' % i for i in range(n)]; c.out_names = ['y%d' % j for j in range(m)]
                    ok = verify_core(c, table)
                    results.append({'time_capped': final.get('iters', 0) < args.iters,
                                    'round': rnd, 'seed': seed, 'kernel_seed': seed + 1000 * rnd, 'tag': tag,
                                    'returncode': p.returncode, 'core_ok': ok,
                                    'metrics': c.metrics(model), 'wall_s': round(time.time() - t0, 2),
                                    'final': final, 'improvements': bests, 'moves': moves,
                                    'circuit': c})
        key = lambda r: (r['final'].get('obj', 1e18), r['seed'])
        results.sort(key=key)
        for r in results:
            if r['returncode'] != 0 or not r['core_ok']:
                raise SystemExit('run %s failed (rc %s, core_ok %s); see its log'
                                 % (r['tag'], r['returncode'], r['core_ok']))
        # next round's pool: distinct best circuits
        seen = set(); pool = []
        for r in results:
            h = core.to_kernel(r['circuit'])
            if h in seen: continue
            seen.add(h); pool.append(r['circuit'])
            if len(pool) >= max(1, args.pool): break
        for r in results:
            rr = dict(r); rr.pop('circuit'); summary['runs'].append(rr)
        best = results[0]
        print('round %d: best %s %s (seed %d)' % (rnd, json.dumps({k: best['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')}),
                                                   json.dumps(best['metrics']['counts']), best['seed']), flush=True)
    summary['wall_s'] = round(time.time() - t_all, 1)
    # write and verify the best circuit
    bc = best['circuit']
    bc.name = '%s-%s-best' % (args.target, model.name)
    bpath = out / 'best.circ.txt'
    bpath.write_text(core.write_ncff(bc, model, comments=[
        'BoolFlux result for %s (%s)' % (args.target, desc),
        'model %s, objective %s, caps %s' % (model.name, args.objective, summary['caps']),
        'command: %s' % summary['command'], 'kernel bfx.c sha256 %s' % summary['code_sha256_12'],
        'seed %d round %d' % (best['seed'], best['round'])]), encoding='utf-8')
    caps = {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a}
    v = verify_file(bpath, args.target, args.model, caps)
    mt = v['metrics']
    feas = ((args.cap_gd is None or mt['GD'] <= args.cap_gd) and (args.cap_ad is None or mt['AD'] <= args.cap_ad)
            and (args.cap_a is None or mt['A'] <= args.cap_a))
    summary['best'] = {'file': str(bpath), 'seed': best['seed'], 'round': best['round'], 'feasible': feas,
                       'metrics': v['metrics'], 'core_ok': v['core_ok'], 'library_ok': v['library_ok'],
                       'independent_ok': v['independent_ok'],
                       'independent_metrics': v['independent'].get('metrics')}
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print('best: %s  core_ok=%s independent_ok=%s library_ok=%s  -> %s' % (
        json.dumps({k: v['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')}), v['core_ok'],
        v['independent_ok'], v['library_ok'], bpath))
    if not feas:
        raise SystemExit('CAPS NOT MET by the best circuit %s (no feasible circuit found)' % bpath)
    if not (v['core_ok'] and v['independent_ok'] and v['library_ok']):
        raise SystemExit('VERIFICATION FAILED for %s' % bpath)


# ---- pipeline: skeleton search -> synthesis -> gate search ---------------------------------
SKEL_DEFAULTS = {'w.a': 1, 'w.lin': 0.02, 'T0': 0.3, 'Tperiod_it': 4000, 'mv.swap': 4, 'mv.merge': 3,
                 'mv.split': 1, 'mv.perturb': 1, 'pairs': 60000, 'fext': 400}


def run_skel(c, table, out, tag, seed, args, extra):
    """Skeleton search from circuit c; returns (synthesized circuit, kernel log)."""
    sk = skeleton.extract(c)
    outs = core.tables_from_values(c.n, c.m, table)
    sp = out / ('%s.skin' % tag); sp.write_text(skeleton.write_skel(sk, outs), encoding='utf-8')
    so = out / ('%s.skout' % tag); cp = out / ('%s.skcfg' % tag)
    cfg = dict(SKEL_DEFAULTS); cfg.update({k[5:]: v for k, v in extra.items() if k.startswith('skel.')})
    if args.cap_ad is not None: cfg['cap.ad'] = args.cap_ad
    cfg.update({'in': sp, 'out': so, 'seed': seed, 'iters': args.skel_iters, 'seconds': args.seconds})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()), encoding='utf-8')
    r = subprocess.run([str(SBIN), str(cp)], capture_output=True, text=True)
    (out / ('%s.sklog' % tag)).write_text(r.stdout + r.stderr, encoding='utf-8')
    if r.returncode != 0:
        raise RuntimeError('skel failed %s: %s' % (tag, r.stderr[-500:]))
    sk2 = skeleton.read_skel(so.read_text())
    model = core.Model.load(args.model)
    # three synthesis variants (greedy; Paar per AND level; Paar also for the outputs): keep the smallest
    # synthesis variants (seeded + three from forms): seeded with the parent circuit (reuses every parent gate whose function
    # survives), and from forms only (greedy; Paar per AND level; Paar also for the outputs)
    variants = [skeleton.synthesize(sk2, model.ops(), name=tag, parent=c)]
    if extra.get('synth.unseeded', '1') != '0':
        variants += [skeleton.synthesize(sk2, model.ops(), name=tag, use_paar=up, paar_outputs=po)
                     for up, po in ((False, False), (True, False), (True, True))]
    c2 = min(variants, key=lambda c: c.metrics(model)['cost'])
    if c2.value_table() != list(table):
        raise RuntimeError('synthesized circuit wrong (%s)' % tag)
    return c2, r.stdout


def run_gate(c, out, tag, seed, model, args, extra):
    sp = out / ('%s.start.bfx' % tag); sp.write_text(core.to_kernel(c), encoding='utf-8')
    bp = out / ('%s.best.bfx' % tag); cp = out / ('%s.cfg' % tag)
    kernel_config(cp, str(sp), str(bp), model, args, seed,
                  {k: v for k, v in extra.items() if not k.startswith(('skel.', 'synth.'))})
    with open(out / ('%s.log' % tag), 'w') as lf:
        r = subprocess.run([str(KBIN), str(cp)], stdout=lf, stderr=subprocess.STDOUT)
    log = (out / ('%s.log' % tag)).read_text()
    if r.returncode != 0:
        raise RuntimeError('bfx failed %s' % tag)
    final, bests, moves = parse_kernel_log(log)
    c2 = core.from_kernel(bp.read_text(), tag)
    return c2, final, bests, moves


def cmd_pipe(args):
    model = core.Model.load(args.model)
    n, m, table, desc = targets.load(args.target)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    code_hash = snapshot(out)
    start = make_start(args.target, args.start, model)
    extra = parse_sets(args.set)
    seeds = parse_seeds(args.seeds)
    obj_w = objective_weights(args.objective)

    def objective(mt):
        return (obj_w['w.cost'] * mt['cost'] + obj_w['w.g'] * mt['G'] + obj_w['w.a'] * mt['A']
                + obj_w['w.gd'] * mt['GD'] + obj_w['w.ad'] * mt['AD'])

    def feasible(mt):
        return ((args.cap_gd is None or mt['GD'] <= args.cap_gd)
                and (args.cap_ad is None or mt['AD'] <= args.cap_ad)
                and (args.cap_a is None or mt['A'] <= args.cap_a))

    summary = {'command': ' '.join(['python3', 'nonlinear/boolflux/cli.py'] + sys.argv[1:]),
               'target': args.target, 'target_description': desc, 'model': model.name,
               'model_gates': model.gates, 'objective': args.objective,
               'caps': {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a},
               'start': args.start, 'start_metrics': start.metrics(model), 'seeds': seeds,
               'iters': args.iters, 'skel_iters': args.skel_iters, 'rounds': args.rounds,
               'skel_share': args.skel_share, 'code_sha256_12': code_hash, 'code_snapshot': str(Path(args.out) / 'src'),
               'settings': {**DEFAULTS, **{'skel.' + k: v for k, v in SKEL_DEFAULTS.items()}, **extra},
               'runs': []}
    pool = [start]; t_all = time.time(); best = None
    for rnd in range(args.rounds):
        def job(i_seed):
            i, seed = i_seed
            ks = seed + 1000 * rnd
            c0 = pool[i % len(pool)]
            tag = 'r%d-s%d' % (rnd, seed)
            use_skel = args.skel_share > 0 and ((i * 0.618034) % 1.0) < args.skel_share
            t0 = time.time()
            rec = {'round': rnd, 'seed': seed, 'kernel_seed': ks, 'tag': tag, 'skel': use_skel,
                   'from': c0.metrics(model)}
            if use_skel:
                c1, sklog = run_skel(c0, table, out, tag, ks, args, extra)
                rec['synth'] = c1.metrics(model)
            else:
                c1 = c0
            c2, final, bests, moves = run_gate(c1, out, tag, ks, model, args, extra)
            c2.in_names = ['x%d' % k for k in range(n)]; c2.out_names = ['y%d' % k for k in range(m)]
            ok = verify_core(c2, table)
            mt = c2.metrics(model)
            rec.update({'time_capped': final.get('iters', 0) < args.iters,
                        'core_ok': ok, 'metrics': mt, 'obj': objective(mt), 'feasible': feasible(mt),
                        'final': final, 'improvements': bests, 'moves': moves,
                        'wall_s': round(time.time() - t0, 2)})
            return rec, c2
        order = list(enumerate(seeds))
        with ThreadPoolExecutor(max_workers=args.jobs or os.cpu_count()) as ex:
            res = list(ex.map(job, order))
        for rec, c2 in res:
            if not rec['core_ok']:
                raise SystemExit('verification failed in %s' % rec['tag'])
        cands = [(rec['obj'], rec['seed'], rec, c2) for rec, c2 in res if rec['feasible']]
        for pc in pool:     # the pool's circuits stay candidates (a job may not improve)
            mt = pc.metrics(model)
            if feasible(mt):
                cands.append((objective(mt), 10 ** 9, {'tag': 'pool', 'metrics': mt}, pc))
        cands.sort(key=lambda t: (t[0], t[1]))
        seen = set(); newpool = []
        for o, sd, rec, c2 in cands:
            h = core.to_kernel(c2)
            if h in seen: continue
            seen.add(h); newpool.append(c2)
            if len(newpool) >= args.pool: break
        if newpool: pool = newpool
        if cands and (best is None or cands[0][0] < best[0]): best = cands[0]
        for rec, _ in res: summary['runs'].append(rec)
        bm = best[2]['metrics'] if best else None
        print('round %d: best %s %s  (jobs: %s)' % (
            rnd, json.dumps({k: bm[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}), json.dumps(bm['counts']),
            ' '.join('%s:%g/%d' % ('S' if r['skel'] else 'G', r['metrics']['cost'], r['metrics']['A'])
                     for r, _ in res)), flush=True)
    summary['wall_s'] = round(time.time() - t_all, 1)
    if best is None:
        raise SystemExit('no feasible circuit found')
    bc = best[3]; bc.name = '%s-%s-best' % (args.target, model.name)
    bc.in_names = ['x%d' % k for k in range(n)]; bc.out_names = ['y%d' % k for k in range(m)]
    bpath = out / 'best.circ.txt'
    bpath.write_text(core.write_ncff(bc, model, comments=[
        'BoolFlux result for %s (%s)' % (args.target, desc),
        'model %s, objective %s, caps %s' % (model.name, args.objective, summary['caps']),
        'command: %s' % summary['command'], 'kernel sha256 %s' % summary['code_sha256_12'],
        'from job %s' % best[2].get('tag')]), encoding='utf-8')
    v = verify_file(bpath, args.target, args.model, {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a})
    summary['best'] = {'file': str(bpath), 'job': best[2].get('tag'), 'metrics': v['metrics'],
                       'core_ok': v['core_ok'], 'library_ok': v['library_ok'],
                       'independent_ok': v['independent_ok'],
                       'independent_metrics': v['independent'].get('metrics')}
    (out / 'summary.json').write_text(json.dumps(summary, indent=1, default=str) + '\n', encoding='utf-8')
    print('best: %s  core_ok=%s independent_ok=%s library_ok=%s  -> %s' % (
        json.dumps({k: v['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')}), v['core_ok'],
        v['independent_ok'], v['library_ok'], bpath))
    if not (v['core_ok'] and v['independent_ok'] and v['library_ok']):
        raise SystemExit('VERIFICATION FAILED for %s' % bpath)


def cmd_verify(args):
    ok = True
    for f in args.files:
        v = verify_file(f, args.target, args.model)
        good = v['core_ok'] and v['independent_ok'] and v['library_ok']
        ok &= good
        print('%s %s %s core=%s indep=%s lib=%s' % ('ok  ' if good else 'FAIL', f,
              json.dumps({k: v['metrics'].get(k) for k in ('cost', 'G', 'A', 'GD', 'AD', 'counts')}),
              v['core_ok'], v['independent_ok'], v['library_ok']))
    sys.exit(0 if ok else 1)


def cmd_start(args):
    model = core.Model.load(args.model)
    c = make_start(args.target, args.start, model)
    Path(args.out).write_text(core.write_ncff(c, model, comments=['start: %s' % args.start]), encoding='utf-8')
    print(json.dumps(c.metrics(model)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog='boolflux')
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--target', required=True)
    r.add_argument('--model', required=True)
    r.add_argument('--start', default='anf', help="'anf' or an NCFF circuit file")
    r.add_argument('--objective', default='cost', help='lexicographic, e.g. cost,gd or a,cost')
    r.add_argument('--cap-gd', type=int); r.add_argument('--cap-ad', type=int); r.add_argument('--cap-a', type=int)
    r.add_argument('--iters', type=int, default=200000)
    r.add_argument('--seconds', type=float, default=3600, help='safety cap per process')
    r.add_argument('--seeds', default='1-8')
    r.add_argument('--rounds', type=int, default=1)
    r.add_argument('--pool', type=int, default=4, help='distinct circuits carried to the next round')
    r.add_argument('--jobs', type=int, default=0)
    r.add_argument('--out', required=True)
    r.add_argument('--set', action='append', help='kernel setting key=value')
    r.set_defaults(func=cmd_run)
    p = sub.add_parser('pipe', help='skeleton search + synthesis + gate search, in rounds')
    p.add_argument('--target', required=True); p.add_argument('--model', required=True)
    p.add_argument('--start', default='anf'); p.add_argument('--objective', default='cost')
    p.add_argument('--cap-gd', type=int); p.add_argument('--cap-ad', type=int); p.add_argument('--cap-a', type=int)
    p.add_argument('--iters', type=int, default=100000); p.add_argument('--skel-iters', type=int, default=20000)
    p.add_argument('--seconds', type=float, default=3600); p.add_argument('--seeds', default='1-8')
    p.add_argument('--rounds', type=int, default=3); p.add_argument('--pool', type=int, default=4)
    p.add_argument('--skel-share', type=float, default=0.5, help='fraction of jobs that run the skeleton search first')
    p.add_argument('--jobs', type=int, default=0); p.add_argument('--out', required=True)
    p.add_argument('--set', action='append')
    p.set_defaults(func=cmd_pipe)
    v = sub.add_parser('verify')
    v.add_argument('files', nargs='+'); v.add_argument('--target', required=True); v.add_argument('--model', required=True)
    v.set_defaults(func=cmd_verify)
    s = sub.add_parser('start')
    s.add_argument('--target', required=True); s.add_argument('--model', required=True)
    s.add_argument('--start', default='anf'); s.add_argument('--out', required=True)
    s.set_defaults(func=cmd_start)
    a = ap.parse_args(argv)
    a.func(a)


if __name__ == '__main__':
    main()
