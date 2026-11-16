"""Plateau walk moves: remove helpers, repair exactly, trim.

Role in the method
------------------
The walk is the main move (DESIGN section 1): every forward 88 and the cascade 91@4 came out of
walk chunks, and the archive counts 736 walk against 22 LNS improvements.  Its strength is the
*exact* repair: after removing a helper, every single value that makes all targets realisable
again is enumerated (``ValueSet.valid_repairs``), instead of sampling a few guesses.  Exact repair
made the 88 plateau walkable (~7x plateau mobility in campaign 87); a ``valid[:4]`` prescreen
deleted 30-37% of true plateau edges, so the moves here evaluate up to ``top_k`` repairs.

Moves (all edit ``ctx.state`` inside a journal and leave it trimmed):

``walk.remove1``  remove one helper; if the rest still realises every target, trim and stop (a
                  free removal, -1 or better); else repair with one value chosen among the
                  feasible ones by smallest trimmed size.  Never uphill.  (v2/hunt87 remove-one)
``walk.hub``      remove two helpers (the second near the first in Hamming distance with
                  probability ``near_p``) and repair with one: -1 or better when it succeeds.
                  (v2 hub move: dead at the 88 frontier, useful higher up -> low weight)
``walk.expand``   remove one helper and add two values: the first is a buildable value that
                  directly unlocks the most stuck values, the second an exact repair from the
                  extended bank.  Up to +1: the real uphill step the v1 walk lacked (v2
                  ``_expand_repair``).
``walk.window``   remove k (2-4) connected helpers and search for at most k-1 new values by a
                  bounded first-unlock DFS (campaign-87 ``exact_window`` solve1/solve2 idea on
                  the kernel): every level branches on buildable values that unlock a stuck
                  value, the last level is the complete single-value repair.  No proof claims.

Repair selection (``moves.walk.repair``): candidates are ranked by (popcount, -reuse) after a
shuffle (hunt87 ``_repair``), the first ``top_k`` are inserted one at a time inside a nested
journal, cap-infeasible ones are dropped (the state's cap is the search cap, so "fits the cap" is
just ``ok()``), and the smallest trimmed size wins with random tie-break.  ``local_peel``
additionally tries to drop the witness operands of values that gained a recipe through the new
value: the kernel's earliest witness keeps one recipe per value, so a repair that makes an old
operand redundant is otherwise invisible to trim (the 4-input toy 0111/1110 needs this).

Victim selection (``moves.walk.victim``) mixes three policies by weight: uniform (the historical
walk), low fan-out (tournament on witness children: cheap to remove) and near recent changes
(triple-index neighbours of values this move recently added: keeps working where the chain just
moved).

Trace fields (in addition to ``components``, ``params``, ``removed``, ``added``):
``victims``, ``stuck`` (stuck values after removal), ``candidates`` (complete repair count),
``evaluated``, ``feasible`` (cap-feasible evaluations), ``rank`` (position of the chosen repair
in the ranked list), ``size_before``/``size_after``, ``reason`` when nothing was changed; expand
adds ``firsts`` and ``first``/``second``; window adds ``k``, ``window``, ``budget_values``,
``tests``, ``solution``.

Work units (``Budget.tick``): one per repair enumeration plus one per enumerated candidate, one
per candidate insertion tested, one per first-step candidate.  Candidates are scored inside
nested journals (``journal()`` / ``rollback`` / ``commit``), and the moves read the kernel's
public ``tri``, ``level``, ``par``, ``kids``, ``iset``, ``tset``.  Repair enumeration is the hot
spot (``repair_candidates``), so the walk wants the pair-sum counter (``pairsums=True``).
"""
from __future__ import annotations

from ..config.schema import Knob, Section
from .base import Move, Proposal, register
from .rebuild import clip, helpers_of, local_peel, trace_limit, value_diff

VICTIM = Section("moves.walk.victim", "How walk moves choose the values they remove.", {
    "uniform": Knob(1.0, "Weight of uniform victim choice (the historical walk).", min=0),
    "low_fanout": Knob(0.0, "Weight of a tournament preferring few witness children.", min=0),
    "recent": Knob(0.0, "Weight of choosing near a value this move recently added.", min=0),
    "tournament": Knob(3, "Tournament size of the low fan-out policy.", min=1),
    "recent_max": Knob(32, "Recently added values remembered per move (move state).", min=1),
})

