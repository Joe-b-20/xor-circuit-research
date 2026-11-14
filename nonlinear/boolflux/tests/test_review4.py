"""Regression tests for the review-4 findings (nonlinear/boolflux/review4/REVIEW4.md).

    python3 -m unittest nonlinear/boolflux/tests/test_review4.py        (from the repository root; ~1 min)
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))

from boolflux import core, starts, targets, workflow   # noqa: E402

CLI = [sys.executable, str(PKG / 'cli.py')]


def run_cli(*args):
    return subprocess.run(CLI + list(args), capture_output=True, text=True, cwd=str(REPO))


def model_file(gates, name='m', not_as=None):
    d = Path(tempfile.mkdtemp(prefix='r4m-'))
    m = {'name': name, 'gates': gates}
    if not_as: m['not_as'] = not_as
    (d / (name + '.json')).write_text(json.dumps(m))
    return str(d / (name + '.json'))


class TestCostScale(unittest.TestCase):
    """M1: T0 / uphill / max_excess are in units of one gate, so scaling every cost by 10 must not
    turn the kernel into pure descent."""

    def test_bgc_times_ten_reaches_14(self):
        m10 = model_file({'AND': 10, 'OR': 10, 'XOR': 10, 'NOT': 10}, 'bgc10')
        out = Path(tempfile.mkdtemp(prefix='r4s-'))
        r = run_cli('run', '--target', 'present', '--model', m10, '--iters', '20000', '--seeds', '1-4',
                    '--jobs', '4', '--out', str(out))
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        s = json.loads((out / 'summary.json').read_text())
        self.assertIn('scale unit 10', (out / 'r0-s1.log').read_text())
        Gs = sorted(x['metrics']['G'] for x in s['runs'])
        self.assertLessEqual(Gs[1], 15, Gs)       # bgc unit costs: 14 on all four seeds; descent only: 14-18


class TestSetGuard(unittest.TestCase):
    """M2: --set may not change costs, depth weights, caps, objective or weights."""

    def test_forbidden_keys(self):
        out = Path(tempfile.mkdtemp())
        for key in ('cost.8=5', 'gdw.3=0', 'cap.gd=3', 'lex=g', 'w.cost=2'):
            r = run_cli('run', '--target', 'maj3', '--model', 'xag', '--iters', '10', '--seeds', '1',
                        '--out', str(out / key.split('=')[0]), '--set', key)
            self.assertNotEqual(r.returncode, 0, key)
            self.assertIn('not allowed', r.stderr + r.stdout, key)

    def test_allowed_keys_still_work(self):
        out = Path(tempfile.mkdtemp())
        r = run_cli('run', '--target', 'maj3', '--model', 'xag', '--iters', '200', '--seeds', '1',
                    '--out', str(out), '--set', 'mv.resub3=0', '--set', 'skip_noop=0')
        self.assertEqual(r.returncode, 0, r.stderr[-800:])

    def test_run_never_worse_than_start(self):
        # the start is a candidate: with 0 iterations the result must equal the (cleaned) start
        model = core.Model.load('bgc')
        n, m, tab, _ = targets.load('present')
        st = starts.anf(n, m, tab, model.ops())
        f = Path(tempfile.mkdtemp()) / 'st.circ.txt'; f.write_text(core.write_ncff(st, model))
        out = Path(tempfile.mkdtemp())
        r = run_cli('run', '--target', 'present', '--model', 'bgc', '--start', str(f), '--iters', '0',
                    '--seeds', '1-2', '--out', str(out))
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        s = json.loads((out / 'summary.json').read_text())
        self.assertLessEqual(s['best']['metrics']['cost'], st.metrics(model)['cost'])


class TestModels(unittest.TestCase):
    """m2: model validation."""

    def test_not_xnor_cost_mismatch_rejected(self):
        p = model_file({'AND': 1, 'XOR': 1, 'XNOR': 1, 'NOT': 2}, 'bad', not_as='XNOR0')
        with self.assertRaises(SystemExit):
            core.Model.load(p)

    def test_bad_costs_rejected(self):
        for gates in ({'AND': -1, 'XOR': 1}, {'AND': float('nan'), 'XOR': 1}, {'AND': 1, 'FOO': 1}):
            with self.assertRaises(SystemExit):
                core.Model.load(model_file(gates, 'bad'))

    def test_stock_models_load(self):
        for f in sorted((PKG / 'models').glob('*.json')):
            core.Model.load(f.stem)


class TestExactCosts(unittest.TestCase):
    """m3: kernel prints costs exactly (fractional costs survive the log)."""

    def test_fractional_cost_in_log(self):
        p = model_file({'AND': 1.37, 'XOR': 0.31, 'NOT': 0.07}, 'frac')
        out = Path(tempfile.mkdtemp())
        r = run_cli('run', '--target', 'maj3', '--model', p, '--iters', '300', '--seeds', '1', '--out', str(out))
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        s = json.loads((out / 'summary.json').read_text())
        log = (out / 'r0-s1.log').read_text()
        final = [l for l in log.splitlines() if l.startswith('final')][0]
        self.assertAlmostEqual(float(final.split()[2]), s['best']['metrics']['cost'], places=9)


if __name__ == '__main__':
    unittest.main()
