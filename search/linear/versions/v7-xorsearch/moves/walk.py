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
``walk.expand``   remove one helper and add two values: the first is a buildable value that
                  directly unlocks the most stuck values, the second an exact repair from the
                  extended bank.  Up to +1: the real uphill step the v1 walk lacked (v2
                  ``_expand_repair``).

(``walk.window``, remove k connected helpers and search for at most k-1 new values, was removed
after the 2026-10-28 campaigns: 3.4% of fleet CPU, 0.1% acceptance and 0.03x the average
weighted yield per CPU.)

Repair selection (``moves.walk.repair``): candidates are ranked by (popcount, -reuse) after a
shuffle (hunt87 ``_repair``), the first ``top_k`` are inserted one at a time inside a nested
journal, cap-infeasible ones are dropped (the state's cap is the search cap, so "fits the cap" is
just ``ok()``), and the smallest trimmed size wins with random tie-break.  ``local_peel``
additionally tries to drop the witness operands of values that gained a recipe through the new
value: the kernel's earliest witness keeps one recipe per value, so a repair that makes an old
operand redundant is otherwise invisible to trim (the 4-input toy 0111/1110 needs this).

Victims are uniform over the helpers (the historical walk).  The low fan-out and near-recent
victim policies were removed: weight 0 in every campaign.  The moves are stateless.

Trace fields (in addition to ``components``, ``params``, ``removed``, ``added``):
``victims``, ``stuck`` (stuck values after removal), ``candidates`` (complete repair count),
``evaluated``, ``feasible`` (cap-feasible evaluations), ``rank`` (position of the chosen repair
in the ranked list), ``size_before``/``size_after``, ``reason`` when nothing was changed; expand
adds ``firsts``, ``tests`` and ``victim``/``first``/``second``.

