"""One CPU-bound worker. Only the coordinator launches this module."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import signal
import time
import traceback

import runtime as rt


class Worker:
    def __init__(self, run_dir, label, owner_token):
        self.run_dir = Path(run_dir).resolve()
        self.config = rt.load_config(self.run_dir)
        self.config_hash = rt.digest(self.config)
        self.spec = next((s for s in self.config["workers"] if s["label"] == label), None)
        if self.spec is None:
            raise ValueError("Unknown worker")
        self.objective = self.spec.get("objective", "gates")
        self.label, self.token = label, owner_token
        selected_seed = self.config["targets"][self.spec["target_id"]]["seed_snapshots"][self.spec["seed_index"]]
        if "seed_sha256" in self.spec and self.spec["seed_sha256"] != selected_seed["sha256"]:
            raise ValueError("Worker seed binding mismatch")
        owner = rt.read_json(self.run_dir / "runner.lock", {})
        if owner.get("token") != owner_token or not rt.identity_alive(owner):
            raise RuntimeError("Worker has no live campaign owner")
        self.parent = owner
        self.directory = self.run_dir / "workers" / label
        self.directory.mkdir(parents=True, exist_ok=True)
        self.settings = self.config["settings"]
        self.target_api, self.engine_api = rt.api_modules()
        self.target = rt.read_json(self.run_dir / self.config["targets"][self.spec["target_id"]]["matrix_snapshot"]["path"])
        if self.target["id"] != self.spec["target_id"] or self.target["matrix_sha256"] != self.spec["matrix_sha256"]:
            raise ValueError("Worker target identity mismatch")
        if self.spec["cpu_id"] is not None:
            if not hasattr(os, "sched_setaffinity"):
                raise RuntimeError("CPU affinity unavailable on this host")
            os.sched_setaffinity(0, {self.spec["cpu_id"]})
        self.stop_requested = False
        self.last_status = self.last_owner_check = 0.0
        self.parent_ok = True
        self.started = time.monotonic()
        self.logger = logging.getLogger("search.worker." + label)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        for previous in list(self.logger.handlers):
            previous.close()
            self.logger.removeHandler(previous)
        handler = RotatingFileHandler(self.directory / "worker.log", maxBytes=self.settings["worker_log_bytes"],
                                      backupCount=self.settings["worker_log_backups"], encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        self.logger.addHandler(handler)
        saved = rt.read_json(self.directory / "checkpoint.json")
        self.chunk = 0
        self.next_engine = 0
        self.engine_states = {}
        self.frontier = []
        self.records = []
        self.candidate_origin = "seed_import"
        self.metrics = {}
        self.adopted_offer = None
        self.current_gates = None
        self.best = None
        self.chunk_start = None
        self.active_engine = None
        self.active_seed = None
        self.discovery_state = None
        if saved is not None:
            self.validate_state(saved)
            self.chunk = saved["chunk"]
            self.next_engine = saved["next_engine"]
            self.engine_states = saved["engine_states"]
            self.current_gates = saved["current_gates"]
            self.metrics = saved["metrics"]
            self.adopted_offer = saved.get("adopted_offer")
            self.check(self.current_gates)
            for engine, state in self.engine_states.items():
                if engine not in self.spec["engines"]:
                    raise ValueError("Checkpoint contains an unconfigured engine")
                self.check(state["gates"])
        else:
            seed = self.config["targets"][self.spec["target_id"]]["seed_snapshots"][self.spec["seed_index"]]
            self.current_gates = rt.read_json(self.run_dir / seed["path"])["gates"]
            self.check(self.current_gates)
        # Recover committed records even if a crash preceded the next trajectory checkpoint.
        for path in sorted((self.directory / "records").glob("*.json")):
            if path.name.endswith((".verification.json", ".rng-start.json")):
                continue
            circuit = rt.read_json(path)
            rt.validate_record_binding(self.run_dir, path, circuit, self.config, self.label)
            checked = self.check(circuit)
            rt.require_record_limits(checked, self.spec, path)
            record = self.record_summary(path, checked)
            self.frontier.append(record)
            self.records.append(record)
            # Complete a record interrupted between its atomic JSON and exports.
            rt.atomic_json(path.with_suffix(".verification.json"), checked)
            rt.atomic_bytes(path.with_suffix(".ncff"), self.target_api.ncff(circuit, self.target).encode())
        self.frontier = rt.nondominated(self.frontier)
        if self.frontier:
            self.best = min(self.frontier, key=self.score)
        else:
            if saved is not None:
                raise ValueError("Checkpoint exists but committed records are missing")
            self.candidate(self.current_gates, note="initial verified seed")
        self.candidate_origin = "new_search_record"
        self.write_frontier()
        self.save()
        captured_environment = {**rt.environment(), "process": rt.process_identity(),
                                "owner_token": self.token, "worker": self.spec}
        rt.atomic_json(self.directory / "environments" / (self.token + ".json"), captured_environment)
        rt.atomic_json(self.directory / "environment.json", captured_environment)

    def validate_state(self, state):
        expected = {"schema": rt.SCHEMA, "run_id": self.config["run_id"], "worker": self.label,
                    "target_id": self.spec["target_id"], "matrix_sha256": self.spec["matrix_sha256"],
                    "config_sha256": self.config_hash,
                    "source_manifest_sha256": self.config["source"]["manifest_sha256"],
                    **rt.search_binding(self.spec)}
        if any(state.get(k) != v for k, v in expected.items()):
            raise ValueError("Checkpoint target/config/source binding mismatch")
        supplied = state.get("checkpoint_sha256")
        if supplied != rt.digest({k: v for k, v in state.items() if k != "checkpoint_sha256"}):
            raise ValueError("Checkpoint hash mismatch")
        if not isinstance(state.get("engine_states"), dict) or not isinstance(state.get("chunk"), int):
            raise ValueError("Malformed checkpoint")

    def score(self, metrics):
        return rt.objective_key(metrics, self.objective)

    def check(self, circuit):
        if isinstance(circuit, list):
            circuit = {"gates": circuit}
        checked = self.target_api.verify(circuit, self.target, cap=self.spec["depth_cap"])
        if not checked["equivalent"]:
            raise ValueError("Circuit does not compute this target")
        return checked

    def record_summary(self, path, checked):
        return {"target_id": self.spec["target_id"], "matrix_sha256": self.spec["matrix_sha256"],
                "worker": self.label, **rt.search_binding(self.spec),
                "gate_count": checked["gate_count"], "depth": checked["depth"],
                "circuit_sha256": checked["circuit_sha256"],
                "exact_dag_sha256": (checked.get("dag_sha256") or checked["circuit_sha256"]), "path": path.relative_to(self.run_dir).as_posix(),
                "file_sha256": rt.file_hash(path)}

    def write_frontier(self):
        rt.atomic_json(self.directory / "frontier.json", {"target_id": self.spec["target_id"],
                       "matrix_sha256": self.spec["matrix_sha256"], "records": self.frontier})
        rt.atomic_json(self.directory / "collection.json", {"target_id": self.spec["target_id"], "records": self.records})
        if self.best:
            rt.atomic_json(self.directory / "best.json", rt.read_json(self.run_dir / self.best["path"]))

    def candidate(self, gates, note=None, metrics=None):
        self.metrics["candidates_verified"] = self.metrics.get("candidates_verified", 0) + 1
        normalized = self.target_api.normalise(gates, self.target)
        checked = self.check(normalized)
        pair = checked["gate_count"], checked["depth"]
        if not rt.within_gate_limit(checked, self.spec):
            self.metrics["record_gate_limit_rejections"] = self.metrics.get("record_gate_limit_rejections", 0) + 1
            return False
        better = self.best is None or self.score(checked) < self.score(self.best)
        baseline = [seed["verification"] for seed in self.config["targets"][self.spec["target_id"]]["seed_snapshots"]]
        if self.candidate_origin == "new_search_record" and any(
                b["gate_count"] <= pair[0] and b["depth"] <= pair[1] and
                (b["gate_count"], b["depth"]) != pair for b in baseline):
            return False
        if any(r["gate_count"] <= pair[0] and r["depth"] <= pair[1] and
               (r["gate_count"], r["depth"]) != pair for r in self.frontier):
            return False
        same_point = [r for r in self.records if (r["gate_count"], r["depth"]) == pair]
        dag_hash = (checked.get("dag_sha256") or checked["circuit_sha256"])
        if (any(r["exact_dag_sha256"] == dag_hash for r in same_point) or
                len(same_point) >= self.settings["equal_point_circuits"]):
            return better
        stem = f"g{pair[0]}-d{pair[1]}-{checked['circuit_sha256']}"
        path = self.directory / "records" / (stem + ".json")
        normalized["metadata"] = {"target_id": self.spec["target_id"], "matrix_sha256": self.spec["matrix_sha256"],
            "run_id": self.config["run_id"], "worker": self.label, "saved_utc": rt.utc_now(),
            "config_sha256": self.config_hash, "source_manifest_sha256": self.config["source"]["manifest_sha256"],
            **rt.search_binding(self.spec),
            "engine": self.active_engine if self.candidate_origin == "new_search_record" else None,
            "chunk": self.chunk, "note": note,
            "origin": self.candidate_origin,
            "verification_scope": "exact linear target matrix; affine output complements are excluded from XOR search",
            "affine_output_constants": self.target.get("affine_output_constants", [0] * self.target["output_count"]),
            "verifier_version": checked.get("verifier_version"),
            "verifier_sha256": checked.get("verifier_source_sha256", rt.file_hash(self.target_api.__file__)),
            "imported_seed": self.config["targets"][self.spec["target_id"]]["seed_snapshots"][self.spec["seed_index"]]
                             if self.candidate_origin == "seed_import" else None,
            "engine_metrics": metrics,
            "engine_seed": self.active_seed if self.candidate_origin == "new_search_record" else None,
            "shared_offer": self.chunk_start.get("offer") if self.chunk_start and self.candidate_origin == "shared_adoption" else None,
            "rng_state_at_discovery": self.discovery_state.get("rng_state") if self.discovery_state and self.candidate_origin == "new_search_record" else None,
            "rng_evidence": "Chunk-start state is saved beside this record; callback-time RNG state is not exposed; endpoint states are saved when available",
            "chunk_start_state_path": str(path.with_suffix(".rng-start.json").relative_to(self.run_dir))}
        rt.atomic_bytes(path.with_suffix(".ncff"), self.target_api.ncff(normalized, self.target).encode())
        rt.atomic_json(path.with_suffix(".verification.json"), checked)
        rng_start = {**(self.chunk_start or {"engine": None, "state": None,
                     "initial_seed": self.spec["random_seed"], "source": "initial seed"}),
                     "run_id": self.config["run_id"], "worker": self.label,
                     "target_id": self.spec["target_id"], "matrix_sha256": self.spec["matrix_sha256"],
                     "config_sha256": self.config_hash,
                     "source_manifest_sha256": self.config["source"]["manifest_sha256"],
                     **rt.search_binding(self.spec)}
        rt.atomic_json(path.with_suffix(".rng-start.json"), rng_start)
        # The circuit JSON is the commit marker: every referenced sidecar is durable first.
        rt.atomic_json(path, normalized)
        record = self.record_summary(path, checked)
        self.records.append(record)
        self.frontier = rt.nondominated(self.frontier + [record])
        self.best = min(self.frontier, key=self.score)
        self.write_frontier()
        rt.append_event(self.directory / "discoveries.jsonl", {"event": self.candidate_origin, "utc": rt.utc_now(),
                        "owner_token": self.token, "note": note, "chunk": self.chunk,
                        "engine": self.active_engine, "record": record})
        self.logger.info("%s gates=%d depth=%d engine=%s note=%s", self.candidate_origin, *pair, self.active_engine, note)
        return better

    def status(self, phase, error=None, force=False):
        now = time.monotonic()
        if not force and now - self.last_status < self.settings["status_interval_seconds"]:
            return
        self.last_status = now
        rt.atomic_json(self.directory / "status.json", {"phase": phase, "updated_utc": rt.utc_now(),
            "process": rt.process_identity(), "owner_token": self.token, "target_id": self.spec["target_id"],
            "matrix_sha256": self.spec["matrix_sha256"], "chunk": self.chunk,
            "engine": self.active_engine, "best": self.best, "metrics": self.metrics,
            "objective": self.objective, "gate_limit": self.spec.get("gate_limit"),
            "current_gate_count": len(self.current_gates),
            "current_within_record_gate_limit": rt.within_gate_limit({"gate_count": len(self.current_gates)}, self.spec),
            "elapsed_seconds": now - self.started, "error": error})

    def should_stop(self):
        now = time.monotonic()
        if self.stop_requested:
            return True
        if now - self.last_owner_check >= self.settings["parent_check_seconds"]:
            self.last_owner_check = now
            owner = rt.read_json(self.run_dir / "runner.lock", {})
            stop = rt.read_json(self.run_dir / "STOP", {})
            self.parent_ok = (owner.get("token") == self.token and rt.identity_alive(self.parent) and
                              stop.get("owner_token") != self.token)
        self.status("running")
        return not self.parent_ok

    def save(self):
        state = {"schema": rt.SCHEMA, "run_id": self.config["run_id"], "worker": self.label,
            "target_id": self.spec["target_id"], "matrix_sha256": self.spec["matrix_sha256"],
            "config_sha256": self.config_hash, "source_manifest_sha256": self.config["source"]["manifest_sha256"],
            "saved_utc": rt.utc_now(), "chunk": self.chunk, "next_engine": self.next_engine,
            "current_gates": self.current_gates, "engine_states": self.engine_states,
            "best": self.best, "frontier": self.frontier, "metrics": self.metrics,
            "adopted_offer": self.adopted_offer,
            "rng_algorithm": "CPython random.Random / MT19937", **rt.search_binding(self.spec),
            "current_gate_count": len(self.current_gates),
            "current_within_record_gate_limit": rt.within_gate_limit({"gate_count": len(self.current_gates)}, self.spec)}
        state["checkpoint_sha256"] = rt.digest(state)
        rt.atomic_json(self.directory / "checkpoint.json", state)

    def adopt(self):
        offer = rt.read_json(self.directory / "offer.json")
        if not rt.valid_offer(offer, self.config, self.spec, self.token):
            return
        if offer.get("offer_id") == self.adopted_offer:
            return
        if self.best and self.score(offer) >= self.score(self.best):
            return
        path = rt.safe_run_path(self.run_dir, offer["path"])
        if rt.file_hash(path) != offer["file_sha256"]:
            raise ValueError("Shared record hash drift")
        circuit = rt.read_json(path)
        donor = rt.validate_record_binding(self.run_dir, path, circuit, self.config, offer.get("worker"))
        if donor["target_id"] != self.spec["target_id"] or donor["matrix_sha256"] != self.spec["matrix_sha256"]:
            raise ValueError("Shared donor target mismatch")
        checked = self.check(circuit)
        if checked["gate_count"] != offer["gate_count"] or checked["depth"] != offer["depth"]:
            raise ValueError("Shared record metric mismatch")
        self.current_gates = circuit["gates"]
        self.engine_states = {}  # A reseed is deliberate, never mistaken for exact continuation.
        self.adopted_offer = offer["offer_id"]
        self.chunk_start = {"source": "shared adoption", "offer": offer, "state": None}
        previous_origin = self.candidate_origin
        self.candidate_origin = "shared_adoption"
        self.candidate(self.current_gates, "same-target shared record")
        self.candidate_origin = previous_origin
        rt.append_event(self.directory / "discoveries.jsonl", {"event": "shared_adoption",
                        "utc": rt.utc_now(), "offer": offer, "engine_states_reset": True})
        self.save()

    def run(self):
        def stop(signum, frame):
            self.stop_requested = True
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        self.status("running", force=True)
        try:
            while not self.should_stop():
                self.adopt()
                index = self.next_engine % len(self.spec["engines"])
                engine = self.spec["engines"][index]
                self.active_engine = engine
                self.active_seed = self.spec["random_seed"] + index * 104729
                prior = self.engine_states.get(engine)
                gates = prior["gates"] if prior else self.current_gates
                fresh_seed_record = None
                if prior is None and not rt.within_gate_limit({"gate_count": len(gates)}, self.spec):
                    # A new engine needs a feasible incumbent; existing engines resume their honest uphill state.
                    fresh_seed_record = self.best["path"]
                    gates = rt.read_json(self.run_dir / fresh_seed_record)["gates"]
                state = prior["state"] if prior else None
                self.discovery_state = None
                self.chunk_start = {"engine": engine, "engine_seed": self.active_seed, "chunk": self.chunk,
                                    "gates": gates, "state": state, "fresh_seed_record": fresh_seed_record, "target_id": self.spec["target_id"],
                                    "matrix_sha256": self.spec["matrix_sha256"], **rt.search_binding(self.spec)}
                rt.atomic_json(self.directory / "chunk-start.json", self.chunk_start)
                objective_options = {"objective": self.objective, "gate_limit": self.spec.get("gate_limit")} if (
                    self.objective != "gates" or self.spec.get("gate_limit") is not None) else {}
                result = self.engine_api.run_chunk(self.target, engine, gates, seed=self.active_seed,
                    seconds=self.settings["chunk_seconds"], depth_cap=self.spec["depth_cap"], state=state,
                    knobs=self.spec["engine_knobs"][engine], on_candidate=self.candidate, should_stop=self.should_stop,
                    **objective_options)
                self.check(result["gates"])
                self.current_gates = result["gates"]
                self.engine_states[engine] = {"gates": result["gates"], "state": result["state"]}
                self.metrics[engine] = result.get("metrics", {})
                self.discovery_state = result["state"]
                self.candidate(self.current_gates, "chunk endpoint", result.get("metrics"))
                self.discovery_state = None
                self.chunk += 1
                self.next_engine = (index + 1) % len(self.spec["engines"])
                self.save()
                self.status("running", force=True)
            self.save()
            self.status("stopped", force=True)
            return 0
        except BaseException as exc:
            self.logger.exception("Worker failed")
            rt.atomic_json(self.directory / "error.json", {"utc": rt.utc_now(), "type": type(exc).__name__,
                           "message": str(exc), "traceback": traceback.format_exc(), "chunk": self.chunk,
                           "engine": self.active_engine, "owner_token": self.token})
            self.status("failed", str(exc), force=True)
            return 1
        finally:
            for handler in list(self.logger.handlers):
                handler.close()
                self.logger.removeHandler(handler)
