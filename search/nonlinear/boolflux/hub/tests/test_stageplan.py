"""Stage accounting and planned (minimal-support) joins (2026-11-17):
    python3 -m unittest boolflux.hub.tests.test_stageplan   (from search/nonlinear/)

Stage splits of published circuits (measured values), the exact plan_pair prediction of the 31/5 recipe
(32/5 front + 32/4 last layer = 9+5+17), the built join verified on all 256 inputs, plan_pair equal to the built
metrics on every feasible pair of a small pool (or an upper bound on A when clean() merges an AND), the 27-AND
refusal, the span grouping of make_plan.  No test starts a kernel.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ.setdefault('BOOLFLUX_FUNCTION', 'aes-sbox')
from boolflux.hub import stageplan as SP              # noqa: E402
from boolflux.hub.common import metrics, verify       # noqa: E402

PUB = Path(__file__).resolve().parents[5] / 'circuits' / 'aes-sbox'
F = {k: PUB / v for k, v in {
    '32/5': Path(__file__).resolve().parent / 'data' / 'aes-sbox-a32-ad5-g104-gd29-xx72-23.circ.txt', '32/4': 'aes-sbox-a32-ad4-g111-gd25-xx79-30.circ.txt',
    '28/5': 'aes-sbox-a28-ad5-g125-gd24-xx97-50.circ.txt', '28/4': 'aes-sbox-a28-ad4-g130-gd24-xx102-45.circ.txt',
    '35/3': Path(__file__).resolve().parent / 'data' / 'aes-sbox-a35-ad3-g137-gd28-xx102-47.circ.txt'}.items()}


def pool():
    return {k: SP.load_pools([str(p)], 'aes-sbox', log=lambda *a: None)[0] for k, p in F.items()}


class TestStagePlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['BOOLFLUX_FUNCTION'] = 'aes-sbox'
        cls.P = pool()

    def test_stages(self):
        want = {'32/5': (9, 5, 18), '32/4': (9, 6, 17), '28/5': (10, 5, 13), '28/4': (9, 6, 13), '35/3': (11, 12, 12)}
        for k, s in want.items():
            self.assertEqual(self.P[k].stages, s, k)
            self.assertTrue(self.P[k].indep, k)

    def test_31_5_recipe(self):
        X, Y = self.P['32/5'], self.P['32/4']
        p = SP.plan_pair(X, Y, 3)
        self.assertEqual((p['A'], p['AD'], p['xa'], p['ya']), (31, 5, 14, 17))
        c = SP.build_pair(X, Y, 3, p['need'])
        ok, info = verify(c)
        self.assertTrue(ok, info)
        self.assertEqual(metrics(c)[:2], (31, 5))

    def test_prediction_exact_or_upper(self):
        n = 0
        for X in self.P.values():
            for Y in self.P.values():
                for LY in range(1, Y.AD):
                    p = SP.plan_pair(X, Y, LY)
                    if p is None: continue
                    c = SP.build_pair(X, Y, LY, p['need'])
                    self.assertIsNotNone(c)
                    self.assertTrue(verify(c)[0])
                    m = metrics(c)
                    self.assertLessEqual(m[0], p['A'])
                    if m[0] == p['A']: self.assertEqual(m[1], p['AD'])
                    n += 1
        self.assertGreater(n, 10)

    def test_make_plan_and_refusal(self):
        pts = SP.known_points(self.P.values())
        rows, fronts, backs = SP.make_plan(list(self.P.values()), pts, log=lambda *a: None)
        self.assertEqual(len(fronts), 5)
        self.assertTrue(any((r['A'], r['AD'], r['kind']) == (31, 5, 'new-class') for r in rows))
        self.assertTrue(all(r['A'] >= 28 for r in rows))
        with self.assertRaises(SystemExit):
            SP.make_plan(list(self.P.values()), pts, min_a=27, log=lambda *a: None)


if __name__ == '__main__':
    unittest.main()
