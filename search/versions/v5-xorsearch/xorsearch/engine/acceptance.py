"""Acceptance policies: decide whether the chain keeps a scored proposal.

Role in the method (DESIGN.md section 2): after a move edits the chain and the engine scores the
result, the acceptance policy says keep or undo.  Improving proposals are always kept.  Proposals
that keep the primary score (``objective.key(...)[0]``, i.e. gates for the gate objective) are
*neutral*: the plateau walk that produced every historical record lives on them, so they are kept
with probability ``neutral_p`` (1.0 by default).  Uphill proposals are the policy's business.

Policies (``acceptance.policy``):

``threshold`` (default)
    Uphill by at most ``max_uphill`` primary units, and only while the result stays within
    ``best_window`` of the chain best, with probability ``uphill_p``.  The defaults reproduce the
    historical v2 walk (+1 slack within best+2 at p~0.15).  v2-lns/v2-translate, which never went
    uphill, stayed nearest the incumbent in the framework runs, so the slack is kept small.
``anneal``
    Simulated annealing with geometric cooling and a reheat after ``reheat_after`` decisions
    without a chain-best improvement.  The historical LNS schedule (T0 1.2, cooling 0.9997) left
    the chain 5-10 gates above its best, so the defaults are cooler: at T0 = 0.5 a +1 step is taken
    with probability e^-2 ~ 0.14, close to the threshold policy, and +2 with ~0.02.
``late``
    Late-acceptance hill climbing: accept when not worse than the cost ``length`` decisions ago.

Every policy also answers ``snapback(cur, best)``: when the chain has drifted more than
``acceptance.snapback`` primary units above its best, the engine restores the chain best.

Costs are plain ints (the primary component of the objective key), so a decision is a few
comparisons and at most one ``rng.random()``; it runs once per proposal.
"""
from __future__ import annotations

import math

from ..config.schema import Knob, Section

KNOBS = (
    Section("acceptance", "Which proposals the chain keeps.", {
        "policy": Knob("threshold", "threshold: bounded uphill near the best (default). anneal: "
                       "simulated annealing with reheat. late: late-acceptance hill climbing.",
                       choices=("threshold", "anneal", "late")),
        "neutral_p": Knob(1.0, "Probability of keeping a proposal with an unchanged primary score "
                          "(plateau moves; the walk that made every historical record relies on "
                          "them).", min=0, max=1),
        "snapback": Knob(4, "Restore the chain best when the current primary score exceeds it by "
                         "more than this (v2 used 4-8, capped runs 3). Null disables.",
                         min=0, kind=int, nullable=True),
    }),
    Section("acceptance.threshold", "Threshold acceptance (default policy).", {
        "max_uphill": Knob(1, "Largest uphill step accepted, in primary units (v2 walk: +1).",
                           min=0),
        "best_window": Knob(2, "Uphill only while the result stays within this many primary "
                            "units of the chain best (v2 walk: best+2).", min=0),
        "uphill_p": Knob(0.15, "Probability of accepting an allowed uphill step (v2 walk ~0.15; "
                         "the catalog found this slack nearly inert, so it is low risk).",
                         min=0, max=1),
    }),
    Section("acceptance.anneal", "Simulated annealing.", {
        "t0": Knob(0.5, "Start and reheat temperature (historical 1.2 drifted 5-10 gates above "
                   "best; 0.5 takes +1 with p~0.14).", min=0),
        "cooling": Knob(0.9995, "Geometric cooling factor per decision.", min=0, max=1),
        "t_min": Knob(0.05, "Temperature floor.", min=0),
        "reheat_after": Knob(4000, "Decisions without a chain-best improvement before reheating "
                             "to t0 (historical: 4000).", min=1),
        "max_uphill": Knob(2, "Largest uphill step considered at all, in primary units.", min=0),
    }),
    Section("acceptance.late", "Late-acceptance hill climbing.", {
        "length": Knob(500, "History length (decisions) the candidate is compared against.",
                       min=1),
        "max_uphill": Knob(2, "Largest uphill step accepted, in primary units.", min=0),
    }),
)


