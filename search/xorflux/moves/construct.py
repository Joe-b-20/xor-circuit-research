"""Root constructors: fresh, randomized, verified starting circuits for restarts.

Role in the method (DESIGN.md section 2): when a chain stalls, the restart controller can start
it again from a *fresh randomized constructor root*. The evidence of earlier versions gives the reason
and the limits:

* fresh naive roots found new basins: 7 of 58 ``c_naive`` roots reached 88 on MixColumns, and
  every from-scratch record (88@6, 88@5, 91@4) came from one;
* the forward 97@3 and the 91@4 recipe started from the depth-3 annealer (``moves/depth3.py``);
* as scheduled *moves*, constructors never improved anything (their output sits 69 to 595 gates
  above the worker best), so here they are root builders only, never moves.

Roots
-----
``naive``    randomized balanced XOR tree per output. Identical sub-sums are shared. Always reaches
             the minimum possible depth, max over rows of ceil(log2 weight).
``paar``     Paar's cancellation-free greedy: repeatedly contract the pair of signals that occurs
             in the most rows. Ties are broken at random, and pair counts are kept incrementally
             in count buckets. Under a depth cap a contraction is applied only in rows whose
             Kraft sum stays within ``2**cap``, so every row can always be finished.
``bp``       Boyar-Peralta greedy over a growing base S: add the pair sum that most reduces the
             summed target distances. Distances use the exact tiers (1: in S, 2: a pair sum,
             3: S plus a pair sum) and then the *upper-bound fallback* (popcount, or one hop over
             S) from ``search/engines/reference/inverse-bp5ub.c``. With exact tiers only, rows
             of weight 11 to 19 (InvMixColumns) never score an improvement, and the clean-room
             version produced zero circuits. Each target also keeps a concrete representation
             over S, so an upper bound is never "forgotten": that alone took InvMixColumns from
             about 230 to about 135 gates. Candidates are sampled plus targeted, the work is
             budgeted, and whatever is left unbuilt is completed with depth-aware trees.
``anneal3``  depth-3 partition annealer, registered from ``moves/depth3.py`` (rows of weight <= 8,
             cap None or >= 3).

Every builder returns recorded recipes. ``emit`` turns them into the earliest-arrival live
circuit (Knuth's algorithm over the recipe AND-OR graph, so a value with several recipes takes
the shallowest one and no cycle can arise). ``verify_gates`` then replays that circuit
independently before it is returned. If a builder cannot meet the cap, ``build_root`` falls back
to ``naive`` and says so in ``info["fallback"]``.

Public API
----------
``build_root(name, target, rng, cap=None, budget=None, cfg=None) -> (values, info)``
``choose_root(rng, cfg=None, target=None, cap=None) -> name``
``ROOTS``: name -> builder ``(n, rows, rng, cap, budget, cfg) -> (triples, info)``
``build_restricted_root(names, target, allowed, rng, cap=None, budget=None, cfg=None)``: a root
whose level-1 set (weight-2 values) lies within ``allowed`` (foundation restarts; ``l1tree``
or a ``ROOTS`` constructor with its forbidden-pair recipes dropped), ``level1(values)``.
Helpers shared with depth3/structural: ``target_rows``, ``needed_rows``, ``bits_of``, ``emit``,
``verify_gates``.
"""
from __future__ import annotations

import heapq

from ..config.schema import Knob, Section
from ..core.budget import Budget
from ..core.target import min_depth

KNOBS = (
    Section("construct.mix", "Restart-root mixture: prior weight of each constructor. "
            "Roots that cannot be used on the target or cap are skipped.", {
                "naive": Knob(1.0, "Weight of the randomized balanced-tree root.", min=0),
                "paar": Knob(0.5, "Weight of the Paar cancellation-free root.", min=0),
                "bp": Knob(0.5, "Weight of the Boyar-Peralta upper-bound-distance root.", min=0),
                "anneal3": Knob(1.0, "Weight of the depth-3 partition annealer root (rows of "
                                "weight <= 8 and cap None or >= 3 only).", min=0),
            }),
    Section("construct.paar", "Paar frequency contraction with random tie-breaks.", {
        "work": Knob(50_000_000, "Work units (pair-count updates) before the remaining rows "
                     "are finished by depth-aware merging.", min=1),
        "cap_tries": Knob(8, "Under a depth cap: most-frequent pairs sampled before taking the "
                          "one legal in the most rows.", min=1),
    }),
    Section("construct.bp", "Boyar-Peralta greedy with upper-bound distance fallback.", {
        "work": Knob(30_000_000, "Work units (distance-scan steps) before the remaining targets "
                     "are completed by depth-aware trees.", min=1),
        "pair_samples": Knob(96, "Random base pairs scored per step (the C reference scores "
                             "every pair; that is too slow in Python).", min=1),
        "recent": Knob(8, "Every pair among this many newest base elements is also scored.",
                       min=0),
        "targeted": Knob(32, "Targeted candidates per step: pair sums finishing distance-3 "
                         "targets (per target) and the most frequent input pairs of the open "
                         "targets' residuals.", min=0),
        "exact_tiers": Knob(3, "Exact distance tiers: 2 = in S or a pair sum; 3 = also S plus a "
                            "pair sum (one O(|S|) scan).", choices=(2, 3)),
        "fallback": Knob(2, "Upper bound beyond the exact tiers: 0 none (exact only, fails on "
                         "dense rows), 1 popcount, 2 min(popcount, 1 + min_s popcount(v^s)).",
                         choices=(0, 1, 2)),
        "norm": Knob("max", "Tie-break on equal distance sums by the squared norm of the "
                     "distance vector: max (Boyar-Peralta), min or none.",
                     choices=("max", "min", "none")),
        "near_p": Knob(0.25, "Probability of choosing uniformly among improving candidates "
                       "with sum <= best + 1 instead of the best (the C reference uses 1/4).",
                       min=0, max=1),
    }),
)


