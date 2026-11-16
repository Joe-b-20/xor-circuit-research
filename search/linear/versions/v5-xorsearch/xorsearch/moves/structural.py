"""Structural moves: wrappers over the vendored v2/v3 coordinated-rewrite kernels.

Role in the method: walk and LNS change a few values at a time. These moves rewrite several
output equations together, keep every outside consumer and price the whole resulting circuit:

``structural.translate``  v2: XOR-translate both parent roles of a connected group of output
                          edges (optionally splitting shared parents into groups), then rebuild.
                          It was the top producer of depth-tradeoff frontier points (fox_mu4
                          129/6 and 130/5, Joltik 45/4, fox_mu8 601/7). Default weight 0.5.
``structural.cores``      v2: rebuild several weight-3/5 values through pair/quartet cores with
                          joint pair optimisation. 1 improvement in 127 CPU-h (fox_mu8). 0.2.
``structural.component``  v3 component merge: translate one output-edge component onto
                          another's parents. 0 improvements, 0.00 proposals/iteration on AES
                          and Joltik. Off (0).
``structural.interface``  v3 interface basis: rebuild a 2-3 signal interface in a new basis and
                          re-express every consumer. 1 frontier point in 127 CPU-h. Off (0).
``structural.backward``   v3 backward package: rebuild 2-3 outputs from a shared new
                          companion. 0 improvements. Off (0).

(Numbers: docs/evidence/evidence-framework-runs.md.) The v3 moves stay available and every
vendored knob is a Knob, so a campaign can switch them on.

Adapter. The chain's ValueSet gives its live witness DAG (``state.gates()``), which is
converted to masks or index pairs. The kernel runs within ``max_seconds`` (the kernels keep their
wall-clock budgets, so every proposal is ``deterministic=False``) plus its own node/trial limits.
Its result is replayed independently (``construct.verify_gates``) at the chain's cap and applied
to ``ctx.state`` as a diff inside one journal (``apply_values``). Work units are the kernel's own
counts: trials plus constructible candidates for v2, search nodes for v3.

ValueSet API used beyond DESIGN.md 4.2 (all public in ``core/valueset.py``): the attributes
``n``, ``rows``, ``targets`` (distinct nonzero rows) and ``cap`` (the chain's search cap), and
``retain(keep)``. The journal opened by ``apply_values`` is left open; the engine commits or
rolls it back.
"""
from __future__ import annotations

import time

from ..config.schema import Knob, Section
from .base import Move, Proposal, register
from .construct import target_rows, verify_gates

_MAX_N = 64     # the vendored kernels validate masks as unsigned 64-bit integers


def _common(weight: float, burst: float, seconds: float) -> dict:
    return {
        "weight": Knob(weight, "Prior scheduler weight in the plateau phase.", min=0),
        "burst_weight": Knob(burst, "Scheduler weight in the burst phase.", min=0),
        "max_seconds": Knob(seconds, "Wall-clock limit of one kernel call (it is also capped "
                            "by the proposal budget's deadline).", min=0),
        "objective": Knob("gates", "Kernel ranking of its candidates: gates (then depth) or "
                          "depth_then_gates.", choices=("gates", "depth_then_gates")),
    }


_V2 = {
    "root_trials": Knob(8, "Translations or core groups tried per call.", min=1),
    "constructor_seconds": Knob(0.03, "Seconds for the deadline-beam clean-up of each "
                                "constructible candidate.", min=0),
}

_V3_CONSTRUCTOR = {
    "max_nodes": Knob(3000, "Search nodes per call.", min=0),
    "max_trials": Knob(24, "Candidate rewrites per call.", min=0),
    "constructor_branch_factor": Knob(12, "Recipes tried per value by the backtracking "
                                      "constructor.", min=0),
    "constructor_known_limit": Knob(64, "Known-signal anchors ranked per value.", min=0),
    "constructor_raw_splits": Knob(12, "Raw support splits tried per value.", min=0),
    "constructor_max_new": Knob(32, "New gates one reconstruction may create.", min=0),
    "constructor_attempts": Knob(2, "Constructor restarts per candidate.", min=0),
}

