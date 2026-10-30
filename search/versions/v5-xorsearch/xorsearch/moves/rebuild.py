"""Rebuild strategies and shared state-edit helpers for the local moves.

Role in the method
------------------
LNS (``moves/lns.py``) and depth repair (``moves/depth.py``) end the same way: the chain's value
set U has been enlarged with candidate values (a *bank*), and a rebuild picks a subset of U that
realises every target within a depth deadline using as few values as possible.  The chosen subset
then replaces U (``commit_choice``).  Two strategies are provided:

``greedy``
    The kernel's top-down ``extract`` over earliest levels with pull-in cost classes (1 kept,
    2 candidate, 3 victim).  O(sum of degrees); 109 us on invmc88, 0.8 ms on fox_mu8.

``deadline``
    A port of v2 ``deadline_search.reconstruct`` onto the triple index.  Every demanded value gets
    a deadline that is propagated through the *chosen* recipes, so a slower shared construction is
    legal whenever it still meets the cap; the greedy extractor only ever allows a value's fastest
    recipes.  Evidence: v2 LNS with deadline rebuild led the framework engines (9 of 29 strict
    improvements) and the v2 89@4 / 90@4 records were "lns rebuild" events at deadline_p 0.4/0.25.

What changed from v2 (kernel-performance report section 2 and rule 4):

* recipe alternatives come from ``tri[v]`` lazily, only for values that become demanded (the v2
  O(n^2) alternatives loop was 18 ms of every 40 ms proposal on fox_mu8; x70 from the index);
* levels are the kernel's maintained earliest levels, so there is no normalise/_earliest pass;
* completion of a partial beam branch is incremental: the default fill layer (the best's recipes
  over the kernel witness, or the witness alone) is reference-counted once, and a completion only
  replays the chosen recipes that differ from it (``_Completer``, O(|chosen| + touched) instead
  of O(circuit)); only a count that beats the best is confirmed by a full DFS for cycles and
  depth, and only then is a value set materialised (v2 ``_emit`` from ``complete_partial`` was
  34% of v2-lns on invmc88);
* beam signatures are incremental XOR hashes instead of sorted tuples of whole dicts;
* the look-ahead score (sum of cheapest recipe costs of pending values) is updated from the values
  whose deadline or demand status changed instead of being recomputed over every pending value.

``reconstruct`` is a bounded heuristic, not an optimality solver.  Work is counted in beam states
and completions through ``Budget.tick`` so a call replays exactly from its RNG state.

Shared helpers used by walk, LNS and depth (``trace_limit``, ``clip``, ``value_diff``,
``helpers_of``, ``commit_choice``, ``local_peel``, ``recipes_within``) live here too, so the three move modules
share one definition of "trimmed state" and of the trace value lists.
"""
from __future__ import annotations

from ..config.schema import Knob, Section

KNOBS = Section("moves.rebuild", "Rebuild strategies shared by LNS and depth repair.", {
    "noise": Knob(0.0625, "Greedy extract: probability that a recipe's cost gets +1 (v2 _extract "
                  "used 1/16; it keeps the greedy from re-deriving the incumbent every time).",
                  min=0, max=1),
    "beam_width": Knob(6, "Deadline beam: branches kept per expansion level (v2 lanes used "
                       "4/6/8).", min=1),
    "max_states": Knob(800, "Deadline beam: child states examined per call (v2 deadline_states "
                       "800).", min=0),
    "lookahead": Knob(0.45, "Deadline beam: weight of the cheapest-completion estimate in a "
                      "branch score (v2 constant 0.45).", min=0),
    "complete_head": Knob(4, "Deadline beam: complete every child while states <= this many "
                          "beam widths (v2 used 4), so short calls still yield whole circuits.",
                          min=0),
    "complete_every": Knob(6, "Deadline beam: afterwards complete every this many states (v2 "
                           "used max(4, beam_width)).", min=1),
})

_INF = 1 << 30
# Used only when the full schema (with telemetry.trace_values_max) is not loaded, e.g. in unit
# tests built with for_sections(); never an algorithm parameter.
_TRACE_FALLBACK = 16


# --------------------------------------------------------------------------- shared helpers
def trace_limit(settings) -> int:
    """Maximum length of value lists in a trace (``telemetry.trace_values_max``)."""
    if settings is not None:
        value = settings.values.get("telemetry.trace_values_max")
        if value is not None:
            return int(value)
    return _TRACE_FALLBACK