REPAIR = Section("moves.walk.repair", "How walk moves choose among exact repairs.", {
    "rank": Knob("weight_reuse", "Candidate order before the top_k cut: weight_reuse = "
                 "(popcount, -reuse) as hunt87; weight = popcount; random.",
                 choices=("weight_reuse", "weight", "random")),
    "top_k": Knob(16, "Repairs inserted and scored per proposal (v2 scored up to 16; a top-4 "
                  "prescreen lost 30-37% of plateau edges).", min=1),
    "local_peel": Knob(True, "After inserting a repair, try dropping witness operands it made "
                       "redundant (finds shared-value gains the earliest witness hides)."),
})

REMOVE1 = Section("moves.walk.remove1", "Remove one helper, then exact single-value repair.", {
    "weight": Knob(6.0, "Prior scheduler weight in the plateau phase (walk made nearly every "
                   "record; remove-one is its main step).", min=0),
    "burst_weight": Knob(1.0, "Scheduler weight in the burst phase (near uniform).", min=0),
})

HUB = Section("moves.walk.hub", "Remove two helpers, repair with one.", {
    "weight": Knob(1.5, "Prior scheduler weight in the plateau phase (v2 hub_move_p 0.3, but 0 "
                   "successes in 2.24M samples at the 88 frontier).", min=0),
    "burst_weight": Knob(1.0, "Scheduler weight in the burst phase.", min=0),
    "near_hamming": Knob(8, "Second victim within this Hamming distance of the first (v2 "
                         "close_hamming).", min=0),
    "near_p": Knob(0.5, "Probability the second victim is chosen near the first.", min=0, max=1),
})

EXPAND = Section("moves.walk.expand", "Remove one helper, add two values (up to +1).", {
    "weight": Knob(0.6, "Prior scheduler weight in the plateau phase (v2 expansion_p "
                   "0.04-0.12 of walk iterations).", min=0),
    "burst_weight": Knob(1.0, "Scheduler weight in the burst phase.", min=0),
    "victims": Knob(4, "Victims tried per proposal (v2 tried up to 4).", min=1),
    "first_candidates": Knob(8, "First values tried per victim (v2 expansion_candidates 8).",
                             min=1),
    "head_fraction": Knob(0.5, "Share of first values taken by unlock count; the rest is a "
                          "uniform sample so low weight does not lock the neighbourhood.",
                          min=0, max=1),
    "second_k": Knob(8, "Second values (exact repairs) scored per first value.", min=1),
    "results": Knob(1, "Stop after this many complete results and keep the smallest.", min=1),
})

WINDOW = Section("moves.walk.window", "Remove k connected helpers, repair with at most k-1.", {
    "weight": Knob(0.6, "Prior scheduler weight in the plateau phase (legacy-window made 2 of "
                   "29 framework improvements).", min=0),
    "burst_weight": Knob(1.0, "Scheduler weight in the burst phase.", min=0),
    "k_min": Knob(2, "Smallest window.", min=2),
    "k_max": Knob(4, "Largest window (k-1 new values are searched).", min=2),
    "branch_cap": Knob(8, "Unlock-anchored candidates branched on per DFS level above the "
                       "last.", min=1),
})

KNOBS = (VICTIM, REPAIR, REMOVE1, HUB, EXPAND, WINDOW)


# --------------------------------------------------------------------------- victim choice
class VictimPolicy:
    """Mixture of victim-selection policies (``moves.walk.victim``)."""
    __slots__ = ("w_uniform", "w_low", "w_recent", "total", "tournament", "recent_max")

    def __init__(self, view):
        self.w_uniform = float(view.uniform)
        self.w_low = float(view.low_fanout)
        self.w_recent = float(view.recent)
        self.total = self.w_uniform + self.w_low + self.w_recent
        self.tournament = int(view.tournament)
        self.recent_max = int(view.recent_max)

    def pick(self, state, helpers, rng, recent):
        """One victim from ``helpers`` (sorted list) and the name of the policy used."""
        r = rng.random() * self.total if self.total > 0 else 0.0
        if r < self.w_uniform or self.total <= 0:
            return rng.choice(helpers), "uniform"
        r -= self.w_uniform
        if r < self.w_low:
            kids = state.kids
            group = rng.sample(helpers, min(self.tournament, len(helpers)))
            return min(group, key=lambda v: (len(kids[v]), v)), "low_fanout"
        tri = state.tri
        alive = [v for v in recent if v in tri]
        if alive:
            anchor = rng.choice(alive)
            iset = state.iset
            tset = state.tset
            near = sorted(x for x in tri[anchor] if x not in iset and x not in tset)
            if anchor not in tset:
                near.append(anchor)
            if near:
                return rng.choice(near), "recent"
        return rng.choice(helpers), "uniform"


