"""Elite archive: distinct good value sets kept for restarts and sharing.

Role in the method (DESIGN.md section 2): restarts may start from "a distinct elite from the
worker archive", and the campaign pool is fed with distinct DAGs per frontier point.  The
framework runs ended with 10 workers on 4 DAGs at fox_mu8 538/9 while 90 distinct DAGs at that
point sat in records, and seeding everyone with one shared DAG collapsed diversity.  So this
archive keeps *distinct, far-apart* members near the best rather than many near-copies:

* identity is ``ValueSet.key()`` (a frozenset of values; equal keys are the same DAG up to
  recipes), so duplicates are rejected in O(1);
* only members within ``band`` primary units of the archive best are kept (the near-best band);
* at most ``per_point`` members per objective point and ``capacity`` in total;
* on overflow the most *redundant* member goes: the one closest (Jaccard distance on value sets)
  to its nearest neighbour, taken from the overfull point, or from the worst point when the whole
  archive is full.  Nearest-neighbour distances are maintained incrementally, so an insertion
  costs one distance per member and an eviction recomputes only the members that pointed at the
  evicted one.

``sample_diverse(ref_key, rng)`` draws a member other than ``ref_key`` with probability rising
with its distance from ``ref_key`` and with its score, which is what a restart wants.

Offers are rare (new chain bests, sampled distinct DAGs, restarts), never per proposal.
"""
from __future__ import annotations

from ..config.schema import Knob, Section
from ..telemetry.metrics import jaccard_distance

KNOBS = Section("archive", "Elite archive of distinct value sets.", {
    "capacity": Knob(64, "Maximum members in total.", min=1),
    "per_point": Knob(16, "Maximum members at one objective point.", min=1),
    "band": Knob(2, "Keep members within this many primary units of the archive best.", min=0),
    "sample_power": Knob(2.0, "Restart sampling weight grows as distance ** sample_power.", min=0),
    "score_bias": Knob(0.5, "Restart sampling weight is multiplied by this per primary unit "
                       "above the archive best (1 = ignore score).", min=0, max=1),
})


#: Jaccard distance of two value sets (0 = equal, 1 = disjoint); one implementation for the
#: archive, the engine's dossiers/epochs and the telemetry panels.
distance = jaccard_distance


class Entry:
    """One archived value set with its score and nearest-neighbour bookkeeping."""
    __slots__ = ("key", "gates", "depth", "score", "feasible", "seq", "origin", "nn", "nn_key")

    def __init__(self, key, gates, depth, score, feasible, seq, origin):
        self.key = key
        self.gates = gates
        self.depth = depth
        self.score = tuple(score)
        self.feasible = feasible
        self.seq = seq
        self.origin = origin
        self.nn = 1.0          # distance to the nearest other member (1.0 when alone)
        self.nn_key = None

    def summary(self) -> dict:
        """JSON-safe description without the values."""
        return {"gates": self.gates, "depth": self.depth, "feasible": self.feasible,
                "seq": self.seq, "origin": self.origin, "nn": round(self.nn, 4)}


