"""Move protocol shared by every neighbourhood.

A move edits the chain's ValueSet speculatively and returns a Proposal describing exactly what it
did.  The engine scores the edited state, then either keeps it or rolls the journal back.  The
trace is what an improvement dossier attributes, so it must name every sub-operation that
contributed (``components``) and the parameters actually used (``params``).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from ..config.schema import Section

REGISTRY: dict[str, type["Move"]] = {}


def register(cls: type["Move"]) -> type["Move"]:
    """Class decorator: make a move available by its ``name``."""
    if cls.name in REGISTRY and REGISTRY[cls.name] is not cls:
        raise ValueError(f"move {cls.name} registered twice")
    REGISTRY[cls.name] = cls
    return cls


def load_all() -> dict[str, type["Move"]]:
    """Import every move module so the registry is complete."""
    from . import walk, lns, depth, structural, depth3  # noqa: F401  (registration side effect)
    return REGISTRY


@dataclass
class Proposal:
    """What a move did to the state.

    ``journal`` undoes the edits (None when the state was not touched).  ``trace`` is small,
    JSON-safe and stable: see DESIGN.md section 4.3.  ``work`` is the work spent, used for
    scheduler credit.  ``deterministic`` is False when a wall-clock limit shaped the result.
    """
    move: str
    journal: Any
    trace: dict = field(default_factory=dict)
    work: int = 0
    deterministic: bool = True


@dataclass
class MoveContext:
    """Everything a move may read.  Only ``state`` and the RNG may be changed.

    ``state``      the chain's ValueSet (edit it, record edits in a journal)
    ``target``     core.target.Target
    ``objective``  core.objective.Objective (the real caps and limits)
    ``best_key``   objective key of the chain best
    ``rng``        the engine's random.Random
    ``cfg``        this move's knob view
    ``budget``     core.budget.Budget for this proposal
    ``archive``    engine.archive.Archive, read-only
    ``phase``      current phase name
    ``settings``   the full Settings (rarely needed; prefer ``cfg``)
    """
    state: Any
    target: Any
    objective: Any
    best_key: tuple
    rng: Any
    cfg: Any
    budget: Any
    archive: Any = None
    phase: str = "plateau"
    settings: Any = None


class Move:
    """Base class.  Subclasses set the class attributes and implement ``propose``."""
    name: ClassVar[str] = ""
    family: ClassVar[str] = ""
    knobs: ClassVar[Section | None] = None

    def __init__(self, settings):
        self.settings = settings
        self.cfg = settings.view(self.knobs.path) if self.knobs is not None else None

    def applicable(self, target, objective) -> str | None:
        """None when this move can run on the target/objective, else a short reason."""
        return None

    def propose(self, ctx: MoveContext) -> Proposal | None:
        """Edit ``ctx.state`` and return a Proposal, or return None and leave it unchanged."""
        raise NotImplementedError

    def state(self) -> dict:
        """JSON-safe persistent state for checkpoints (most moves are stateless)."""
        return {}

    def load_state(self, data: dict) -> None:
        """Restore what ``state()`` returned."""
