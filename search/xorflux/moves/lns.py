"""Large-neighbourhood search: destroy part of the circuit, rebuild it from a candidate bank.

Role in the method
------------------
LNS is the second move (DESIGN section 1): v2 LNS with deadline-aware rebuild was the top framework
engine (9 of 29 strict improvements, 7.1 per 100 CPU-h), made the v2 89@4 and 90@4, and every point
of the capped inverse depth staircase.  It is a secondary improver next to the walk, so its prior
weight is lower.  This is the v2 ``engine_lns`` iteration on the incremental kernel; acceptance
belongs to the engine.

One proposal (``lns.rebuild``):

1. **destroy**: pick victims with one operator (mixture weights are knobs)

   * ``small``  1-4 random helpers (the moves that actually rebuild);
   * ``cone``   2-4 *connected* helpers grown from a seed (children of victims and parents that
     feed only victims, v2 ``_cone_pick``), plus injection (~12x improvements/s over random
     destroys in campaign 87);
   * ``big``    8-16 random helpers plus injection, viable only because of the peel window.

   (v2's forced 12-16 value "kshake" was removed: ~4,900 proposals in the 2026-10-28
   campaigns, 0 improvements.)

   Victims are *not* removed: they stay in the bank at cost class ``vic_cost`` so a rebuild never
   dead-ends (~34x accepted moves) while the higher cost pushes it elsewhere.
2. **bank**: add candidate values to U: draws from the pool / hot list (``hot_frac`` of draws from
   the hot list of values a rebuild recently re-introduced, ~11x accepted moves), random kept ^ kept
   sums, injections (victim ^ kept, victim ^ input, victim ^ victim; v2 ``_inject``).
3. **rebuild**: a strategy from ``moves/rebuild.py``: the greedy extract always, and with
   probability ``deadline_p`` (never after a big destroy) the deadline-aware beam, which wins
   when it is not larger.  2026-10-28: greedy-only proposals were 5.5% of CPU for 37% of the
   tightness-weighted LNS yield; any proposal with the beam 5.4% for 2.8%, and a beam after a
   big destroy cost 47 ms for almost nothing.
4. **commit and peel**: U becomes the rebuilt set (trimmed); a result up to ``peel_window`` values
   larger than before is peeled once per distinct set before the engine judges it (kernel peel
   to 1-minimal, bounded to ``peel_passes`` passes over the helpers; v2).  Measured on the four
   real seeds, the full peel gives the most accepted plateau moves per second (invmc88 8.7/s
   against 2.8/s for a local peel of only the operands the new values made redundant, which was
   removed, and 1/s without peel).

Move state (``state()``/``load_state()``): the bounded pool (vocabulary of values that appeared in
accepted rebuilds), the bounded hot list and the bounded set of already-peeled set hashes.  Both
lists are ring buffers: no per-iteration re-sort (454 us in legacy) and no deepcopy (300 us);
the perf report's rule 3.  Pool and hot updates follow v2's *accepted* semantics without knowing
the engine's decision: the values a proposal introduced are remembered and absorbed at the next
call only if they are still in the chain.

Trace fields (besides ``components``, ``params``, ``removed``, ``added``): ``op``, ``victims``,
``k``, ``draws``, ``extras`` (values added to the bank), ``bank`` (|U| with extras),
``greedy_size``, ``deadline_size``, ``deadline`` (beam stats), ``rebuild`` (strategy that produced
the result), ``peeled``, ``size_before``/``size_after``, ``reason`` when nothing changed.

Work units: one per bank insertion, beam state or completion (see rebuild.py) and the kernel's
peel units.  Requirements beyond DESIGN 4.2: ``extract`` with cost classes, read access to
``tri``, ``par``, ``kids``, ``iset``, ``tset``, ``inputs``, ``cap``; LNS never needs the pair-sum
index (perf report section 4).
"""
from __future__ import annotations

