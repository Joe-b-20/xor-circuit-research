"""ValueSet: the incremental triple-indexed state every move edits (the hot kernel).

Role in the method
------------------
Each worker chain holds one ``ValueSet``.  A move edits it speculatively (``remove``, ``add``,
``extract`` + ``retain``, ``peel``) inside a ``journal()``; the engine scores the result
(``ok()``, ``count()``, ``depth()``) and either commits or ``rollback``s the journal.
Nothing is replayed or deep-copied per proposal: the state is valid by construction and only a
new record goes through the independent verifier in ``core.circuit``.

Model
-----
Inputs are the n unit vectors ``1 << i`` (level 0).  The state is a set U = inputs | S of distinct
nonzero masks.  A value v is realizable when v = a ^ b with a, b realizable; its *level* is its
earliest arrival depth.  Levels are a pure function of U and the depth cap (values that cannot
arrive within the cap have no level and are called *stuck*).  Each realized value has one
*witness parent*: of all recipes {a, b} that achieve its level, the one with the smallest operand
(``par[v] = min(a, b)``).  Because the witness is canonical, the whole state -- levels, witnesses,
live DAG, gate count -- is a pure function of (U, cap).  That is what makes every undo exact,
a rebuild from the sorted values identical (checkpoints and replays store only the values) and
random choices replayable regardless of the history of set/dict iteration orders.

The triple index
----------------
For every v in U keep ``tri[v] = {x in U : v ^ x in U}``.  A relation a ^ b ^ c = 0 is
symmetric, so ``tri[v]`` lists both every recipe of v and every value v helps build.  On real
circuits it is very sparse (mean 2.5 triples per value, 545 triples for 540 values on FOX Mu8),
so re-levelling after a removal, greedy extraction and repair unlock tests cost O(degree) per
value instead of O(|U|).  Building it from scratch is one O(|U|^2 / 2) pass; ``add`` costs one
O(|U|) scan, or O(pairs of the new value) with the pair index.

Optional lazy pair-sum index
----------------------------
Over a committed base B, ``p2[m]`` describes the pairs {a, b} of B with a ^ b == m: ``-a`` when
there is one such pair (so the pair is known without a scan), else their count c >= 2.  The
sums with two or more representations (``p2_multi``, ~2% of the keys on FOX Mu8) also keep
their pairs (``p2_mpairs``) and the adjacency ``p2_adj[x] = {y : x ^ y in p2_multi}``.  A
complete single-value repair query visits only ``p2_adj`` of each stuck value and decides each
candidate from its own pairs (``_repairs_by_index``); ``add`` takes the triple partners of a new
value from its pairs (``_p2_partners``).  Against the earlier pair *counter*, which counted every
pair touching an unrealized value per query, the index made fixed-seed walk runs 1.2-2.0x faster
with identical trajectories (FOX Mu8 at cap 10: 2.0x; 2026-10-29 profiling).  The index is lazy:
edits only record which values left or joined U; queries correct for those pending changes
exactly, and ``p2_sync()`` folds them in when the next outermost journal opens, i.e. once they
are committed (eager maintenance made remove+restore 11x slower on FOX Mu8, and syncing inside a
proposal paid twice for every speculative add that was rolled back).  Enable it for walk style
repair only, and only while |U| stays below about 1,200 values (memory grows as |U|^2).

Speed notes (CPython 3.12, measured with tests/bench_core.py):
hot per-value loops bind attributes to locals and use plain for-loops.  Passes over a whole
collection (U, a sum list, the level keys) use C-level set algebra, comprehensions, ``filter``/
``map`` and ``collections._count_elements`` instead (``trim``, ``key``, ``values``, ``p2_sync``:
1.3-8x per call in the 2026-10-29 profiling).  Level queues are bucket lists, not heaps, because
levels are small ints.
"""
from __future__ import annotations

from collections import deque
from itertools import compress, filterfalse, repeat
from operator import not_

_consume = deque(maxlen=0).extend      # run an iterator to exhaustion at C speed

try:                                   # the C helper behind Counter.update(iterable)
    from collections import _count_elements
except ImportError:                    # pragma: no cover - other implementations
    def _count_elements(mapping, iterable):
        get = mapping.get
        for elem in iterable:
            mapping[elem] = get(elem, 0) + 1

INF = 1 << 30          # "no level": larger than any reachable depth

# A repair query folds the index's pending changes in itself (p2_sync) only above this many;
# below it, it corrects for them exactly (O(pending * |U|) probes).  A speed guard, not a search
# parameter: results are identical either way.  Committed changes are synced when the next
# outermost journal opens, so inside a move only its own speculative edits are pending.
_P2_PENDING_MAX = 64

# Journal entry kinds (first element of each log tuple).
_ADD, _REMOVE = 0, 1


# --------------------------------------------------------------------------------------------
# One-shot primitive (no index): exact earliest arrival for an arbitrary bank
# --------------------------------------------------------------------------------------------
def earliest_scan(values, n, cap=None, parents=False):
    """Exact earliest-arrival levels of an arbitrary bank of masks over n unit-vector inputs.

    A level BFS (like the old ``relax``/``_earliest``) with two exact refinements: a value is at
    level 1 iff its popcount is 2, and a value of weight w cannot arrive before ceil(log2 w), so
    it only joins the active list at that level.  Stops at ``cap``.  Use it for one-shot
    questions about a bank; use a ``ValueSet`` for a state that is edited repeatedly.

    Returns ``(level, parent, unresolved)``: ``level`` maps every realized mask (inputs
    included) to its level, ``parent`` maps each realized non-input v to one operand a of an
    earliest recipe (a, v ^ a) when ``parents`` is true (else None; not canonical), and
    ``unresolved`` lists the bank values with no level within the cap.  Zero is ignored; a
    value with bits outside the n inputs (or a negative one) is never realizable and is listed
    as unresolved (the popcount rule alone would have put e.g. ``1 | 1 << n`` at level 1).
    """
    level = {1 << i: 0 for i in range(n)}
    resolved = set(level)
    par = {} if parents else None
    outside = ~((1 << n) - 1)
    foreign = []
    waiting = {}
    frontier = []
    for v in set(values):
        if v in resolved or v == 0:
            continue
        if v & outside:
            foreign.append(v)
            continue
        w = v.bit_count()
        if w == 2:
            frontier.append(v)
        else:
            waiting.setdefault((w - 1).bit_length(), []).append(v)
    if cap is not None and cap < 1:
        return level, par, frontier + [v for vs in waiting.values() for v in vs] + foreign
    for v in frontier:
        level[v] = 1
        if parents:
            par[v] = v & -v
    resolved.update(frontier)
    active = []
    d = 2
    lim = INF if cap is None else cap
    while frontier and d <= lim and (active or waiting):
        w = waiting.pop(d, None)
        if w:
            active.extend(w)
        newly = []
        still = []
        for v in active:
            for a in frontier:          # some operand must be on the previous level
                if v ^ a in resolved:
                    newly.append(v)
                    if parents:
                        par[v] = a
                    break
            else:
                still.append(v)
        for v in newly:
            level[v] = d
        resolved.update(newly)
        frontier = newly
        active = still
        d += 1
    unresolved = active + [v for vs in waiting.values() for v in vs]
    unresolved.extend(foreign)
    return level, par, unresolved


