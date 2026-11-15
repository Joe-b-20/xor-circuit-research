"""Regression tests for the review-5 gate-kernel findings (nonlinear/boolflux/review5/KERNEL.md).

    python3 -m unittest nonlinear/boolflux/tests/test_review5_kernel.py     (from the repository root)

The tests drive the kernel binary directly with hand-written configs, so they do not depend on
cli.py / workflow.py.
"""
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))

from boolflux import core, starts, targets   # noqa: E402


def build():
    d = Path(tempfile.mkdtemp(prefix='bfx-r5-'))
    subprocess.run(['gcc', '-O2', '-o', str(d / 'bfx'), str(PKG / 'kernel' / 'bfx.c'), '-lm'], check=True)
    return d / 'bfx'


BIN = build()
NIST = REPO / 'nonlinear' / 'nist' / 'aes-sbox'
BASE = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
        'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
        'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
NIST_LIB = {'cost.8': 1, 'cost.6': 1, 'cost.9': 1, 'cost.3': 1}
BGC_LIB = {'cost.8': 1, 'cost.14': 1, 'cost.6': 1, 'cost.3': 1}
LEX_A = {'lex': 'a,ad,cost,gd', 'w.a': 1, 'w.ad': 1e-4, 'w.cost': 1e-8, 'w.gd': 1e-12}
LEX_COST = {'lex': 'cost,gd', 'w.cost': 1, 'w.gd': 1e-4}


def present_start():
    n, m, tab, _ = targets.load('present')
    return core.to_kernel(starts.anf(n, m, tab, [8, 14, 6, 3]))


def aes(name):
    return core.to_kernel(core.read_ncff(str(NIST / name)))


