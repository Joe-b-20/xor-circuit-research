"""Collect every module's ``KNOBS`` section into one schema.

Add a module here when it declares knobs.  A module may declare one ``Section`` as ``KNOBS`` or
several as a tuple ``KNOBS = (Section(...), Section(...))``.
"""
from __future__ import annotations

import importlib
from functools import lru_cache

from .schema import Schema, Section

MODULES = (
    "xorsearch.core.budget",
    "xorsearch.core.objective",
    "xorsearch.moves.walk",
    "xorsearch.moves.lns",
    "xorsearch.moves.rebuild",
    "xorsearch.moves.depth",
    "xorsearch.moves.structural",
    "xorsearch.moves.depth3",
    "xorsearch.moves.construct",
    "xorsearch.engine.loop",
    "xorsearch.engine.acceptance",
    "xorsearch.engine.scheduler",
    "xorsearch.engine.archive",
    "xorsearch.engine.restart",
    "xorsearch.engine.phase",
    "xorsearch.telemetry.recorder",
    "xorsearch.campaign.coordinator",
    "xorsearch.campaign.worker",
    "xorsearch.campaign.sharing",
)


def sections():
    """Every declared Section, in module order."""
    out = []
    for name in MODULES:
        module = importlib.import_module(name)
        declared = getattr(module, "KNOBS", ())
        if isinstance(declared, Section):
            declared = (declared,)
        out.extend(declared)
    return out


@lru_cache(maxsize=1)
def schema() -> Schema:
    """The full schema (cached; modules are imported once)."""
    return Schema(sections())
