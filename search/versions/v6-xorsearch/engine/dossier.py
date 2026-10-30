"""Improvements, records and dossiers: what the engine hands the recorder and the record writer.

Role in the method (DESIGN.md sections 2 and 4.5).  When a kept proposal makes a new worker best
or a new nondominated feasible point, the engine

1. counts it and updates the worker best / frontier (``_found``, called inside ``step`` with the
   chain state rebuilt from the new values, the old values read by one rollback);
2. after ``recorder.proposal`` (so the ring holds the improving proposal) asks the recorder to
   write the dossier and passes it a ``verify(id)`` callback that runs the ``on_record``
   callbacks (the campaign's verifying ``RecordWriter.save``) on the circuit; the verdict lands
   in the dossier's ``verification`` and the ``improve`` event's ``verified`` (``_report``);
3. undoes everything it counted when a verifier rejects the circuit and restarts the chain on a
   clean state (``_verification_failed``; strict workers raise instead).

A dossier answers "what found it" (move, ``trace.components`` and parameters, phase, scheduler
weights), "from where" (chain, root, lineage, distances to the chain best / root / worker best /
archive), "before" (``state_before``: plateau shape, acceptance state, ages), "during" (the
recorder's ring of recent proposals and its summary), "after" (``shape_after``, then the
recorder's follow-up events) and "can it be replayed" (``replay``).

Replay (``replay`` block, see telemetry/schema.md section 6).  With ``engine.replay_seeds`` every
proposal runs on ``random.Random(seed)`` for a fresh 63-bit ``seed`` drawn from the engine RNG.
A proposal is a function of (values before, search cap, seed, the move's knobs) plus the move's
own memory (LNS pool and hot list, depth3 partition) and, for structural
moves or ``budget.mode = "time"``, the wall clock.  Move memory can only be snapshotted after
the proposal (snapshotting it before every proposal would cost more than the proposals), so the
dossier says honestly what replay needs: ``replayable`` is ``exact`` (a work-bounded move that
is stateless or made its first proposal), ``move_state`` (the move has memory; the snapshot is
taken after the proposal and ``move_state_sha256`` identifies it) or ``no`` (wall clock, or no
seed), with ``reasons``.  ``engine.replay.replay_dossier`` re-runs a dossier, undoing what the
proposal added to the move's memory, and reports whether it reproduces.

Records: every new worker best and frontier point, and every ``record_stride``-th kept
state-changing move at the worker-best point (distinct DAGs, up to ``records_per_point``) go to
the ``on_record`` callbacks.  ``record["ref"]`` is the dossier id (or ``<worker>:it<N>`` for
sampled DAGs), so a record file links back to its dossier.

This module is a mixin of ``loop.Engine``; it reads the engine's attributes and adds no state of
its own besides what ``Engine._setup`` initialises.
"""
from __future__ import annotations

import hashlib
import json

from ..telemetry import metrics
from ..telemetry.recorder import verification_failed
from .archive import distance

REPLAY_RECIPE = ("state = make_state(values_before, replay.cap) (sorted values, trimmed); "
                 "move = registry[move](settings); move.load_state(replay.move_state); "
                 "ctx.rng = random.Random(replay.seed); ctx.budget = Budget(replay.work_limit); "
                 "move.propose(ctx); compare state.key() with values_after "
                 "(engine.replay.replay_dossier does this)")


def score(gates, depth) -> dict | None:
    """``{"gates": g, "depth": d}`` (telemetry scores are objects), or None."""
    if gates is None:
        return None
    return {"gates": gates, "depth": depth}


