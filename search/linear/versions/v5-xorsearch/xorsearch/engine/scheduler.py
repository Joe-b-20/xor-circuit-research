"""Move selection: which move the next proposal uses.

Role in the method (DESIGN.md section 2): every proposal starts with the scheduler picking a move
for the current phase.  The phase controller supplies one prior weight vector per phase (from the
moves' ``weight`` / ``burst_weight`` / ``repair_weight`` knobs); the scheduler turns it into
selection probabilities.

Modes (``scheduler.mode``):

``fixed``
    Probabilities are the normalised prior weights.
``adaptive`` (default)
    A bandit over moves.  Each move earns discounted *credit per unit of cost*: a chain-best
    improvement is worth ``reward_chain``, a worker-best improvement adds ``reward_worker``, a new
    frontier point ``reward_frontier``, and a kept neutral move that changed the state
    ``reward_neutral`` (plateau movement is the frequent, weak signal; best improvements are rare
    and strong).  Each move's rate is shrunk toward the fleet rate with ``prior_pulls`` pseudo
    pulls, and its probability is ``prior * (rate / mean rate) ** sensitivity``, capped at
    ``max_boost``, then mixed with a ``min_share`` floor so no applicable move starves.  Evidence:
    the framework campaigns spent 52.7% of CPU on engines that never improved anything under
    round-robin; a credit-driven share moves that CPU to the walk/LNS moves that did.

Cost (``scheduler.cost``) is what a proposal is charged.  ``seconds`` (default) is the measured
time of the proposal, the only unit comparable across moves: work units count different things
per move (a walk candidate test versus a vendored constructor trial), and charging them let a
40 ms structural proposal look as cheap as a 1 ms walk proposal.  ``work`` keeps the whole
trajectory, scheduler included, exactly replayable from a checkpoint, at the price of that bias.

Discounting uses a growing global scale instead of decaying every arm every step, so ``credit``
is O(1).  Probabilities are recomputed every ``refresh_every`` credits, and ``pick`` is one
``rng.random()`` plus a bisect over a cached cumulative list.

The burst phase uses its prior weights as given (near-uniform by construction) unless
``burst_adaptive`` is set: right after a new best every local move deserves a fair shot.
"""
from __future__ import annotations

from bisect import bisect_right

from ..config.schema import Knob, Section

KNOBS = Section("scheduler", "Move selection per phase.", {
    "mode": Knob("adaptive", "adaptive: bandit on discounted credit per unit of cost (default). "
                 "fixed: normalised prior weights.", choices=("adaptive", "fixed")),
    "cost": Knob("seconds", "What a proposal is charged. seconds: measured proposal time "
                 "(comparable across moves). work: the move's work units (replayable "
                 "scheduling, but units differ between moves).", choices=("seconds", "work")),
    "reward_chain": Knob(1.0, "Credit for a new chain best.", min=0),
    "reward_worker": Knob(4.0, "Extra credit for a new worker best (the outcome that matters).",
                          min=0),
    "reward_frontier": Knob(1.0, "Extra credit for a new nondominated feasible point.", min=0),
    "reward_neutral": Knob(0.01, "Credit for a kept neutral move that changed the state (weak "
                           "plateau-movement signal; 'accepted' alone measured nothing in v2/v3).",
                           min=0),
    "half_life": Knob(5000, "Credit half-life in proposals.", min=1),
    "prior_pulls": Knob(50.0, "Pseudo pulls at the mean rate that every move starts with; "
                        "larger values trust the configured weights longer.", min=0),
    "sensitivity": Knob(1.0, "Exponent on a move's rate relative to the mean rate.", min=0),
    "max_boost": Knob(10.0, "Cap on a move's rate relative to the mean rate.", min=1),
    "min_share": Knob(0.02, "Selection-probability floor for every move with a nonzero prior "
                      "in the phase.", min=0, max=1),
    "refresh_every": Knob(64, "Credits between probability recomputations.", min=1),
    "burst_adaptive": Knob(False, "Let credit reshape the burst phase too (default: burst uses "
                           "its near-uniform priors)."),
})

PHASES = ("plateau", "burst", "repair")

# Rescale the discounted sums once the global scale passes this, long before float overflow.
_RESCALE_AT = 1e100


