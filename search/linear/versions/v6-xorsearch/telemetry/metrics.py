"""Search-state metrics: distances, diversity, plateau shape, circuit shape.

The engine computes these and hands the results to the Recorder (``epoch`` fields, dossier
``state_before``, ``plateau`` events); the coordinator uses ``diversity`` for its fleet panel.
Nothing here does I/O.  The evidence behind each metric:

* ``jaccard_distance`` / ``diversity``: the fleet collapsed onto a handful of DAGs while 90
  distinct ones existed, and no log showed it.  The panel reports mean/min pairwise distance,
  the distinct count, the modal fraction and a basin count so a collapse is one number.
* ``PlateauTracker``: plateaus lasted hours and their size (distinct equal-score states) was
  only known when someone counted by hand; the old detector capped at 32 states.  The tracker
  counts exactly up to a cap and then switches to a HyperLogLog estimate, so it never stops
  counting and never grows without bound.
* ``shape_from_gates``: dossier "what did the circuit look like".

Knobs live in the ``telemetry.plateau`` and ``telemetry.diversity`` sections declared here;
``telemetry.recorder.KNOBS`` re-exports them so the config registry (which imports only the
recorder) sees them.  Classes take explicit parameters and fall back
to the knob defaults, so ``PlateauTracker()`` works without a Settings object.
"""
from __future__ import annotations

import math
import random
from collections import Counter

from ..config.schema import Knob, Section

PLATEAU_KNOBS = Section("telemetry.plateau", "Plateau tracking (distinct states, drift).", {
    "distinct_cap": Knob(50_000, "Distinct plateau states counted exactly; beyond this a "
                         "HyperLogLog estimate takes over (bounded memory).", min=0),
    "hll_precision": Knob(12, "HyperLogLog register bits once the exact cap is passed "
                          "(2^p registers, relative error about 1.04/sqrt(2^p)).", min=4, max=16),
    "drift_every": Knob(64, "Accepted moves between samples of the Jaccard drift from the "
                        "plateau entry state (each sample is O(|state|)); 0 disables max_drift.",
                        min=0),
})

DIVERSITY_KNOBS = Section("telemetry.diversity", "Pairwise-distance diversity panels.", {
    "max_pairs": Knob(5_000, "Pairs evaluated exactly; above this a uniform random sample of "
                      "this many pairs estimates mean/min distance.", min=1),
    "basin_radius": Knob(0.05, "Two states within this Jaccard distance share a basin "
                         "(leader clustering).", min=0, max=1),
    "basin_sample": Knob(200, "At most this many distinct states are clustered into basins.",
                         min=1),
    "sample_seed": Knob(0, "Seed for pair and basin sampling (keeps panels reproducible)."),
})

KNOBS = (PLATEAU_KNOBS, DIVERSITY_KNOBS)

_M64 = (1 << 64) - 1


def _default(section: Section, name: str):
    """Knob default, used when a caller passes None for a parameter."""
    return section.knobs[name].default


# --------------------------------------------------------------------------- distances

def jaccard_distance(a, b) -> float:
    """``1 - |a & b| / |a | b|`` for two sets; 0.0 when both are empty.

    Value sets are frozensets of ints (``ValueSet.key()``), so ``len(a & b)`` runs in C and is
    the only O(n) step.
    """
    if a is b:
        return 0.0
    la, lb = len(a), len(b)
    if not la and not lb:
        return 0.0
    if la > lb:  # intersect from the smaller side
        a, b = b, a
    inter = len(a & b) if isinstance(a, (set, frozenset)) else len(set(a) & set(b))
    return 1.0 - inter / (la + lb - inter)


