"""Stall detection and restart-source selection.

Role in the method (DESIGN.md section 2): a chain whose best has not improved for a while is
restarted from a fresh randomized constructor root, a distinct archive elite, a distinct elite
from the shared campaign pool, or the worker best.  Evidence behind the defaults:

* Fresh roots are the diversity mechanism that worked [historical S]: 7 of 58 naive roots reached
  88 (median 2,234 s, range 626-3,855 s), and every 88-reaching restart landed in a new pocket.
  So ``w_fresh`` dominates.
* Restarts ended on stall in 52 of 58 cases with stall 2,400 s; the report recommends a stall of
  about 1,500-2,400 s and a per-root budget of about 1-1.5 h for ~100-value circuits, hence
  ``stall_seconds`` 2,000 and ``root_seconds`` 5,400, scaled up with circuit size
  (``size_ref``/``size_exponent``) because large circuits run proportionally fewer proposals per
  second (walk: 695 it/s at 88 values, 119 it/s at 540).
* Long chains broke every long plateau in the framework runs (2.5-24 h old), and adoption that
  reset chains hurt.  So a chain that *holds the worker best* is never cut by root age and gets
  ``incumbent_factor`` times the stall allowance.  Fully persistent workers set
  ``restart.enabled = false``.
* Pull-on-stall sharing of distinct elites replaced push-adopt (diversity collapse); ``w_shared``
  is the pull probability.

Seconds-based triggers depend on the wall clock and so are not replayable across runs; the
``stall_work`` / ``stall_proposals`` triggers are, and either kind may be used alone.
The controller is consulted only every ``engine.periodic_every`` proposals.
"""
from __future__ import annotations

from ..config.schema import Knob, Section

KNOBS = Section("restart", "When and from where a stalled chain restarts.", {
    "enabled": Knob(True, "Restart stalled chains (false: one persistent chain per worker)."),
    "stall_seconds": Knob(2000.0, "Restart after this long without a chain-best improvement "
                          "(historical: 1,500-2,400 s at ~100 values). 0 disables.", min=0),
    "stall_work": Knob(0, "Restart after this much work without a chain-best improvement "
                       "(replayable alternative). 0 disables.", min=0),
    "stall_proposals": Knob(0, "Restart after this many proposals without a chain-best "
                            "improvement (replayable alternative). 0 disables.", min=0),
    "root_seconds": Knob(5400.0, "Per-root time budget (historical: every 88 arrived within "
                         "3,855 s of its root; 1-1.5 h recommended). 0 disables.", min=0),
    "size_ref": Knob(100, "Circuit size (gates) at which the timers apply unscaled.", min=1),
    "size_exponent": Knob(1.0, "Timers scale by (gates / size_ref) ** size_exponent above "
                          "size_ref (never below 1).", min=0),
    "incumbent_factor": Knob(3.0, "Stall allowance multiplier while the chain best equals the "
                             "worker best; such chains are also exempt from root_seconds "
                             "(long chains broke every long plateau).", min=1),
    "w_fresh": Knob(0.6, "Weight of a fresh randomized constructor root.", min=0),
    "w_elite": Knob(0.2, "Weight of a distinct elite from the worker archive.", min=0),
    "w_shared": Knob(0.1, "Weight of a distinct elite pulled from the campaign pool.", min=0),
    "w_best": Knob(0.1, "Weight of the worker best.", min=0),
    "build_work": Knob(0, "Work budget for building a constructor root (0 = unbounded).", min=0),
})

SOURCES = ("fresh", "elite", "shared", "best")


