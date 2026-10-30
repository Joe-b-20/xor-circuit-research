"""Stub backend for the campaign runtime tests (and its own sanity tests).

The campaign runtime talks to core/engine/telemetry only through ``campaign.records.Backend``.
This module replaces every dependency with a tiny, deterministic stand-in so the runtime tests
pass on their own:

* target ``toy4``: 4 inputs, rows x0^x1, x0^x1^x2, x0^x1^x2^x3 (known optimum 3 gates at depth 3,
  and 4 gates at depth 2);
* a small exact verifier with the same result fields as ``core.circuit.verify``;
* ``StubEngine``: walks a fixed ladder of better circuits (6@3 -> 5@3 -> 4@2 -> 3@3), reporting
  each through ``on_record`` and pulling from the pool on periodic "restarts";
* ``StubRecorder`` / ``StubEventLog``: JSONL files with the documented method names.

Used as ``backend = "xorsearch.tests.test_campaign_stub:StubBackend"`` in campaign files (the
frozen copy then needs ``campaign.freeze_tests = true``).
"""
from __future__ import annotations

import hashlib
import json
import random
import time
import unittest
from dataclasses import dataclass
from pathlib import Path

from xorsearch.campaign.checkpoint import append_jsonl, atomic_text, utc_now
from xorsearch.campaign.records import Backend
from xorsearch.config.schema import Schema

TOY_ROWS = [0b0011, 0b0111, 0b1111]

#: Valid toy4 circuits, worse to better: (gates, depth) 6@3, 5@3, 4@2, 3@3.
LADDER = [
    [[0, 1], [0, 1], [5, 2], [0, 1], [7, 2], [8, 3]],
    [[0, 1], [4, 2], [0, 1], [6, 2], [7, 3]],
    [[0, 1], [4, 2], [2, 3], [4, 6]],
    [[0, 1], [4, 2], [5, 3]],
]


def circuit(gates) -> dict:
    """Circuit JSON (old format) for toy4 gates."""
    return {"benchmark": "toy4", "inputCount": 4, "gates": [list(g) for g in gates]}