def run(circuit_text, settings, raw_cfg=None, d=None):
    """Run the kernel; returns (returncode, stdout, stderr, workdir)."""
    d = Path(d or tempfile.mkdtemp(prefix='r5k-'))
    (d / 'in.bfx').write_text(circuit_text)
    if raw_cfg is None:
        cfg = {'in': d / 'in.bfx', 'out': d / 'out.bfx', 'seed': 1, 'seconds': 600}
        cfg.update(settings)
        raw_cfg = ''.join('%s %s\n' % kv for kv in cfg.items())
    (d / 'k.cfg').write_text(raw_cfg)
    r = subprocess.run([str(BIN), str(d / 'k.cfg')], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr, d


def final(log):
    ln = [x for x in log.splitlines() if x.startswith('final ')][-1].split()
    return {ln[i]: float(ln[i + 1]) for i in range(1, len(ln) - 1, 2)}


def trajectory(log, d):
    """Everything the kernel reports except wall-clock fields, plus the result circuit."""
    t = re.sub(r' (t|seconds|time) [0-9.]+', '', log)
    out = '\n'.join(x for x in (d / 'out.bfx').read_text().splitlines() if not x.startswith('#'))
    return hashlib.md5((t + out).encode()).hexdigest()[:12]


def check_same_function(test, a_text, b_text):
    a, b = core.from_kernel(a_text), core.from_kernel(b_text)
    test.assertEqual(a.value_table(), b.value_table())


class TestConfigParsing(unittest.TestCase):
    """K1: config reader."""

    def test_one_word_comment_does_not_eat_next_line(self):
        d = Path(tempfile.mkdtemp(prefix='r5k-'))
        cfg = ('#note\niters 0\n# two words\n\nin %s\nout %s\nseed 1\nseconds 0.3\ncost.8 1\ncost.14 1\ncost.6 1\ncost.3 1\n'
               % (d / 'in.bfx', d / 'out.bfx'))
        rc, out, err, _ = run(present_start(), None, cfg, d)
        self.assertEqual(rc, 0, err)
        self.assertEqual(final(out)['iters'], 0)       # the old reader dropped `iters 0` and searched for 0.3 s

    def test_bad_op_number_rejected(self):
        for key in ('cost.99', 'cost.-1', 'cost.8x', 'gdw.16'):
            s = dict(BASE); s.update(BGC_LIB); s.update({key: 1, 'iters': 10})
            rc, out, err, _ = run(present_start(), s)
            self.assertEqual(rc, 2, key)
            self.assertIn('bad op number', err)

    def test_unknown_move_and_missing_value_rejected(self):
        s = dict(BASE); s.update(BGC_LIB); s.update({'mv.resub9': 1, 'iters': 10})
        rc, out, err, _ = run(present_start(), s)
        self.assertEqual(rc, 2); self.assertIn('unknown move', err)
        rc, out, err, _ = run(present_start(), None, 'iters\n')
        self.assertEqual(rc, 2); self.assertIn('no value', err)

    def test_path_with_space(self):
        d = Path(tempfile.mkdtemp(prefix='r5k sp-'))
        s = dict(BASE); s.update(BGC_LIB); s.update(LEX_COST)
        s.update({'in': d / 'in.bfx', 'out': d / 'out file.bfx', 'seed': 1, 'seconds': 600, 'iters': 200})
        rc, out, err, _ = run(present_start(), None, ''.join('%s %s\n' % kv for kv in s.items()), d)
        self.assertEqual(rc, 0, err)
        check_same_function(self, present_start(), (d / 'out file.bfx').read_text())

    def test_stats_without_file(self):
        r = subprocess.run([str(BIN), '--stats'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)             # was a NULL strcpy (segfault)

    def test_cand_cap_bounds(self):
        s = dict(BASE); s.update(BGC_LIB); s.update(LEX_COST); s.update({'cand_cap': 0, 'iters': 10})
        self.assertEqual(run(present_start(), s)[0], 2)
        # K2: more than 1024 kept candidates are all evaluated (was: silently only the first 1024)
        s.update({'cand_cap': 5000, 'iters': 300})
        rc, out, err, d = run(present_start(), s)
        self.assertEqual(rc, 0, err)
        check_same_function(self, present_start(), (d / 'out.bfx').read_text())


class TestTraceAndEdges(unittest.TestCase):
    def test_trace_costs_exact(self):
        """K3: trace / tracemoves costs are printed exactly (were %.4f / %.2f)."""
        d = Path(tempfile.mkdtemp(prefix='r5k-'))
        s = dict(BASE); s.update(LEX_COST)
        s.update({'cost.8': 1.5, 'cost.6': 0.123456789, 'cost.3': 0.123456789, 'iters': 1500,
                  'trace': d / 'tr.txt', 'tracemoves': d / 'mv.txt'})
        n, m, tab, _ = targets.load('present')
        rc, out, err, _ = run(core.to_kernel(starts.anf(n, m, tab, [8, 6, 3])), s, d=d)
        self.assertEqual(rc, 0, err)
        rows = [x.split() for x in (d / 'tr.txt').read_text().splitlines()]
        self.assertTrue(rows)
        for r in rows:
            cost, g, a = float(r[3]), int(r[4]), int(r[5])
            self.assertAlmostEqual(cost, 1.5 * a + 0.123456789 * (g - a), delta=1e-7)
        for ln in (d / 'mv.txt').read_text().splitlines():
            mm = re.search(r'after cost (\S+) G (\d+) A (\d+)', ln)
            self.assertAlmostEqual(float(mm.group(1)), 1.5 * int(mm.group(3)) + 0.123456789 * (int(mm.group(2)) - int(mm.group(3))), delta=1e-7)

    def test_degenerate_circuits(self):
        """Empty circuit, outputs that are inputs / repeated, a single NOT: the kernel must end cleanly."""
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s['iters'] = 200
        for text, g in (('n 3\nm 2\ng 0\no 0 2\n', 0),
                        ('n 2\nm 3\ng 1\n3 0 0\no 2 2 1\n', 1),
                        ('n 2\nm 2\ng 3\n6 0 1\n6 2 1\n8 0 1\no 3 4\n', 1)):      # (x^y)^y = x
            rc, out, err, d = run(text, s)
            self.assertEqual(rc, 0, err)
            self.assertEqual(final(out)['G'], g)
            check_same_function(self, text, (d / 'out.bfx').read_text())
        rc, out, err, d = run('n 2\nm 1\ng -1\no 0\n', s)
        self.assertEqual(rc, 2)


if __name__ == '__main__':
    unittest.main()
