"""Structural moves: wrappers over the vendored v2 coordinated-rewrite kernels.

Role in the method: walk and LNS change a few values at a time. These moves rewrite several
output equations together, keep every outside consumer and price the whole resulting circuit:

``structural.translate``  v2: XOR-translate both parent roles of a connected group of output
                          edges (optionally splitting shared parents into groups), then rebuild.
                          It was the top producer of depth-tradeoff frontier points (fox_mu4
                          129/6 and 130/5, Joltik 45/4, fox_mu8 601/7). Weight 0.2 (~2% of
                          time): 2026-10-28, 0.17 of the average weighted yield per CPU.
``structural.cores``      v2: rebuild several weight-3/5 values through pair/quartet cores with
                          joint pair optimisation. 1 improvement in 127 CPU-h (fox_mu8); some
                          tight new points in 2026-10-28 (Joltik, InvMixColumns). 0.2.
Neither runs in the burst phase: there they took ~72% of burst CPU for 25% of its yield.

(Numbers: docs/evidence/evidence-framework-runs.md and docs/evidence/campaigns-2026-10-28.md.)
All v3 kernels were removed after those campaigns. Component merge and interface basis took
~27% of the fleet's CPU between them for 3 worker bests and one step on one record lineage;
the backward package ~13% at weight 0.2 for 4 worker bests in ~110 CPU-h, at most 0.11x the
average weighted yield per CPU.

Adapter. The chain's ValueSet gives its live witness DAG (``state.gates()``), which is
converted to masks. The kernel runs within ``max_seconds`` (the kernels keep their wall-clock
budgets, so every proposal is ``deterministic=False``) plus its own trial limits. Its result is
replayed independently (``construct.verify_gates``) at the chain's cap and applied to
``ctx.state`` as a diff inside one journal (``apply_values``). Work units are the kernel's own
counts: trials plus constructible candidates.

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

TRANSLATE_KNOBS = Section("moves.structural.translate", "v2 coordinated output-edge translation.", {
    **_common(0.2, 0.0, 0.04), **_V2,
    "max_parent_edges": Knob(6, "Output edges translated together.", min=1),
})
CORES_KNOBS = Section("moves.structural.cores", "v2 joint core rebuild of weight-3/5 values.", {
    **_common(0.2, 0.0, 0.04), **_V2,
    "max_roots": Knob(4, "Weight-3/5 values rebuilt together.", min=1),
})
KNOBS = (TRANSLATE_KNOBS, CORES_KNOBS)


# ------------------------------------------------------------------------ shared adapters
def search_cap(objective):
    """The depth cap chains are searched at: ``Objective.search_cap`` (real cap + soft
    slack), falling back to a ``depth_cap`` or ``cap`` attribute for duck-typed objectives;
    None when there is no objective or no cap."""
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

    def _run(self, ctx, masks, targets, n, cap, seconds):
        """Call the kernel on the live gate masks; return ``(result gates or None, kernel
        stats, work units)``."""
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
        result, stats, work = self._run(ctx, _live_masks(gates, n), targets, n, cap, seconds)
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

    def _run(self, ctx, masks, targets, n, cap, seconds):
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

    def _run(self, ctx, masks, targets, n, cap, seconds):
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

