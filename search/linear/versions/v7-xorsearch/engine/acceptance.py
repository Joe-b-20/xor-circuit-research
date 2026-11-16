"""Acceptance: decide whether the chain keeps a scored proposal.

Role in the method (DESIGN.md section 2): after a move edits the chain and the engine scores the
result, the acceptance policy says keep or undo.  Improving proposals are always kept.  Proposals
that keep the primary score (``objective.key(...)[0]``, i.e. gates for the gate objective) are
*neutral*: the plateau walk that produced every historical record lives on them, so they are kept
with probability ``neutral_p`` (1.0 by default).

Uphill proposals: threshold acceptance, by at most ``max_uphill`` primary units, and only while
the result stays within ``best_window`` of the chain best, with probability ``uphill_p``.  The
defaults reproduce the historical v2 walk (+1 slack within best+2 at p~0.15).  v2-lns/v2-translate,
which never went uphill, stayed nearest the incumbent in the framework runs, so the slack is kept
small.  (The simulated-annealing and late-acceptance policies were never configured in any
campaign and were removed, as was snapback: its +4 trigger lies outside the best+2 uphill
window, and it fired 0 times in the 120 workers of the 2026-10-28 campaigns.)

Costs are plain ints (the primary component of the objective key), so a decision is a few
comparisons and at most one ``rng.random()``; it runs once per proposal.
"""
from __future__ import annotations

from ..config.schema import Knob, Section

KNOBS = (
    Section("acceptance", "Which proposals the chain keeps.", {
        "neutral_p": Knob(1.0, "Probability of keeping a proposal with an unchanged primary score "
                          "(plateau moves; the walk that made every historical record relies on "
                          "them).", min=0, max=1),
    }),
    Section("acceptance.threshold", "Threshold acceptance of uphill proposals.", {
        "max_uphill": Knob(1, "Largest uphill step accepted, in primary units (v2 walk: +1).",
                           min=0),
        "best_window": Knob(2, "Uphill only while the result stays within this many primary "
                            "units of the chain best (v2 walk: best+2).", min=0),
        "uphill_p": Knob(0.15, "Probability of accepting an allowed uphill step (v2 walk ~0.15; "
                         "the catalog found this slack nearly inert, so it is low risk).",
                         min=0, max=1),
    }),
)


class Threshold:
    """Accept improvements and neutral moves; small uphill steps near the best, rarely.

    ``decide`` is the hot call; the rest runs on rare events.  ``cfg`` is the ``acceptance``
    settings view.
    """
    name = "threshold"

    def __init__(self, cfg):
        self.neutral_p = cfg.neutral_p
        sub = cfg.threshold
        self.max_uphill = sub.max_uphill
        self.window = sub.best_window
        self.uphill_p = sub.uphill_p
        self.best = 0

    def decide(self, cur: int, new: int, better: bool, rng) -> bool:
        """True to keep the proposal.  ``cur`` and ``new`` are primary costs; ``better`` is the
        full key comparison (``key_new < key_cur``), so depth tie-breaks count as
        improvements."""
        if better:
            return True
        d = new - cur
        if d <= 0:
            p = self.neutral_p
            return p >= 1.0 or (p > 0.0 and rng.random() < p)
        if d > self.max_uphill or new > self.best + self.window:
            return False
        return rng.random() < self.uphill_p

    def set_best(self, best: int) -> None:
        """A new chain started or its best improved (primary cost ``best``)."""
        self.best = best

    def summary(self) -> dict:
        """Small JSON-safe description for epochs and dossiers."""
        return {"kind": self.name, "best": self.best, "neutral_p": self.neutral_p}

    def state(self) -> dict:
        """JSON-safe state for checkpoints."""
        return {"best": self.best}

    def load_state(self, data: dict) -> None:
        """Restore ``state()``."""
        self.best = data.get("best", self.best)
