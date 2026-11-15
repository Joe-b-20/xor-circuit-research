"""BoolFlux command line: run searches, verify circuits, build starting circuits.

    python3 nonlinear/boolflux/cli.py run --target present --model bgc --start anf \\
        --objective cost,gd --iters 200000 --seeds 1-8 --out ~/xs-campaigns/DATE-NAME/present-bgc
    python3 nonlinear/boolflux/cli.py verify FILE.circ.txt --target present --model bgc [--cap-gd 14]
    python3 nonlinear/boolflux/cli.py list
    python3 nonlinear/boolflux/cli.py start --target aes --start anf --model nist --out start.circ.txt
    python3 nonlinear/boolflux/cli.py flow --target aes --model nist --start FILE --cap-gd 14 \\
        --objective cost,gd --config full --skel-set iters=0 --adaptive --seconds 120 --seeds 1-4 --out DIR

`run` = gate kernel in rounds of a fixed iteration count; `pipe` = skeleton search, rebuild and gate
search in rounds; `flow` = the time-sliced workflows of the benchmark driver (workflow.py).
Ranking everywhere: feasible first, then total cap excess, then the objective keys in order
(objective.py); the kernel compares the same way (`lex`).  Run output belongs outside the
repository (runs/README.md); `python3 nonlinear/boolflux/cli.py CMD -h` explains every option.

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

from boolflux import core, objective, starts, targets, skeleton, workflow   # noqa: E402
from concurrent.futures import ThreadPoolExecutor   # noqa: E402

KDIR = HERE / 'kernel'
KBIN = KDIR / 'bfx'
SBIN = KDIR / 'skel'
INDEP = HERE / 'independent' / 'verify.py'
REPO = HERE.parents[1]


def compile_kernel(src, dst):
    """gcc -O2 SRC into DST through a temporary file of its own in DST's folder and an atomic
    rename (review 5: gcc wrote DST in place, so another process could start a half-written
    binary, and two builders wrote the same file)."""
    import tempfile
    dst = Path(dst)
    fd, tmp = tempfile.mkstemp(prefix=dst.name + '.', suffix='.tmp', dir=str(dst.parent)); os.close(fd)
    try:
        subprocess.run(['gcc', '-O2', '-o', tmp, str(src), '-lm'], check=True)
        os.chmod(tmp, 0o755)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def build_kernel():
    for b, src in ((KBIN, KDIR / 'bfx.c'), (SBIN, KDIR / 'skel.c')):
        if not b.exists() or b.stat().st_mtime < src.stat().st_mtime:
            compile_kernel(src, b)
    return KBIN


def snapshot(out):
    """Copy the sources into OUT/src and build private kernel binaries OUT/bin/{bfx,skel}, so
    a run keeps using the code it started with and records exactly what ran."""
    import shutil
    src = Path(out) / 'src'; bindir = Path(out) / 'bin'
    if not (bindir / 'bfx').exists():
        src.mkdir(parents=True, exist_ok=True); bindir.mkdir(parents=True, exist_ok=True)
        for f in ('kernel/bfx.c', 'kernel/skel.c', 'cli.py', 'core.py', 'skeleton.py', 'starts.py', 'targets.py', 'objective.py', 'workflow.py'):
            shutil.copy(HERE / f, src / Path(f).name)
        for b in ('bfx', 'skel'):
            compile_kernel(src / (b + '.c'), bindir / b)
    global KBIN, SBIN
    KBIN = bindir / 'bfx'; SBIN = bindir / 'skel'
    h = hashlib.sha256()
    for f in sorted(src.iterdir()):
        h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:12]


def kernel_hash():
    """Hash of every source file that can change a result (kernels and the Python side)."""
    h = hashlib.sha256()
    for f in ('kernel/bfx.c', 'kernel/skel.c', 'cli.py', 'core.py', 'skeleton.py', 'starts.py', 'targets.py', 'objective.py', 'workflow.py'):
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
    mpath = core.model_path(model_name)
    ind = verify_independent(path, target, mpath, caps)
    mt = c.metrics(model) if lib_ok else c.metrics()
    im = dict(ind.get('metrics') or {})
    # write_ncff emits `BUF y x` for an output that is an input or repeats an earlier output; the
    # independent verifier lists BUF in its counts (not in G), core has no such gate
    nbuf = (im.get('counts') or {}).get('BUF', 0)
    if nbuf:
        im['counts'] = {k: v for k, v in im['counts'].items() if k != 'BUF'}
    def fold(cn):
        # under a NOT-as-XNOR0 model a NOT may be written `XNOR t a 0` (our files) or `NOT t a`
        # (NIST-format copies); core reads both as NOT, the independent verifier counts what is
        # written, so both sides are compared with NOT counted as XNOR.  review5 P19: only core's
        # side was folded, and every file with an explicit NOT failed with identical metrics.
        cn = dict(cn or {})
        if model.not_as == 'XNOR0' and 'NOT' in cn:
            cn['XNOR'] = cn.get('XNOR', 0) + cn.pop('NOT')
        return dict(sorted(cn.items()))
    agree = all(im.get(k) == mt[k] for k in ('G', 'A', 'GD', 'AD')) and fold(im.get('counts')) == fold(mt['counts'])
    if lib_ok and ind.get('ok'):
        agree = agree and abs(float(im.get('cost', -1)) - mt['cost']) < 1e-6
    return {'file': str(path), 'core_ok': ok1, 'library_ok': lib_ok, 'buf_lines': nbuf,
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


def objective_weights(spec):
    """Kernel weights for the Metropolis step size plus the exact lexicographic order (`lex`)."""
    return objective.weights(spec)


DEFAULTS = workflow.DEFAULTS


def kernel_config(path, start_path, out_path, model, args, seed, extra):
    cfg = dict(DEFAULTS)
    cfg.update(objective_weights(args.objective))
    for op, c in model.cost.items(): cfg['cost.%d' % op] = c
    if args.cap_gd is not None: cfg['cap.gd'] = args.cap_gd
    if args.cap_ad is not None: cfg['cap.ad'] = args.cap_ad
    if args.cap_a is not None: cfg['cap.a'] = args.cap_a
    if workflow.is_linear(model): cfg['linear'] = 1      # exact n+1-pattern mode for XOR-only models
    cfg.update(extra)
    cfg.update({'in': start_path, 'out': out_path, 'seed': seed, 'seconds': args.seconds,
                'iters': args.iters})
    path.write_text(''.join('%s %s\n' % kv for kv in cfg.items()), encoding='utf-8')
    return cfg


def seed_scheme(args, cmd):
    """--seed-scheme v2 (default) or legacy = the formula this command used before review 5"""
    s = getattr(args, 'seed_scheme', None) or 'v2'
    return ('legacy-flow' if cmd == 'flow' else 'legacy-run') if s == 'legacy' else s


def kseed(args, seed, rnd):
    return workflow.kernel_seed(seed, rnd, seed_scheme(args, 'run'))


def parse_seeds(s):
    out = []
    try:
        for part in s.split(','):
            if '-' in part:
                a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
            else:
                out.append(int(part))
    except ValueError:
        out = []
    if not out:                 # review5 P7: 'a-b', '', '8-1' used to give a traceback or an empty run
        raise SystemExit('bad --seeds %r: use a list of non-negative integers and ranges, e.g. 1-8 or 1,3,5-7' % s)
    return out


def parse_sets(items, kernel=True):
    d = {}
    for it in items or []:
        if '=' not in it or not it.split('=', 1)[0]:
            raise SystemExit('bad setting %r: use KEY=VALUE (e.g. --set mv.resub3=0)' % it)
        k, v = it.split('=', 1); d[k] = v
    if kernel:      # gate-kernel settings (skel.* and synth.* go to the skeleton stage and are not checked here)
        workflow.check_sets({k: v for k, v in d.items() if not k.startswith(('skel.', 'synth.'))})
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


def caps_of(args):
    return {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a}


def write_best(out, bc, model, args, desc, summary, origin):
    """Write OUT/best.circ.txt (and summary.json) for the current incumbent; called after every
    round, so a later failure cannot lose it.  An incumbent outside the caps is marked."""
    n, m = bc.n, bc.m
    bc.name = '%s-%s-best' % (args.target, model.name)
    bc.in_names = ['x%d' % k for k in range(n)]; bc.out_names = ['y%d' % k for k in range(m)]
    caps = caps_of(args)
    mt = bc.metrics(model)
    feas = objective.feasible(mt, caps)
    bpath = out / 'best.circ.txt'
    bpath.write_text(core.write_ncff(bc, model, comments=[
        'BoolFlux result for %s (%s)' % (args.target, desc),
        'model %s, objective %s, caps %s' % (model.name, args.objective, caps),
        'command: %s' % summary['command'], 'code sha256 %s' % summary['code_sha256_12'], origin]
        + ([] if feas else ['CAPS NOT MET: this circuit violates the caps (best repair so far)'])), encoding='utf-8')
    v = verify_file(bpath, args.target, args.model, caps)
    summary['best'] = {'file': str(bpath), 'origin': origin, 'feasible': feas, 'metrics': v['metrics'],
                       'core_ok': v['core_ok'], 'library_ok': v['library_ok'],
                       'independent_ok': v['independent_ok'], 'buf_lines': v['buf_lines'],
                       'independent_metrics': v['independent'].get('metrics')}
    (out / 'summary.json').write_text(json.dumps(summary, indent=1, default=str) + '\n', encoding='utf-8')
    return v, feas, bpath


def finish(v, feas, bpath, failures):
    print('best: %s  core_ok=%s independent_ok=%s library_ok=%s  -> %s' % (
        json.dumps({k: v['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')}), v['core_ok'],
        v['independent_ok'], v['library_ok'], bpath))
    if not (v['core_ok'] and v['library_ok'] and (v['independent_ok'] or not feas)):
        raise SystemExit('VERIFICATION FAILED for %s' % bpath)
    if not feas:
        raise SystemExit('CAPS NOT MET by the best circuit %s (no feasible circuit found)' % bpath)
    if failures:
        raise SystemExit('%d job(s) failed (%s); the best of the others is saved' % (len(failures), ', '.join(failures)))


def cmd_run(args):
    model = core.Model.load(args.model)
    n, m, table, desc = targets.load(args.target)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    code_hash = snapshot(out)
    start = make_start(args.target, args.start, model)
    extra = parse_sets(args.set)
    seeds = parse_seeds(args.seeds)
    caps = caps_of(args)
    R = lambda mt: objective.rank(mt, caps, args.objective)
    pool = [start]
    summary = {'target': args.target, 'target_description': desc, 'model': model.name,
               'model_gates': model.gates, 'objective': args.objective, 'caps': caps,
               'start': args.start, 'start_metrics': start.metrics(model), 'seeds': seeds,
               'iters': args.iters, 'seconds_cap': args.seconds, 'rounds': args.rounds,
               'seed_scheme': seed_scheme(args, 'run'),
               'code_sha256_12': code_hash, 'code_snapshot': str(Path(args.out) / 'src'), 'settings': {**DEFAULTS, **extra},
               'command': ' '.join(['python3', 'nonlinear/boolflux/cli.py'] + sys.argv[1:]),
               'runs': []}
    t_all = time.time(); failures = []
    best = {'circuit': start, 'metrics': objective.measure(start, model, caps), 'seed': -1, 'round': -1}
    for rnd in range(args.rounds):
        procs = []
        for i, seed in enumerate(seeds):
            st = pool[i % len(pool)]
            tag = 'r%d-s%d' % (rnd, seed)
            sp = out / ('%s.start.bfx' % tag); sp.write_text(core.to_kernel(st), encoding='utf-8')
            bp = out / ('%s.best.bfx' % tag); cp = out / ('%s.cfg' % tag)
            kernel_config(cp, str(sp), str(bp), model, args, kseed(args, seed, rnd), extra)
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
                    rec = {'round': rnd, 'seed': seed, 'kernel_seed': kseed(args, seed, rnd), 'tag': tag,
                           'returncode': p.returncode, 'wall_s': round(time.time() - t0, 2),
                           'final': final, 'improvements': bests, 'moves': moves,
                           'time_capped': final.get('iters', 0) < args.iters}
                    try:
                        c = core.from_kernel(bp.read_text(), '%s-%s' % (args.target, tag))
                        rec['core_ok'] = p.returncode == 0 and verify_core(c, table)
                    except Exception as e:
                        c = None; rec['core_ok'] = False; rec['error'] = repr(e)
                    if rec['core_ok']:
                        rec['metrics'] = objective.measure(c, model, caps); rec['circuit'] = c
                    else:
                        failures.append(tag)
                    results.append(rec)
        ok = [r for r in results if r['core_ok']]
        ok.sort(key=lambda r: (R(r['metrics']), r['seed']))      # lexicographic, exact (M1)
        seen = set(); newpool = []
        for r in ok:
            h = core.to_kernel(r['circuit'])
            if h in seen: continue
            seen.add(h); newpool.append(r['circuit'])
            if len(newpool) >= max(1, args.pool): break
        if newpool: pool = newpool
        for r in results:
            rr = dict(r); rr.pop('circuit', None); summary['runs'].append(rr)
        if ok and (best is None or R(ok[0]['metrics']) < R(best['metrics'])):
            best = ok[0]
        summary['wall_s'] = round(time.time() - t_all, 1)
        v, feas, bpath = write_best(out, best['circuit'], model, args, desc, summary,
                                    'seed %d round %d' % (best['seed'], best['round']) if best['round'] >= 0 else 'the start (no job was better)')
        print('round %d: best %s %s (seed %d)%s' % (rnd, json.dumps({k: best['metrics'][k] for k in ('cost', 'G', 'A', 'GD', 'AD')}),
                                                     json.dumps(best['metrics']['counts']), best['seed'],
                                                     '' if feas else ' CAPS NOT MET'), flush=True)
    finish(v, feas, bpath, failures)


# ---- pipeline: skeleton search -> synthesis -> gate search ---------------------------------
SKEL_DEFAULTS = workflow.SKEL_DEFAULTS


def run_skel(c, table, out, tag, seed, args, extra):
    """Skeleton search from circuit c; returns (synthesized circuit, kernel log)."""
    sk = skeleton.extract(c)
    outs = core.tables_from_values(c.n, c.m, table)
    sp = out / ('%s.skin' % tag); sp.write_text(skeleton.write_skel(sk, outs), encoding='utf-8')
    so = out / ('%s.skout' % tag); cp = out / ('%s.skcfg' % tag)
    cfg = dict(SKEL_DEFAULTS)
    if args.cap_ad is not None: cfg['cap.ad'] = args.cap_ad
    cfg.update({'in': sp, 'out': so, 'seed': seed, 'iters': args.skel_iters, 'seconds': args.seconds})
    cfg.update({k[5:]: v for k, v in extra.items() if k.startswith('skel.')})   # --set skel.X wins (m12)
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()), encoding='utf-8')
    r = subprocess.run([str(SBIN), str(cp)], capture_output=True, text=True)
    (out / ('%s.sklog' % tag)).write_text(r.stdout + r.stderr, encoding='utf-8')
    if r.returncode != 0:
        raise RuntimeError('skel failed %s: %s' % (tag, r.stderr[-500:]))
    sk2 = skeleton.read_skel(so.read_text())
    model = core.Model.load(args.model)
    # synthesis variants (seeded + three from forms): seeded with the parent circuit (reuses every parent gate whose function
    # survives), and from forms only (greedy; Paar per AND level; Paar also for the outputs)
    variants = []
    if extra.get('synth.seeded', '1') != '0':
        variants.append(skeleton.synthesize(sk2, model.ops(), name=tag, parent=c))
    if extra.get('synth.unseeded', '1') != '0':
        variants += [skeleton.synthesize(sk2, model.ops(), name=tag, use_paar=up, paar_outputs=po)
                     for up, po in ((False, False), (True, False), (True, True))]
    if not variants:
        raise SystemExit('synth.seeded=0 and synth.unseeded=0: no rebuild variant')
    # by (feasible, cap excess, objective); the input is kept unless a variant is better (m1)
    caps = {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a}
    R = lambda x: objective.rank(objective.measure(x, model, caps), caps, args.objective)
    c2 = min(variants, key=R)
    if c2.value_table() != list(table):
        raise RuntimeError('synthesized circuit wrong (%s)' % tag)
    if not R(c2) < R(c):
        c2 = c
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
    caps = caps_of(args)
    R = lambda mt: objective.rank(mt, caps, args.objective)

    summary = {'command': ' '.join(['python3', 'nonlinear/boolflux/cli.py'] + sys.argv[1:]),
               'target': args.target, 'target_description': desc, 'model': model.name,
               'model_gates': model.gates, 'objective': args.objective,
               'caps': {'GD': args.cap_gd, 'AD': args.cap_ad, 'A': args.cap_a},
               'start': args.start, 'start_metrics': start.metrics(model), 'seeds': seeds,
               'iters': args.iters, 'skel_iters': args.skel_iters, 'rounds': args.rounds,
               'seed_scheme': seed_scheme(args, 'run'),
               'skel_share': args.skel_share, 'code_sha256_12': code_hash, 'code_snapshot': str(Path(args.out) / 'src'),
               'settings': {**DEFAULTS, **{'skel.' + k: v for k, v in SKEL_DEFAULTS.items()}, **extra},
               'runs': []}
    pool = [start]; t_all = time.time(); best = None; failures = []
    for rnd in range(args.rounds):
        def job(i_seed):
            i, seed = i_seed
            ks = kseed(args, seed, rnd)
            c0 = pool[i % len(pool)]
            tag = 'r%d-s%d' % (rnd, seed)
            use_skel = args.skel_share > 0 and ((i * 0.618034) % 1.0) < args.skel_share
            t0 = time.time()
            rec = {'round': rnd, 'seed': seed, 'kernel_seed': ks, 'tag': tag, 'skel': use_skel,
                   'from': objective.measure(c0, model, caps)}
            try:
                if use_skel:
                    c1, sklog = run_skel(c0, table, out, tag, ks, args, extra)
                    rec['synth'] = objective.measure(c1, model, caps)
                else:
                    c1 = c0
                c2, final, bests, moves = run_gate(c1, out, tag, ks, model, args, extra)
            except Exception as e:                 # recorded; the other jobs and earlier rounds survive (m7)
                rec.update({'core_ok': False, 'error': repr(e), 'wall_s': round(time.time() - t0, 2)})
                return rec, None
            c2.in_names = ['x%d' % k for k in range(n)]; c2.out_names = ['y%d' % k for k in range(m)]
            ok = verify_core(c2, table)
            mt = objective.measure(c2, model, caps)
            rec.update({'time_capped': final.get('iters', 0) < args.iters,
                        'core_ok': ok, 'metrics': mt, 'rank': R(mt), 'feasible': objective.feasible(mt, caps),
                        'final': final, 'improvements': bests, 'moves': moves,
                        'wall_s': round(time.time() - t0, 2)})
            return rec, c2
        order = list(enumerate(seeds))
        with ThreadPoolExecutor(max_workers=args.jobs or os.cpu_count()) as ex:
            res = list(ex.map(job, order))
        failures += [rec['tag'] for rec, c2 in res if not rec['core_ok']]
        # every verified job is a candidate, feasible or not: ranked by (feasible, excess, keys),
        # so a repair that has not met the caps yet carries its progress to the next round (M2)
        cands = [(rec['rank'], rec['seed'], rec, c2) for rec, c2 in res if rec['core_ok']]
        for pc in pool:     # the pool's circuits stay candidates (a job may not improve)
            mt = objective.measure(pc, model, caps)
            cands.append((R(mt), 10 ** 9, {'tag': 'pool', 'metrics': mt}, pc))
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
        if best is None:
            continue
        summary['wall_s'] = round(time.time() - t_all, 1)
        v, feas, bpath = write_best(out, best[3], model, args, desc, summary, 'from job %s' % best[2].get('tag'))
        bm = best[2]['metrics']
        print('round %d: best %s %s%s  (jobs: %s)' % (
            rnd, json.dumps({k: bm[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}), json.dumps(bm['counts']),
            '' if feas else ' CAPS NOT MET',
            ' '.join('%s:%s' % ('S' if r['skel'] else 'G', ('%g/%d' % (r['metrics']['cost'], r['metrics']['A'])) if r.get('metrics') else 'FAILED')
                     for r, _ in res)), flush=True)
    if best is None:
        raise SystemExit('every job failed (%s)' % ', '.join(failures))
    finish(v, feas, bpath, failures)


def _flow_job(job):
    run, bindir, wd, cpu = job
    if cpu is not None:
        os.sched_setaffinity(0, {cpu})
    try:
        r = workflow.search(run, bindir, wd, cpu)
    except Exception as e:
        return {'seed': run['seed'], 'error': repr(e)}
    c = r.pop('circuit')
    (Path(wd) / 'incumbent.bfx').write_text(core.to_kernel(c))
    r['seed'] = run['seed']
    return r


def cmd_flow(args):
    """The benchmark driver's time-sliced workflows (workflow.search), one process per seed."""
    import multiprocessing as mp
    bad = sorted(k.split('=', 1)[0] for k in (args.set or []) if k.startswith(('skel.', 'synth.')))
    if bad:        # review5 P7: these reached the gate kernel, which stopped every job with 'unknown key'
        raise SystemExit('flow: --set %s is a pipe setting; in flow use --skel-set KEY=VALUE and '
                         '--no-seeded / --no-unseeded' % ', '.join(bad))
    model = core.Model.load(args.model)
    n, m, table, desc = targets.load(args.target)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    code_hash = snapshot(out)
    start = make_start(args.target, args.start, model)
    caps = caps_of(args); seeds = parse_seeds(args.seeds)
    sp = out / 'start.bfx'; sp.write_text(core.to_kernel(start))
    base = {'target': args.target, 'model': args.model, 'objective': args.objective, 'caps': caps,
            'start': args.start, 'seconds': args.seconds,
            'config': args.config, 'round_s': args.round_s, 'adaptive': args.adaptive,
            'seeded': not args.no_seeded, 'unseeded': not args.no_unseeded,
            'set': parse_sets(args.set), 'skel_set': parse_sets(args.skel_set, kernel=False),
            'seed_scheme': seed_scheme(args, 'flow')}
    cpus = [int(x) for x in args.cpus.split(',')] if args.cpus else None
    jobs = [(dict(base, seed=sd), str(KBIN.parent), str(out / ('s%d' % sd)),
             cpus[i % len(cpus)] if cpus else None) for i, sd in enumerate(seeds)]
    summary = {'command': ' '.join(['python3', 'nonlinear/boolflux/cli.py'] + sys.argv[1:]),
               'target': args.target, 'target_description': desc, 'model': model.name,
               'objective': args.objective, 'caps': caps, 'start': args.start,
               'start_metrics': start.metrics(model), 'workflow': base, 'seeds': seeds,
               'code_sha256_12': code_hash, 'code_snapshot': str(out / 'src'), 'runs': []}
    t_all = time.time()
    width = args.jobs or (len(cpus) if cpus else os.cpu_count())
    with mp.get_context('fork').Pool(min(width, len(jobs))) as pool:
        res = pool.map(_flow_job, jobs, chunksize=1)
    failures = ['s%d' % r['seed'] for r in res if r.get('error')]
    ok = [r for r in res if not r.get('error')]
    for r in res:
        summary['runs'].append({k: v for k, v in r.items()})
    if not ok:
        raise SystemExit('every job failed: %s' % [r['error'] for r in res])
    R = lambda mt: objective.rank(mt, caps, args.objective)
    best = min(ok, key=lambda r: (R(r['metrics']), r['seed']))
    bc = core.from_kernel((out / ('s%d' % best['seed']) / 'incumbent.bfx').read_text())
    summary['wall_s'] = round(time.time() - t_all, 1)
    summary['success'] = '%d/%d feasible' % (sum(r['feasible'] for r in ok), len(seeds))
    v, feas, bpath = write_best(out, bc, model, args, desc, summary, 'seed %d' % best['seed'])
    for r in ok:
        print('seed %d: %s%s  (%d trajectory points, %.1f s)' % (
            r['seed'], json.dumps(r['metrics']), '' if r['feasible'] else ' CAPS NOT MET', len(r['trajectory']), r['search_s']))
    finish(v, feas, bpath, failures)