def clip(values, limit: int) -> list:
    """Sorted list of at most ``limit`` values (traces stay small and JSON-safe)."""
    out = sorted(values)
    return out[:limit] if len(out) > limit else out


def value_diff(before, state, limit: int) -> dict:
    """Trace fields ``removed``/``added`` (clipped) plus their full counts.

    ``before`` is the non-input value set captured at proposal start (``state.key()``).
    """
    after = state.key()
    removed = before - after
    added = after - before
    return {"removed": clip(removed, limit), "added": clip(added, limit),
            "n_removed": len(removed), "n_added": len(added)}


def helpers_of(state) -> list:
    """Sorted non-input, non-target values: the values a move may remove.

    Sorted so every RNG draw over the list is independent of the kernel's dict/set history,
    which makes a proposal replay from (values, RNG state) alone.
    """
    iset = state.iset
    tset = state.tset
    return sorted(v for v in state.tri if v not in iset and v not in tset)


def commit_choice(state, chosen) -> None:
    """Replace U by inputs + ``chosen`` and trim (journaled by the caller).

    ``chosen`` must realise every target by itself (both strategies guarantee it); dropping the
    rest can only raise levels up to the construction the strategy found, so the cap still holds.
    """
    state.retain(chosen)
    state.trim()


def local_peel(state, w) -> int:
    """Drop witness operands made redundant by the new value ``w``; return how many went.

    Values with a recipe through w are its triple partners; their current witness operands are
    the values that may no longer be needed.  Each is removed on trial and kept out only if no
    target becomes stuck.  O(deg(w)) trial removals, deterministic.
    """
    tri = state.tri
    par = state.par
    iset = state.iset
    tset = state.tset
    partners = tri.get(w)
    if not partners:
        return 0
    cand = []
    for x in sorted(partners):
        for v in (x, w ^ x):
            a = par.get(v)
            if a is None:
                continue
            for p in (a, v ^ a):
                if p != w and p not in iset and p not in tset:
                    cand.append(p)
    dropped = 0
    remove = state.remove
    restore = state.restore
    for p in dict.fromkeys(cand):
        if p not in tri:
            continue
        undo = remove((p,))
        if tset.isdisjoint(undo.stuck):
            dropped += 1
        else:
            restore(undo)             # p is still needed: exact inverse of that remove
    return dropped


def recipes_within(state, chosen) -> dict:
    """``{v: a}`` recipes (v = a ^ (v ^ a)) of every value of ``chosen`` using only chosen values,
    inputs and strictly smaller earliest levels, as the greedy extractor built them."""
    level = state.level
    tri = state.tri
    iset = state.iset
    out = {}
    for v in chosen:
        lv = level.get(v)
        if lv is None:
            continue
        for a in sorted(tri[v]):
            b = v ^ a
            if (a in chosen or a in iset) and (b in chosen or b in iset):
                la = level.get(a)
                lb = level.get(b)
                if la is not None and lb is not None and la < lv and lb < lv:
                    out[v] = a
                    break
    return out


def witness_recipes(state) -> dict:
    """``{v: a}`` witness recipes of the live circuit (a valid construction within the cap)."""
    par = state.par
    return {v: par[v] for v in state.live()}


# --------------------------------------------------------------------------- greedy
def greedy(state, cost, rng, noise):
    """Kernel ``extract``: chosen value set over U, or None if a target is unrealised."""
    return state.extract(cost, rng, noise)


# --------------------------------------------------------------------------- deadline beam
class DeadlineParams:
    """The beam's parameters, read once from the ``moves.rebuild`` view."""
    __slots__ = ("beam_width", "max_states", "lookahead", "complete_head", "complete_every")

    def __init__(self, view, max_states=None):
        self.beam_width = int(view.beam_width)
        self.max_states = int(view.max_states if max_states is None else max_states)
        self.lookahead = float(view.lookahead)
        self.complete_head = int(view.complete_head)
        self.complete_every = int(view.complete_every)