def diversity(sets, *, max_pairs=None, basin_radius=None, basin_sample=None, seed=None) -> dict:
    """Diversity of a population of states (one per worker, or an archive/pool).

    Returns ``n``, ``distinct`` (distinct sets), ``modal_fraction`` (share of the population on
    the most common set: 1.0 means total collapse), ``mean``/``min``/``max`` pairwise Jaccard
    distance over all ordered-free pairs (identical members count as distance 0, so collapse
    shows in the mean), ``pairs`` evaluated, ``sampled`` (True when pairs were sampled) and
    ``basins`` (leader clusters at ``basin_radius`` among distinct sets).
    """
    max_pairs = _default(DIVERSITY_KNOBS, "max_pairs") if max_pairs is None else max_pairs
    radius = _default(DIVERSITY_KNOBS, "basin_radius") if basin_radius is None else basin_radius
    bsample = _default(DIVERSITY_KNOBS, "basin_sample") if basin_sample is None else basin_sample
    seed = _default(DIVERSITY_KNOBS, "sample_seed") if seed is None else seed
    items = [s if isinstance(s, frozenset) else frozenset(s) for s in sets]
    n = len(items)
    counts = Counter(items)
    out = {"n": n, "distinct": len(counts),
           "modal_fraction": (max(counts.values()) / n) if n else 0.0,
           "mean": 0.0, "min": 0.0, "max": 0.0, "pairs": 0, "sampled": False, "basins": len(counts)}
    total_pairs = n * (n - 1) // 2
    if total_pairs == 0:
        return out
    rng = random.Random(seed)
    if total_pairs <= max_pairs:
        pairs = ((i, j) for i in range(n) for j in range(i + 1, n))
        npairs = total_pairs
    else:
        # Sample pairs with replacement: cheap, unbiased for the mean; min is an upper bound.
        pairs = []
        for _ in range(max_pairs):
            i = rng.randrange(n)
            j = rng.randrange(n - 1)
            pairs.append((i, j + (j >= i)))
        npairs = max_pairs
        out["sampled"] = True
    total, lo, hi = 0.0, 1.0, 0.0
    for i, j in pairs:
        d = jaccard_distance(items[i], items[j])
        total += d
        if d < lo:
            lo = d
        if d > hi:
            hi = d
    out.update(mean=total / npairs, min=lo, max=hi, pairs=npairs)
    out["basins"] = basins(list(counts), radius=radius, sample=bsample, seed=seed)
    return out


def basins(distinct_sets, *, radius=None, sample=None, seed=None) -> int:
    """Leader-clustering count of distinct states at Jaccard ``radius``.

    Each state joins the first leader within ``radius`` or becomes a leader.  O(n * leaders),
    bounded by clustering at most ``sample`` states (deterministically sampled).
    """
    radius = _default(DIVERSITY_KNOBS, "basin_radius") if radius is None else radius
    sample = _default(DIVERSITY_KNOBS, "basin_sample") if sample is None else sample
    seed = _default(DIVERSITY_KNOBS, "sample_seed") if seed is None else seed
    items = list(distinct_sets)
    if len(items) > sample:
        items = random.Random(seed).sample(items, sample)
    leaders: list[frozenset] = []
    for s in items:
        for lead in leaders:
            if jaccard_distance(s, lead) <= radius:
                break
        else:
            leaders.append(s)
    return len(leaders)


# --------------------------------------------------------------------------- distinct counting

def _mix64(h: int) -> int:
    """splitmix64 finaliser: spreads Python's (structured) set hashes over 64 bits."""
    x = h & _M64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & _M64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & _M64
    return x ^ (x >> 31)


class HyperLogLog:
    """Minimal HyperLogLog over 64-bit mixed hashes (registers in a bytearray).

    Used only after the exact distinct-state cap is reached; ``estimate`` includes the
    linear-counting correction so small counts stay near-exact.
    """
    __slots__ = ("p", "m", "reg")

    def __init__(self, p: int, registers: bytes | None = None):
        self.p = p
        self.m = 1 << p
        self.reg = bytearray(registers) if registers is not None else bytearray(self.m)

    def add(self, h: int) -> None:
        """Insert one (unmixed) hash value."""
        x = _mix64(h)
        p = self.p
        idx = x >> (64 - p)
        rest = x & ((1 << (64 - p)) - 1)
        rank = (64 - p) - rest.bit_length() + 1
        if rank > self.reg[idx]:
            self.reg[idx] = rank

    def estimate(self) -> float:
        """Cardinality estimate."""
        m = self.m
        alpha = 0.7213 / (1 + 1.079 / m)
        z = sum(2.0 ** -r for r in self.reg)
        e = alpha * m * m / z
        zeros = self.reg.count(0)
        if e <= 2.5 * m and zeros:
            return m * math.log(m / zeros)
        return e


# --------------------------------------------------------------------------- plateaus

