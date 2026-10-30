"""One worker process: a single search chain with checkpoints, verified records and sharing.

The coordinator starts ``python -P -m xorflux _worker RUN_DIR WORKER_ID TOKEN`` with the frozen
source on ``PYTHONPATH``.  The worker

1. loads its plan entry, frozen settings (hash-checked) and target snapshot;
2. builds Objective, Recorder, RecordWriter and Pool, then a fresh Engine from its seed, or
   ``Engine.resume`` from ``checkpoint.json`` when one exists (bound to run, worker, settings and
   source; any mismatch refuses to resume);
3. drives ``engine.step()`` until stopped, writing ``status.json`` + ``chain.json`` every
   ``worker.status_seconds`` and an atomic checkpoint every ``worker.checkpoint_seconds``;
4. stops cleanly on SIGINT/SIGTERM/SIGHUP, a ``STOP`` addressed to its coordinator's token, or loss of its
   coordinator (lock gone or owner dead), always writing a final checkpoint; on a crash it writes
   ``error.json`` and exits non-zero.

The worker drives ``step()`` itself rather than ``Engine.run(stop)`` so checkpoints and status
writes happen only between whole proposals; a stop request waits for the current step.

``xorflux quick`` runs the same class in-process with a deadline instead of a coordinator.
"""
from __future__ import annotations

import os
import signal
import time
import traceback
from pathlib import Path

from ..config.schema import Knob, Section
from .checkpoint import (STOP_SIGNALS, CampaignLock, atomic_json, digest, identity_alive,
                         load_checkpoint, process_identity, read_json, save_checkpoint,
                         stop_requested, utc_now)
from .freeze import frozen_settings, frozen_target, load_plan
from .records import RecordWriter, load_backend
from .sharing import NullPool, Pool

KNOBS = Section("worker", "Worker process: checkpoints, status and record policy.", {
    "checkpoint_seconds": Knob(60.0, "Seconds between atomic engine checkpoints (a crash loses at "
                               "most this much search; records are saved immediately).", min=1),
    "status_seconds": Knob(2.0, "Seconds between status.json / chain.json writes.", min=0.1),
    "owner_check_seconds": Knob(1.0, "Seconds between checks that the coordinator is alive and has "
                                "not asked this worker to stop.", min=0.05),
    "records_per_point": Knob(32, "Distinct DAGs a worker saves per (gates, depth) point.", min=1),
    "strict_verify": Knob(True, "A record the independent verifier rejects stops the worker "
                          "(an engine bug); false only rejects it (logged to rejected.jsonl)."),
})


# --------------------------------------------------------------------------------------------
# Who decides when the worker stops
# --------------------------------------------------------------------------------------------
class CoordinatorLink:
    """Ties a worker to its coordinator session: shared campaign clock and stop conditions."""

    def __init__(self, run_dir: Path, token: str):
        self.run_dir = Path(run_dir)
        self.token = token
        lock = CampaignLock(run_dir).read()
        if lock.get("token") != token or not identity_alive(lock):
            raise RuntimeError("worker has no live coordinator with this token; "
                               "workers are started only by `xorflux run/resume`")
        self.owner = lock
        session = read_json(self.run_dir / "sessions" / f"{token}.json", {}) or {}
        # CLOCK_MONOTONIC is system-wide on Linux, so the coordinator's t0 is valid here.
        self.t0 = session.get("t0", time.monotonic())

    def clock(self) -> float:
        """Seconds since campaign start (continues across resumed sessions)."""
        return time.monotonic() - self.t0

    def lost(self) -> str | None:
        """Reason to stop, or None while the coordinator wants this worker running."""
        stop = stop_requested(self.run_dir, self.token)
        if stop:
            return f"stop requested: {stop.get('reason', '')}"
        if CampaignLock(self.run_dir).read().get("token") != self.token:
            return "campaign lock lost"
        if not identity_alive(self.owner):
            return "coordinator died"
        return None


class DeadlineLink:
    """Standalone worker (``xorflux quick``): stops after ``seconds`` (None = until Ctrl-C)."""

    def __init__(self, seconds: float | None):
        self.t0 = time.monotonic()
        self.deadline = None if seconds is None else self.t0 + seconds
        self.token = "standalone"

    def clock(self) -> float:
        """Seconds since start."""
        return time.monotonic() - self.t0

    def lost(self) -> str | None:
        """'duration elapsed' once past the deadline."""
        if self.deadline is not None and time.monotonic() >= self.deadline:
            return "duration elapsed"
        return None


