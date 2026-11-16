"""Coordinator collection on synthetic records: frontier attribution, pool, rejection, diversity.

Event shapes follow telemetry/schema.md section 5 (``point``, ``by``, ``improvement``, ...).
"""
import json
import tempfile
import unittest
from pathlib import Path

from xorsearch.campaign.checkpoint import atomic_json, read_json
from xorsearch.campaign.coordinator import Collector, Coordinator
from xorsearch.campaign.freeze import freeze, frozen_target, load_campaign, resolve
from xorsearch.campaign.records import RecordWriter, circuit_values
from xorsearch.tests.test_campaign_stub import (LADDER, ListLog, StubBackend, circuit, pairwise,
                                                toy_campaign, write_campaign)

GROUPS = """
[[workers]]
name = "a"
target = "toy4"
count = 2
[[workers]]
name = "b"
target = "toy4"
count = 1
depth_cap = 2
"""


class CollectorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        path = write_campaign(base, toy_campaign(GROUPS))
        self.run = base / "run"
        self.plan = freeze(resolve(load_campaign(path), campaign_path=path), self.run, freeze_source=False)
        self.backend = StubBackend()
        self.targets = {"toy4": frozen_target(self.run, self.plan, "toy4", self.backend)}
        self.log = ListLog()
        self.collector = Collector(self.run, self.plan, self.backend, self.targets, 8, self.log, 0.05)
        self.specs = {w["id"]: w for w in self.plan["workers"]}

    def tearDown(self):
        self.tmp.cleanup()

    def writer(self, wid):
        spec = self.specs[wid]
        context = {"run_id": self.plan["run_id"], "worker": wid, "group": spec["group"], "target": "toy4",
                   "matrix_sha256": self.plan["targets"]["toy4"]["matrix_sha256"]}
        return RecordWriter(self.run / "workers" / wid, self.run, context, self.backend, self.targets["toy4"],
                            spec, 4, 32, True, clock=lambda: float(len(self.log.events)))

    def save(self, wid, gates, ref=None):
        writer = self.writer(wid)
        entry = writer.add({"circuit": circuit(gates), "ref": ref, "kind": "gates", "move": "walk.remove1"})
        atomic_json(self.run / "workers" / wid / "chain.json", {
            "best_values": writer.best_values, "best_dag": writer.best["dag_sha256"],
            "chain_values": circuit_values(circuit(gates), 4)})
        return entry

    def test_frontier_events_with_attribution(self):
        self.save("a-00", LADDER[0], ref="a-00:it40")                    # a sampled DAG
        self.save("a-01", LADDER[1], ref="a-01-000001")                  # an improvement
        self.assertEqual(self.collector.collect(), 2)
        frontier = self.log.of("frontier")
        self.assertEqual([(e["point"], e["by"]) for e in frontier],
                         [({"gates": 6, "depth": 3}, "a-00"), ({"gates": 5, "depth": 3}, "a-01")])
        self.assertEqual(frontier[1]["removed"], [{"gates": 6, "depth": 3}])
        self.assertIsNone(frontier[0]["improvement"])                     # ref with a ':'
        self.assertEqual(frontier[1]["improvement"], "a-01-000001")       # the dossier id ref
        self.assertEqual(frontier[1]["ref"], "a-01-000001")
        self.assertEqual(frontier[1]["move"], "walk.remove1")
        self.assertEqual(frontier[1]["kind"], "gates")
        self.assertTrue(frontier[1]["dag"])
        self.save("b-00", LADDER[2])
        self.save("a-00", LADDER[3])
        self.collector.collect()
        summary = self.collector.frontier_summary()["toy4"]
        self.assertEqual([(p["gates"], p["depth"], p["worker"]) for p in summary], [(3, 3, "a-00"), (4, 2, "b-00")])
        self.assertEqual(self.collector.collect(), 0)                     # nothing new: offsets kept
        pool = read_json(self.run / "pool" / "toy4.json")
        self.assertEqual(sorted((p["gates"], p["depth"]) for p in pool["points"]), [(3, 3), (4, 2)])
        pool_events = self.log.of("pool")
        self.assertTrue(all({"point", "size", "distinct", "added", "donor", "evicted"} <= set(e)
                            for e in pool_events))
        self.assertIn({"gates": 5, "depth": 3}, pool_events[-1]["evicted"] + pool_events[-2]["evicted"])

    def test_first_finder_is_credited_within_one_pass(self):
        # a-01 finds 4@2 first (t from its writer clock), a-00 later; one collection sees both.
        self.save("a-01", LADDER[2])
        self.log.events.append({"ev": "tick"})                            # advances the fake clock
        self.save("a-00", LADDER[2])
        self.collector.collect()
        self.assertEqual([e["by"] for e in self.log.of("frontier")], ["a-01"])

    def test_tampered_record_is_rejected(self):
        entry = self.save("a-00", LADDER[1])
        path = self.run / entry["path"]
        data = json.loads(path.read_text())
        data["metadata"]["worker"] = "a-01"                               # claims another worker
        path.write_text(json.dumps(data))
        self.assertEqual(self.collector.collect(), 0)
        rejected = self.log.of("record_rejected")
        self.assertEqual(len(rejected), 1)
        self.assertIn("hash", rejected[0]["reason"])
        self.assertEqual(self.collector.rejected, 1)
        self.assertFalse(self.log.of("frontier"))

    def test_record_claimed_by_other_worker_is_rejected(self):
        entry = self.save("a-00", LADDER[3])
        index = self.run / "workers" / "b-00" / "records.jsonl"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(json.dumps({**entry, "worker": "b-00"}) + "\n")
        self.collector.collect()
        reasons = [e["reason"] for e in self.log.of("record_rejected")]
        self.assertTrue(any("binding" in r for r in reasons), reasons)

    def test_resume_pass_is_silent(self):
        self.save("a-00", LADDER[1])
        self.collector.collect(announce=False)
        self.assertFalse(self.log.of("frontier"))
        self.assertFalse(self.log.of("pool"))
        self.assertEqual(self.collector.frontier_summary()["toy4"][0]["gates"], 5)

    def test_fleet_diversity_and_collapse_alarm(self):
        for wid in ("a-00", "a-01"):
            self.save(wid, LADDER[3])                                      # identical bests
        self.collector.collect()
        snapshot = self.collector.fleet_diversity()["toy4"]
        self.assertEqual(snapshot["bests"]["mean"], 0.0)
        self.assertEqual(snapshot["distinct_best_dags"], 1)
        self.assertTrue(snapshot["alarm"])
        events = self.log.of("fleet_diversity")
        self.assertEqual(sorted(e["scope"] for e in events), ["bests", "chains"])
        bests = next(e for e in events if e["scope"] == "bests")
        self.assertEqual((bests["n"], bests["distinct"], bests["alarm"]), (2, 1, True))
        self.assertEqual(bests["workers"], ["a-00", "a-01"])
        self.assertEqual(len(self.log.of("collapse_alarm")), 1)
        self.collector.fleet_diversity()
        self.assertEqual(len(self.log.of("collapse_alarm")), 1)           # raised once, not every snapshot
        self.save("b-00", LADDER[2])
        snapshot = self.collector.fleet_diversity()["toy4"]
        self.assertGreater(snapshot["bests"]["mean"], 0.05)
        self.assertEqual(snapshot["bests"]["n"], 3)
        self.assertEqual(len(self.log.of("collapse_cleared")), 1)
        self.assertEqual(len(self.log.of("fleet_diversity")), 6)

    def test_campaign_clock_never_runs_backwards(self):
        # After a coordinator crash its status.json lags the workers'; resume continues from the
        # latest time any process wrote.
        atomic_json(self.run / "status.json", {"phase": "running", "t": 5.0})
        atomic_json(self.run / "workers" / "a-01" / "status.json", {"phase": "running", "t": 9.5})
        coordinator = Coordinator(self.run, resume=True, backend=self.backend)
        self.assertEqual(coordinator._previous_t(), 9.5)
        self.assertIsNone(Coordinator(self.run, resume=True, seconds=float("inf"),
                                      backend=self.backend).seconds)          # --seconds 0: unbounded

    def test_stub_diversity_matches_contract(self):
        d = pairwise([frozenset({1, 2}), frozenset({2, 3})])
        self.assertAlmostEqual(d["mean"], 1 - 1 / 3)
        self.assertEqual(pairwise([frozenset({1})])["mean"], 0.0)


if __name__ == "__main__":
    unittest.main()