TRANSLATE_KNOBS = Section("moves.structural.translate", "v2 coordinated output-edge translation.", {
    **_common(0.5, 0.5, 0.04), **_V2,
    "max_parent_edges": Knob(6, "Output edges translated together.", min=1),
})
CORES_KNOBS = Section("moves.structural.cores", "v2 joint core rebuild of weight-3/5 values.", {
    **_common(0.2, 0.2, 0.04), **_V2,
    "max_roots": Knob(4, "Weight-3/5 values rebuilt together.", min=1),
})
COMPONENT_KNOBS = Section("moves.structural.component", "v3 component merge (off by default).", {
    **_common(0.0, 0.0, 0.04), **_V3_CONSTRUCTOR,
    "max_merge_pairs": Knob(48, "Component pairs (moving, fixed) considered.", min=0),
    "max_merge_vertices": Knob(16, "Parent vertices per side used to form translations.", min=0),
})
INTERFACE_KNOBS = Section("moves.structural.interface", "v3 interface basis change (off).", {
    **_common(0.0, 0.0, 0.04), **_V3_CONSTRUCTOR,
    "max_interface_sets": Knob(12, "Interfaces tried per call.", min=0),
    "interface_sizes": Knob([2, 3], "Interface sizes (2 and/or 3 signals)."),
    "interface_signal_limit": Knob(18, "Candidate interface signals (high fan-out first).",
                                   min=0),
    "basis_matrix_limit": Knob(168, "Basis matrices tried per interface (6 exist for 2 "
                               "signals, 168 for 3).", min=0),
    "interface_sets": Knob(None, "Explicit interfaces (lists of existing gate masks); null = "
                           "choose automatically.", kind=list, nullable=True),
    "basis_matrices": Knob(None, "Explicit basis matrices (row bitmasks); null = all, "
                           "shuffled.", kind=list, nullable=True),
})
BACKWARD_KNOBS = Section("moves.structural.backward", "v3 backward output package (off).", {
    **_common(0.0, 0.0, 0.04), **_V3_CONSTRUCTOR,
    "package_sizes": Knob([2, 3], "Outputs packaged together (2 and/or 3)."),
    "package_anchor_limit": Knob(48, "Anchors tried per output group.", min=0),
    "package_group_limit": Knob(24, "Output groups tried per call.", min=0),
})

KNOBS = (TRANSLATE_KNOBS, CORES_KNOBS, COMPONENT_KNOBS, INTERFACE_KNOBS, BACKWARD_KNOBS)


# ------------------------------------------------------------------------ shared adapters
def search_cap(objective):
    """The depth cap chains are searched at, read from an Objective.

    Assumption (core/objective.py was not written yet): the first non-None attribute among
    ``search_cap``, ``depth_cap`` and ``cap``; None when there is no objective or no cap.
    """
    for name in ("search_cap", "depth_cap", "cap"):
        value = getattr(objective, name, None)
        if value is not None:
            return value
    return None


def apply_values(state, values):
    """Make the chain's value set equal ``values`` (plus inputs) as one journaled diff.

    New values are added first, lightest first so that most operands already exist. The old
    values go after, in one ``retain`` (targets always stay in U). Adding first means removing
    never strands a target that the new circuit realizes. ``trim()`` then drops anything the
    witness DAG no longer uses, which can only lower the count. Returns
    ``(journal, added, removed)``, the journal still open for the engine to commit or roll
    back, plus the sorted value lists. The journal is None and nothing is touched when the
    value sets are already equal.
    """
    new = {v for v in values if v & (v - 1)}          # non-zero, non-unit
    new.update(t for t in state.targets if t & (t - 1))
    old = set(state.key())
    added = sorted(new - old)
    removed = sorted(old - new)
    if not added and not removed:
        return None, [], []
    journal = state.journal()
    for w in sorted(added, key=int.bit_count):
        state.add(w)
    if removed:
        state.retain(new)
    state.trim()
    return journal, added, removed


def _live_masks(gates, n):
    """Gate output masks of an index-pair circuit over n inputs."""
    masks = [1 << i for i in range(n)]
    for a, b in gates:
        masks.append(masks[a] ^ masks[b])
    return masks[n:]


def _seconds(cfg, budget) -> float:
    """``max_seconds`` clipped to the proposal budget's deadline, if it has one."""
    seconds = cfg.max_seconds
    deadline = getattr(budget, "deadline", None)
    if deadline is not None:
        seconds = min(seconds, max(0.0, deadline - time.monotonic()))
    return seconds


class _Structural(Move):
    """Shared propose(): ValueSet -> kernel -> verified result -> journaled diff."""
    family = "structural"
    kernel = ""

    def applicable(self, target, objective) -> str | None:
        n, _ = target_rows(target)
        if n > _MAX_N:
            return f"vendored kernels are 64-bit (n = {n})"
        return None

    def _run(self, ctx, gates, masks, targets, n, cap, seconds):
        """Call the kernel; return ``(result gates or None, kernel stats, work units)``."""
        raise NotImplementedError

    def propose(self, ctx) -> Proposal | None:
        state = ctx.state
        if not state.ok() or state.n > _MAX_N:
            return None
        seconds = _seconds(self.cfg, ctx.budget)
        if seconds <= 0:
            return None
        n, cap = state.n, state.cap
        targets = [t for t in state.targets if t]
        params = {k: v for k, v in self.cfg.as_dict().items()
                  if k not in ("weight", "burst_weight")}
        params["max_seconds"] = seconds
        trace = {"components": [self.name, self.kernel], "params": params}
        gates, _ = state.gates()
        started = time.monotonic()
        result, stats, work = self._run(ctx, gates, _live_masks(gates, n), targets, n, cap,
                                        seconds)
        trace["kernel_seconds"] = time.monotonic() - started
        trace["kernel"] = stats
        if ctx.budget is not None:
            ctx.budget.tick(work)
        if result is None:      # the kernel found no distinct complete circuit in its budget
            return Proposal(self.name, None, trace, work, deterministic=False)
        try:
            verify_gates(n, targets, result, cap)
        except AssertionError as exc:     # a kernel bug must never reach the chain
            trace["invalid"] = str(exc)
            ctx.stats["invalid"] = ctx.stats.get("invalid", 0) + 1
            return Proposal(self.name, None, trace, work, deterministic=False)
        journal, added, removed = apply_values(state, _live_masks(result, n))
        trace["added"], trace["removed"] = added, removed
        # The result may be neutral or uphill as well as downhill; the engine's acceptance decides.
        trace["kernel_gates"] = len(result)
        return Proposal(self.name, journal, trace, work, deterministic=False)