from ..config.schema import Knob, Section
from .base import Move, Proposal, register
from .rebuild import (KNOBS as REBUILD_KNOBS, DeadlineParams, clip, commit_choice, diff_fields,
                      greedy, helpers_of, reconstruct, recipes_within, trace_limit,
                      witness_recipes)

KNOBS = Section("moves.lns.rebuild", "Destroy-rebuild with cost classes, bank and peel.", {
    "weight": Knob(3.0, "Prior scheduler weight in the plateau phase (LNS: secondary move, "
                   "historically best at 20-35% of time).", min=0),
    "burst_weight": Knob(1.0, "Scheduler weight in the burst phase (near uniform).", min=0),
    "op_small": Knob(0.35, "Mixture weight of the small destroy (v2 op_mix).", min=0),
    "op_cone": Knob(0.45, "Mixture weight of the connected cone destroy + injection.", min=0),
    "op_big": Knob(0.20, "Mixture weight of the big destroy + injection.", min=0),
    "small_p": Knob([0.45, 0.30, 0.15, 0.10], "Small destroy: probabilities of 1, 2, 3, 4 ... "
                    "victims (v2).", kind=list),
    "cone_min": Knob(2, "Cone destroy: fewest victims.", min=1),
    "cone_max": Knob(4, "Cone destroy: most victims.", min=1),
    "big_min": Knob(8, "Big destroy: fewest victims.", min=1),
    "big_max": Knob(16, "Big destroy: most victims.", min=1),
    "inject_cone": Knob(6, "Injected victim ^ kept values per victim after a cone destroy.",
                        min=0),
    "inject_big": Knob(8, "Injected victim ^ kept values per victim after a big destroy.",
                       min=0),
    "inject_inputs": Knob(2, "Injected victim ^ input values per victim.", min=0),
    "draws_base": Knob(12, "Pool/hot draws and kept-pair draws per rebuild, base (v2 nsamp "
                       "(12, 12) was 1.3-1.8x the throughput of (24, 24) at equal drift).", min=0),
    "draws_extra": Knob(12, "Plus up to this many (uniform).", min=0),
    "pair_inputs": Knob(True, "Kept-pair draws may use inputs as operands (finds values such "
                        "as kept ^ input that v2's kept-only pairs missed)."),
    "hot_frac": Knob(0.5, "Share of pool draws taken from the hot list.", min=0, max=1),
    "extra_cost": Knob(2, "Pull-in cost class of a bank candidate.", min=0),
    "vic_cost": Knob(3, "Pull-in cost class of a victim.", min=0),
    "strategy": Knob("mixed", "Rebuild: greedy, deadline, or mixed (greedy always, deadline "
                     "with probability deadline_p; the smaller wins).",
                     choices=("greedy", "deadline", "mixed")),
    "deadline_p": Knob(0.05, "Mixed strategy: probability of also running the deadline beam "
                       "after a small or cone destroy (v2 lanes 0.12/0.25/0.40 found 90@4 and "
                       "89@4; at 0.25 the beam was 5.4% of 2026-10-28 CPU for 2.8% of the "
                       "weighted LNS yield).", min=0, max=1),
    "deadline_states": Knob(400, "Beam states per LNS deadline call (moves.rebuild.max_states "
                            "is the depth-repair default).", min=0),
    "peel": Knob("full", "How a near miss is peeled: full = kernel peel to 1-minimal (v2), "
                 "off.", choices=("full", "off")),
    "peel_window": Knob(6, "Peel results up to this many values larger than before (v2).",
                        min=0),
    "peel_passes": Knob(1.0, "Full peel: trial removals allowed, in passes over the helpers.",
                        min=0),
    "pool_limit": Knob(6000, "Pool size bound (v2 campaign profile).", min=1),
    "hot_limit": Knob(1000, "Hot list bound (v2 campaign profile).", min=1),
    "pool_init": Knob(2000, "Random pair sums of the chain seeding an empty pool.", min=0),
    "peel_seen_max": Knob(2048, "Peeled-set hashes remembered (cleared when full).", min=1),
})