# --------------------------------------------------------------------------- repair helpers
def rank_repairs(state, cands, rng, rule, top_k):
    """Candidates in evaluation order: canonical sort, shuffle, then the ranking rule.

    Ranking only decides which candidates make the ``top_k`` cut; when all of them are scored the
    O(|U|)-per-candidate reuse count is skipped (selection then breaks ties at random anyway).
    """
    out = sorted(cands)
    rng.shuffle(out)
    if rule == "random" or len(out) <= 1:
        return out
    if rule == "weight" or len(out) <= top_k:
        out.sort(key=int.bit_count)
        return out
    level = state.level
    avail = [x for x in state.tri if x in level]
    reuse = {}
    for w in out:
        c = 0
        for p in avail:
            if (w ^ p) in level:
                c += 1
        reuse[w] = c
    out.sort(key=lambda w: (w.bit_count(), -reuse[w]))
    return out


def choose_repair(state, ranked, rng, top_k, peel, budget, require=()):
    """Score the first ``top_k`` repairs by trimmed size; leave the state unchanged.

    Each candidate is inserted inside a nested journal; it counts only when every target is then
    realised within the state's (search) cap and it, and every value of ``require``, is live.
    Returns ``(w, size, rank, evaluated, feasible)`` with w None when nothing qualified.
    """
    best_size = None
    ties = []
    evaluated = 0
    feasible = 0
    for i, w in enumerate(ranked[:top_k]):
        if not budget.tick():
            break
        evaluated += 1
        mark = state.journal()
        state.add(w)
        if state.ok():
            feasible += 1
            if peel:
                local_peel(state, w)
            live = state.live()
            if w in live and all(r in live for r in require):
                size = len(live)
                if best_size is None or size < best_size:
                    best_size = size
                    ties = [(i, w)]
                elif size == best_size:
                    ties.append((i, w))
        state.rollback(mark)
    if not ties:
        return None, None, None, evaluated, feasible
    i, w = ties[0] if len(ties) == 1 else rng.choice(ties)
    return w, best_size, i, evaluated, feasible


def apply_repair(state, w, peel) -> None:
    """Insert the chosen repair exactly as it was scored, then trim."""
    state.add(w)
    if peel:
        local_peel(state, w)
    state.trim()


