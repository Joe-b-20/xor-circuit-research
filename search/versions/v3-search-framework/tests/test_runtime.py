"""Durability and isolation tests. No long campaigns or 20-worker launches."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime as rt
import target as real_target
from worker import Worker
import run as campaign


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "search"
        self.root.mkdir()
        self.run = Path(self.temporary.name) / "campaign"
        self.gates = [[0, 1], [2, 3]]
        self.definition = {"id": "toy", "input_count": 3, "output_count": 1, "rows": [7],
                           "matrix_sha256": real_target.matrix_sha256(3, [7]),
                           "seeds": [{"path": "seed.json", "gates": 2, "depth": 2}]}
        rt.atomic_json(self.root / "seed.json", real_target.normalise(self.gates, self.definition))
        (self.root / "README.md").write_text("fixture source\n")
        (self.root / "LICENSE").write_text("fixture license\n")
        (self.root / "runs" / "old").mkdir(parents=True)
        (self.root / "runs" / "old" / "ignored.py").write_text("not source\n")
        self.target_api = types.SimpleNamespace(load_target=lambda value: dict(self.definition),
            verify=real_target.verify, normalise=real_target.normalise, ncff=real_target.ncff,
            __file__=real_target.__file__)
        self.engines = types.SimpleNamespace(available_engines=lambda: ["test"],
            effective_knobs=lambda name, overrides: {"all_defaults": 1, **overrides},
            engine_applicability=lambda *args, **kwargs: {"applicable": True, "reason": "fixture"})
        self.patches = [patch.object(rt, "SEARCH_ROOT", self.root),
                        patch.object(rt, "api_modules", return_value=(self.target_api, self.engines))]
        for item in self.patches:
            item.start()
        self.owner = None
        self.worker_objects = []

    def tearDown(self):
        for worker in self.worker_objects:
            for handler in list(worker.logger.handlers):
                handler.close()
                worker.logger.removeHandler(handler)
        if self.owner:
            rt.release_lock(self.run, self.owner)
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    def prepare(self, **overrides):
        return rt.prepare(self.run, {"allocation": {"toy": 1}, "chunk_seconds": .02, **overrides})

    def worker(self):
        if not self.owner:
            self.owner = rt.take_lock(self.run)
        worker = Worker(self.run, "toy-00", self.owner["token"])
        self.worker_objects.append(worker)
        return worker

    def test_prepare_freezes_all_defaults_without_workers_and_excludes_runs(self):
        plan = self.prepare()
        self.assertEqual(plan["settings"]["equal_point_circuits"], 32)
        self.assertIsNone(plan["settings"]["session_seconds"])
        self.assertEqual(plan["workers"][0]["engine_knobs"], {"test": {"all_defaults": 1}})
        self.assertEqual(rt.load_config(self.run), plan)
        self.assertFalse((self.run / "workers").exists())
        self.assertIn("README.md", plan["source"]["files"])
        self.assertIn("LICENSE", plan["source"]["files"])
        self.assertFalse(any(name.startswith("runs/") for name in plan["source"]["files"]))
        self.assertFalse(plan["source"]["commit_is_exact_snapshot"])

    def test_source_matrix_and_seed_drift_are_rejected(self):
        plan = self.prepare()
        snapshot = self.run / "source" / "search" / "README.md"
        original = snapshot.read_bytes()
        snapshot.write_text("changed")
        with self.assertRaisesRegex(ValueError, "Source snapshot hash drift"):
            rt.load_config(self.run)
        snapshot.write_bytes(original)
        seed = self.run / plan["targets"]["toy"]["seed_snapshots"][0]["path"]
        seed.write_text("{}")
        with self.assertRaisesRegex(ValueError, "Target/seed snapshot hash drift"):
            rt.load_config(self.run)

    def test_atomic_failure_preserves_previous_state_and_cleans_temporary(self):
        path = self.root / "atomic.json"
        rt.atomic_json(path, {"old": True})
        with patch.object(rt.os, "replace", side_effect=OSError("fixture disk failure")):
            with self.assertRaises(OSError):
                rt.atomic_json(path, {"new": True})
        self.assertEqual(rt.read_json(path), {"old": True})
        self.assertEqual(list(self.root.glob(".atomic.json.*")), [])

    def test_truncated_event_tail_is_recovered(self):
        path = self.root / "events.jsonl"
        rt.append_event(path, {"event": "saved"})
        with path.open("ab") as stream:
            stream.write(b'{"event":"cut')
        rt.append_event(path, {"event": "after"})
        events = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([e["event"] for e in events], ["saved", "truncated_event_recovered", "after"])

    def test_concurrent_stale_lock_reclaim_has_one_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        self.prepare()
        rt.atomic_json(self.run / "runner.lock", {**rt.process_identity(), "pid": 2147483647})
        barrier = threading.Barrier(2)
        def claim():
            barrier.wait()
            try:
                return rt.take_lock(self.run)
            except RuntimeError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        owners = [value for value in results if value is not None]
        self.assertEqual(len(owners), 1)
        self.owner = owners[0]
        self.assertEqual(rt.read_json(self.run / "runner.lock")["token"], self.owner["token"])

    def test_exclusive_lock_and_pid_identity(self):
        self.prepare()
        self.owner = rt.take_lock(self.run)
        with self.assertRaisesRegex(RuntimeError, "live coordinator"):
            rt.take_lock(self.run)
        wrong = {**rt.process_identity(), "start_ticks": "impossible"}
        if rt.process_identity()["start_ticks"] is not None:
            self.assertFalse(rt.identity_alive(wrong))

    def test_offer_requires_same_target_matrix_config_and_session(self):
        config = self.prepare()
        spec = config["workers"][0]
        offer = {"owner_token": "session", "run_id": config["run_id"], "target_id": "toy",
                 "matrix_sha256": spec["matrix_sha256"], "config_sha256": rt.digest(config), "depth": 2}
        self.assertTrue(rt.valid_offer(offer, config, spec, "session"))
        for field in ("target_id", "matrix_sha256", "config_sha256", "owner_token", "run_id"):
            self.assertFalse(rt.valid_offer({**offer, field: "other"}, config, spec, "session"), field)
        self.assertFalse(rt.valid_offer({**offer, "depth": 3}, config, spec, "session"))

    def test_resume_uses_actual_engine_state_and_current_not_best(self):
        self.prepare()
        first = self.worker()
        trajectory = self.gates + [[0, 2]]  # Useful exploratory gate remains outside the live best DAG.
        seen = []
        def chunk(target, engine, gates, *, seed, seconds, depth_cap, state, knobs, on_candidate, should_stop):
            seen.append((gates, state))
            active.stop_requested = True
            return {"gates": trajectory, "state": {"rng_state": [3, [10, 20], None],
                    "iterations": (state or {}).get("iterations", 0) + 1}, "metrics": {"moves": 1}}
        self.engines.run_chunk = chunk
        active = first
        self.assertEqual(active.run(), 0)
        checkpoint = rt.read_json(first.directory / "checkpoint.json")
        self.assertEqual(len(checkpoint["current_gates"]), 3)
        self.assertEqual(rt.read_json(first.directory / "best.json")["gateCount"], 2)
        active = self.worker()
        self.assertEqual(active.run(), 0)
        self.assertEqual(seen[1][0], trajectory)
        self.assertEqual(seen[1][1]["iterations"], 1)
        self.assertEqual(rt.read_json(active.directory / "checkpoint.json")["engine_states"]["test"]["state"]["iterations"], 2)

    def test_checkpoint_corruption_and_target_rebinding_rejected(self):
        self.prepare()
        worker = self.worker()
        path = worker.directory / "checkpoint.json"
        original = rt.read_json(path)
        changed = {**original, "chunk": 100}
        rt.atomic_json(path, changed)
        with self.assertRaisesRegex(ValueError, "Checkpoint hash mismatch"):
            self.worker()
        changed = {**original, "target_id": "other"}
        changed["checkpoint_sha256"] = rt.digest({k: v for k, v in changed.items() if k != "checkpoint_sha256"})
        rt.atomic_json(path, changed)
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.worker()

    def test_import_labels_and_equal_point_diversity_limit(self):
        self.prepare(equal_point_circuits=1)
        worker = self.worker()
        events = [json.loads(line) for line in (worker.directory / "discoveries.jsonl").read_text().splitlines()]
        self.assertEqual(events[0]["event"], "seed_import")
        record = rt.read_json(self.run / worker.records[0]["path"])
        self.assertEqual(record["metadata"]["origin"], "seed_import")
        self.assertIsNotNone(record["metadata"]["imported_seed"])
        worker.candidate([[1, 2], [0, 3]], "alternate equal objective")
        self.assertEqual(len(worker.records), 1)

    def test_recovery_and_collection_reject_foreign_campaign_records_before_repair(self):
        config = self.prepare()
        worker = self.worker()
        path = self.run / worker.records[0]["path"]
        original = rt.read_json(path)
        for field in ("run_id", "worker", "config_sha256", "source_manifest_sha256"):
            changed = {**original, "metadata": {**original["metadata"], field: "foreign"}}
            rt.atomic_json(path, changed)
            rt.atomic_json(path.with_suffix(".verification.json"), {"must_not_be_rewritten": True})
            with self.assertRaisesRegex(ValueError, "provenance binding"):
                self.worker()
            self.assertEqual(rt.read_json(path.with_suffix(".verification.json")), {"must_not_be_rewritten": True})
            row = {**worker.records[0], "file_sha256": rt.file_hash(path)}
            rt.atomic_json(worker.directory / "frontier.json", {"target_id": "toy",
                "matrix_sha256": worker.spec["matrix_sha256"], "records": [row]})
            with self.assertRaisesRegex(ValueError, "provenance binding"):
                campaign.collect(self.run, config, self.owner["token"], {})
        rt.atomic_json(path, original)

    def test_valid_recovery_repairs_exports_but_requires_rng_evidence(self):
        self.prepare()
        worker = self.worker()
        path = self.run / worker.records[0]["path"]
        path.with_suffix(".verification.json").unlink()
        path.with_suffix(".ncff").unlink()
        recovered = self.worker()
        self.assertTrue(path.with_suffix(".verification.json").exists())
        self.assertTrue(path.with_suffix(".ncff").exists())
        rng_path = path.with_suffix(".rng-start.json")
        rng = rt.read_json(rng_path)
        for field in ("run_id", "worker", "config_sha256", "source_manifest_sha256"):
            rt.atomic_json(rng_path, {**rng, field: "foreign"})
            with self.assertRaisesRegex(ValueError, "RNG evidence"):
                self.worker()
        rt.atomic_json(rng_path, rng)
        rng_path.unlink()
        with self.assertRaisesRegex(ValueError, "RNG evidence"):
            self.worker()

    def test_resume_with_missing_authoritative_records_rejected(self):
        self.prepare()
        worker = self.worker()
        for record in worker.records:
            (self.run / record["path"]).unlink()
        with self.assertRaisesRegex(ValueError, "committed records are missing"):
            self.worker()

    def test_adoption_uses_donor_worker_binding(self):
        config = self.prepare(allocation={"toy": 2})
        donor = self.worker()
        recipient = Worker(self.run, "toy-01", self.owner["token"])
        self.worker_objects.append(recipient)
        record = donor.records[0]
        offer = {**record, "owner_token": self.owner["token"], "run_id": config["run_id"],
                 "config_sha256": rt.digest(config), "offer_id": "valid-donor"}
        recipient.best = {**recipient.best, "gate_count": 3}
        rt.atomic_json(recipient.directory / "offer.json", offer)
        recipient.adopt()
        self.assertEqual(recipient.adopted_offer, "valid-donor")
        recipient.best = {**recipient.best, "gate_count": 3}
        rt.atomic_json(recipient.directory / "offer.json", {**offer, "worker": recipient.label,
                                                          "offer_id": "wrong-donor"})
        with self.assertRaisesRegex(ValueError, "provenance path"):
            recipient.adopt()

    def test_stop_survives_damaged_or_missing_configuration(self):
        self.prepare()
        self.owner = rt.take_lock(self.run)
        (self.run / "config.json").write_text("damaged")
        stopped = campaign.request_stop(self.run)
        self.assertEqual(stopped["owner_token"], self.owner["token"])
        with self.assertRaises(ValueError):
            rt.load_config(self.run)
        (self.run / "config.json").unlink()
        stopped = campaign.request_stop(self.run)
        self.assertEqual(stopped["owner_token"], self.owner["token"])

    def depth_fixture(self, gate_limit=3, workers=1):
        self.gates = [[0, 1], [2, 4], [3, 5]]
        self.definition = {"id": "toy", "input_count": 4, "output_count": 2, "rows": [15, 7],
                           "matrix_sha256": real_target.matrix_sha256(4, [15, 7]),
                           "seeds": [{"path": "seed.json", "gates": 3, "depth": 3,
                                      "source_kind": "official fixture"}]}
        source = real_target.normalise(self.gates, self.definition)
        source["metadata"] = {"source": "local test discovery"}
        rt.atomic_json(self.root / "local.json", source)
        self.depth_settings = {"allocation": {"toy": workers}, "target_overrides": {"toy": {
            "seed_paths": ["local.json"], "objective": "depth_then_gates", "gate_limit": gate_limit,
            "cap_cycle": [3]}}}
        self.shallow_gates = [[0, 1], [2, 3], [4, 5], [2, 4]]
        return self.prepare(**self.depth_settings)

    def test_target_specific_seed_objective_and_limits_are_resolved_and_bound(self):
        config = self.depth_fixture()
        spec = config["workers"][0]
        self.assertEqual((spec["objective"], spec["gate_limit"], spec["depth_cap"]), ("depth_then_gates", 3, 3))
        seed = config["targets"]["toy"]["seed_snapshots"][0]
        self.assertEqual(seed["source_path"], "local.json")
        self.assertEqual(seed["source_kind"], "explicit local circuit")
        self.assertEqual(seed["source_metadata"], {"source": "local test discovery"})
        self.assertEqual(spec["seed_sha256"], seed["sha256"])
        worker = self.worker()
        checkpoint = rt.read_json(worker.directory / "checkpoint.json")
        for field in ("objective", "gate_limit", "seed_sha256"):
            self.assertEqual(checkpoint[field], spec[field])
            corrupted = {**checkpoint, field: "wrong"}
            corrupted["checkpoint_sha256"] = rt.digest({k: v for k, v in corrupted.items() if k != "checkpoint_sha256"})
            with self.assertRaisesRegex(ValueError, "binding mismatch"):
                worker.validate_state(corrupted)

    def test_shallower_over_budget_program_is_not_a_record_but_trajectory_is_honest(self):
        self.depth_fixture(gate_limit=3)
        worker = self.worker()
        self.assertFalse(worker.candidate(self.shallow_gates, "shallower but four gates"))
        self.assertEqual(len(worker.records), 1)
        self.assertEqual((worker.best["gate_count"], worker.best["depth"]), (3, 3))
        worker.current_gates = self.shallow_gates
        worker.save()
        checkpoint = rt.read_json(worker.directory / "checkpoint.json")
        self.assertEqual(checkpoint["current_gate_count"], 4)
        self.assertFalse(checkpoint["current_within_record_gate_limit"])
        self.assertFalse(any(json.loads(line)["event"] == "new_search_record" for line in
                             (worker.directory / "discoveries.jsonl").read_text().splitlines()))
        recovered = self.worker()
        self.assertEqual(len(recovered.current_gates), 4)
        self.assertEqual(recovered.best["gate_count"], 3)

    def test_depth_objective_prefers_and_shares_shallower_feasible_higher_gate_point(self):
        config = self.depth_fixture(gate_limit=4, workers=2)
        donor = self.worker()
        recipient = Worker(self.run, "toy-01", self.owner["token"])
        self.worker_objects.append(recipient)
        recipient.status("running", force=True)
        self.assertTrue(donor.candidate(self.shallow_gates, "feasible depth improvement"))
        self.assertEqual((donor.best["gate_count"], donor.best["depth"]), (4, 2))
        campaign.collect(self.run, config, self.owner["token"], {})
        offer = rt.read_json(recipient.directory / "offer.json")
        self.assertEqual((offer["gate_count"], offer["depth"]), (4, 2))
        recipient.adopt()
        self.assertEqual((recipient.best["gate_count"], recipient.best["depth"]), (4, 2))
        # Gate-first remains unchanged for existing plans.
        self.assertLess(rt.objective_key({"gate_count": 3, "depth": 3}),
                        rt.objective_key({"gate_count": 4, "depth": 2}))

    def test_forged_same_binding_over_limit_record_is_rejected_everywhere(self):
        config = self.depth_fixture(gate_limit=3)
        worker = self.worker()
        original_path = self.run / worker.records[0]["path"]
        original = rt.read_json(original_path)
        forged = real_target.normalise(self.shallow_gates, self.definition)
        checked = real_target.verify(forged, self.definition)
        self.assertEqual((checked["gate_count"], checked["depth"]), (4, 2))
        path = worker.directory / "records" / "forged-same-binding.json"
        forged["metadata"] = {**original["metadata"],
            "chunk_start_state_path": path.with_suffix(".rng-start.json").relative_to(self.run).as_posix()}
        rt.atomic_json(path.with_suffix(".rng-start.json"), rt.read_json(original_path.with_suffix(".rng-start.json")))
        rt.atomic_json(path.with_suffix(".verification.json"), checked)
        rt.atomic_bytes(path.with_suffix(".ncff"), real_target.ncff(forged, self.definition).encode())
        rt.atomic_json(path, forged)
        with self.assertRaisesRegex(ValueError, "Retained record exceeds gate_limit"):
            self.worker()
        row = worker.record_summary(path, checked)
        rt.atomic_json(worker.directory / "frontier.json", {"target_id": "toy",
            "matrix_sha256": worker.spec["matrix_sha256"], "records": [row]})
        with self.assertRaisesRegex(ValueError, "Retained record exceeds gate_limit"):
            campaign.collect(self.run, config, self.owner["token"], {})
        with self.assertRaisesRegex(ValueError, "Retained record exceeds gate_limit"):
            campaign.verify_run(self.run)
        # The same valid exploratory program remains permissible in a checkpoint.
        path.unlink()
        worker.current_gates = self.shallow_gates
        worker.save()
        self.assertEqual(len(self.worker().current_gates), 4)

    def test_new_engine_gets_feasible_best_when_current_trajectory_exceeds_gate_limit(self):
        self.depth_fixture(gate_limit=3)
        worker = self.worker()
        worker.current_gates = self.shallow_gates
        received = []
        def chunk(target, engine, gates, **options):
            received.append((gates, options))
            worker.stop_requested = True
            return {"gates": gates, "state": {"rng_state": [3, [10], None]}, "metrics": {}}
        self.engines.run_chunk = chunk
        self.assertEqual(worker.run(), 0)
        self.assertEqual(len(received[0][0]), 3)
        self.assertEqual(received[0][1]["objective"], "depth_then_gates")
        self.assertEqual(received[0][1]["gate_limit"], 3)

    def test_explicit_seed_must_fit_gate_limit_and_stay_inside_source_tree(self):
        self.depth_fixture(gate_limit=3)
        overrides = {**self.depth_settings, "target_overrides": {"toy": {
            **self.depth_settings["target_overrides"]["toy"], "gate_limit": 2}}}
        with self.assertRaisesRegex(ValueError, "Initial seed exceeds gate_limit"):
            rt.resolve_plan(overrides)
        overrides["target_overrides"]["toy"]["gate_limit"] = 3
        overrides["target_overrides"]["toy"]["seed_paths"] = [str(self.root / "local.json")]
        with self.assertRaisesRegex(ValueError, "Seed path escapes"):
            rt.resolve_plan(overrides)

    def test_oversubscription_requires_explicit_override(self):
        with patch.object(rt, "environment", return_value={"available_cpu_ids": [0]}):
            with self.assertRaisesRegex(ValueError, "exceeds available CPUs"):
                rt.resolve_plan({"allocation": {"toy": 2}})
            plan = rt.resolve_plan({"allocation": {"toy": 2}, "allow_oversubscription": True})
            self.assertEqual(len(plan["workers"]), 2)


class SubprocessSmokeTests(unittest.TestCase):
    def test_new_profile_and_old_default_plans(self):
        profile = rt.read_json(rt.SEARCH_ROOT / "configs" / "joltik-depth-foxmu8-15.json")
        if not (rt.SEARCH_ROOT / "targets" / "fox_mu8.json").exists():
            self.skipTest("FOX Mu8 target not yet installed")
        plan = rt.resolve_plan(profile)
        self.assertEqual(len(plan["workers"]), 15)
        joltik = [worker for worker in plan["workers"] if worker["target_id"] == "joltik"]
        fox = [worker for worker in plan["workers"] if worker["target_id"] == "fox_mu8"]
        self.assertEqual((len(joltik), len(fox)), (5, 10))
        self.assertTrue(all(worker["objective"] == "depth_then_gates" and worker["gate_limit"] == 43 and
                            worker["depth_cap"] == 8 for worker in joltik))
        self.assertEqual(plan["targets"]["joltik"]["seeds"][0]["verification"]["gate_count"], 43)
        self.assertEqual(plan["targets"]["joltik"]["seeds"][0]["verification"]["depth"], 8)
        self.assertIn("not NIST", plan["targets"]["joltik"]["seeds"][0]["source_kind"])
        self.assertIsNotNone(plan["targets"]["joltik"]["seeds"][0]["source_provenance"])
        self.assertEqual(plan["targets"]["fox_mu8"]["definition"]["input_count"], 64)
        self.assertEqual(plan["targets"]["fox_mu8"]["seeds"][0]["verification"]["gate_count"], 540)
        self.assertEqual([worker["depth_cap"] for worker in fox], [14, 15, None, 14, 15, None, 14, 15, None, 14])
        self.assertEqual(fox[0]["engine_knobs"]["v2-lns"]["proposal_seconds"], .2)
        self.assertEqual(fox[0]["engine_knobs"]["v3-component"]["move_knobs"]["max_seconds"], .2)
        old_plan = rt.resolve_plan(rt.read_json(rt.SEARCH_ROOT / "configs" / "default20.json"))
        self.assertEqual(len(old_plan["workers"]), 20)
        self.assertTrue(all(worker["objective"] == "gates" and worker["gate_limit"] is None for worker in old_plan["workers"]))

    def test_short_worker_resume_and_exports(self):
        import subprocess
        if not (rt.SEARCH_ROOT / "targets" / "joltik.json").exists():
            self.skipTest("Built-in target fixtures not yet installed")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "run"
            rt.prepare(directory, {"allocation": {"joltik": 1}, "engines": ["legacy-walk"],
                                  "chunk_seconds": .025, "parent_check_seconds": .02,
                                  "stop_grace_seconds": 3.0})
            script = rt.SEARCH_ROOT / "run.py"
            for resume in (False, True):
                command = [sys.executable, str(script), "run", str(directory), "--seconds", ".35"]
                if resume:
                    command.append("--resume")
                process = subprocess.run(command, capture_output=True, text=True, timeout=15)
                self.assertEqual(process.returncode, 0, process.stderr)
                state = rt.read_json(directory / "workers" / "joltik-00" / "checkpoint.json")
                self.assertGreater(state["chunk"], 0)
                if not resume:
                    first_chunks = state["chunk"]
                else:
                    self.assertGreater(state["chunk"], first_chunks)
            checked = subprocess.run([sys.executable, str(script), "verify-run", str(directory)],
                                     capture_output=True, text=True, timeout=15)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertTrue(json.loads(checked.stdout)["verified"])
            self.assertFalse((directory / "runner.lock").exists())
            self.assertEqual(len(list((directory / "sessions").glob("*.json"))), 2)
            self.assertEqual(len(list((directory / "workers" / "joltik-00" / "launchers").glob("*.log"))), 2)


if __name__ == "__main__":
    unittest.main()