def state_digest(data) -> str:
    """SHA-256 of a JSON-safe value in canonical form (sorted keys, compact)."""
    text = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DossierMixin:
    """Improvement bookkeeping, dossiers and records for ``loop.Engine``."""

    # ------------------------------------------------------------------ records ---------
    def _record(self, kind, g, d, values, move_name, ident) -> dict:
        """The record handed to the on_record callbacks (the current state's circuit)."""
        gates, outputs = self.state.gates()
        gates = [[a, b] for a, b in gates]
        return {"kind": kind, "dossier": ident, "improvement": ident,
                "ref": ident or f"{self.worker_id}:it{self.it}",
                "circuit": {"inputCount": self._n, "gates": gates, "outputSignals": outputs,
                            "gateCount": len(gates), "depth": d},
                "gate_count": g, "depth": d, "values": sorted(values), "it": self.it,
                "move": move_name, "worker": self.worker_id, "chain": self._chain_label(),
                "root": self.root.get("id")}

    def _chain_label(self):
        """The recorder's chain id (``<worker>-cNNNN``) when it has one, else the engine's
        chain sequence number."""
        label = getattr(self.recorder, "chain_id", None)
        return label if isinstance(label, str) else self.chain_seq

    def _deliver(self, record):
        """Run the callbacks; ``(ok, last result)``."""
        result = None
        for callback in self._callbacks:
            result = callback(record)
            if verification_failed(result):
                return False, result
        return True, result

    def _sample_best_point(self, move_name) -> None:
        """Every ``record_stride``-th kept move at the worker-best point: record a new DAG."""
        if len(self._best_seen) >= self._records_per_point:
            return
        self._at_best += 1
        if self._at_best < self._record_stride:
            return
        self._at_best = 0
        key = self.state.key()
        h = hash(key)
        if h in self._best_seen:
            return
        self._best_seen.add(h)
        g, d = self.cur_g, self.cur_d
        self.archive.offer(key, g, d, self.cur_key, True, f"record{self.chain_seq}")
        if not self._callbacks:
            return
        ok, result = self._deliver(self._record("record", g, d, key, move_name, None))
        if not ok:
            self._verification_failed("record", None, result, None)
            return
        entry = result if isinstance(result, dict) else {}
        if entry.get("saved") is False:        # the writer skipped it (duplicate, point full)
            return
        self.counters["records"] += 1
        self.recorder.event("record", point=score(g, d), dag=entry.get("dag_sha256"),
                            record=entry.get("record") or entry.get("path"),
                            distinct_at_point=len(self._best_seen), move=move_name)

    # ------------------------------------------------------------------ dossiers --------
    def _state_before(self, before, phase) -> dict:
        """Search state just before an improving move (dossier ``state_before``)."""
        snap = self._plateau.snapshot(self.it, self._t) or {}
        proposals = snap.get("proposals") or 0
        wvalues = self.worker_best_values
        return {
            "phase": phase,
            "plateau": snap,
            "neutral_rate": (snap.get("neutral_accepts", 0) / proposals) if proposals else None,
            "acceptance": self.acceptance.summary(),
            "weights": self.scheduler.weights(phase),
            "cur": score(self.cur_g, self.cur_d),
            "chain_best": score(self.chain_best_g, self.chain_best_d),
            "worker_best": score(self.worker_best_g, self.worker_best_d),
            "dist_chain_best": distance(before, self.chain_best_values),
            "dist_root": distance(before, self.root_values),
            "dist_worker_best": None if wvalues is None else distance(before, wvalues),
            "dist_elites": self.archive.distance_stats(before),
            "archive": {"size": len(self.archive), **self.archive.diversity()},
            "chain_age": self.restarter.ages(self.it, self.work_total, self._t),
            "chain_improvements": self.chain_improvements,
        }

    def _replay_info(self, move, seed, deterministic) -> dict:
        """The dossier ``replay`` block (see the module docstring).

        ``move_calls`` is how many proposals the move made before this one (the scheduler's
        undiscounted pulls, checkpointed): at 0 its memory was the freshly constructed one, so
        the proposal replays exactly on a new instance whatever the move remembers."""
        reasons = []
        if seed is None:
            reasons.append("no_seed" if move is not None else "not_a_proposal")
        if not deterministic:
            reasons.append("wall_clock")
        info = {"seed": seed, "engine_seed": self.rng_seed, "cap": self._cap,
                "work_limit": self._proposal_work, "recipe": REPLAY_RECIPE}
        if move is not None:
            calls = self.scheduler.pulls[self._moves.index(move)]
            info["move_calls"] = calls
            state = move.state() if calls else None
            if state:
                reasons.append("move_state")
                mode = self._replay_move_state
                if mode != "off":
                    info["move_state_sha256"] = state_digest(state)
                if mode == "full":
                    info["move_state"] = state
        if "no_seed" in reasons or "wall_clock" in reasons or "not_a_proposal" in reasons:
            info["replayable"] = "no"
        elif "move_state" in reasons:
            info["replayable"] = "move_state"
        else:
            info["replayable"] = "exact"
        info["reasons"] = reasons
        return info

    def _found(self, move, trace, work, deterministic, seed, phase, before, g0, d0,
               worker, proposal_s=None) -> dict:
        """The (rebuilt) chain state is a new worker best or frontier point: count it and
        return the dossier fields (sent after ``recorder.proposal``, see ``_report``).

        ``move`` is the Move (None for an improvement made by a restart itself)."""
        self._t = self.recorder.now()
        st = self.state
        g1, d1 = st.size(), st.depth()
        key1 = self._key(g1, d1)
        after = st.key()
        wg, wd = self.worker_best_g, self.worker_best_d
        if not worker:
            kind = "frontier"
        elif self._depth_first:
            kind = "depth" if wd is None or d1 < wd else "gates"
        else:
            kind = "gates" if wg is None or g1 < wg else "depth"
        deterministic = deterministic and not self._time_budget
        name = move.name if move is not None else trace["components"][0]
        dossier = {
            "kind": kind, "it": self.it,
            "before": score(g0, d0), "after": score(g1, d1),
            "worker_best_before": score(wg, wd),
            "move": name, "family": move.family if move is not None else "restart",
            "phase": phase, "trace": trace, "work": work, "proposal_s": proposal_s,
            "deterministic": deterministic,
            "chain": {"source": self.source, "root": self.root, "engine_chain": self.chain_seq,
                      "donor": self.donor},
            "state_before": None if before is None else self._state_before(before, phase),
            "values_before": None if before is None else sorted(before),
            "values_after": sorted(after),
            "rng": {"seed": seed, "engine_seed": self.rng_seed},
            "replay": self._replay_info(move, seed, deterministic),
            "verification": None,
        }
        if self.donor is not None:
            dossier["lineage"] = {"donor": self.donor}
        saved = (self.worker_best_key, self.worker_best_values, wg, wd, list(self.frontier),
                 set(self._best_seen))
        if worker:
            self._set_worker_best(g1, d1, key1, after)
            self.counters["improvements"] += 1
        else:
            self._add_frontier(g1, d1)
            self.counters["frontier"] += 1
        return {"dossier": dossier, "saved": saved, "before": before, "after": after,
                "point": (g1, d1), "worker": worker}

    def _report(self, found: dict) -> bool:
        """Write the dossier (after ``recorder.proposal``, so the ring holds the improving
        proposal) with the callbacks' verification in it.  False when a callback rejected the
        circuit (everything ``_found`` counted is then undone and the chain restarted)."""
        dossier = found["dossier"]
        g1, d1 = found["point"]
        record = self._record(dossier["kind"], g1, d1, found["after"], dossier["move"], None)
        dossier["gates_after"] = record["circuit"]["gates"]
        dossier["outputs"] = record["circuit"]["outputSignals"]
        dossier["shape_after"] = metrics.shape_from_gates(dossier["gates_after"],
                                                          dossier["outputs"], self._n)
        verdict = []

        def verify(ident):
            record["dossier"] = record["improvement"] = record["ref"] = ident
            ok, result = self._deliver(record)
            verdict.append((ok, result))
            return result

        ident = self.recorder.improvement(dossier, verify=verify if self._callbacks else None)
        if verdict and not verdict[0][0]:
            self._flush_plateau(None)
            self._verification_failed(dossier["kind"], ident, verdict[0][1], found)
            return False
        self.last_improvement = ident
        self._flush_plateau(ident)             # the plateau this improvement closed, if any
        return True

    def _verification_failed(self, kind, ident, result, found) -> None:
        """A verifier rejected a state the kernel called valid: undo what it counted and
        restart on a clean state (a kernel bug; strict workers raise instead)."""
        self.counters["verify_fail"] += 1
        self.recorder.event("verify_fail", kind=kind, id=ident, point=score(self.cur_g, self.cur_d),
                            result=result)
        values = self.worker_best_values
        if found is not None:
            wkey, wvalues, wg, wd, frontier, seen = found["saved"]
            self.worker_best_key, self.worker_best_values = wkey, wvalues
            self.worker_best_g, self.worker_best_d = wg, wd
            self.frontier, self._best_seen = frontier, seen
            self._dominated = None             # the frontier shrank: the cache may be stale
            self.counters["improvements" if found["worker"] else "frontier"] -= 1
            values = found["before"] if found["before"] is not None else wvalues
        if values is not None:
            self._restart("verify_fail", forced=(values, "best", {"id": "verified"}, None))