# --------------------------------------------------------------------------- shared move base
class _WalkMove(Move):
    """Common setup: knob caching, victim memory, trace assembly."""
    family = "walk"

    def __init__(self, settings):
        super().__init__(settings)
        self.victim = VictimPolicy(settings.view(VICTIM.path))
        rep = settings.view(REPAIR.path)
        self.rank_rule = rep.rank
        self.top_k = int(rep.top_k)
        self.peel = bool(rep.local_peel)
        self.limit = trace_limit(settings)
        self.recent = []

    # Move state: the values this move recently added (for the "recent" victim policy).
    def state(self) -> dict:
        return {"recent": list(self.recent)}

    def load_state(self, data: dict) -> None:
        self.recent = [int(v) for v in data.get("recent", ())][-self.victim.recent_max:]

    def _remember(self, values) -> None:
        recent = self.recent
        recent.extend(sorted(values))
        extra = len(recent) - self.victim.recent_max
        if extra > 0:
            del recent[:extra]

    def _params(self, policy, **extra) -> dict:
        params = {"victim": policy, "rank": self.rank_rule, "top_k": self.top_k,
                  "local_peel": self.peel}
        params.update(extra)
        return params

    def _finish(self, ctx, journal, before, trace, work0) -> Proposal:
        """Proposal for an edited state (journal) or an untouched one (journal None)."""
        state = ctx.state
        if journal is not None:
            trace.update(value_diff(before, state, self.limit))
            trace["size_after"] = state.count()
            self._remember(state.key() - before)
        return Proposal(self.name, journal, trace, ctx.budget.used - work0)

    def _noop(self, ctx, trace, reason, work0) -> Proposal:
        trace["reason"] = reason
        return Proposal(self.name, None, trace, ctx.budget.used - work0)

    def _remove_and_repair(self, ctx, victims, trace, work0) -> Proposal:
        """Remove ``victims``; trim if every target survives, else insert the best single exact
        repair (smallest trimmed size among the ranked top_k, cap-feasible), else undo."""
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        before = state.key()
        journal = state.journal()
        undo = state.remove(victims)
        budget.tick()
        if not _stuck_targets(undo, state.tset):
            state.trim()
            trace["components"] += ["free", "trim"]
            return self._finish(ctx, journal, before, trace, work0)
        stuck = undo.stuck
        cands = state.valid_repairs(stuck, victims)
        budget.tick(1 + len(cands))
        trace["stuck"] = len(stuck)
        trace["candidates"] = len(cands)
        if not cands:
            state.rollback(journal)
            return self._noop(ctx, trace, "no_repair", work0)
        ranked = rank_repairs(state, cands, rng, self.rank_rule, self.top_k)
        w, _, rank, evaluated, feasible = choose_repair(
            state, ranked, rng, self.top_k, self.peel, budget)
        trace.update(evaluated=evaluated, feasible=feasible)
        if w is None:
            state.rollback(journal)
            return self._noop(ctx, trace, "no_feasible_repair", work0)
        apply_repair(state, w, self.peel)
        trace["rank"] = rank
        trace["components"] += ["repair"] + (["local_peel"] if self.peel else []) + ["trim"]
        return self._finish(ctx, journal, before, trace, work0)


def _stuck_targets(undo, tset) -> bool:
    """True when the removal behind ``undo`` left some target unrealizable."""
    return not tset.isdisjoint(undo.stuck)


# --------------------------------------------------------------------------- walk.remove1
@register
class RemoveOne(_WalkMove):
    """Remove one helper; free removal or exact single-value repair (never uphill)."""
    name = "walk.remove1"
    knobs = REMOVE1

    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        helpers = helpers_of(state)
        trace = {"components": ["remove1"], "size_before": state.count()}
        if not helpers:
            return self._noop(ctx, trace, "no_helpers", work0)
        v, policy = self.victim.pick(state, helpers, rng, self.recent)
        trace["params"] = self._params(policy)
        trace["victims"] = [v]
        return self._remove_and_repair(ctx, (v,), trace, work0)


# --------------------------------------------------------------------------- walk.hub
@register
class Hub(_WalkMove):
    """Remove two helpers (often close in Hamming distance), repair with one value."""
    name = "walk.hub"
    knobs = HUB

    def __init__(self, settings):
        super().__init__(settings)
        self.near_hamming = int(self.cfg.near_hamming)
        self.near_p = float(self.cfg.near_p)

    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        helpers = helpers_of(state)
        trace = {"components": ["remove2"], "size_before": state.count()}
        if len(helpers) < 2:
            return self._noop(ctx, trace, "too_few_helpers", work0)
        v1, policy = self.victim.pick(state, helpers, rng, self.recent)
        others = [u for u in helpers if u != v1]
        near = False
        if rng.random() < self.near_p:
            h = self.near_hamming
            close = [u for u in others if (u ^ v1).bit_count() <= h]
            if close:
                others = close
                near = True
        v2 = rng.choice(others)
        trace["params"] = self._params(policy, near=near, near_hamming=self.near_hamming)
        trace["victims"] = [v1, v2]
        return self._remove_and_repair(ctx, (v1, v2), trace, work0)


