"""Old kernel (9f4c8df) vs new kernel (ccb323f): are defaults unchanged, does tracemoves perturb?

For each case and seed, with an iteration budget (iteration-based schedules from cli.DEFAULTS):
  old            = bin/bfx_old (kernel before 3a71f0f)
  new_sn0        = bin/bfx_new with skip_noop 0
  new_sn0_trace  = bin/bfx_new with skip_noop 0 and tracemoves
  new_default    = bin/bfx_new as shipped (skip_noop 1 by default)
Compares the timing-free stdout and the output circuit byte for byte.
    taskset -c 16-19 python3 test_defaults.py
"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import BIN, CPUS, TMP, REPO, core, starts, targets, base_cfg, write_cfg, run_pinned, strip_times

NIST = REPO / 'nonlinear' / 'nist' / 'aes-sbox'
CASES = [
    ('aes142', 'aes', 'nist', 'cost,gd', {'A': 36, 'AD': 4, 'GD': 13}, NIST / 'aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt', 20000),
    ('aes104', 'aes', 'nist', 'cost,gd', {}, NIST / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt', 20000),
    ('aesgd14', 'aes', 'nist', 'cost,gd', {'GD': 14}, NIST / 'aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt', 20000),
    ('present', 'present', 'bgc', 'cost', {}, 'anf', 20000),
    ('ascon-gc', 'ascon', 'gc', 'cost', {}, 'anf', 15000),
    ('gf16mul', 'gf16-mul', 'xag', 'a,cost', {}, 'anf', 10000),
    ('maj3', 'maj3', 'xag', 'a,cost', {}, 'anf', 3000),
    ('joltik-xor', 'map:joltik', 'xor', 'cost,gd', {'GD': 4}, 'anf', 5000),
]


def one(job):
    (name, tgt, model_name, obj, caps, st, iters), seed, cpu = job
    model = core.Model.load(model_name)
    n, m, table, _ = targets.load(tgt)
    c = starts.anf(n, m, table, model.ops()) if st == 'anf' else core.read_ncff(str(st))
    d = TMP / 'defaults' / ('%s-s%d' % (name, seed)); d.mkdir(parents=True, exist_ok=True)
    (d / 'start.bfx').write_text(core.to_kernel(c))
    res = {}
    for var, binname, extra in (('old', 'bfx_old', {}), ('new_sn0', 'bfx_new', {'skip_noop': 0}),
                                ('new_sn0_trace', 'bfx_new', {'skip_noop': 0, 'tracemoves': d / 'moves.txt'}),
                                ('new_default', 'bfx_new', {})):
        cfg = base_cfg(model, obj, caps); cfg.update(extra)
        cfg.update({'in': d / 'start.bfx', 'out': d / (var + '.out'), 'seed': seed, 'seconds': 1e9, 'iters': iters})
        write_cfg(d / (var + '.cfg'), cfg)
        r = run_pinned([BIN / binname, d / (var + '.cfg')], cpu)
        log = '\n'.join(l for l in strip_times(r.stdout).splitlines() if not l.startswith('noop_candidates'))
        res[var] = {'rc': r.returncode, 'log': log, 'circ': (d / (var + '.out')).read_text() if r.returncode == 0 else None,
                    'final': [l for l in r.stdout.splitlines() if l.startswith('final')]}
    o = res['old']
    return {'case': name, 'seed': seed,
            'rc': {k: v['rc'] for k, v in res.items()},
            'old==new_sn0': o['log'] == res['new_sn0']['log'] and o['circ'] == res['new_sn0']['circ'],
            'new_sn0==new_sn0_trace': res['new_sn0']['log'] == res['new_sn0_trace']['log'] and res['new_sn0']['circ'] == res['new_sn0_trace']['circ'],
            'old==new_default': o['log'] == res['new_default']['log'] and o['circ'] == res['new_default']['circ'],
            'final_old': o['final'], 'final_default': res['new_default']['final']}


def main():
    jobs = [(c, s) for c in CASES for s in (1, 2, 3)]
    jobs = [(c, s, CPUS[i % len(CPUS)]) for i, (c, s) in enumerate(jobs)]
    with ThreadPoolExecutor(max_workers=len(CPUS)) as ex:
        out = list(ex.map(one, jobs))
    for r in out: print(json.dumps(r))
    (TMP / 'test_defaults.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
