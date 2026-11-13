"""What the full configuration's skeleton slice does on the AES benchmark starts.

Runs the skeleton kernel exactly as bench.py does (cli.SKEL_DEFAULTS, cap.ad from the caps,
seconds = round_s * 0.2 = 6 s, no emit_current) and reports whether the returned skeleton differs
from the input, and the variants bench.py would build (seeded + 3 unseeded) with their cost,
GD/AD and cap feasibility, and which one bench.py's min-by-cost rule picks.
    taskset -c 16 python3 test_fullconfig.py
"""
import json
from concurrent.futures import ThreadPoolExecutor

from common import BIN, TMP, REPO, cli, core, skeleton, targets, write_cfg, run_pinned

NIST = REPO / 'nonlinear' / 'nist' / 'aes-sbox'
CASES = [('a36g142', NIST / 'aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt', {'A': 36, 'AD': 4, 'GD': 13}),
         ('g104', NIST / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt', {}),
         ('gd14repair', NIST / 'aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt', {'GD': 14})]
CPUS = [17, 18, 19]


def job(arg):
    (name, path, caps), seed, cpu = arg
    model = core.Model.load('nist'); n, m, table, _ = targets.load('aes')
    c = core.read_ncff(str(path)); sk = skeleton.extract(c)
    d = TMP / 'full' / ('%s-%d' % (name, seed)); d.mkdir(parents=True, exist_ok=True)
    (d / 'sk.in').write_text(skeleton.write_skel(sk, core.tables_from_values(n, m, table)))
    cfg = dict(cli.SKEL_DEFAULTS)
    if caps.get('AD') is not None: cfg['cap.ad'] = caps['AD']
    cfg.update({'in': d / 'sk.in', 'out': d / 'sk.out', 'seed': seed * 1000, 'iters': 10 ** 15, 'seconds': 6.0})
    write_cfg(d / 'sk.cfg', cfg)
    r = run_pinned([BIN / 'skel', d / 'sk.cfg'], cpu)
    sk2 = skeleton.read_skel((d / 'sk.out').read_text())
    same = sk2['ands'] == sk['ands']
    acc = sum(int(l.split()[5]) for l in r.stdout.splitlines() if l.startswith('move '))
    vs = [('seeded', skeleton.synthesize(sk2, model.ops(), parent=c))]
    vs += [('unseeded%d%d' % ab, skeleton.synthesize(sk2, model.ops(), use_paar=ab[0], paar_outputs=ab[1])) for ab in ((0, 0), (1, 0), (1, 1))]
    feas = lambda mt: all(cp is None or mt[k] <= cp for k, cp in caps.items())
    info = []
    for vn, v in vs:
        mt = v.metrics(model); info.append((vn, mt['G'], mt['GD'], mt['AD'], feas(mt)))
    pick = min(vs, key=lambda x: x[1].metrics(model)['cost'])[0]
    return {'case': name, 'seed': seed, 'K_in': len(sk['ands']), 'K_out': len(sk2['ands']), 'skeleton_unchanged': same,
            'accepted_moves': acc, 'parent_G': len(c.gates), 'variants': info, 'bench_pick': pick,
            'final_line': [l for l in r.stdout.splitlines() if l.startswith('final')]}


def main():
    jobs = [(cse, s) for cse in CASES for s in (1, 2, 3, 4)]
    jobs = [(a, s, CPUS[i % 3]) for i, (a, s) in enumerate(jobs)]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(job, jobs): print(json.dumps(r))


if __name__ == '__main__':
    main()