# --------------------------------------------------------------------------- walk.expand
@register
class Expand(_WalkMove):
    """Remove one helper, add an unlocking value and an exact repair (the +1 uphill step)."""
    name = "walk.expand"
    knobs = EXPAND

    def __init__(self, settings):
        super().__init__(settings)
        cfg = self.cfg
        self.victims = int(cfg.victims)
        self.firsts = int(cfg.first_candidates)
        self.head_fraction = float(cfg.head_fraction)
        self.second_k = int(cfg.second_k)
        self.results = int(cfg.results)

    def _firsts(self, state, stuck, forbid, rng):
        """First values: buildable, directly unlock a stuck value, not a full repair alone.

        Ordered by how many stuck values they unlock directly (v2: pair-sum unlocking most stuck
        values), head by count plus a uniform tail.
        """
        cands = sorted(state.repair_candidates(stuck, forbid))
        if not cands:
            return [], 0
        level = state.level
        unlocks = state.unlocks
        count = {}
        for w in cands:
            c = 0
            for s in stuck:
                if (s ^ w) in level:
                    c += 1
            count[w] = c
        # A value that repairs everything alone is remove1's step; here it would leave the
        # second value with nothing to do.
        cands = [w for w in cands if not unlocks(w, stuck)]
        n = len(cands)
        rng.shuffle(cands)
        cands.sort(key=lambda w: (-count[w], w.bit_count()))
        head_n = max(1, int(self.firsts * self.head_fraction))
        head = cands[:head_n]
        tail = cands[head_n:]
        rest = self.firsts - len(head)
        if rest > 0 and tail:
            head += rng.sample(tail, min(rest, len(tail)))
        return head, n

    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        tset = state.tset
        helpers = helpers_of(state)
        size0 = state.count()
        trace = {"components": ["remove1"], "size_before": size0}
        if not helpers:
            return self._noop(ctx, trace, "no_helpers", work0)
        order = list(helpers)
        rng.shuffle(order)
        # The first victim follows the victim policy; further tries are uniform.
        first_victim, policy = self.victim.pick(state, helpers, rng, self.recent)
        order.remove(first_victim)
        order.insert(0, first_victim)
        trace["params"] = self._params(policy, victims=self.victims, firsts=self.firsts,
                                       second_k=self.second_k)
        before = state.key()
        journal = state.journal()
        tried = []
        firsts_total = 0
        results = []          # (size, v, first, second)
        tests = 0
        for v in order[:self.victims]:
            if budget.exhausted():
                break
            tried.append(v)
            mark0 = state.journal()
            undo = state.remove((v,))
            budget.tick()
            if not _stuck_targets(undo, tset):
                state.rollback(mark0)          # a free removal is remove1's job
                continue
            stuck = undo.stuck
            firsts, n_firsts = self._firsts(state, stuck, (v,), rng)
            firsts_total += n_firsts
            budget.tick(1 + n_firsts)
            for first in firsts:
                if not budget.tick():
                    break
                mark1 = state.journal()
                state.add(first)
                level = state.level
                if first in level:
                    stuck2 = {s for s in stuck if s not in level}
                    seconds = state.valid_repairs(stuck2, (v, first))
                    budget.tick(1 + len(seconds))
                    tests += len(seconds)
                    if seconds:
                        ranked = rank_repairs(state, seconds, rng, self.rank_rule, self.second_k)
                        w, size, _, _, _ = choose_repair(
                            state, ranked, rng, self.second_k, self.peel, budget,
                            require=(first,))
                        if w is not None:
                            results.append((size, v, first, w))
                state.rollback(mark1)
                if len(results) >= self.results:
                    break
            state.rollback(mark0)
            if len(results) >= self.results:
                break
        trace.update(victims=clip(tried, self.limit), firsts=firsts_total, tests=tests)
        if not results:
            state.rollback(journal)
            return self._noop(ctx, trace, "no_expansion", work0)
        best = min(r[0] for r in results)
        size, v, first, second = rng.choice([r for r in results if r[0] == best])
        state.remove((v,))
        state.add(first)
        apply_repair(state, second, self.peel)
        trace.update(victim=v, first=first, second=second, results=len(results))
        trace["components"] += ["first.unlock", "second.repair"] + \
            (["local_peel"] if self.peel else []) + ["trim"]
        return self._finish(ctx, journal, before, trace, work0)


