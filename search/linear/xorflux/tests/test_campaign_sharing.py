"""Campaign pool: coordinator PoolBook and worker Pool (pull / off, scope, exclusions)."""
import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from xorflux.campaign.checkpoint import read_json, read_jsonl
from xorflux.campaign.records import RecordWriter, circuit_values
from xorflux.campaign.sharing import NullPool, Pool, PoolBook, pool_path
from xorflux.tests.test_campaign_stub import LADDER, StubBackend, StubRecorder, circuit, toy_target

# Two distinct DAGs at 4@3 (the 3@3 optimum plus different dead gates) and the 3@3 optimum.
DAG_A = LADDER[3] + [[0, 2]]
DAG_B = LADDER[3] + [[1, 3]]


def cfg(**overrides):
    base = {"mode": "pull", "scope": "target", "sample_points": 1, "exclude_own": True}
    return SimpleNamespace(**{**base, **overrides})


class SharingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name)
        self.backend = StubBackend()
        self.target = toy_target()
        self.book = PoolBook(self.run, per_point=8)

    def tearDown(self):
        self.tmp.cleanup()

    def writer(self, worker, group):
        spec = {"id": worker, "objective": "gates", "depth_cap": None, "gate_limit": None}
        context = {"run_id": "r", "worker": worker, "group": group, "target": "toy4",
                   "matrix_sha256": self.target.matrix_sha256}
        return RecordWriter(self.run / "workers" / worker, self.run, context, self.backend, self.target,
                            spec, 4, 32, True)

    def record(self, worker, group, gates):
        entry = self.writer(worker, group).add({"circuit": circuit(gates)})
        self.book.add("toy4", entry)
        self.book.write("toy4", self.target.matrix_sha256)
        return entry

    def pool(self, worker="me", group="g1", **overrides):
        spec = {"id": worker, "group": group, "target": "toy4", "objective": "gates",
                "depth_cap": overrides.pop("depth_cap", None), "gate_limit": None}
        return Pool(self.run, spec, self.target.matrix_sha256, cfg(**overrides), self.backend, self.target, 4)

    def test_book_keeps_distinct_nondominated(self):
        a = self.record("w1", "g1", DAG_A)
        self.record("w2", "g1", DAG_B)
        self.assertFalse(self.book.add("toy4", a))                       # same DAG again
        self.assertEqual(self.book.summary("toy4"), {"4@3": 2})
        best = self.writer("w2", "g2").add({"circuit": circuit(LADDER[3])})
        self.book.add("toy4", best)                                       # 3@3 evicts 4@3
        changes = self.book.write("toy4", self.target.matrix_sha256)
        self.assertEqual(changes[(3, 3)], {"added": [best["path"]], "donor": ["w2"],
                                           "evicted": [{"gates": 4, "depth": 3}]})
        self.assertEqual(self.book.summary("toy4"), {"3@3": 1})
        data = read_json(pool_path(self.run, "toy4"))
        self.assertEqual(data["version"], 3)
        self.assertEqual([(p["gates"], p["depth"]) for p in data["points"]], [(3, 3)])

    def test_per_point_cap_is_per_group(self):
        self.book = PoolBook(self.run, per_point=1)
        self.record("w1", "g1", DAG_A)
        self.record("w2", "g1", DAG_B)                                   # g1 slot full
        self.assertEqual(self.book.summary("toy4"), {"4@3": 1})
        self.record("w3", "g2", DAG_B)                                   # g2 has its own slot
        self.assertEqual(self.book.summary("toy4"), {"4@3": 2})
        self.assertEqual(self.book.point_size("toy4", (4, 3)), (2, 2))

    def test_sample_is_distinct_and_verified(self):
        self.record("w1", "g1", DAG_A)
        b = self.record("w2", "g2", DAG_B)
        pool = self.pool()
        pool.recorder = StubRecorder(self.run, "me")
        elite = pool.sample(set(), random.Random(1))
        self.assertIn(elite["donor"], ("w1", "w2"))
        self.assertEqual((elite["gates"], elite["depth"]), (4, 3))
        self.assertIn(elite["values"], (circuit_values(circuit(DAG_A), 4),
                                        circuit_values(circuit(DAG_B), 4)))
        events = read_jsonl(self.run / "events.jsonl")[0]
        self.assertEqual(events[0]["ev"], "pool_sample")
        self.assertEqual(events[0]["donor"], elite["donor"])
        # Excluding one DAG by hash and the other by value set (the engine's archive keys).
        exclude = {b["dag_sha256"], frozenset(circuit_values(circuit(DAG_A), 4))}
        self.assertIsNone(pool.sample(exclude, random.Random(1)))
        self.assertEqual(pool.stats["sample_misses"], 1)

    def test_exclude_own_and_scope(self):
        self.record("me", "g1", DAG_A)
        self.record("w2", "g2", DAG_B)
        self.assertEqual(self.pool().sample(set(), random.Random(0))["donor"], "w2")
        self.assertIsNone(self.pool(scope="group").sample(set(), random.Random(0)))
        own = self.pool(exclude_own=False, scope="group")
        self.assertEqual(own.sample(set())["donor"], "me")

    def test_cap_filters_points(self):
        self.record("w2", "g1", LADDER[3])                                 # 3@3 only
        self.assertIsNone(self.pool(depth_cap=2).sample(set()))
        self.assertIsNotNone(self.pool(depth_cap=3).sample(set()))

    def test_modes(self):
        self.record("w2", "g1", LADDER[3])
        self.assertIsNone(self.pool(mode="off").sample(set()))
        self.assertIsNotNone(self.pool(mode="pull").sample(set()))
        self.assertIsNone(NullPool().sample(set()))

    def test_pool_file_for_other_matrix_is_ignored(self):
        self.record("w2", "g1", LADDER[3])
        pool = Pool(self.run, {"id": "me", "group": "g1", "target": "toy4", "objective": "gates",
                               "depth_cap": None, "gate_limit": None}, "f" * 64, cfg(), self.backend,
                    self.target, 4)
        self.assertIsNone(pool.sample(set()))


if __name__ == "__main__":
    unittest.main()