# --------------------------------------------------------------------------------------------
# Undo records and journals
# --------------------------------------------------------------------------------------------
class Undo:
    """What one ``remove`` changed; ``ValueSet.restore(undo)`` is its exact inverse.

    ``removed``  tuple of the values taken out of U
    ``tri``      their triple-index partner sets (re-inserted on restore)
    ``old``      {v: (level, parent)} before the removal, for removed and re-levelled values
    ``stuck``    values left in U that became unrealizable (pre-existing stuck values excluded)
    """
    __slots__ = ('removed', 'tri', 'old', 'stuck')

    def __init__(self, removed, tri, old, stuck):
        self.removed = removed
        self.tri = tri
        self.old = old
        self.stuck = stuck


class Journal:
    """A recorded sequence of edits that ``ValueSet.rollback`` can undo exactly.

    Obtain one with ``state.journal()``.  Every ``add``, ``remove``, ``trim``, ``peel`` and
    ``retain`` made while it is open is recorded.  Close it with ``state.commit(j)`` (keep the
    edits) or ``state.rollback(j)`` (undo them).  Journals nest: an inner journal can be rolled
    back alone; committing it leaves its edits in the enclosing journal.
    """
    __slots__ = ('state', 'mark', 'open')

    def __init__(self, state, mark):
        self.state = state
        self.mark = mark          # index into the state's log where this journal starts
        self.open = True

    def changes(self):
        """Net ``(added, removed)`` value lists (sorted) relative to the state at the mark.

        Values added and then removed again (or the reverse) cancel out.  Valid while open.
        """
        if not self.open:
            raise ValueError('journal is closed')
        added = set()
        removed = set()
        for entry in self.state._log[self.mark:]:
            if entry[0] == _ADD:
                w = entry[1]
                if w in removed:
                    removed.discard(w)
                else:
                    added.add(w)
            elif entry[0] == _REMOVE:
                for v in entry[1].removed:
                    if v in added:
                        added.discard(v)
                    else:
                        removed.add(v)
        return sorted(added), sorted(removed)


