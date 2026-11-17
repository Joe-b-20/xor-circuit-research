"""Gate kernel options of idea 04 (2026-11-17), both default off: `chain_p` (two-step compound move) and `l3n`
(AND-like root of two pair values in resub3).  Off, the kernel prints the old lines (6 forms, no chain/l3n kstat);
on, runs keep the function and report their counters; bad values are refused.  The bit-identity of the default
trajectory against 08012e1 is checked by the golden trajectories in test_kernel.py and by the idea-04 kid.py run.

    python3 -m unittest search/nonlinear/boolflux/tests/test_kernel_idea04.py     (from the repository root)
"""
import re
import unittest

from boolflux.tests.test_kernel import BASE, LEX_COST, NIST_LIB, aes, check_same_function, run

START = 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'


def cfg(**kw):
    s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s.update({'iters': 300, 'seed': 3}); s.update(kw)
    return s


class TestIdea04(unittest.TestCase):
    def go(self, s):
        text = aes(START)
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        check_same_function(self, text, (d / 'out.bfx').read_text())
        return out

    def test_off_prints_the_old_lines(self):
        out = self.go(cfg())
        self.assertRegex(out, r'kstat forms L0,L1,L2x,L2n,L3,XS\n')
        self.assertNotIn('kstat chain', out); self.assertNotIn('kstat l3n', out)

    def test_chain_runs_and_keeps_the_function(self):
        out = self.go(cfg(**{'chain_p': 0.2, 'chain.k1': 2, 'chain.k2': 3}))
        m = re.search(r'kstat chain prop (\d+) step1_circuits (\d+) targets2 (\d+)', out)
        self.assertIsNotNone(m)
        self.assertGreater(int(m.group(1)), 0); self.assertGreater(int(m.group(3)), 0)
        self.assertIn('kstat chain_hist', out)
        out = self.go(cfg(**{'chain_p': 1, 'chain.freed': 0, 'chain.accept': 0, 'chain.lev1': 1, 'chain.lev2': 2, 'iters': 30}))
        self.assertRegex(out, r'acc_neutral 0 ')

    def test_l3n_runs_and_keeps_the_function(self):
        out = self.go(cfg(**{'l3n': 5000, 'mv.resub3': 3}))
        self.assertRegex(out, r'kstat forms L0,L1,L2x,L2n,L3,XS,L3n\n')
        self.assertRegex(out, r'kstat l3n moves [1-9]\d* ')

    def test_bad_values(self):
        for k, v in (('chain_p', 2), ('chain.k1', 0), ('chain.lev2', 4), ('chain.accept', 3)):
            rc, out, err, d = run(aes(START), cfg(**{k: v}))
            self.assertEqual(rc, 2, (k, v)); self.assertIn('chain', err)


if __name__ == '__main__':
    unittest.main()
