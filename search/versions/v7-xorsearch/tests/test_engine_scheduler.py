"""Scheduler: fixed weights, adaptive credit per work, floors, decay and state round trips."""
import json
import random
import unittest

from xorsearch.engine.scheduler import Scheduler
from xorsearch.tests.test_engine_fakes import settings_for


def view(**overrides):
    return settings_for(overrides={f"scheduler.{k}": v for k, v in overrides.items()}
                        ).view("scheduler")


PRIORS = {"plateau": [2.0, 1.0, 1.0, 0.0], "burst": [1.0, 1.0, 1.0, 0.0],
          "repair": [0.0, 0.0, 0.0, 0.0]}
NAMES = ["walk", "lns", "other", "off"]


def share(sched, phase, idx, n=20000, seed=1):
    rng = random.Random(seed)
    return sum(sched.pick(phase, rng) == idx for _ in range(n)) / n


class FixedTest(unittest.TestCase):
    def test_normalised_priors(self):
        s = Scheduler(view(mode="fixed", min_share=0.0), NAMES, PRIORS)
        self.assertEqual(s.probabilities("plateau"), [0.5, 0.25, 0.25, 0.0])
        self.assertAlmostEqual(share(s, "plateau", 0), 0.5, delta=0.015)

    def test_zero_prior_never_picked_and_empty_phase_falls_back(self):
        s = Scheduler(view(mode="fixed"), NAMES, PRIORS)
        rng = random.Random(2)
        self.assertNotIn(3, {s.pick("plateau", rng) for _ in range(5000)})
        self.assertEqual(s.probabilities("repair"), s.probabilities("plateau"))

    def test_floor_is_exact(self):
        s = Scheduler(view(mode="fixed", min_share=0.1), ["a", "b"],
                      {"plateau": [1000.0, 1.0]})
        p = s.probabilities("plateau")
        self.assertAlmostEqual(p[1], 0.1 + 0.8 * (1 / 1001))
        self.assertAlmostEqual(sum(p), 1.0)

    def test_weights_and_floor_are_time_shares(self):
        # A 40x slower move at weight 1:1 gets half the time, so 1/41 of the proposals; held
        # at the floor it gets the floor's share of the time, not of the proposals.
        s = Scheduler(view(mode="fixed", min_share=0.0, prior_pulls=0.0), ["fast", "slow"],
                      {"plateau": [1.0, 1.0]})
        for _ in range(1000):
            s.credit(0, 1.0, False, False, False, False)
            s.credit(1, 40.0, False, False, False, False)
        p = s.probabilities("plateau")
        self.assertAlmostEqual(p[1], 1 / 41)
        s = Scheduler(view(mode="fixed", min_share=0.1, prior_pulls=0.0), ["fast", "slow"],
                      {"plateau": [1000.0, 1e-9]})
        for _ in range(1000):
            s.credit(0, 1.0, False, False, False, False)
            s.credit(1, 40.0, False, False, False, False)
        p = s.probabilities("plateau")
        self.assertAlmostEqual(p[1] * 40 / (p[1] * 40 + p[0]), 0.1, places=6)

    def test_credit_does_not_change_fixed_mode(self):
        s = Scheduler(view(mode="fixed"), NAMES, PRIORS)
        before = s.probabilities("plateau")
        for _ in range(500):
            s.credit(1, 1, False, True, True, False)
        self.assertEqual(s.probabilities("plateau"), before)