# --------------------------------------------------------------------------------------------
# Incremental state
# --------------------------------------------------------------------------------------------
class ValueSet:
    """Value set U = inputs | targets | values with triple index, exact earliest levels,
    canonical witness parents, witness children and an optional lazy pair-sum index.

    ``targets`` is the target row list in output order; repeated rows, zero rows (constant
    outputs) and unit-vector rows (free outputs, wired straight from an input) are all allowed.
    Every nonzero non-input target is always put into U.  Inputs are never removed.

    Public attributes (read-only for callers):
      ``n``, ``inputs`` (tuple), ``iset`` (frozenset), ``rows`` (all target rows, output order),
      ``targets`` (distinct nonzero rows), ``tset`` (frozenset of them), ``cap``,
      ``tri``, ``level``, ``par``, ``kids`` (see invariants), ``p2`` (index or None),
      ``p2_multi`` (its keys with count >= 2), ``p2_mpairs``, ``p2_adj``, ``p2_removed`` /
      ``p2_added`` (pending changes).

    Invariants (``check()`` recomputes them):
      tri[v]  = {x in U : v ^ x in U}                      for v in U
      level[v] = exact earliest arrival <= cap, absent when v is stuck
      par[v]  = min(a, b) over the recipes {a, b} achieving level[v] (canonical witness)
      kids[x] = {v : x in (par[v], v ^ par[v])}
      p2 indexes pair sums of B = U - p2_added + p2_removed: p2[m] = -a for one pair
        {a, a ^ m}, else the pair count c >= 2; p2_multi = {m : c >= 2}, p2_mpairs[m] =
        {min of each pair} and p2_adj[x] = {y in B : x ^ y in p2_multi} for those
    """
    __slots__ = ('n', 'inputs', 'iset', 'rows', 'targets', 'tset', 'cap',
                 'tri', 'level', 'par', 'kids', 'p2', 'p2_multi', 'p2_removed', 'p2_added',
                 'p2_adj', 'p2_mpairs',
                 '_log', '_open')

    # ------------------------------------------------------------------------- build
    def __init__(self, n, targets, values=(), cap=None, pairsums=False):
        if type(n) is not int or n <= 0:
            raise ValueError('n must be a positive int')
        if cap is not None and (type(cap) is not int or cap < 0):
            raise ValueError('cap must be a nonnegative int or None')
        full = (1 << n) - 1
        rows = tuple(int(t) for t in targets)
        for t in rows:
            if t < 0 or t > full:
                raise ValueError('target row %d outside %d inputs' % (t, n))
        self.n = n
        self.inputs = tuple(1 << i for i in range(n))
        self.iset = frozenset(self.inputs)
        self.rows = rows
        self.targets = tuple(dict.fromkeys(t for t in rows if t))
        self.tset = frozenset(self.targets)
        self.cap = cap
        self._log = None
        self._open = []
        iset = self.iset
        extra = set()
        for v in values:
            v = int(v)
            if v and v not in iset:
                if v < 0 or v > full:
                    raise ValueError('value %d outside %d inputs' % (v, n))
                extra.add(v)
        extra.update(t for t in self.targets if t not in iset)
        allv = list(self.inputs) + sorted(extra)
        self.tri = self._build_index(allv)
        self.level = dict.fromkeys(self.inputs, 0)
        self.par = {}
        self.kids = {v: set() for v in allv}
        self.disable_pairsums()
        if pairsums:
            self.enable_pairsums()
        self._resolve(set(allv[n:]))

    @staticmethod
    def _build_index(allv):
        """Triple index of the value list ``allv`` in one O(|U|^2 / 2) pass."""
        uset = set(allv)
        tri = {}
        # Pass 1 records, for every pair a before b in list order with a ^ b in U, b under a
        # (a C-level set comprehension per a).  Pass 2 makes each triple {a, b, a ^ b}
        # symmetric over its three members.
        for i, a in enumerate(allv):
            tri[a] = {b for b in allv[i + 1:] if a ^ b in uset}
        for a in allv:
            ta = tri[a]
            if not ta:
                continue
            for b in list(ta):
                c = a ^ b
                tb = tri[b]
                tc = tri[c]
                tb.add(a)
                tb.add(c)
                tc.add(a)
                tc.add(b)
                ta.add(c)
        return tri

    # ------------------------------------------------------------------- pair sums
    def enable_pairsums(self):
        """Build the pair-sum index over the current U (O(|U|^2 / 2) time and entries).

        ``p2[m]`` describes the pairs {a, b} of the base with a ^ b == m: for a sum with one
        pair it is ``-a`` (minus one member, so the pair is known without a scan), for a sum
        with c >= 2 pairs it is c, and those *multi* sums (``p2_multi``, ~2% of the keys on
        FOX Mu8) also keep ``p2_mpairs[m]`` (the smaller member of each pair) and the
        adjacency ``p2_adj[x]`` = the y with x ^ y in ``p2_multi``.  Repair queries visit only
        ``p2_adj[s]`` per stuck value s instead of every realized value, decide buildability
        from a candidate's own pairs, and ``add`` finds the triple partners of a new value from
        its pairs instead of scanning U (``_repairs_by_index``, ``_p2_partners``).
        """
        p2 = {}
        allv = list(self.tri)
        count = _count_elements
        for i, a in enumerate(allv):
            count(p2, [a ^ b for b in allv[i + 1:]])
        self.p2 = p2
        # Sums with two or more representations: the only ones a repair query can accept
        # (see repair_candidates).  About 2% of the keys on FOX Mu8, so it stays in cache.
        multi = self.p2_multi = {m for m, c in p2.items() if c > 1}
        inm = multi.__contains__
        adj = {v: set() for v in allv}
        mpairs = {}
        for i, a in enumerate(allv):
            rest = allv[i + 1:]
            ms = [a ^ b for b in rest]
            p2.update(zip(filterfalse(inm, ms), repeat(-a)))     # single pairs: -member
            aa = adj[a]
            for b in [b for b, m in zip(rest, ms) if m in multi]:
                aa.add(b)
                adj[b].add(a)
                m = a ^ b
                mp = mpairs.get(m)
                if mp is None:
                    mp = mpairs[m] = set()
                mp.add(a if a < b else b)
        self.p2_adj = adj
        self.p2_mpairs = mpairs
        self.p2_removed = set()
        self.p2_added = set()

    def disable_pairsums(self):
        """Drop the pair index (frees its memory)."""
        self.p2 = None
        self.p2_multi = set()
        self.p2_removed = set()
        self.p2_added = set()
        self.p2_adj = {}
        self.p2_mpairs = {}

    def _p2_partners(self, w):
        """``{x in U : x ^ w in U}`` for w not in U, from the pair index instead of a scan.

        Pairs of the base B summing to w come from ``p2`` / ``p2_mpairs`` (minus those with
        a member removed since the base); pairs with a member added since the base are found
        from ``p2_added``.  Together that is every pair of U = B - removed + added.
        """
        tri = self.tri
        out = set()
        c = self.p2.get(w)
        if c is not None:
            removed = self.p2_removed
            if c < 0:
                x = -c
                y = x ^ w
                if not removed or (x not in removed and y not in removed):
                    out.add(x)
                    out.add(y)
            else:
                for x in self.p2_mpairs[w]:
                    y = x ^ w
                    if not removed or (x not in removed and y not in removed):
                        out.add(x)
                        out.add(y)
        for a in self.p2_added:
            y = a ^ w
            if y in tri:
                out.add(a)
                out.add(y)
        return out

    def _p2_track(self, v, added):
        """Lazy index bookkeeping: note that v joined (added) or left U since the base."""
        if added:
            if v in self.p2_removed:
                self.p2_removed.discard(v)
            else:
                self.p2_added.add(v)
        elif v in self.p2_added:
            self.p2_added.discard(v)
        else:
            self.p2_removed.add(v)

    def p2_sync(self):
        """Fold the pending membership changes into the index: O(changes * |U|).

        Called automatically when the outermost journal opens (and by ``repair_candidates``
        when more than ``_P2_PENDING_MAX`` changes are pending); callers rarely need it.
        """
        p2 = self.p2
        if p2 is None or not (self.p2_removed or self.p2_added):
            return
        base = set(self.tri)
        base.difference_update(self.p2_added)
        base.update(self.p2_removed)
        multi = self.p2_multi
        inm = multi.__contains__
        inp = p2.__contains__
        pop = p2.pop
        adj = self.p2_adj
        mpairs = self.p2_mpairs
        # The sums r ^ x (x in base) are distinct for one r, so each is updated once.  Mostly
        # C-level: sums with one representation (not in multi) are deleted by a map over
        # p2.pop; only the few multi-represented ones are handled in Python.
        for r in self.p2_removed:
            base.discard(r)
            ms = [r ^ x for x in base]
            twos = list(filter(inm, ms))
            _consume(map(pop, filterfalse(inm, ms)))     # single pair -> none
            for m in twos:
                c = p2[m] - 1
                x = r ^ m
                adj[x].discard(r)
                mp = mpairs[m]
                mp.discard(r if r < x else x)
                if c == 1:                               # m keeps one pair: no longer multi
                    multi.discard(m)
                    y = mp.pop()
                    del mpairs[m]
                    z = y ^ m
                    adj[y].discard(z)
                    adj[z].discard(y)
                    p2[m] = -y
                else:
                    p2[m] = c
            del adj[r]
        for a in self.p2_added:
            ms = [a ^ x for x in base]
            present = list(filter(inp, ms))              # these reach count >= 2
            p2.update(zip(filterfalse(inp, ms), repeat(-a)))     # new single pairs
            aa = adj[a] = set()
            for m in present:
                x = a ^ m
                c = p2[m]
                if c > 0:
                    p2[m] = c + 1
                    mpairs[m].add(a if a < x else x)
                else:                                    # second representation of m
                    p2[m] = 2
                    multi.add(m)
                    y = -c
                    z = y ^ m
                    mpairs[m] = {y if y < z else z, a if a < x else x}
                    adj[y].add(z)
                    adj[z].add(y)
                aa.add(x)
                adj[x].add(a)
            base.add(a)
        self.p2_removed = set()
        self.p2_added = set()

    # ------------------------------------------------------------------- levelling
    def _resolve(self, pend):
        """Exact levels and canonical witnesses for the unlevelled values ``pend``; every other
        level is final.  Returns the subset of ``pend`` left stuck within the cap.

        Knuth/Dijkstra over the AND-OR triple graph with a bucket queue (levels are small
        ints): a tentative level from recipes whose operands are already final, then values
        settle in level order and offer recipes to their pend neighbours.  Ties keep the
        recipe with the smaller operand so the witness is canonical.
        """
        level = self.level
        tri = self.tri
        par = self.par
        kids = self.kids
        lim = INF if self.cap is None else self.cap
        tent = {}           # v -> best tentative level
        tpar = {}           # v -> smaller operand of that recipe
        buckets = {}
        for v in pend:
            best = INF
            bp = 0
            for x in tri[v]:
                y = v ^ x
                if x > y:                   # visit each unordered recipe once
                    continue
                lx = level.get(x)
                if lx is None:
                    continue
                ly = level.get(y)
                if ly is None:
                    continue
                m = lx if lx > ly else ly
                if m < best or (m == best and x < bp):
                    best = m
                    bp = x
            if bp and best < lim:
                best += 1
                tent[v] = best
                tpar[v] = bp
                b = buckets.get(best)
                if b is None:
                    buckets[best] = [v]
                else:
                    b.append(v)
        if not buckets:
            return set(pend)
        d = min(buckets)
        while buckets:
            vs = buckets.pop(d, None)
            if vs is not None:
                for v in vs:
                    if v in level or tent[v] != d:
                        continue            # stale entry: settled earlier or improved since
                    level[v] = d
                    a = tpar[v]
                    par[v] = a
                    kids[a].add(v)
                    kids[v ^ a].add(v)
                    if d >= lim:
                        continue            # nothing it builds fits under the cap
                    for x in tri[v]:
                        y = v ^ x
                        if y not in pend or y in level:
                            continue
                        lx = level.get(x)
                        if lx is None:
                            continue
                        m = 1 + (d if d > lx else lx)
                        if m > lim:
                            continue
                        k = x if x < v else v
                        t = tent.get(y)
                        if t is None or m < t:
                            tent[y] = m
                            tpar[y] = k
                            b = buckets.get(m)
                            if b is None:
                                buckets[m] = [y]
                            else:
                                b.append(y)
                        elif m == t and k < tpar[y]:
                            tpar[y] = k
            d += 1
        return {v for v in pend if v not in level}

    def _lower(self, seeds, changed):
        """Propagate level decreases (and better tied witnesses) from ``seeds``, values whose
        level just dropped or that just became realizable.  Records the previous
        (level, parent) of every value it touches in ``changed`` (first change only)."""
        level = self.level
        tri = self.tri
        par = self.par
        kids = self.kids
        lim = INF if self.cap is None else self.cap
        buckets = {}
        for s in seeds:
            buckets.setdefault(level[s], []).append(s)
        d = min(buckets)
        while buckets:
            us = buckets.pop(d, None)
            if us is not None and d < lim:
                for u in us:
                    if level.get(u) != d:
                        continue            # stale: lowered again after being queued
                    m = d + 1
                    for x in tri[u]:
                        lx = level.get(x)
                        if lx is None:
                            continue
                        y = u ^ x
                        mm = m if lx < d else lx + 1
                        ly = level.get(y)
                        # Fast path first: most neighbours are already shallower.  Inputs
                        # (level 0 < mm) are skipped here too.
                        if ly is not None and ly < mm:
                            continue
                        if mm > lim:
                            continue
                        k = x if x < u else u
                        if ly is None or mm < ly:
                            if y not in changed:
                                changed[y] = (ly, par.get(y))
                            if ly is not None:
                                a = par[y]
                                kids[a].discard(y)
                                kids[y ^ a].discard(y)
                            level[y] = mm
                            par[y] = k
                            kids[k].add(y)
                            kids[y ^ k].add(y)
                            b = buckets.get(mm)
                            if b is None:
                                buckets[mm] = [y]
                            else:
                                b.append(y)
                        elif mm == ly and k < par[y]:
                            # Same level, smaller witness operand: relink only, nothing moves.
                            if y not in changed:
                                changed[y] = (ly, par[y])
                            a = par[y]
                            kids[a].discard(y)
                            kids[y ^ a].discard(y)
                            par[y] = k
                            kids[k].add(y)
                            kids[y ^ k].add(y)
            d += 1

    # ------------------------------------------------------------------- mutations
    def add(self, w, partners=None):
        """Insert value w and update levels; False if w is 0, an input or already in U.

        w's triples come from ``partners`` when given (a superset of the values x with x ^ w in
        U, e.g. the map ``valid_repairs`` fills), else from the pair index (its pairs of w), else
        from one O(|U|) scan.  w may end up stuck if it has no recipe within the cap.
        """
        rec = self._add(w, partners)
        if rec is None:
            return False
        if self._log is not None:
            self._log.append((_ADD, w, rec))
        return True

    def _add(self, w, partners):
        """``add`` without journaling; returns the {value: old (level, parent)} change record
        (w itself excluded) or None if nothing was inserted."""
        tri = self.tri
        if w in tri or w == 0:
            return None
        if partners is None:
            if self.p2 is not None:
                partners = self._p2_partners(w)     # O(pairs of w), not O(|U|)
            else:
                partners = {x for x in tri if x ^ w in tri}
        else:
            given = partners
            partners = set()
            for x in given:
                if x in tri and x ^ w in tri:
                    partners.add(x)
                    partners.add(x ^ w)
        tri[w] = partners
        # Each new triple {w, x, x ^ w}: x gains partners w and x ^ w (and x ^ w gains w and x
        # when the loop reaches it, since the partner set holds both operands).
        for x in partners:
            tx = tri[x]
            tx.add(w)
            tx.add(x ^ w)
        self.kids[w] = set()
        if self.p2 is not None:
            self._p2_track(w, True)
        changed = {}
        level = self.level
        best = INF
        bp = 0
        for x in partners:
            y = w ^ x
            if x > y:
                continue
            lx = level.get(x)
            if lx is None:
                continue
            ly = level.get(y)
            if ly is None:
                continue
            m = lx if lx > ly else ly
            if m < best or (m == best and x < bp):
                best = m
                bp = x
        if bp and (self.cap is None or best < self.cap):
            level[w] = best + 1
            self.par[w] = bp
            kids = self.kids
            kids[bp].add(w)
            kids[w ^ bp].add(w)
            self._lower((w,), changed)
        return changed

    def _unadd(self, w, changed):
        """Exact inverse of ``_add(w)`` given its change record."""
        # Relinking inlined (a method call per re-levelled value was 5-8% of a remove1 run).
        par = self.par
        kids = self.kids
        level = self.level
        for y, (ly, ay) in changed.items():
            a = par.pop(y, None)
            if a is not None:
                ka = kids.get(a)
                if ka is not None:
                    ka.discard(y)
                kb = kids.get(y ^ a)
                if kb is not None:
                    kb.discard(y)
            if ly is None:
                level.pop(y, None)
            else:
                level[y] = ly
                if ay is not None:
                    par[y] = ay
                    kids[ay].add(y)
                    kids[y ^ ay].add(y)
        a = par.pop(w, None)
        if a is not None:
            ka = kids.get(a)
            if ka is not None:
                ka.discard(w)
            kb = kids.get(w ^ a)
            if kb is not None:
                kb.discard(w)
        level.pop(w, None)
        tri = self.tri
        del self.kids[w]
        for x in tri.pop(w):
            tx = tri[x]
            tx.discard(w)
            tx.discard(x ^ w)
        if self.p2 is not None:
            self._p2_track(w, False)

    def remove(self, values):
        """Remove ``values`` from U (inputs and absent values are ignored).

        Only witness descendants are re-levelled.  Returns an ``Undo``; its ``stuck`` lists
        values still in U that became unrealizable.  Targets may be removed (the state is then
        not ``ok()`` until they are added back).
        """
        u = self._remove(values)
        if self._log is not None:
            self._log.append((_REMOVE, u))
        return u

    def _remove(self, values):
        tri = self.tri
        level = self.level
        par = self.par
        kids = self.kids
        iset = self.iset
        D = tuple(v for v in dict.fromkeys(values) if v in tri and v not in iset)
        Dset = set(D)
        aff = set()
        stack = list(D)
        while stack:
            x = stack.pop()
            for c in kids[x]:
                if c not in aff and c not in Dset:
                    aff.add(c)
                    stack.append(c)
        old = {}
        for v in D:
            old[v] = (level.get(v), par.get(v))
        for v in aff:
            old[v] = (level[v], par[v])
        for v in aff:
            a = par.pop(v)
            kids[a].discard(v)
            kids[v ^ a].discard(v)
            del level[v]
        saved = {}
        track = self.p2 is not None
        for v in D:
            a = par.pop(v, None)
            if a is not None:
                ka = kids.get(a)
                if ka is not None:
                    ka.discard(v)
                kb = kids.get(v ^ a)
                if kb is not None:
                    kb.discard(v)
            level.pop(v, None)
        for v in D:
            tv = tri.pop(v)
            saved[v] = tv
            for x in tv:
                tx = tri.get(x)
                if tx is not None:
                    tx.discard(v)
                    tx.discard(x ^ v)
            del kids[v]
            if track:
                self._p2_track(v, False)
        stuck = self._resolve(aff) if aff else set()
        return Undo(D, saved, old, stuck)

    def restore(self, undo):
        """Exact inverse of the ``remove`` that returned ``undo``.

        Nothing else may have changed since that ``remove``.  Inside a journal it cancels the
        journal's most recent entry, which must be that removal.
        """
        log = self._log
        if log is not None:
            if not log or log[-1][0] != _REMOVE or log[-1][1] is not undo:
                raise ValueError('restore() must undo the most recent journaled remove()')
            log.pop()
        self._restore(undo)

    def _restore(self, u):
        tri = self.tri
        kids = self.kids
        for v in u.removed:
            tri[v] = u.tri[v]
            kids[v] = set()
        for v in u.removed:
            for x in u.tri[v]:
                tx = tri[x]
                tx.add(v)
                tx.add(x ^ v)
        if self.p2 is not None:
            for v in u.removed:
                self._p2_track(v, True)
        # Clear current levels of every recorded value first, then relink: a restored witness
        # may point at another value restored in the same pass.  (Relinking inlined, as in
        # _unadd.)
        par = self.par
        level = self.level
        old = u.old
        for v in old:
            a = par.pop(v, None)
            if a is not None:
                ka = kids.get(a)
                if ka is not None:
                    ka.discard(v)
                kb = kids.get(v ^ a)
                if kb is not None:
                    kb.discard(v)
            level.pop(v, None)
        for v, (lv, a) in old.items():
            if lv is not None:
                level[v] = lv
                if a is not None:
                    par[v] = a
                    kids[a].add(v)
                    kids[v ^ a].add(v)

    def retain(self, keep):
        """Remove every non-input, non-target value not in ``keep``; returns the ``Undo``."""
        keep = keep if isinstance(keep, (set, frozenset, dict)) else set(keep)
        iset = self.iset
        tset = self.tset
        return self.remove([v for v in self.tri
                            if v not in keep and v not in iset and v not in tset])

    def trim(self):
        """Drop stuck non-targets and, cascading, every non-target that no witness uses.

        Exact and cheap: such values have no witness children, so their removal re-levels
        nothing.  Done as one ``remove`` (one journal entry).
        """
        tset = self.tset
        iset = self.iset
        kids = self.kids
        par = self.par
        level = self.level
        # Set algebra and itertools instead of a Python loop over U (5-8x faster at |U| 600):
        # stuck non-targets (never anyone's witness operand), then the realized helpers with
        # no witness child (kids has exactly the keys of tri).  The cascade below reaches the
        # same fixpoint whatever the order.
        dead = self.tri.keys() - level.keys()
        if dead:
            dead -= tset
        stack = set(compress(kids, map(not_, kids.values())))
        stack -= iset
        stack -= tset
        stack -= dead
        stack = list(stack)
        while stack:
            v = stack.pop()
            if v in dead:
                continue
            dead.add(v)
            a = par[v]
            for p in (a, v ^ a):
                if p not in iset and p not in tset and p not in dead and kids[p] <= dead:
                    stack.append(p)
        if dead:
            self.remove(dead)

    # --------------------------------------------------------------------- journal
    def journal(self):
        """Start recording edits; returns a ``Journal`` for ``commit`` or ``rollback``.

        Opening the outermost journal (a move starting a proposal) first folds the index's
        pending changes -- by then they are committed edits -- into the pair-sum index, so the
        repair queries inside the proposal only correct for its own speculative edits.  A
        speculative add that is rolled back before any sync costs the index nothing.
        """
        if self._log is None:
            if self.p2 is not None and (self.p2_added or self.p2_removed):
                self.p2_sync()
            self._log = []
        j = Journal(self, len(self._log))
        self._open.append(j)
        return j

    def _close(self, j):
        if not j.open or j.state is not self:
            raise ValueError('journal is not open on this state')
        while self._open:
            top = self._open.pop()
            top.open = False
            if top is j:
                break
        if not self._open:
            self._log = None

    def rollback(self, j):
        """Undo every edit since ``j`` started (and close ``j`` and journals opened after it)."""
        if not j.open or j.state is not self:
            raise ValueError('journal is not open on this state')
        log = self._log
        while len(log) > j.mark:
            entry = log.pop()
            kind = entry[0]
            if kind == _ADD:
                self._unadd(entry[1], entry[2])
            else:
                self._restore(entry[1])
        self._close(j)

    def commit(self, j):
        """Keep the edits since ``j`` started and close it (and journals opened after it)."""
        self._close(j)

    # --------------------------------------------------------------------- queries
    def ok(self):
        """True when every target row is realized within the cap."""
        level = self.level
        for t in self.targets:
            if t not in level:
                return False
        return True

    def depth(self):
        """Max target level (0 when every row is free); None when a target is stuck."""
        level = self.level
        d = 0
        for t in self.targets:
            lt = level.get(t)
            if lt is None:
                return None
            if lt > d:
                d = lt
        return d

    def values(self):
        """All non-input values of U (stuck ones included), ascending.

        Sorted so that random choices over it replay identically on a rebuilt state.
        """
        out = set(self.tri)          # C-level set algebra: ~1.3x faster than a filtered genexpr
        out -= self.iset
        return sorted(out)

    def key(self):
        """Hashable identity of U (frozenset of non-input values); equal keys, equal states."""
        return frozenset(self.tri).difference(self.iset)    # 2x faster than a genexpr at |U| 600

    def live(self):
        """Set of values reachable from the targets through witness parents (the gates)."""
        par = self.par
        iset = self.iset
        seen = set()
        stack = [t for t in self.targets if t not in iset and t in par]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            a = par[v]
            if a not in iset and a not in seen:
                stack.append(a)
            b = v ^ a
            if b not in iset and b not in seen:
                stack.append(b)
        return seen

    def size(self):
        """Live gate count, ``len(live())``.  After ``trim()`` this equals ``count()``."""
        return len(self.live())

    def count(self):
        """Realized non-input values in U, O(1).  Equals ``size()`` on a trimmed state."""
        return len(self.level) - self.n

    def gates(self):
        """``(gates, outputs)`` of the live witness DAG.

        Gates are ``(a, b)`` signal-index pairs in (level, value) order, smaller operand mask
        first, so the output is a pure function of the state.  ``outputs[i]`` is the signal of
        target row i: an input index for a unit row, -1 for a zero row.  Requires ``ok()``.
        """
        live = self.live()
        level = self.level
        par = self.par
        n = self.n
        idx = {v: i for i, v in enumerate(self.inputs)}
        order = sorted(live)
        order.sort(key=level.__getitem__)
        gates = []
        append = gates.append
        i = n
        for v in order:
            a = par[v]
            append((idx[a], idx[v ^ a]))
            idx[v] = i
            i += 1
        get = idx.get
        outputs = [(-1 if t == 0 else get(t)) for t in self.rows]
        if None in outputs:
            raise ValueError('gates() needs every target realized (ok() is False)')
        return gates, outputs

    # ---------------------------------------------------------------------- repair
    def repair_candidates(self, stuck, forbid=()):
        """Every value w not in U (and not in ``forbid``) that is buildable from realized
        values and builds some ``stuck`` value with a realized partner: the complete
        candidate set (stuck ^ avail) & pairsums(avail) - U, ascending.

        With the pair index it visits only the ``p2_multi`` neighbours of each stuck value and
        the pairs of each candidate (``_repairs_by_index``); without it, each candidate is
        tested by an O(|U|) scan.  ``stuck`` may repeat values or contain realized ones (they
        are ignored).
        """
        if self.p2 is not None and len(self.p2_added) + len(self.p2_removed) > _P2_PENDING_MAX:
            self.p2_sync()
        tri = self.tri
        level = self.level
        # Only genuinely unlevelled members of U can be repaired (repeats and realized values
        # are dropped).
        stuck = [s for s in dict.fromkeys(stuck) if s in tri and s not in level]
        if not stuck:
            return []
        # Every levelled value is in U, so the realized values are the level keys (a C-level
        # copy; 8x cheaper than filtering U).  Their order only affects intermediate sets: the
        # result is sorted below.
        if self.p2 is None:
            out = self._repairs_by_scan(stuck, list(level), forbid)
        else:
            out = self._repairs_by_index(stuck, forbid)
        out.sort()
        return out

    def _repairs_by_index(self, stuck, forbid):
        """``repair_candidates`` with the pair index (unordered list).

        ``stuck``: deduplicated unlevelled members of U.  A candidate is w = s ^ a (s stuck,
        a realized) not in U or ``forbid`` that is *buildable*: some pair of realized values
        sums to w.  For s and a both in the base B, (s, a) is itself a pair of w that is not
        realized, so a buildable w has a second base pair (w in ``p2_multi``, i.e. a in
        ``p2_adj[s]``) or a pair with a member added since the base (a *gain* sum x ^ y,
        x added): only those are generated.  Buildability is then decided per candidate from
        its base pairs (``p2`` / ``p2_mpairs``: realized iff both members are levelled)
        and its pairs through added realized values, O(pairs of w + |added|) instead of
        counting every pair touching an unrealized value.  Same set as ``_repairs_by_scan``.
        """
        tri = self.tri
        level = self.level
        p2 = self.p2
        mpairs = self.p2_mpairs
        adj = self.p2_adj
        added = self.p2_added
        if added:
            new_avail = [x for x in added if x in level]       # realized added values
            base_stuck = [s for s in stuck if s not in added]
            new_stuck = [s for s in stuck if s in added]
        else:
            new_avail = new_stuck = ()
            base_stuck = stuck
        cand = set()
        # s in the base, a realized base value, s ^ a in p2_multi.
        for s in base_stuck:
            cand.update([s ^ a for a in adj[s] if a in level])
        if new_avail:
            # s ^ a a gain sum: s ^ a = x ^ y (x added realized, y realized), i.e. {a, y} is a
            # realized pair summing to t = s ^ x: a base pair from the index, or y added.
            for s in base_stuck:
                for x in new_avail:
                    t = s ^ x
                    c = p2.get(t)
                    if c is None:
                        pass
                    elif c < 0:
                        a = -c
                        y = a ^ t
                        if a in level and y in level:
                            cand.add(s ^ a)
                            cand.add(s ^ y)
                    elif c:
                        for a in mpairs[t]:
                            y = a ^ t
                            if a in level and y in level:
                                cand.add(s ^ a)
                                cand.add(s ^ y)
                    for y in new_avail:
                        a = t ^ y
                        if a in level and a not in added:
                            cand.add(s ^ a)
                # a itself added
                cand.update([s ^ x for x in new_avail])
        if new_stuck:
            cand.update([s ^ a for s in new_stuck for a in level])
        out = []
        append = out.append
        for w in cand:
            if w in tri or w in forbid:
                continue
            c = p2.get(w)
            if c is None:
                pass
            elif c < 0:
                a = -c
                if a in level and (a ^ w) in level:
                    append(w)
                    continue
            elif c:
                for a in mpairs[w]:
                    if a in level and (a ^ w) in level:
                        break
                else:
                    a = None
                if a is not None:
                    append(w)
                    continue
            for x in new_avail:
                if (x ^ w) in level:
                    append(w)
                    break
        return out

    def _repairs_by_scan(self, stuck, avail, forbid):
        """``repair_candidates`` without the index: each candidate s ^ a is tested for a
        realized partner pair by an O(|U|) scan (unordered list)."""
        level = self.level
        X = {s ^ a for s in stuck for a in avail}
        X.difference_update(self.tri)
        if forbid:
            X.difference_update(forbid)
        out = []
        for w in X:
            for a in avail:
                if (w ^ a) in level:
                    out.append(w)
                    break
        return out

    def unlocks(self, w, stuck):
        """Cap-free test: does inserting w (not in U) make every stuck target realizable?

        ``stuck`` must be the set of unlevelled members of U.  Cascades through the triple
        index in O(|stuck| + sum of degrees of unlocked values).  Exact when ``cap`` is None;
        with a cap it is a necessary condition (``valid_repairs`` confirms it exactly).
        """
        level = self.level
        tri = self.tri
        tset = self.tset
        # The answer only asks about the stuck targets: stop the closure (monotone, so its
        # order does not matter) as soon as every one of them is reached.
        need = len(tset.intersection(stuck))
        if not need:
            return True
        got = set()
        stack = []
        for s in stuck:
            if (s ^ w) in level and s not in got:
                got.add(s)
                stack.append(s)
                if s in tset:
                    need -= 1
        while stack and need:
            u = stack.pop()
            y = u ^ w                       # recipe (w, u)
            if y in stuck and y not in got:
                got.add(y)
                stack.append(y)
                if y in tset:
                    need -= 1
            for x in tri[u]:                # recipe (u, x) for y = u ^ x
                y = u ^ x
                if y in stuck and y not in got and (x in level or x in got):
                    got.add(y)
                    stack.append(y)
                    if y in tset:
                        need -= 1
        return not need

    def valid_repairs(self, stuck, forbid=(), partners=None):
        """Every single value w whose insertion makes the state ``ok()`` (ascending).

        ``stuck`` should hold every unlevelled member of U (values that are not are ignored;
        without a cap, a stuck target left out is not checked).  Exact buildability first,
        then ``unlocks`` (the reverse order measured 13x slower: the pair-sum test is the
        selective one), then, only under a cap, an exact trial insertion of each survivor.  If
        a target was removed from U, the only possible single repair is that target itself.

        ``partners`` (optional dict) receives ``{w: triple partners of w}`` for every trial
        insertion: valid while U is unchanged, they let ``add(w, partners[w])`` skip its
        O(|U|) partner scan when the caller then inserts a repair (walk moves do).
        """
        tri = self.tri
        absent = [t for t in self.targets if t not in tri]
        if absent:
            # A target was removed from U: only re-inserting it can repair, if it is the only
            # one missing.  Decide by an exact trial insertion.
            if len(absent) > 1 or absent[0] in forbid:
                return []
            out = absent
        else:
            # unlocks() tests membership and walks tri[] of what it unlocks: keep only
            # unlevelled members of U (repair_candidates ignores anything else too).
            level = self.level
            stuck = {s for s in stuck if s in tri and s not in level}
            unlocks = self.unlocks
            out = [w for w in self.repair_candidates(stuck, forbid) if unlocks(w, stuck)]
        if out and (absent or self.cap is not None):
            exact = []
            for w in out:
                rec = self._add(w, None)
                if partners is not None:
                    partners[w] = tri[w]          # _unadd pops but does not change it
                good = self.ok()
                self._unadd(w, rec)
                if good:
                    exact.append(w)
            out = exact
        return out

    # --------------------------------------------------------------------- extract
    def extract(self, cost, rng, noise=0.0):
        """Greedy top-down rebuild of the targets over U; returns the chosen value set.

        From the deepest target down, each chosen value takes the recipe (both operands
        strictly below its level) with the lowest pull-in cost: 0 for inputs and values already
        chosen, else ``cost.get(v, 1)``.  Ties are broken by a uniform random term; with
        probability ``noise`` a recipe's cost is raised by 1.  Candidate recipes are visited in
        ascending operand order and a value with one recipe draws nothing, so the result is a
        function of (U, cap, cost, RNG state) only.  O(sum of degrees).  None if a target is
        stuck.  ``retain(result)`` then ``trim()`` turns the state into the rebuilt circuit.
        """
        level = self.level
        tri = self.tri
        iset = self.iset
        rnd = rng.random
        chosen = set()
        maxd = 0
        for t in self.targets:
            lt = level.get(t)
            if lt is None:
                return None
            if t not in iset:
                chosen.add(t)
                if lt > maxd:
                    maxd = lt
        buckets = [[] for _ in range(maxd + 1)]
        for t in sorted(chosen):
            buckets[level[t]].append(t)
        cget = cost.get
        for d in range(maxd, 0, -1):
            for S in buckets[d]:
                opts = []
                for a in tri[S]:
                    b = S ^ a
                    if a > b:
                        continue
                    la = level.get(a)
                    if la is None or la >= d:
                        continue
                    lb = level.get(b)
                    if lb is None or lb >= d:
                        continue
                    opts.append(a)
                if not opts:
                    return None             # cannot happen while levels are consistent
                if len(opts) == 1:
                    ba = opts[0]
                else:
                    opts.sort()
                    best = INF
                    ba = 0
                    for a in opts:
                        b = S ^ a
                        c = 0
                        if a not in chosen and a not in iset:
                            c = cget(a, 1)
                        if b not in chosen and b not in iset:
                            c += cget(b, 1)
                        r = rnd()
                        k = c + r * 0.5 + (1.0 if r < noise else 0.0)
                        if k < best:
                            best = k
                            ba = a
                for p in (ba, S ^ ba):
                    if p not in chosen and p not in iset:
                        chosen.add(p)
                        buckets[level[p]].append(p)
        return chosen

    # ------------------------------------------------------------------------ peel
    def peel(self, rng, budget=None):
        """Remove non-target values whose removal leaves every value of U realizable, until no
        single removal works (1-minimal, the old ``engines._peel`` semantics).

        Candidates are visited in a shuffled ascending order (replayable).  ``budget`` is an
        optional ``core.budget.Budget``; one unit is spent per candidate and the peel stops
        early when it runs out.  Returns the number of values removed.

        Most candidates are needed, so each is first screened without touching the state
        (``strands``: a cap-free realizability closure over its witness descendants, exact
        when ``cap`` is None); only the survivors get the trial removal.  The result is
        identical to trying every candidate.
        """
        tset = self.tset
        iset = self.iset
        tri = self.tri
        strands = self.strands
        removed = 0
        progress = True
        while progress:
            progress = False
            order = sorted(v for v in tri if v not in iset and v not in tset)
            rng.shuffle(order)
            for v in order:
                if v not in tri:
                    continue
                if budget is not None:
                    if budget.exhausted():
                        return removed
                    budget.tick(1)
                if strands(v):
                    continue
                u = self.remove((v,))
                if u.stuck:
                    self.restore(u)         # realizable, but not within the cap
                else:
                    removed += 1
                    progress = True
        return removed

    def strands(self, v, among=None):
        """True if removing v would leave some value of U (or of ``among``, e.g. ``tset``)
        unrealizable even without a cap.  No state is changed.

        Only v's witness descendants can lose their level; every other realized value keeps
        it.  A descendant is realizable again iff some recipe avoiding v has both operands kept
        or realizable again: the least fixpoint, grown with a worklist through the triple
        index.  O(sum of degrees of the descendants), against a ``remove`` plus ``restore``
        that also re-levels and relinks them.  Exact without a cap.  With a cap, True still
        means the removal strands something (realizable within a cap implies realizable),
        while False needs the trial removal to confirm.
        """
        kids = self.kids
        tri = self.tri
        level = self.level
        aff = set()
        stack = [v]
        while stack:
            for c in kids[stack.pop()]:
                if c not in aff:
                    aff.add(c)
                    stack.append(c)
        if not aff:
            return False
        if among is not None:
            # Only the members of ``among`` among the descendants matter: none, nothing can
            # strand; otherwise stop the (monotone) closure once all of them are reached.
            need = len(aff.intersection(among))
            if not need:
                return False
        else:
            among = ()
            need = -1                           # never reaches 0: run to the fixpoint
        # bad = the descendants and v: operands that may lose their level (one probe for
        # "x != v and x not in aff").
        bad = set(aff)
        bad.add(v)
        # Seed: descendants with a recipe whose operands both keep their level (each recipe
        # {x, y ^ x} is listed twice in tri[y]; visiting it once is enough).
        got = set()
        for y in aff:
            for x in tri[y]:
                z = y ^ x
                if x < z and x not in bad and z not in bad and x in level and z in level:
                    got.add(y)
                    stack.append(y)
                    if y in among:
                        need -= 1
                    break
        if not need:
            return False
        while stack:
            u = stack.pop()
            for x in tri[u]:                    # recipe (u, x) of y = u ^ x
                y = u ^ x
                if y in aff and y not in got and (x in got or (x not in bad and x in level)):
                    got.add(y)
                    stack.append(y)
                    if y in among:
                        need -= 1
                        if not need:
                            return False
        if need < 0:
            return len(got) < len(aff)
        return True

    # ----------------------------------------------------------------------- debug
    def check(self):
        """Recompute every invariant from scratch and assert equality (tests, debug mode).

        Uses ``assert`` statements, so it checks nothing under ``python -O``.  Folds pending
        index changes in (``p2_sync``) before comparing the index.
        """
        tri = self.tri
        iset = self.iset
        assert all(i in tri for i in iset), 'inputs missing'
        for v, tv in tri.items():
            expect = {x for x in tri if x ^ v in tri and x != v}
            assert tv == expect, ('tri', v)
        lev, _, _ = earliest_scan(self.values(), self.n, self.cap)
        assert {v: lv for v, lv in lev.items() if v in tri} == self.level, 'levels'
        level = self.level
        for v, lv in level.items():
            if v in iset:
                assert lv == 0 and v not in self.par, 'input level'
                continue
            best = None
            for x in tri[v]:
                y = v ^ x
                if x < y and x in level and y in level:
                    k = (max(level[x], level[y]), x)
                    if best is None or k < best:
                        best = k
            assert best is not None and best[0] == lv - 1, ('level/recipe', v)
            assert self.par[v] == best[1], ('witness not canonical', v)
        assert set(self.par) == {v for v in level if v not in iset}, 'parents'
        assert set(self.kids) == set(tri), 'kids keys'
        for x, ks in self.kids.items():
            for v in ks:
                assert x in (self.par[v], v ^ self.par[v]), 'kids'
        for v, a in self.par.items():
            assert v in self.kids[a] and v in self.kids[v ^ a], 'kids missing'
        if self.p2 is not None:
            self.p2_sync()
            allv = list(tri)
            p2 = {}
            for i, a in enumerate(allv):
                for b in allv[i + 1:]:
                    p2[a ^ b] = p2.get(a ^ b, 0) + 1
            assert p2 == {m: (1 if c < 0 else c) for m, c in self.p2.items()}, 'p2'
            assert self.p2_multi == {m for m, c in p2.items() if c > 1}, 'p2_multi'
            adj = {v: set() for v in allv}
            mpairs = {}
            for i, a in enumerate(allv):
                for b in allv[i + 1:]:
                    m = a ^ b
                    if p2[m] > 1:
                        adj[a].add(b)
                        adj[b].add(a)
                        mpairs.setdefault(m, set()).add(min(a, b))
            assert adj == self.p2_adj, 'p2_adj'
            assert mpairs == self.p2_mpairs, 'p2_mpairs'
            for m, c in self.p2.items():
                assert c < 0 or c >= 2, 'p2 encoding'
                if c < 0:
                    assert -c in tri and (-c ^ m) in tri, 'p2 single pair'
        return True