def cmd_verify(args):
    """Both verifiers on each file; with --cap-* the caps are checked too (by the independent
    verifier and here).  A kernel .bfx file is converted to NCFF in a temporary folder first."""
    import tempfile
    ok = True
    caps = caps_of(args)
    model = core.Model.load(args.model)
    with tempfile.TemporaryDirectory(prefix='boolflux-verify-') as tmp:
        for i, f in enumerate(args.files):
            try:
                path = Path(f)
                if path.suffix == '.bfx':
                    c = core.from_kernel(path.read_text(), name=path.stem)
                    path = Path(tmp) / ('%d-%s.circ.txt' % (i, path.stem))
                    path.write_text(core.write_ncff(c, model), encoding='utf-8')
                v = verify_file(path, args.target, args.model, caps)
            except (OSError, ValueError, KeyError) as e:       # unreadable or malformed: this file fails
                ok = False
                print('FAIL %s cannot be read as a circuit: %s' % (f, e))
                continue
            feas = objective.feasible(v['metrics'], caps)
            good = v['core_ok'] and v['independent_ok'] and v['library_ok'] and feas
            ok &= good
            print('%s %s %s core=%s indep=%s lib=%s%s' % ('ok  ' if good else 'FAIL', f,
                  json.dumps({k: v['metrics'].get(k) for k in ('cost', 'G', 'A', 'GD', 'AD', 'counts')}),
                  v['core_ok'], v['independent_ok'], v['library_ok'],
                  '' if all(x is None for x in caps.values()) else ' caps=%s' % ('met' if feas else 'NOT MET')))
            if not good:
                why = list(v['independent'].get('errors') or [])
                if v['independent'].get('error'): why.append(v['independent']['error'].strip()[-300:])
                if v['independent'].get('ok') and not v['metrics_agree']:
                    why.append('metrics differ: core %s, independent %s' % (
                        {k: v['metrics'].get(k) for k in ('G', 'A', 'GD', 'AD', 'counts')},
                        {k: (v['independent'].get('metrics') or {}).get(k) for k in ('G', 'A', 'GD', 'AD', 'counts')}))
                if not v['core_ok']: why.append('core: the circuit does not compute %s' % args.target)
                if not v['library_ok']: why.append('gates outside model %s' % args.model)
                print('     ' + '; '.join(why))
    sys.exit(0 if ok else 1)