class AdaptiveTest(unittest.TestCase):
    def test_rewarded_move_gains_share_others_keep_floor(self):
        s = Scheduler(view(min_share=0.05, refresh_every=1), NAMES, PRIORS)
        rng = random.Random(3)
        for _ in range(3000):
            i = s.pick("plateau", rng)
            s.credit(i, 1, i == 1, i == 1 and rng.random() < 0.1, False, False)
        p = s.probabilities("plateau")
        self.assertGreater(p[1], 0.5)              # prior share was 0.25
        self.assertGreaterEqual(p[0], 0.05 - 1e-12)
        self.assertGreaterEqual(p[2], 0.05 - 1e-12)
        self.assertEqual(p[3], 0.0)

    def test_credit_is_per_work_unit(self):
        s = Scheduler(view(min_share=0.0, refresh_every=1), ["cheap", "costly"],
                      {"plateau": [1.0, 1.0]})
        for _ in range(2000):
            s.credit(0, 1, False, True, False, False)
            s.credit(1, 10, False, True, False, False)
        p = s.probabilities("plateau")
        self.assertGreater(p[0], 0.85)

    def test_worker_best_counts_more_than_chain_best_more_than_neutral(self):
        s = Scheduler(view(min_share=0.0, refresh_every=1, max_boost=100.0),
                      ["n", "c", "w"], {"plateau": [1.0, 1.0, 1.0]})
        for _ in range(500):
            s.credit(0, 1, True, False, False, False)
            s.credit(1, 1, False, True, False, False)
            s.credit(2, 1, False, True, True, False)
        p = s.probabilities("plateau")
        self.assertLess(p[0], p[1])
        self.assertLess(p[1], p[2])

    def test_decay_forgets_old_credit(self):
        s = Scheduler(view(min_share=0.0, refresh_every=1, half_life=200), ["a", "b"],
                      {"plateau": [1.0, 1.0]})
        for _ in range(1000):
            s.credit(0, 1, False, True, False, False)
            s.credit(1, 1, False, False, False, False)
        early = s.probabilities("plateau")[0]
        for _ in range(3000):                         # now b earns, a does not
            s.credit(0, 1, False, False, False, False)
            s.credit(1, 1, False, True, False, False)
        self.assertGreater(early, 0.8)
        self.assertLess(s.probabilities("plateau")[0], 0.2)

    def test_burst_uses_priors_unless_adaptive(self):
        s = Scheduler(view(min_share=0.0, refresh_every=1), NAMES, PRIORS)
        for _ in range(500):
            s.credit(1, 1, False, True, False, False)
        self.assertAlmostEqual(s.probabilities("burst")[0], 1 / 3)
        s2 = Scheduler(view(min_share=0.0, refresh_every=1, burst_adaptive=True), NAMES, PRIORS)
        for _ in range(500):
            s2.credit(0, 1, False, False, False, False)
            s2.credit(1, 1, False, True, False, False)
            s2.credit(2, 1, False, False, False, False)
        self.assertGreater(s2.probabilities("burst")[1], 0.5)

    def test_weights_snapshot(self):
        s = Scheduler(view(), NAMES, PRIORS)
        w = s.weights()
        self.assertEqual(set(w), {"plateau", "burst", "repair"})
        self.assertAlmostEqual(sum(w["plateau"].values()), 1.0, places=4)

    def test_state_round_trip_same_picks(self):
        a = Scheduler(view(refresh_every=7), NAMES, PRIORS)
        rng = random.Random(4)
        for _ in range(777):
            i = a.pick("plateau", rng)
            a.credit(i, 1 + i, rng.random() < 0.5, rng.random() < 0.05, False, False)
        b = Scheduler(view(refresh_every=7), NAMES, PRIORS)
        b.load_state(json.loads(json.dumps(a.state())))
        ra, rb = random.Random(8), random.Random(8)
        for _ in range(2000):
            ia, ib = a.pick("plateau", ra), b.pick("plateau", rb)
            self.assertEqual(ia, ib)
            r = ra.random() < 0.05
            rb.random()
            a.credit(ia, 2, True, r, False, False)
            b.credit(ib, 2, True, r, False, False)

    def test_rescale_keeps_probabilities(self):
        s = Scheduler(view(half_life=1, refresh_every=1), ["a", "b"], {"plateau": [1.0, 1.0]})
        for i in range(400):                          # scale doubles per credit: forces rescale
            s.credit(i % 2, 1, False, i % 2 == 0, False, False)
        self.assertLess(s.scale, 1e101)
        self.assertAlmostEqual(sum(s.probabilities("plateau")), 1.0)


if __name__ == "__main__":
    unittest.main()