def _evaluate(targets, chosen, inc, base, iset, cap):
    """Count the circuit of a layered recipe lookup; None if incomplete, cyclic or over cap.

    The recipe of v is ``chosen[v]``, else ``inc[v]``, else ``base[v]`` (the kernel witness).
    Returns ``(count, depth, recipes)`` with ``recipes`` = ``{v: a}`` for every live value.
    """
    dep = {}
    rec = {}
    grey = set()
    cget = chosen.get
    iget = inc.get if inc is not None else None
    bget = base.get
    top = 0
    for t in targets:
        if t in dep:
            continue
        stack = [t]
        while stack:
            v = stack[-1]
            if v in dep:
                stack.pop()
                continue
            a = cget(v)
            if a is None and iget is not None:
                a = iget(v)
            if a is None:
                a = bget(v)
                if a is None:
                    return None
            b = v ^ a
            if v in grey:
                # Both operands are finished: v's depth is final.
                da = 0 if a in iset else dep[a]
                db = 0 if b in iset else dep[b]
                d = 1 + (da if da > db else db)
                if d > cap:
                    return None
                dep[v] = d
                rec[v] = a
                if d > top:
                    top = d
                grey.discard(v)
                stack.pop()
                continue
            grey.add(v)
            for p in (a, b):
                if p not in iset and p not in dep:
                    if p in grey:          # p is an ancestor of v: the lookup has a cycle
                        return None
                    stack.append(p)
    return len(dep), top, rec


class _Completer:
    """Gate count of "chosen recipes over a fixed default layer" in O(|chosen| + touched).

    A beam completion fills every value without a chosen recipe from a default layer (the
    current best's recipes over the kernel witness, or the witness alone).  The default DAG and
    its reference counts (live parents using a value, plus one per target) are built once per
    layer; a completion only replays the chosen recipes that differ from the default, moving
    references from old to new operands and cascading when a value's count reaches or leaves
    zero.  Every value reachable from the targets keeps a positive count, so the result is an
    upper bound on the circuit size, exact unless a recipe cycle survives outside the circuit
    (its members keep each other counted).  An over-count can only hide a candidate, never accept
    a wrong one: a count that beats the best is confirmed by the full ``_evaluate`` (rarely
    needed, which is what makes completions cheap).  Checked against ``_evaluate`` on 5,521 real
    beam completions (Joltik, invmc88 LNS banks): no difference.
    """
    __slots__ = ("targets", "inc", "base", "iset", "ref", "count", "valid")

    def __init__(self, targets, inc, base, iset):
        self.targets = targets
        self.inc = inc
        self.base = base
        self.iset = iset
        ref = {}
        count = 0
        valid = True
        stack = []
        for t in targets:
            stack.append(t)
        while stack:
            x = stack.pop()
            if x in iset:
                continue
            r = ref.get(x, 0)
            ref[x] = r + 1
            if r:
                continue
            count += 1
            a = self.default(x)
            if a is None:
                valid = False
                break
            stack.append(a)
            stack.append(x ^ a)
        self.ref = ref
        self.count = count
        self.valid = valid

    def default(self, x):
        """Default-layer operand of x (incumbent recipe, else kernel witness), or None."""
        inc = self.inc
        if inc is not None:
            a = inc.get(x)
            if a is not None:
                return a
        return self.base.get(x)

    def count_with(self, chosen):
        """Upper bound (normally exact) on the gate count with ``chosen`` recipes overriding the
        layer; None if some value needed has no recipe at all."""
        if not self.valid:
            return None
        ref = self.ref
        iset = self.iset
        default = self.default
        delta = {}            # value -> reference count after this completion's edits
        counted = {}          # value -> operand whose references are currently counted
        n = self.count
        for v, a_new in chosen.items():
            if a_new == default(v):
                continue
            r = delta[v] if v in delta else ref.get(v, 0)
            if r == 0:
                continue      # not reachable (yet): its chosen recipe counts once reached
            a_old = counted.get(v)
            if a_old is None:
                a_old = default(v)
            if a_old == a_new:
                continue
            counted[v] = a_new
            # Add the new references first so shared operands never die transiently.
            stack = [a_new, v ^ a_new]
            while stack:
                x = stack.pop()
                if x in iset:
                    continue
                r = delta[x] if x in delta else ref.get(x, 0)
                delta[x] = r + 1
                if r:
                    continue
                n += 1
                a = chosen.get(x)
                if a is None:
                    a = default(x)
                    if a is None:
                        return None
                counted[x] = a
                stack.append(a)
                stack.append(x ^ a)
            stack = [a_old, v ^ a_old]
            while stack:
                x = stack.pop()
                if x in iset:
                    continue
                r = (delta[x] if x in delta else ref.get(x, 0)) - 1
                delta[x] = r
                if r:
                    continue
                n -= 1
                a = counted.pop(x, None)
                if a is None:
                    a = default(x)
                stack.append(a)
                stack.append(x ^ a)
        return n


