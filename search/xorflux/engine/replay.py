"""Replay one improvement from its dossier: rebuild the state before, re-run the move.

Role in the method (DESIGN.md section 1, last row: "89@4 not attributable; no RNG at
discovery").  A dossier's ``replay`` block (``dossier.DossierMixin._replay_info``) holds the
per-proposal seed, the search cap, the proposal work limit and, for moves with memory, a
snapshot of that memory taken after the proposal.  ``replay_dossier`` rebuilds the chain state
exactly as the engine builds states (``loop.canonical_state``: sorted values, trimmed), loads
the move memory, runs ``move.propose`` once on ``random.Random(seed)`` and compares the result
with ``values_after``.

What a match means: the improvement is a deterministic function of the recorded inputs, so its
cause can be re-examined (step through the move, change one parameter, ...).  A mismatch on a
``replayable = "exact"`` dossier means the move depends on something the dossier does not hold
(for example the iteration order of sets in an edited state); on ``"move_state"`` dossiers the
snapshot was taken after the proposal, which can differ from the memory the proposal saw.

Memory a proposal extends while it runs is undone from the trace before replaying: a move may
provide ``replay_state(snapshot, trace) -> snapshot``; otherwise ``PRE_PROPOSAL`` holds the
known cases.  ``lns.rebuild`` remembers the hash of every state it peeled (``peel_seen``) and
looks one hash up per proposal, so a proposal whose components include a peel saw that hash
absent: replaying it with an empty cache reproduces the peel, and its own ``pending`` record
of the change is dropped.  (Measured on fox_mu4: without this every LNS improvement that
peeled failed to replay; with it they reproduce.)  A move's first proposal (``move_calls`` 0)
ran on its freshly constructed memory and replays on a new instance (an LNS pool seeded from
the RNG on that first call would otherwise be skipped).

Usage (target, objective and settings are the frozen ones of the run)::

    result = replay_dossier(json.load(open(path)), target, objective, settings)
    result["match"], result["values"], result["trace"]
"""
from __future__ import annotations

import random

from ..core.budget import Budget
from ..moves.base import MoveContext
from .loop import canonical_state, valueset_factory


def _lns_pre_proposal(snapshot: dict, trace: dict) -> dict:
    """``lns.rebuild`` memory as the proposal saw it (see the module docstring)."""
    out = dict(snapshot)
    out["pending"] = [[], [], []]
    if any(str(c).startswith("peel") for c in (trace or {}).get("components") or ()):
        out["peel_seen"] = []
    return out


#: move name -> ``f(post-proposal snapshot, trace) -> snapshot the proposal saw``.
PRE_PROPOSAL = {"lns.rebuild": _lns_pre_proposal}


def pre_proposal_state(move, snapshot: dict, trace: dict) -> dict:
    """The move memory to load for a replay: the move's own ``replay_state`` hook, else the
    ``PRE_PROPOSAL`` rule for its name, else the snapshot unchanged."""
    hook = getattr(move, "replay_state", None)
    if callable(hook):
        return hook(snapshot, trace)
    rule = PRE_PROPOSAL.get(getattr(move, "name", None))
    return rule(snapshot, trace) if rule is not None else snapshot


def replay_dossier(dossier: dict, target, objective, settings, *, move=None,
                   state_factory=None, walk: bool = True) -> dict:
    """Re-run the proposal of ``dossier``; returns ``{match, reason, replayable, seed,
    after, expected, values, symdiff, trace}``.

    ``move`` defaults to a fresh instance of the registered move named in the dossier (its
    memory is loaded from ``replay.move_state`` when present).  ``state_factory`` defaults to
    the engine's ValueSet factory with the pair-sum counter set as for a run with walk moves
    (``walk``)."""
    replay = dossier.get("replay") or {}
    seed = replay.get("seed", (dossier.get("rng") or {}).get("seed"))
    values = dossier.get("values_before")
    out = {"id": dossier.get("id"), "move": dossier.get("move"),
           "replayable": replay.get("replayable"), "seed": seed, "match": False,
           "reason": None}
    if seed is None:
        out["reason"] = "no seed (engine.replay_seeds off, or a restart improvement)"
        return out
    if values is None:
        out["reason"] = "no values_before (telemetry.dossier_detail is not full)"
        return out
    if move is None:
        from ..moves.base import load_all
        cls = load_all().get(dossier.get("move"))
        if cls is None:
            out["reason"] = f"unknown move {dossier.get('move')!r}"
            return out
        move = cls(settings)
    if replay.get("move_calls") == 0:
        pass                                   # the move's first proposal: fresh memory
    elif replay.get("move_state") is not None:
        move.load_state(pre_proposal_state(move, replay["move_state"], dossier.get("trace")))
    elif "move_state" in (replay.get("reasons") or ()):
        out["reason"] = "move memory not stored (engine.replay_move_state is not full)"
    if state_factory is None:
        state_factory = valueset_factory(target, settings, walk)
    cap = replay.get("cap", objective.search_cap)
    state = canonical_state(state_factory, values, cap)
    if replay.get("level1_allowed") is not None:     # made in a pinned foundation phase
        state.restrict_level1(replay["level1_allowed"])
    limit = replay.get("work_limit")
    ctx = MoveContext(state=state, target=target, objective=objective, best_key=(),
                      rng=random.Random(seed), cfg=move.cfg,
                      budget=Budget(limit, None, None, settings["budget.check_every"]),
                      archive=None, phase=dossier.get("phase") or "plateau", settings=settings)
    before = state.key()
    proposal = move.propose(ctx)
    got = state.key()
    out["trace"] = None if proposal is None else proposal.trace
    out["values"] = sorted(got)
    out["after"] = {"gates": state.count() if hasattr(state, "count") else state.size(),
                    "depth": state.depth()}
    out["expected"] = dossier.get("after")
    expected = dossier.get("values_after")
    if expected is not None:
        # The own-depth polish ran after the proposal: its removals were the proposal's.
        expected = frozenset(expected).union((dossier.get("polish") or {}).get("removed", ()))
        out["match"] = got == expected
        out["symdiff"] = {"missing": sorted(expected - got), "extra": sorted(got - expected)}
    else:
        out["match"] = out["after"] == out["expected"]
    if not out["match"] and out["reason"] is None:
        out["reason"] = ("proposal returned nothing" if proposal is None or got == before
                         else "different result")
    return out