class _Ring:
    """Bounded list with O(1) append that overwrites the oldest entry when full.

    ``unique`` keeps a membership set and skips values already present (the pool);
    the hot list allows repeats so frequently re-introduced values are drawn more often.
    """
    __slots__ = ("items", "limit", "pos", "members")

    def __init__(self, limit, unique):
        self.items = []
        self.limit = limit
        self.pos = 0
        self.members = set() if unique else None

    def add(self, v):
        members = self.members
        if members is not None:
            if v in members:
                return
            members.add(v)
        items = self.items
        if len(items) < self.limit:
            items.append(v)
            return
        old = items[self.pos]
        items[self.pos] = v
        self.pos = (self.pos + 1) % self.limit
        if members is not None:
            members.discard(old)

    def ordered(self):
        """Oldest first (for checkpoints)."""
        return self.items[self.pos:] + self.items[:self.pos]

    def draw(self, rng):
        """Uniform entry, indexed in oldest-first order so a reloaded ring draws identically."""
        items = self.items
        n = len(items)
        return items[(self.pos + rng.randrange(n)) % n]

    def load(self, values):
        self.items = []
        self.pos = 0
        if self.members is not None:
            self.members = set()
        for v in values:
            self.add(int(v))


def cone_pick(state, helpers, rng, k):
    """Connected victims grown from one seed (v2 ``_cone_pick`` on the witness DAG).

    Candidates are witness children of victims and witness parents whose every child is already
    a victim: removing a cone leaves a hole the rebuild can genuinely re-plan.
    """
    par = state.par
    kids = state.kids
    iset = state.iset
    tset = state.tset
    seed = rng.choice(helpers)
    vict = [seed]
    vs = {seed}
    while len(vict) < k:
        cand = set()
        for u in vict:
            a = par.get(u)
            if a is not None:
                for p in (a, u ^ a):
                    if p in iset or p in tset or p in vs:
                        continue
                    if all(c in vs for c in kids[p]):
                        cand.add(p)
            for c in kids[u]:
                if c not in tset and c not in vs:
                    cand.add(c)
        if not cand:
            break
        x = rng.choice(sorted(cand))
        vict.append(x)
        vs.add(x)
    return vict


def inject(victims, kept, inputs, rng, per_victim, per_input):
    """Candidates aimed at the hole (v2 ``_inject``): victim ^ kept, victim ^ input, victim pairs."""
    out = []
    nk = len(kept)
    ni = len(inputs)
    for v in victims:
        if nk:
            for _ in range(per_victim):
                out.append(v ^ kept[rng.randrange(nk)])
        for _ in range(per_input):
            out.append(v ^ inputs[rng.randrange(ni)])
    for i, a in enumerate(victims):
        for b in victims[i + 1:]:
            out.append(a ^ b)
    return out