class Acceptance:
    """Base policy.  ``decide`` is the hot call; the rest runs on rare events.

    ``cur`` and ``new`` are primary costs (ints); ``better`` is the full key comparison
    (``key_new < key_cur``), so depth tie-breaks count as improvements.
    """
    name = ""

    def __init__(self, cfg):
        self.neutral_p = cfg.neutral_p
        self.snap = cfg.snapback
        self.best = 0

    # -- hot path -------------------------------------------------------------------------
    def decide(self, cur: int, new: int, better: bool, rng) -> bool:
        """True to keep the proposal."""
        raise NotImplementedError

    def _neutral(self, rng) -> bool:
        p = self.neutral_p
        return p >= 1.0 or (p > 0.0 and rng.random() < p)

    # -- events ---------------------------------------------------------------------------
    def reset(self, cur: int, best: int) -> None:
        """A new chain (restart): forget the old trajectory."""
        self.best = best

    def set_best(self, best: int) -> None:
        """The chain best improved (primary cost ``best``)."""
        self.best = best

    def snapback(self, cur: int, best: int) -> bool:
        """True when the chain should return to its best."""
        snap = self.snap
        return snap is not None and cur > best + snap

    def temperature(self) -> float | None:
        """Current temperature (anneal only), for dossiers and epochs."""
        return None

    def summary(self) -> dict:
        """Small JSON-safe description for epochs and dossiers."""
        return {"kind": self.name, "best": self.best, "temperature": self.temperature(),
                "neutral_p": self.neutral_p, "snapback": self.snap}

    def state(self) -> dict:
        """JSON-safe state for checkpoints."""
        return {"policy": self.name, "best": self.best}

    def load_state(self, data: dict) -> None:
        """Restore ``state()``."""
        self.best = data.get("best", self.best)


class Threshold(Acceptance):
    """Accept improvements and neutral moves; small uphill steps near the best, rarely."""
    name = "threshold"

    def __init__(self, cfg):
        super().__init__(cfg)
        sub = cfg.threshold
        self.max_uphill = sub.max_uphill
        self.window = sub.best_window
        self.uphill_p = sub.uphill_p

    def decide(self, cur, new, better, rng):
        if better:
            return True
        d = new - cur
        if d <= 0:
            return self._neutral(rng)
        if d > self.max_uphill or new > self.best + self.window:
            return False
        return rng.random() < self.uphill_p


class Anneal(Acceptance):
    """Metropolis acceptance at a geometrically cooled temperature, reheated on stagnation."""
    name = "anneal"

    def __init__(self, cfg):
        super().__init__(cfg)
        sub = cfg.anneal
        self.t0 = sub.t0
        self.cooling = sub.cooling
        self.t_min = sub.t_min
        self.reheat_after = sub.reheat_after
        self.max_uphill = sub.max_uphill
        self.t = self.t0
        self.since_best = 0

    def decide(self, cur, new, better, rng):
        # Cool and count first so every decision advances the schedule exactly once.
        t = self.t * self.cooling
        self.t = t if t > self.t_min else self.t_min
        self.since_best += 1
        if self.since_best >= self.reheat_after:
            self.t = self.t0
            self.since_best = 0
        if better:
            return True
        d = new - cur
        if d <= 0:
            return self._neutral(rng)
        if d > self.max_uphill or self.t <= 0.0:
            return False
        return rng.random() < math.exp(-d / self.t)

    def reset(self, cur, best):
        super().reset(cur, best)
        self.t = self.t0
        self.since_best = 0

    def set_best(self, best):
        super().set_best(best)
        self.since_best = 0

    def temperature(self):
        return self.t

    def state(self):
        out = super().state()
        out.update(t=self.t, since_best=self.since_best)
        return out

    def load_state(self, data):
        super().load_state(data)
        self.t = data.get("t", self.t0)
        self.since_best = data.get("since_best", 0)


class LateAcceptance(Acceptance):
    """Accept when no worse than the current cost or the cost ``length`` decisions ago."""
    name = "late"

    def __init__(self, cfg):
        super().__init__(cfg)
        sub = cfg.late
        self.length = sub.length
        self.max_uphill = sub.max_uphill
        self.hist: list[int] = []
        self.pos = 0

    def decide(self, cur, new, better, rng):
        hist = self.hist
        if not hist:                       # first decision on a chain without reset()
            hist.extend([cur] * self.length)
        if better:
            ok = True
        else:
            d = new - cur
            if d <= 0:
                ok = self._neutral(rng)
            else:
                ok = d <= self.max_uphill and new <= hist[self.pos]
        # LAHC stores the cost the chain holds after this decision.
        hist[self.pos] = new if ok else cur
        self.pos = (self.pos + 1) % self.length
        return ok

    def reset(self, cur, best):
        super().reset(cur, best)
        self.hist = [cur] * self.length
        self.pos = 0

    def state(self):
        out = super().state()
        out.update(hist=list(self.hist), pos=self.pos)
        return out

    def load_state(self, data):
        super().load_state(data)
        self.hist = list(data.get("hist", []))
        self.pos = data.get("pos", 0)


POLICIES = {cls.name: cls for cls in (Threshold, Anneal, LateAcceptance)}


def make(cfg) -> Acceptance:
    """The policy named by ``acceptance.policy`` (``cfg`` is the ``acceptance`` view)."""
    return POLICIES[cfg.policy](cfg)
