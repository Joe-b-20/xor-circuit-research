"""Depth repair: rebuild the chain's value set at a tighter depth deadline.

Role in the method
------------------
The evidence (DESIGN section 1) says: search on gates with a soft depth cap, then repair depth.
fox_mu4 129/7 -> 128/10 -> 128/7 took 0.14 h and Joltik 44/5 -> 43/10 -> 43/8 0.29 h, while the
cap-7 Joltik workers sat at 44/5 for 75 h because the cap ruled out the deeper intermediate.
The engine's ``repair`` phase (chain beats the worker best on gates but exceeds the real cap)
gives this move most of the weight; in the plateau phase it runs at a low weight as a depth
tie-break ("squeeze": same gates, one level shallower is a new Pareto point, and the historical
tie-breaks turned every 88 into a shallow record within seconds).

One proposal (``depth.repair``):

1. goal = the objective's real depth cap when the chain is deeper than it, else (``squeeze``)
   the chain depth - 1;
2. the kernel's earliest levels are exact for the current value set, so the set itself cannot
   meet a smaller goal: the bank is enlarged with *depth injections* (for every value too deep
   for the goal, v ^ a for shallow a whose sum is shallow enough by popcount) and random sums of
   shallow values;
3. the deadline-aware beam (``rebuild.reconstruct``) rebuilds the targets with deadline = goal,
   preferring kept values (cost 1) over injected ones (cost 2);
4. the result replaces U and is trimmed; its depth is at most the goal by construction.

There is no separate "reschedule": v2 re-ordered gates for minimum depth, which the kernel's
maintained earliest levels already are.

Trace fields: ``mode`` (cap | squeeze), ``goal``, ``depth_before``/``depth_after``,
``size_before``/``size_after``, ``extras``, ``deep`` (values above the goal's operand level),
``deadline`` (beam stats), ``removed``/``added``, ``reason`` when nothing changed.

Objective access: ``objective.depth_cap`` (the real cap; the state's own cap is the search cap,
``depth_cap`` + soft slack) and ``objective.kind`` (``depth_then_gates`` ranks depth first).
"""
from __future__ import annotations

from ..config.schema import Knob, Section
from ..core.target import min_depth
from .base import Move, Proposal, register
from .rebuild import (KNOBS as REBUILD_KNOBS, DeadlineParams, commit_choice, reconstruct,
                      trace_limit, value_diff)

KNOBS = Section("moves.depth.repair", "Deadline rebuild of the chain at a tighter depth.", {
    "weight": Knob(1.0, "Prior scheduler weight (time share) in the plateau phase (depth "
                   "tie-break; 2026-10-28: the highest weighted yield per CPU-h of any move, "
                   "2.8-18x the walk's, at 1-2% of CPU).", min=0),
    "burst_weight": Knob(0.5, "Scheduler weight in the burst phase (a new best is often "
                         "shallower one step later).", min=0),
    "repair_weight": Knob(1.0, "Weight within the repair phase's depth-family share.", min=0),
    "squeeze": Knob(True, "Also propose depth - 1 when the chain already fits the real cap (a "
                    "Pareto tie-break); False restricts the move to over-cap chains and "
                    "depth-first objectives."),
    "injections": Knob(6, "Depth injections v ^ a per too-deep value.", min=0),
    "shallow_pairs": Knob(24, "Random sums of two shallow values added to the bank.", min=0),
    "extra_cost": Knob(2, "Ranking cost of an injected value (kept values cost 1).", min=0),
    "max_states": Knob(800, "Beam states per call.", min=0),
})

_DEPTH_KINDS = ("depth_then_gates",)


def real_cap(objective):
    """The objective's real (publication) depth cap, or None (``Objective.depth_cap``)."""
    return getattr(objective, "depth_cap", None)


def depth_first(objective) -> bool:
    """True when the objective ranks depth before gates (``Objective.kind``)."""
    return getattr(objective, "kind", "gates") in _DEPTH_KINDS