class PlateauTracker:
    """Shape of the current plateau: the time the chain best has stayed at one score level.

    The engine calls ``enter`` when the chain reaches a new best level (or restarts),
    ``observe`` for every proposal, ``snapshot`` for dossiers/epochs and ``close`` when the
    plateau ends (exit kinds: ``improve``, ``restart``, ``repair``, ``stop``, ...).

    ``observe`` is O(1) for rejected proposals (counter increments only).  For accepted ones the
    state key's hash is added to the distinct set; ``state_key`` may be the frozenset from
    ``ValueSet.key()`` (enables drift) or a precomputed int hash (drift then unavailable), or
    None when unknown.  Drift (Jaccard distance from the plateau entry state) is computed on
    ``snapshot``/``close`` and sampled every ``drift_every`` accepts for ``max_drift``.
    """

    def __init__(self, distinct_cap=None, hll_precision=None, drift_every=None):
        self.distinct_cap = (_default(PLATEAU_KNOBS, "distinct_cap")
                             if distinct_cap is None else distinct_cap)
        self.hll_precision = (_default(PLATEAU_KNOBS, "hll_precision")
                              if hll_precision is None else hll_precision)
        self.drift_every = (_default(PLATEAU_KNOBS, "drift_every")
                            if drift_every is None else drift_every)
        self.index = 0          # plateaus entered so far (per tracker = per worker)
        self.active = False
        self._reset(None, None, 0, 0.0)

    @classmethod
    def from_settings(cls, settings) -> "PlateauTracker":
        """Tracker configured from ``telemetry.plateau`` (missing keys use defaults)."""
        values = getattr(settings, "values", {}) if settings is not None else {}
        get = lambda name: values.get(f"telemetry.plateau.{name}")  # noqa: E731
        return cls(get("distinct_cap"), get("hll_precision"), get("drift_every"))

    def _reset(self, level_key, state_key, it, t):
        self.level = level_key
        self.entry_key = state_key if isinstance(state_key, (set, frozenset)) else None
        self.last_key = self.entry_key
        self.entry_it, self.entry_t = it, t
        self.last_it, self.last_t = it, t
        self.proposals = 0
        self.accepted = 0
        self.neutral_accepts = 0
        self.visits = 0          # accepted proposals that reported a state key
        self.max_drift = 0.0
        self._seen: set[int] | None = set()
        self._hll: HyperLogLog | None = None
        self._since_drift = 0
        if state_key is not None:
            self._see(state_key)

    def _see(self, state_key) -> None:
        h = state_key if isinstance(state_key, int) else hash(state_key)
        seen = self._seen
        if seen is not None:
            seen.add(h)
            if len(seen) > self.distinct_cap:
                # Switch to the estimator once; the exact set seeds it, then is dropped.
                hll = HyperLogLog(self.hll_precision)
                for x in seen:
                    hll.add(x)
                self._hll, self._seen = hll, None
        else:
            self._hll.add(h)

    def enter(self, level_key, state_key, it, t) -> None:
        """Start a plateau at score ``level_key`` (e.g. ``(gates, depth)``) from ``state_key``."""
        self.index += 1
        self.active = True
        self._reset(level_key, state_key, it, t)

    def observe(self, state_key, accepted: bool, neutral: bool, it, t) -> None:
        """Count one proposal; on acceptance record the resulting state."""
        self.proposals += 1
        self.last_it = it
        self.last_t = t
        if not accepted:
            return
        self.accepted += 1
        if neutral:
            self.neutral_accepts += 1
        if state_key is None:
            return
        self.visits += 1
        self._see(state_key)
        if isinstance(state_key, (set, frozenset)):
            self.last_key = state_key
            if self.drift_every and self.entry_key is not None:
                self._since_drift += 1
                if self._since_drift >= self.drift_every:
                    self._since_drift = 0
                    d = jaccard_distance(self.entry_key, state_key)
                    if d > self.max_drift:
                        self.max_drift = d

    def distinct_states(self) -> tuple[int, bool]:
        """``(count, exact)``: distinct states seen on this plateau."""
        if self._seen is not None:
            return len(self._seen), True
        return int(round(self._hll.estimate())), False

    def drift(self) -> float | None:
        """Jaccard distance from the entry state to the latest accepted state (None if unknown)."""
        if self.entry_key is None or self.last_key is None:
            return None
        return jaccard_distance(self.entry_key, self.last_key)

    def snapshot(self, it=None, t=None) -> dict:
        """Current plateau shape (JSON-safe).  ``it``/``t`` default to the last observation."""
        it = self.last_it if it is None else it
        t = self.last_t if t is None else t
        distinct, exact = self.distinct_states()
        drift = self.drift()
        level = self.level
        return {
            "index": self.index,
            "level": list(level) if isinstance(level, tuple) else level,
            "entry_it": self.entry_it, "entry_t": self.entry_t,
            "age_it": it - self.entry_it, "age_s": t - self.entry_t,
            "proposals": self.proposals, "accepted": self.accepted,
            "neutral_accepts": self.neutral_accepts,
            "neutral_rate": self.neutral_accepts / self.proposals if self.proposals else 0.0,
            "distinct_states": distinct, "distinct_exact": exact, "visits": self.visits,
            "revisit_ratio": self.visits / distinct if distinct else 0.0,
            "drift": drift, "max_drift": max(self.max_drift, drift or 0.0),
        }

    def close(self, exit_kind: str, it, t) -> dict:
        """End the plateau; returns the snapshot plus ``exit`` (fields of a ``plateau`` event)."""
        snap = self.snapshot(it, t)
        snap["exit"] = exit_kind
        self.active = False
        return snap

    def checkpoint(self) -> dict:
        """JSON-safe state.  Distinct states are stored as HLL registers (bounded size); a
        restored tracker therefore continues in estimator mode (``distinct_exact`` False).
        The entry/last state keys are not stored; the engine calls ``rekey`` after a
        restore."""
        regs = HyperLogLog(self.hll_precision)
        if self._seen is not None:
            for x in self._seen:
                regs.add(x)
        else:
            regs = self._hll
        return {"index": self.index, "active": self.active,
                "level": list(self.level) if isinstance(self.level, tuple) else self.level,
                "entry_it": self.entry_it, "entry_t": self.entry_t,
                "last_it": self.last_it, "last_t": self.last_t,
                "proposals": self.proposals, "accepted": self.accepted,
                "neutral_accepts": self.neutral_accepts, "visits": self.visits,
                "max_drift": self.max_drift, "hll_p": regs.p, "hll": bytes(regs.reg).hex()}

    def rekey(self, entry_key, last_key=None) -> None:
        """Give a restored tracker its entry (and latest) state again so ``drift`` is
        measurable after a resume; ``checkpoint`` stores no state keys (size)."""
        if isinstance(entry_key, (set, frozenset)):
            self.entry_key = entry_key
            self.last_key = last_key if isinstance(last_key, (set, frozenset)) else entry_key

    def restore(self, data: dict) -> None:
        """Inverse of ``checkpoint`` (drift needs ``rekey`` afterwards)."""
        level = data.get("level")
        self._reset(tuple(level) if isinstance(level, list) else level, None,
                    data["entry_it"], data["entry_t"])
        self.index = data["index"]
        self.active = data["active"]
        self.last_it, self.last_t = data["last_it"], data["last_t"]
        for name in ("proposals", "accepted", "neutral_accepts", "visits", "max_drift"):
            setattr(self, name, data[name])
        self._seen = None
        self._hll = HyperLogLog(data["hll_p"], bytes.fromhex(data["hll"]))