def cmd_list(args):
    """Targets and stock models."""
    print('targets (--target):')
    for nm in targets.names():
        n, m, _, desc = targets.load(nm)
        print('  %-18s %2d -> %-2d %s' % (nm, n, m, desc))
    print('  map:<name>         linear map circuits/<name>/<name>.mat.txt')
    print('models (--model, or a path to a .json model file):')
    for f in sorted(core.MODELS.glob('*.json')):
        md = core.Model.load(f.stem)
        print('  %-6s %s' % (md.name, md.description))
    print('objective keys (--objective, lexicographic): %s' % ', '.join(objective.KEYS))


def check_target(name):
    """review5 P7: an unknown target used to end in a KeyError traceback."""
    try:
        targets.load(name)
    except (KeyError, OSError, ValueError, IndexError) as e:
        raise SystemExit('unknown or unreadable target %r (%s); targets: %s, or map:<name> for a linear map '
                         'of circuits/ (see `cli.py list`)' % (name, e, ', '.join(targets.names())))


def cmd_start(args):
    model = core.Model.load(args.model)
    c = make_start(args.target, args.start, model)
    Path(args.out).write_text(core.write_ncff(c, model, comments=['start: %s' % args.start]), encoding='utf-8')
    print(json.dumps(c.metrics(model)))