# ------------------------------------------------------------------------------ target helpers
def target_rows(target) -> tuple[int, list[int]]:
    """``(n, rows)`` from a Target-like object, a target dict or an ``(n, rows)`` pair.

    Accepted: ``core.target.Target`` (``n_inputs``/``rows``), a ValueSet (``n``/``rows``), a
    target JSON dict (``input_count``/``rows``) or an ``(n, rows)`` tuple.
    """
    if isinstance(target, tuple) and len(target) == 2:
        n, rows = target
    elif isinstance(target, dict):
        n, rows = target["input_count"], target["rows"]
    else:
        n = getattr(target, "n_inputs", None)
        if n is None:
            n = target.n
        rows = target.rows
    return int(n), [int(r) for r in rows]


def needed_rows(rows) -> list[int]:
    """Distinct rows that need at least one gate (weight >= 2), in first-seen order."""
    return [t for t in dict.fromkeys(rows) if t.bit_count() >= 2]


def bits_of(mask: int) -> list[int]:
    """The unit vectors of ``mask``, lowest first."""
    out = []
    while mask:
        low = mask & -mask
        out.append(low)
        mask ^= low
    return out


# ------------------------------------------------------------------------- emit and verify
def emit(n: int, rows, triples, cap=None):
    """Earliest-arrival live circuit over recorded recipes.

    ``triples`` is an iterable of ``(m, a, b)`` with ``m == a ^ b``; a value may have several
    recipes. Levels are computed with Knuth's generalisation of Dijkstra over the AND-OR graph
    (value <- any recipe, recipe <- both operands). Each level is exact for the recorded recipes
    and the witnesses are acyclic by construction. Returns ``(gates, values, depth)``, where
    ``gates`` are index pairs in level order and ``values`` the live non-input masks in the same
    order. Returns None if a row cannot be reached within ``cap``.
    """
    inputs = [1 << i for i in range(n)]
    level = {x: 0 for x in inputs}
    recipes = []
    uses: dict[int, list[int]] = {}
    for m, a, b in triples:
        if m in level or a == b or not m:
            continue
        rid = len(recipes)
        recipes.append((m, a, b))
        uses.setdefault(a, []).append(rid)
        uses.setdefault(b, []).append(rid)
    missing = [2] * len(recipes)
    witness: dict[int, int] = {}
    heap: list = []
    push = heapq.heappush

    def settle(v, lv):
        for rid in uses.get(v, ()):
            missing[rid] -= 1
            if not missing[rid]:
                m, a, b = recipes[rid]
                if m not in level:
                    la, lb = level[a], level[b]
                    push(heap, (1 + (la if la > lb else lb), m, rid))

    for x in inputs:
        settle(x, 0)
    limit = cap if cap is not None else 1 << 30
    while heap:
        lv, m, rid = heapq.heappop(heap)
        if m in level:
            continue
        if lv > limit:
            break
        level[m] = lv
        witness[m] = rid
        settle(m, lv)
    need = [t for t in dict.fromkeys(rows) if t]
    for t in need:
        if t not in level:
            return None
    live = set()
    stack = [t for t in need if t.bit_count() > 1]
    while stack:
        v = stack.pop()
        if v in live:
            continue
        live.add(v)
        _, a, b = recipes[witness[v]]
        if a.bit_count() > 1 and a not in live:
            stack.append(a)
        if b.bit_count() > 1 and b not in live:
            stack.append(b)
    order = sorted(sorted(live), key=level.__getitem__)    # (level, mask): set-order free
    index = {x: i for i, x in enumerate(inputs)}
    gates = []
    for v in order:
        _, a, b = recipes[witness[v]]
        index[v] = n + len(gates)
        gates.append([index[a], index[b]])
    depth = max((level[t] for t in need), default=0)
    return gates, order, depth


def verify_gates(n: int, rows, gates, cap=None) -> int:
    """Independent replay of an index-pair circuit; return its output depth.

    Raises AssertionError if a gate is malformed or non-topological, if a value is zero or
    duplicated, if a nonzero row is not produced, or if the output depth exceeds ``cap``.  The
    checks are explicit raises, not ``assert`` statements, so ``python -O`` keeps them.
    """
    masks = [1 << i for i in range(n)]
    depths = [0] * n
    seen = set(masks)
    for k, gate in enumerate(gates):
        top = n + k
        try:
            a, b = gate
        except (TypeError, ValueError):
            raise AssertionError(f"bad gate {k}: {gate!r}") from None
        if not (type(a) is int and type(b) is int and 0 <= a < top and 0 <= b < top
                and a != b):
            raise AssertionError(f"bad gate {k}: {(a, b)}")
        m = masks[a] ^ masks[b]
        if not m or m in seen:
            raise AssertionError(f"zero or duplicate value at gate {k}")
        seen.add(m)
        masks.append(m)
        da, db = depths[a], depths[b]
        depths.append(1 + (da if da > db else db))
    where = {m: i for i, m in enumerate(masks)}
    depth = 0
    for t in rows:
        if not t:
            continue
        if t not in where:
            raise AssertionError(f"row {t:#x} not produced")
        if depths[where[t]] > depth:
            depth = depths[where[t]]
    if cap is not None and depth > cap:
        raise AssertionError(f"depth {depth} exceeds cap {cap}")
    return depth


