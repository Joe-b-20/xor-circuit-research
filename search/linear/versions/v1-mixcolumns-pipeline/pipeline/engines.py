#!/usr/bin/env python3
"""
engines.py  --  the search engines used by the record hunter.

All engines minimise the number of 2-input XOR gates for AES MixColumns, with
an optional depth cap.  They share one interface (run_engine) and talk to the
run through a small `ctx` object:

    ctx.log(msg)                 -> write a line to console + log file
    ctx.improve(gates, masks)    -> verify the candidate; if valid AND smaller
                                    than the best so far, save it and log it.
                                    Returns True if it became the new best.

An engine never "claims" a gate count; it only ever proposes candidates to
ctx.improve, which verifies against the GF(2^8) oracle before anything is saved
or reported.

Engines
    "lns"     depth-capped large-neighbourhood re-synthesis (destroy & rebuild).
              General purpose; seedable; the main hunter for depth >= 4 and for
              reducing a warm-started circuit.
    "walk"    value-set local search (remove-1 + remove-2-add-1 hub moves).
              Seedable; good for unconstrained / high-depth reduction.
    "anneal3" depth-3 partition annealer (from scratch, depth fixed at 3).
              The reliable way to reach a low count at depth 3 from nothing.

The lns and walk engines here are the ones rebuilt during the 88-gate campaign
(raw archive: gitignored campaign_87/, curated archives: ../evidence/
campaign87_*).  Each mechanism carries a one-line note saying what it does and
what it measured; the shipped defaults ARE the measured-good configuration.
The October 2026 upgrade adds bounded deadline-aware reconstruction,
coordinated parent/core moves, joint depth-three construction, and explicit
trajectory checkpoints. Historical engines remain in the evidence archives.
New heuristics are experimental; only replayed circuits are records.
"""
import time, math, random, itertools, json, glob, os
import mixcolumns_core as core

T = core.TARGETS
TSET = core.TARGET_SET
INPUTS = core.INPUTS
ISET = core.INPUT_SET
bits_of = core.bits_of
wt = core.wt

INF = 1_000_000                # sentinel: mask not (yet) realizable from the set


def _tuple_tree(value):
    """Restore Random state after an ordinary JSON checkpoint roundtrip."""
    return tuple(_tuple_tree(x) for x in value) if isinstance(value, list) else value


def _saved_state(ctx, name, knobs):
    if not knobs.get("persist_state", True):
        return {}
    return getattr(ctx, "engine_states", {}).get(name, {}) or {}


def _resumed_rng(saved, seeds):
    rng = random.Random(seeds[0] if seeds else 1)
    if saved.get("rng_state") is not None:
        try:
            rng.setstate(_tuple_tree(saved["rng_state"]))
        except (TypeError, ValueError):
            pass                         # an incompatible old RNG is not a seed
    return rng


def _metric(ctx, key, amount=1):
    metrics = getattr(ctx, "metrics", None)
    if metrics is not None:
        metrics[key] = metrics.get(key, 0) + amount


def _halt(ctx, deadline):
    callback = getattr(ctx, "should_stop", None)
    return time.monotonic() >= deadline or bool(callback and callback())


def _checkpoint(ctx, name, current, best, rng, iterations, **extra):
    state = {"version": 2, "engine": name, "current_masks": sorted(current),
             "best_masks": sorted(best), "rng_state": rng.getstate(),
             "iterations": iterations}
    state.update(extra)
    states = getattr(ctx, "engine_states", None)
    if states is not None:
        states[name] = state
    callback = getattr(ctx, "checkpoint_engine", None)
    if callback is not None:
        callback(name, state)
    return state


def _trim_at_cap(mask_set, cap):
    """One live cap-valid witness, allowing unused/unreachable bank extras.

    Unlike ordinary closure trimming, the retained subset is selected from
    minimum-depth recipes. A cap-feasible bank cannot lose its shallow route
    merely because an arbitrary closure happened to choose a deeper recipe.
    This is a safe inexpensive fallback, not joint gate minimization.
    """
    bank = sorted(set(mask_set) - ISET - {0})
    avail = list(INPUTS) + bank
    dep, pos = relax(avail)
    if any(t not in pos or dep[pos[t]] >= INF or
           (cap is not None and dep[pos[t]] > cap) for t in T):
        return None
    needed = set(TSET) - ISET
    todo = list(needed)
    while todo:
        m = todo.pop()
        ds = dep[pos[m]]
        options = []
        for a in avail:
            b = m ^ a
            if a >= b or b not in pos:
                continue
            if dep[pos[a]] < ds and dep[pos[b]] < ds:
                extra = int(a not in ISET and a not in needed) + int(b not in ISET and b not in needed)
                options.append((extra, max(dep[pos[a]], dep[pos[b]]), a, b))
        if not options:
            return None
        _, _, a, b = min(options)
        for p in (a, b):
            if p not in ISET and p not in needed:
                needed.add(p); todo.append(p)
    return needed


def _bounded_pool(pool, required, limit):
    """Keep current values and the most recently useful vocabulary bounded."""
    required = sorted(set(required))
    limit = max(int(limit), len(required))
    if len(required) >= limit:
        return required
    selected = set(required); tail = []
    for value in reversed(pool):
        if value not in selected:
            selected.add(value); tail.append(value)
            if len(selected) >= limit:
                break
    return required + list(reversed(tail))


def _structured_candidate(current, cap, rng, knobs, ctx, kind, deadline):
    from structured_search import propose
    seconds = min(float(knobs.get("structured_seconds", .12)),
                  max(0., deadline - time.monotonic()))
    if seconds <= 0:
        return None
    stats = {}
    _metric(ctx, kind + ".calls")
    result = propose(set(current), cap, rng, max_seconds=seconds,
                     max_parent_edges=int(knobs.get("max_parent_edges", 6)),
                     root_trials=int(knobs.get("root_trials", 8)),
                     constructor_budget=float(knobs.get("constructor_seconds", .03)),
                     kind=kind, stats=stats)
    for key, value in stats.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            _metric(ctx, kind + "." + key, value)
    if result is None:
        _metric(ctx, kind + ".no_proposal")
        return None
    candidate = set(result["masks"])
    if not TSET <= candidate or not feasible_at(candidate, cap):
        _metric(ctx, kind + ".invalid_rejected")
        return None
    _metric(ctx, kind + ".constructible")
    if candidate != set(current):
        _metric(ctx, kind + ".changed")
    return candidate


# ==========================================================================
# Depth machinery shared by the lns/walk engines (min-depth + reconstruction)
# ==========================================================================
def relax_reference(avail):
    """Minimum XOR build-depth by the original O(passes * n^2) fixpoint.  Kept
    verbatim as the ground truth of what `relax` must compute, and used for the
    rare case `relax` cannot handle (a value-set containing duplicate masks)."""
    na = len(avail)
    pos = {m: i for i, m in enumerate(avail)}
    dep = [0] * 32 + [INF] * (na - 32)
    changed = True
    while changed:
        changed = False
        for i in range(32, na):
            cur = dep[i]
            if cur == 1:
                continue
            S = avail[i]; best = cur
            for j in range(na):
                dA = dep[j]
                if dA + 1 >= best:
                    continue
                B = S ^ avail[j]
                if B == 0 or B == S:
                    continue
                bi = pos.get(B)
                if bi is None:
                    continue
                nd = 1 + (dA if dA > dep[bi] else dep[bi])
                if nd < best:
                    best = nd
                    if best == 1:
                        break
            if best < cur:
                dep[i] = best; changed = True
    return dep, pos