EPILOG = """\
Metrics: G = number of gates (NOT gates count too), A = nonlinear gates (#AND), GD = gate depth,
AD = AND depth, cost = sum of the model's gate costs (= G for the stock models).
Ranking: circuits that meet every cap first, then the smaller total cap excess, then the
--objective keys in order.  Exit status: 0 = a verified circuit within the caps was saved;
1 = verification failed, caps not met ("CAPS NOT MET"), or a job failed (the message says which).
Output belongs outside the repository, e.g. --out ~/xs-campaigns/DATE-NAME/RUN (runs/README.md).
OUT/best.circ.txt and OUT/summary.json are rewritten after every round."""


def _common(p, seeds, start=True):
    p.add_argument('--target', required=True, metavar='NAME',
                   help='function to implement: aes, aes-inv, an S-box of benchmarks/sboxes.json, map:<name>, ... '
                        '(`cli.py list` prints all)')
    p.add_argument('--model', required=True, metavar='NAME|FILE.json',
                   help='gate library and costs: nist, bgc, gc, gc6, xag, xor, or a model file')
    if start:
        p.add_argument('--start', default='anf', metavar='anf|FILE',
                       help="starting circuit: 'anf' (naive, built from the truth table) or an NCFF / NIST "
                            ".circ.txt file that computes the target with the model's gates (default: anf)")
    if seeds is not None:
        p.add_argument('--objective', default='cost', metavar='KEYS',
                       help='lexicographic objective, keys from cost, g, a, gd, ad; e.g. cost,gd or a,ad,cost '
                            '(default: cost)')
        p.add_argument('--cap-gd', type=int, metavar='N', help='hard cap on the gate depth (default: none)')
        p.add_argument('--cap-ad', type=int, metavar='N', help='hard cap on the AND depth (default: none)')
        p.add_argument('--cap-a', type=int, metavar='N', help='hard cap on the number of nonlinear gates (default: none)')
        p.add_argument('--seeds', default=seeds, metavar='LIST',
                       help='seeds, one job each: e.g. 1-8 or 1,3,5-7 (default: %(default)s)')
        p.add_argument('--seed-scheme', choices=['v2', 'legacy'], default='v2',
                       help='kernel seed of a job: v2 = seed + round x 2^32 (default; equals the seed in round 0); '
                            'legacy = the formula used before review 5 (run/pipe: seed + 1000 x round, flow: '
                            'seed x 1000 + round), to replay a command recorded with it')
        p.add_argument('--jobs', type=int, default=0, metavar='N',
                       help='jobs run at the same time (default 0: one per CPU)')
        p.add_argument('--out', required=True, metavar='DIR',
                       help='run folder (created): source snapshot, per-job files, best.circ.txt, summary.json')


