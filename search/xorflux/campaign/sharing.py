"""Campaign pool: distinct elite DAGs per frontier point, and how workers use it.

Evidence (DESIGN.md section 1, from earlier versions): forced adoption of the global best collapsed
fleets onto a handful of DAGs (FOX Mu8: 10 workers on 4 DAGs while 90 distinct DAGs at the same
point sat in the records) and adopters rarely made the next step.  So the default policy is
**pull**: a worker takes a *distinct* elite from the pool only when its own restart controller
decides to restart, and never interrupts a running chain.

Two halves:

* :class:`PoolBook` (coordinator) keeps, per target and per nondominated point, up to
  ``sharing.pool_per_point`` distinct verified DAGs *per provenance group* and writes them
  atomically to ``pool/<target>.json``.  Entries reference record files; they are not copied.
* :class:`Pool` (worker) is what the engine receives as ``pool``: ``sample(exclude_keys, rng)``
  returns a distinct elite for a restart, as a dict with ``values`` and its attribution
  (``donor``, ``record``, ``dag_sha256``, ``gates``, ``depth``), or ``None`` when nothing fits;
  the engine calls it for its "shared" restart source.  The worker's records reach the
  coordinator through its ``records.jsonl`` (the engine's ``on_record`` callback saves them).

Modes (``sharing.mode``): ``pull`` (default) and ``off``.  ``sharing.scope = "group"`` restricts a
worker to elites from its own ``[[workers]]`` group (lineage-only sharing).  The old ``push``
mode (adopt strictly better elites mid-chain) was removed: it was kept only for comparison and
never used in a campaign.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..config.schema import Knob, Section
from .checkpoint import SCHEMA, atomic_json, file_hash, read_json, safe_join, utc_now
from .records import circuit_values, dominates, objective_key, score

KNOBS = Section("sharing", "How workers share elites through the campaign pool.", {
    "mode": Knob("pull", "pull: take a distinct pooled elite only when the engine restarts. "
                 "off: no sharing.", choices=("pull", "off")),
    "scope": Knob("target", "target: share with every worker on the same target matrix. group: "
                  "only with workers of the same [[workers]] group (lineage-only).",
                  choices=("target", "group")),
    "pool_per_point": Knob(64, "Distinct DAGs the coordinator keeps per frontier point and "
                           "provenance group (campaign-wide; read by the coordinator).", min=1),
    "sample_points": Knob(1, "Restart elites are drawn uniformly from the distinct DAGs at the "
                          "best this-many feasible pool points (by the worker's objective).", min=1),
    "exclude_own": Knob(True, "Never hand a worker its own records (they are already in its "
                        "archive, the engine's 'elite' restart source)."),
})


def pool_path(run_dir: Path, target: str) -> Path:
    """Where the pool of ``target`` lives."""
    return Path(run_dir) / "pool" / f"{target}.json"


# --------------------------------------------------------------------------------------------
# Coordinator side
# --------------------------------------------------------------------------------------------
class PoolBook:
    """The coordinator's in-memory pools, one per target, written as ``pool/<target>.json``.

    ``changes[target][point]`` accumulates what changed since the last ``write`` (records
    added, donors, points evicted) for the coordinator's ``pool`` events.
    """

    def __init__(self, run_dir: Path, per_point: int):
        self.run_dir = Path(run_dir)
        self.per_point = per_point
        # target -> (gates, depth) -> group -> list of entries (insertion order = discovery order)
        self.pools: dict[str, dict[tuple[int, int], dict[str, list[dict]]]] = {}
        self.versions: dict[str, int] = {}
        self.changes: dict[str, dict[tuple[int, int], dict]] = {}

    def add(self, target: str, entry: Mapping) -> bool:
        """Offer one verified record; True if the pool changed.

        Only nondominated points are kept; a new point evicts the points it dominates.
        A full (point, group) slot keeps its earliest DAGs: later ones carry no rank the
        coordinator could use, and a stable pool keeps restart sampling reproducible.
        """
        pool = self.pools.setdefault(target, {})
        point = (entry["gates"], entry["depth"])
        if any(dominates(q, point) for q in pool):
            return False
        slot = pool.setdefault(point, {}).setdefault(entry.get("group") or "", [])
        if len(slot) >= self.per_point or any(e["dag_sha256"] == entry["dag_sha256"] for e in slot):
            return False  # a full or duplicate slot is never empty, so the point stays valid
        change = self.changes.setdefault(target, {}).setdefault(point, {"added": [], "donor": [],
                                                                        "evicted": []})
        for q in [q for q in pool if dominates(point, q)]:
            del pool[q]
            change["evicted"].append(score(*q))
            self.changes[target].pop(q, None)
        slot.append({k: entry.get(k) for k in ("dag_sha256", "worker", "group", "path", "file_sha256",
                                               "gates", "depth", "ref", "t")})
        change["added"].append(entry["path"])
        if entry["worker"] not in change["donor"]:
            change["donor"].append(entry["worker"])
        return True

    def point_size(self, target: str, point: tuple[int, int]) -> tuple[int, int]:
        """(entries, distinct DAGs) at one point."""
        entries = [e for slot in self.pools.get(target, {}).get(point, {}).values() for e in slot]
        return len(entries), len({e["dag_sha256"] for e in entries})

    def summary(self, target: str) -> dict[str, int]:
        """``{"G@D": distinct DAG count}`` for one target."""
        return {f"{g}@{d}": self.point_size(target, (g, d))[1]
                for g, d in sorted(self.pools.get(target, {}))}

    def write(self, target: str, matrix_sha256: str) -> dict[tuple[int, int], dict]:
        """Atomically publish one target's pool file; returns and clears its pending changes."""
        self.versions[target] = self.versions.get(target, 0) + 1
        pool = self.pools.get(target, {})
        points = [{"gates": g, "depth": d,
                   "entries": [e for group in sorted(pool[(g, d)]) for e in pool[(g, d)][group]]}
                  for g, d in sorted(pool)]
        atomic_json(pool_path(self.run_dir, target), {
            "schema": SCHEMA, "target": target, "matrix_sha256": matrix_sha256,
            "version": self.versions[target], "updated_utc": utc_now(), "points": points})
        return self.changes.pop(target, {})