def relax(avail):
    """Minimum XOR build-depth of every mask in `avail` (inputs depth 0).

    Level-BFS rewrite of relax_reference: masks are resolved one depth level at
    a time, so a mask is only ever tested against the level that could lower it
    instead of against the whole set on every pass.  Same least fixpoint --
    bit-identical 1500-iteration trajectories -- at 18.9x per call, and since
    relax runs inside every lns iteration that is 17.5x end-to-end lns
    (42.3 -> 739 it/s; campaign: relax-kernel): the single biggest throughput
    change in the engine.  Falls back to the reference on the rare
    duplicate-mask input, where the level frontier is not well defined."""
    na = len(avail)
    pos = {m: i for i, m in enumerate(avail)}
    if len(pos) != na:                       # duplicate masks: exact legacy path
        return relax_reference(avail)
    dep = [0] * 32 + [INF] * (na - 32)
    if na <= 32:
        return dep, pos
    resolved = set(avail[:32])
    frontier = avail[:32]
    unresolved = range(32, na)
    d = 1
    if avail[:32] == INPUTS:
        # level-1 shortcut: with the standard input singletons at depth 0, a
        # mask resolves at depth 1 iff wt == 2 (a ^ b, two inputs), or it is 0.
        still = []; newly = []
        for i in unresolved:
            S = avail[i]
            t = S & (S - 1)
            if S == 0 or (t != 0 and t & (t - 1) == 0):
                dep[i] = 1
                newly.append(S)
            else:
                still.append(i)
        if not still:
            return dep, pos
        resolved.update(newly)
        frontier = newly
        unresolved = still
        d = 2
    while frontier:
        still = []; newly = []
        for i in unresolved:
            S = avail[i]
            for a in frontier:
                if S ^ a in resolved:
                    dep[i] = d
                    newly.append(S)
                    break
            else:
                still.append(i)
        if not still:
            break
        resolved.update(newly)
        frontier = newly
        unresolved = still
        d += 1
    return dep, pos


def feasible_at(mask_set, cap):
    """True iff every mask in the set is realizable AND (if cap given) builds at
    depth <= cap.  cap=None means 'no depth limit' but the set must still be
    realizable.

    With cap=None the depth numbers are never read, so that case skips relax
    entirely and runs a plain realizability closure that bails out as soon as a
    round resolves nothing (campaign: relax-kernel).  cap=None is the regime the
    88-hunt runs in, and feasible_at is called once per peel step."""
    if cap is not None or not ISET.isdisjoint(mask_set):
        avail = list(INPUTS) + list(mask_set)
        dep, _ = relax(avail)
        for i in range(32, len(avail)):
            if dep[i] >= INF:                # not realizable from this set at all
                return False
            if cap is not None and dep[i] > cap:
                return False
        return True
    resolved = set(INPUTS)
    pending = []; frontier = []
    for S in mask_set:                       # round 1: wt == 2 (or 0) resolves
        t = S & (S - 1)
        if S == 0 or (t != 0 and t & (t - 1) == 0):
            frontier.append(S)
        else:
            pending.append(S)
    if pending and not frontier:
        return False
    resolved.update(frontier)
    while pending:
        still = []; newly = []
        for S in pending:
            for a in frontier:
                if S ^ a in resolved:
                    newly.append(S)
                    break
            else:
                still.append(S)
        if not newly:
            return False
        resolved.update(newly)
        frontier = newly
        pending = still
    return True


def order_by_depth(mask_set, cap):
    """Emit (mask, parentA, parentB) triples in depth order so the circuit
    respects the cap.  Requires feasible_at(mask_set, cap)."""
    avail = list(INPUTS) + list(mask_set)
    dep, pos = relax(avail)
    real = [dep[i] for i in range(32, len(avail))]
    if any(d >= INF for d in real):
        raise RuntimeError("value-set not realizable")
    top = cap if cap is not None else (max(real) if real else 0)
    out = []
    for lvl in range(1, top + 1):
        for i in range(32, len(avail)):
            if dep[i] != lvl:
                continue
            S = avail[i]; done = False
            for j in range(len(avail)):
                if dep[j] >= lvl:
                    continue
                B = S ^ avail[j]
                k = pos.get(B)
                if k is None or dep[k] >= lvl:
                    continue
                out.append((S, avail[j], B)); done = True; break
            if not done:
                raise RuntimeError("cannot realize mask %08x within depth" % S)
    return out


def indexpairs_from_masks(mask_set, cap):
    """Turn a value-set into index-pair gates the verifier accepts."""
    trip = order_by_depth(mask_set, cap)
    idx = {1 << i: i for i in range(32)}
    gates = []
    for (m, a, b) in trip:
        gates.append([idx[a], idx[b]])
        idx[m] = 32 + len(gates) - 1
    return gates


# ==========================================================================
# Value-set closure/trim shared by the walk engine
# ==========================================================================
def _closure_core(S, stop_at_targets=False):
    """Which masks of S can actually be built, in build order.

    Worklist rewrite of the original re-scan-everything fixpoint: a mask is only
    re-tested when a NEW mask it could pair with appears, i.e. O(|S|^2) instead
    of O(passes * |S| * |avail|) (campaign: closure-kernel).  Returns
    (avail, order, parents, remaining) with remaining = S - realized; with
    stop_at_targets it returns as soon as all 32 targets are available, which is
    all the caller needs for a feasibility verdict or a trim."""
    avail = set(INPUTS)
    order = []; parents = {}
    remaining = set(S) - avail
    tleft = len(TSET & remaining) if stop_at_targets else -1
    newly = []
    # seed: masks realizable from the inputs alone (= weight-2 masks; 0 is the
    # degenerate a^a case the naive loop also admits)
    for v in list(remaining):
        w = wt(v)
        if w == 2:
            lo = v & -v
            avail.add(v); remaining.discard(v)
            order.append(v); parents[v] = (lo, v ^ lo); newly.append(v)
        elif v == 0:
            avail.add(v); remaining.discard(v)
            order.append(v); parents[v] = (INPUTS[0], INPUTS[0]); newly.append(v)
    qi = 0
    while qi < len(newly) and remaining:
        u = newly[qi]; qi += 1
        hits = [v for v in remaining if (v ^ u) in avail]
        for v in hits:
            avail.add(v); remaining.discard(v)
            order.append(v); parents[v] = (u, v ^ u); newly.append(v)
            if tleft >= 0 and v in TSET:
                tleft -= 1
                if tleft == 0:
                    return avail, order, parents, remaining
    return avail, order, parents, remaining


def closure(S):
    avail, order, parents, _ = _closure_core(S)
    return avail, order, parents


def realizable(S):
    Sset = S if isinstance(S, (set, frozenset)) else set(S)
    if not TSET <= Sset:   # targets have weight 5/7, never inputs: must be in S
        return False
    avail, _, _, _ = _closure_core(Sset, stop_at_targets=True)
    return TSET <= avail


def trim_masks(S):
    """Keep only masks needed to reach the 32 targets."""
    avail, order, parents, _ = _closure_core(S, stop_at_targets=True)
    if not (TSET <= avail):
        return set(S)
    needed = set(); stack = list(TSET)
    while stack:
        v = stack.pop()
        if v in needed or v in ISET:
            continue
        needed.add(v); a, b = parents[v]; stack.append(a); stack.append(b)
    return needed