@register
class DepthRepair(Move):
    """Rebuild at deadline = real cap (over-cap chain) or depth - 1 (squeeze)."""
    name = "depth.repair"
    family = "depth"
    knobs = KNOBS

    def __init__(self, settings):
        super().__init__(settings)
        c = self.cfg
        self.squeeze = bool(c.squeeze)
        self.injections = int(c.injections)
        self.shallow_pairs = int(c.shallow_pairs)
        self.extra_cost = int(c.extra_cost)
        self.beam = DeadlineParams(settings.view(REBUILD_KNOBS.path), max_states=int(c.max_states))
        self.limit = trace_limit(settings)

    def applicable(self, target, objective):
        if self.squeeze or real_cap(objective) is not None or depth_first(objective):
            return None
        return "no depth cap or depth objective and squeeze is off"

    def _goal(self, state, objective):
        """(goal depth, mode, current depth); goal None when there is nothing to aim for."""
        depth = state.depth()
        if depth is None:
            return None, None, None             # not ok(): nothing to rebuild from
        cap = real_cap(objective)
        if cap is not None and depth > cap:
            return cap, "cap", depth
        if depth > 0 and (self.squeeze or depth_first(objective)):
            return depth - 1, "squeeze", depth  # depth 0: every row is free already
        return None, None, depth

    def _bank(self, state, goal, rng):
        """Depth injections and shallow sums that give over-deep values shallower recipes."""
        level = state.level
        iset = state.iset
        tset = state.tset
        tri = state.tri
        # A demanded operand must sit at most goal - 1, so values deeper than that are "deep":
        # targets above the goal and helpers above goal - 1.
        deep = sorted(v for v, lv in level.items()
                      if v not in iset and (lv > goal if v in tset else lv > goal - 1))
        shallow = sorted(v for v, lv in level.items() if lv <= goal - 2)
        out = set()
        if shallow:
            ns = len(shallow)
            lim = 1 << max(goal - 1, 0)
            for v in deep:
                # v = a ^ (v ^ a) at level <= goal needs v ^ a at level <= goal - 1.
                for _ in range(self.injections):
                    m = v ^ shallow[rng.randrange(ns)]
                    if 1 < m.bit_count() <= lim:
                        out.add(m)
            # Two operands at level <= goal - 2 always give a sum at level <= goal - 1.
            for _ in range(self.shallow_pairs):
                m = shallow[rng.randrange(ns)] ^ shallow[rng.randrange(ns)]
                if m.bit_count() > 1:
                    out.add(m)
        return sorted(m for m in out if m not in tri), len(deep)

    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        goal, mode, depth0 = self._goal(state, ctx.objective)
        size0 = state.count()
        trace = {"components": ["depth.repair"], "mode": mode, "goal": goal,
                 "depth_before": depth0, "size_before": size0,
                 "params": {"mode": mode, "goal": goal, "injections": self.injections,
                            "shallow_pairs": self.shallow_pairs,
                            "max_states": self.beam.max_states}}
        if goal is None:
            trace["reason"] = "no_goal"
            return Proposal(self.name, None, trace, budget.used - work0)
        iset = state.iset
        if min_depth(state.targets) > goal:
            trace["reason"] = "goal_below_popcount_bound"
            return Proposal(self.name, None, trace, budget.used - work0)
        extras, deep = self._bank(state, goal, rng)
        trace.update(extras=len(extras), deep=deep)
        before = state.key()
        journal = state.journal()
        for m in extras:
            state.add(m)
        budget.tick(1 + len(extras))
        level = state.level
        if any(level.get(t, goal + 1) > goal for t in state.targets if t not in iset and t != 0):
            state.rollback(journal)
            trace["reason"] = "bank_too_deep"
            return Proposal(self.name, None, trace, budget.used - work0)
        cost = dict.fromkeys(extras, self.extra_cost)
        chosen, stats = reconstruct(state, rng, self.beam, budget, cap=goal, preferred=cost)
        trace["deadline"] = stats
        trace["components"] += ["inject", "rebuild.deadline"]
        if chosen is None:
            state.rollback(journal)
            trace["reason"] = "rebuild_failed"
            return Proposal(self.name, None, trace, budget.used - work0)
        commit_choice(state, chosen)
        trace["components"].append("trim")
        if state.key() == before:
            state.rollback(journal)
            trace["reason"] = "unchanged"
            return Proposal(self.name, None, trace, budget.used - work0)
        trace.update(value_diff(before, state, self.limit))
        trace["size_after"] = state.count()
        trace["depth_after"] = state.depth()
        return Proposal(self.name, journal, trace, budget.used - work0)
