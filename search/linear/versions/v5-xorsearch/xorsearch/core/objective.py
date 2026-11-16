"""Objective: what "better" means for a campaign, and which caps the search state uses.

Role in the method
------------------
Every score in the engine is ``objective.key(gates, depth)``: a tuple, lower is better,
compared lexicographically.  ``feasible`` applies the *real* constraints (the published depth
cap and an optional gate limit); only feasible states become records.  ``search_cap`` is the
cap given to the ``ValueSet`` during search: the real cap plus a soft slack.

Why a slack: the framework evidence (docs/evidence/evidence-framework-runs.md, recommendation 6)
showed that gate reductions often pass through states slightly deeper than the cap
(129/7 -> 128/10 -> 128/7 in 0.14 h, while a hard-capped chain stalled for 75 h).  So a
``gates`` objective searches at cap + slack (default 2) and the engine's repair phase squeezes
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
    "default_slack_gates": Knob(2, "Soft slack for the gates objective when soft_depth_slack is "
                                "null (evidence: cap + 2..3 helps gate reduction).", min=0),
    "default_slack_depth_then_gates": Knob(0, "Soft slack for depth_then_gates when "
                                           "soft_depth_slack is null.", min=0),
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
    def from_settings(cls, settings, **overrides):
        """Objective from the ``objective`` knobs (a Settings or its ``view('objective')``);
        keyword overrides win (e.g. a worker group's ``depth_cap``)."""
        cfg = settings.view('objective') if hasattr(settings, 'view') else settings
        kind = overrides.get('kind', cfg.kind)
        slack = overrides.get('soft_depth_slack', cfg.soft_depth_slack)
        if slack is None:
            slack = (cfg.default_slack_gates if kind == 'gates'
                     else cfg.default_slack_depth_then_gates)
        return cls(kind, overrides.get('depth_cap', cfg.depth_cap),
                   overrides.get('gate_limit', cfg.gate_limit), slack)

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

    def better(self, a, b):
        """True when (gates, depth) pair ``a`` scores strictly better than ``b``."""
        return self.key(*a) < self.key(*b)

    def describe(self):
        """Short human-readable form, e.g. ``gates, depth <= 9 (search 11), gates <= 100``."""
        parts = ['fewest gates' if self.kind == 'gates' else 'shallowest, then fewest gates']
        if self.depth_cap is not None:
            text = 'depth <= %d' % self.depth_cap
            if self.soft_depth_slack:
                text += ' (search %d)' % self.search_cap
            parts.append(text)
        if self.gate_limit is not None:
            parts.append('gates <= %d' % self.gate_limit)
        return ', '.join(parts)

    def to_dict(self):
        """JSON-safe dict (checkpoints, dossiers)."""
        return {'kind': self.kind, 'depth_cap': self.depth_cap, 'gate_limit': self.gate_limit,
                'soft_depth_slack': self.soft_depth_slack}

    @classmethod
    def from_dict(cls, data):
        """Inverse of ``to_dict``."""
        return cls(data.get('kind', 'gates'), data.get('depth_cap'), data.get('gate_limit'),
                   data.get('soft_depth_slack', 0))
