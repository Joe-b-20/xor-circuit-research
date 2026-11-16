"""Objective: what "better" means for a campaign, and which caps the search state uses.

Role in the method
------------------
Every score in the engine is ``objective.key(gates, depth)``: a tuple, lower is better,
compared lexicographically.  ``feasible`` applies the *real* constraints (the published depth
cap and an optional gate limit); only feasible states become records.  ``search_cap`` is the
cap given to the ``ValueSet`` during search: the real cap plus a soft slack.

Why a slack: the framework evidence of earlier versions (recommendation 6)
showed that gate reductions often pass through states slightly deeper than the cap
(129/7 -> 128/10 -> 128/7 in 0.14 h, while a hard-capped chain stalled for 75 h).  So a
``gates`` objective searches at cap + slack (default 1) and the engine's repair phase squeezes
depth back under the real cap before recording.  ``depth_then_gates`` minimises depth first, so
its slack defaults to 0.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config.schema import Knob, Section

KINDS = ('gates', 'depth_then_gates')

KNOBS = Section("objective", "What the search minimises and under which caps.", {
    "kind": Knob("gates", "gates: fewest gates, depth breaks ties. depth_then_gates: shallowest "
                 "circuit, gates break ties.", choices=KINDS),
    "depth_cap": Knob(None, "Real output-depth cap; records must meet it (null: none).",
                      kind=int, nullable=True, min=0),
    "gate_limit": Knob(None, "Records must have at most this many gates (null: none).",
                       kind=int, nullable=True, min=0),
    "soft_depth_slack": Knob(None, "Extra depth allowed during search above depth_cap "
                             "(null: the kind's default below).", kind=int, nullable=True,
                             min=0),
    "default_slack_gates": Knob(1, "Soft slack for the gates objective when soft_depth_slack is "
                                "null. Repair success falls fast with distance above the cap "
                                "(2026-10-29 rerun: FOX Mu8 0.63/0.42/0.22/0.09 at cap+1..+4, "
                                "small targets 0.19 at cap+1 vs 0.04 at cap+2); FOX Mu4 cap 7 "
                                "from roots reached 121@7 in 4 of 18 workers at slack 1, 0 of 18 "
                                "at slack 6. Deep frontier points come from higher-cap groups.",
                                min=0),
    "default_slack_depth_then_gates": Knob(0, "Soft slack for depth_then_gates when "
                                           "soft_depth_slack is null.", min=0),
    "hard_cap_margin": Knob(1, "When soft_depth_slack is null, the slack is at most the cap "
                            "minus (the target's minimum depth + this): 0 at or just above the "
                            "minimum depth, then growing by one per level up to the kind's "
                            "default. Near the minimum depth the deeper basin is far smaller "
                            "(MixColumns: 88@5 vs 97@3, 88@6 vs 89@4), so slack chains never "
                            "came back (2026-10-28: every cap-3/cap-4 chain sat at depth 5/6; "
                            "slack 1 helped cap 5). -1 = no limit.", min=-1),
})


@dataclass(frozen=True)
class Objective:
    """Score keys, caps and feasibility for one campaign or worker group.

    ``kind``              ``"gates"`` or ``"depth_then_gates"``
    ``depth_cap``         real output-depth cap (None: unconstrained)
    ``gate_limit``        real gate limit (None: unconstrained)
    ``soft_depth_slack``  extra depth the search state may use above ``depth_cap``
    """
    kind: str = 'gates'
    depth_cap: int | None = None
    gate_limit: int | None = None
    soft_depth_slack: int = 0

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError('objective kind must be one of %s' % (KINDS,))
        for name in ('depth_cap', 'gate_limit'):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('%s must be a nonnegative int or None' % name)
        if type(self.soft_depth_slack) is not int or self.soft_depth_slack < 0:
            raise ValueError('soft_depth_slack must be a nonnegative int')

    @classmethod
    def from_settings(cls, settings, min_depth=None, **overrides):
        """Objective from the ``objective`` knobs (a Settings or its ``view('objective')``);
        keyword overrides win (e.g. a worker group's ``depth_cap``).  ``min_depth`` is the
        target's depth lower bound, for ``hard_cap_margin`` (None: the margin never applies)."""
        cfg = settings.view('objective') if hasattr(settings, 'view') else settings
        kind = overrides.get('kind', cfg.kind)
        cap = overrides.get('depth_cap', cfg.depth_cap)
        slack = overrides.get('soft_depth_slack', cfg.soft_depth_slack)
        if slack is None:
            slack = (cfg.default_slack_gates if kind == 'gates'
                     else cfg.default_slack_depth_then_gates)
            margin = cfg.hard_cap_margin
            if cap is not None and min_depth is not None and margin >= 0:
                slack = max(0, min(slack, cap - min_depth - margin))
        return cls(kind, cap, overrides.get('gate_limit', cfg.gate_limit), slack)

    def key(self, gates, depth):
        """Score tuple, lower is better: (gates, depth) or (depth, gates) by ``kind``."""
        if self.kind == 'gates':
            return (gates, depth)
        return (depth, gates)

    def feasible(self, gates, depth):
        """True when the real depth cap and gate limit are met (what a record needs)."""
        if self.depth_cap is not None and depth > self.depth_cap:
            return False
        if self.gate_limit is not None and gates > self.gate_limit:
            return False
        return True

    @property
    def search_cap(self):
        """Depth cap for the search state: ``depth_cap + soft_depth_slack``, or None."""
        if self.depth_cap is None:
            return None
        return self.depth_cap + self.soft_depth_slack
