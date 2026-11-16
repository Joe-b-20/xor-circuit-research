"""Metrics: distances, diversity panels, plateau tracking, circuit shape."""
from __future__ import annotations

import random
import unittest

from xorflux.telemetry import metrics
from xorflux.telemetry.metrics import (HyperLogLog, PlateauTracker, diversity,
                                         jaccard_distance, shape_from_gates)


class DistanceTest(unittest.TestCase):
    def test_jaccard(self):
        a, b = frozenset({1, 2, 3}), frozenset({2, 3, 4})
        self.assertAlmostEqual(jaccard_distance(a, b), 0.5)
        self.assertEqual(jaccard_distance(a, a), 0.0)
        self.assertEqual(jaccard_distance(frozenset(), frozenset()), 0.0)
        self.assertEqual(jaccard_distance(a, frozenset({9})), 1.0)
        self.assertAlmostEqual(jaccard_distance([1, 2], [2, 3]), 2 / 3)

    def test_diversity_collapse_and_spread(self):
        s = frozenset(range(10))
        collapsed = diversity([s, s, s, s])
        self.assertEqual((collapsed["distinct"], collapsed["modal_fraction"], collapsed["mean"]),
                         (1, 1.0, 0.0))
        spread = diversity([frozenset(range(i * 10, i * 10 + 10)) for i in range(5)])
        self.assertEqual(spread["distinct"], 5)
        self.assertEqual(spread["min"], 1.0)
        self.assertEqual(spread["basins"], 5)
        self.assertEqual(spread["pairs"], 10)
        self.assertFalse(spread["sampled"])
        self.assertEqual(diversity([])["n"], 0)

    def test_diversity_samples_when_large(self):
        rng = random.Random(1)
        sets = [frozenset(rng.sample(range(200), 50)) for _ in range(120)]
        exact = diversity(sets, max_pairs=10**6)
        sampled = diversity(sets, max_pairs=500)
        self.assertTrue(sampled["sampled"])
        self.assertEqual(sampled["pairs"], 500)
        self.assertAlmostEqual(sampled["mean"], exact["mean"], delta=0.02)

    def test_basins_group_near_states(self):
        base = set(range(100))
        near = [frozenset(base - {i}) for i in range(5)]        # all within 0.02 of each other
        far = [frozenset(range(1000, 1100))]
        self.assertEqual(metrics.basins(near + far, radius=0.05), 2)


class PlateauTest(unittest.TestCase):
    def test_counts_drift_and_close(self):
        p = PlateauTracker(drift_every=1)
        entry = frozenset(range(10))
        p.enter((100, 7), entry, it=50, t=5.0)
        p.observe(None, False, False, 51, 5.1)
        p.observe(frozenset(range(1, 11)), True, True, 52, 5.2)
        p.observe(frozenset(range(2, 12)), True, True, 53, 5.3)
        p.observe(frozenset(range(1, 11)), True, True, 54, 5.4)    # revisit
        snap = p.snapshot()
        self.assertEqual((snap["age_it"], snap["proposals"], snap["neutral_accepts"]), (4, 4, 3))
        self.assertAlmostEqual(snap["age_s"], 0.4)
        self.assertEqual((snap["distinct_states"], snap["distinct_exact"]), (3, True))
        self.assertEqual(snap["visits"], 3)
        self.assertAlmostEqual(snap["neutral_rate"], 0.75)
        self.assertAlmostEqual(snap["drift"], jaccard_distance(entry, frozenset(range(1, 11))))
        self.assertAlmostEqual(snap["max_drift"], jaccard_distance(entry, frozenset(range(2, 12))))
        self.assertEqual(snap["level"], [100, 7])
        closed = p.close("improve", 60, 6.0)
        self.assertEqual((closed["exit"], closed["age_it"]), ("improve", 10))
        self.assertFalse(p.active)

    def test_switches_to_estimate_beyond_cap(self):
        p = PlateauTracker(distinct_cap=1000, hll_precision=12)
        p.enter((1, 1), None, 0, 0.0)
        n = 20_000
        for i in range(n):
            p.observe(frozenset((i, i + 1)), True, True, i, float(i))
        count, exact = p.distinct_states()
        self.assertFalse(exact)
        self.assertLess(abs(count - n) / n, 0.05)

    def test_int_keys_and_checkpoint(self):
        p = PlateauTracker()
        p.enter((5, 2), 123, 0, 0.0)
        for i in range(50):
            p.observe(i % 20, True, False, i, i * 0.1)
        self.assertEqual(p.distinct_states(), (21, True))       # 0..19 plus the entry key
        self.assertIsNone(p.drift())
        q = PlateauTracker()
        q.restore(p.checkpoint())
        count, exact = q.distinct_states()
        self.assertFalse(exact)
        self.assertEqual(count, 21)                             # HLL is near-exact when small
        self.assertEqual(q.snapshot()["proposals"], 50)
        self.assertEqual(q.level, (5, 2))

    def test_rekey_restores_drift_after_restore(self):
        entry, later = frozenset(range(10)), frozenset(range(5, 15))
        p = PlateauTracker()
        p.enter((10, 3), entry, 0, 0.0)
        p.observe(later, True, True, 1, 0.1)
        q = PlateauTracker()
        q.restore(p.checkpoint())
        self.assertIsNone(q.snapshot()["drift"])
        q.rekey(entry, later)
        self.assertAlmostEqual(q.snapshot()["drift"], p.snapshot()["drift"])
        q.rekey(None)                                    # unknown keys change nothing
        self.assertIs(q.entry_key, entry)

    def test_hll_small_and_large(self):
        h = HyperLogLog(10)
        for i in range(100):
            h.add(i)
        self.assertAlmostEqual(h.estimate(), 100, delta=5)


class ShapeTest(unittest.TestCase):
    def test_shape_from_gates(self):
        # 3 inputs: g3 = x0^x1, g4 = g3^x2, g5 = x0^x2 ; outputs g4, g5
        gates = [[0, 1], [3, 2], [0, 2]]
        s = shape_from_gates(gates, [4, 5], 3)
        self.assertEqual((s["gates"], s["depth"], s["output_gates"]), (3, 2, 2))
        self.assertEqual(s["levels"], {"1": 2, "2": 1})
        self.assertEqual(s["weights"], {"2": 2, "3": 1})
        self.assertEqual(s["input_fanout"]["max"], 2)
        self.assertEqual(s["fanout_hist"], {"0": 2, "1": 1})
        self.assertEqual(shape_from_gates(gates)["n_inputs"], 3)

    def test_symmetric_difference(self):
        self.assertEqual(metrics.symmetric_difference([1, 2, 3], [3, 4]),
                         {"removed": [1, 2], "added": [4]})


if __name__ == "__main__":
    unittest.main()
