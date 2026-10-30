"""Depth-3 specialist: the anneal3 partition annealer, as a root constructor and as a move.

Role in the method: the forward MixColumns 97@3 came from this annealer (235 s from scratch),
and so did the root of the capped-walk recipe that gave 91@4 (docs/evidence). This port reaches
97@3 from scratch in about 3M iterations (about 95 s at 30k iterations/s). Generic walk/LNS
are weak at a hard cap of 3 because almost every single-value edit breaks some output. The
partition model instead edits the *structure* of a depth-3 circuit directly. Here it is:

* ``construct.anneal3``: a root builder for the restart controller (see ``moves/construct.py``);
* ``depth3.anneal``: a move, applicable only when the real depth cap is 3 and every row has
  weight <= 8. It runs v1's seed loop (anneal, iterated local search, fresh seed) a slice per
  proposal on a private partition and proposes only partitions smaller than the chain (see
  the class docstring). The 2026-10-28 campaign showed why: v2's loop proposed its wandering
  final partitions, and with soft depth slack the cap-3 chains sat at 89@5 and rolled back
  every depth-3 proposal for two hours; this loop in isolation reaches 97@3 in ~15 s.

The model (ported from ``sources/mixcolumns-v2/pipeline/engines.py`` ``engine_anneal3``, made
generic in n and in row weights)
--------------------------------------------------------------------------------------------
In a depth-3 circuit every value at level <= 2 has weight <= 4: level-1 values are *pairs*
(weight 2), level-2 values are *bigs* (weight 3 = pair ^ input, weight 4 = pair ^ pair, a
choice of "pairing"). A row t of weight 5..8 is a level-3 output ``t = a ^ b`` with
``wt(a), wt(b) <= 4``: its *split*. With weight >= 5, a and b overlap in at most one bit, and only
for weight 5 or 6. So the split list (disjoint splits plus, with ``cancel_splits``, one-bit
cancellation splits) covers every depth-3 recipe of the row. Rows of weight 2 are forced pairs.
Rows of weight 3..4 are forced bigs, built at level 2; this is a restriction, since the model
never builds them at level 3. The gate count is exact:

    cost = #split rows + #distinct bigs + #distinct pairs

because the three classes have disjoint weights. A proposal edits reference counts through an
undo log, so a rejected annealing step costs only its own edits. The annealing schedule, the
operators (re-split 60%, re-pair 25%, greedy re-split 15%, periodic kicks, snap-back to the best
after ``patience``) and the optional joint group update follow v2. The joint update's exact
fixed-parent pair optimizer is ``optimize_pairs``, a port of v2 ``optimize_depth3`` that is
bounded by nodes only (no clock), so every result is replayable.
"""
from __future__ import annotations

import hashlib
import math
from itertools import combinations

from ..config.schema import Knob, Section
from ..core.budget import Budget
from .base import Move, Proposal, register
from .construct import bits_of, target_rows
from .structural import apply_values, search_cap

MAX_ROW_WEIGHT = 8          # depth 3 cannot produce a row of weight > 2**3


def _anneal_knobs(iterations: int, iterations_doc: str, ils_rounds: int) -> dict:
    """Knobs shared by the root and the move (each section declares its own copy)."""
    return {
        "iterations": Knob(iterations, iterations_doc, min=1),
        "ils_rounds": Knob(ils_rounds, "Iterated-local-search rounds after a cooling period: "
                           "restore the best, randomize kick_min..kick_max rows, descend to a "
                           "local optimum, keep if no worse (v1 engine_anneal3: its anneal "
                           "reached ~100 gates, this tail made 97@3). 0 = none.", min=0),
        "t0": Knob(2.0, "Annealing temperature at the start of each cooling period.", min=1e-6),
        "t1": Knob(0.05, "Annealing temperature at the end of each cooling period.", min=1e-6),
        "period": Knob(150_000, "Iterations per geometric cooling period (then it restarts).",
                       min=1),
        "p_split": Knob(0.6, "Probability of re-splitting one random row at random.",
                        min=0, max=1),
        "p_repair": Knob(0.25, "Probability of re-pairing one random weight-3/4 parent "
                         "(the rest of the mass is a greedy re-split).", min=0, max=1),
        "kick_every": Knob(0, "Every this many annealing iterations: re-split kick_min..kick_max "
                           "rows at random, then greedily re-split all rows (0 = never; v2 used "
                           "257 and made 0 improvements in 67.8M iterations).", min=0),
        "kick_min": Knob(2, "Fewest rows randomized by a kick (ILS round or annealing kick).",
                         min=0),
        "kick_max": Knob(6, "Most rows randomized by a kick.", min=0),
        "patience": Knob(0, "Annealing iterations without a new best before snapping back to "
                         "the best partition (0 = never, as v1; v2 used 50,000).", min=0),
        "joint_every": Knob(0, "Every this many iterations: joint update of a small row group "
                            "with exact fixed-parent pair optimisation (0 = never, as v2).",
                            min=0),
        "joint_outputs": Knob(3, "Rows in a joint group.", min=2),
        "joint_split_candidates": Knob(6, "Split choices kept per row in a joint group.", min=2),
        "joint_beam": Knob(8, "Beam width over the joint group's split assignments.", min=1),
        "joint_nodes": Knob(1500, "Branch-and-bound node limit of each fixed-parent pair "
                            "optimisation.", min=0),
        "cancel_splits": Knob(True, "Also offer one-bit cancellation splits for rows of weight 5 "
                              "and 6 (needed to cover every depth-3 recipe)."),
    }