# ---------------------------------------------------------------------------------- naive
def _naive(n, rows, rng, cap, budget, cfg):
    """Randomized balanced XOR tree per output; identical sub-sums are shared.

    Rows are visited in random order and each row's bits are paired in random order, round by
    round. Every round keeps each item's depth at most the round number, so with earliest
    arrival each row reaches depth ceil(log2 weight): the minimum possible.
    """
    order = needed_rows(rows)
    rng.shuffle(order)
    triples = []
    record = triples.append
    shuffle = rng.shuffle
    for t in order:
        items = bits_of(t)
        shuffle(items)
        while len(items) > 1:
            nxt = []
            keep = nxt.append
            for k in range(0, len(items) - 1, 2):
                a = items[k]
                b = items[k + 1]
                record((a ^ b, a, b))
                keep(a ^ b)
            if len(items) & 1:
                keep(items[-1])
            shuffle(nxt)
            items = nxt
    budget.tick(len(triples) + 1)
    return triples, {}


# ----------------------------------------------------------------------------------- paar
_SHIFT = 21                     # pair key = i << _SHIFT | j (signals < 2**21)
_LOW = (1 << _SHIFT) - 1


class _PairBuckets:
    """Pair -> co-occurrence count, with O(1) update and uniform choice among the maximum.

    ``buckets[c]`` lists the pairs with count c; ``pos`` gives each pair's slot, so a pair moves
    between buckets in O(1) (swap with the bucket's last element and pop).
    """
    __slots__ = ("cnt", "pos", "buckets", "top")

    def __init__(self, max_count):
        self.cnt: dict[int, int] = {}
        self.pos: dict[int, int] = {}
        self.buckets: list[list[int]] = [[] for _ in range(max_count + 2)]
        self.top = 0

    def _out(self, key, c):
        bucket = self.buckets[c]
        i = self.pos.pop(key)
        last = bucket.pop()
        if last != key:
            bucket[i] = last
            self.pos[last] = i

    def _in(self, key, c):
        bucket = self.buckets[c]
        self.pos[key] = len(bucket)
        bucket.append(key)
        if c > self.top:
            self.top = c

    def inc(self, key):
        c = self.cnt.get(key, 0)
        if c:
            self._out(key, c)
        self.cnt[key] = c + 1
        self._in(key, c + 1)

    def dec(self, key):
        c = self.cnt[key]
        self._out(key, c)
        if c > 1:
            self.cnt[key] = c - 1
            self._in(key, c - 1)
        else:
            del self.cnt[key]

    def best_count(self):
        """Largest count that still has a pair (0 when every row is finished)."""
        buckets = self.buckets
        while self.top and not buckets[self.top]:
            self.top -= 1
        return self.top


def _pk(i, j):
    return (i << _SHIFT | j) if i < j else (j << _SHIFT | i)