@register
class Translate(_Structural):
    """``structural.translate``: v2 ``propose(kind='translate')``."""
    name = "structural.translate"
    knobs = TRANSLATE_KNOBS
    kernel = "v2.translate"

    def _run(self, ctx, gates, masks, targets, n, cap, seconds):
        from ..vendor import v2_structured_search as v2s
        cfg = self.cfg
        stats = {}
        result = v2s.propose(set(masks), cap, rng=ctx.rng, max_seconds=seconds,
                             max_parent_edges=cfg.max_parent_edges, root_trials=cfg.root_trials,
                             constructor_budget=cfg.constructor_seconds, kind="translate",
                             targets=targets, inputs=[1 << i for i in range(n)], stats=stats,
                             objective=cfg.objective, source_depth_cap=cap)
        work = 1 + stats.get("attempted", 0) + stats.get("constructible", 0)
        return (None if result is None else result["gates"]), stats, work


@register
class Cores(_Structural):
    """``structural.cores``: v2 ``propose(kind='cores')``."""
    name = "structural.cores"
    knobs = CORES_KNOBS
    kernel = "v2.cores"

    def _run(self, ctx, gates, masks, targets, n, cap, seconds):
        from ..vendor import v2_structured_search as v2s
        cfg = self.cfg
        stats = {}
        result = v2s.propose(set(masks), cap, rng=ctx.rng, max_seconds=seconds,
                             root_trials=cfg.root_trials, max_roots=cfg.max_roots,
                             constructor_budget=cfg.constructor_seconds, kind="cores",
                             targets=targets, inputs=[1 << i for i in range(n)], stats=stats,
                             objective=cfg.objective, source_depth_cap=cap)
        work = 1 + stats.get("attempted", 0) + stats.get("constructible", 0)
        return (None if result is None else result["gates"]), stats, work


class _V3(_Structural):
    """Shared call into v3 ``advanced_moves.propose``."""
    v3_kind = ""
    v3_knobs: tuple = ()

    def _run(self, ctx, gates, masks, targets, n, cap, seconds):
        from ..vendor import v3_advanced_moves as v3
        cfg = self.cfg
        knobs = {name: cfg[name] for name in _V3_CONSTRUCTOR}
        knobs.update({name: cfg[name] for name in self.v3_knobs})
        knobs["max_seconds"] = seconds
        if knobs.get("interface_sets") is not None:
            # The kernel rejects (ValueError) interfaces that are not gates of the current
            # circuit; a configured list outlives the chain's edits, so keep the valid ones.
            present = set(masks)
            knobs["interface_sets"] = [g for g in knobs["interface_sets"]
                                       if set(g) <= present and len(set(g)) == len(g)]
        budget = ctx.budget
        stop = getattr(budget, "stop", None)
        steps, metrics = v3.propose(self.v3_kind, gates, targets, n, cap, ctx.rng, knobs,
                                    should_stop=stop, objective=cfg.objective,
                                    source_depth_cap=cap)
        return steps, metrics, 1 + metrics.get("nodes", 0)


@register
class Component(_V3):
    """``structural.component``: v3 ``component_merge``."""
    name = "structural.component"
    knobs = COMPONENT_KNOBS
    kernel = "v3.component_merge"
    v3_kind = "component_merge"
    v3_knobs = ("max_merge_pairs", "max_merge_vertices")


@register
class Interface(_V3):
    """``structural.interface``: v3 ``interface_basis``."""
    name = "structural.interface"
    knobs = INTERFACE_KNOBS
    kernel = "v3.interface_basis"
    v3_kind = "interface_basis"
    v3_knobs = ("max_interface_sets", "interface_sizes", "interface_signal_limit",
                "basis_matrix_limit", "interface_sets", "basis_matrices")


@register
class Backward(_V3):
    """``structural.backward``: v3 ``backward_package``."""
    name = "structural.backward"
    knobs = BACKWARD_KNOBS
    kernel = "v3.backward_package"
    v3_kind = "backward_package"
    v3_knobs = ("package_sizes", "package_anchor_limit", "package_group_limit")
