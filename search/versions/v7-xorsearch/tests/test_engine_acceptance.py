"""Threshold acceptance: improvements, neutral and uphill decisions, state round trips."""
import json
import random
import unittest

from xorsearch.engine.acceptance import Threshold
from xorsearch.tests.test_engine_fakes import settings_for


def view(**overrides):
    return settings_for(overrides={f"acceptance.{k}": v for k, v in overrides.items()}
                        ).view("acceptance")


def rate(policy, cur, new, n=20000, seed=3):
    rng = random.Random(seed)
    return sum(policy.decide(cur, new, False, rng) for _ in range(n)) / n


class ThresholdTest(unittest.TestCase):
    def test_improvements_always_kept(self):
        pol = Threshold(view(neutral_p=0.0))
        pol.set_best(10)
        rng = random.Random(1)
        self.assertTrue(all(pol.decide(10, 9, True, rng) for _ in range(100)))
        # A depth tie-break: same primary, key better -> kept even with neutral_p = 0.
        self.assertTrue(pol.decide(10, 10, True, rng))

    def test_neutral_probability(self):
        pol = Threshold(view())
        pol.set_best(10)
        self.assertEqual(rate(pol, 10, 10, n=1000), 1.0)
        pol = Threshold(view(neutral_p=0.0))
        self.assertEqual(rate(pol, 10, 10, n=1000), 0.0)
        pol = Threshold(view(neutral_p=0.3))
        self.assertAlmostEqual(rate(pol, 10, 10), 0.3, delta=0.02)

    def test_uphill_bounded_by_step_and_window(self):
        pol = Threshold(view(**{"threshold.uphill_p": 0.15}))
        pol.set_best(10)
        self.assertAlmostEqual(rate(pol, 10, 11), 0.15, delta=0.015)   # +1 within best+2
        self.assertEqual(rate(pol, 10, 12, n=500), 0.0)                 # +2 > max_uphill
        pol.set_best(9)
        self.assertEqual(rate(pol, 11, 12, n=500), 0.0)                 # 12 > best 9 + 2
        self.assertGreater(rate(pol, 10, 11, n=2000), 0.0)              # 11 <= 9 + 2


class RoundTripTest(unittest.TestCase):
    def test_state_round_trip_continues_identically(self):
        a = Threshold(view())
        a.set_best(20)
        rng = random.Random(5)
        for _ in range(300):
            new = 20 + rng.randrange(-1, 3)
            if a.decide(20, new, new < 20, rng) and new < a.best:
                a.set_best(new)
        data = json.loads(json.dumps(a.state()))
        b = Threshold(view())
        b.load_state(data)
        self.assertEqual(b.summary(), a.summary())
        ra, rb = random.Random(9), random.Random(9)
        for _ in range(300):
            new = 20 + ra.randrange(-1, 3)
            rb.randrange(-1, 3)
            self.assertEqual(a.decide(20, new, False, ra), b.decide(20, new, False, rb))


if __name__ == "__main__":
    unittest.main()