# --------------------------------------------------------------------------- circuit shape

def _histogram(values) -> dict:
    """``{str(value): count}`` sorted by value (JSON object keys must be strings)."""
    return {str(k): v for k, v in sorted(Counter(values).items())}


def _stats(xs) -> dict:
    if not xs:
        return {"mean": 0.0, "max": 0, "min": 0}
    return {"mean": sum(xs) / len(xs), "max": max(xs), "min": min(xs)}


def shape_from_gates(gates, outputs=None, n_inputs=None) -> dict:
    """Shape summary of an index-pair circuit (``ValueSet.gates()`` format).

    ``gates[k] = [i, j]``: gate k XORs nodes i and j; nodes ``< n_inputs`` are inputs and node
    ``n_inputs + k`` is gate k.  ``n_inputs`` defaults to the smallest index that makes every
    reference valid.  Returns gate count, depth (max output level, or max gate level without
    outputs), level and Hamming-weight histograms, gate/input fan-out (number of gates reading
    a node) stats and histogram, and how many outputs are gates (the rest are free inputs).
    """
    if n_inputs is None:
        n_inputs = 0
        for k, (i, j) in enumerate(gates):
            # A reference to node r at gate k requires r < n + k, i.e. n > r - k.
            n_inputs = max(n_inputs, i - k + 1, j - k + 1)
    level = [0] * n_inputs
    value = [1 << b for b in range(n_inputs)]
    fanout = [0] * (n_inputs + len(gates))
    for i, j in gates:
        level.append(max(level[i], level[j]) + 1)
        value.append(value[i] ^ value[j])
        fanout[i] += 1
        fanout[j] += 1
    glevels = level[n_inputs:]
    depth = max((level[o] for o in outputs), default=0) if outputs else max(glevels, default=0)
    gate_fan = fanout[n_inputs:]
    return {
        "n_inputs": n_inputs, "gates": len(gates), "depth": depth,
        "levels": _histogram(glevels),
        "weights": _histogram(bin(v).count("1") for v in value[n_inputs:]),
        "fanout": _stats(gate_fan), "fanout_hist": _histogram(gate_fan),
        "input_fanout": _stats(fanout[:n_inputs]),
        "output_gates": sum(1 for o in (outputs or ()) if o >= n_inputs),
    }


def symmetric_difference(before, after) -> dict:
    """``removed``/``added`` sorted value lists between two value sets (dossier symdiff)."""
    b, a = set(before), set(after)
    return {"removed": sorted(b - a), "added": sorted(a - b)}
