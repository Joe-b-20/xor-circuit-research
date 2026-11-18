"""hwbench with the EDA tools (skipped when hardware/tools/install.sh has not been run).

    python3 -m unittest discover -s hardware/tests -t hardware

The negative tests check that the equivalence checks are not vacuous: a one-gate mutation of
the RTL must fail both the Icarus simulation and the formal proof, and a mutated mapped
netlist must fail the Liberty simulation and the formal proof.
"""
import json
import pathlib
import re
import shutil
import tempfile
import unittest

from hwbench import design as D, flow as F, liberty as L, netlist as N, platforms as P, verilog as V

OURS = D.REPO / 'circuits/aes-invsbox/aes-invsbox-a40-ad4-g134-gd12-xx94-41.circ.txt'
HAVE_TOOLS = all((P.TOOLS / 'mamba' / 'envs' / e / 'bin' / x).exists()
                 for e, x in (('yosys', 'yosys'), ('yosys', 'iverilog'), ('openroad', 'openroad'))) \
    and P.get('nangate45').path(P.get('nangate45').lib).exists()


@unittest.skipUnless(HAVE_TOOLS, 'EDA tools not installed (hardware/tools/install.sh)')
class TestTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix='hwbench-test-'))
        cls.saved = F.BUILD
        F.BUILD = cls.tmp

    @classmethod
    def tearDownClass(cls):
        F.BUILD = cls.saved
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_rtl_checks_catch_a_mutation(self):
        d, res = F.prepare_design(OURS, force=True)
        self.assertEqual(res, {'sim_vectors': 256, 'sim_exhaustive': True, 'formal': 'proved'})
        work = self.tmp / 'mutant'
        shutil.copytree(F.design_dir(d), work)
        rtl = (work / 'rtl.v').read_text()
        mutated = rtl.replace(' ^ ', ' & ', 1)
        self.assertNotEqual(rtl, mutated)
        (work / 'rtl.v').write_text(mutated)
        F.tool('yosys', ['iverilog', '-g2005', '-o', 'tb.vvp', 'tb.v', 'rtl.v'], work,
               work / 'iverilog.log')
        log = F.tool('yosys', ['vvp', '-n', 'tb.vvp'], work, work / 'sim.log')
        errors = int(re.search(r'ERRORS (\d+)', log).group(1))
        self.assertGreater(errors, 0)
        with self.assertRaises(F.CheckFailed):
            F.formal_equiv(work, 'rtl.v', work / 'sat.log')

    def test_preserve_job(self):
        r = F.run_job(OURS, 'nangate45', 'preserve', force=True)
        self.assertEqual(r['cell_types'], {'AND2_X1': 40, 'XOR2_X1': 53, 'XNOR2_X1': 41})
        # Nangate45 areas: AND2_X1 1.064, XOR2_X1 and XNOR2_X1 1.596 um^2
        self.assertAlmostEqual(r['area_um2'], 40 * 1.064 + 94 * 1.596, places=3)
        self.assertEqual(r['route']['drc'], 0)
        self.assertTrue(r['checks']['routed']['sim_exhaustive'])
        st = r['stages']
        self.assertLess(st['synth']['delay_ns'], st['route']['delay_ns'])    # wires add delay
        self.assertGreater(r['route']['power']['total_W'], 0)
        # a mutated copy of the mapped netlist fails both checks
        out = F.job_dir(D.load(OURS), 'nangate45', 'preserve')
        work = self.tmp / 'mapped-mutant'
        work.mkdir()
        text = (out / 'mapped.v').read_text()
        mutated = text.replace('XOR2_X1 ', 'XNOR2_X1 ', 1).replace('.Z(', '.ZN(', 1)
        (work / 'mapped.v').write_text(mutated)
        shutil.copy(F.design_dir(D.load(OURS)) / 'spec.v', work / 'spec.v')
        p = P.get('nangate45')
        lib = L.load(p.path(p.lib))
        sim = N.simulate(N.parse(mutated), lib, D.load(OURS), V.vectors(D.load(OURS)))
        self.assertGreater(sim.mismatches, 0)
        with self.assertRaises(F.CheckFailed):
            F.formal_equiv(work, 'mapped.v', work / 'sat.log', liberty=p.path(p.lib))

    def test_deterministic(self):
        a = F.run_job(OURS, 'nangate45', 'free-area', force=True)
        b = F.run_job(OURS, 'nangate45', 'free-area', force=True)
        for k in ('cell_types', 'area_um2', 'delay_ns', 'stages'):
            self.assertEqual(a[k], b[k], k)
        self.assertEqual(a['route']['wirelength_um'], b['route']['wirelength_um'])


if __name__ == '__main__':
    unittest.main()