def _reaches(chosen, starts, goal, iset):
    """True if ``goal`` is reachable from ``starts`` through chosen recipes (would make a cycle)."""
    stack = [p for p in starts if p not in iset]
    seen = set()
    while stack:
        u = stack.pop()
        if u == goal:
            return True
        if u in seen:
            continue
        seen.add(u)
        a = chosen.get(u)
        if a is not None:
            if a not in iset:
                stack.append(a)
            b = u ^ a
            if b not in iset:
                stack.append(b)
    return False


def reconstruct(state, rng, params, budget, cap=None, preferred=None, incumbents=()):
    """Deadline-aware beam reconstruction over the state's value set U.

    ``cap`` is the deadline of every target (None: the bank size, i.e. no depth restriction);
    it may be tighter than the state's own cap.  ``preferred`` maps values to ranking costs
    (default 1; it only steers ties, never the gate objective).  ``incumbents`` are ``{v: a}``
    recipe dicts of known valid constructions; the best of them and of the kernel's earliest
    witness is the starting best, and completions also try filling missing recipes from the
    current best.  Returns ``(chosen value set or None, stats)``; None means no target set
    meets ``cap`` from this bank.
    """
    level = state.level
    tri = state.tri
    iset = state.iset
    base = state.par
    targets = [t for t in state.targets if t not in iset and t != 0]
    deadline = cap if cap is not None else len(tri)
    stats = {"states": 0, "completions": 0, "improving": 0, "baseline": None,
             "gates": None, "state_limit": False, "budget_hit": False}
    for t in targets:
        lt = level.get(t)
        if lt is None or lt > deadline:
            return None, stats
    pref = preferred.get if preferred is not None else None

    # ---- starting best: earliest witness of the bank, then any better incumbent
    best = _evaluate(targets, {}, None, base, iset, deadline)
    for inc in incumbents:
        cand = _evaluate(targets, {}, inc, base, iset, deadline)
        if cand is not None and (best is None or (cand[0], cand[1]) < (best[0], best[1])):
            best = cand
    if best is None:
        return None, stats
    stats["baseline"] = best[0]
    if not targets or params.max_states <= 0:
        stats["gates"] = best[0]
        return set(best[2]), stats

    alts = {}

    def alts_of(m):
        """Sorted recipe pairs (x, y), x < y, of m over levelled values (memoised)."""
        r = alts.get(m)
        if r is None:
            r = []
            for x in tri[m]:
                y = m ^ x
                if x < y and x in level and y in level:
                    r.append((x, y))
            r.sort()
            alts[m] = r
        return r

    def mincost(m, needed):
        """Fewest new demands among m's recipes that meet m's deadline; None if none does."""
        lim = needed[m] - 1
        bestc = None
        for x, y in alts_of(m):
            if level[x] > lim or level[y] > lim:
                continue
            c = (x not in iset and x not in needed) + (y not in iset and y not in needed)
            if bestc is None or c < bestc:
                bestc = c
                if c == 0:
                    break
        return bestc

    def pref_of(m):
        return 1.0 if pref is None else float(pref(m, 1))

    # ---- root branch: every target demanded at the deadline
    needed0 = {t: deadline for t in targets}
    sig0 = 0
    for t in targets:
        sig0 ^= hash((1, t, deadline))
    mc0 = {}
    mcsum0 = 0
    for t in targets:
        c = mincost(t, needed0)
        if c is None:
            stats["gates"] = best[0]
            return set(best[2]), stats
        mc0[t] = c
        mcsum0 += c
    prefsum0 = sum(pref_of(t) for t in targets)
    beam = [({}, needed0, sig0, mc0, mcsum0, prefsum0)]
    seen = set()
    states = 0
    completions = 0
    improving = 0
    max_states = params.max_states
    width = params.beam_width
    lookahead = params.lookahead
    head = params.complete_head * width
    every = params.complete_every
    tick = budget.tick
    halted = False

    # Completion counters for the two fill layers (v2 complete_partial): the current best's
    # recipes over the witness, and the witness alone.  The best's layer is rebuilt on the rare
    # improvement.
    fill_base = _Completer(targets, None, base, iset)
    fill_best = _Completer(targets, best[2], base, iset)

    def consider(result):
        nonlocal best, improving, fill_best
        if result is not None and (result[0], result[1]) < (best[0], best[1]):
            best = result
            improving += 1
            fill_best = _Completer(targets, best[2], base, iset)

    def complete(chosen):
        """Fill ``chosen`` from both layers; fully evaluate only a count that beats the best."""
        for fill in (fill_best, fill_base):
            c = fill.count_with(chosen)
            if c is not None and c < best[0]:
                consider(_evaluate(targets, chosen, fill.inc, base, iset, deadline))

    while beam and states < max_states and not halted:
        next_beam = []
        for chosen, needed, sig, mc, mcsum, prefsum in beam:
            if states >= max_states or halted:
                break
            if not mc:
                completions += 1
                consider(_evaluate(targets, chosen, None, base, iset, deadline))
                continue
            # Tight-deadline, deep demands first: they expose infeasible branches early.
            value = min(mc, key=lambda m: (needed[m] - level[m], -level[m], m))
            pd = needed[value] - 1
            choices = [p for p in alts_of(value) if level[p[0]] <= pd and level[p[1]] <= pd]
            rng.shuffle(choices)

            def rank_pair(pair, needed=needed):
                x, y = pair
                c = 0
                s = 0.0
                if x not in iset and x not in needed:
                    c += 1
                    s += pref_of(x)
                if y not in iset and y not in needed:
                    c += 1
                    s += pref_of(y)
                lx = level[x]
                ly = level[y]
                return (c, s, lx if lx > ly else ly)

            choices.sort(key=rank_pair)
            for x, y in choices:
                if states >= max_states:
                    break
                states += 1
                if not tick():
                    halted = True
                    stats["budget_hit"] = True
                    break
                if _reaches(chosen, (x, y), value, iset):
                    continue
                # ---- extend: fix value's recipe, propagate deadlines through chosen recipes
                chosen2 = dict(chosen)
                chosen2[value] = x
                needed2 = dict(needed)
                sig2 = sig ^ hash((0, value, x))
                changed = []
                queue = [value]
                ok = True
                while queue and ok:
                    node = queue.pop()
                    an = chosen2.get(node)
                    if an is None:
                        continue
                    nd = needed2[node] - 1
                    for p in (an, node ^ an):
                        if p in iset:
                            if nd < 0:
                                ok = False
                                break
                            continue
                        lp = level.get(p)
                        if lp is None or lp > nd:
                            ok = False
                            break
                        prev = needed2.get(p)
                        if prev is None or nd < prev:
                            needed2[p] = nd
                            if prev is not None:
                                sig2 ^= hash((1, p, prev))
                            sig2 ^= hash((1, p, nd))
                            changed.append((p, prev))
                            if p in chosen2:
                                queue.append(p)
                if not ok:
                    continue
                # Every demanded value becomes a gate: a branch already demanding more than the
                # best circuit cannot win.
                if len(needed2) > best[0]:
                    continue
                if sig2 in seen:
                    continue
                seen.add(sig2)
                pending_left = len(needed2) - len(chosen2)
                if pending_left == 0:
                    completions += 1
                    consider(_evaluate(targets, chosen2, None, base, iset, deadline))
                    continue
                # Complete every shallow branch, then periodically: a whole-circuit candidate
                # from a short call is worth more than a deep unfinished branch.
                if states <= head or states % every == 0:
                    completions += 2
                    complete(chosen2)
                # ---- incremental look-ahead: only values whose deadline or operand demand
                # status changed can change their cheapest-recipe cost.
                mc2 = dict(mc)
                mcsum2 = mcsum - mc2.pop(value)
                prefsum2 = prefsum
                touch = []
                for p, prev in changed:
                    if p not in chosen2:
                        touch.append(p)
                    if prev is None:
                        prefsum2 += pref_of(p)
                        for q in tri[p]:
                            touch.append(q)
                            touch.append(p ^ q)
                for m in touch:
                    if m in chosen2 or m not in needed2:
                        continue
                    c = mincost(m, needed2)
                    if c is None:
                        ok = False
                        break
                    old = mc2.get(m)
                    if old is None:
                        mcsum2 += c
                    else:
                        mcsum2 += c - old
                    mc2[m] = c
                if not ok:
                    continue
                score = (len(needed2) + lookahead * mcsum2, len(needed2), prefsum2, rng.random())
                next_beam.append((score, chosen2, needed2, sig2, mc2, mcsum2, prefsum2))
        if halted:
            break
        next_beam.sort(key=lambda row: row[0])
        beam = [row[1:] for row in next_beam[:width]]
    stats.update(states=states, completions=completions, improving=improving,
                 gates=best[0], state_limit=states >= max_states)
    return set(best[2]), stats