def _paar(n, rows, rng, cap, budget, cfg):
    """Paar's greedy cancellation-free contraction (see the module docstring).

    Each row is a set of signal indices whose masks XOR (disjointly) to the row. The most
    frequent pair is replaced by a new signal in every row where it is legal. Under a cap,
    ``kraft[r] = sum(2**depth)`` over the row's signals must stay <= 2**cap. That is the exact
    condition for finishing the row within the cap, and merging the row's two shallowest
    signals never breaks it.
    """
    knobs = cfg.paar
    need = needed_rows(rows)
    sig = [1 << i for i in range(n)]
    dep = [0] * n
    index = {m: i for i, m in enumerate(sig)}
    occ: list[set] = [set() for _ in range(n)]
    R = []
    for r, t in enumerate(need):
        row = {i for i in range(n) if t >> i & 1}
        R.append(row)
        for i in row:
            occ[i].add(r)
    pb = _PairBuckets(len(need))
    for row in R:
        idx = sorted(row)
        for x in range(len(idx)):
            for y in range(x + 1, len(idx)):
                pb.inc(idx[x] << _SHIFT | idx[y])
    budget.tick(len(pb.cnt) + 1)
    limit = (1 << cap) if cap is not None else None
    kraft = [len(row) for row in R]
    triples = []
    inc, dec = pb.inc, pb.dec
    stats = {"contractions": 0, "fallback_merges": 0, "budget_exhausted": False}

    def contract(a, b, where):
        """Replace signals a, b by their XOR in the rows ``where``."""
        ma, mb = sig[a], sig[b]
        m = ma ^ mb
        d = 1 + (dep[a] if dep[a] > dep[b] else dep[b])
        z = index.get(m)
        if z is None:
            z = len(sig)
            sig.append(m)
            dep.append(d)
            occ.append(set())
            index[m] = z
        elif d < dep[z]:
            # A shallower recipe for an existing signal: keep the Kraft sums exact.
            drop = (1 << dep[z]) - (1 << d)
            for r in occ[z]:
                kraft[r] -= drop
            dep[z] = d
        triples.append((m, ma, mb))
        gain = (1 << dep[z]) - (1 << dep[a]) - (1 << dep[b])
        units = 0
        ab = _pk(a, b)
        for r in where:
            row = R[r]
            row.discard(a)
            row.discard(b)
            dec(ab)
            for x in row:
                dec(_pk(a, x))
                dec(_pk(b, x))
                inc(_pk(z, x))
            units += len(row)
            row.add(z)
            occ[a].discard(r)
            occ[b].discard(r)
            occ[z].add(r)
            kraft[r] += gain
        budget.tick(3 * units + 1)

    def legal_rows(key):
        a, b = key >> _SHIFT, key & _LOW
        rows_ab = occ[a] & occ[b]
        if limit is None:
            return a, b, rows_ab, len(rows_ab)
        da, db = dep[a], dep[b]
        m = sig[a] ^ sig[b]
        dz = 1 + (da if da > db else db)
        z = index.get(m)
        if z is not None and dep[z] < dz:
            dz = dep[z]
        gain = (1 << dz) - (1 << da) - (1 << db)
        if gain <= 0:
            return a, b, rows_ab, len(rows_ab)
        ok = {r for r in rows_ab if kraft[r] + gain <= limit}
        return a, b, ok, len(rows_ab)

    def merge_shallowest(r):
        """Always-legal fallback: merge the two shallowest signals of row r."""
        row = sorted(R[r], key=lambda i: (dep[i], rng.random()))
        contract(row[0], row[1], (r,))
        stats["fallback_merges"] += 1

    while True:
        top = pb.best_count()
        if not top:
            break
        if budget.exhausted():
            stats["budget_exhausted"] = True
            break
        bucket = pb.buckets[top]
        choice = None
        tries = knobs.cap_tries if limit is not None else 1
        for _ in range(tries):
            a, b, where, total = legal_rows(bucket[rng.randrange(len(bucket))])
            if where and (choice is None or len(where) > len(choice[2])):
                choice = (a, b, where)
            if len(where) == total:
                break
        if choice is not None:
            contract(*choice)
            stats["contractions"] += 1
        else:
            merge_shallowest(rng.choice([r for r, row in enumerate(R) if len(row) > 1]))
    # Budget stop (or nothing left): finish every row by always-legal merges.
    for r, row in enumerate(R):
        while len(row) > 1:
            merge_shallowest(r)
    return triples, stats


# ------------------------------------------------------------------------------------- bp
def _complete(t, base, dep, cap, triples, rng):
    """Build target t over the base: greedy weight-cutting helpers, then shallowest merges.

    Helpers are taken (heaviest first) while they cut the residual weight by at least 2 and
    keep the parts' Kraft sum within ``2**cap``. The parts (helpers plus residual input bits)
    are then merged two shallowest at a time. Equal parts cancel, so a merge whose result is
    already a part removes both. Every new value is added to ``base``/``dep`` so later
    completions can reuse it. Returns False only if t cannot meet the cap (weight > 2**cap).
    """
    limit = (1 << cap) if cap is not None else None
    if limit is not None and t.bit_count() > limit:
        return False
    helpers = [h for h in base if h.bit_count() > 1]
    rng.shuffle(helpers)
    helpers.sort(key=lambda h: -h.bit_count())
    parts = []
    rest = t
    kraft_helpers = 0
    for h in helpers:
        r2 = rest ^ h
        if r2.bit_count() <= rest.bit_count() - 2:
            if limit is not None and kraft_helpers + (1 << dep[h]) + r2.bit_count() > limit:
                continue
            parts.append(h)
            kraft_helpers += 1 << dep[h]
            rest = r2
    parts.extend(bits_of(rest))
    while len(parts) > 1:
        parts.sort(key=lambda p: (dep[p], rng.random()))
        a = parts.pop(0)
        b = parts.pop(0)
        m = a ^ b
        triples.append((m, a, b))
        d = 1 + (dep[a] if dep[a] > dep[b] else dep[b])
        if m not in dep:
            base.append(m)
            dep[m] = d
        elif d < dep[m]:
            dep[m] = d
        if m in parts:
            parts.remove(m)        # m ^ m = 0: the two copies cancel
        else:
            parts.append(m)
    return True