class Archive:
    """Distinct near-best value sets with diversity-aware eviction."""

    def __init__(self, cfg):
        self.capacity = cfg.capacity
        self.per_point = cfg.per_point
        self.band = cfg.band
        self.sample_power = cfg.sample_power
        self.score_bias = cfg.score_bias
        self._members: dict[frozenset, Entry] = {}
        self._points: dict[tuple, int] = {}
        self._seq = 0
        self.best: tuple | None = None
        self.offers = 0
        self.stored = 0

    # -- queries --------------------------------------------------------------------------
    def __len__(self):
        return len(self._members)

    def __contains__(self, key):
        return key in self._members

    def members(self) -> list[Entry]:
        """Members in insertion order."""
        return list(self._members.values())

    def keys(self) -> set:
        """Keys of all members (for pool exclusion)."""
        return set(self._members)

    def count(self, score) -> int:
        """Members at one objective point."""
        return self._points.get(tuple(score), 0)

    def distance_stats(self, key: frozenset) -> dict:
        """``{n, min, mean}`` of the distances from ``key`` to the other members (dossiers)."""
        ds = [distance(key, other) for other in self._members if other != key]
        if not ds:
            return {"n": 0, "min": None, "mean": None}
        return {"n": len(ds), "min": min(ds), "mean": sum(ds) / len(ds)}

    def diversity(self) -> dict:
        """Count, points, and mean / min nearest-neighbour distance (cheap: no pair scan)."""
        entries = list(self._members.values())
        if not entries:
            return {"count": 0, "points": 0, "nn_mean": None, "nn_min": None}
        nns = [e.nn for e in entries]
        return {"count": len(entries), "points": len(self._points),
                "nn_mean": sum(nns) / len(nns), "nn_min": min(nns),
                "best": list(self.best) if self.best is not None else None}

    # -- insertion ------------------------------------------------------------------------
    def offer(self, key: frozenset, gates: int, depth: int, score, feasible: bool,
              origin: str = "") -> bool:
        """Insert a value set; True when it is stored (it may be evicted later)."""
        self.offers += 1
        if key in self._members:
            return False
        score = tuple(score)
        best = self.best
        if best is not None and score[0] > best[0] + self.band:
            return False
        entry = Entry(key, gates, depth, score, feasible, self._seq, origin)
        self._seq += 1
        self._insert(entry)
        if best is None or score < best:
            self.best = score
            self._prune_band()
        if key not in self._members:
            return False
        if self._points[score] > self.per_point:
            self._evict([e for e in self._members.values() if e.score == score])
        if len(self._members) > self.capacity:
            worst = max(self._points)
            self._evict([e for e in self._members.values() if e.score == worst])
        stored = key in self._members
        self.stored += stored
        return stored

    def _insert(self, entry):
        key = entry.key
        for other in self._members.values():
            d = distance(key, other.key)
            if d < entry.nn:
                entry.nn = d
                entry.nn_key = other.key
            if d < other.nn:
                other.nn = d
                other.nn_key = key
        self._members[key] = entry
        self._points[entry.score] = self._points.get(entry.score, 0) + 1

    def _remove(self, entry):
        del self._members[entry.key]
        n = self._points[entry.score] - 1
        if n:
            self._points[entry.score] = n
        else:
            del self._points[entry.score]
        gone = entry.key
        for other in self._members.values():
            if other.nn_key == gone:
                self._recompute_nn(other)

    def _recompute_nn(self, entry):
        entry.nn = 1.0
        entry.nn_key = None
        key = entry.key
        for other in self._members:
            if other == key:
                continue
            d = distance(key, other)
            if d < entry.nn:
                entry.nn = d
                entry.nn_key = other

    def _evict(self, candidates):
        # Most redundant first; among equals the oldest, so fresh states can enter.
        victim = min(candidates, key=lambda e: (e.nn, e.seq))
        self._remove(victim)

    def _prune_band(self):
        limit = self.best[0] + self.band
        for entry in [e for e in self._members.values() if e.score[0] > limit]:
            self._remove(entry)

    # -- sampling -------------------------------------------------------------------------
    def sample_diverse(self, ref_key, rng) -> Entry | None:
        """A member other than ``ref_key``, favouring ones far from it and near the best."""
        cands = [e for e in self._members.values() if e.key != ref_key]
        if not cands:
            return None
        best0 = self.best[0]
        power = self.sample_power
        bias = self.score_bias
        weights = []
        for e in cands:
            w = distance(ref_key, e.key) ** power if ref_key is not None else 1.0
            weights.append(w * bias ** (e.score[0] - best0))
        total = sum(weights)
        if total <= 0.0:
            return cands[int(rng.random() * len(cands))]
        r = rng.random() * total
        acc = 0.0
        for e, w in zip(cands, weights):
            acc += w
            if r < acc:
                return e
        return cands[-1]

    # -- persistence ----------------------------------------------------------------------
    def state(self) -> dict:
        """JSON-safe state (values as sorted lists, insertion order kept)."""
        return {"seq": self._seq, "best": list(self.best) if self.best is not None else None,
                "offers": self.offers, "stored": self.stored,
                "members": [[sorted(e.key), e.gates, e.depth, list(e.score), e.feasible, e.seq,
                             e.origin] for e in self._members.values()]}

    def load_state(self, data: dict) -> None:
        """Restore ``state()``; nearest-neighbour distances are recomputed (pure functions of
        the member set, so they equal the saved engine's)."""
        self._members.clear()
        self._points.clear()
        for values, gates, depth, score, feasible, seq, origin in data.get("members", []):
            self._insert(Entry(frozenset(values), gates, depth, score, feasible, seq, origin))
        self._seq = data.get("seq", len(self._members))
        best = data.get("best")
        self.best = tuple(best) if best is not None else None
        self.offers = data.get("offers", 0)
        self.stored = data.get("stored", 0)