@register
class LNSRebuild(Move):
    """Destroy (small / cone / big), bank, rebuild (greedy or deadline), peel."""
    name = "lns.rebuild"
    family = "lns"
    knobs = KNOBS

    def __init__(self, settings):
        super().__init__(settings)
        c = self.cfg
        self.ops = ("small", "cone", "big")
        self.op_w = (float(c.op_small), float(c.op_cone), float(c.op_big))
        self.small_p = [float(p) for p in c.small_p] or [1.0]
        self.cone = (int(c.cone_min), max(int(c.cone_min), int(c.cone_max)))
        self.big = (int(c.big_min), max(int(c.big_min), int(c.big_max)))
        self.inject_cone = int(c.inject_cone)
        self.inject_big = int(c.inject_big)
        self.inject_inputs = int(c.inject_inputs)
        self.draws = (int(c.draws_base), int(c.draws_extra))
        self.pair_inputs = bool(c.pair_inputs)
        self.hot_frac = float(c.hot_frac)
        self.extra_cost = int(c.extra_cost)
        self.vic_cost = int(c.vic_cost)
        self.strategy = c.strategy
        self.deadline_p = float(c.deadline_p)
        self.peel = c.peel == "full"
        self.peel_window = int(c.peel_window)
        self.peel_passes = float(c.peel_passes)
        self.pool_init = int(c.pool_init)
        self.peel_seen_max = int(c.peel_seen_max)
        rb = settings.view(REBUILD_KNOBS.path)
        self.noise = float(rb.noise)
        self.beam = DeadlineParams(rb, max_states=int(c.deadline_states))
        self.limit = trace_limit(settings)
        self.pool = _Ring(int(c.pool_limit), unique=True)
        self.hot = _Ring(int(c.hot_limit), unique=False)
        self.peel_seen = set()
        # (new, re-introduced, removed) values of the last proposal, absorbed into pool/hot at
        # the next call if the chain still shows exactly that change (i.e. it was accepted).
        self.pending = ((), (), ())

    # ------------------------------------------------------------------ move state
    def state(self) -> dict:
        return {"pool": self.pool.ordered(), "hot": self.hot.ordered(),
                "peel_seen": sorted(self.peel_seen),
                "pending": [list(p) for p in self.pending]}

    def load_state(self, data: dict) -> None:
        self.pool.load(data.get("pool", ()))
        self.hot.load(data.get("hot", ()))
        self.peel_seen = set(int(h) for h in data.get("peel_seen", ()))
        pend = data.get("pending") or ((), (), ())
        self.pending = tuple(tuple(int(v) for v in p) for p in pend)

    def _absorb(self, state, values, rng):
        """Fold the previous proposal into pool/hot if the chain kept it; seed an empty pool."""
        tri = state.tri
        new, back, gone = self.pending
        if new or back or gone:
            if all(v in tri for v in new) and not any(v in tri for v in gone):
                for v in new:
                    self.pool.add(v)
                for v in back:
                    self.hot.add(v)
            self.pending = ((), (), ())
        if not self.pool.items:
            add = self.pool.add
            for v in values:
                add(v)
            n = len(values)
            if n >= 2:
                for _ in range(self.pool_init):
                    m = values[rng.randrange(n)] ^ values[rng.randrange(n)]
                    if m.bit_count() > 1:
                        add(m)

    # ------------------------------------------------------------------ destroy
    def _destroy(self, state, helpers, rng):
        """(operator name, victims, injection per victim)."""
        n = len(helpers)
        total = sum(self.op_w)
        r = rng.random() * total
        op = self.ops[-1]
        for name, w in zip(self.ops, self.op_w):
            if r < w:
                op = name
                break
            r -= w
        if op == "small":
            r = rng.random() * sum(self.small_p)
            k = len(self.small_p)
            for i, p in enumerate(self.small_p):
                if r < p:
                    k = i + 1
                    break
                r -= p
            return op, rng.sample(helpers, min(k, n)), 0
        if op == "cone":
            k = min(n, rng.randint(*self.cone))
            return op, cone_pick(state, helpers, rng, k), self.inject_cone
        k = min(n, rng.randint(*self.big))
        return op, rng.sample(helpers, k), self.inject_big

    # ------------------------------------------------------------------ propose
    def propose(self, ctx):
        state = ctx.state
        rng = ctx.rng
        budget = ctx.budget
        work0 = budget.used
        iset = state.iset
        tri = state.tri
        values = state.values()
        self._absorb(state, values, rng)
        helpers = helpers_of(state)
        size0 = state.count()
        trace = {"components": [], "size_before": size0}
        if not helpers:
            trace["reason"] = "no_helpers"
            return Proposal(self.name, None, trace, budget.used - work0)

        # ---- destroy
        op, victims, per_victim = self._destroy(state, helpers, rng)
        vset = set(victims)
        kept = [v for v in values if v not in vset]
        trace["components"].append("destroy." + op)
        trace.update(op=op, k=len(victims), victims=clip(victims, self.limit))

        # ---- bank
        cand = []
        base, extra = self.draws
        draws = base + (rng.randrange(extra) if extra > 0 else 0)
        pool = self.pool
        hot = self.hot
        hot_frac = self.hot_frac
        for _ in range(draws):
            source = hot if hot.items and rng.random() < hot_frac else pool
            if source.items:
                cand.append(source.draw(rng))
        pop = kept + list(state.inputs) if self.pair_inputs else kept
        npop = len(pop)
        if npop >= 2:
            for _ in range(draws):
                cand.append(pop[rng.randrange(npop)] ^ pop[rng.randrange(npop)])
        if op in ("cone", "big"):
            cand.extend(inject(victims, kept, state.inputs, rng, per_victim, self.inject_inputs))
            trace["components"].append("inject")
        extras = sorted({m for m in cand if m.bit_count() > 1 and m not in tri})
        cost = dict.fromkeys(extras, self.extra_cost)
        for v in victims:
            cost[v] = self.vic_cost
        use_deadline = self.strategy == "deadline" or (
            self.strategy == "mixed" and op != "big" and rng.random() < self.deadline_p)
        incumbent = witness_recipes(state) if use_deadline else None
        trace["params"] = {"op": op, "k": len(victims), "draws": draws, "strategy": self.strategy,
                           "deadline": use_deadline, "vic_cost": self.vic_cost,
                           "extra_cost": self.extra_cost}
        before = state.key()
        journal = state.journal()
        add = state.add
        for m in extras:
            add(m)
        budget.tick(1 + len(extras))
        trace.update(draws=draws, extras=len(extras), bank=len(tri) - len(iset))
        trace["components"].append("bank")

        # ---- rebuild
        chosen = None
        source = None
        if self.strategy != "deadline":
            chosen = greedy(state, cost, rng, self.noise)
            trace["components"].append("rebuild.greedy")
            trace["greedy_size"] = None if chosen is None else len(chosen)
            source = "greedy"
        if use_deadline and not budget.exhausted():
            incs = [incumbent]
            if chosen is not None:
                incs.append(recipes_within(state, chosen))
            result, dstats = reconstruct(state, rng, self.beam, budget, cap=state.cap,
                                         preferred=cost, incumbents=incs)
            trace["components"].append("rebuild.deadline")
            trace["deadline_size"] = None if result is None else len(result)
            trace["deadline"] = dstats
            if result is not None and (chosen is None or len(result) <= len(chosen)):
                chosen = result
                source = "deadline"
        if chosen is None:
            state.rollback(journal)
            trace["reason"] = "rebuild_failed"
            return Proposal(self.name, None, trace, budget.used - work0)
        commit_choice(state, chosen)
        trace["rebuild"] = source

        # ---- peel a near miss once per distinct set
        size1 = state.count()
        if self.peel and size0 < size1 <= size0 + self.peel_window:
            h = hash(state.key())
            if h not in self.peel_seen:
                if len(self.peel_seen) >= self.peel_seen_max:
                    self.peel_seen.clear()
                self.peel_seen.add(h)
                work = int(self.peel_passes * (len(state.tri) - len(iset)))
                peel_budget = budget.child(work)
                state.peel(rng, peel_budget)
                budget.tick(peel_budget.used)
                trace["components"].append("peel")
                trace["peeled"] = size1 - state.count()
        after = state.key()
        if after == before:
            state.rollback(journal)
            trace["reason"] = "unchanged"
            return Proposal(self.name, None, trace, budget.used - work0)
        trace.update(diff_fields(after - before, before - after, self.limit))
        trace["size_after"] = state.count()
        self.pending = (tuple(sorted(after - before)), tuple(sorted(after - set(kept))),
                        tuple(sorted(before - after)))
        return Proposal(self.name, journal, trace, budget.used - work0)
