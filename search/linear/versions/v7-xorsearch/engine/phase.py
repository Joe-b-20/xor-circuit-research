"""Phase controller: burst, plateau and repair.

Role in the method (DESIGN.md section 2): the loop never changes, only the move weights do.

``burst``
    Entered on every new chain best (and after a restart).  For ``burst_budget`` proposals (or
    work units, see ``unit``) every local move runs near uniformly from the new best.  Evidence:
    15 of 29 framework improvements came within <=374 iterations of a fresh start on a new best,
    and fox_mu4 took 7 of its 10 steps within 0.12 h of the previous one.
``plateau``
    The default: configured weights, reshaped by the adaptive scheduler.
``repair``
    The chain best beats the worker best but is infeasible under the real objective (it used
    the soft depth slack).  Depth-repair moves get ``repair_share`` of the probability until a
    feasible state is recorded or ``repair_budget`` runs out; then, with ``repair_revert``, the
    chain restarts from the worker best (the deep chain best is already a recorded frontier
    point).  Evidence: fox_mu4
    129/7 -> 128/10 -> 128/7 in 0.14 h and Joltik 44/5 -> 43/10 -> 43/8 in 0.29 h went through a
    deeper intermediate, while cap-7 Joltik workers sat at 44/5 for 75 h.  With
    ``repair_monotone`` the engine also rejects sideways moves that deepen the chain while
    repairing, so neutral drift does not undo the repair.  2026-10-28: 134 of 403 repairs ran
    the full 20,000 proposals without success (13% of fox_mu8 CPU), the chance of a late
    success fell to 0.16 after 10,000, and the failed chains stayed on their deep best: capped
    workers spent half their time there.

``phase_priors`` derives the three weight vectors from the moves' knobs:
``weight`` (plateau), optional ``burst_weight`` and ``repair_weight``.
"""
from __future__ import annotations

from ..config.schema import Knob, Section

KNOBS = Section("phase", "Burst / plateau / repair phases.", {
    "unit": Knob("proposals", "Phase budgets count proposals (replayable, default) or move work "
                 "units.", choices=("proposals", "work")),
    "burst_budget": Knob(400, "Burst length after a new chain best (framework: 15 of 29 "
                         "improvements within 374 iterations of a fresh start).", min=0),
    "burst_uniform": Knob(0.8, "Burst weights mix this share of uniform over local moves with "
                          "the rest of their burst/plateau weights.", min=0, max=1),
    "burst_families": Knob(["walk", "lns", "depth", "depth3", "structural"],
                           "Move families that run in the burst phase (only moves with a nonzero "
                           "burst weight)."),
    "burst_on_restart": Knob(True, "Start every restarted chain with a burst (fresh-start "
                             "harvest)."),
    "repair_budget": Knob(8000, "Repair-phase length (successful repairs: median 294-1,452 "
                          "proposals; P(success) 0.51 after 1,000 without one, 0.29 after "
                          "5,000).", min=0),
    "repair_revert": Knob(True, "When a repair runs out of budget, restart the chain from the "
                          "worker best instead of staying on the infeasible chain best."),
    "repair_share": Knob(0.8, "Probability mass given to repair-family moves while repairing.",
                         min=0, max=1),
    "repair_families": Knob(["depth"], "Move families that repair depth."),
    "repair_default_weight": Knob(1.0, "Repair weight of a repair-family move that declares no "
                                  "repair_weight knob.", min=0),
    "repair_monotone": Knob(True, "While repairing, reject non-improving moves that increase "
                            "depth."),
})

PLATEAU, BURST, REPAIR = "plateau", "burst", "repair"


def _knob(cfg, name, default=None):
    """A move knob, or ``default`` when the move does not declare it."""
    if cfg is None:
        return default
    return cfg.get(name, default)


