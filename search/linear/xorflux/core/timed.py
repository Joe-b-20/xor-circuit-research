"""TimedValueSet: a ValueSet with per-input arrival levels and per-target deadlines.

Role in the method
------------------
The XOR part of a circuit with a fixed nonlinear skeleton (e.g. the AND gates of an S-box
circuit) is one linear map from the variables (circuit inputs and AND outputs) to the AND inputs
and the circuit outputs.  Its variables arrive at different gate levels (an AND output at the
level of its AND) and its targets have different deadlines (an AND input one level below its
AND, an output the circuit's gate-depth cap).  ``TimedValueSet`` searches that map exactly:

* input i sits at level ``arrival[i]`` instead of 0;
* a target row t is *realized* only at a level <= ``deadline[t]`` (and <= the cap); a target
  that cannot arrive by its deadline is stuck, so ``ok()`` means "every deadline is met" and the
  engine's existing rejection of not-ok proposals enforces the timing;
* other values are bounded by the cap as before.

Everything else (triple index, canonical witnesses, journal, undo, pair-sum index) is inherited
unchanged: only the three places that compare a level with the cap (``_resolve``, ``_lower``,
``_add``) take the per-value limit, and ``_lower`` never relevels an input (with level-0 inputs
the fast path skipped them implicitly).  The levels stay a pure function of (U, cap, timing).

Popcount bounds (``ceil(log2 w)``) stay valid lower bounds (arrivals are >= 0) but are weaker.
"""
from __future__ import annotations

from .valueset import INF, ValueSet


class TimedValueSet(ValueSet):
    """``TimedValueSet(n, targets, values, cap, pairsums, arrival=, deadline=)``.

    ``arrival``: n nonnegative ints (input i's level).  ``deadline``: one int (or None = no
    deadline but the cap) per row of ``targets``; repeated rows take their smallest deadline.
    """

    def __init__(self, n, targets, values=(), cap=None, pairsums=False, arrival=None,
                 deadline=None):
        arrival = [0] * n if arrival is None else [int(a) for a in arrival]
        if len(arrival) != n or any(a < 0 for a in arrival):
            raise ValueError('arrival needs n nonnegative levels')
        rows = [int(t) for t in targets]
        if deadline is None:
            deadline = [None] * len(rows)
        if len(deadline) != len(rows):
            raise ValueError('deadline needs one entry per target row')
        dl = {}
        for t, d in zip(rows, deadline):
            if t and d is not None:
                dl[t] = min(int(d), dl.get(t, INF))
        self._tm_arrival = tuple(arrival)
        self._tm_dl = dl
        self._tm_init = False
        super().__init__(n, rows, values, cap=cap, pairsums=pairsums)

    # The base __init__ sets every input to level 0 and then calls _resolve once: the first
    # call puts the arrivals in place before anything is levelled.
    def _arrive(self):
        if not self._tm_init:
            self._tm_init = True
            level = self.level
            for i, a in enumerate(self._tm_arrival):
                level[1 << i] = a

    def limit(self, v):
        """Largest level at which v counts as realized (deadline, cap)."""
        lim = INF if self.cap is None else self.cap
        d = self._tm_dl.get(v)
        return lim if d is None or d > lim else d

    def deadline_of(self, v):
        return self._tm_dl.get(v)

    def slack(self):
        """min over targets of (limit - level); None when a target is stuck."""
        level = self.level
        out = INF
        for t in self.targets:
            lt = level.get(t)
            if lt is None:
                return None
            s = self.limit(t) - lt
            if s < out:
                out = s
        return out

    def _resolve(self, pend):
        self._arrive()
        level = self.level
        tri = self.tri
        par = self.par
        kids = self.kids
        lim = INF if self.cap is None else self.cap
        dl = self._tm_dl
        tent = {}
        tpar = {}
        buckets = {}
        for v in pend:
            best = INF
            bp = 0
            for x in tri[v]:
                y = v ^ x
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
            lv = dl.get(v, lim)
            if lv > lim:
                lv = lim
            if bp and best < lv:
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
                        continue
                    level[v] = d
                    a = tpar[v]
                    par[v] = a
                    kids[a].add(v)
                    kids[v ^ a].add(v)
                    if d >= lim:
                        continue
                    for x in tri[v]:
                        y = v ^ x
                        if y not in pend or y in level:
                            continue
                        lx = level.get(x)
                        if lx is None:
                            continue
                        m = 1 + (d if d > lx else lx)
                        ly_lim = dl.get(y, lim)
                        if m > lim or m > ly_lim:
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
        level = self.level
        tri = self.tri
        par = self.par
        kids = self.kids
        iset = self.iset
        lim = INF if self.cap is None else self.cap
        dl = self._tm_dl
        buckets = {}
        for s in seeds:
            buckets.setdefault(level[s], []).append(s)
        d = min(buckets)
        while buckets:
            us = buckets.pop(d, None)
            if us is not None and d < lim:
                for u in us:
                    if level.get(u) != d:
                        continue
                    m = d + 1
                    for x in tri[u]:
                        lx = level.get(x)
                        if lx is None:
                            continue
                        y = u ^ x
                        mm = m if lx < d else lx + 1
                        ly = level.get(y)
                        if ly is not None and ly < mm:
                            continue
                        if mm > lim or y in iset:
                            continue
                        if mm > dl.get(y, lim):
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
                            if y not in changed:
                                changed[y] = (ly, par[y])
                            a = par[y]
                            kids[a].discard(y)
                            kids[y ^ a].discard(y)
                            par[y] = k
                            kids[k].add(y)
                            kids[y ^ k].add(y)
            d += 1

    def _add(self, w, partners):
        tri = self.tri
        if w in tri or w == 0:
            return None
        if partners is None:
            if self.p2 is not None:
                partners = self._p2_partners(w)
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
        if bp and best < self.limit(w):
            level[w] = best + 1
            self.par[w] = bp
            kids = self.kids
            kids[bp].add(w)
            kids[w ^ bp].add(w)
            self._lower((w,), changed)
        return changed

    def check(self):
        """Invariants: levels equal a from-scratch timed earliest-arrival fixpoint."""
        tri = self.tri
        iset = self.iset
        assert all(i in tri for i in iset), 'inputs missing'
        for v, tv in tri.items():
            expect = {x for x in tri if x ^ v in tri and x != v}
            assert tv == expect, ('tri', v)
        lev = {1 << i: a for i, a in enumerate(self._tm_arrival)}
        changed = True
        while changed:
            changed = False
            for v in tri:
                if v in iset:
                    continue
                best = INF
                for x in tri[v]:
                    y = v ^ x
                    if x in lev and y in lev:
                        best = min(best, max(lev[x], lev[y]) + 1)
                if best <= self.limit(v) and best < lev.get(v, INF):
                    lev[v] = best
                    changed = True
        assert lev == self.level, 'timed levels'
        for v, a in self.par.items():
            assert v in self.kids[a] and v in self.kids[v ^ a], 'kids missing'
        return True
