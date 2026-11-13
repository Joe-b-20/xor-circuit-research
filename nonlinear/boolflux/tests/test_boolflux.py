"""Tests for the BoolFlux Python side and a short deterministic kernel run.

    python3 -m unittest discover -s nonlinear/boolflux/tests -t nonlinear
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
sys.path.insert(0, str(PKG.parent))

from boolflux import core, skeleton, starts, targets   # noqa: E402

NIST = REPO / 'nonlinear' / 'nist'


class TestCore(unittest.TestCase):
    def test_aes_table(self):
        s = targets.aes_sbox()
        self.assertEqual((s[0], s[1], s[0x53]), (0x63, 0x7c, 0xed))
        inv = targets.aes_inv_sbox()
        self.assertTrue(all(inv[s[x]] == x for x in range(256)))

    def test_nist_read_eval(self):
        tab = targets.aes_sbox()
        for f in sorted((NIST / 'aes-sbox').glob('*.circ.txt'))[:12]:
            c = core.read_ncff(str(f))
            self.assertEqual(c.value_table(), tab, f.name)

    def test_ncff_roundtrip(self):
        model = core.Model.load('nist')
        f = NIST / 'aes-sbox' / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'
        c = core.read_ncff(str(f))
        m0 = c.metrics(model)
        text = core.write_ncff(c, model)
        c2 = core.read_ncff(text)
        self.assertEqual(c2.value_table(), targets.aes_sbox())
        m2 = c2.metrics(model)
        for k in ('G', 'A', 'GD', 'AD', 'cost'):
            self.assertEqual(m0[k], m2[k], k)
        self.assertEqual((m0['G'], m0['A'], m0['GD'], m0['AD']), (104, 32, 30, 5))

    def test_kernel_format_roundtrip(self):
        c = starts.anf(4, 4, targets.load('present')[2])
        self.assertEqual(core.from_kernel(core.to_kernel(c)).value_table(), c.value_table())

    def test_all_ops(self):
        ones = (1 << 4) - 1
        a, b = 0b1100, 0b1010     # truth tables over (a,b) patterns 0..3 (bit index = 2a+b ... reversed)
        for op in range(16):
            r = core.op_apply(op, a, b, ones)
            for x in range(4):
                av, bv = (a >> x) & 1, (b >> x) & 1
                self.assertEqual((r >> x) & 1, (op >> ((av << 1) | bv)) & 1)


class TestStartsSkeleton(unittest.TestCase):
    def test_anf_starts(self):
        for name in ('present', 'gift', 'ascon', 'aes', 'maj3', 'gf16-mul'):
            n, m, tab, _ = targets.load(name)
            for model in ('nist', 'bgc', 'gc', 'xag'):
                mod = core.Model.load(model)
                c = starts.anf(n, m, tab, mod.ops())
                self.assertEqual(c.value_table(), tab, (name, model))
                self.assertTrue({g[0] for g in c.gates} <= mod.ops(), (name, model))

    def test_skeleton_roundtrip_nist(self):
        tab = targets.aes_sbox()
        for f in sorted((NIST / 'aes-sbox').glob('*.circ.txt')):
            c = core.read_ncff(str(f))
            sk = skeleton.extract(c)
            self.assertEqual(len(sk['ands']), c.metrics()['A'])
            for model in ('nist', 'bgc'):
                c2 = skeleton.synthesize(sk, core.Model.load(model).ops())
                self.assertEqual(c2.value_table(), tab, f.name)
                self.assertEqual(c2.metrics()['A'], len(sk['ands']))

    def test_skeleton_file_roundtrip(self):
        c = core.read_ncff(str(NIST / 'aes-sbox' / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'))
        sk = skeleton.extract(c)
        text = skeleton.write_skel(sk, core.tables_from_values(8, 8, targets.aes_sbox()))
        sk2 = skeleton.read_skel(text)
        self.assertEqual(sk2['ands'], sk['ands'])


class TestKernel(unittest.TestCase):
    def run_cli(self, *args):
        r = subprocess.run([sys.executable, str(PKG / 'cli.py')] + list(args), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_maj_and_determinism(self):
        with tempfile.TemporaryDirectory() as d:
            outs = []
            for k in range(2):
                o = Path(d) / ('m%d' % k)
                self.run_cli('run', '--target', 'maj3', '--model', 'xag', '--objective', 'a,cost',
                             '--iters', '3000', '--seeds', '1-2', '--out', str(o))
                s = json.loads((o / 'summary.json').read_text())
                self.assertTrue(s['best']['core_ok'] and s['best']['independent_ok'])
                self.assertEqual((s['best']['metrics']['G'], s['best']['metrics']['A']), (4, 1))
                outs.append([(o / ('r0-s%d.best.bfx' % i)).read_text() for i in (1, 2)])
            self.assertEqual(outs[0], outs[1])

    def test_caps_respected(self):
        with tempfile.TemporaryDirectory() as d:
            o = Path(d) / 'p'
            self.run_cli('run', '--target', 'present', '--model', 'gc', '--objective', 'cost',
                         '--cap-gd', '4', '--iters', '20000', '--seeds', '1-2', '--out', str(o))
            s = json.loads((o / 'summary.json').read_text())
            # the ANF start of PRESENT has depth <= 4 here, so the cap is feasible from the start
            self.assertLessEqual(s['best']['metrics']['GD'], 4)
            self.assertTrue(s['best']['independent_ok'])


if __name__ == '__main__':
    unittest.main()