class _WalkState:
    """Incremental closure over the walk's current (realizable) mask set.

    A walk iteration asks "what breaks if I remove these one or two masks?".
    Recomputing the whole closure for that question is what the v1 walk did;
    here the recorded build order lets us mark only the masks whose derivation
    transitively used a removed mask and re-derive just those.  The answer is
    the exact least fixpoint of S - D.  With the improve-only-on-change fix in
    engine_walk it took the walk from 12.3 to 269 it/s in one process (21.9x;
    campaign: closure-kernel)."""
    __slots__ = ("S", "avail", "order", "parents")

    def __init__(self, cur):
        self.reset(cur)

    def reset(self, cur):
        self.S = set(cur)
        avail, order, parents, _ = _closure_core(self.S)
        self.avail = avail; self.order = order; self.parents = parents

    def remove_query(self, D):
        """Exact closure info for S - D.
        Returns (ok, avail2, unrealized):
          avail2     == closure(S - D)[0]
          unrealized == (S - D) - avail2
          ok         == TSET <= avail2."""
        aff = set(D)
        parents = self.parents
        for u in self.order:                     # topological, so one pass
            if u in aff:
                continue
            a, b = parents[u]
            if a in aff or b in aff:
                aff.add(u)
        avail2 = self.avail - aff
        remaining = aff.difference(D)
        newly = []
        base = list(avail2)
        for v in list(remaining):
            for a in base:
                if (v ^ a) in avail2:
                    avail2.add(v); remaining.discard(v); newly.append(v)
                    break
        qi = 0
        while qi < len(newly) and remaining:
            u = newly[qi]; qi += 1
            hits = [v for v in remaining if (v ^ u) in avail2]
            for v in hits:
                avail2.add(v); remaining.discard(v); newly.append(v)
        return TSET <= avail2, avail2, remaining


# ==========================================================================
# Plateau harvesting (shared by lns and walk)
# ==========================================================================
class _Harvester:
    """Record every DISTINCT best-size mask set the search visits.

    The campaign's knob sweep found that tuning cannot buy an improvement on
    this plateau, but that the search constantly walks over sibling circuits of
    the same size and throws them away (only a strictly better -- or equally
    sized but shallower -- circuit is ever exported).  Harvesting writes each
    distinct plateau state as one JSON mask list to <label>.pop.jsonl; the
    88-gate campaign collected ~139k distinct 88-gate states this way, and both
    new 88s were found inside such a harvesting run.

    With `glob_pat` set, merge_into() also feeds the masks of SIBLING workers'
    harvests into this worker's rebuild pool (cross-pollination).  That is off
    in the shipped configuration: it mixes the mask provenance of every worker
    in the run, and a circuit built from a pool containing imported masks is
    "derived from published work", not our own (the three provenance classes
    are defined in METHODS_INDEX.md, "Provenance classes").  Turn it on deliberately, for workers seeded from our own
    circuits only.
    """
    LIMIT = 300000                       # bound the in-memory dedupe set

    def __init__(self, path, glob_pat=None, period_s=120.0):
        self.path = path
        self.glob_pat = glob_pat
        self.period_s = period_s
        self.seen = set()
        self.offsets = {}                # per sibling file: bytes already read

    def add(self, mset):
        if self.path is None:
            return
        fz = frozenset(mset)
        if fz in self.seen or len(self.seen) >= self.LIMIT:
            return
        self.seen.add(fz)
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(sorted(mset)) + "\n")
        except OSError:                  # a full disk must not kill a hunt
            pass

    def merge_into(self, pool, accumulate):
        """Append unseen sibling masks to `pool`; returns how many are new."""
        n_new = 0
        for path in glob.glob(self.glob_pat):
            if self.path and os.path.abspath(path) == os.path.abspath(self.path):
                continue
            try:
                with open(path) as f:
                    f.seek(self.offsets.get(path, 0))
                    for line in f:
                        try:
                            ms = json.loads(line)
                        except ValueError:      # a half-written last line
                            continue
                        for m in ms:
                            if m and wt(m) > 1 and m not in accumulate:
                                accumulate.add(m); pool.append(m); n_new += 1
                    self.offsets[path] = f.tell()
            except OSError:
                continue
        return n_new


# ==========================================================================
# ENGINE  "lns"  --  depth-capped destroy & rebuild
# ==========================================================================
def _extract(avail, dep, pos, cost_of, rng, cap, noise=True):
    """Greedy top-down rebuild of all targets out of the candidate pool.

    `cost_of` is the per-index pull-in cost class (campaign: lns-extract): 1 for
    a mask the current solution already keeps, 2 for a sampled/injected
    candidate, 3 for a just-destroyed victim.  Giving victims a cost instead of
    excluding them means a rebuild can always fall back on what it destroyed, so
    an iteration never dead-ends -- that alone multiplied accepted moves by ~34x
    -- while the higher cost still pushes the rebuild to find something else."""
    na = len(avail)
    for t in T:
        i = pos.get(t)
        if i is None or dep[i] >= INF or (cap is not None and dep[i] > cap):
            return None
    inU = [False] * na; processed = [i < 32 for i in range(na)]
    for t in T:
        inU[pos[t]] = True
    while True:
        pick = -1; pd = -1
        for i in range(32, na):
            if inU[i] and not processed[i] and dep[i] > pd:
                pd = dep[i]; pick = i
        if pick < 0:
            break
        processed[pick] = True; S = avail[pick]; ds = dep[pick]
        bestc = 99; bi = bj = -1; nties = 0
        for j in range(na):
            if dep[j] >= ds:
                continue
            B = S ^ avail[j]; k = pos.get(B)
            if k is None or dep[k] >= ds or avail[j] > B:
                continue
            cst = 0
            if j >= 32 and not inU[j]:
                cst += cost_of[j]
            if k >= 32 and not inU[k]:
                cst += cost_of[k]
            if noise and rng.randrange(8) == 0:
                cst += rng.randrange(2)
            if cst < bestc:
                bestc = cst; bi = j; bj = k; nties = 1
            elif cst == bestc:
                nties += 1
                if rng.randrange(nties) == 0:
                    bi = j; bj = k
        if bi < 0:
            return None
        if bi >= 32:
            inU[bi] = True
        if bj >= 32:
            inU[bj] = True
    return [avail[i] for i in range(32, na) if inU[i]]


def _peel(mset, rng, cap, deadline=float("inf"), stop=None):
    """Drop any non-target mask the rest of the set can do without."""
    s = list(mset); improved = True
    while improved:
        if time.monotonic() >= deadline or (stop is not None and stop()):
            break
        improved = False; idx = list(range(len(s))); rng.shuffle(idx)
        for i in idx:
            if time.monotonic() >= deadline or (stop is not None and stop()):
                return s
            if i >= len(s) or s[i] in TSET:
                continue
            tmp = s[:i] + s[i + 1:]
            if feasible_at(tmp, cap):
                s = tmp; improved = True; break
    return s


def dag_info(Ucur):
    """The circuit shape behind a value-set: per-mask depth, canonical parents,
    fanout and children (campaign: lns-destroy).  Used to destroy a CONNECTED
    piece of the circuit rather than k unrelated masks."""
    avail = list(INPUTS) + list(Ucur)
    dep, pos = relax(avail)
    parents = {}
    for i in range(32, len(avail)):
        S = avail[i]; d = dep[i]
        for j in range(len(avail)):
            if dep[j] >= d:
                continue
            B = S ^ avail[j]
            kb = pos.get(B)
            if kb is None or dep[kb] >= d:
                continue
            parents[S] = (avail[j], B)
            break
    fan = {m: 0 for m in Ucur}
    children = {m: [] for m in Ucur}
    for m, (a, b) in parents.items():
        for p in (a, b):
            if p in fan:
                fan[p] += 1
                children[p].append(m)
    depth = {avail[i]: dep[i] for i in range(32, len(avail))}
    return depth, parents, fan, children


def _inject(victims, kept, rng, per_victim=6):
    """Repair candidates aimed at the hole just destroyed: shifted copies of
    each victim (v ^ kept, v ^ input) and victim pairwise sums (campaign:
    lns-destroy).  Without these the rebuild only ever sees the global pool and
    a big destroy has nothing local to rebuild from."""
    ex = []
    nk = len(kept)
    for v in victims:
        for _ in range(per_victim):
            m = v ^ kept[rng.randrange(nk)]
            if m and wt(m) > 1:
                ex.append(m)
        for _ in range(2):
            m = v ^ (1 << rng.randrange(32))
            if wt(m) > 1:
                ex.append(m)
    vl = list(victims)
    for i in range(len(vl)):
        for j in range(i + 1, len(vl)):
            m = vl[i] ^ vl[j]
            if m and wt(m) > 1:
                ex.append(m)
    return ex