def _positive(v):
    v = int(v)
    if v < 1: raise argparse.ArgumentTypeError('must be at least 1')
    return v


def build_parser():
    F = argparse.RawDescriptionHelpFormatter
    ap = argparse.ArgumentParser(
        prog='boolflux', formatter_class=F,
        description='BoolFlux: search for small Boolean circuits of a complete function, and verify them.\n'
                    '`boolflux CMD -h` lists the options of a command.', epilog=EPILOG)
    sub = ap.add_subparsers(dest='cmd', required=True, metavar='CMD')
    r = sub.add_parser('run', formatter_class=F, epilog=EPILOG,
                       help='gate kernel, one job per seed, in rounds of a fixed iteration count (deterministic)',
                       description='Gate-level search: every seed runs the gate kernel for --iters iterations from a '
                                   'circuit of the pool; the best --pool distinct results start the next round. '
                                   'Deterministic unless a job hits the --seconds safety cap.')
    _common(r, '1-8')
    r.add_argument('--iters', type=int, default=200000, metavar='N', help='kernel iterations per job and round (default: %(default)s)')
    r.add_argument('--seconds', type=float, default=3600, metavar='S',
                   help='safety cap per job; a job stopped by it makes the run non-deterministic (default: %(default)s)')
    r.add_argument('--rounds', type=_positive, default=1, metavar='N', help='number of rounds (default: %(default)s)')
    r.add_argument('--pool', type=int, default=4, metavar='N', help='distinct circuits carried to the next round (default: %(default)s)')
    r.add_argument('--set', action='append', metavar='KEY=VALUE',
                   help='gate-kernel setting, repeatable (e.g. mv.resub3=0, neutral=0, T0=0.3); costs, caps, '
                        'objective and run controls are refused here')
    r.set_defaults(func=cmd_run)
    p = sub.add_parser('pipe', formatter_class=F, epilog=EPILOG,
                       help='skeleton search + synthesis + gate search, in rounds',
                       description='A fraction --skel-share of the jobs first searches the AND skeleton of its start '
                                   '(skel kernel, --skel-iters) and rebuilds a circuit from it, then every job runs the '
                                   'gate kernel (--iters).  Iteration-based like `run`.')
    _common(p, '1-8')
    p.add_argument('--iters', type=int, default=100000, metavar='N', help='gate-kernel iterations per job and round (default: %(default)s)')
    p.add_argument('--skel-iters', type=int, default=20000, metavar='N',
                   help='skeleton-kernel iterations (0 = rebuild only) (default: %(default)s)')
    p.add_argument('--seconds', type=float, default=3600, metavar='S', help='safety cap per kernel process (default: %(default)s)')
    p.add_argument('--rounds', type=_positive, default=3, metavar='N', help='number of rounds (default: %(default)s)')
    p.add_argument('--pool', type=int, default=4, metavar='N', help='distinct circuits carried to the next round (default: %(default)s)')
    p.add_argument('--skel-share', type=float, default=0.5, metavar='X',
                   help='fraction of jobs that run the skeleton search first (default: %(default)s)')
    p.add_argument('--set', action='append', metavar='KEY=VALUE',
                   help='setting, repeatable: gate kernel KEY=VALUE, skeleton kernel skel.KEY=VALUE, '
                        'synth.seeded=0 / synth.unseeded=0 to drop rebuild variants')
    p.set_defaults(func=cmd_pipe)
    f = sub.add_parser('flow', formatter_class=F, epilog=EPILOG,
                       help='time-sliced workflows of the benchmark driver (gate / full / rebuild-only / adaptive)',
                       description='One search per seed with a wall-time budget (the loop of bench/bench.py, '
                                   'workflow.py): --config gate = one gate-kernel run; --config full = rounds of '
                                   'skeleton stage, rebuild and gate stage.  Time-budgeted, so not bit-reproducible.\n'
                                   'The benchmark configurations (bench/make_plan.py): "gate" = --config gate; "full" = '
                                   '--config full; "rebuild" = --config full --skel-set iters=0; the adaptive skeleton '
                                   'share of bench v3 = add --adaptive; repair under a cap = add --cap-gd N with a '
                                   'start outside the cap.')
    _common(f, '1-4')
    f.add_argument('--config', choices=['gate', 'full'], default='gate', help='workflow (default: %(default)s)')
    f.add_argument('--seconds', type=float, required=True, metavar='S', help='wall budget per seed, rebuild included')
    f.add_argument('--round-s', type=float, default=10.0, metavar='S', help='full: seconds per round (default: %(default)s)')
    f.add_argument('--adaptive', action='store_true', help='full: adaptive skeleton share (bench v3)')
    f.add_argument('--no-seeded', action='store_true', help='full: no rebuild seeded with the parent')
    f.add_argument('--no-unseeded', action='store_true', help='full: no rebuilds from forms only')
    f.add_argument('--skel-set', action='append', metavar='KEY=VALUE', help='skeleton kernel setting, repeatable (iters=0: rebuild only)')
    f.add_argument('--set', action='append', metavar='KEY=VALUE', help='gate kernel setting, repeatable')
    f.add_argument('--cpus', default='', metavar='LIST', help='pin seed i to CPU LIST[i %% len], like bench.py (default: not pinned)')
    f.set_defaults(func=cmd_flow)
    v = sub.add_parser('verify', formatter_class=F,
                       help='check circuit files with both verifiers (function, library, metrics, optional caps)',
                       description='Each FILE (NCFF / NIST .circ.txt, or kernel .bfx) is evaluated on every input by '
                                   'boolflux.core and by independent/verify.py; the gate library is the model\'s and '
                                   'the two metric sets (G, A, GD, AD, cost, counts) must agree.  Exit status 1 if any '
                                   'file fails.  For AES S-box circuits against the pinned NIST set use '
                                   'campaigns/aes_check.py.')
    v.add_argument('files', nargs='+', metavar='FILE')
    _common(v, None, start=False)
    v.add_argument('--cap-gd', type=int, metavar='N', help='fail a circuit whose gate depth exceeds N')
    v.add_argument('--cap-ad', type=int, metavar='N', help='fail a circuit whose AND depth exceeds N')
    v.add_argument('--cap-a', type=int, metavar='N', help='fail a circuit with more than N nonlinear gates')
    v.set_defaults(func=cmd_verify)
    st = sub.add_parser('start', formatter_class=F, help='write a starting circuit as NCFF and print its metrics',
                        description="Build the naive ANF circuit of the target (or re-write an existing circuit file) "
                                    "in the model's gates, check that it computes the target, and write it to --out.")
    _common(st, None)
    st.add_argument('--out', required=True, metavar='FILE', help='NCFF file to write')
    st.set_defaults(func=cmd_start)
    ls = sub.add_parser('list', help='list the targets, stock models and objective keys')
    ls.set_defaults(func=cmd_list)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    if getattr(a, 'target', None) is not None:
        check_target(a.target)
    if getattr(a, 'objective', None) is not None:
        objective.parse(a.objective)                  # a bad key stops here, before the source snapshot
    a.func(a)


if __name__ == '__main__':
    main()
