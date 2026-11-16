"""Record files, their independent verification, and the backend seam to core/engine/telemetry.

A **record** is a distinct DAG a worker found at a nondominated (gates, depth) point.  It is saved
as three files in ``workers/<id>/records/``::

    g<G>-d<D>-<dag16>.ncff               NIST circuit file format export
    g<G>-d<D>-<dag16>.verification.json  result of the independent verifier (core.circuit.verify)
    g<G>-d<D>-<dag16>.json               circuit JSON (old xor-circuit-lab format) + "metadata"

and one line in ``workers/<id>/records.jsonl``.  The sidecars are written first and the circuit
JSON last: it is the commit marker, so a crash never leaves a circuit without its verification.
The index line follows; ``RecordWriter.recover`` re-indexes a committed record whose line was lost.
The coordinator re-verifies every indexed record before it enters the global frontier or the pool.

Records and improvement dossiers are joined by the engine's candidate ``ref``
(``<worker>:<chain>:<it>``): the record is saved first (the engine verifies before it counts an
improvement), and when the engine publishes the improvement a ``{"link": "improvement", ...}``
line in ``records.jsonl`` adds the dossier id.

**Backend.**  Every call the campaign runtime makes into ``core``, ``engine`` and ``telemetry`` is
a method of :class:`Backend`, so the integration surface is in one place and tests or experiments
can substitute a stub with ``[campaign] backend = "module:Class"`` (frozen into the plan).
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import random
from pathlib import Path
from typing import Any, Mapping

from .checkpoint import append_jsonl, atomic_json, atomic_text, file_hash, read_json, read_jsonl, utc_now


# --------------------------------------------------------------------------------------------
# Backend seam
# --------------------------------------------------------------------------------------------
def _as_dict(value: Any) -> dict:
    """A result object as a plain dict (``to_dict()`` preferred: it may add derived fields)."""
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    return dict(vars(value))


def json_safe(value: Any) -> Any:
    """``value`` round-tripped through JSON (sets become sorted lists, tuples lists)."""
    return json.loads(json.dumps(value, default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else list(o)))


class Backend:
    """How the campaign runtime talks to the rest of xorsearch.

    Each method names the API it calls.  Override methods in a subclass to adapt or stub one
    dependency (``tests/test_campaign_stub.py`` stubs all of them).
    """
    name = "xorsearch"

    # ---- configuration --------------------------------------------------------------------
    def schema(self):
        """The full knob schema: ``config.registry.schema()``."""
        from ..config.registry import schema
        return schema()

    # ---- targets ---------------------------------------------------------------------------
    def load_target(self, spec: str):
        """``core.target.load_target(spec)``: catalog name, JSON/matrix path or generator spec."""
        from ..core.target import load_target
        return load_target(spec)

    def target_json(self, target) -> dict:
        """``Target.to_json()``: the target file format (``rows``, ``input_count``,
        ``matrix_sha256``, ...) that ``load_target(path)`` reads back."""
        return _as_dict(target.to_json())

    def target_seeds(self, target) -> list[tuple[str, dict]]:
        """``(label, circuit JSON)`` per built-in seed: ``Seed.load(n).to_json(target)``."""
        return [(seed.label or Path(seed.path).name, seed.load(target.n_inputs).to_json(target))
                for seed in target.seeds]

    def catalog(self) -> list[str]:
        """``core.target.catalog()``: names ``load_target`` accepts."""
        from ..core.target import catalog
        return list(catalog())

    def root_names(self) -> list[str] | None:
        """Named root constructors (``moves.construct.ROOTS``), for ``seeds = ["root:<name>"]``."""
        from ..moves.construct import ROOTS
        return sorted(ROOTS)

    # ---- circuits --------------------------------------------------------------------------
    def verify(self, circuit: dict, target, cap: int | None = None) -> dict:
        """``core.circuit.verify(circuit, target, cap).to_dict()``, with ``error`` = ``reason``.

        Fields used: ``equivalent``, ``gate_count``, ``depth``, ``dag_sha256``,
        ``circuit_sha256`` (and ``ok`` / ``within_cap`` when a cap is given).
        """
        from ..core.circuit import verify
        result = json_safe(_as_dict(verify(circuit, target, cap)))
        if result.get("reason") and "error" not in result:
            result["error"] = result["reason"]
        return result

    def ncff(self, circuit: dict, target) -> str:
        """``core.circuit.ncff(circuit, target)``."""
        from ..core.circuit import ncff
        return ncff(circuit, target)

    def record_circuit(self, record: Mapping, target) -> dict:
        """Circuit JSON of an engine candidate.

        The engine's ``on_record`` candidate carries ``gates`` (index pairs) and ``outputs``
        (signal per row); it becomes ``core.circuit.Circuit(n, gates, outputs).to_json(target)``
        (``benchmark``, ``inputCount``, ``gates``, ``outputSignals``, ``gateCount``, ``depth``,
        ...).  A ready circuit JSON may instead be given as ``record["circuit"]``.
        """
        if isinstance(record.get("circuit"), Mapping):
            return dict(record["circuit"])
        from ..core.circuit import Circuit
        gates = [tuple(g) for g in record["gates"]]
        outputs = record.get("outputs")
        return Circuit(target.n_inputs, gates, None if outputs is None else list(outputs)).to_json(target)

    # ---- search ----------------------------------------------------------------------------
    def objective(self, target, spec: Mapping, settings):
        """``core.objective.Objective.from_settings(settings, kind=, depth_cap=, gate_limit=)``."""
        from ..core.objective import Objective
        return Objective.from_settings(settings, kind=spec["objective"], depth_cap=spec["depth_cap"],
                                       gate_limit=spec["gate_limit"])

    def root_seed(self, constructor: str, target, settings, rng_seed: int, objective) -> dict | None:
        """``{"values": [...]}`` from ``moves.construct.build_root(name, target, rng, cap, None,
        settings)`` for a named constructor; None (= the engine's own randomized root) for
        'default'.  The full Settings is passed: construct picks its own ``construct.*`` view."""
        if constructor in ("", "default"):
            return None
        from ..moves.construct import build_root
        built = build_root(constructor, target, random.Random(rng_seed), objective.search_cap, None,
                           settings)
        values = built[0] if isinstance(built, tuple) else built  # (values, info)
        return {"values": list(values)}

    def recorder(self, directory: Path, worker_id: str, settings, t0: float):
        """``telemetry.recorder.Recorder(directory, worker_id, settings, t0=t0)``.

        ``t0`` is the ``time.monotonic()`` value of campaign start, shared by every process.
        """
        from ..telemetry.recorder import Recorder
        return Recorder(directory, worker_id, settings, t0=t0)

    def engine(self, target, objective, settings, *, rng_seed, recorder, worker_id, seed_circuit, pool):
        """``engine.loop.Engine(...)`` for a fresh chain (``seed_circuit``: circuit JSON with
        ``gates``, a ``{"values": ...}`` dict, or None for a fresh root)."""
        from ..engine.loop import Engine
        return Engine(target, objective, settings, rng_seed=rng_seed, recorder=recorder,
                      worker_id=worker_id, seed_circuit=seed_circuit, pool=pool)

    def resume_engine(self, data: dict, target, objective, settings, *, recorder, pool):
        """``Engine.resume(data, target, objective, settings, recorder=, pool=)``."""
        from ..engine.loop import Engine
        return Engine.resume(data, target, objective, settings, recorder=recorder, pool=pool)

    def engine_status(self, engine) -> dict:
        """``engine.snapshot()``: it, phase, cur, chain_best, worker_best, frontier."""
        return engine.snapshot()

    def chain_values(self, engine) -> list[int] | None:
        """Current chain value set for fleet diversity: ``engine.state.values()``."""
        return sorted(engine.state.values())

    def diversity(self, sets: list) -> dict:
        """``telemetry.metrics.diversity(sets)``: n, distinct, modal_fraction, mean/min/max, ..."""
        from ..telemetry.metrics import diversity
        return diversity(sets)

    def event_log(self, path: Path, settings, t0: float):
        """``telemetry.recorder.EventLog(path, "coord", settings=settings, t0=t0)``."""
        from ..telemetry.recorder import EventLog
        return EventLog(path, "coord", settings=settings, t0=t0)

    def build_report(self, run_dir: Path):
        """``telemetry.report.build_report(run_dir)`` (returns the report directory)."""
        from ..telemetry.report import build_report
        return build_report(run_dir)


def load_backend(spec: str | None) -> Backend:
    """``"xorsearch"`` (or None) for the built-in backend, else ``"module:Class"``."""
    if not spec or spec == "xorsearch":
        return Backend()
    module_name, sep, attr = spec.partition(":")
    if not sep:
        raise ValueError(f"backend must be 'xorsearch' or 'module:Class', got {spec!r}")
    return getattr(importlib.import_module(module_name), attr)()


# --------------------------------------------------------------------------------------------
# Small circuit helpers (independent of core: identities and diversity only)
# --------------------------------------------------------------------------------------------
def objective_key(kind: str, gates: int, depth: int) -> tuple[int, int]:
    """Lexicographic score of a (gates, depth) point under an objective kind (lower is better)."""
    return (depth, gates) if kind.startswith("depth") else (gates, depth)


def dominates(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """True when point ``a`` is at least as good as ``b`` in gates and depth, and not equal."""
    return a[0] <= b[0] and a[1] <= b[1] and a != b


def circuit_values(circuit: Mapping, input_count: int) -> list[int]:
    """Sorted distinct non-input masks computed by a circuit JSON (its value set)."""
    masks = [1 << i for i in range(input_count)]
    for a, b in circuit["gates"]:
        masks.append(masks[a] ^ masks[b])
    inputs = set(masks[:input_count])
    return sorted(set(masks[input_count:]) - inputs)


def dag_identity(verification: Mapping) -> str:
    """The verifier's exact-DAG hash, falling back to the circuit hash."""
    return verification.get("dag_sha256") or verification.get("circuit_sha256") or ""


def score(gates: int, depth: int) -> dict:
    """Score object of the telemetry schema."""
    return {"gates": gates, "depth": depth}


# --------------------------------------------------------------------------------------------
# Record writing
# --------------------------------------------------------------------------------------------
#: Engine candidate fields kept in record metadata and the index (DESIGN.md 4.4, engine/loop.py).
CANDIDATE_FIELDS = ("ref", "kind", "it", "move", "chain", "root")
VERIFICATION_FIELDS = ("equivalent", "gate_count", "depth", "dag_sha256", "circuit_sha256",
                       "verifier_version")


class RecordError(RuntimeError):
    """The engine reported a circuit the independent verifier rejects (an engine bug)."""


class RecordWriter:
    """Saves verified records for one worker and tracks its own frontier.

    ``context`` holds the binding written into every record's metadata (run id, worker, group,
    target, matrix hash, plan/settings/source hashes).  ``spec`` gives the real ``depth_cap``,
    ``gate_limit`` and ``objective``.  ``per_point`` caps distinct DAGs saved per point and
    ``strict`` makes a non-equivalent circuit fatal (default) instead of only rejected.
    """

    def __init__(self, worker_dir: Path, run_dir: Path, context: dict, backend: Backend, target,
                 spec: Mapping, input_count: int, per_point: int, strict: bool, clock=None):
        self.worker_dir = Path(worker_dir)
        self.run_dir = Path(run_dir)
        self.records_dir = self.worker_dir / "records"
        self.index_path = self.worker_dir / "records.jsonl"
        self.context = context
        self.backend = backend
        self.target = target
        self.spec = spec
        self.input_count = input_count
        self.per_point = per_point
        self.strict = strict
        self.clock = clock or (lambda: None)
        self.points: dict[tuple[int, int], set[str]] = {}
        self.entries: list[dict] = []
        self.by_dag: dict[str, dict] = {}
        self.best: dict | None = None
        self.best_values: list[int] | None = None
        self.skipped: dict[str, int] = {}
        self.recover()

    # ---- state -----------------------------------------------------------------------------
    def _score(self, entry: Mapping) -> tuple[int, int]:
        return objective_key(self.spec["objective"], entry["gates"], entry["depth"])

    def frontier(self) -> list[tuple[int, int]]:
        """Nondominated (gates, depth) points among saved records."""
        points = sorted(self.points)
        return [p for p in points if not any(dominates(q, p) for q in points)]

    def _remember(self, entry: dict, circuit: Mapping | None = None) -> None:
        self.points.setdefault((entry["gates"], entry["depth"]), set()).add(entry["dag_sha256"])
        self.entries.append(entry)
        self.by_dag[entry["dag_sha256"]] = entry
        if self.best is None or self._score(entry) < self._score(self.best):
            self.best = entry
            if circuit is None:
                circuit = read_json(self.run_dir / entry["path"])
            self.best_values = circuit_values(circuit, self.input_count)

    def recover(self) -> None:
        """Rebuild state from ``records.jsonl`` and re-index records committed after a lost line."""
        lines, _ = read_jsonl(self.index_path)
        known = set()
        for entry in lines:
            if "path" not in entry:  # link lines and torn-line recovery markers
                continue
            known.add(entry["path"])
            self._remember(entry)
        if not self.records_dir.is_dir():
            return
        for path in sorted(self.records_dir.glob("*.json")):
            if path.name.endswith(".verification.json"):
                continue
            relative = path.relative_to(self.run_dir).as_posix()
            if relative in known:
                continue
            circuit = read_json(path)
            bare = {k: v for k, v in circuit.items() if k != "metadata"}
            verification = self.backend.verify(bare, self.target, None)
            if not verification.get("equivalent"):
                raise RecordError(f"committed record fails verification: {path}")
            # Finish the sidecars an interrupted save may have skipped, then index it.
            atomic_json(path.with_suffix(".verification.json"), verification)
            atomic_text(path.with_suffix(".ncff"), self.backend.ncff(bare, self.target))
            entry = self._entry(relative, path, verification, circuit.get("metadata", {}))
            append_jsonl(self.index_path, entry)
            self._remember(entry, bare)

    def _entry(self, relative: str, path: Path, verification: Mapping, meta: Mapping) -> dict:
        return {"path": relative, "file_sha256": file_hash(path),
                "gates": verification["gate_count"], "depth": verification["depth"],
                "dag_sha256": dag_identity(verification),
                "circuit_sha256": verification.get("circuit_sha256"),
                "worker": self.context["worker"], "group": self.context.get("group"),
                "target": self.context["target"],
                **{k: meta.get(k) for k in (*CANDIDATE_FIELDS, "t", "saved_utc")}}

    # ---- saving ----------------------------------------------------------------------------
    def save(self, record: Mapping) -> dict:
        """Engine ``on_record`` callback: verify and save one candidate; returns the
        verification summary the engine keeps in its dossier.

        ``ok`` is False only when the circuit is wrong or breaks the real cap / gate limit (the
        engine then rolls the candidate back).  A valid candidate may still not be written
        (``saved`` False, ``skipped`` says why): duplicate DAG, point dominated by an own record,
        or the point already holds ``worker.records_per_point`` DAGs.
        """
        entry, summary = self._save(record)
        return summary

    def add(self, record: Mapping) -> dict | None:
        """Like ``save`` but returns the index entry (None when not written)."""
        return self._save(record)[0]

    def _skip(self, reason: str, summary: dict, ok: bool = True) -> tuple[None, dict]:
        self.skipped[reason] = self.skipped.get(reason, 0) + 1
        summary.update(ok=ok, saved=False, skipped=reason)
        return None, summary

    def _save(self, record: Mapping) -> tuple[dict | None, dict]:
        if not isinstance(record, Mapping):
            record = vars(record)
        circuit = self.backend.record_circuit(record, self.target)
        circuit.pop("metadata", None)
        verification = self.backend.verify(circuit, self.target, None)
        summary = {k: verification.get(k) for k in VERIFICATION_FIELDS}
        summary["verifier"] = "core.circuit.verify (campaign record writer)"
        if not verification.get("equivalent"):
            reason = verification.get("error", "outputs missing")
            append_jsonl(self.worker_dir / "rejected.jsonl", {
                "utc": utc_now(), "reason": reason, **{k: record.get(k) for k in CANDIDATE_FIELDS},
                "circuit": circuit})
            if self.strict:
                raise RecordError(f"{self.context['worker']}: engine record does not compute the "
                                  f"target: {reason}")
            summary["reason"] = reason
            return self._skip("not_equivalent", summary, ok=False)
        gates, depth = verification["gate_count"], verification["depth"]
        point, dag = (gates, depth), dag_identity(verification)
        cap, limit = self.spec.get("depth_cap"), self.spec.get("gate_limit")
        if cap is not None and depth > cap:
            summary["reason"] = f"depth {depth} above the real cap {cap}"
            return self._skip("over_depth_cap", summary, ok=False)
        if limit is not None and gates > limit:
            summary["reason"] = f"{gates} gates above the gate limit {limit}"
            return self._skip("over_gate_limit", summary, ok=False)
        if dag in self.points.get(point, ()):
            summary["record"] = self.by_dag[dag]["path"]
            return self._skip("duplicate", summary)
        if any(dominates(q, point) for q in self.points):
            return self._skip("dominated", summary)
        if len(self.points.get(point, ())) >= self.per_point:
            return self._skip("point_full", summary)
        meta = {**self.context, **{k: record.get(k) for k in CANDIDATE_FIELDS},
                "t": self.clock(), "saved_utc": utc_now(),
                "verification": {k: verification.get(k) for k in VERIFICATION_FIELDS}}
        path = self.records_dir / f"g{gates}-d{depth}-{dag[:16]}.json"
        atomic_text(path.with_suffix(".ncff"), self.backend.ncff(circuit, self.target))
        atomic_json(path.with_suffix(".verification.json"), verification)
        atomic_json(path, {**circuit, "metadata": meta}, pretty=True)  # commit marker
        entry = self._entry(path.relative_to(self.run_dir).as_posix(), path, verification, meta)
        append_jsonl(self.index_path, entry)
        self._remember(entry, circuit)
        summary.update(ok=True, saved=True, record=entry["path"])
        return entry, summary

    def link_improvement(self, ref: str | None, improvement: str | None, dag: str | None = None) -> None:
        """Record that engine candidate ``ref`` became improvement (dossier) ``improvement``."""
        if not ref or not improvement:
            return
        entry = next((e for e in reversed(self.entries) if e.get("ref") == ref), None)
        if entry is None and dag in self.by_dag:
            entry = self.by_dag[dag]
        append_jsonl(self.index_path, {"link": "improvement", "ref": ref, "improvement": improvement,
                                       "record": entry["path"] if entry else None})


# --------------------------------------------------------------------------------------------
# Independent re-verification (coordinator, ``xorsearch verify``)
# --------------------------------------------------------------------------------------------
def check_record(run_dir: Path, entry: Mapping, spec: Mapping, plan: Mapping, backend: Backend,
                 target, deep: bool = False) -> tuple[dict | None, str | None]:
    """Re-verify one indexed record; returns (circuit, None) or (None, reason it is rejected).

    Checks the file hash, the metadata binding (run, worker, matrix), equivalence, that gates,
    depth and DAG hash match the index, the worker's real depth cap and gate limit.  ``deep`` also
    compares the verification sidecar and the NCFF export with freshly computed ones.
    """
    from .checkpoint import safe_join
    try:
        path = safe_join(run_dir, entry["path"])
    except ValueError as exc:
        return None, str(exc)
    if not path.is_file():
        return None, "record file missing"
    if file_hash(path) != entry.get("file_sha256"):
        return None, "record file hash differs from the index"
    circuit = read_json(path)
    meta = circuit.get("metadata", {})
    target_info = plan["targets"][spec["target"]]
    expected = {"run_id": plan["run_id"], "worker": spec["id"], "matrix_sha256": target_info["matrix_sha256"]}
    wrong = [k for k, v in expected.items() if meta.get(k) != v]
    if wrong:
        return None, f"metadata binding mismatch: {', '.join(wrong)}"
    bare = {k: v for k, v in circuit.items() if k != "metadata"}
    verification = backend.verify(bare, target, None)
    if not verification.get("equivalent"):
        return None, f"not equivalent: {verification.get('error', 'outputs missing')}"
    if (verification["gate_count"], verification["depth"]) != (entry["gates"], entry["depth"]):
        return None, "gate count or depth differs from the index"
    if dag_identity(verification) != entry["dag_sha256"]:
        return None, "DAG hash differs from the index"
    if spec.get("depth_cap") is not None and entry["depth"] > spec["depth_cap"]:
        return None, "depth above the worker's real cap"
    if spec.get("gate_limit") is not None and entry["gates"] > spec["gate_limit"]:
        return None, "gates above the worker's gate limit"
    if deep:
        sidecar = read_json(path.with_suffix(".verification.json"))
        keys = ("equivalent", "gate_count", "depth", "dag_sha256", "circuit_sha256")
        if not sidecar or any(sidecar.get(k) != verification.get(k) for k in keys):
            return None, "verification sidecar differs from a fresh verification"
        ncff_path = path.with_suffix(".ncff")
        if not ncff_path.is_file() or ncff_path.read_text(encoding="utf-8") != backend.ncff(bare, target):
            return None, "NCFF export differs from a fresh export"
    return bare, None
