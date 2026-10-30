"""The search engine: one loop (``loop.Engine``) and its policies.

``loop``        Engine: the chain, step(), improvements and dossiers, restarts, checkpoints
``acceptance``  which proposals the chain keeps (threshold / anneal / late acceptance, snapback)
``scheduler``   which move runs next (fixed or adaptive bandit, per phase)
``phase``       burst / plateau / repair weights and budgets
``archive``     distinct near-best elites with diversity-aware eviction
``restart``     stall detection and restart-source choice

``SECTIONS`` lists every knob section the engine reads besides ``budget`` (useful for
``config.settings.for_sections`` in tests).
"""
from . import acceptance, archive, loop, phase, restart, scheduler
from .loop import Engine, StepResult


def _sections():
    out = []
    for module in (loop, acceptance, scheduler, archive, restart, phase):
        knobs = module.KNOBS
        out.extend(knobs if isinstance(knobs, tuple) else (knobs,))
    return tuple(out)


SECTIONS = _sections()

__all__ = ["Engine", "StepResult", "SECTIONS"]