class Scheduler:
    """Selection probabilities per phase over a fixed list of moves.

    ``names`` lists the moves (index = arm).  ``priors`` maps each phase to a list of
    non-negative weights; a phase whose weights are all zero falls back to ``plateau``.
    """

    def __init__(self, cfg, names, priors):
        self.names = list(names)
        k = len(self.names)
        self.priors = {}
        for phase in PHASES:
            weights = [float(w) for w in priors.get(phase, priors["plateau"])]
            if len(weights) != k:
                raise ValueError(f"phase {phase}: {len(weights)} weights for {k} moves")
            if sum(weights) <= 0:
                weights = [float(w) for w in priors["plateau"]]
            self.priors[phase] = weights
        if sum(self.priors["plateau"]) <= 0:
            raise ValueError("every move has zero weight in the plateau phase")
        self.adaptive = cfg.mode == "adaptive"
        self.adaptive_phases = {"plateau", "repair"}
        if cfg.burst_adaptive:
            self.adaptive_phases.add("burst")
        self.r_chain = cfg.reward_chain
        self.r_worker = cfg.reward_worker
        self.r_frontier = cfg.reward_frontier
        self.r_neutral = cfg.reward_neutral
        self.decay = 0.5 ** (1.0 / cfg.half_life)
        self.prior_pulls = cfg.prior_pulls
        self.sensitivity = cfg.sensitivity
        self.max_boost = cfg.max_boost
        self.min_share = cfg.min_share
        self.refresh_every = cfg.refresh_every
        # Discounted sums, stored multiplied by `scale` (true value = stored / scale).
        self.scale = 1.0
        self.inv_decay = 1.0 / self.decay
        self.R = [0.0] * k
        self.N = [0.0] * k
        self.W = [0.0] * k
        self.pulls = [0] * k            # undiscounted, for reports
        self._since_refresh = 0
        self._cum: dict[str, list[float]] = {}

    # -- hot path -------------------------------------------------------------------------
    def pick(self, phase: str, rng) -> int:
        """Index of the move for the next proposal."""
        cum = self._cum.get(phase)
        if cum is None:
            cum = self._cum[phase] = self._cumulative(phase)
        return bisect_right(cum, rng.random() * cum[-1])

    def credit(self, idx: int, work: float, neutral: bool, chain: bool, worker: bool,
               frontier: bool) -> None:
        """Record the outcome of one proposal by move ``idx`` that cost ``work`` (seconds or
        work units, per ``scheduler.cost``; the engine passes the right one)."""
        reward = 0.0
        if neutral:
            reward = self.r_neutral
        if chain:
            reward += self.r_chain
        if worker:
            reward += self.r_worker
        if frontier:
            reward += self.r_frontier
        scale = self.scale * self.inv_decay
        self.scale = scale
        self.R[idx] += reward * scale
        self.N[idx] += scale
        self.W[idx] += work * scale
        self.pulls[idx] += 1
        if scale > _RESCALE_AT:
            self._rescale()
        self._since_refresh += 1
        if self._since_refresh >= self.refresh_every and self.adaptive:
            self._since_refresh = 0
            self._invalidate()

    # -- probabilities --------------------------------------------------------------------
    def _invalidate(self):
        # Fixed phases never change, so only drop the adaptive ones.
        for phase in self.adaptive_phases:
            self._cum.pop(phase, None)

    def probabilities(self, phase: str) -> list[float]:
        """Selection probability of every move in ``phase``."""
        prior = self.priors[phase]
        active = [i for i, w in enumerate(prior) if w > 0]
        total = sum(prior[i] for i in active)
        probs = [0.0] * len(prior)
        for i in active:
            probs[i] = prior[i] / total
        if self.adaptive and phase in self.adaptive_phases:
            probs = self._adapt(probs, active)
        # Exact floor: p_i = f + (1 - K f) p_i, so every active move gets at least f.
        k = len(active)
        f = min(self.min_share, 1.0 / k)
        if f > 0:
            rest = 1.0 - k * f
            for i in active:
                probs[i] = f + rest * probs[i]
        return probs

    def _adapt(self, probs, active):
        inv = 1.0 / self.scale
        n_tot = sum(self.N[i] for i in active) * inv
        r_tot = sum(self.R[i] for i in active) * inv
        w_tot = sum(self.W[i] for i in active) * inv
        if r_tot <= 0.0 or n_tot <= 0.0 or w_tot <= 0.0:
            return probs                   # no evidence yet: priors only
        rho_bar = r_tot / n_tot
        w_bar = w_tot / n_tot
        c_bar = rho_bar / w_bar
        k = self.prior_pulls
        beta = self.sensitivity
        cap = self.max_boost
        out = [0.0] * len(probs)
        for i in active:
            n = self.N[i] * inv
            rho = (self.R[i] * inv + k * rho_bar) / (n + k) if n + k > 0 else rho_bar
            w = (self.W[i] * inv + k * w_bar) / (n + k) if n + k > 0 else w_bar
            q = (rho / w) / c_bar if w > 0 else cap
            if q > cap:
                q = cap
            out[i] = probs[i] * (q ** beta)
        total = sum(out)
        if total <= 0.0:
            return probs
        return [p / total for p in out]

    def _cumulative(self, phase):
        cum = []
        acc = 0.0
        for p in self.probabilities(phase):
            acc += p
            cum.append(acc)
        return cum

    def weights(self, phase: str | None = None) -> dict:
        """``{move: probability}`` for one phase, or ``{phase: {...}}`` for all."""
        if phase is None:
            return {ph: self.weights(ph) for ph in PHASES}
        return {name: round(p, 6) for name, p in zip(self.names, self.probabilities(phase))}

    def summary(self) -> dict:
        """Per-move undiscounted pulls and discounted reward / work (for epochs)."""
        inv = 1.0 / self.scale
        return {name: {"pulls": self.pulls[i], "reward": self.R[i] * inv, "work": self.W[i] * inv}
                for i, name in enumerate(self.names)}

    # -- persistence ----------------------------------------------------------------------
    def _rescale(self):
        inv = 1.0 / self.scale
        self.R = [x * inv for x in self.R]
        self.N = [x * inv for x in self.N]
        self.W = [x * inv for x in self.W]
        self.scale = 1.0

    def state(self) -> dict:
        """JSON-safe state.  Normalises the scale in place and drops cached probabilities so
        the running scheduler and one restored from this state continue bit-identically."""
        self._rescale()
        self._cum.clear()
        return {"names": list(self.names), "R": list(self.R), "N": list(self.N),
                "W": list(self.W), "pulls": list(self.pulls),
                "since_refresh": self._since_refresh}

    def load_state(self, data: dict) -> None:
        """Restore ``state()``; moves are matched by name, unknown ones start fresh."""
        index = {name: i for i, name in enumerate(data.get("names", []))}
        for i, name in enumerate(self.names):
            j = index.get(name)
            if j is None:
                continue
            self.R[i] = data["R"][j]
            self.N[i] = data["N"][j]
            self.W[i] = data["W"][j]
            self.pulls[i] = data["pulls"][j]
        self.scale = 1.0
        self._since_refresh = data.get("since_refresh", 0)
        self._cum.clear()
