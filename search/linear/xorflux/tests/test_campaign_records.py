"""Record writing, recovery and independent re-verification."""
import json
import tempfile
import unittest
from pathlib import Path

from xorflux.campaign.checkpoint import (CheckpointError, append_jsonl, atomic_json, digest,
                                           load_checkpoint, read_json, read_jsonl, save_checkpoint)
from xorflux.campaign.records import RecordError, RecordWriter, check_record, circuit_values
from xorflux.tests.test_campaign_stub import LADDER, StubBackend, circuit, toy_target

SPEC = {"id": "w-00", "target": "toy4", "objective": "gates", "depth_cap": None, "gate_limit": None}
PLAN = {"run_id": "run1", "targets": {"toy4": {"matrix_sha256": toy_target().matrix_sha256}}}


def candidate(gates, **extra):
    """An engine on_record candidate (engine/loop.py shape)."""
    return {"ref": "w-00:1:7", "kind": "gates", "it": 7, "chain": 1, "root": "seed",
            "move": "walk.expand", "gates": gates, "outputs": None, **extra}


class RecordWriterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name)
        self.backend = StubBackend()
        self.target = toy_target()

    def tearDown(self):
        self.tmp.cleanup()

    def writer(self, spec=SPEC, strict=True, per_point=32):
        context = {"run_id": "run1", "worker": spec["id"], "group": "w", "target": "toy4",
                   "matrix_sha256": self.target.matrix_sha256}
        return RecordWriter(self.run / "workers" / spec["id"], self.run, context, self.backend, self.target,
                            spec, 4, per_point, strict, clock=lambda: 1.5)

    def index(self):
        return [e for e in read_jsonl(self.run / "workers" / "w-00" / "records.jsonl")[0] if "path" in e]

    def test_save_writes_all_files_and_index(self):
        writer = self.writer()
        summary = writer.save(candidate(LADDER[1]))
        self.assertEqual((summary["ok"], summary["saved"], summary["gate_count"]), (True, True, 5))
        entry = self.index()[0]
        self.assertEqual(summary["record"], entry["path"])
        path = self.run / entry["path"]
        self.assertTrue(path.with_suffix(".ncff").is_file())
        self.assertEqual(read_json(path.with_suffix(".verification.json"))["gate_count"], 5)
        data = read_json(path)
        self.assertEqual(data["gates"], LADDER[1])                      # old circuit format kept
        self.assertEqual(data["metadata"]["ref"], "w-00:1:7")            # join key to the dossier
        self.assertEqual(data["metadata"]["t"], 1.5)
        self.assertEqual((entry["gates"], entry["depth"], entry["move"], entry["chain"]), (5, 3, "walk.expand", 1))
        self.assertEqual(writer.best_values, circuit_values(circuit(LADDER[1]), 4))
        self.assertIsNone(check_record(self.run, entry, SPEC, PLAN, self.backend, self.target, deep=True)[1])

    def test_skips_are_ok_but_not_saved(self):
        writer = self.writer(per_point=1)
        self.assertIsNotNone(writer.add({"circuit": circuit(LADDER[2])}))       # 4@2
        dup = writer.save({"circuit": circuit(LADDER[2])})
        self.assertEqual((dup["ok"], dup["saved"], dup["skipped"]), (True, False, "duplicate"))
        self.assertIsNotNone(dup["record"])
        self.assertIsNone(writer.add({"circuit": circuit(LADDER[1])}))          # 5@3 dominated by 4@2
        self.assertIsNone(writer.add({"circuit": circuit(LADDER[2] + [[0, 2]])}))  # 5@2 dominated
        self.assertIsNotNone(writer.add({"circuit": circuit(LADDER[3])}))       # 3@3 new point
        same_dag = circuit([[1, 0], [2, 4], [3, 5]])                             # LADDER[3], other order
        self.assertIsNone(writer.add({"circuit": same_dag}))
        self.assertEqual(writer.skipped, {"duplicate": 2, "dominated": 2})
        self.assertEqual(writer.frontier(), [(3, 3), (4, 2)])
        self.assertEqual((writer.best["gates"], writer.best["depth"]), (3, 3))

    def test_over_cap_is_a_frontier_record_and_gate_limit_rejects(self):
        writer = self.writer({**SPEC, "depth_cap": 2, "gate_limit": 4})
        over_cap = writer.save({"circuit": circuit(LADDER[3])})                # depth 3 > cap 2
        self.assertEqual((over_cap["ok"], over_cap["saved"]), (True, True))
        self.assertIsNone(writer.best)            # the worker best stays within the real cap
        over_limit = writer.save({"circuit": circuit(LADDER[2] + [[0, 2], [1, 3]])})  # 6@2
        self.assertEqual((over_limit["ok"], over_limit["skipped"]), (False, "over_gate_limit"))

    def test_non_equivalent_record(self):
        bad = candidate([[0, 1], [4, 2]])
        with self.assertRaises(RecordError):
            self.writer().save(bad)
        lenient = self.writer(strict=False)
        result = lenient.save(bad)
        self.assertEqual((result["ok"], result["saved"]), (False, False))
        self.assertEqual(lenient.skipped, {"not_equivalent": 1})
        rejected, _ = read_jsonl(self.run / "workers" / "w-00" / "rejected.jsonl")
        self.assertEqual([r["ref"] for r in rejected], ["w-00:1:7", "w-00:1:7"])

    def test_recover_reindexes_committed_record(self):
        writer = self.writer()
        entry = writer.add({"circuit": circuit(LADDER[1])})
        orphan = self.run / "workers" / "w-00" / "records" / "g3-d3-manual.json"
        atomic_json(orphan, {**circuit(LADDER[3]), "metadata": {"kind": "gates"}})
        index = self.run / "workers" / "w-00" / "records.jsonl"
        index.write_text(index.read_text() + '{"torn":')                     # crash mid-append
        again = self.writer()
        self.assertEqual(len(again.entries), 2)
        self.assertTrue(orphan.with_suffix(".ncff").is_file())
        self.assertEqual((again.best["gates"], again.best["depth"]), (3, 3))
        lines, _ = read_jsonl(index)
        self.assertEqual(lines[0], entry)
        self.assertEqual(lines[1]["ev"], "truncated_line_recovered")

    def test_check_record_rejections(self):
        entry = self.writer().add({"circuit": circuit(LADDER[2])})
        path = self.run / entry["path"]
        self.assertIsNone(check_record(self.run, entry, SPEC, PLAN, self.backend, self.target)[1])
        # A record deeper than the worker's real cap is a valid frontier record.
        self.assertIsNone(check_record(self.run, entry, {**SPEC, "depth_cap": 1}, PLAN,
                                       self.backend, self.target)[1])
        _, reason = check_record(self.run, {**entry, "gates": 3}, SPEC, PLAN, self.backend, self.target)
        self.assertIn("differs from the index", reason)
        _, reason = check_record(self.run, {**entry, "path": "../x.json"}, SPEC, PLAN, self.backend, self.target)
        self.assertIn("escapes", reason)
        data = read_json(path)
        data["gates"][3] = [4, 2]
        path.write_text(json.dumps(data))
        _, reason = check_record(self.run, entry, SPEC, PLAN, self.backend, self.target)
        self.assertIn("hash", reason)