def _cone_pick(nontarget, rng, info, kk):
    """Grow a connected victim set from one seed mask: children of victims, plus
    parents that feed nothing outside the set (campaign: lns-destroy).  Removing
    a cone leaves a hole the rebuild can genuinely re-plan; removing k random
    masks usually just gets them re-derived."""
    depth, parents, fan, children = info
    nts = set(nontarget)
    v = rng.choice(nontarget)
    vict = {v}
    for _ in range(kk * 3):
        if len(vict) >= kk:
            break
        cand = set()
        for u in vict:
            a, b = parents.get(u, (0, 0))
            for p in (a, b):
                if p in nts and p not in vict and \
                   all(c in vict for c in children.get(p, [])):
                    cand.add(p)                       # parent only feeding vict
            for c in children.get(u, []):
                if c in nts and c not in vict:
                    cand.add(c)                       # child of a victim
        cand -= vict
        if not cand:
            break
        vict.add(rng.choice(sorted(cand)))
    return list(vict)


def engine_lns(start_masks, cap, target, time_limit, seeds, k, ctx):
    """Bounded destroy/rebuild with deadline and coordinated-region proposals.

    The state returned (and periodically checkpointed) separates the current
    trajectory from its best result. Incoming start_masks is always the active
    handoff, while cached RNG, vocabulary, and temperature may be resumed.
    """
    saved = _saved_state(ctx, "lns", k)
    rng = _resumed_rng(saved, seeds)
    start = set(start_masks if start_masks is not None else core.naive_masks())
    if not TSET <= start or not feasible_at(start, cap):
        raise ValueError("lns start does not realize all targets at the depth cap")
    Ucur = list(_trim_at_cap(start, cap) or start)
    Ubest = list(Ucur)
    previous_best = saved.get("best_masks") or getattr(ctx, "best_masks", None)
    if previous_best is not None and len(previous_best) <= len(Ubest):
        old = set(previous_best)
        if TSET <= old and feasible_at(old, cap):
            Ubest = list(old)
    ctx.improve(indexpairs_from_masks(Ubest, cap), set(Ubest), note="lns entry")
    harv = _Harvester(k.get("harvest_path"), k.get("pop_glob"), k.get("pop_period_s", 120.))
    harv.LIMIT = int(k.get("harvest_limit", 10000))
    harv.add(Ucur)
    op_mix = k.get("op_mix", {"small": .35, "coneinj": .45, "biginj": .20})
    ops, opw = list(op_mix), list(op_mix.values())
    hot_frac = k.get("hot_frac", .5)
    pool_limit = int(k.get("pool_limit", 30000)); hot_limit = int(k.get("hot_limit", 4000))
    sol = list(Ucur)
    pool = list(saved.get("pool", ()))
    if not pool:
        pool = sorted({a ^ b for a in sol for b in sol if wt(a ^ b) > 1})
    pool = _bounded_pool(pool, sol, pool_limit)
    accumulate = set(pool)
    hot = [m for m in saved.get("hot", ()) if m in accumulate][-hot_limit:]
    peel_seen = set()
    iters = int(saved.get("iterations", 0)); local_iters = 0
    Temp = float(saved.get("temperature", k.get("sa_T0", 1.2)))
    last_record_it = int(saved.get("last_record_it", iters))
    sa_T0 = float(k.get("sa_T0", 1.2)); sa_cool = float(k.get("sa_cool", .9997))
    sa_reheat = int(k.get("sa_reheat", 4000))
    use_sa = k.get("accept", "sa") == "sa"
    t0 = time.monotonic()
    deadline = float("inf") if time_limit is None else t0 + max(0., float(time_limit))
    next_checkpoint = t0 + float(k.get("checkpoint_seconds", 10.))
    next_pop = t0 + harv.period_s
    checkpoint = None
    info_key = None; info = None

    def save_state():
        return _checkpoint(ctx, "lns", Ucur, Ubest, rng, iters,
                           pool=list(pool), hot=list(hot), temperature=Temp,
                           last_record_it=last_record_it)

    try:
        while not _halt(ctx, deadline) and (target is None or len(Ubest) > target):
            if k.get("max_iterations") is not None and local_iters >= int(k["max_iterations"]):
                break
            local_iters += 1; iters += 1
            _metric(ctx, "lns.iterations")
            nu = len(Ucur); curset = set(Ucur)
            nontarget = [m for m in Ucur if m not in TSET]
            if not nontarget:
                break
            res = None; operator = "rebuild"
            core_every = int(k.get("core_every", 0))
            tree_every = int(k.get("structured_every", 0))
            if core_every and iters % core_every == 0:
                operator = "cores"
                res = _structured_candidate(Ucur, cap, rng, k, ctx, operator, deadline)
            elif tree_every and iters % tree_every == 0:
                operator = "translate"
                res = _structured_candidate(Ucur, cap, rng, k, ctx, operator, deadline)
            keptset = curset
            if res is None:
                operator = "rebuild"
                extra_cand = []
                if iters % 997 == 0:
                    kk = min(int(k.get("kshake", 12)) + rng.randrange(5), len(nontarget))
                    victims = rng.sample(nontarget, kk)
                else:
                    op = rng.choices(ops, weights=opw)[0]
                    if op == "small":
                        rr = rng.random()
                        kk = 1 if rr < .45 else 2 if rr < .75 else 3 if rr < .90 else 4
                        victims = rng.sample(nontarget, min(kk, len(nontarget)))
                    elif op == "uniform":
                        victims = rng.sample(nontarget, min(1 + rng.randrange(int(k.get("kmax", 4))), len(nontarget)))
                    elif op == "coneinj":
                        key = frozenset(Ucur)
                        if key != info_key:
                            info = dag_info(Ucur); info_key = key
                        kk = min(rng.randint(int(k.get("cone_lo", 2)), int(k.get("cone_hi", 4))), len(nontarget))
                        victims = _cone_pick(nontarget, rng, info, kk)
                        kept0 = [m for m in Ucur if m not in set(victims)]
                        if kept0:
                            extra_cand = _inject(victims, kept0, rng)
                    else:
                        kk = min(rng.randint(int(k.get("biginj_lo", 8)), int(k.get("biginj_hi", 16))), len(nontarget))
                        victims = rng.sample(nontarget, kk)
                        kept0 = [m for m in Ucur if m not in set(victims)]
                        if kept0:
                            extra_cand = _inject(victims, kept0, rng, per_victim=8)
                vset = set(victims)
                kept = [m for m in Ucur if m not in vset]; keptset = set(kept)
                if not kept:
                    continue
                cand = list(kept)
                base, extra = k.get("nsamp", (12, 12))
                draws = int(base) + (rng.randrange(int(extra)) if int(extra) > 0 else 0)
                for _ in range(draws):
                    source = hot if hot and rng.random() < hot_frac else pool
                    if source:
                        cand.append(rng.choice(source))
                for _ in range(draws):
                    m = rng.choice(kept) ^ rng.choice(kept)
                    if m:
                        cand.append(m)
                cand.extend(extra_cand); cand.extend(victims)
                bank = list(dict.fromkeys(m for m in cand if wt(m) > 1))
                avail = list(INPUTS) + bank
                dep, pos = relax(avail)
                costs = [0] * 32 + [1 if m in keptset else int(k.get("vic_cost", 3)) if m in vset else 2 for m in bank]
                res = _extract(avail, dep, pos, costs, rng, cap)
                if rng.random() < float(k.get("deadline_rebuild_p", 0.)) and not _halt(ctx, deadline):
                    from deadline_search import reconstruct
                    _metric(ctx, "deadline.calls")
                    seconds = min(float(k.get("deadline_seconds", .04)), max(0., deadline - time.monotonic()))
                    rebuilt = reconstruct(bank, T, inputs=INPUTS, cap=cap,
                                          preferred={m: costs[32+i] for i, m in enumerate(bank)},
                                          rng=rng, max_seconds=seconds,
                                          beam_width=int(k.get("beam_width", 8)),
                                          max_states=int(k.get("deadline_states", 800)),
                                          fallback_masks=res or Ucur)
                    if rebuilt is not None:
                        candidate = set(rebuilt["masks"])
                        if TSET <= candidate and feasible_at(candidate, cap):
                            _metric(ctx, "deadline.valid")
                            if res is None or len(candidate) <= len(res):
                                if res is not None and len(candidate) < len(res):
                                    _metric(ctx, "deadline.improved_extraction")
                                res = list(candidate)
                        else:
                            _metric(ctx, "deadline.invalid_rejected")
            if res is None:
                _metric(ctx, "lns.rebuild_failed")
            else:
                res = list(res); r = len(res)
                if nu < r <= nu + int(k.get("peel_window", 6)) and not _halt(ctx, deadline):
                    fz = frozenset(res)
                    if fz not in peel_seen:
                        if len(peel_seen) >= 10000:
                            peel_seen.clear()
                        peel_seen.add(fz)
                        res = _peel(res, rng, cap, deadline=deadline,
                                    stop=getattr(ctx, "should_stop", None)); r = len(res)
                delta = r - nu
                if use_sa:
                    accept = delta <= 0 or rng.random() < math.exp(-delta / max(Temp, 1e-6))
                    Temp *= sa_cool
                    if iters - last_record_it > sa_reheat:
                        Temp = sa_T0; last_record_it = iters
                else:
                    accept = delta <= 0 or (delta <= int(k.get("up_slack", 4)) and rng.random() < float(k.get("up_prob", .5)))
                if accept:
                    _metric(ctx, "lns.accepted")
                    _metric(ctx, operator + ".accepted")
                    if delta > 0:
                        _metric(ctx, "lns.uphill")
                    if set(res) != curset:
                        _metric(ctx, "lns.changed")
                    for m in res:
                        if m not in accumulate:
                            accumulate.add(m); pool.append(m)
                        if m not in keptset:
                            hot.append(m)
                    if len(pool) > pool_limit:
                        pool = _bounded_pool(pool, res, pool_limit); accumulate = set(pool)
                    hot = hot[-hot_limit:]
                    Ucur = res
                    if len(Ucur) <= len(Ubest):
                        if not _halt(ctx, deadline):
                            Ucur = _peel(Ucur, rng, cap, deadline=deadline,
                                         stop=getattr(ctx, "should_stop", None))
                        harv.add(Ucur)
                        if len(Ucur) < len(Ubest):
                            Ubest = list(Ucur); last_record_it = iters
                            ctx.improve(indexpairs_from_masks(Ubest, cap), set(Ubest), note="lns %s it=%d" % (operator, iters))
                        elif ctx.improve(indexpairs_from_masks(Ucur, cap), set(Ucur), note="lns depth it=%d" % iters):
                            Ubest = list(Ucur)
                else:
                    _metric(ctx, operator + ".cost_rejected")
            if len(Ucur) > len(Ubest) + int(k.get("snapback", 12)):
                Ucur = list(Ubest); _metric(ctx, "lns.snapbacks")
            now = time.monotonic()
            if harv.glob_pat and now >= next_pop:
                next_pop = now + harv.period_s
                harv.merge_into(pool, accumulate)
                pool = _bounded_pool(pool, Ucur, pool_limit); accumulate = set(pool)
            if now >= next_checkpoint:
                checkpoint = save_state()
                next_checkpoint = now + float(k.get("checkpoint_seconds", 10.))
    finally:
        checkpoint = save_state()
    return checkpoint