ROOT_KNOBS = Section(
    "construct.anneal3", "Depth-3 partition annealer used as a restart root (cap None or >= 3).",
    _anneal_knobs(150_000, "Annealing iterations for one root (one work unit each; one "
                  "cooling period, ~5 s).", 300))

MOVE_KNOBS = Section(
    "moves.depth3.anneal", "Depth-3 partition annealer as a move (real cap 3, rows <= 8).",
    {"weight": Knob(12.0, "Prior scheduler weight (time share) in the plateau phase. The move "
                    "only applies at a real depth cap of 3, where single-value edits are weak "
                    "and v1 ran this annealer alone (97@3 in 38-337 s per core).", min=0),
     "burst_weight": Knob(1.0, "Scheduler weight in the burst phase.", min=0),
     "ils_batch": Knob(16, "ILS rounds per proposal (a round is ~10 ms on MixColumns).", min=1),
     "fresh_seeds": Knob(True, "After a seed's ILS rounds, start over from a random partition "
                         "(v1: a fresh seed every cooling period; one seed in three stalls at "
                         "98). False: keep annealing from the seed's best."),
     **_anneal_knobs(2_000, "Annealing iterations per proposal.", 2500)})

KNOBS = (ROOT_KNOBS, MOVE_KNOBS)


# ----------------------------------------------------------------------------------- model
def _canon(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def root_reason(n: int, rows, cap=None) -> str | None:
    """None when the depth-3 model applies to the rows (and cap), else why not."""
    if cap is not None and cap < 3:
        return f"depth-3 model needs cap >= 3 (got {cap})"
    heavy = max((t.bit_count() for t in rows), default=0)
    if heavy > MAX_ROW_WEIGHT:
        return f"row weight {heavy} > {MAX_ROW_WEIGHT}"
    return None


def model_signature(n: int, rows, cancel_splits: bool) -> str:
    """Short hash identifying a model (target and split list), stored with saved state."""
    body = repr((n, sorted(set(rows)), bool(cancel_splits))).encode()
    return hashlib.sha256(body).hexdigest()[:16]


class Depth3Model:
    """Static part of the partition model for one target: rows, splits and pairings."""

    def __init__(self, n: int, rows, cancel_splits: bool = True):
        self.n = n
        distinct = [t for t in dict.fromkeys(rows) if t]
        self.T = [t for t in distinct if t.bit_count() >= 5]
        self.forced_pairs = [t for t in distinct if t.bit_count() == 2]
        self.forced_bigs = [t for t in distinct if 3 <= t.bit_count() <= 4]
        self.splits = [self._gen_splits(t, cancel_splits) for t in self.T]
        self.split_index = [{s: i for i, s in enumerate(opts)} for opts in self.splits]
        self.pairings: dict[int, tuple] = {}
        self.cancel_splits = cancel_splits
        self.signature = model_signature(n, rows, cancel_splits)
        # Flat per-part cost records for the hot greedy loop (see part_cost).
        info: dict[int, tuple] = {}
        for opts in self.splits:
            for split in opts:
                for m in split:
                    if m not in info:
                        info[m] = self._part_info(m)
        self.split_info = [[(info[a], info[b]) for a, b in opts] for opts in self.splits]

    def _part_info(self, m: int) -> tuple:
        w = m.bit_count()
        if w == 1:
            return (0, m)
        if w == 2:
            return (1, m)
        opts = self.pairing_options(m)
        if w == 3:
            return (3, m, opts[0][0], opts[1][0], opts[2][0])
        return (4, m, *opts[0], *opts[1], *opts[2])

    def _gen_splits(self, t: int, cancel: bool) -> list[tuple[int, int]]:
        bits = bits_of(t)
        w = len(bits)
        out = set()
        for k in range(max(1, w - 4), min(4, w - 1) + 1):
            for comb in combinations(bits, k):
                a = sum(comb)
                out.add(_canon(a, t ^ a))
        if cancel and w in (5, 6):
            outside = [1 << i for i in range(self.n) if not t >> i & 1]
            for k in range(max(1, w - 3), min(3, w - 1) + 1):
                for comb in combinations(bits, k):
                    a = sum(comb)
                    b = t ^ a
                    for x in outside:
                        out.add(_canon(a | x, b | x))
        return sorted(out)

    def pairing_options(self, m: int) -> tuple:
        """Canonical pairings of a weight-3/4 parent: tuples of the pairs it is built from."""
        opts = self.pairings.get(m)
        if opts is None:
            bits = bits_of(m)
            if len(bits) == 3:
                opts = tuple((m ^ bit,) for bit in bits)
            elif len(bits) == 4:
                a, b, c, d = bits
                opts = (_canon(a | b, c | d), _canon(a | c, b | d), _canon(a | d, b | c))
            else:
                raise ValueError("a depth-2 parent must have weight 3 or 4")
            self.pairings[m] = opts
        return opts

    # ------------------------------------------------------------------ snapshots to circuits
    def recipes(self, snap) -> list[tuple[int, int, int]]:
        """``(m, a, b)`` triples of the circuit described by a snapshot."""
        choices, pairing = snap
        out = {}
        pairs = set(self.forced_pairs)
        bigs = set(self.forced_bigs)
        for o, idx in enumerate(choices):
            a, b = self.splits[o][idx]
            out[self.T[o]] = (a, b)
            for m in (a, b):
                w = m.bit_count()
                if w == 2:
                    pairs.add(m)
                elif w >= 3:
                    bigs.add(m)
        for m in bigs:
            pr = pairing[m]
            pairs.update(pr)
            a = pr[0]
            out[m] = (a, m ^ a)
        for p in pairs:
            low = p & -p
            out[p] = (low, p ^ low)
        return [(m, a, b) for m, (a, b) in out.items()]

    def values(self, snap) -> set[int]:
        """Non-input values of the circuit described by a snapshot."""
        return {m for m, _, _ in self.recipes(snap)}

    def decode(self, gates, n: int):
        """Snapshot of a depth-3 circuit given as index-pair gates, or None if not in the model.

        Each split row must be built from one of its listed splits. Each weight-3/4 parent
        (including forced rows) must be a level-2 value built from its pairs. Unused values
        are ignored, so decoding never costs more gates than the circuit has.
        """
        masks = [1 << i for i in range(n)]
        recipe = {}
        for a, b in gates:
            ma, mb = masks[a], masks[b]
            m = ma ^ mb
            masks.append(m)
            recipe[m] = (ma, mb)
        choices = []
        bigs = set(self.forced_bigs)
        for o, t in enumerate(self.T):
            ab = recipe.get(t)
            idx = None if ab is None else self.split_index[o].get(_canon(*ab))
            if idx is None:
                return None
            choices.append(idx)
            for m in ab:
                if m.bit_count() >= 3:
                    bigs.add(m)
        pairing = {}
        for m in bigs:
            ab = recipe.get(m)
            if ab is None:
                return None
            pr = tuple(sorted(x for x in ab if x.bit_count() == 2))
            if pr not in self.pairing_options(m):
                return None
            pairing[m] = pr
        for p in self.forced_pairs:
            if p not in recipe:
                return None
        return (choices, pairing)


# ------------------------------------------------------------------------------ partition
def _part_cost(e, pairs, big):
    """Gates that adding a part costs now; ``e`` is a ``Depth3Model._part_info`` record.

    (0, m) input: free. (1, m) pair: 1 unless present. (3, m, q1, q2, q3) weight-3 big:
    0 if present, else 1 plus 0 if one of its three pairs exists, else 1. (4, m, x1, y1, ...)
    weight-4 big: 0 if present, else 1 plus the fewest missing pairs over its three pairings.
    """
    k = e[0]
    if k == 0:
        return 0
    if k == 1:
        return 0 if e[1] in pairs else 1
    if e[1] in big:
        return 0
    if k == 3:
        return 1 if (e[2] in pairs or e[3] in pairs or e[4] in pairs) else 2
    c = (e[2] not in pairs) + (e[3] not in pairs)
    if c:
        c2 = (e[4] not in pairs) + (e[5] not in pairs)
        if c2 < c:
            c = c2
        if c:
            c3 = (e[6] not in pairs) + (e[7] not in pairs)
            if c3 < c:
                c = c3
    return 1 + c


class Partition:
    """Dynamic partition state: split choice per row, reference-counted parents and pairs.

    Edits append to ``log`` while it is a list; ``undo(log, cost)`` reverts them exactly, so a
    rejected annealing step costs only what it changed. Log entries are small tuples:
    0/1 pair added/removed, 2/4 big reference up/down, 3/5 big created/deleted, 6 re-paired,
    7 split choice changed.
    """
    __slots__ = ("model", "choice", "big", "pairs", "pairing", "cost", "log")

    def __init__(self, model: Depth3Model):
        self.model = model
        self.choice: list = []
        self.big: dict[int, int] = {}
        self.pairs: dict[int, int] = {}
        self.pairing: dict[int, tuple] = {}
        self.cost = 0
        self.log = None

    # ------------------------------------------------------------------ primitive edits
    def _pair_add(self, p):
        c = self.pairs.get(p, 0)
        self.pairs[p] = c + 1
        if not c:
            self.cost += 1
        if self.log is not None:
            self.log.append((0, p))

    def _pair_del(self, p):
        c = self.pairs[p]
        if c == 1:
            del self.pairs[p]
            self.cost -= 1
        else:
            self.pairs[p] = c - 1
        if self.log is not None:
            self.log.append((1, p))

    def best_pairing(self, m, rng):
        """Pairing of m needing the fewest new pairs (uniform among ties)."""
        pairs = self.pairs
        best = None
        best_score = 3
        ties = 0
        for pr in self.model.pairing_options(m):
            s = 0
            for p in pr:
                if p not in pairs:
                    s += 1
            if s < best_score:
                best_score, best, ties = s, pr, 1
            elif s == best_score:
                ties += 1
                if rng.random() * ties < 1.0:
                    best = pr
        return best

    def _part_add(self, m, rng, forced=None):
        w = m.bit_count()
        if w == 1:
            return
        if w == 2:
            self._pair_add(m)
            return
        c = self.big.get(m, 0)
        self.big[m] = c + 1
        log = self.log
        if c:
            if log is not None:
                log.append((2, m))
            return
        self.cost += 1
        pr = forced if forced is not None else self.best_pairing(m, rng)
        self.pairing[m] = pr
        if log is not None:
            log.append((3, m))
        for p in pr:
            self._pair_add(p)

    def _part_del(self, m):
        w = m.bit_count()
        if w == 1:
            return
        if w == 2:
            self._pair_del(m)
            return
        c = self.big[m]
        log = self.log
        if c > 1:
            self.big[m] = c - 1
            if log is not None:
                log.append((4, m))
            return
        del self.big[m]
        self.cost -= 1
        pr = self.pairing.pop(m)
        if log is not None:
            log.append((5, m, pr))
        for p in pr:
            self._pair_del(p)

    def undo(self, log, cost):
        """Revert the edits recorded in ``log`` (newest first) and restore ``cost``."""
        pairs, big, pairing, choice = self.pairs, self.big, self.pairing, self.choice
        for e in reversed(log):
            k = e[0]
            if k == 0:
                p = e[1]
                c = pairs[p]
                if c == 1:
                    del pairs[p]
                else:
                    pairs[p] = c - 1
            elif k == 1:
                p = e[1]
                pairs[p] = pairs.get(p, 0) + 1
            elif k == 2:
                big[e[1]] -= 1
            elif k == 3:
                del big[e[1]]
                del pairing[e[1]]
            elif k == 4:
                big[e[1]] += 1
            elif k == 5:
                big[e[1]] = 1
                pairing[e[1]] = e[2]
            elif k == 6:
                pairing[e[1]] = e[2]
            else:
                choice[e[1]] = e[2]
        self.cost = cost

    # ------------------------------------------------------------------ operators
    def set_choice(self, o, idx, rng, forced=None):
        """Use split ``idx`` for row o (None: no split, during greedy re-choice)."""
        old = self.choice[o]
        if self.log is not None:
            self.log.append((7, o, old))
        splits = self.model.splits[o]
        if old is not None:
            for m in splits[old]:
                self._part_del(m)
        self.choice[o] = idx
        if idx is not None:
            for m in splits[idx]:
                self._part_add(m, rng, None if forced is None else forced.get(m))

    def repair(self, m, rng):
        """Re-pair parent m with its currently cheapest pairing."""
        old = self.pairing[m]
        for p in old:
            self._pair_del(p)
        new = self.best_pairing(m, rng)
        self.pairing[m] = new
        if self.log is not None:
            self.log.append((6, m, old))
        for p in new:
            self._pair_add(p)

    def delta_add(self, m):
        """Gates that adding parent m would cost now (its best pairing)."""
        w = m.bit_count()
        if w == 1:
            return 0
        pairs = self.pairs
        if w == 2:
            return 0 if m in pairs else 1
        if m in self.big:
            return 0
        best = 3
        for pr in self.model.pairing_options(m):
            s = 0
            for p in pr:
                if p not in pairs:
                    s += 1
            if s < best:
                best = s
        return 1 + best

    def greedy_rechoice(self, o, rng):
        """Re-split row o with its currently cheapest split (uniform among ties).

        This is the annealer's hot loop (up to ~600 splits per row), so the part costs are
        computed inline from the precomputed records instead of calling ``delta_add``.
        """
        self.set_choice(o, None, rng)
        pairs, big = self.pairs, self.big
        rnd = rng.random
        best = None
        best_score = 1 << 30
        ties = 0
        i = -1
        for ea, eb in self.model.split_info[o]:
            i += 1
            s = _part_cost(ea, pairs, big)
            if s > best_score:
                continue
            s += _part_cost(eb, pairs, big)
            if s < best_score:
                best_score, best, ties = s, i, 1
            elif s == best_score:
                ties += 1
                if rnd() * ties < 1.0:
                    best = i
        self.set_choice(o, best, rng)

    # ------------------------------------------------------------------ snapshots
    def snapshot(self):
        """``(choices, pairing)``: enough to rebuild this state exactly."""
        return (list(self.choice), dict(self.pairing))

    def restore(self, snap, rng):
        """Rebuild from a snapshot (or at random when ``snap`` is None)."""
        model = self.model
        self.log = None
        self.big, self.pairs, self.pairing = {}, {}, {}
        self.cost = len(model.T)
        self.choice = [None] * len(model.T)
        pairing = {} if snap is None else snap[1]
        for p in model.forced_pairs:
            self._pair_add(p)
        for m in model.forced_bigs:
            self._part_add(m, rng, pairing.get(m))
        for o in range(len(model.T)):
            idx = rng.randrange(len(model.splits[o])) if snap is None else snap[0][o]
            self.set_choice(o, idx, rng, pairing)
        # Parent choices draw from ``list(self.big)``, so its order is part of the state:
        # follow the snapshot's order so a resumed annealer replays exactly.
        if snap is not None and len(pairing) == len(self.big) and all(m in self.big for m in pairing):
            self.big = {m: self.big[m] for m in pairing}
            self.pairing = {m: self.pairing[m] for m in pairing}


# ----------------------------------------------------------------- fixed-parent optimizer
def optimize_pairs(parents, existing_pairs, rng, max_nodes):
    """Choose pairings for fixed weight-3/4 parents that minimise the new pairs.

    Port of v2 ``optimize_depth3`` (``search/engines/vendor_v2/deadline_search.py``), bounded
    by ``max_nodes`` only, so it is replayable. Weight-2 parents are required pairs. Returns
    ``(pairs, pairings, complete)``: the union of required pairs, ``{parent: pairing}`` with
    canonical pairings, and whether the branch and bound finished (an optimum of this fixed-
    parent problem only). Returns None if a parent has weight > 4.
    """
    parents = sorted(set(parents))
    free = set(existing_pairs)
    if any(m.bit_count() > 4 for m in parents):
        return None
    direct = {m for m in parents if m.bit_count() == 2}
    choices = {}
    for m in parents:
        bits = bits_of(m)
        if len(bits) == 3:
            choices[m] = [(m ^ bit,) for bit in bits]
        elif len(bits) == 4:
            a, b, c, d = bits
            choices[m] = [_canon(a | b, c | d), _canon(a | c, b | d), _canon(a | d, b | c)]
    popularity = {}
    for opts in choices.values():
        for ps in opts:
            for p in ps:
                popularity[p] = popularity.get(p, 0) + 1
    # Parents whose options are widely shared go first: better greedy incumbent, earlier cuts.
    order = sorted(choices, key=lambda m: (-max(sum(popularity[p] for p in ps)
                                               for ps in choices[m]), m))
    greedy_pairs = set(direct)
    greedy = {}
    for m in order:
        opts = list(choices[m])
        rng.shuffle(opts)
        opts.sort(key=lambda ps: (len(set(ps) - greedy_pairs - free),
                                  -sum(popularity[p] for p in ps)))
        greedy_pairs.update(opts[0])
        greedy[m] = opts[0]
    best_pairs, best_pairings = greedy_pairs, greedy
    best_cost = len(best_pairs - free)
    nodes = 0
    complete = True
    seen = set()
    stack = [(0, frozenset(direct), {})]
    while stack:
        if nodes >= max_nodes:
            complete = False
            break
        i, required, picked = stack.pop()
        nodes += 1
        paid = required - free
        if len(paid) >= best_cost:
            continue
        if i == len(order):
            best_cost, best_pairs, best_pairings = len(paid), set(required), picked
            continue
        signature = (i, paid)
        if signature in seen:
            continue
        seen.add(signature)
        # Safe bound: the largest single shortfall (shortfalls may share one new pair).
        extra = max(min(len(set(ps) - required - free) for ps in choices[m]) for m in order[i:])
        if len(paid) + extra >= best_cost:
            continue
        m = order[i]
        opts = list(choices[m])
        rng.shuffle(opts)
        opts.sort(key=lambda ps: (len(set(ps) - required - free),
                                  -sum(popularity[p] for p in ps)))
        for ps in reversed(opts):
            nxt = dict(picked)
            nxt[m] = ps
            stack.append((i + 1, required | set(ps), nxt))
    return best_pairs, best_pairings, complete


# ------------------------------------------------------------------------------ annealing
class AnnealParams:
    """Annealer settings read once from a knob view (root or move section)."""
    __slots__ = ("iterations", "ils_rounds", "t0", "t1", "period", "p_split", "p_repair",
                 "kick_every",
                 "kick_min", "kick_max", "patience", "joint_every", "joint_outputs",
                 "joint_split_candidates", "joint_beam", "joint_nodes", "cancel_splits")

    def __init__(self, view):
        for name in self.__slots__:
            setattr(self, name, view[name])


def _joint_update(part, rng, prm):
    """Joint re-split of a small row group with exact fixed-parent pair optimisation (v2).

    The group is one random row plus the rows sharing most of its current parents. A beam
    over their split menus is scored by new parents against the retained outside bank. Each
    beam entry is priced exactly by ``optimize_pairs`` against the outside pairs. The state
    only changes to an assignment that is no more expensive.
    """
    model = part.model
    T, splits = model.T, model.splits
    if len(T) < 2:
        return
    old = part.snapshot()
    old_cost = part.cost
    size = max(2, min(prm.joint_outputs, len(T)))
    seed = rng.randrange(len(T))
    seed_parents = set(splits[seed][part.choice[seed]])
    others = [o for o in range(len(T)) if o != seed]
    rng.shuffle(others)
    others.sort(key=lambda o: -len(seed_parents & set(splits[o][part.choice[o]])))
    group = [seed] + others[:size - 1]
    in_group = set(group)
    outside_big = set(model.forced_bigs)
    outside_pairs = set(model.forced_pairs)
    for m in model.forced_bigs:
        outside_pairs.update(part.pairing[m])
    for o in range(len(T)):
        if o in in_group:
            continue
        for m in splits[o][part.choice[o]]:
            w = m.bit_count()
            if w == 2:
                outside_pairs.add(m)
            elif w >= 3:
                outside_big.add(m)
                outside_pairs.update(part.pairing[m])
    count = prm.joint_split_candidates
    menus = {}
    for o in group:
        options = list(range(len(splits[o])))
        rng.shuffle(options)
        options.sort(key=lambda i: part.delta_add(splits[o][i][0]) + part.delta_add(splits[o][i][1]))
        chosen = [part.choice[o]] + options[:max(1, count - 2)]
        rest = [i for i in options if i not in chosen]
        if rest:
            chosen += rng.sample(rest, min(2, len(rest)))
        menus[o] = list(dict.fromkeys(chosen))
    beam = [({}, frozenset(), frozenset())]
    for o in group:
        expanded = []
        for assign, bigs, directs in beam:
            for idx in menus[o]:
                nb, nd = set(bigs), set(directs)
                for m in splits[o][idx]:
                    w = m.bit_count()
                    if w >= 3:
                        nb.add(m)
                    elif w == 2:
                        nd.add(m)
                na = dict(assign)
                na[o] = idx
                score = len(nb - outside_big) + len(nd - outside_pairs)
                expanded.append((score, rng.random(), na, nb, nd))
        expanded.sort(key=lambda row: row[:2])
        beam = [(a, b, d) for _, _, a, b, d in expanded[:prm.joint_beam]]
    baseline = {o: part.choice[o] for o in group}
    if not any(a == baseline for a, _, _ in beam):
        beam.insert(0, (baseline, frozenset(), frozenset()))
    best, best_cost = None, old_cost
    for assign, _, _ in beam:
        selected = {m for o, idx in assign.items() for m in splits[o][idx]}
        build = {m for m in selected - outside_big if m.bit_count() >= 2}
        result = optimize_pairs(build, outside_pairs, rng, prm.joint_nodes)
        if result is None:
            continue
        pairs, pairings, _ = result
        new_bigs = {m for m in selected if m.bit_count() >= 3} - outside_big
        cost = len(T) + len(outside_big) + len(new_bigs) + len(outside_pairs | pairs)
        if cost < best_cost or (cost == best_cost and rng.random() < 0.5):
            choices = list(part.choice)
            for o, idx in assign.items():
                choices[o] = idx
            pairing = {m: part.pairing[m] for m in outside_big}
            pairing.update(pairings)
            best, best_cost = (choices, pairing), cost
    if best is not None:
        part.restore(best, rng)
        if part.cost > old_cost:        # a beam price that disagrees with the state: keep old
            part.restore(old, rng)


def anneal(part, rng, prm, iterations, budget, it0=0):
    """Run up to ``iterations`` annealing steps on ``part``; return the best seen.

    Returns ``(best_snapshot, best_cost, it, steps)``, where ``it`` is the global iteration
    counter (it sets the temperature phase and the kick/joint timing) and ``steps`` the steps
    actually run. One step is one work unit; the budget is charged and polled every 64 steps.
    """
    t0, ratio, period = prm.t0, prm.t1 / prm.t0, prm.period
    p_split, p_rep = prm.p_split, prm.p_split + prm.p_repair
    kick_every, joint_every, patience = prm.kick_every, prm.joint_every, prm.patience
    model = part.model
    nT = len(model.T)
    sizes = [len(s) for s in model.splits]
    rnd, rrange = rng.random, rng.randrange
    exp = math.exp
    best = part.snapshot()
    best_cost = part.cost
    last = it = it0
    steps = 0
    if not nT:
        return best, best_cost, it, steps
    charged = 0               # steps charged to the budget (in advance, 64 at a time)
    for steps in range(1, iterations + 1):
        if not steps & 63:
            charged = steps
            if not budget.tick(64):
                steps -= 1        # this step is not run (one unit stays charged)
                break
        it += 1
        before = part.cost
        if joint_every and it % joint_every == 0:
            _joint_update(part, rng, prm)
        else:
            log = []
            part.log = log
            if kick_every and it % kick_every == 0:
                hi = max(prm.kick_min, prm.kick_max)
                for _ in range(rng.randint(prm.kick_min, hi)):
                    o = rrange(nT)
                    part.set_choice(o, rrange(sizes[o]), rng)
                order = list(range(nT))
                rng.shuffle(order)
                for o in order:
                    part.greedy_rechoice(o, rng)
            else:
                r = rnd()
                if r < p_split:
                    o = rrange(nT)
                    part.set_choice(o, rrange(sizes[o]), rng)
                elif r < p_rep and part.big:
                    part.repair(rng.choice(list(part.big)), rng)
                else:
                    part.greedy_rechoice(rrange(nT), rng)
            part.log = None
            delta = part.cost - before
            if delta > 0:
                temp = t0 * ratio ** ((it % period) / period)
                if rnd() > exp(-delta / temp):
                    part.undo(log, before)
        if part.cost < best_cost:
            best_cost = part.cost
            best = part.snapshot()
            last = it
        elif patience and it - last >= patience:
            part.restore(best, rng)
            last = it
    if steps > charged:
        budget.tick(steps - charged)
    return best, best_cost, it, steps


def descend(part, rng, budget) -> int:
    """Move ``part`` to a local optimum: greedily re-split every row (random order) and re-pair
    every weight-3/4 parent, repeating until a whole sweep gains nothing.  One work unit per
    operator call; returns the work and stops early when the budget runs out."""
    order = list(range(len(part.model.T)))
    work = 0
    improved = True
    while improved:
        improved = False
        rng.shuffle(order)
        for o in order:
            c = part.cost
            part.greedy_rechoice(o, rng)
            if part.cost < c:
                improved = True
        for m in list(part.big):
            if m in part.big:           # an earlier re-pair may have dropped it
                c = part.cost
                part.repair(m, rng)
                if part.cost < c:
                    improved = True
        n = len(order) + len(part.big)
        work += n
        if not budget.tick(n):
            break
    return work


def ils(part, rng, prm, cur, cur_cost, rounds, budget):
    """Up to ``rounds`` rounds of iterated local search around snapshot ``cur``: restore it,
    re-split ``kick_min..kick_max`` random rows at random, ``descend``, and keep the result
    when it is no worse (plateau moves included).  This is v1 ``engine_anneal3``'s tail: its
    150k-step anneal ended near 100 gates on MixColumns and these rounds took it to 97 (an
    ablation on this port: 97 after 19-1,470 rounds).  Returns ``(cur, cur_cost, rounds_run,
    work)``; ``part`` is left on the last round's state."""
    nT = len(part.model.T)
    if not nT:
        return cur, cur_cost, 0, 0
    sizes = [len(s) for s in part.model.splits]
    lo = prm.kick_min
    hi = max(lo, prm.kick_max)
    done = work = 0
    while done < rounds:
        done += 1
        part.restore(cur, rng)
        for _ in range(rng.randint(lo, hi)):
            o = rng.randrange(nT)
            part.set_choice(o, rng.randrange(sizes[o]), rng)
        work += nT + descend(part, rng, budget)
        if part.cost <= cur_cost:
            cur, cur_cost = part.snapshot(), part.cost
        if budget.exhausted():
            break
    return cur, cur_cost, done, work


# ---------------------------------------------------------------------------- root builder
def build_anneal3_root(n, rows, rng, cap, budget, cfg):
    """Root constructor: anneal a random partition; return the best circuit's recipes.

    ``cfg`` is the ``construct`` view (``cfg.anneal3`` holds the knobs). Returns
    ``(triples, info)`` for ``construct.build_root``. Raises ValueError when the model does not
    apply, so that ``build_root`` falls back to ``naive``.
    """
    reason = root_reason(n, rows, cap)
    if reason is not None:
        raise ValueError(reason)
    prm = AnnealParams(cfg.anneal3)
    model = Depth3Model(n, rows, prm.cancel_splits)
    part = Partition(model)
    part.restore(None, rng)
    for o in range(len(model.T)):        # greedy start: random splits waste the first period
        part.greedy_rechoice(o, rng)
    best, cost, _, steps = anneal(part, rng, prm, prm.iterations, budget)
    rounds = 0
    if prm.ils_rounds and not budget.exhausted():
        part.restore(best, rng)
        descend(part, rng, budget)
        if part.cost <= cost:
            best, cost = part.snapshot(), part.cost
        best, cost, rounds, _ = ils(part, rng, prm, best, cost, prm.ils_rounds, budget)
    return model.recipes(best), {"model_cost": cost, "iterations": steps, "ils_rounds": rounds}


# ------------------------------------------------------------------------------------ move
def _encode_snap(model, snap) -> dict:
    """JSON form of a partition snapshot: each row's split as masks, each pairing by parent."""
    choice, pairing = snap
    return {"choices": [list(model.splits[o][i]) for o, i in enumerate(choice)],
            "pairing": {str(m): list(pr) for m, pr in pairing.items()}}


def _decode_snap(model, data):
    """Inverse of ``_encode_snap`` for this model, or None when it does not fit."""
    if "choices" not in data:
        return None
    choices = [model.split_index[o].get(_canon(*ab)) if o < len(model.T) else None
               for o, ab in enumerate(data["choices"])]
    if None in choices or len(choices) != len(model.T):
        return None
    return choices, {int(m): tuple(pr) for m, pr in data.get("pairing", {}).items()}


@register
class Depth3Anneal(Move):
    """``depth3.anneal``: v1's seed loop (anneal, then ILS, then a fresh seed), run a slice per
    proposal on a private partition, proposing only partitions smaller than the chain.

    Applicable when the real depth cap is 3 and every row has weight <= 8. The move keeps a
    *seed*: a partition being worked on and the best partition the seed reached. Each proposal
    runs one slice of the seed's current stage:

    * ``anneal``: ``iterations`` annealing steps; when the global iteration counter crosses a
      cooling period, the seed's best is descended to a local optimum and the stage becomes
    * ``ils``: ``ils_batch`` ILS rounds around the seed's best; after ``ils_rounds`` rounds the
      seed is done and (``fresh_seeds``) a new one starts from a random partition.

    The chain is read only when it changed and is smaller than the seed's best: then the seed
    becomes the decoded chain (if it decodes) and goes straight to ILS around it. The proposal
    is the seed's best when it is smaller than the chain, else nothing (the annealer's uphill
    wandering stays private: v2 proposed its final partitions and the threshold acceptance
    rolled back every depth-3 edit of a smaller, deeper chain). Trace fields: ``stage``,
    ``seed``, ``rounds``, ``start_cost`` (seed best before), ``best_cost``, ``chain_size``,
    ``synced``, ``it``, ``added``/``removed``. Work: one unit per annealing step or ILS
    operator call; deterministic (no clock).
    """
    name = "depth3.anneal"
    family = "depth3"
    knobs = MOVE_KNOBS

    def __init__(self, settings):
        super().__init__(settings)
        self._model = None
        self._part = None
        self._it = 0
        self._last_key = None
        self._pending = None            # load_state data waiting for its model
        self._stage = "anneal"
        self._best = None               # the seed's best snapshot and its cost
        self._best_cost = None
        self._rounds = 0                # ILS rounds run on this seed
        self._seed = 0                  # seeds started (for traces)

    def applicable(self, target, objective) -> str | None:
        # The real cap decides, not the search cap: this move only ever emits depth-3
        # circuits, which fit any search cap >= 3, so the gates objective's soft slack
        # (search cap 5 for a cap-3 campaign) must not switch it off.  A real cap of 3 is
        # exactly where it earned its place (the forward 97@3 record).
        cap = getattr(objective, "depth_cap", None)
        if cap is None:
            cap = search_cap(objective)
        if cap != 3:
            return f"depth cap is {cap}, not 3"
        n, rows = target_rows(target)
        return root_reason(n, rows, 3)

    def _ensure_model(self, state, rng):
        """The model for the chain's target (built once) and the annealer parameters."""
        n, rows = state.n, list(state.targets)
        prm = AnnealParams(self.cfg)
        model = self._model
        if model is None or model.signature != model_signature(n, rows, prm.cancel_splits):
            model = self._model = Depth3Model(n, rows, prm.cancel_splits)
            self._part = Partition(model)
            pending = self._pending
            self._pending = None
            cur = best = None
            if pending is not None and pending.get("signature") == model.signature:
                cur = _decode_snap(model, pending)
                best = _decode_snap(model, pending.get("best") or {})
            if cur is None:
                self._fresh(rng)
                self._last_key = None       # force a resync from the chain
            else:
                part = self._part
                if best is not None:
                    part.restore(best, rng)
                    self._best, self._best_cost = best, part.cost
                part.restore(cur, rng)
                if best is None:
                    self._best, self._best_cost = cur, part.cost
                self._it = int(pending.get("it", 0))
                self._stage = pending.get("stage", "anneal")
                self._rounds = int(pending.get("rounds", 0))
                self._seed = int(pending.get("seed", 0))
        return model, prm

    def _fresh(self, rng):
        """Start a new seed: a random partition, greedily cleaned up (random splits would
        waste the first cooling period)."""
        part = self._part
        part.restore(None, rng)
        for o in range(len(part.model.T)):
            part.greedy_rechoice(o, rng)
        self._best, self._best_cost = part.snapshot(), part.cost
        self._stage, self._rounds = "anneal", 0
        self._seed += 1

    def propose(self, ctx) -> Proposal | None:
        state = ctx.state
        # Same rule as applicable(): the real cap (the state's cap when there is no
        # objective) must be 3; the chain may search above it (soft slack), never below.
        cap = getattr(ctx.objective, "depth_cap", None)
        if cap is None:
            cap = state.cap
        if (cap != 3 or (state.cap is not None and state.cap < 3)
                or root_reason(state.n, state.targets, 3) is not None):
            return None
        rng = ctx.rng
        model, prm = self._ensure_model(state, rng)
        part = self._part
        budget = ctx.budget if ctx.budget is not None else Budget(None)
        size = state.count()
        synced = False
        key = state.key()
        if key != self._last_key and state.ok():
            self._last_key = key
            if size < self._best_cost:
                gates, _ = state.gates()
                snap = model.decode(gates, state.n)
                if snap is not None:
                    part.restore(snap, rng)
                    self._best, self._best_cost = part.snapshot(), part.cost
                    self._stage, self._rounds = "ils", 0
                    synced = True
        start_cost = self._best_cost
        stage = self._stage
        if stage == "anneal":
            period = self._it // prm.period
            best, best_cost, self._it, work = anneal(part, rng, prm, prm.iterations, budget,
                                                     self._it)
            if best_cost < self._best_cost:
                self._best, self._best_cost = best, best_cost
            if prm.ils_rounds and self._it // prm.period > period:
                part.restore(self._best, rng)
                work += descend(part, rng, budget)
                if part.cost <= self._best_cost:
                    self._best, self._best_cost = part.snapshot(), part.cost
                self._stage, self._rounds = "ils", 0
        else:
            self._best, self._best_cost, done, work = ils(
                part, rng, prm, self._best, self._best_cost,
                min(self.cfg.ils_batch, prm.ils_rounds - self._rounds), budget)
            self._rounds += done
        best, best_cost = self._best, self._best_cost
        if self._stage == "ils" and self._rounds >= prm.ils_rounds:
            if self.cfg.fresh_seeds:
                self._fresh(rng)
            else:
                part.restore(best, rng)
                self._stage = "anneal"
        trace = {"components": ["depth3.anneal", stage],
                 "params": {"iterations": prm.iterations, "ils_rounds": prm.ils_rounds,
                            "ils_batch": self.cfg.ils_batch, "t0": prm.t0, "t1": prm.t1},
                 "stage": stage, "seed": self._seed, "rounds": self._rounds,
                 "start_cost": start_cost, "best_cost": best_cost, "chain_size": size,
                 "synced": synced, "it": self._it}
        journal = None
        if best_cost < size:
            journal, added, removed = apply_values(state, model.values(best))
            trace["added"], trace["removed"] = added, removed
            if journal is not None:
                self._last_key = state.key()
        return Proposal(self.name, journal, trace, work or 1)

    def state(self) -> dict:
        """The seed (current and best partitions, as split masks so they survive a split-list
        change), its stage and counters: a resumed move continues exactly."""
        if self._part is None:
            return dict(self._pending) if self._pending else {}
        model = self._model
        return {"signature": model.signature, "it": self._it, "stage": self._stage,
                "rounds": self._rounds, "seed": self._seed,
                **_encode_snap(model, self._part.snapshot()),
                "best": _encode_snap(model, self._best),
                "chain_key": None if self._last_key is None else sorted(self._last_key)}

    def load_state(self, data: dict) -> None:
        """Restore what ``state()`` returned; applied when the model is next built."""
        self._model = None
        self._part = None
        self._pending = dict(data) if data else None
        self._it = int(data.get("it", 0)) if data else 0
        key = data.get("chain_key") if data else None
        self._last_key = None if key is None else frozenset(key)
