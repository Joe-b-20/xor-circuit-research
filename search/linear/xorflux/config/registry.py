"""Collect every module's ``KNOBS`` section into one schema.

Add a module here when it declares knobs.  A module may declare one ``Section`` as ``KNOBS`` or
several as a tuple ``KNOBS = (Section(...), Section(...))``.
"""
from __future__ import annotations

import importlib
from functools import lru_cache

from .schema import Schema, Section

MODULES = (
    "xorflux.core.budget",
    "xorflux.core.objective",
    "xorflux.moves.walk",
    "xorflux.moves.lns",
    "xorflux.moves.rebuild",
    "xorflux.moves.depth",
    "xorflux.moves.structural",
    "xorflux.moves.depth3",
    "xorflux.moves.construct",
    "xorflux.engine.loop",
    "xorflux.engine.acceptance",
    "xorflux.engine.scheduler",
    "xorflux.engine.archive",
    "xorflux.engine.restart",
    "xorflux.engine.phase",
    "xorflux.telemetry.recorder",
    "xorflux.campaign.coordinator",
    "xorflux.campaign.worker",
    "xorflux.campaign.sharing",
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
