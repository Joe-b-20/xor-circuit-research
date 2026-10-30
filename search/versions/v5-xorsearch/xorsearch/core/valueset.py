"""ValueSet: the incremental triple-indexed state every move edits (the hot kernel).

Role in the method
------------------
Each worker chain holds one ``ValueSet``.  A move edits it speculatively (``remove``, ``add``,
``extract`` + ``retain``, ``peel``, ``set_cap``) inside a ``journal()``; the engine scores the
result (``ok()``, ``size()``, ``depth()``) and either commits or ``rollback``s the journal.
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
live DAG, gate count, DAG hash -- is a pure function of (U, cap).  That is what makes every undo
exact, snapshots tiny (just the values) and random choices replayable regardless of the history of
set/dict iteration orders.

The triple index
----------------
For every v in U keep ``tri[v] = {x in U : v ^ x in U}``.  A relation a ^ b ^ c = 0 is
symmetric, so ``tri[v]`` lists both every recipe of v and every value v helps build.  On real
circuits it is very sparse (mean 2.5 triples per value, 545 triples for 540 values on FOX Mu8),
so re-levelling after a removal, greedy extraction and repair unlock tests cost O(degree) per
value instead of O(|U|).  Building it from scratch is one O(|U|^2 / 2) pass; ``add`` costs one
O(|U|) scan.

Optional lazy pair-sum counter
------------------------------
``p2[m] = #{ {a, b} subset B : a ^ b == m }`` over a committed base B.  It makes the complete
single-value repair enumeration O((|stuck| + |unrealized|) * |U|).  It is lazy: speculative
edits only record which values left or joined U, and ``p2_sync()`` folds them in when a query
needs it (eager maintenance made remove+restore 11x slower on FOX Mu8).  Enable it for walk
style repair only, and only while |U| stays below about 1,200 values (memory grows as |U|^2).

Speed notes (CPython 3.12, measured in docs/evidence/kernel-performance.md and bench_core.py):
hot loops bind attributes to locals and use plain for-loops; map/isdisjoint idioms measured
slower on 64-bit masks.  Level queues are bucket lists, not heaps, because levels are small ints.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

INF = 1 << 30          # "no level": larger than any reachable depth

# Journal entry kinds (first element of each log tuple).
_ADD, _REMOVE, _CAP = 0, 1, 2


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
    ``unresolved`` lists the bank values with no level within the cap.
    """
    level = {1 << i: 0 for i in range(n)}
    resolved = set(level)
    par = {} if parents else None
    if cap is not None and cap < 1:
        return level, par, [v for v in set(values) if v and v not in resolved]
    waiting = {}
    frontier = []
    for v in set(values):
        if v in resolved or v == 0:
            continue
        w = v.bit_count()
        if w == 2:
            frontier.append(v)
            if parents:
                par[v] = v & -v
        else:
            waiting.setdefault((w - 1).bit_length(), []).append(v)
    for v in frontier:
        level[v] = 1
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

    Obtain one with ``state.journal()``.  Every ``add``, ``remove``, ``trim``, ``peel``,
    ``retain`` and ``set_cap`` made while it is open is recorded.  Close it with
    ``state.commit(j)`` (keep the edits) or ``state.rollback(j)`` (undo them).  Journals nest:
    an inner journal can be rolled back alone; committing it leaves its edits in the enclosing
    journal.  As a context manager it commits on normal exit and rolls back on an exception.
    """
    __slots__ = ('state', 'mark', 'open')

    def __init__(self, state, mark):
        self.state = state
        self.mark = mark          # index into the state's log where this journal starts
        self.open = True

    def __len__(self):
        log = self.state._log
        return len(log) - self.mark if (self.open and log is not None) else 0

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.open:
            if exc_type is None:
                self.state.commit(self)
            else:
                self.state.rollback(self)
        return False


# --------------------------------------------------------------------------------------------
# Incremental state
# --------------------------------------------------------------------------------------------
class ValueSet:
    """Value set U = inputs | targets | values with triple index, exact earliest levels,
    canonical witness parents, witness children and an optional lazy pair-sum counter.

    ``targets`` is the target row list in output order; repeated rows, zero rows (constant
    outputs) and unit-vector rows (free outputs, wired straight from an input) are all allowed.
    Every nonzero non-input target is always put into U.  Inputs are never removed.

    Public attributes (read-only for callers):
      ``n``, ``inputs`` (tuple), ``iset`` (frozenset), ``rows`` (all target rows, output order),
      ``targets`` (distinct nonzero rows), ``tset`` (frozenset of them), ``cap``,
      ``tri``, ``level``, ``par``, ``kids`` (see invariants), ``p2`` (counter or None).

    Invariants (``check()`` recomputes them):
      tri[v]  = {x in U : v ^ x in U}                      for v in U
      level[v] = exact earliest arrival <= cap, absent when v is stuck
      par[v]  = min(a, b) over the recipes {a, b} achieving level[v] (canonical witness)
      kids[x] = {v : x in (par[v], v ^ par[v])}
    """
    __slots__ = ('n', 'inputs', 'iset', 'rows', 'targets', 'tset', 'cap',
                 'tri', 'level', 'par', 'kids', 'p2', 'p2_removed', 'p2_added',
                 '_log', '_open', '_matrix_sha256')

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
        self._matrix_sha256 = None
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
        self.p2 = None
        self.p2_removed = set()
        self.p2_added = set()
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

    @classmethod
    def from_circuit(cls, target, gates, cap=None, pairsums=False):
        """State whose values are the gate outputs of a circuit (dead gates included; call
        ``trim()`` to drop them).

        ``target`` is a ``core.target.Target`` (or anything with ``n_inputs`` and ``rows``) or
        an ``(n_inputs, rows)`` pair.  ``gates`` is a sequence of operand index pairs or a
        ``core.circuit.Circuit``.
        """
        n, rows = _target_parts(target)
        gates = getattr(gates, 'gates', gates)
        masks = [1 << i for i in range(n)]
        for i, pair in enumerate(gates):
            a, b = pair
            if not (0 <= a < n + i and 0 <= b < n + i):
                raise ValueError('gate %d is not topological' % i)
            masks.append(masks[a] ^ masks[b])
        return cls(n, rows, masks[n:], cap=cap, pairsums=pairsums)

    def copy(self):
        """Independent copy (dicts and sets copied, no rebuild).  Journals are not copied."""
        new = type(self).__new__(type(self))
        new.n = self.n
        new.inputs = self.inputs
        new.iset = self.iset
        new.rows = self.rows
        new.targets = self.targets
        new.tset = self.tset
        new.cap = self.cap
        new.tri = {v: set(s) for v, s in self.tri.items()}
        new.level = dict(self.level)
        new.par = dict(self.par)
        new.kids = {v: set(s) for v, s in self.kids.items()}
        new.p2 = None if self.p2 is None else dict(self.p2)
        new.p2_removed = set(self.p2_removed)
        new.p2_added = set(self.p2_added)
        new._log = None
        new._open = []
        new._matrix_sha256 = self._matrix_sha256
        return new

    def snapshot(self):
        """JSON-safe description that ``from_snapshot`` turns back into an identical state.

        Only the values are stored: levels and witnesses are a pure function of (U, cap).
        """
        return {'kind': 'xorsearch.valueset', 'version': 1, 'n': self.n,
                'rows': list(self.rows), 'cap': self.cap, 'values': self.values(),
                'pairsums': self.p2 is not None}

    @classmethod
    def from_snapshot(cls, data):
        """Rebuild the state described by ``snapshot()``."""
        if data.get('kind') != 'xorsearch.valueset':
            raise ValueError('not a ValueSet snapshot')
        vs = cls(data['n'], data['rows'], data['values'], cap=data['cap'],
                 pairsums=bool(data.get('pairsums')))
        # The constructor always inserts the targets; a snapshot taken after a target was
        # removed must not get it back (the state is a pure function of U, so this is exact).
        values = set(data['values'])
        missing = [t for t in vs.targets if t not in vs.iset and t not in values]
        if missing:
            vs._remove(missing)
            if vs.p2 is not None:
                vs.p2_sync()
        return vs

    def to_circuit(self):
        """The live witness DAG as a ``core.circuit.Circuit`` (level order, no dead gates)."""
        from .circuit import Circuit
        gates, outputs = self.gates()
        return Circuit(self.n, gates, outputs)

    # ------------------------------------------------------------------- pair sums
    def enable_pairsums(self):
        """Build the pair-sum counter over the current U (O(|U|^2 / 2) time and entries)."""
        p2 = {}
        get = p2.get
        allv = list(self.tri)
        for i, a in enumerate(allv):
            for b in allv[i + 1:]:
                m = a ^ b
                p2[m] = get(m, 0) + 1
        self.p2 = p2
        self.p2_removed = set()
        self.p2_added = set()

    def disable_pairsums(self):
        """Drop the counter (frees its memory)."""
        self.p2 = None
        self.p2_removed = set()
        self.p2_added = set()

    def _p2_track(self, v, added):
        """Lazy counter bookkeeping: note that v joined (added) or left U since the base."""
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
        """Fold the pending membership changes into the counter: O(changes * |U|).

        Called automatically by ``repair_candidates`` when values were added since the base;
        call it after accepting a move to keep later queries cheap.
        """
        p2 = self.p2
        if p2 is None or not (self.p2_removed or self.p2_added):
            return
        base = set(self.tri)
        base.difference_update(self.p2_added)
        base.update(self.p2_removed)
        get = p2.get
        for r in self.p2_removed:
            base.discard(r)
            for x in base:
                m = r ^ x
                c = p2[m] - 1
                if c:
                    p2[m] = c
                else:
                    del p2[m]
        for a in self.p2_added:
            for x in base:
                m = a ^ x
                p2[m] = get(m, 0) + 1
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

    def _set_state(self, v, old):
        """Put v back to an old (level, parent) pair, keeping ``kids`` consistent."""
        par = self.par
        kids = self.kids
        a = par.pop(v, None)
        if a is not None:
            ka = kids.get(a)
            if ka is not None:
                ka.discard(v)
            kb = kids.get(v ^ a)
            if kb is not None:
                kb.discard(v)
        lv, a = old
        if lv is None:
            self.level.pop(v, None)
        else:
            self.level[v] = lv
            if a is not None:
                par[v] = a
                kids[a].add(v)
                kids[v ^ a].add(v)

    # ------------------------------------------------------------------- mutations
    def add(self, w, partners=None):
        """Insert value w and update levels; False if w is 0, an input or already in U.

        One O(|U|) scan finds w's triples unless ``partners`` (a superset of the values x with
        x ^ w in U) is given.  w may end up stuck if it has no recipe within the cap.
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
        for y, old in changed.items():
            self._set_state(y, old)
        self._set_state(w, (None, None))
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
        # may point at another value restored in the same pass.
        for v in u.old:
            self._set_state(v, (None, None))
        for v, old in u.old.items():
            if old[0] is not None:
                self._set_state(v, old)

    def retain(self, keep):
        """Remove every non-input, non-target value not in ``keep``; returns the ``Undo``."""
        keep = keep if isinstance(keep, (set, frozenset, dict)) else set(keep)
        iset = self.iset
        tset = self.tset
        return self.remove([v for v in self.tri
                            if v not in keep and v not in iset and v not in tset])

    def set_cap(self, cap):
        """Change the depth cap and re-level exactly (journaled)."""
        if cap is not None and (type(cap) is not int or cap < 0):
            raise ValueError('cap must be a nonnegative int or None')
        old_cap = self.cap
        if cap == old_cap:
            return
        level = self.level
        changed = {}
        if cap is not None and (old_cap is None or cap < old_cap):
            # Tighter: levels at or below the new cap are unchanged (earliest arrival does not
            # depend on the cap), everything above it becomes stuck.
            par = self.par
            for v in [v for v, lv in level.items() if lv > cap]:
                changed[v] = (level[v], par[v])
            for v in changed:
                self._set_state(v, (None, None))
            self.cap = cap
        else:
            # Looser: only stuck values can gain a level.
            self.cap = cap
            pend = {v for v in self.tri if v not in level}
            if pend:
                for v in pend - self._resolve(pend):
                    changed[v] = (None, None)
        if self._log is not None:
            self._log.append((_CAP, old_cap, changed))

    def _uncap(self, old_cap, changed):
        for v in changed:
            self._set_state(v, (None, None))
        for v, old in changed.items():
            if old[0] is not None:
                self._set_state(v, old)
        self.cap = old_cap

    def discard_stuck(self):
        """Drop stuck non-target values from U (they are not gates).  Stuck targets stay:
        the state is then not ``ok()`` and must be repaired or rejected."""
        tset = self.tset
        level = self.level
        dead = [v for v in self.tri if v not in level and v not in tset]
        if dead:
            self.remove(dead)

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
        dead = set()
        stack = []
        for v in self.tri:
            if v in iset or v in tset:
                continue
            if v not in level:
                dead.add(v)             # stuck: never anyone's witness operand
            elif not kids[v]:
                stack.append(v)
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
        """Start recording edits; returns a ``Journal`` for ``commit`` or ``rollback``."""
        if self._log is None:
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
            elif kind == _REMOVE:
                self._restore(entry[1])
            else:
                self._uncap(entry[1], entry[2])
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

        Sorted so that random choices over it replay identically from a snapshot.
        """
        iset = self.iset
        return sorted(v for v in self.tri if v not in iset)

    def key(self):
        """Hashable identity of U (frozenset of non-input values); equal keys, equal states."""
        iset = self.iset
        return frozenset(v for v in self.tri if v not in iset)

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

    def stuck(self):
        """Set of values in U without a level."""
        level = self.level
        return {v for v in self.tri if v not in level}

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

    def matrix_sha256(self):
        """Canonical target hash, identical to ``search/target.py`` ``matrix_sha256``."""
        if self._matrix_sha256 is None:
            body = json.dumps({'input_count': self.n, 'rows': list(self.rows)},
                              sort_keys=True, separators=(',', ':')).encode()
            self._matrix_sha256 = hashlib.sha256(body).hexdigest()
        return self._matrix_sha256

    def dag_sha256(self, matrix_sha256=None):
        """DAG hash of the live witness circuit, bit-identical to ``core.circuit.dag_sha256``
        (and ``search/target.py`` ``verify()['dag_sha256']``) of ``to_circuit()``.

        Builds the canonical JSON body directly instead of replaying a circuit.
        """
        if matrix_sha256 is None:
            matrix_sha256 = self.matrix_sha256()
        par = self.par
        triples = []
        for v in self.live():
            a = par[v]
            triples.append((v, a, v ^ a))     # a = par[v] is already the smaller operand
        triples.sort()
        body = ('{"matrix_sha256":"%s","triples":[%s]}' % (
            matrix_sha256, ','.join(['[%d,%d,%d]' % t for t in triples])))
        return hashlib.sha256(body.encode()).hexdigest()

    # ---------------------------------------------------------------------- repair
    def repair_candidates(self, stuck, forbid=()):
        """Every value w not in U (and not in ``forbid``) that is buildable from realized
        values and builds some ``stuck`` value with a realized partner: the complete
        candidate set (stuck ^ avail) & pairsums(avail) - U, ascending.

        With the counter enabled this costs O((|stuck| + |unrealized|) * |U|): the counter
        describes the committed base, so pairs touching removed or unrealized values are
        subtracted temporarily.  Without it, each candidate is tested by an O(|U|) scan.
        """
        if self.p2 is not None and self.p2_added:
            self.p2_sync()
        tri = self.tri
        level = self.level
        avail = [x for x in tri if x in level]
        # Only genuinely unlevelled members of U can be repaired.
        stuck = [s for s in stuck if s in tri and s not in level]
        p2 = self.p2
        # Comprehensions, Counter and set algebra run in C; the explicit loops they replace
        # measured about 1.4x slower on whole walk proposals.
        if p2 is not None:
            # The counter's base is U plus the removed values (nothing is added after the sync).
            # Its pairs that touch an unrealized or removed value r are exactly r ^ avail plus
            # the pairs inside that set, counted here once; w is buildable from realized values
            # iff the base count exceeds the touched count.  Listing the stuck values first
            # makes the head of the same pair list the candidate set X = stuck ^ avail.
            sset = set(stuck)
            unreal = stuck + [x for x in tri if x not in level and x not in sset]
            unreal.extend(self.p2_removed)
            pairs = [r ^ a for r in unreal for a in avail]
            X = set(pairs[:len(stuck) * len(avail)])
            touched = Counter(pairs)
            for i, r in enumerate(unreal):
                for r2 in unreal[i + 1:]:
                    touched[r ^ r2] += 1
        else:
            X = {s ^ a for s in stuck for a in avail}
        X.discard(0)
        X.difference_update(tri)
        if forbid:
            X.difference_update(forbid)
        if p2 is not None:
            # Every w = s ^ a in X is a base pair and a touched pair, so both lookups hit;
            # plain subscripts avoid the cost of .get method calls.
            out = [w for w in X if p2[w] > touched[w]]
        else:
            out = []
            for w in X:
                for a in avail:
                    if (w ^ a) in level:
                        out.append(w)
                        break
        out.sort()
        return out

    def unlocks(self, w, stuck):
        """Cap-free test: does inserting w (not in U) make every stuck target realizable?

        ``stuck`` must be the set of unlevelled members of U.  Cascades through the triple
        index in O(|stuck| + sum of degrees of unlocked values).  Exact when ``cap`` is None;
        with a cap it is a necessary condition (``valid_repairs`` confirms it exactly).
        """
        level = self.level
        tri = self.tri
        got = set()
        stack = []
        for s in stuck:
            if (s ^ w) in level:
                got.add(s)
                stack.append(s)
        while stack:
            u = stack.pop()
            y = u ^ w                       # recipe (w, u)
            if y in stuck and y not in got:
                got.add(y)
                stack.append(y)
            for x in tri[u]:                # recipe (u, x) for y = u ^ x
                y = u ^ x
                if y in stuck and y not in got and (x in level or x in got):
                    got.add(y)
                    stack.append(y)
        tset = self.tset
        for s in stuck:
            if s in tset and s not in got:
                return False
        return True

    def valid_repairs(self, stuck, forbid=()):
        """Every single value w whose insertion makes the state ``ok()`` (ascending).

        ``stuck`` must be the set of unlevelled members of U.  Exact buildability first, then
        ``unlocks`` (the reverse order measured 13x slower: the pair-sum test is the selective
        one), then, only under a cap, an exact trial insertion of each survivor.  If a target
        was removed from U, the only possible single repair is that target itself.
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
            unlocks = self.unlocks
            out = [w for w in self.repair_candidates(stuck, forbid) if unlocks(w, stuck)]
        if out and (absent or self.cap is not None):
            exact = []
            for w in out:
                rec = self._add(w, None)
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
        optional ``core.budget.Budget``; one unit is spent per trial removal and the peel stops
        early when it runs out.  Returns the number of values removed.
        """
        tset = self.tset
        iset = self.iset
        tri = self.tri
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
                u = self.remove((v,))
                if u.stuck:
                    self.restore(u)
                else:
                    removed += 1
                    progress = True
        return removed

    # ----------------------------------------------------------------------- debug
    def check(self):
        """Recompute every invariant from scratch and assert equality (tests, debug mode)."""
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
            assert p2 == self.p2, 'p2'
        return True

    def __repr__(self):
        return ('ValueSet(n=%d, values=%d, realized=%d, cap=%r, ok=%s)'
                % (self.n, len(self.tri) - self.n, self.count(), self.cap, self.ok()))


def _target_parts(target):
    """(n_inputs, rows) from a Target-like object, an old-style dict or an (n, rows) pair."""
    if isinstance(target, tuple) and len(target) == 2 and isinstance(target[0], int):
        return target[0], list(target[1])
    if isinstance(target, dict):
        return target['input_count'], list(target['rows'])
    return target.n_inputs, list(target.rows)