# ==========================================================================
# ENGINE  "walk"  --  value-set remove-1 / remove-2-add-1 hub moves
# ==========================================================================
def _repair_candidates(S2, rng, avail=None, forbid=(), deadline=float("inf"), stop=None):
    """Enumerate all one-mask reachability repairs, unless interrupted.

    This retains the exact C-intersect-pair-sums enumeration of the original
    engine. Ranking and cap-aware selection are separate. An interrupted call
    returns the candidates checked so far and makes no completeness claim.
    """
    if avail is None:
        avail, _, _ = closure(S2)
    if TSET <= avail:
        return []
    stuck = (set(S2) | TSET) - avail
    al = sorted(avail); P2 = set()
    for i, a in enumerate(al):
        if time.monotonic() >= deadline or (stop is not None and stop()):
            return []
        for b in al[i + 1:]:
            P2.add(a ^ b)
    cands = {v ^ a for v in stuck for a in al if (v ^ a) in P2}
    valid = []; av = set(avail); forbidden = set(forbid)
    for w in sorted(cands):
        if time.monotonic() >= deadline or (stop is not None and stop()):
            break
        if w in av or w in forbidden or w == 0:
            continue
        added = [w]; av.add(w)
        rem = set(stuck); qi = 0
        while qi < len(added):
            x = added[qi]; qi += 1
            for v in list(rem):
                if (v ^ x) in av:
                    av.add(v); rem.discard(v); added.append(v)
        ok = not (rem & TSET)
        for x in added:
            av.discard(x)
        if ok:
            valid.append(w)
    reuse = {w: sum(1 for p in al if (w ^ p) in avail) for w in valid}
    rng.shuffle(valid)
    valid.sort(key=lambda w: (wt(w), -reuse[w]))
    return valid


def _repair(S2, rng, avail=None, forbid=(), cap=None, cap_aware=True,
            max_evaluations=32, deadline=float("inf"), stop=None, stats=None):
    """Select a repair after cap-valid construction, with bounded ranking.

    Candidate generation remains complete when uninterrupted. The selection
    budget is explicitly heuristic; candidates outside it are not certified
    impossible. Cap-invalid choices do not consume the successful-score quota.
    """
    stats = stats if stats is not None else {}
    if avail is None:
        avail, _, _ = closure(S2)
    trim = (lambda bank: _trim_at_cap(bank, cap)) if cap_aware and cap is not None else trim_masks
    if TSET <= avail:
        result = trim(S2)
        return result if result is not None and (cap is None or feasible_at(result, cap)) else None
    valid = _repair_candidates(S2, rng, avail, forbid, deadline, stop)
    stats["enumerated_repairs"] = stats.get("enumerated_repairs", 0) + len(valid)
    scored = []
    for index, w in enumerate(valid):
        if time.monotonic() >= deadline or (stop is not None and stop()):
            break
        if not cap_aware and index >= 4:
            break
        result = trim(set(S2) | {w})
        stats["scored_repairs"] = stats.get("scored_repairs", 0) + 1
        if result is None or (cap is not None and not feasible_at(result, cap)):
            stats["cap_rejected"] = stats.get("cap_rejected", 0) + 1
            continue
        scored.append(result)
        if len(scored) >= max(1, int(max_evaluations)):
            break
    if not scored:
        return None
    best_size = min(map(len, scored))
    return set(rng.choice([x for x in scored if len(x) == best_size]))