class RestartController:
    """Remembers when the chain started and last improved; says when to restart and from where.

    Times are ``recorder.now()`` seconds, work is the engine's cumulative work counter, and
    ``it`` its proposal counter.
    """

    def __init__(self, cfg):
        self.enabled = cfg.enabled
        self.stall_seconds = cfg.stall_seconds
        self.stall_work = cfg.stall_work
        self.stall_proposals = cfg.stall_proposals
        self.root_seconds = cfg.root_seconds
        self.size_ref = cfg.size_ref
        self.size_exponent = cfg.size_exponent
        self.incumbent_factor = cfg.incumbent_factor
        self.weights = {"fresh": cfg.w_fresh, "elite": cfg.w_elite, "shared": cfg.w_shared,
                        "best": cfg.w_best}
        self.build_work = cfg.build_work
        self.root_t = self.root_it = self.root_work = 0
        self.best_t = self.best_it = self.best_work = 0
        self.restarts = 0
        self.by_reason: dict[str, int] = {}
        self.by_source: dict[str, int] = {}

    # -- bookkeeping ----------------------------------------------------------------------
    def started(self, it: int, work: int, t: float) -> None:
        """A chain (re)started now."""
        self.root_t = self.best_t = t
        self.root_it = self.best_it = it
        self.root_work = self.best_work = work

    def improved(self, it: int, work: int, t: float) -> None:
        """The chain best improved now."""
        self.best_t = t
        self.best_it = it
        self.best_work = work

    def restarted(self, reason: str, source: str) -> None:
        """Count one executed restart."""
        self.restarts += 1
        self.by_reason[reason] = self.by_reason.get(reason, 0) + 1
        self.by_source[source] = self.by_source.get(source, 0) + 1

    # -- decisions ------------------------------------------------------------------------
    def scale(self, gates: int) -> float:
        """Timer multiplier for a chain of ``gates`` gates."""
        ratio = gates / self.size_ref
        return ratio ** self.size_exponent if ratio > 1.0 else 1.0

    def due(self, it: int, work: int, t: float, gates: int, incumbent: bool) -> str | None:
        """The restart reason if the chain should restart now, else None."""
        if not self.enabled:
            return None
        scale = self.scale(gates)
        stall = scale * (self.incumbent_factor if incumbent else 1.0)
        if self.stall_seconds and t - self.best_t >= self.stall_seconds * stall:
            return "stall_seconds"
        if self.stall_work and work - self.best_work >= self.stall_work * stall:
            return "stall_work"
        if self.stall_proposals and it - self.best_it >= self.stall_proposals * stall:
            return "stall_proposals"
        if self.root_seconds and not incumbent and t - self.root_t >= self.root_seconds * scale:
            return "root_seconds"
        return None

    def order(self, rng, available: dict) -> list[str]:
        """Restart sources to try, in order: one drawn by weight among the available ones, then
        the remaining available ones by decreasing weight (fallbacks if the first fails)."""
        cands = [s for s in SOURCES if available.get(s) and self.weights[s] > 0]
        if not cands:
            return [s for s in SOURCES if available.get(s)]
        total = sum(self.weights[s] for s in cands)
        r = rng.random() * total
        acc = 0.0
        first = cands[-1]
        for s in cands:
            acc += self.weights[s]
            if r < acc:
                first = s
                break
        rest = sorted((s for s in cands if s != first), key=lambda s: -self.weights[s])
        return [first] + rest

    def ages(self, it: int, work: int, t: float) -> dict:
        """Chain age and stall length (for restart events and dossiers)."""
        return {"root_s": t - self.root_t, "root_it": it - self.root_it,
                "stall_s": t - self.best_t, "stall_it": it - self.best_it,
                "stall_work": work - self.best_work}

    # -- persistence ----------------------------------------------------------------------
    def state(self, t: float) -> dict:
        """JSON-safe state.  Times are stored as ages so a resumed run continues the timers."""
        return {"root_age_s": t - self.root_t, "best_age_s": t - self.best_t,
                "root_it": self.root_it, "best_it": self.best_it,
                "root_work": self.root_work, "best_work": self.best_work,
                "restarts": self.restarts, "by_reason": dict(self.by_reason),
                "by_source": dict(self.by_source)}

    def load_state(self, data: dict, t: float) -> None:
        """Restore ``state()`` relative to the new clock reading ``t``."""
        self.root_t = t - data.get("root_age_s", 0.0)
        self.best_t = t - data.get("best_age_s", 0.0)
        self.root_it = data.get("root_it", 0)
        self.best_it = data.get("best_it", 0)
        self.root_work = data.get("root_work", 0)
        self.best_work = data.get("best_work", 0)
        self.restarts = data.get("restarts", 0)
        self.by_reason = dict(data.get("by_reason", {}))
        self.by_source = dict(data.get("by_source", {}))
