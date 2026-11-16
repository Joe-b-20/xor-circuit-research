"""Restart controller: stall and root-age triggers, size scaling, incumbent protection, source
choice and state round trips."""
import json
import random
import unittest

from xorflux.engine.restart import RestartController
from xorflux.tests.test_engine_fakes import settings_for


def make(**overrides):
    return RestartController(settings_for(
        overrides={f"restart.{k}": v for k, v in overrides.items()}).view("restart"))


class TriggerTest(unittest.TestCase):
    def test_stall_seconds(self):
        rc = make(stall_seconds=100.0, root_seconds=0.0)
        rc.started(0, 0, 0.0)
        self.assertIsNone(rc.due(10, 10, 99.0, 50, False))
        self.assertEqual(rc.due(10, 10, 100.0, 50, False), "stall_seconds")
        rc.improved(10, 10, 90.0)
        self.assertIsNone(rc.due(20, 20, 150.0, 50, False))

    def test_replayable_triggers(self):
        rc = make(stall_seconds=0.0, root_seconds=0.0, stall_proposals=50)
        rc.started(0, 0, 0.0)
        self.assertIsNone(rc.due(49, 0, 1e9, 10, False))
        self.assertEqual(rc.due(50, 0, 1e9, 10, False), "stall_proposals")
        rc = make(stall_seconds=0.0, root_seconds=0.0, stall_work=500)
        rc.started(0, 0, 0.0)
        self.assertEqual(rc.due(1, 500, 0.0, 10, False), "stall_work")

    def test_root_age_and_incumbent(self):
        rc = make(stall_seconds=1000.0, root_seconds=300.0, incumbent_factor=3.0)
        rc.started(0, 0, 0.0)
        rc.improved(5, 5, 250.0)
        self.assertEqual(rc.due(9, 9, 300.0, 50, False), "root_seconds")
        self.assertIsNone(rc.due(9, 9, 300.0, 50, True))          # holds the worker best
        self.assertIsNone(rc.due(9, 9, 250.0 + 2999.0, 50, True))
        self.assertEqual(rc.due(9, 9, 250.0 + 3000.0, 50, True), "stall_seconds")

    def test_size_scaling(self):
        rc = make(stall_seconds=100.0, root_seconds=0.0, size_ref=100, size_exponent=1.0)
        self.assertEqual(rc.scale(50), 1.0)                      # never below 1
        self.assertEqual(rc.scale(400), 4.0)
        rc.started(0, 0, 0.0)
        self.assertIsNone(rc.due(1, 1, 399.0, 400, False))
        self.assertEqual(rc.due(1, 1, 400.0, 400, False), "stall_seconds")

    def test_disabled(self):
        rc = make(enabled=False, stall_seconds=1.0)
        rc.started(0, 0, 0.0)
        self.assertIsNone(rc.due(10**6, 10**6, 1e9, 10, False))

    def test_defaults_follow_evidence(self):
        rc = make()
        self.assertTrue(600 <= rc.stall_seconds <= 1200)          # 2026-10-28 decay of rates
        self.assertTrue(3600 <= rc.root_seconds <= 5400)
        self.assertEqual(max(rc.weights, key=rc.weights.get), "fresh")


class SourceTest(unittest.TestCase):
    def test_weighted_choice(self):
        rc = make(w_fresh=0.6, w_elite=0.2, w_shared=0.1, w_best=0.1)
        rng = random.Random(1)
        avail = {"fresh": True, "elite": True, "shared": True, "best": True}
        firsts = [rc.order(rng, avail)[0] for _ in range(10000)]
        self.assertAlmostEqual(firsts.count("fresh") / 1e4, 0.6, delta=0.02)
        self.assertAlmostEqual(firsts.count("shared") / 1e4, 0.1, delta=0.01)

    def test_unavailable_excluded_and_fallback_order(self):
        rc = make(w_fresh=0.6, w_elite=0.2, w_shared=0.1, w_best=0.1)
        rng = random.Random(2)
        order = rc.order(rng, {"fresh": False, "elite": True, "shared": False, "best": True})
        self.assertEqual(sorted(order), ["best", "elite"])
        order = rc.order(rng, {"fresh": True, "elite": True, "shared": True, "best": True})
        self.assertEqual(sorted(order[1:], key=lambda s: -rc.weights[s]), order[1:])

    def test_zero_weights_fall_back_to_available(self):
        rc = make(w_fresh=0.0, w_elite=0.0, w_shared=0.0, w_best=0.0)
        self.assertEqual(rc.order(random.Random(1), {"best": True}), ["best"])

    def test_state_round_trip_keeps_ages(self):
        rc = make(stall_seconds=100.0, root_seconds=0.0)
        rc.started(0, 0, 1000.0)
        rc.improved(4, 40, 1050.0)
        rc.restarted("stall_seconds", "fresh")
        data = json.loads(json.dumps(rc.state(1080.0)))
        other = make(stall_seconds=100.0, root_seconds=0.0)
        other.load_state(data, 5.0)                    # new process clock
        self.assertIsNone(other.due(5, 50, 74.0, 10, False))
        self.assertEqual(other.due(5, 50, 75.0, 10, False), "stall_seconds")
        self.assertEqual(other.by_source, {"fresh": 1})


if __name__ == "__main__":
    unittest.main()