def _bp(n, rows, rng, cap, budget, cfg):
    """Boyar-Peralta greedy with the upper-bound distance fallback (module docstring).

    Every open target t keeps a *representation* ``rep[t]``: base elements that XOR to t, with
    ``d[t] = len(rep[t])``. That is an upper bound on BP's distance, and 1 exactly when t is in
    the base. One step scores candidate pair sums u by sum_t min(d[t], new_t(u)). Here new_t(u)
    is the smaller of ``dist(t ^ u) + 1`` (exact tiers, then the popcount / one-hop fallback of
    inverse-bp5ub.c) and ``d[t] - 1`` when u is the XOR of two members of ``rep[t]``. The
    second term is the cancellation-free (Paar) step. It keeps a historical bound
    re-derivable, so the greedy never stalls while a target is open. Ties go by the squared
    norm, then at random. A distance query only has to decide whether dist(t ^ u) <= d[t] - 2,
    which keeps the common case to a few set lookups. Candidates: random pairs, pairs of recent
    elements, pair sums that finish distance-2/3 targets, and the most frequent pairs inside
    the representations.
    """
    knobs = cfg.bp
    tiers, fallback, norm_mode = knobs.exact_tiers, knobs.fallback, knobs.norm
    samples, recent, near_p = knobs.pair_samples, knobs.recent, knobs.near_p
    targeted = knobs.targeted
    need = needed_rows(rows)
    S = [1 << i for i in range(n)]
    Sset = set(S)
    dep = {x: 0 for x in S}
    P = {S[i] ^ S[j] for i in range(n) for j in range(i + 1, n)}
    rep = [bits_of(t) for t in need]
    repset = [set(r) for r in rep]
    d = [len(r) for r in rep]
    triples = []
    top_level = cap if cap is not None else 1 << 30
    max_steps = sum(t.bit_count() - 1 for t in need)   # the trivial circuit's size
    stats = {"steps": 0, "completed": 0, "budget_exhausted": False, "stuck": False}
    tset = set(need)
    INF = 1 << 30

    def dist(v, bound):
        """Bounded distance of v from S: min(value, bound + 1); see inverse-bp5ub.c."""
        if not v:
            return 0
        if v in Sset:
            return 1
        if bound < 2:
            return bound + 1
        if v in P:
            return 2
        if bound < 3:
            return bound + 1
        lo = 3
        ub = v.bit_count() if fallback else INF
        if tiers >= 3:
            lo = 4
            if fallback == 2:
                for s in S:
                    x = v ^ s
                    if x in P:
                        return 3
                    c = x.bit_count() + 1
                    if c < ub:
                        ub = c
            else:
                for s in S:
                    if (v ^ s) in P:
                        return 3
        elif fallback == 2:
            for s in S:
                c = (v ^ s).bit_count() + 1
                if c < ub:
                    ub = c
        if ub < lo:
            ub = lo
        return ub if ub <= bound else bound + 1

    def parents_of(u):
        """Shallowest (a, b) in S with a ^ b == u, or None."""
        best = None
        bd = INF
        for a in S:
            b = a ^ u
            if b in Sset:
                da, db = dep[a], dep[b]
                m = da if da > db else db
                if m < bd:
                    bd = m
                    best = (a, b)
        return best

    def witness(v, bound):
        """Base elements XOR-ing to v, as ``dist`` counts them, or None if > bound."""
        if not v:
            return []
        if v in Sset:
            return [v]
        if bound < 2:
            return None
        if v in P:
            return list(parents_of(v))
        if bound < 3:
            return None
        best, best_s = (v.bit_count() if fallback else INF), None
        for s in S:
            x = v ^ s
            if tiers >= 3 and x in P:
                return [s, *parents_of(x)]
            if fallback == 2:
                c = x.bit_count() + 1
                if c < best:
                    best, best_s = c, s
        if best > bound:
            return None
        return bits_of(v) if best_s is None else [best_s, *bits_of(v ^ best_s)]

    def allowed(u, a, b):
        da, db = dep[a], dep[b]
        du = 1 + (da if da > db else db)
        return du <= (top_level if u in tset else top_level - 1)

    def _shrink(k):
        """Replace two members of rep[k] whose XOR is already in S, while any exist (free)."""
        r = rep[k]
        found = True
        while found and len(r) > 1:
            found = False
            for i in range(len(r)):
                ri = r[i]
                for j in range(i + 1, len(r)):
                    u = ri ^ r[j]
                    if u in Sset:
                        rj = r[j]
                        r = [m for m in r if m != ri and m != rj]
                        if u in r:
                            r.remove(u)          # u ^ u = 0: the copies cancel
                        else:
                            r.append(u)
                        found = True
                        break
                if found:
                    break
        if r is not rep[k]:
            rep[k], repset[k], d[k] = r, set(r), len(r)
        return r

    def offer(cands, u, a, b):
        if u not in Sset and u not in cands and allowed(u, a, b):
            cands[u] = (a, b)

    while stats["steps"] < max_steps:
        open_t = [k for k in range(len(need)) if d[k] > 1]
        if not open_t:
            break
        if budget.exhausted():
            stats["budget_exhausted"] = True
            break
        cands = {}
        size = len(S)
        for _ in range(samples):
            i = rng.randrange(size)
            j = rng.randrange(size)
            if i != j:
                offer(cands, S[i] ^ S[j], S[i], S[j])
        tail = S[-recent:] if recent else []
        for i in range(len(tail)):
            for j in range(i + 1, len(tail)):
                offer(cands, tail[i] ^ tail[j], tail[i], tail[j])
        # Targeted candidates. Random samples almost never hit the few pair sums that finish
        # a nearly built target, or the pairs that many representations share.
        pair_freq = {}
        for k in open_t:
            t = need[k]
            dk = d[k]
            if dk == 2:
                ab = parents_of(t)
                if ab is not None:
                    offer(cands, t, *ab)
                continue
            if dk == 3:
                # t = s ^ p with p a pair sum: building p brings t to distance 2.
                found = 0
                for s in S:
                    p = t ^ s
                    if p in P and p not in Sset and p not in cands:
                        ab = parents_of(p)
                        if ab is not None:
                            offer(cands, p, *ab)
                            found += 1
                            if found >= targeted:
                                break
            r = _shrink(k)
            for i in range(len(r)):
                ri = r[i]
                for j in range(i + 1, len(r)):
                    u = ri ^ r[j]
                    pair_freq[u] = pair_freq.get(u, 0) + 1
        if pair_freq and targeted:
            ranked = sorted(pair_freq, key=lambda u: (-pair_freq[u], rng.random()))
            for u in ranked[:targeted]:
                ab = parents_of(u)
                if ab is not None:
                    offer(cands, u, *ab)
        budget.tick(size * (1 + len(open_t)) + len(pair_freq) + len(cands))
        # Score: (sum, norm) over the open targets; only improving candidates count.
        scored = []
        best_sum = INF
        for u in cands:
            total = 0
            sq = 0
            improved = False
            for k in open_t:
                dk = d[k]
                q = dist(need[k] ^ u, dk - 2) + 1
                if q >= dk:
                    rs = repset[k]
                    for x in rep[k]:
                        if (u ^ x) in rs:
                            q = dk - 1
                            break
                if q < dk:
                    dk = q
                    improved = True
                total += dk
                sq += dk * dk
            if improved:
                scored.append((total, sq, u))
                if total < best_sum:
                    best_sum = total
        budget.tick(len(cands) * len(open_t) * (1 + size // 8))
        if not scored:
            stats["stuck"] = True
            break
        if rng.random() < near_p:
            pool = [u for total, _, u in scored if total <= best_sum + 1]
        elif norm_mode == "none":
            pool = [u for total, _, u in scored if total == best_sum]
        else:
            sign = 1 if norm_mode == "max" else -1
            best_sq = max(sign * sq for total, sq, _ in scored if total == best_sum)
            pool = [u for total, sq, u in scored if total == best_sum and sign * sq == best_sq]
        u = pool[rng.randrange(len(pool))]
        a, b = cands[u]
        triples.append((u, a, b))
        da, db = dep[a], dep[b]
        dep[u] = 1 + (da if da > db else db)
        for s in S:
            P.add(u ^ s)
        S.append(u)
        Sset.add(u)
        stats["steps"] += 1
        # Update each representation (u is now in S): the cheaper of a distance witness and
        # the Paar step that replaces two members by u.
        for k in open_t:
            dk = d[k]
            parts = witness(need[k] ^ u, dk - 2)
            if parts is not None and len(parts) + 1 < dk:
                new = [u, *parts]
            else:
                rs = repset[k]
                new = None
                for x in rep[k]:
                    y = u ^ x
                    if y in rs and y != x:
                        new = [m for m in rep[k] if m != x and m != y]
                        new.append(u)
                        break
                if new is None:
                    continue
            # XOR-cancel repeated members so the representation stays a set.
            odd = {}
            for m in new:
                if m in odd:
                    del odd[m]
                else:
                    odd[m] = None
            rep[k] = list(odd)
            repset[k] = set(odd)
            d[k] = len(odd)
        budget.tick(len(open_t) * (1 + len(S) // 8))
    for k, t in enumerate(need):
        if t not in Sset:
            if not _complete(t, S, dep, cap, triples, rng):
                raise ValueError(f"row {t:#x} cannot meet depth cap {cap}")
            Sset.add(t)
            stats["completed"] += 1
    return triples, stats


# ------------------------------------------------------------------------- registry and API
def _anneal3(n, rows, rng, cap, budget, cfg):
    """Depth-3 partition annealer root (implemented in moves/depth3.py)."""
    from .depth3 import build_anneal3_root
    return build_anneal3_root(n, rows, rng, cap, budget, cfg)


def _anneal3_reason(n, rows, cap):
    from .depth3 import root_reason
    return root_reason(n, rows, cap)


ROOTS = {"naive": _naive, "paar": _paar, "bp": _bp, "anneal3": _anneal3}
"""Name -> builder ``(n, rows, rng, cap, budget, cfg) -> (triples, info)``."""

_REASONS = {"anneal3": _anneal3_reason}


def root_reason(name: str, target, cap=None) -> str | None:
    """None when root ``name`` can be built for ``target`` within ``cap``, else why not."""
    n, rows = target_rows(target)
    if name not in ROOTS:
        return f"unknown root {name!r}"
    if cap is not None and min_depth(rows) > cap:
        return f"no circuit within cap {cap} (needs depth {min_depth(rows)})"
    check = _REASONS.get(name)
    return check(n, rows, cap) if check is not None else None


def _construct_view(cfg):
    """The ``construct`` settings view from a View, a Settings object or None (defaults)."""
    if cfg is None:
        from ..config.settings import for_sections
        from . import depth3
        extra = depth3.KNOBS if isinstance(depth3.KNOBS, tuple) else (depth3.KNOBS,)
        cfg = for_sections(*KNOBS, *[s for s in extra if s.path.startswith("construct.")])
    if hasattr(cfg, "view"):
        return cfg.view("construct")
    return cfg


def choose_root(rng, cfg=None, target=None, cap=None) -> str:
    """Pick a root name from the ``construct.mix`` weights.

    With ``target`` given, roots that cannot be built for it within ``cap`` are left out.
    ``naive`` is the answer when every applicable weight is zero.
    """
    view = _construct_view(cfg)
    names, weights = [], []
    for name in ROOTS:
        w = view.mix[name]
        if w > 0 and (target is None or root_reason(name, target, cap) is None):
            names.append(name)
            weights.append(w)
    if not names:
        return "naive"
    return rng.choices(names, weights=weights, k=1)[0]


def build_root(name, target, rng, cap=None, budget=None, cfg=None):
    """Build one verified root circuit with constructor ``name``.

    ``target`` is anything ``target_rows`` accepts. ``rng`` is a ``random.Random`` and its
    state fully determines the root. ``cap`` is the depth cap or None. ``budget`` is an
    optional ``core.budget.Budget``: the constructor runs in a child budget limited by its own
    ``construct.<name>.work`` knob, and the parent is charged the work used. ``cfg`` is the
    ``construct`` settings view (or a Settings, or None for defaults).

    Returns ``(values, info)``. ``values`` is the list of distinct, live, non-input masks in
    level order, ready for ``ValueSet(n, rows, values, cap)``. ``info`` has ``name``,
    ``gates`` (verified index-pair circuit), ``gate_count``, ``depth``, ``work``,
    ``fallback`` (None, or why ``naive`` was used instead) and builder-specific stats.
    Raises ValueError if no circuit exists within ``cap``.
    """
    n, rows = target_rows(target)
    view = _construct_view(cfg)
    if cap is not None and min_depth(rows) > cap:
        raise ValueError(f"no circuit within cap {cap}: rows need depth {min_depth(rows)}")
    reason = root_reason(name, (n, rows), cap)
    used = name
    if reason is not None:
        used = "naive"
    section = view.get(used)
    work = section.get("work") if section is not None else None
    child = budget.child(work) if budget is not None else Budget(work)
    try:
        triples, stats = ROOTS[used](n, rows, rng, cap, child, view)
        result = emit(n, rows, triples, cap)
    except ValueError as exc:      # a builder that cannot meet the cap
        result, stats, reason = None, {}, str(exc)
    if result is None and used != "naive":
        reason = reason or f"{used} did not meet cap {cap}"
        used = "naive"
        triples, stats = _naive(n, rows, rng, cap, child, view)
        result = emit(n, rows, triples, cap)
    if result is None:
        raise ValueError(f"no circuit within cap {cap}")
    gates, values, depth = result
    checked = verify_gates(n, rows, gates, cap)
    if checked != depth:
        raise AssertionError("emit and verify disagree on depth")
    if budget is not None:
        budget.tick(child.used)
    info = {"name": name, "built": used, "gates": gates, "gate_count": len(gates),
            "depth": depth, "work": child.used, "fallback": reason}
    info.update(stats)
    return values, info


# ---------------------------------------------------------------- level-1-restricted roots
# Roots whose level-1 set (weight-2 values) lies inside an allowed set A, for the foundation
# restart (engine/restart.py, ``restart.foundation``).  Evidence: 2026-11-02 foundations
# (~/xs-campaigns/2026-11-02-why/foundations/REPORT.md section 3): with the 89@4 level-1 set held
# fixed, roots built this way and completed by the engine re-found 89@4 in 9 of 13 runs.
L1TREE_TRIES = 200      # random trees per target before the root fails (as in l1root.py)
L1TREE_PAIRS = 4        # most allowed pairs combined in one cancellation representation


def level1(values) -> set[int]:
    """The level-1 set of a value collection: its weight-2 masks (XORs of two inputs)."""
    return {v for v in values if v.bit_count() == 2}


def _l1_valid(m, allowed) -> bool:
    """``m`` may appear in a restricted root: nonzero, not an input, not a forbidden pair."""
    w = m.bit_count()
    return w > 2 or (w == 2 and m in allowed)


def _l1_merge(nodes, allowed, cap, rng):
    """Recipes merging ``nodes`` ``[(level, mask)]`` into their XOR, shallowest first, never
    creating a value ``_l1_valid`` rejects and never deeper than ``cap``; None if stuck."""
    nodes = list(nodes)
    out = []
    while len(nodes) > 1:
        rng.shuffle(nodes)
        nodes.sort(key=lambda x: x[0])
        la, a = nodes.pop(0)
        j = None
        for i, (_, b) in enumerate(nodes):
            if _l1_valid(a ^ b, allowed):
                j = i
                break
        if j is None:
            return None
        lb, b = nodes.pop(j)
        level = (la if la > lb else lb) + 1
        if cap is not None and level > cap:
            return None
        out.append((a ^ b, a, b))
        nodes.append((level, a ^ b))
    return out


def _l1_reps(t, allowed, budget, keep=40):
    """Cheapest representations t = XOR(P) ^ singles with P at most ``L1TREE_PAIRS`` allowed
    pairs (pairs may reach outside t: cancellation), as ``[(cost, P)]``, cheapest first."""
    from itertools import combinations
    al = sorted(allowed)
    out = []
    for r in range(1, min(L1TREE_PAIRS, len(al)) + 1):
        before = len(out)
        for pairs in combinations(al, r):
            x = 0
            for m in pairs:
                x ^= m
            out.append((r + (t ^ x).bit_count(), pairs))
        budget.tick(len(out) - before)
    out.sort(key=lambda z: z[0])
    return out[:keep]


def _l1_target(t, allowed, cap, rng, get_reps):
    """Recipes building target ``t`` as one tree over allowed pairs (level 1) and inputs
    (level 0), or None.  First a random maximal matching of t's bits by allowed pairs inside
    its support; then a cheap representation with cancellation (``get_reps()``, cached by
    the caller)."""
    edges = [m for m in sorted(allowed) if m & t == m]
    rng.shuffle(edges)
    used = 0
    pairs = []
    for m in edges:
        if m & used == 0:
            used |= m
            pairs.append(m)
    for attempt in range(2):
        if attempt == 1:
            reps = get_reps()
            if not reps:
                return None
            low = reps[0][0]
            pairs = list(rng.choice([p for c, p in reps if c <= low + 1]))
        x = 0
        for m in pairs:
            x ^= m
        leaves = [(1, m) for m in pairs] + [(0, b) for b in bits_of(t ^ x)]
        merged = _l1_merge(leaves, allowed, cap, rng)
        if merged is not None:
            return [(m, m & -m, m ^ (m & -m)) for m in pairs] + merged
    return None


def _l1tree(n, rows, rng, cap, budget, allowed):
    """Port of the 2026-11-02 ``l1root.build_root``: each target separately as a tree of depth
    <= cap over allowed pairs and single inputs (``L1TREE_TRIES`` random tries per target).
    Unlike the prototype the cancellation fallback combines at most ``L1TREE_PAIRS`` pairs on
    every try (the prototype went to 6 in the second half; C(26, 6) combinations per target
    was the slow part)."""
    triples = []
    for t in needed_rows(rows):
        cache = []

        def get_reps(t=t, cache=cache):
            if not cache:
                cache.append(_l1_reps(t, allowed, budget))
            return cache[0]
        for _ in range(L1TREE_TRIES):
            got = _l1_target(t, allowed, cap, rng, get_reps)
            budget.tick(1)
            if got is not None:
                triples.extend(got)
                break
            if budget.exhausted():
                raise ValueError("l1tree: work budget spent")
        else:
            raise ValueError(f"l1tree: no restricted tree for row {t:#x}")
    return triples, {}


RESTRICTED_ROOTS = ("l1tree", *ROOTS)
"""Constructors ``build_restricted_root`` accepts: the dedicated ``l1tree`` and every root of
``ROOTS`` run with the restriction (their recipes creating a forbidden pair are dropped; they
complete only when the rest of their recipes still reach every row)."""


def build_restricted_root(names, target, allowed, rng, cap=None, budget=None, cfg=None):
    """A verified root whose level-1 set lies within ``allowed``, from the first constructor
    of ``names`` that can complete under that restriction.

    ``l1tree`` builds for the restriction (see ``_l1tree``); a ``ROOTS`` constructor runs
    unchanged and its recipes that would create a weight-2 value outside ``allowed`` are
    dropped before ``emit``, so it completes only if the rest still reach every row.
    Weight-2 rows are always allowed (every circuit holds them).  Returns ``(values, info)``
    like ``build_root`` (``info["built"]`` names the constructor that completed and
    ``info["tried"]`` lists ``(name, reason)`` for those that did not); raises ValueError when
    none completes.
    """
    n, rows = target_rows(target)
    allowed = frozenset(allowed) | {t for t in rows if t.bit_count() == 2}
    view = _construct_view(cfg)
    if cap is not None and min_depth(rows) > cap:
        raise ValueError(f"no circuit within cap {cap}: rows need depth {min_depth(rows)}")
    parent = budget if budget is not None else Budget(None)
    tried = []
    for name in names:
        if name not in RESTRICTED_ROOTS:
            raise ValueError(f"unknown restricted root {name!r}")
        if name != "l1tree":
            reason = root_reason(name, (n, rows), cap)
            if reason is not None:
                tried.append((name, reason))
                continue
        section = view.get(name) if name != "l1tree" else None
        child = parent.child(section.get("work") if section is not None else None)
        try:
            if name == "l1tree":
                triples, stats = _l1tree(n, rows, rng, cap, child, allowed)
            else:
                triples, stats = ROOTS[name](n, rows, rng, cap, child, view)
                triples = [r for r in triples if _l1_valid(r[0], allowed)]
            result = emit(n, rows, triples, cap)
        except ValueError as exc:
            result, stats = None, {"reason": str(exc)}
        parent.tick(child.used)
        if result is None:
            tried.append((name, stats.get("reason") or "could not complete under the "
                          "restriction"))
            continue
        gates, values, depth = result
        if verify_gates(n, rows, gates, cap) != depth:
            raise AssertionError("emit and verify disagree on depth")
        if not level1(values) <= allowed:
            raise AssertionError("restricted root left the allowed level-1 set")
        info = {"name": name, "built": name, "gates": gates, "gate_count": len(gates),
                "depth": depth, "work": child.used, "tried": tried}
        info.update({k: v for k, v in stats.items() if k != "reason"})
        return values, info
    raise ValueError("no constructor completed under the level-1 restriction: "
                     + "; ".join(f"{a}: {b}" for a, b in tried))