Work units (``Budget.tick``): one per repair enumeration plus one per enumerated candidate, one
per candidate insertion tested, one per first-step candidate.  Candidates are scored inside
nested journals (``journal()`` / ``rollback`` / ``commit``), and the moves read the kernel's
public ``tri``, ``level``, ``par``, ``kids``, ``iset``, ``tset``.  Repair enumeration is the hot
spot (``repair_candidates``), so the walk wants the pair-sum index (``pairsums=True``).
"""
from __future__ import annotations

from ..config.schema import Knob, Section
from .base import Move, Proposal, register
from .rebuild import clip, diff_fields, helpers_of, local_peel, trace_limit

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
    "skip_dead": Knob(True, "Skip victims whose removal had no repair (none at all, or none "
                      "feasible among all candidates) until the state changes."),
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

KNOBS = (REPAIR, REMOVE1, EXPAND)


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


def choose_repair(state, ranked, rng, top_k, peel, budget, require=(), partners=None):
    """Score the first ``top_k`` repairs by trimmed size; leave the state unchanged.

    Each candidate is inserted inside a nested journal; it counts only when every target is then
    realised within the state's (search) cap and it, and every value of ``require``, survives
    the trim (is live).  Returns ``(w, size, rank, evaluated, feasible)`` with w None when
    nothing qualified.  The score is exactly what ``apply_repair`` produces.  ``partners`` is
    the ``valid_repairs`` partner map for this state (each insertion then skips its partner
    search).
    """
    best_size = None
    ties = []
    evaluated = 0
    feasible = 0
    tri = state.tri
    pget = (partners or {}).get
    for i, w in enumerate(ranked[:top_k]):
        if not budget.tick():
            break
        evaluated += 1
        mark = state.journal()
        state.add(w, pget(w))
        if state.ok():
            feasible += 1
            if peel:
                local_peel(state, w)
            # After trim() every realized value is live, so count() is the live size.  The
            # trim (one O(|U|) scan, rolled back below) is 2-3x cheaper than live().
            state.trim()
            if w in tri and all(r in tri for r in require):
                size = state.count()
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


def unlock_counts(state, cands, stuck) -> dict:
    """``{w: #{s in stuck : s ^ w realized}}``: stuck values each candidate builds directly
    (with a realized partner), the "most unlocks first" order of expand."""
    level = state.level
    out = {}
    for w in cands:
        c = 0
        for s in stuck:
            if (s ^ w) in level:
                c += 1
        out[w] = c
    return out


def apply_repair(state, w, peel, partners=None) -> None:
    """Insert the chosen repair exactly as it was scored, then trim."""
    state.add(w, partners.get(w) if partners else None)
    if peel:
        local_peel(state, w)
    state.trim()


# --------------------------------------------------------------------------- shared move base
class _WalkMove(Move):
    """Common setup: knob caching, trace assembly."""
    family = "walk"

    def __init__(self, settings):
        super().__init__(settings)
        rep = settings.view(REPAIR.path)
        self.rank_rule = rep.rank
        self.top_k = int(rep.top_k)
        self.peel = bool(rep.local_peel)
        self.limit = trace_limit(settings)

    def _params(self, **extra) -> dict:
        params = {"rank": self.rank_rule, "top_k": self.top_k, "local_peel": self.peel}
        params.update(extra)
        return params

    def _finish(self, ctx, journal, trace, work0) -> Proposal:
        """Proposal for the state edited inside the open ``journal``."""
        added, removed = journal.changes()
        trace.update(diff_fields(added, removed, self.limit))
        trace["size_after"] = ctx.state.count()
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
        journal = state.journal()
        undo = state.remove(victims)
        budget.tick()
        if not _stuck_targets(undo, state.tset):
            state.trim()
            trace["components"] += ["free", "trim"]
            return self._finish(ctx, journal, trace, work0)
        stuck = undo.stuck
        partners = {}
        cands = state.valid_repairs(stuck, victims, partners)
        budget.tick(1 + len(cands))
        trace["stuck"] = len(stuck)
        trace["candidates"] = len(cands)
        if not cands:
            state.rollback(journal)
            return self._noop(ctx, trace, "no_repair", work0)
        ranked = rank_repairs(state, cands, rng, self.rank_rule, self.top_k)
        w, _, rank, evaluated, feasible = choose_repair(
            state, ranked, rng, self.top_k, self.peel, budget, partners=partners)
        trace.update(evaluated=evaluated, feasible=feasible)
        if w is None:
            state.rollback(journal)
            return self._noop(ctx, trace, "no_feasible_repair", work0)
        apply_repair(state, w, self.peel, partners)
        trace["rank"] = rank
        trace["components"] += ["repair"] + (["local_peel"] if self.peel else []) + ["trim"]
        return self._finish(ctx, journal, trace, work0)


def _stuck_targets(undo, tset) -> bool:
    """True when the removal behind ``undo`` left some target unrealizable."""
    return not tset.isdisjoint(undo.stuck)


# --------------------------------------------------------------------------- walk.remove1
@register
class RemoveOne(_WalkMove):
    """Remove one helper; free removal or exact single-value repair (never uphill)."""
    name = "walk.remove1"
    knobs = REMOVE1

    def __init__(self, settings):
        super().__init__(settings)
        self.skip_dead = bool(self.cfg.skip_dead)
        # Victims whose removal has no repair on the state with this key hash.  A chain that
        # stays put (MixColumns cap 4: 90@4 revisited 7x, drift 0.04) otherwise retries
        # them: such no-op remove1 calls were 41% of the 2026-10-29 rerun CPU.
        self.dead_on = None
        self.dead = set()

    def state(self) -> dict:
        return {"dead_on": self.dead_on, "dead": sorted(self.dead)} if self.dead else {}

    def load_state(self, data: dict) -> None:
        self.dead_on = data.get("dead_on")
        self.dead = set(int(v) for v in data.get("dead", ()))

    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        helpers = helpers_of(state)
        trace = {"components": ["remove1"], "size_before": state.count()}
        if not helpers:
            return self._noop(ctx, trace, "no_helpers", work0)
        on = None
        if self.dead:
            on = hash(state.key())         # int hashes: the same in every process
            if on != self.dead_on:
                self.dead.clear()
            else:
                trace["dead"] = len(self.dead)
                helpers = [h for h in helpers if h not in self.dead]
                if not helpers:
                    return self._noop(ctx, trace, "all_dead", work0)
        v = rng.choice(helpers)
        trace["params"] = self._params()
        trace["victims"] = [v]
        prop = self._remove_and_repair(ctx, (v,), trace, work0)
        # Only outcomes that do not depend on the RNG: no candidate at all, or every
        # candidate scored and none feasible.
        if self.skip_dead and prop.journal is None and (
                trace.get("reason") == "no_repair"
                or (trace.get("reason") == "no_feasible_repair"
                    and trace.get("evaluated") == trace.get("candidates"))):
            if on is None:
                on = hash(state.key())
            if on != self.dead_on:
                self.dead.clear()
                self.dead_on = on
            self.dead.add(v)
        return prop


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
        cands = state.repair_candidates(stuck, forbid)      # ascending
        if not cands:
            return [], 0
        # A value that repairs everything alone is remove1's step; here it would leave the
        # second value with nothing to do.
        unlocks = state.unlocks
        cands = [w for w in cands if not unlocks(w, stuck)]
        count = unlock_counts(state, cands, stuck)
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
        # Distinct uniform victims (a sample instead of shuffling all ~540 helpers on FOX Mu8).
        order = rng.sample(helpers, min(len(helpers), self.victims))
        trace["params"] = self._params(victims=self.victims, firsts=self.firsts,
                                       second_k=self.second_k)
        journal = state.journal()
        tried = []
        firsts_total = 0
        results = []          # (size, v, first, second)
        tests = 0
        for v in order:
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
                    partners = {}
                    seconds = state.valid_repairs(stuck2, (v, first), partners)
                    budget.tick(1 + len(seconds))
                    tests += len(seconds)
                    if seconds:
                        ranked = rank_repairs(state, seconds, rng, self.rank_rule, self.second_k)
                        w, size, _, _, _ = choose_repair(
                            state, ranked, rng, self.second_k, self.peel, budget,
                            require=(first,), partners=partners)
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
        return self._finish(ctx, journal, trace, work0)