def matrix_sha256(n, rows) -> str:
    """Same construction as the old target module."""
    body = json.dumps({"input_count": n, "rows": rows}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


class StubTarget:
    """Minimal Target: name, n, rows, matrix hash, built-in seeds."""

    def __init__(self, name, n, rows, seeds=()):
        self.name, self.n, self.rows = name, n, list(rows)
        self.matrix_sha256 = matrix_sha256(n, self.rows)
        self.seeds = list(seeds)

    def to_json(self) -> dict:
        """Old target file format."""
        return {"id": self.name, "name": self.name, "input_count": self.n, "output_count": len(self.rows),
                "rows": self.rows, "matrix_sha256": self.matrix_sha256}


def toy_target() -> StubTarget:
    """The toy4 catalog target with the worst ladder circuit as its built-in seed."""
    return StubTarget("toy4", 4, TOY_ROWS, seeds=[circuit(LADDER[0])])


def stub_verify(data, target, cap=None) -> dict:
    """Exact toy verifier with core.circuit.verify's result fields."""
    n, rows = target.n, target.rows
    masks, depths = [1 << i for i in range(n)], [0] * n
    for index, pair in enumerate(data["gates"]):
        a, b = pair
        if not (0 <= a < n + index and 0 <= b < n + index):
            return {"equivalent": False, "error": f"gate {index} is not topological"}
        masks.append(masks[a] ^ masks[b])
        depths.append(1 + max(depths[a], depths[b]))
    best = {}
    for i, value in enumerate(masks):
        if value not in best or depths[i] < depths[best[value]]:
            best[value] = i
    equivalent = all(r in best for r in rows)
    depth = max(depths[best[r]] for r in rows) if equivalent else 0
    if cap is not None and equivalent and depth > cap:
        return {"equivalent": False, "error": "circuit exceeds output depth cap"}
    triples = sorted([masks[n + i], *sorted((masks[a], masks[b]))] for i, (a, b) in enumerate(data["gates"]))
    dag = hashlib.sha256(json.dumps({"m": target.matrix_sha256, "t": triples}).encode()).hexdigest()
    body = json.dumps({"rows": rows, "gates": sorted(sorted(g) for g in data["gates"])}).encode()
    return {"equivalent": equivalent, "gate_count": len(data["gates"]), "depth": depth,
            "dag_sha256": dag, "circuit_sha256": hashlib.sha256(body).hexdigest(),
            "verifier_version": "stub-1", "masks": masks}


@dataclass
class StubObjective:
    """Objective stand-in: just the parameters (no soft slack)."""
    kind: str
    depth_cap: int | None
    gate_limit: int | None

    @property
    def search_cap(self):
        """Same as the real cap here."""
        return self.depth_cap


@dataclass
class StepResult:
    """The fields of engine.loop.StepResult the worker reads."""
    it: int
    move: str
    accepted: bool
    improved_worker: bool
    gates_after: int
    depth_after: int


class StubRecorder:
    """Recorder stand-in (``events.jsonl``); same constructor, ``t0`` and ``close`` semantics."""

    def __init__(self, directory, worker_id, settings=None, clock=None, *, t0=None):
        self.path = Path(directory) / "events.jsonl"
        self.worker = worker_id
        self.t0 = time.monotonic() if t0 is None else t0

    def now(self):
        """Seconds since campaign start."""
        return time.monotonic() - self.t0

    def begin(self, kind, info):
        """Lifecycle event with the worker-supplied fields."""
        self.event(kind, **{k: info.get(k) for k in ("seed", "source", "root", "settings_sha256")})

    def event(self, ev, **fields):
        """One event line."""
        append_jsonl(self.path, {"t": self.now(), "utc": utc_now(), "worker": self.worker, "ev": ev, **fields})

    def close(self, reason="normal", **fields):
        """The real Recorder emits ``stop`` on close."""
        self.event("stop", reason=reason, **fields)


class StubEventLog:
    """EventLog stand-in for campaign.jsonl (``write(ev, it=None, **fields)``, ``now()``)."""

    def __init__(self, path, worker="coord", *, settings=None, t0=None):
        self.path = Path(path)
        self.worker = worker
        self.t0 = time.monotonic() if t0 is None else t0

    def now(self):
        """Seconds since campaign start."""
        return time.monotonic() - self.t0

    def write(self, ev, it=None, **fields):
        """One event line with the telemetry envelope."""
        record = {"v": 1, "t": self.now(), "utc": utc_now(), "worker": self.worker, "it": it, "ev": ev}
        record.update(fields)
        append_jsonl(self.path, record)
        return record

    def close(self):
        """Nothing buffered."""


class ListLog:
    """In-memory event log for unit tests."""

    def __init__(self):
        self.events = []

    def now(self):
        """Fixed clock."""
        return 0.0

    def write(self, ev, it=None, **fields):
        """Remember one event."""
        self.events.append({"ev": ev, **fields})

    def of(self, ev):
        """All events of one type."""
        return [e for e in self.events if e["ev"] == ev]


def pairwise(sets) -> dict:
    """Small stand-in for telemetry.metrics.diversity (same keys the coordinator reads)."""
    items = [frozenset(s) for s in sets]
    distances = [1 - len(a & b) / len(a | b) if a | b else 0.0
                 for i, a in enumerate(items) for b in items[i + 1:]]
    return {"n": len(items), "distinct": len(set(items)),
            "mean": sum(distances) / len(distances) if distances else 0.0,
            "min": min(distances, default=0.0), "max": max(distances, default=0.0)}


class StubEngine:
    """Engine stand-in: improves along LADDER at random steps; pulls on periodic restarts.

    Mirrors the engine.loop contract the campaign runtime relies on: ``on_record`` candidates
    with ``ref`` (the improvement's dossier id ``<worker>-NNNNNN``)/``kind``/``gates``/
    ``outputs``/``values``, rollback when a callback returns ``ok`` False,
    ``pool.sample(exclude, rng)`` returning an elite dict, ``snapshot``, ``checkpoint``/``resume``.
    """
    #: Probability per step of reaching the next ladder circuit, and steps between restarts.
    IMPROVE_P = 0.05
    RESTART_EVERY = 200
    STEP_SLEEP = 0.001  # keep end-to-end tests cheap on CPU

    def __init__(self, target, objective, settings, *, rng_seed, recorder, worker_id,
                 seed_circuit=None, pool=None):
        self.target, self.objective, self.recorder, self.pool = target, objective, recorder, pool
        self.worker_id = worker_id
        self.rng = random.Random(rng_seed)
        self.it = 0
        self.index = 0
        self.callbacks = []
        self.pulls = 0
        self.improvements = 0
        self.current = seed_circuit if seed_circuit and "gates" in seed_circuit else circuit(LADDER[0])

    def on_record(self, callback):
        """Register the verified-saving hook."""
        self.callbacks.append(callback)

    def _found(self, candidate_gates):
        check = stub_verify(circuit(candidate_gates), self.target)
        ident = f"{self.worker_id}-{self.improvements + 1:06d}"
        cand = {"ref": ident, "improvement": ident, "kind": "gates", "worker": self.worker_id,
                "it": self.it, "chain": 1, "root": "seed", "move": "stub.ladder",
                "gate_count": check["gate_count"], "depth": check["depth"],
                "values": sorted(set(check["masks"][self.target.n:])), "gates": candidate_gates,
                "outputs": None}
        for callback in self.callbacks:
            result = callback(cand)
            if isinstance(result, dict) and result.get("ok") is False:
                return False
        self.current = circuit(candidate_gates)
        self.improvements += 1
        return True

    def step(self):
        """One fake proposal."""
        self.it += 1
        if self.STEP_SLEEP:
            time.sleep(self.STEP_SLEEP)
        improved = False
        if self.index + 1 < len(LADDER) and self.rng.random() < self.IMPROVE_P:
            self.index += 1
            check = stub_verify(circuit(LADDER[self.index]), self.target)
            cap = self.objective.depth_cap
            if cap is None or check["depth"] <= cap:   # the engine only offers feasible points
                improved = self._found(LADDER[self.index])
        if self.pool is not None and self.it % self.RESTART_EVERY == 0:
            values = self.pool.sample(set(), self.rng)
            self.recorder.event("pull", ok=values is not None)
            self.pulls += values is not None
        check = stub_verify(self.current, self.target)
        return StepResult(self.it, "stub.ladder", improved, improved, check["gate_count"], check["depth"])

    def snapshot(self):
        """Status summary."""
        check = stub_verify(self.current, self.target)
        return {"it": self.it, "cur": [check["gate_count"], check["depth"]], "phase": "plateau"}

    def checkpoint(self) -> dict:
        """JSON-safe state."""
        version, internal, gauss = self.rng.getstate()
        return {"it": self.it, "index": self.index, "current": self.current, "pulls": self.pulls,
                "improvements": self.improvements, "rng": [version, list(internal), gauss]}

    @classmethod
    def resume(cls, data, target, objective, settings, *, recorder, pool=None):
        """Continue exactly from ``checkpoint()``."""
        engine = cls(target, objective, settings, rng_seed=0, recorder=recorder, worker_id="resumed",
                     seed_circuit=data["current"], pool=pool)
        engine.it, engine.index, engine.pulls = data["it"], data["index"], data["pulls"]
        engine.improvements = data["improvements"]
        version, internal, gauss = data["rng"]
        engine.rng.setstate((version, tuple(internal), gauss))
        engine.resumed = True
        return engine


class StubBackend(Backend):
    """Backend with every dependency stubbed (see module docstring)."""
    name = "stub"

    def schema(self):
        from xorsearch.campaign import coordinator, sharing, worker
        return Schema([coordinator.KNOBS, worker.KNOBS, sharing.KNOBS])

    def load_target(self, spec):
        if spec == "toy4":
            return toy_target()
        path = Path(spec)
        if not path.is_file():
            raise ValueError(f"unknown target {spec!r}")
        data = json.loads(path.read_text())
        return StubTarget(data.get("name", path.stem), data["input_count"], data["rows"], data.get("seeds", ()))

    def target_json(self, target):
        return target.to_json()

    def target_seeds(self, target):
        return [(f"s{i}", dict(s)) for i, s in enumerate(target.seeds)]

    def catalog(self):
        return ["toy4"]

    def root_names(self):
        return ["naive", "paar"]

    def verify(self, data, target, cap=None):
        return stub_verify(data, target, cap)

    def ncff(self, data, target):
        lines = ["%NCFF stub", f"Inputs: {target.n}"]
        lines += [f"XOR t{target.n + i} {a} {b}" for i, (a, b) in enumerate(data["gates"])]
        return "\n".join(lines) + "\n"

    def record_circuit(self, record, target):
        if "circuit" in record:
            return dict(record["circuit"])
        return {"benchmark": target.name, "inputCount": target.n, "gates": [list(g) for g in record["gates"]]}

    def objective(self, target, spec, settings):
        if spec["objective"] not in ("gates", "depth_then_gates"):
            raise ValueError("unknown objective kind")
        return StubObjective(spec["objective"], spec["depth_cap"], spec["gate_limit"])

    def root_seed(self, constructor, target, settings, rng_seed, objective):
        return None

    def recorder(self, directory, worker_id, settings, t0):
        return StubRecorder(directory, worker_id, settings, t0=t0)

    def engine(self, target, objective, settings, *, rng_seed, recorder, worker_id, seed_circuit, pool):
        return StubEngine(target, objective, settings, rng_seed=rng_seed, recorder=recorder,
                          worker_id=worker_id, seed_circuit=seed_circuit, pool=pool)

    def resume_engine(self, data, target, objective, settings, *, recorder, pool):
        return StubEngine.resume(data, target, objective, settings, recorder=recorder, pool=pool)

    def chain_values(self, engine):
        masks = stub_verify(engine.current, engine.target)["masks"]
        return sorted(set(masks[engine.target.n:]))

    def diversity(self, sets):
        return pairwise(sets)

    def event_log(self, path, settings, t0):
        return StubEventLog(path, "coord", settings=settings, t0=t0)

    def build_report(self, run_dir):
        path = Path(run_dir) / "report.txt"
        atomic_text(path, "stub report\n")
        return str(path)


class CrashOnceEngine(StubEngine):
    """StubEngine that raises once per worker directory (a marker file makes it one-shot even
    across processes), to exercise ``campaign.on_worker_failure``."""
    CRASH_AT = 30

    def step(self):
        """Crash at step CRASH_AT the first time this worker runs."""
        marker = self.recorder.path.parent / "crashed-once"
        if self.it + 1 == self.CRASH_AT and not marker.exists():
            marker.write_text("1\n")
            raise RuntimeError("deliberate test crash")
        return super().step()


class CrashOnceBackend(StubBackend):
    """StubBackend whose workers each crash once early."""

    def engine(self, target, objective, settings, *, rng_seed, recorder, worker_id, seed_circuit, pool):
        return CrashOnceEngine(target, objective, settings, rng_seed=rng_seed, recorder=recorder,
                               worker_id=worker_id, seed_circuit=seed_circuit, pool=pool)


BACKEND = "xorsearch.tests.test_campaign_stub:StubBackend"
CRASH_BACKEND = "xorsearch.tests.test_campaign_stub:CrashOnceBackend"

#: Fast bookkeeping for short tests (all knobs from the campaign runtime's own sections).
FAST_SET = """
[set]
"campaign.collect_seconds" = 0.3
"campaign.poll_seconds" = 0.05
"campaign.diversity_seconds" = 1.0
"campaign.stop_grace_seconds" = 10.0
"campaign.git_status" = false
"worker.status_seconds" = 0.3
"worker.checkpoint_seconds" = 1.0
"worker.owner_check_seconds" = 0.2
"""

TWO_WORKERS = """
[[workers]]
name = "a"
target = "toy4"
count = 2
depth_cap = [2, "none"]
"""


def toy_campaign(groups: str = TWO_WORKERS, head: str = "", sets: str = FAST_SET,
                 backend: str = BACKEND) -> str:
    """Campaign TOML text using the stub backend."""
    return f'[campaign]\nname = "toy"\nseed = 11\nbackend = "{backend}"\n{head}\n{sets}\n{groups}\n'


def write_campaign(directory, text: str, name: str = "campaign.toml") -> Path:
    """Write campaign text into ``directory``; returns its path."""
    path = Path(directory) / name
    path.write_text(text)
    return path


class StubSelfTest(unittest.TestCase):
    """The stub must itself be right, or every other test proves nothing."""

    def test_ladder_is_valid_and_improving(self):
        target = toy_target()
        points = [(r["gate_count"], r["depth"]) for r in (stub_verify(circuit(g), target) for g in LADDER)]
        self.assertEqual(points, [(6, 3), (5, 3), (4, 2), (3, 3)])
        self.assertTrue(all(stub_verify(circuit(g), target)["equivalent"] for g in LADDER))

    def test_verifier_rejects_wrong_circuit(self):
        self.assertFalse(stub_verify(circuit([[0, 1], [4, 2]]), toy_target())["equivalent"])
        self.assertFalse(stub_verify(circuit(LADDER[3]), toy_target(), cap=2)["equivalent"])


if __name__ == "__main__":
    unittest.main()
