"""Archive: dedup, near-best band, per-point and total capacity with diversity-aware eviction,
diverse sampling and state round trips."""
import json
import random
import unittest

from xorsearch.engine.archive import Archive, distance
from xorsearch.tests.test_engine_fakes import settings_for


def make(**overrides):
    return Archive(settings_for(overrides={f"archive.{k}": v for k, v in overrides.items()}
                                ).view("archive"))


def vs(base, extra=()):
    """A value set: range(base, base + 20) plus ``extra``."""
    return frozenset(range(base, base + 20)) | frozenset(extra)


def offer(arch, key, gates, depth=5, feasible=True):
    return arch.offer(key, gates, depth, (gates, depth), feasible, "test")


class ArchiveTest(unittest.TestCase):
    def test_distance(self):
        self.assertEqual(distance(frozenset({1, 2}), frozenset({1, 2})), 0.0)
        self.assertEqual(distance(frozenset({1}), frozenset({2})), 1.0)
        self.assertAlmostEqual(distance(frozenset({1, 2, 3}), frozenset({2, 3, 4})), 0.5)

    def test_dedup(self):
        arch = make()
        self.assertTrue(offer(arch, vs(0), 20))
        self.assertFalse(offer(arch, vs(0), 20))
        self.assertEqual(len(arch), 1)

    def test_band(self):
        arch = make(band=2)
        offer(arch, vs(0), 20)
        self.assertTrue(offer(arch, vs(100), 22))
        self.assertFalse(offer(arch, vs(200), 23))           # beyond best + band
        offer(arch, vs(300), 19)                             # new best prunes 22
        self.assertNotIn(vs(100), arch)
        self.assertIn(vs(0), arch)
        self.assertEqual(arch.best, (19, 5))

    def test_per_point_eviction_keeps_far_member(self):
        arch = make(per_point=3)
        far = vs(500)
        offer(arch, far, 20)
        near = [vs(0, extra=(1000 + i,)) for i in range(5)]   # near-copies of each other
        for key in near:
            offer(arch, key, 20)
        self.assertEqual(arch.count((20, 5)), 3)
        self.assertIn(far, arch)                              # the diverse one survives
        # Nearest-neighbour bookkeeping equals a from-scratch computation.
        for e in arch.members():
            others = [distance(e.key, o.key) for o in arch.members() if o is not e]
            self.assertAlmostEqual(e.nn, min(others))

    def test_capacity_evicts_from_worst_point(self):
        arch = make(capacity=4, per_point=10, band=5)
        for i in range(3):
            offer(arch, vs(100 * i), 20)
        offer(arch, vs(1000), 22)
        offer(arch, vs(2000, extra=(1,)), 22)               # 5 members > capacity 4
        self.assertEqual(len(arch), 4)
        self.assertEqual(arch.count((20, 5)), 3)
        self.assertEqual(arch.count((22, 5)), 1)

    def test_sample_diverse(self):
        arch = make(sample_power=2.0, score_bias=1.0)
        ref = vs(0)
        close = vs(0, extra=(999,))
        far = vs(700)
        for key in (ref, close, far):
            offer(arch, key, 20)
        rng = random.Random(1)
        picks = [arch.sample_diverse(ref, rng).key for _ in range(2000)]
        self.assertNotIn(ref, picks)
        self.assertGreater(picks.count(far), 1900)
        self.assertIsNone(make().sample_diverse(ref, rng))

    def test_score_bias_prefers_best(self):
        arch = make(sample_power=0.0, score_bias=0.25, band=5)
        offer(arch, vs(0), 20)
        offer(arch, vs(100), 22)
        rng = random.Random(2)
        picks = [arch.sample_diverse(None, rng).gates for _ in range(4000)]
        self.assertAlmostEqual(picks.count(20) / 4000, 1 / (1 + 0.0625), delta=0.02)

    def test_distance_stats_and_diversity(self):
        arch = make()
        offer(arch, vs(0), 20)
        offer(arch, vs(10), 20)
        self.assertAlmostEqual(arch.distance_stats(vs(0))["min"], distance(vs(0), vs(10)))
        div = arch.diversity()
        self.assertEqual(div["count"], 2)
        self.assertEqual(div["points"], 1)

    def test_state_round_trip(self):
        arch = make(per_point=4, capacity=6)
        rng = random.Random(3)
        for i in range(30):
            offer(arch, vs(rng.randrange(0, 200), extra=(rng.randrange(1000, 1100),)),
                  20 + rng.randrange(0, 3))
        data = json.loads(json.dumps(arch.state()))
        other = make(per_point=4, capacity=6)
        other.load_state(data)
        self.assertEqual([e.key for e in arch.members()], [e.key for e in other.members()])
        self.assertEqual([e.nn for e in arch.members()], [e.nn for e in other.members()])
        for i in range(30):                                   # same future behaviour
            key = vs(rng.randrange(0, 200), extra=(rng.randrange(1100, 1200),))
            g = 20 + rng.randrange(0, 3)
            self.assertEqual(offer(arch, key, g), offer(other, key, g))
        self.assertEqual(arch.keys(), other.keys())


if __name__ == "__main__":
    unittest.main()