# --------------------------------------------------------------------------- walk.window
@register
class Window(_WalkMove):
    """Remove k connected helpers and search for at most k-1 new values (first-unlock DFS)."""
    name = "walk.window"
    knobs = WINDOW

    def __init__(self, settings):
        super().__init__(settings)
        cfg = self.cfg
        self.k_min = int(cfg.k_min)
        self.k_max = max(self.k_min, int(cfg.k_max))
        self.branch_cap = int(cfg.branch_cap)

    @staticmethod
    def _grow(state, seed, k, rng, helpers):
        """Connected window grown from ``seed``; returns (window, jumps).

        Neighbours are witness operands and children first (the circuit edges), then any helper
        sharing a triple with the window (an alternative recipe), and only when neither exists a
        uniformly random helper (a "jump"; helpers that meet only through targets are otherwise
        unreachable, e.g. two disjoint target chains).
        """
        par = state.par
        kids = state.kids
        tri = state.tri
        iset = state.iset
        tset = state.tset
        win = [seed]
        inwin = {seed}
        jumps = 0
        while len(win) < k:
            near = set()
            for u in win:
                a = par.get(u)
                if a is not None:
                    for p in (a, u ^ a):
                        if p not in iset and p not in tset and p not in inwin:
                            near.add(p)
                for c in kids.get(u, ()):
                    if c not in tset and c not in inwin:
                        near.add(c)
            if not near:
                for u in win:
                    for x in tri[u]:
                        if x not in iset and x not in tset and x not in inwin:
                            near.add(x)
            if not near:
                rest = [h for h in helpers if h not in inwin]
                if not rest:
                    break
                near = rest
                jumps += 1
            x = rng.choice(sorted(near))
            win.append(x)
            inwin.add(x)
        return win, jumps

    def _solve(self, state, stuck, b, forbid, rng, budget, info):
        """At most ``b`` new values realising every target, applied to the state; else None.

        The last level is the complete single-value repair; higher levels branch on buildable
        values that directly unlock a stuck value (campaign-87 case 1a), most unlocks first.
        The state is left with the solution inserted, or unchanged on failure.
        """
        if b == 1:
            cands = sorted(state.valid_repairs(stuck, forbid))
            info["tests"] += len(cands)
            budget.tick(1 + len(cands))
            rng.shuffle(cands)
            for w in cands:
                mark = state.journal()
                state.add(w)
                if state.ok():
                    state.commit(mark)
                    return [w]
                state.rollback(mark)            # realisable only beyond the search cap
            return None
        cands = sorted(state.repair_candidates(stuck, forbid))
        info["tests"] += len(cands)
        if not budget.tick(1 + len(cands)):
            return None
        level = state.level
        rng.shuffle(cands)
        count = {}
        for w in cands:
            c = 0
            for s in stuck:
                if (s ^ w) in level:
                    c += 1
            count[w] = c
        cands.sort(key=lambda w: -count[w])
        for w in cands[:self.branch_cap]:
            mark = state.journal()
            state.add(w)
            level = state.level
            if w in level:
                if state.ok():
                    state.commit(mark)
                    return [w]
                stuck2 = {s for s in stuck if s not in level}
                res = self._solve(state, stuck2, b - 1, forbid + (w,), rng, budget, info)
                if res is not None:
                    state.commit(mark)
                    return [w] + res
            state.rollback(mark)
            if budget.exhausted():
                return None
        return None

    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        helpers = helpers_of(state)
        trace = {"components": ["window"], "size_before": state.count()}
        if len(helpers) < self.k_min:
            return self._noop(ctx, trace, "too_few_helpers", work0)
        k = rng.randint(self.k_min, min(self.k_max, len(helpers)))
        seed, policy = self.victim.pick(state, helpers, rng, self.recent)
        win, jumps = self._grow(state, seed, k, rng, helpers)
        trace["params"] = self._params(policy, k=k, branch_cap=self.branch_cap)
        trace["k"] = len(win)
        trace["jumps"] = jumps
        trace["window"] = clip(win, self.limit)
        before = state.key()
        journal = state.journal()
        undo = state.remove(win)
        budget.tick()
        if not _stuck_targets(undo, state.tset):
            state.trim()
            trace["components"] += ["free", "trim"]
            return self._finish(ctx, journal, before, trace, work0)
        if len(win) < 2:
            state.rollback(journal)
            return self._noop(ctx, trace, "window_too_small", work0)
        info = {"tests": 0}
        trace["stuck"] = len(undo.stuck)
        trace["budget_values"] = len(win) - 1
        sol = self._solve(state, set(undo.stuck), len(win) - 1, tuple(win), rng, budget, info)
        trace["tests"] = info["tests"]
        if sol is None:
            state.rollback(journal)
            return self._noop(ctx, trace, "no_window_solution", work0)
        state.trim()
        trace["solution"] = clip(sol, self.limit)
        trace["components"] += ["first_unlock_dfs", "trim"]
        return self._finish(ctx, journal, before, trace, work0)