def _expand_repair(cur, rng, cap, max_seconds=.04, max_candidates=16,
                   victim=None, first_candidates=None, stop=None):
    """A real remove-one/add-two move, with both new values live.

    The first new value is built from the surviving closure. The second is an
    exact one-mask repair from that extended bank. A successful result can be
    one gate larger than cur; this is the expansion missing from the old walk.
    All accepted candidates are reconstructed and checked at the actual cap.
    """
    deadline = time.monotonic() + max(0., float(max_seconds))
    nont = sorted(set(cur) - TSET)
    if not nont:
        return None
    if victim is None:
        rng.shuffle(nont)
    else:
        nont = [victim] if victim in nont else []
    for removed in nont[:4]:
        if time.monotonic() >= deadline or (stop is not None and stop()):
            break
        reduced = set(cur) - {removed}
        available = closure(reduced)[0]
        if TSET <= available:
            continue
        if first_candidates is None:
            al = sorted(available)
            candidates = list({a ^ b for i, a in enumerate(al) for b in al[i+1:]
                               if wt(a ^ b) > 1 and (a ^ b) not in cur})
            rng.shuffle(candidates)
            stuck = (reduced | TSET) - available
            candidates.sort(key=lambda w: (-sum((v ^ w) in available for v in stuck), wt(w)))
            # Blend promising seeds and an unbiased tail so low weight does not
            # permanently restrict this bounded two-mask neighbourhood.
            head = candidates[:max(1, max_candidates // 2)]
            tail = candidates[len(head):]
            candidates = head + rng.sample(tail, min(len(tail), max_candidates - len(head)))
        else:
            candidates = list(first_candidates)[:max_candidates]
        for first in candidates:
            if time.monotonic() >= deadline or (stop is not None and stop()):
                return None
            if first in cur or first == 0:
                continue
            extended = reduced | {first}
            extended_available = closure(extended)[0]
            if first not in extended_available:
                continue
            seconds = _repair_candidates(extended, rng, extended_available,
                                         forbid=(removed,), deadline=deadline, stop=stop)
            for second in seconds:
                if time.monotonic() >= deadline or (stop is not None and stop()):
                    return None
                if second in cur or second == first:
                    continue
                proposed = extended | {second}
                result = _trim_at_cap(proposed, cap) if cap is not None else trim_masks(proposed)
                if result is None or first not in result or second not in result:
                    continue
                if len(result) <= len(cur) + 1 and TSET <= result and feasible_at(result, cap):
                    return result
    return None


def _walk_gates(mask_set, cap):
    """Index-pair gates for a mask set.  With cap=None any topological witness
    from the closure is a valid circuit and is ~50x cheaper than the min-depth
    relax ordering (campaign: closure-kernel); the depth then simply is what it
    is, and ctx.improve still oracle-verifies and Pareto-compares it."""
    if cap is not None:
        return indexpairs_from_masks(mask_set, cap)
    avail, order, parents, remaining = _closure_core(set(mask_set))
    if remaining:
        raise RuntimeError("value-set not realizable")
    idx = {1 << i: i for i in range(32)}
    gates = []
    for m in order:
        a, b = parents[m]
        gates.append([idx[a], idx[b]])
        idx[m] = 32 + len(gates) - 1
    return gates


def engine_walk(start_masks, cap, target, time_limit, seeds, k, ctx):
    """Plateau walk with cap-aware repairs, real expansion, and live handoff."""
    saved = _saved_state(ctx, "walk", k)
    rng = _resumed_rng(saved, seeds)
    start = set(start_masks if start_masks is not None else core.naive_masks())
    if not TSET <= start or not feasible_at(start, cap):
        raise ValueError("walk start does not realize all targets at the depth cap")
    cap_aware = bool(k.get("cap_aware_repair", True))
    trim = (lambda masks: _trim_at_cap(masks, cap)) if cap is not None and cap_aware else trim_masks
    cur = trim(start)
    if cur is None or not feasible_at(cur, cap):
        cur = set(start)
    best = set(cur)
    previous = saved.get("best_masks") or getattr(ctx, "best_masks", None)
    if previous is not None and len(previous) <= len(best):
        candidate = set(previous)
        if TSET <= candidate and feasible_at(candidate, cap):
            best = candidate
    ctx.improve(_walk_gates(best, cap), best, note="walk entry")
    harv = _Harvester(k.get("harvest_path")); harv.LIMIT = int(k.get("harvest_limit", 10000))
    harv.add(cur)
    st = _WalkState(cur)
    iters = int(saved.get("iterations", 0)); local_iters = 0
    t0 = time.monotonic()
    deadline = float("inf") if time_limit is None else t0 + max(0., float(time_limit))
    next_checkpoint = t0 + float(k.get("checkpoint_seconds", 10.))
    stop = getattr(ctx, "should_stop", None)

    def save_state():
        return _checkpoint(ctx, "walk", cur, best, rng, iters)

    try:
        while not _halt(ctx, deadline) and (target is None or len(best) > target):
            if k.get("max_iterations") is not None and local_iters >= int(k["max_iterations"]):
                break
            local_iters += 1; iters += 1; _metric(ctx, "walk.iterations")
            nont = sorted(cur - TSET)
            if not nont:
                break
            oldcur = set(cur); nxt = None; operator = "remove_one"
            structured_every = int(k.get("structured_every", 0))
            core_every = int(k.get("core_every", 0))
            if core_every and iters % core_every == 0:
                operator = "cores"
                nxt = _structured_candidate(cur, cap, rng, k, ctx, operator, deadline)
            elif structured_every and iters % structured_every == 0:
                operator = "translate"
                nxt = _structured_candidate(cur, cap, rng, k, ctx, operator, deadline)
            elif rng.random() < float(k.get("expansion_p", 0.)):
                operator = "expansion"; _metric(ctx, "expansion.calls")
                nxt = _expand_repair(cur, rng, cap,
                                     max_seconds=min(float(k.get("expansion_seconds", .04)), max(0., deadline-time.monotonic())),
                                     max_candidates=int(k.get("expansion_candidates", 16)), stop=stop)
                if nxt is not None:
                    _metric(ctx, "expansion.constructible")
            else:
                victims = [rng.choice(nont)]
                if len(nont) >= 2 and rng.random() < float(k.get("hub_move_p", .3)):
                    operator = "hub"
                    v1 = victims[0]
                    close = [u for u in nont if u != v1 and wt(u ^ v1) <= int(k.get("close_hamming", 8))]
                    choices = close if close and rng.random() < .5 else [u for u in nont if u != v1]
                    victims.append(rng.choice(choices))
                reduced = cur - set(victims)
                ok, available, _ = st.remove_query(victims)
                if ok:
                    nxt = trim(reduced)
                else:
                    stats = {}
                    nxt = _repair(reduced, rng, available, forbid=victims, cap=cap,
                                  cap_aware=cap_aware,
                                  max_evaluations=int(k.get("repair_candidates", 16)),
                                  deadline=deadline, stop=stop, stats=stats)
                    for key, value in stats.items():
                        _metric(ctx, "repair." + key, value)
            if nxt is not None:
                nxt = set(nxt)
                if not TSET <= nxt or not feasible_at(nxt, cap):
                    _metric(ctx, operator + ".invalid_rejected")
                else:
                    delta = len(nxt) - len(cur)
                    accept = delta <= 0
                    if operator == "hub":
                        accept = delta < 0
                    if delta == 1 and operator in ("expansion", "translate", "cores"):
                        accept = (len(cur) < len(best) + int(k.get("walk_drift", 2)) and
                                  rng.random() < float(k.get("plateau_slack_p", .15)))
                    if accept and nxt != cur:
                        cur = nxt; st.reset(cur)
                        _metric(ctx, "walk.accepted"); _metric(ctx, operator + ".accepted")
                        if delta > 0:
                            _metric(ctx, "walk.uphill")
                        if len(cur) < len(best):
                            best = set(cur); harv.add(best)
                            ctx.improve(_walk_gates(cur, cap), cur, note="walk %s it=%d" % (operator, iters))
                        elif len(cur) == len(best):
                            harv.add(cur)
                            if ctx.improve(_walk_gates(cur, cap), cur, note="walk depth it=%d" % iters):
                                best = set(cur)
                    elif not accept:
                        _metric(ctx, operator + ".cost_rejected")
            reschedule_every = int(k.get("reschedule_every", 256))
            if cap is None and reschedule_every and iters % reschedule_every == 0 and len(cur) <= len(best):
                _metric(ctx, "walk.reschedules")
                if ctx.improve(indexpairs_from_masks(cur, None), cur, note="walk exact depth it=%d" % iters):
                    best = set(cur)
            now = time.monotonic()
            if now >= next_checkpoint:
                save_state(); next_checkpoint = now + float(k.get("checkpoint_seconds", 10.))
    finally:
        result = save_state()
    return result


# ==========================================================================
# ENGINE  "anneal3"  --  depth-3 partition annealer (from scratch)
# ==========================================================================
def engine_anneal3(start_masks, cap, target, time_limit, seeds, k, ctx):
    """Depth-three search with warm starts and bounded joint output repair.

    All legal W5/W7 final split types remain available. Joint moves choose a
    small output group, vary its splits together, and minimize the *union* of
    its constructor pairs against the actual retained outside pair bank.
    """
    if cap not in (3, None):
        raise ValueError("anneal3 requires depth cap 3 or none")
    saved = _saved_state(ctx, "anneal3", k)
    rng = _resumed_rng(saved, seeds)
    t0 = time.monotonic()
    deadline = float("inf") if time_limit is None else t0 + max(0., float(time_limit))
    from itertools import combinations

    def gen_splits(t):
        bs = bits_of(t); result = set()
        for size in ((4,) if len(bs) == 7 else (4, 3)):
            for chosen in combinations(bs, size):
                a = sum(1 << bit for bit in chosen)
                result.add((a, t ^ a))
        if len(bs) == 5:
            for chosen in combinations(bs, 3):
                base = sum(1 << bit for bit in chosen)
                for bit in range(32):
                    if not (t >> bit) & 1:
                        a = base | (1 << bit)
                        result.add((a, t ^ a))
        return sorted(result)

    SPLITS = [gen_splits(t) for t in T]
    split_index = [{frozenset(pair): i for i, pair in enumerate(options)} for options in SPLITS]
    PAIRINGS = {}

    def get_pairings(m):
        if m not in PAIRINGS:
            bs = bits_of(m)
            if len(bs) == 3:
                PAIRINGS[m] = [tuple([m ^ (1 << bit)]) for bit in bs]
            elif len(bs) == 4:
                a, b, c, d = [1 << bit for bit in bs]
                PAIRINGS[m] = [(a | b, c | d), (a | c, b | d), (a | d, b | c)]
            else:
                raise ValueError("depth-three large parent must have weight 3 or 4")
        return PAIRINGS[m]

    class State:
        def __init__(self):
            self.choice = [None] * len(T); self.big = {}; self.pairs = {}
            self.pairing = {}; self.cost = len(T)
        def pair_add(self, p):
            count = self.pairs.get(p, 0); self.pairs[p] = count + 1
            if count == 0: self.cost += 1
        def pair_del(self, p):
            count = self.pairs[p]
            if count == 1: del self.pairs[p]; self.cost -= 1
            else: self.pairs[p] = count - 1
        def best_pairing(self, m):
            options = list(get_pairings(m)); rng.shuffle(options)
            return min(options, key=lambda pr: sum(p not in self.pairs for p in pr))
        def part_add(self, m, forced=None):
            weight = wt(m)
            if weight == 1: return
            if weight == 2: self.pair_add(m); return
            count = self.big.get(m, 0); self.big[m] = count + 1
            if count == 0:
                self.cost += 1
                pairing = forced if forced is not None else self.best_pairing(m)
                self.pairing[m] = tuple(pairing)
                for p in pairing: self.pair_add(p)
        def part_del(self, m):
            weight = wt(m)
            if weight == 1: return
            if weight == 2: self.pair_del(m); return
            count = self.big[m]
            if count == 1:
                del self.big[m]; self.cost -= 1
                for p in self.pairing.pop(m): self.pair_del(p)
            else: self.big[m] = count - 1
        def set_choice(self, o, idx):
            old = self.choice[o]
            if old is not None:
                for m in SPLITS[o][old]: self.part_del(m)
            self.choice[o] = idx
            if idx is not None:
                for m in SPLITS[o][idx]: self.part_add(m)
        def repair(self, m):
            if m not in self.big: return
            for p in self.pairing[m]: self.pair_del(p)
            chosen = self.best_pairing(m); self.pairing[m] = chosen
            for p in chosen: self.pair_add(p)
        def delta_add(self, m):
            weight = wt(m)
            if weight == 1: return 0
            if weight == 2: return int(m not in self.pairs)
            if m in self.big: return 0
            return 1 + min(sum(p not in self.pairs for p in pr) for pr in get_pairings(m))
        def greedy_rechoice(self, o):
            self.set_choice(o, None)
            candidates = list(range(len(SPLITS[o]))); rng.shuffle(candidates)
            chosen = min(candidates, key=lambda i: sum(self.delta_add(m) for m in SPLITS[o][i]))
            self.set_choice(o, chosen)
        def snapshot(self):
            return (list(self.choice), dict(self.pairing), self.cost)
        def restore(self, snapshot):
            choices, pairings, _ = snapshot
            pairings = {int(m): tuple(v) for m, v in pairings.items()}
            self.choice = [None] * len(T); self.big = {}; self.pairs = {}; self.pairing = {}; self.cost = len(T)
            for o, idx in enumerate(choices):
                if idx is None: continue
                self.choice[o] = idx
                for m in SPLITS[o][idx]: self.part_add(m, pairings.get(m))
        def masks(self):
            return set(self.big) | set(self.pairs) | set(TSET)

    def decode_masks(mask_set):
        if not TSET <= set(mask_set) or not feasible_at(mask_set, 3):
            return None
        triples = order_by_depth(mask_set, 3)
        recipes = {m: (a, b) for m, a, b in triples}
        choices = []; pairing = {}
        for o, t in enumerate(T):
            key = frozenset(recipes[t])
            if key not in split_index[o]:
                return None
            idx = split_index[o][key]; choices.append(idx)
            for m in SPLITS[o][idx]:
                if wt(m) >= 3:
                    a, b = recipes[m]
                    pr = tuple(x for x in (a, b) if wt(x) == 2)
                    if not any(set(pr) == set(option) for option in get_pairings(m)):
                        return None
                    pairing[m] = pr
        return (choices, pairing, len(mask_set))

    def emit(state):
        index = {1 << bit: bit for bit in range(32)}; gates = []
        def add(m, a, b):
            if m in index: return
            gates.append([index[a], index[b]]); index[m] = 31 + len(gates)
        for p in sorted(state.pairs):
            a = p & -p; add(p, a, p ^ a)
        for m in sorted(state.big):
            pr = state.pairing[m]
            a = pr[0]; b = m ^ a
            add(m, a, b)
        for o, t in enumerate(T):
            a, b = SPLITS[o][state.choice[o]]; add(t, a, b)
        return gates

    def joint_update(state):
        """Small beam of joint split assignments + exact/bounded pair union."""
        from deadline_search import optimize_depth3
        started = time.monotonic()
        joint_deadline = min(deadline, started + float(k.get("joint_seconds", .04)))
        old = state.snapshot()
        group_size = max(2, min(int(k.get("joint_outputs", 3)), len(T)))
        seed = rng.randrange(len(T)); group = [seed]
        seedparents = set(SPLITS[seed][state.choice[seed]])
        others = [o for o in range(len(T)) if o != seed]
        rng.shuffle(others)
        others.sort(key=lambda o: -len(seedparents & set(SPLITS[o][state.choice[o]])))
        group += others[:group_size-1]
        outside_big = set(); outside_pairs = set()
        for o in range(len(T)):
            if o in group: continue
            for m in SPLITS[o][state.choice[o]]:
                if wt(m) == 2: outside_pairs.add(m)
                elif wt(m) >= 3: outside_big.add(m); outside_pairs.update(state.pairing[m])
        menus = {}
        count = max(2, int(k.get("joint_split_candidates", 6)))
        for o in group:
            options = list(range(len(SPLITS[o]))); rng.shuffle(options)
            options.sort(key=lambda i: sum(state.delta_add(m) for m in SPLITS[o][i]))
            chosen = [state.choice[o]] + options[:max(1, count-2)]
            remainder = [i for i in options if i not in chosen]
            if remainder: chosen += rng.sample(remainder, min(2, len(remainder)))
            menus[o] = list(dict.fromkeys(chosen))
        beam = [({}, set(), set())]
        for o in group:
            expanded = []
            for assignment, bigs, directs in beam:
                for idx in menus[o]:
                    newbig = set(bigs); newdirect = set(directs)
                    for m in SPLITS[o][idx]:
                        if wt(m) >= 3: newbig.add(m)
                        elif wt(m) == 2: newdirect.add(m)
                    newassignment = dict(assignment); newassignment[o] = idx
                    score = len(newbig - outside_big) + len(newdirect - outside_pairs)
                    expanded.append((score, rng.random(), newassignment, newbig, newdirect))
            expanded.sort(key=lambda row: row[:2])
            beam = [(a, b, d) for _, _, a, b, d in expanded[:max(1, int(k.get("joint_beam", 8)))]]
        # Always include the current split choice as a constructor-only joint
        # opportunity, even if the cheap split beam ranked it outside the cap.
        baseline_assign = {o: state.choice[o] for o in group}
        if not any(a == baseline_assign for a, _, _ in beam):
            beam.insert(0, (baseline_assign, set(), set()))
        best = old; best_cost = state.cost
        _metric(ctx, "joint.calls")
        for bi, (assignment, _, _) in enumerate(beam):
            if _halt(ctx, joint_deadline): break
            selected_parents = {m for o, idx in assignment.items() for m in SPLITS[o][idx]}
            parents_to_build = selected_parents - outside_big
            seconds = max(0., joint_deadline - time.monotonic()) / max(1, min(4, len(beam)-bi))
            result = optimize_depth3(parents_to_build, existing_pairs=outside_pairs,
                                     rng=rng, max_seconds=seconds,
                                     max_nodes=int(k.get("joint_nodes", 1500)))
            if result is None: continue
            _metric(ctx, "joint.constructible")
            if result.get("complete"): _metric(ctx, "joint.complete_local")
            pairings = {m: state.pairing[m] for m in outside_big}
            for m in selected_parents - outside_big:
                if wt(m) >= 3:
                    a, b = result["recipes"][m]
                    pairings[m] = tuple(x for x in (a, b) if wt(x) == 2)
            choices = list(state.choice)
            for o, idx in assignment.items(): choices[o] = idx
            allbig = outside_big | {m for m in selected_parents if wt(m) >= 3}
            allpairs = outside_pairs | set(result["pairs"])
            cost = len(T) + len(allbig) + len(allpairs)
            if cost < best_cost or (cost == best_cost and rng.random() < .5):
                best = (choices, pairings, cost); best_cost = cost
        state.restore(best)
        if state.cost < old[2]: _metric(ctx, "joint.improved")
        if state.choice != old[0] or state.pairing != old[1]: _metric(ctx, "joint.changed")

    state = State()
    initial = None
    if start_masks is not None:
        initial = decode_masks(set(start_masks))
        if initial is None:
            raise ValueError("anneal3 warm start is not a valid depth-three mask set")
    elif saved.get("snapshot"):
        sn = saved["snapshot"]
        initial = (sn["choices"], sn["pairing"], sn["cost"])
    if initial is not None:
        state.restore(initial)
    else:
        for o in range(len(T)): state.set_choice(o, rng.randrange(len(SPLITS[o])))
    best = state.masks(); best_snapshot = state.snapshot()
    old_best = saved.get("best_masks") or getattr(ctx, "best_masks", None)
    if old_best is not None and len(old_best) < len(best):
        decoded = decode_masks(set(old_best))
        if decoded is not None:
            best = set(old_best); best_snapshot = decoded
    ctx.improve(indexpairs_from_masks(best, 3), best, note="anneal3 entry")
    iters = int(saved.get("iterations", 0)); local_iters = 0
    last_improvement = int(saved.get("last_improvement", iters))
    next_checkpoint = time.monotonic() + float(k.get("checkpoint_seconds", 10.))
    sa_T0 = max(1e-6, float(k.get("sa_T0", 2.)))
    sa_T1 = max(1e-6, float(k.get("sa_T1", .05)))
    period = max(1, int(k.get("anneal_iters", 150000)))

    def save_state():
        snap = state.snapshot()
        return _checkpoint(ctx, "anneal3", state.masks(), best, rng, iters,
                           snapshot={"choices": snap[0], "pairing": {str(m): list(pr) for m, pr in snap[1].items()}, "cost": snap[2]},
                           last_improvement=last_improvement)

    try:
        while not _halt(ctx, deadline) and (target is None or len(best) > target):
            if k.get("max_iterations") is not None and local_iters >= int(k["max_iterations"]): break
            local_iters += 1; iters += 1; _metric(ctx, "anneal3.iterations")
            before = state.snapshot()
            temp = sa_T0 * (sa_T1 / sa_T0) ** ((iters % period) / period)
            joint_every = int(k.get("joint_every", 0))
            structured_every = int(k.get("structured_every", 0))
            core_every = int(k.get("core_every", 0))
            kick_every = int(k.get("kick_every", 257))
            if core_every and iters % core_every == 0:
                proposal = _structured_candidate(state.masks(), 3, rng, k, ctx, "cores", deadline)
                if proposal is not None:
                    decoded = decode_masks(proposal)
                    if decoded is not None: state.restore(decoded)
            elif structured_every and iters % structured_every == 0:
                proposal = _structured_candidate(state.masks(), 3, rng, k, ctx, "translate", deadline)
                if proposal is not None:
                    decoded = decode_masks(proposal)
                    if decoded is not None: state.restore(decoded)
            elif joint_every and iters % joint_every == 0:
                joint_update(state)
            elif kick_every and iters % kick_every == 0:
                for _ in range(rng.randint(2, 6)):
                    o = rng.randrange(len(T)); state.set_choice(o, rng.randrange(len(SPLITS[o])))
                order = list(range(len(T))); rng.shuffle(order)
                for o in order:
                    if _halt(ctx, deadline): break
                    state.greedy_rechoice(o)
            else:
                r = rng.random()
                if r < .6:
                    o = rng.randrange(len(T)); state.set_choice(o, rng.randrange(len(SPLITS[o])))
                elif r < .85 and state.big:
                    state.repair(rng.choice(list(state.big)))
                else:
                    state.greedy_rechoice(rng.randrange(len(T)))
            delta = state.cost - before[2]
            if delta > 0 and rng.random() > math.exp(-delta / temp):
                state.restore(before)
            else:
                _metric(ctx, "anneal3.accepted")
                if delta > 0: _metric(ctx, "anneal3.uphill")
            if state.cost < len(best):
                candidate = state.masks(); gates = emit(state)
                if len(gates) != state.cost:
                    raise AssertionError("depth-three accounting disagrees with physical gate count")
                ctx.improve(gates, candidate, note="anneal3 it=%d" % iters)
                best = candidate; best_snapshot = state.snapshot(); last_improvement = iters
            patience = int(k.get("restart_patience", 50000))
            if patience and iters - last_improvement >= patience:
                state.restore(best_snapshot); last_improvement = iters
                _metric(ctx, "anneal3.snapbacks")
            now = time.monotonic()
            if now >= next_checkpoint:
                save_state(); next_checkpoint = now + float(k.get("checkpoint_seconds", 10.))
    finally:
        result = save_state()
    return result


ENGINES = {
    "lns": engine_lns,
    "walk": engine_walk,
    "anneal3": engine_anneal3,
}


def run_engine(name, start_masks, cap, target, time_limit, seeds, knobs, ctx):
    if name not in ENGINES:
        raise SystemExit("unknown engine %r (choose from %s)" % (name, list(ENGINES)))
    return ENGINES[name](start_masks, cap, target, time_limit, seeds, knobs, ctx)