def phase_priors(moves, cfg) -> dict[str, list[float]]:
    """``{phase: [weight per move]}`` from the moves' knobs and the ``phase`` view ``cfg``.

    ``moves`` are Move instances (``family`` and ``cfg`` are read).
    """
    plateau = [float(_knob(m.cfg, "weight", 0.0) or 0.0) for m in moves]

    # Burst: near-uniform over local moves that are switched on.
    local = set(cfg.burst_families)
    base = []
    for m, w in zip(moves, plateau):
        bw = _knob(m.cfg, "burst_weight")
        bw = w if bw is None else float(bw)
        base.append(bw if m.family in local and bw > 0 else 0.0)
    total = sum(base)
    k = sum(1 for b in base if b > 0)
    u = cfg.burst_uniform
    burst = [((1.0 - u) * b / total + u / k) if b > 0 else 0.0 for b in base] if k else plateau[:]

    # Repair: repair-family moves share `repair_share`, the rest keep their plateau proportions.
    fix = set(cfg.repair_families)
    rep = []
    for m, w in zip(moves, plateau):
        if m.family in fix:
            rw = _knob(m.cfg, "repair_weight")
            rep.append(float(cfg.repair_default_weight if rw is None else rw))
        else:
            rep.append(0.0)
    r_total = sum(rep)
    other_total = sum(w for m, w in zip(moves, plateau) if m.family not in fix)
    share = cfg.repair_share
    if r_total > 0:
        repair = []
        for m, w, r in zip(moves, plateau, rep):
            if m.family in fix:
                repair.append(share * r / r_total)
            else:
                repair.append((1.0 - share) * w / other_total if other_total > 0 else 0.0)
    else:
        repair = [0.0] * len(moves)
    return {PLATEAU: plateau, BURST: burst, REPAIR: repair}


class PhaseController:
    """Current phase and its remaining budget.

    ``can_repair`` is False when no repair-family move has weight or ``repair_budget`` is 0;
    the engine then never enters the repair phase (an infeasible chain best simply waits for
    the other moves).  ``repair_monotone`` is applied by the engine's acceptance step.
    """

    def __init__(self, cfg, priors):
        self.by_work = cfg.unit == "work"
        self.burst_budget = cfg.burst_budget
        self.repair_budget = cfg.repair_budget
        self.repair_revert = cfg.repair_revert
        self.burst_on_restart = cfg.burst_on_restart
        self.can_repair = sum(priors[REPAIR]) > 0 and self.repair_budget > 0
        self.can_burst = sum(priors[BURST]) > 0 and self.burst_budget > 0
        self.phase = PLATEAU
        self.left = 0
        self.entered = 0           # phase changes, for epochs

    def enter(self, phase: str) -> bool:
        """Switch to ``phase`` with a fresh budget; True if the phase name changed."""
        if phase == BURST and not self.can_burst:
            phase = PLATEAU
        if phase == REPAIR and not self.can_repair:
            phase = PLATEAU
        self.left = (self.burst_budget if phase == BURST
                     else self.repair_budget if phase == REPAIR else 0)
        changed = phase != self.phase
        self.phase = phase
        self.entered += changed
        return changed

    def on_chain_best(self, needs_repair: bool) -> bool:
        """A new chain best; ``needs_repair`` when it beats the worker best but is infeasible.
        True if the phase name changed.  A repair in progress keeps its budget."""
        if needs_repair and self.can_repair:
            if self.phase == REPAIR:
                return False
            return self.enter(REPAIR)
        return self.enter(BURST)

    def on_restart(self) -> bool:
        """A restarted chain; True if the phase name changed."""
        return self.enter(BURST if self.burst_on_restart else PLATEAU)

    def tick(self, work: int) -> bool:
        """Spend one proposal (or ``work`` units); True when the budget ran out and the
        controller fell back to plateau."""
        if self.phase == PLATEAU:
            return False
        self.left -= work if self.by_work else 1
        if self.left <= 0:
            self.phase = PLATEAU
            self.left = 0
            self.entered += 1
            return True
        return False

    def state(self) -> dict:
        """JSON-safe state."""
        return {"phase": self.phase, "left": self.left, "entered": self.entered}

    def load_state(self, data: dict) -> None:
        """Restore ``state()``."""
        self.phase = data.get("phase", PLATEAU)
        self.left = data.get("left", 0)
        self.entered = data.get("entered", 0)
