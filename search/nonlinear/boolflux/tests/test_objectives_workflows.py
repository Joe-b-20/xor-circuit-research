"""Objectives and workflows: lexicographic ranking, incumbents kept across rounds and stages, move and
start accounting.

    python3 -m unittest search/nonlinear/boolflux/tests/test_objectives_workflows.py   (from the repository root; ~2 min)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))

from boolflux import core, objective, starts, targets, workflow   # noqa: E402
import cli                                                          # noqa: E402

NIST = PKG.parent / 'seeds'
CLI = [sys.executable, str(PKG / 'cli.py')]
A116 = NIST / 'aes-sbox' / 'aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt'


def kernel():
    d = Path(tempfile.mkdtemp(prefix='bft-k-'))
    for b in ('bfx', 'skel'):
        subprocess.run(['gcc', '-O2', '-o', str(d / b), str(PKG / 'kernel' / (b + '.c')), '-lm'], check=True)
    return d


BIN = kernel()


def run_cli(*args, ok=True):
    r = subprocess.run(CLI + list(args), capture_output=True, text=True, cwd=str(REPO))
    if ok and r.returncode != 0:
        raise AssertionError('cli failed (%d): %s' % (r.returncode, (r.stdout + r.stderr)[-1500:]))
    return r


def kernel_run(start, model, objective_spec, iters, extra=None, caps=None, seed=1):
    d = Path(tempfile.mkdtemp(prefix='bft-r-'))
    (d / 'in.bfx').write_text(core.to_kernel(start))
    run = {'objective': objective_spec, 'caps': caps or {}}
    workflow.kernel_cfg(d / 'k.cfg', d / 'in.bfx', d / 'out.bfx', model, run, 600, seed, extra or {}, iters=iters)
    r = subprocess.run([str(BIN / 'bfx'), str(d / 'k.cfg')], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return d, r.stdout


class TestObjectives(unittest.TestCase):
    """Lexicographic ranking, feasibility first, exact printing."""

    def test_rank_lexicographic_third_key(self):
        a = {'cost': 17, 'G': 17, 'A': 4, 'GD': 6, 'AD': 2}
        b = dict(a, cost=18, G=18)
        self.assertLess(objective.rank(a, {}, 'a,gd,cost'), objective.rank(b, {}, 'a,gd,cost'))
        # far more keys than weights could separate: still exact
        c = dict(a, AD=3)
        self.assertLess(objective.rank(a, {}, 'a,gd,cost,g,ad'), objective.rank(c, {}, 'a,gd,cost,g,ad'))

    def test_rank_feasibility_then_excess(self):
        caps = {'GD': 5}
        x = {'cost': 32, 'G': 32, 'A': 4, 'GD': 6, 'AD': 2}   # excess 1
        y = {'cost': 25, 'G': 25, 'A': 4, 'GD': 9, 'AD': 2}   # excess 4, cheaper
        z = {'cost': 40, 'G': 40, 'A': 4, 'GD': 5, 'AD': 2}   # feasible, dearest
        order = sorted([y, x, z], key=lambda m: objective.rank(m, caps, 'cost'))
        self.assertEqual(order, [z, x, y])

    def test_kernel_lex_config_and_exact_obj(self):
        model = core.Model.load('bgc')
        n, m, tab, _ = targets.load('present')
        d, log = kernel_run(starts.anf(n, m, tab, model.ops()), model, 'a,gd,cost', 2000)
        self.assertIn('lex a,gd,cost', (d / 'k.cfg').read_text())
        final, _, _ = cli.parse_kernel_log(log)
        mt = core.from_kernel((d / 'out.bfx').read_text()).metrics(model)
        # obj printed with full precision: the third key is visible
        self.assertAlmostEqual(final['obj'], mt['A'] + 1e-4 * mt['GD'] + 1e-8 * mt['cost'], places=12)

    def test_kernel_unknown_lex_key(self):
        model = core.Model.load('xag')
        n, m, tab, _ = targets.load('maj3')
        d = Path(tempfile.mkdtemp())
        (d / 'in.bfx').write_text(core.to_kernel(starts.anf(n, m, tab, model.ops())))
        workflow.kernel_cfg(d / 'k.cfg', d / 'in.bfx', d / 'o.bfx', model, {'objective': 'cost'}, 1, 1, {}, iters=1)
        with open(d / 'k.cfg', 'a') as f: f.write('lex cost,depth\n')   # not settable through --set
        r = subprocess.run([str(BIN / 'bfx'), str(d / 'k.cfg')], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_run_picks_lexicographic_best_job(self):
        out = Path(tempfile.mkdtemp(prefix='bft-m1-'))
        run_cli('run', '--target', 'present', '--model', 'bgc', '--objective', 'a,gd,cost', '--iters', '3000',
                '--seeds', '1-8', '--jobs', '2', '--out', str(out))
        s = json.loads((out / 'summary.json').read_text())
        R = lambda mt: objective.rank(mt, {}, 'a,gd,cost')
        best_job = min(R(r['metrics']) for r in s['runs'])
        self.assertEqual(R(s['best']['metrics']), best_job)


class TestIncumbents(unittest.TestCase):
    """Repair progress, variant choice, rebuild candidates, per-round saves."""

    def test_pipe_repairs_across_rounds(self):
        out = Path(tempfile.mkdtemp(prefix='bft-m2-'))
        r = run_cli('pipe', '--target', 'aes', '--model', 'nist', '--start', str(A116), '--cap-gd', '14',
                    '--objective', 'cost,gd', '--iters', '1500', '--seeds', '1-2', '--rounds', '2',
                    '--skel-share', '0', '--jobs', '2', '--out', str(out), ok=False)
        self.assertNotIn('Traceback', r.stdout + r.stderr)
        s = json.loads((out / 'summary.json').read_text())
        caps = {'GD': 14}
        R = lambda mt: objective.rank(mt, caps, 'cost,gd')
        r0 = [x for x in s['runs'] if x['round'] == 0]
        r1 = [x for x in s['runs'] if x['round'] == 1]
        self.assertTrue(r1, 'round 1 ran')
        start = objective.measure(core.read_ncff(str(A116)), core.Model.load('nist'), caps)
        best0 = min(R(x['metrics']) for x in r0)
        self.assertLess(best0, R(start))                       # round 0 made repair progress
        for x in r1:                                            # and round 1 starts from it
            self.assertLessEqual(R(x['from']), R(start))
            self.assertNotEqual(R(x['from']), R(start))
        self.assertTrue((out / 'best.circ.txt').exists())

    def test_pipe_variant_respects_caps(self):
        out = Path(tempfile.mkdtemp(prefix='bft-v-'))
        run_cli('pipe', '--target', 'gf16-mul', '--model', 'xag', '--objective', 'cost', '--cap-gd', '4',
                '--iters', '2000', '--skel-iters', '2000', '--seeds', '1-2', '--rounds', '1', '--skel-share', '1',
                '--jobs', '2', '--out', str(out), ok=False)
        s = json.loads((out / 'summary.json').read_text())
        for x in s['runs']:
            if x.get('synth') and x['from']['GD'] <= 4:
                self.assertLessEqual(x['synth']['GD'], 4, 'a feasible input is not replaced by an infeasible rebuild')

    def test_skel_set_iters_wins(self):
        out = Path(tempfile.mkdtemp(prefix='bft-s-'))
        run_cli('pipe', '--target', 'maj3', '--model', 'xag', '--iters', '200', '--skel-iters', '5000',
                '--seeds', '1', '--rounds', '1', '--skel-share', '1', '--set', 'skel.iters=0', '--jobs', '1', '--out', str(out))
        cfg = (out / 'r0-s1.skcfg').read_text().split('\n')
        self.assertIn('iters 0', cfg)

    def test_workflow_trajectory_has_every_feasible_incumbent(self):
        # GF(2^4) multiplication, full config, unseeded rebuilds only (a rebuild-stage gain must be in the trajectory)
        wd = Path(tempfile.mkdtemp(prefix='bft-w-'))
        for seed in (2, 3):
            run = {'target': 'gf16-mul', 'model': 'xag', 'objective': 'a,cost', 'caps': {}, 'start': 'anf',
                   'seconds': 6, 'seed': seed, 'config': 'full', 'seeded': False, 'unseeded': True, 'round_s': 2}
            r = workflow.search(run, BIN, wd / str(seed))
            last = r['trajectory'][-1]
            self.assertEqual((last[1], last[3]), (r['metrics']['cost'], r['metrics']['A']))

    def test_flow_rebuild_repair(self):
        out = Path(tempfile.mkdtemp(prefix='bft-f-'))
        r = run_cli('flow', '--target', 'aes', '--model', 'nist', '--start', str(A116), '--cap-gd', '14',
                    '--objective', 'cost,gd', '--config', 'full', '--skel-set', 'iters=0', '--adaptive',
                    '--seconds', '8', '--round-s', '4', '--seeds', '1-2', '--jobs', '2', '--out', str(out), ok=False)
        self.assertNotIn('Traceback', r.stdout + r.stderr)
        s = json.loads((out / 'summary.json').read_text())
        self.assertEqual(len(s['runs']), 2)
        caps = {'GD': 14}
        R = lambda mt: objective.rank(mt, caps, 'cost,gd')
        start = objective.measure(core.read_ncff(str(A116)), core.Model.load('nist'), caps)
        for x in s['runs']:
            self.assertLess(R(x['metrics']), R(start))            # repair progress is the incumbent
        self.assertIn('rounds', s['runs'][0])


class TestAccounting(unittest.TestCase):
    """No-op moves, BUF lines, start clean-up, trace files, model names."""

    def test_noop_filter_structural(self):
        model = core.Model.load('bgc')
        n, m, tab, _ = targets.load('present')
        d, log = kernel_run(starts.anf(n, m, tab, model.ops()), model, 'cost', 2000, {'skip_noop': 1})
        d0, log0 = kernel_run(starts.anf(n, m, tab, model.ops()), model, 'cost', 2000, {'skip_noop': 0})
        skipped = int(log.split('noop_candidates_skipped')[1].split()[0])
        self.assertGreater(skipped, 1000)        # the memcmp filter skipped ~5,700 of ~2,600+ no-op accepts
        self.assertIn('final', log); self.assertIn('final', log0)

    def test_buf_outputs_verify(self):
        out = Path(tempfile.mkdtemp(prefix='bft-b-'))
        run_cli('run', '--target', 'map:skinny', '--model', 'xor', '--iters', '3000', '--seeds', '1',
                '--jobs', '1', '--out', str(out))
        s = json.loads((out / 'summary.json').read_text())
        self.assertTrue(s['best']['independent_ok'])
        self.assertGreater(s['best']['buf_lines'], 0)

    def test_start_cleanup_logged(self):
        model = core.Model.load('nist')
        n, m, tab, _ = targets.load('aes')
        st = starts.anf(n, m, tab, model.ops())
        d, log = kernel_run(st, model, 'cost', 0)
        line = [l for l in log.splitlines() if l.startswith('start_cleanup')]
        self.assertTrue(line)
        self.assertIn('G %d ' % len(st.gates), line[0] + ' ')

    def test_trace_before_metrics(self):
        model = core.Model.load('xag')
        n, m, tab, _ = targets.load('maj3')
        st = starts.anf(n, m, tab, model.ops())
        d = Path(tempfile.mkdtemp(prefix='bft-t-'))
        _, log = kernel_run(st, model, 'a,cost', 400, {'tracemoves': str(d / 'mv.txt'), 'skip_noop': 0})
        befores = sorted(d.glob('mv.txt.it*.before'))
        self.assertTrue(befores)
        for f in befores:
            head = [l for l in f.read_text().splitlines() if l.startswith('#')]
            self.assertNotIn('cost 0 G 0', ' '.join(head))

    def test_model_name_not_shadowed_by_cwd(self):
        old = os.getcwd()
        try:
            d = tempfile.mkdtemp(); os.mkdir(os.path.join(d, 'nist'))
            os.chdir(d)                                 # contains a directory named nist
            self.assertEqual(core.Model.load('nist').name, 'nist')
        finally:
            os.chdir(old)


if __name__ == '__main__':
    unittest.main()