# --------------------------------------------------------------------------------------------
# Worker side
# --------------------------------------------------------------------------------------------
class Pool:
    """The engine's view of the campaign pool for one worker (see module docstring).

    ``spec`` is the worker's plan entry (objective, real depth cap, gate limit, group);
    ``cfg`` its ``sharing`` settings view.  ``search_cap`` is the depth the worker's chains may
    use (real cap + soft slack): pooled points up to it are usable, so a cap-5 worker searching
    at 6 can pull an 88@6 and repair it (2026-10-28: 65 distinct 88 DAGs pooled, 0 pulls; the
    real-cap filter excluded them all).  ``recorder`` (set by the worker once it exists)
    receives a ``pool_sample`` event naming the donor of each elite handed out, next to the
    engine's own ``pull`` event.
    """

    def __init__(self, run_dir: Path, spec: Mapping, matrix_sha256: str, cfg, backend, target,
                 input_count: int, search_cap=None):
        self.run_dir = Path(run_dir)
        self.spec = spec
        self.search_cap = search_cap if search_cap is not None else spec.get("depth_cap")
        self.matrix_sha256 = matrix_sha256
        self.mode = cfg.mode
        self.scope = cfg.scope
        self.sample_points = cfg.sample_points
        self.exclude_own = cfg.exclude_own
        self.backend = backend
        self.target = target
        self.input_count = input_count
        self.recorder = None
        self.path = pool_path(self.run_dir, spec["target"])
        self._stamp = None
        self._points: list[dict] = []
        self.version = 0
        self.stats = {"samples": 0, "sample_misses": 0, "rejected": 0}

    # ---- pool file -------------------------------------------------------------------------
    def refresh(self) -> None:
        """Re-read the pool file if it changed (its mtime and size)."""
        try:
            info = os.stat(self.path)
        except FileNotFoundError:
            return
        stamp = (info.st_mtime_ns, info.st_size)
        if stamp == self._stamp:
            return
        data = read_json(self.path, {}) or {}
        if data.get("matrix_sha256") != self.matrix_sha256:
            return  # never mix targets, whatever the file says
        self._stamp = stamp
        self._points = data.get("points", [])
        self.version = data.get("version", 0)

    def _feasible(self) -> list[dict]:
        """Pool points this worker may use (within its search cap), best first by its
        objective."""
        cap, limit = self.search_cap, self.spec.get("gate_limit")
        points = [p for p in self._points
                  if (cap is None or p["depth"] <= cap) and (limit is None or p["gates"] <= limit)]
        return sorted(points, key=lambda p: objective_key(self.spec["objective"], p["gates"], p["depth"]))

    def _eligible(self, entry: Mapping) -> bool:
        if self.exclude_own and entry.get("worker") == self.spec["id"]:
            return False
        if self.scope == "group" and entry.get("group") != self.spec.get("group"):
            return False
        return True

    def _load(self, entry: Mapping, exclude: Any) -> dict | None:
        """Load and independently verify one pooled record; None if unusable or excluded."""
        if entry["dag_sha256"] in exclude:
            return None
        try:
            path = safe_join(self.run_dir, entry["path"])
            if file_hash(path) != entry.get("file_sha256"):
                raise ValueError("hash drift")
        except (OSError, ValueError):
            self.stats["rejected"] += 1
            return None
        circuit = {k: v for k, v in (read_json(path) or {}).items() if k != "metadata"}
        checked = self.backend.verify(circuit, self.target, None)
        if not checked.get("equivalent"):
            self.stats["rejected"] += 1
            return None
        values = circuit_values(circuit, self.input_count)
        if frozenset(values) in exclude:
            return None
        return {"values": values, "gates": checked["gate_count"], "depth": checked["depth"],
                "dag_sha256": entry["dag_sha256"], "donor": entry.get("worker"),
                "group": entry.get("group"), "record": entry["path"], "ref": entry.get("ref"),
                "pool_version": self.version}

    def _candidates(self) -> list[dict]:
        out = []
        for point in self._feasible():
            entries = [e for e in point["entries"] if self._eligible(e)]
            if entries:
                out.extend(entries)
                if len({(e["gates"], e["depth"]) for e in out}) >= self.sample_points:
                    break
        return out

    def _note(self, elite: dict) -> None:
        if self.recorder is not None:
            self.recorder.event("pool_sample", donor=elite["donor"], record=elite["record"],
                                point=score(elite["gates"], elite["depth"]),
                                dag=elite["dag_sha256"], pool_version=elite["pool_version"])

    # ---- engine API ------------------------------------------------------------------------
    def sample(self, exclude_keys: Iterable = (), rng=None) -> dict | None:
        """A distinct pooled elite for a restart, or None.

        ``exclude_keys`` holds what the worker already has: value-set frozensets (the engine's
        archive keys) and/or DAG hashes.  ``rng`` (the engine's Random) makes the choice
        replayable given the same pool contents.  The pool is already bound to the worker's
        target by matrix hash.  The returned elite carries ``values`` (sorted masks) plus the
        attribution the engine logs: ``donor``, ``record``, ``dag_sha256``, ``gates``, ``depth``.
        """
        if self.mode == "off":
            return None
        self.refresh()
        exclude = exclude_keys if isinstance(exclude_keys, (set, frozenset)) else set(exclude_keys)
        candidates = self._candidates()
        if rng is not None:
            rng.shuffle(candidates)
        for entry in candidates:
            elite = self._load(entry, exclude)
            if elite is not None:
                self.stats["samples"] += 1
                self._note(elite)
                return elite
        self.stats["sample_misses"] += 1
        return None


class NullPool(Pool):
    """No campaign (``xorflux quick``): nothing to sample."""

    def __init__(self):  # deliberately skips Pool.__init__: no pool file
        self.recorder = None
        self.stats = {"samples": 0, "sample_misses": 0, "rejected": 0}

    def sample(self, exclude_keys: Iterable = (), rng=None) -> dict | None:
        """Always None."""
        return None