class CheckpointEnvelopeTest(unittest.TestCase):
    def test_binding_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            binding = {"run_id": "r", "worker": "w", "settings_sha256": "s"}
            save_checkpoint(path, binding, {"it": 3}, {"counters": {"steps": 3}})
            self.assertEqual(load_checkpoint(path, binding)["engine"], {"it": 3})
            with self.assertRaisesRegex(CheckpointError, "settings_sha256"):
                load_checkpoint(path, {**binding, "settings_sha256": "other"})
            data = read_json(path)
            data["engine"]["it"] = 4
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(CheckpointError, "hash"):
                load_checkpoint(path, binding)
            self.assertIsNone(load_checkpoint(Path(tmp) / "none.json", binding))
            self.assertEqual(digest({"b": 1, "a": 2}), digest({"a": 2, "b": 1}))

    def test_append_jsonl_partial_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.jsonl"
            append_jsonl(path, {"a": 1})
            with path.open("ab") as stream:
                stream.write(b'{"b": 2')                                     # writer mid-line
            lines, offset = read_jsonl(path)
            self.assertEqual(lines, [{"a": 1}])
            with path.open("ab") as stream:
                stream.write(b'}\n')
            more, _ = read_jsonl(path, offset)
            self.assertEqual(more, [{"b": 2}])


if __name__ == "__main__":
    unittest.main()