# --------------------------------------------------------------------------------------------
# Worker
# --------------------------------------------------------------------------------------------
class WorkerProcess:
    """Everything one worker owns; ``run()`` is the process main loop."""

    def __init__(self, run_dir: str | Path, worker_id: str, link, backend=None, standalone_pool=False):
        self.run_dir = Path(run_dir).resolve()
        self.plan = load_plan(self.run_dir)
        spec = next((w for w in self.plan["workers"] if w["id"] == worker_id), None)
        if spec is None:
            raise ValueError(f"no worker {worker_id!r} in this plan")
        self.spec = spec
        self.link = link
        self.backend = backend or load_backend(self.plan["backend"])
        self.settings = frozen_settings(self.run_dir, spec["settings"], self.backend.schema(),
                                        spec["settings_sha256"])
        self.cfg = self.settings.view("worker")
        self.target_info = self.plan["targets"][spec["target"]]
        self.target = frozen_target(self.run_dir, self.plan, spec["target"], self.backend)
        self.dir = self.run_dir / "workers" / worker_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.binding = {"run_id": self.plan["run_id"], "worker": worker_id,
                        "plan_sha256": digest(self.plan), "settings_sha256": spec["settings_sha256"],
                        "source_manifest_sha256": self.plan.get("source_manifest_sha256"),
                        "matrix_sha256": self.target_info["matrix_sha256"]}
        context = {**self.binding, "group": spec["group"], "target": spec["target"],
                   "objective": spec["objective"], "depth_cap": spec["depth_cap"],
                   "gate_limit": spec["gate_limit"]}
        self.writer = RecordWriter(self.dir, self.run_dir, context, self.backend, self.target, spec,
                                   self.target_info["input_count"], self.cfg.records_per_point,
                                   self.cfg.strict_verify, clock=link.clock)
        self.objective = self.backend.objective(self.target, spec, self.settings)
        if standalone_pool:
            self.pool = NullPool()
        else:
            self.pool = Pool(self.run_dir, spec, self.target_info["matrix_sha256"],
                             self.settings.view("sharing"), self.backend, self.target,
                             self.target_info["input_count"],
                             search_cap=getattr(self.objective, "search_cap", None))
        self.recorder = None
        self.engine = None
        self.stop_flag: str | None = None
        self.counters = {"steps": 0, "accepted": 0, "improved": 0, "checkpoints": 0}
        self.session_steps = 0
        self.session_start = time.monotonic()
        self.last_checkpoint_utc = None

    # ---- lifecycle -------------------------------------------------------------------------
    def _seed_circuit(self) -> tuple[dict | None, bool]:
        """(seed for the engine, whether it is a circuit file that can be recorded)."""
        seed = self.spec["seed"]
        if seed["kind"] == "root":
            return self.backend.root_seed(seed["constructor"], self.target, self.settings,
                                          self.spec["rng_seed"], self.objective), False
        info = self.plan["seeds"][seed["sha256"]]
        circuit = read_json(self.run_dir / info["snapshot"])
        if digest(circuit) != seed["sha256"]:
            raise ValueError(f"seed snapshot {info['snapshot']} hash mismatch")
        return circuit, True

    def _info(self) -> dict:
        """Worker-supplied fields of the recorder's start/resume event (telemetry/schema.md)."""
        seed = self.spec["seed"]
        return {"seed": self.spec["rng_seed"], "source_hash": self.plan.get("source_manifest_sha256"),
                "target": self.spec["target"], "objective": self.spec["objective"],
                "depth_cap": self.spec["depth_cap"], "gate_limit": self.spec["gate_limit"],
                "group": self.spec["group"], "run_id": self.plan["run_id"],
                "settings_sha256": self.spec["settings_sha256"],
                "source": "root" if seed["kind"] == "root" else "seed",
                "root": seed.get("constructor"), "seed_sha256": seed.get("sha256"),
                "process": process_identity(), "owner_token": self.link.token}

    def start_engine(self):
        """Resume from ``checkpoint.json`` if present, else start a fresh chain from the seed."""
        envelope = load_checkpoint(self.dir / "checkpoint.json", self.binding)
        self.recorder = self.backend.recorder(self.dir, self.spec["id"], self.settings, self.link.t0)
        self.pool.recorder = self.recorder
        if envelope is not None:
            self.counters.update(envelope["worker"].get("counters", {}))
            self.recorder.begin("resume", {**self._info(), "checkpoint_utc": envelope["saved_utc"]})
            engine = self.backend.resume_engine(envelope["engine"], self.target, self.objective,
                                                self.settings, recorder=self.recorder, pool=self.pool)
        else:
            seed, recordable = self._seed_circuit()
            self.recorder.begin("start", self._info())
            if recordable:
                # The seed is a verified circuit: record it so the frontier has a baseline.
                self.writer.add({"circuit": seed, "kind": "seed", "ref": f"{self.spec['id']}:seed"})
            engine = self.backend.engine(self.target, self.objective, self.settings,
                                         rng_seed=self.spec["rng_seed"], recorder=self.recorder,
                                         worker_id=self.spec["id"], seed_circuit=seed, pool=self.pool)
        engine.on_record(self.writer.save)
        self.engine = engine
        return engine

    def checkpoint(self) -> None:
        """Atomically save the engine state with this worker's counters."""
        save_checkpoint(self.dir / "checkpoint.json", self.binding, self.engine.checkpoint(),
                        {"counters": self.counters, "records": len(self.writer.entries)})
        self.counters["checkpoints"] += 1
        self.last_checkpoint_utc = utc_now()

    def write_status(self, phase: str, error: str | None = None) -> None:
        """``status.json`` (human/coordinator summary) and ``chain.json`` (fleet diversity input).

        Rewritten every ``status_seconds`` while running: atomic but not fsynced then (a crash
        loses at most one status interval; the two fsyncs cost 5-10 ms of every second).
        Lifecycle writes (starting, stopped, failed) stay durable."""
        elapsed = time.monotonic() - self.session_start
        best = self.writer.best
        engine = self.backend.engine_status(self.engine) if self.engine is not None else None
        sync = phase != "running"
        atomic_json(self.dir / "status.json", {
            "phase": phase, "worker": self.spec["id"], "group": self.spec["group"],
            "target": self.spec["target"], "process": process_identity(), "owner_token": self.link.token,
            "t": self.link.clock(), "updated_utc": utc_now(), **self.counters,
            "steps_per_second": self.session_steps / elapsed if elapsed > 0 else 0.0,
            "best": None if best is None else {k: best[k] for k in ("gates", "depth", "dag_sha256", "path")},
            "engine": engine, "records": len(self.writer.entries), "skipped": self.writer.skipped,
            "frontier": self.writer.frontier(), "pool": self.pool.stats,
            "last_checkpoint_utc": self.last_checkpoint_utc, "error": error}, sync=sync)
        chain = self.backend.chain_values(self.engine) if self.engine is not None else None
        atomic_json(self.dir / "chain.json", {"t": self.link.clock(), "steps": self.counters["steps"],
                                              "best_dag": best["dag_sha256"] if best else None,
                                              "best_values": self.writer.best_values,
                                              "chain_values": chain}, sync=sync)

    def _on_signal(self, signum, frame) -> None:
        self.stop_flag = f"signal {signal.Signals(signum).name}"

    def run(self) -> int:
        """Main loop; returns the process exit code (0 clean stop, 1 failure)."""
        previous = {s: signal.signal(s, self._on_signal) for s in STOP_SIGNALS}
        self.write_status("starting")
        reason = "unknown"
        try:
            engine = self.start_engine()
            now = time.monotonic()
            next_status = now + self.cfg.status_seconds
            next_checkpoint = now + self.cfg.checkpoint_seconds
            next_owner = now + self.cfg.owner_check_seconds
            self.write_status("running")
            counters = self.counters
            step = engine.step
            while True:
                if self.stop_flag:
                    reason = self.stop_flag
                    break
                result = step()
                counters["steps"] += 1
                self.session_steps += 1
                if result.accepted:
                    counters["accepted"] += 1
                if result.improved_worker:
                    counters["improved"] += 1
                now = time.monotonic()
                if now >= next_owner:
                    next_owner = now + self.cfg.owner_check_seconds
                    lost = self.link.lost()
                    if lost:
                        reason = lost
                        break
                if now >= next_checkpoint:
                    self.checkpoint()
                    next_checkpoint = time.monotonic() + self.cfg.checkpoint_seconds
                if now >= next_status:
                    self.write_status("running")
                    next_status = now + self.cfg.status_seconds
            self.checkpoint()
            self.write_status("stopped")
            self.recorder.close(reason)
            return 0
        except BaseException as exc:  # noqa: BLE001 - every failure must leave error.json
            atomic_json(self.dir / "error.json", {
                "utc": utc_now(), "worker": self.spec["id"], "type": type(exc).__name__,
                "message": str(exc), "traceback": traceback.format_exc(),
                "steps": self.counters["steps"], "owner_token": self.link.token}, pretty=True)
            try:
                self.write_status("failed", f"{type(exc).__name__}: {exc}")
                if self.recorder is not None:
                    self.recorder.close(f"failed: {type(exc).__name__}")
            except Exception:  # noqa: BLE001 - the error file is what matters
                pass
            return 1
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def worker_main(run_dir: str, worker_id: str, token: str, cpu: int | None = None) -> int:
    """Entry point of ``python -m xorflux _worker`` (started by the coordinator)."""
    if cpu is not None:
        os.sched_setaffinity(0, {cpu})
    try:
        worker = WorkerProcess(run_dir, worker_id, CoordinatorLink(Path(run_dir), token))
    except BaseException as exc:  # noqa: BLE001 - report setup failures the same way
        atomic_json(Path(run_dir) / "workers" / worker_id / "error.json", {
            "utc": utc_now(), "worker": worker_id, "type": type(exc).__name__, "message": str(exc),
            "traceback": traceback.format_exc(), "owner_token": token, "stage": "setup"}, pretty=True)
        return 1
    return worker.run()


def run_standalone(run_dir: str | Path, worker_id: str, seconds: float | None, backend=None) -> int:
    """Run one planned worker in this process until ``seconds`` elapse (``xorflux quick``)."""
    worker = WorkerProcess(run_dir, worker_id, DeadlineLink(seconds), backend=backend, standalone_pool=True)
    return worker.run()
