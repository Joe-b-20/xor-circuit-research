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
anneal3 is unchanged from v1 -- nothing in the campaign touched depth 3.
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


def _peel(mset, rng, cap):
    """Drop any non-target mask the rest of the set can do without."""
    s = list(mset); improved = True
    while improved:
        improved = False; idx = list(range(len(s))); rng.shuffle(idx)
        for i in idx:
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
    """Destroy part of the circuit, rebuild it, keep the result if the
    acceptance rule allows; peel and report every improvement.

    Knobs (see ladder_parallel.py LNS_KNOBS for the shipped values):
      op_mix        destroy operator mix, {"small"|"uniform"|"coneinj"|"biginj": w}
      kmax          victim count for the "uniform" operator (1..kmax)
      cone_lo/hi    victim count for "coneinj"   (connected cone + injection)
      biginj_lo/hi  victim count for "biginj"    (big random destroy + injection)
      kshake        every 997th iteration: a forced kshake..kshake+4 destroy
      nsamp         (base, extra) samples drawn from the pool and from kept sums
      hot_frac      fraction of pool draws taken from the hot (recently useful) list
      vic_cost      pull-in cost class of a destroyed victim (see _extract)
      peel_window   peel a rebuild that came out up to this many masks too big
      accept        "sa" (annealing with reheat) or "threshold" (the v1 rule)
      sa_T0/sa_cool/sa_reheat    annealing temperature, cooling, reheat patience
      up_prob/up_slack           the v1 threshold rule, used when accept != "sa"
      snapback      restart from best once cur drifts this far above it
      harvest_path  write distinct plateau states here (None = off)
      pop_glob/pop_period_s      cross-pollination source glob and cadence
    """
    rng = random.Random(seeds[0] if seeds else 1)
    if start_masks is None:
        start_masks = core.naive_masks()
    start = set(start_masks)
    if not feasible_at(start, cap):
        ctx.log("[lns] start circuit is NOT feasible at depth cap %s -- aborting stage"
                % (cap,))
        return
    op_mix = k.get("op_mix", {"small": 0.35, "coneinj": 0.45, "biginj": 0.20})
    ops, opw = list(op_mix.keys()), list(op_mix.values())
    cone_lo = k.get("cone_lo", 2); cone_hi = k.get("cone_hi", 4)
    biginj_lo = k.get("biginj_lo", 8); biginj_hi = k.get("biginj_hi", 16)
    hot_frac = k.get("hot_frac", 0.5)
    vic_cost = k.get("vic_cost", 3)
    peel_window = k.get("peel_window", 6)
    use_sa = k.get("accept", "sa") == "sa"
    sa_T0 = k.get("sa_T0", 1.2); sa_cool = k.get("sa_cool", 0.9997)
    sa_reheat = k.get("sa_reheat", 4000)
    harv = _Harvester(k.get("harvest_path"), k.get("pop_glob"),
                      k.get("pop_period_s", 120.0))

    # pool = current masks + all pairwise sums (weight>1)
    sol = list(start)
    S = set(sol)
    for a in sol:
        for b in sol:
            m = a ^ b
            if m and wt(m) > 1:
                S.add(m)
    pool = sorted(S)
    accumulate = set(pool)
    # hot list: masks a rebuild actually reintroduced. Sampling half the pool
    # draws from it concentrates the candidate set on masks that have already
    # proved useful here: ~11x accepted moves, 16-18x pool hit rate
    # (campaign: lns-pool).
    hot = []
    peel_seen = set()           # value-sets already peel-processed (peel is slow)

    def small_kk():
        """1-4 victims, biased small: the sweep measured that small destroys are
        the ones that actually rebuild and get accepted."""
        r = rng.random()
        if r < 0.45:
            return 1
        if r < 0.75:
            return 2
        if r < 0.90:
            return 3
        return 4

    info_cache = {"key": None, "info": None}

    def get_info():
        key = hash(frozenset(Ucur))
        if info_cache["key"] != key:
            info_cache["key"] = key
            info_cache["info"] = dag_info(Ucur)
        return info_cache["info"]

    Ucur = _peel(list(start), rng, cap)
    Ubest = list(Ucur)
    ctx.improve(indexpairs_from_masks(Ubest, cap), set(Ubest))
    harv.add(Ubest)
    t0 = time.time(); iters = 0
    Temp = sa_T0; last_record_it = 0
    n_peel_gain = 0; next_pop = harv.period_s
    while (time_limit is None or time.time() - t0 < time_limit) and \
          (target is None or len(Ubest) > target):
        iters += 1
        nu = len(Ucur)
        nontarget = [m for m in Ucur if m not in TSET]
        if not nontarget:
            break

        # ---------------- destroy (operator mix) ----------------
        extra_cand = []
        if iters % 997 == 0:
            kk = min(k["kshake"] + rng.randrange(5), len(nontarget))
            victims = rng.sample(nontarget, kk)
        else:
            op = rng.choices(ops, weights=opw)[0]
            if op == "small":
                victims = rng.sample(nontarget, min(small_kk(), len(nontarget)))
            elif op == "uniform":
                kk = min(1 + rng.randrange(k["kmax"]), len(nontarget))
                victims = rng.sample(nontarget, kk)
            elif op == "coneinj":
                kk = min(cone_lo + rng.randrange(cone_hi - cone_lo + 1),
                         len(nontarget))
                victims = _cone_pick(nontarget, rng, get_info(), kk)
                kept0 = [m for m in Ucur if m not in set(victims)]
                extra_cand = _inject(victims, kept0, rng)
            else:            # biginj: big destroy, only viable with peel-before-accept
                kk = min(biginj_lo + rng.randrange(biginj_hi - biginj_lo + 1),
                         len(nontarget))
                victims = rng.sample(nontarget, kk)
                kept0 = [m for m in Ucur if m not in set(victims)]
                extra_cand = _inject(victims, kept0, rng, per_victim=8)
        vset = set(victims)
        kept = [m for m in Ucur if m not in vset]; nkeep = len(kept)
        if nkeep == 0:
            continue

        # ---------------- rebuild candidates ----------------
        cand = list(kept)
        for _ in range(k["nsamp"][0] + rng.randrange(k["nsamp"][1])):
            if hot and rng.random() < hot_frac:
                cand.append(hot[rng.randrange(len(hot))])
            else:
                cand.append(pool[rng.randrange(len(pool))])
        for _ in range(k["nsamp"][0] + rng.randrange(k["nsamp"][1])):
            m = kept[rng.randrange(nkeep)] ^ kept[rng.randrange(nkeep)]
            if m:
                cand.append(m)
        cand.extend(extra_cand)
        cand.extend(victims)                 # victim-repool: rebuild never dead-ends
        seen = set(); C2 = []
        for m in cand:
            if m not in seen and wt(m) > 1:
                seen.add(m); C2.append(m)
        avail = list(INPUTS) + C2
        dep, pos = relax(avail)
        keptset = set(kept)
        cost_of = [0] * len(avail)
        for i in range(32, len(avail)):
            m = avail[i]
            cost_of[i] = 1 if m in keptset else (vic_cost if m in vset else 2)
        res = _extract(avail, dep, pos, cost_of, rng, cap)
        if res is None:
            continue
        r = len(res)

        # ---------------- peel before accepting a near miss ----------------
        # A rebuild that comes out a few masks too big is usually redundant, not
        # wrong: peeling recovered 2630 such rebuilds in a 2-minute probe that
        # the old code auto-rejected (campaign: lns-destroy).
        if nu < r <= nu + peel_window:
            fz = frozenset(res)
            if fz not in peel_seen:
                if len(peel_seen) < 200000:
                    peel_seen.add(fz)
                res2 = _peel(res, rng, cap)
                if len(res2) < r:
                    n_peel_gain += 1
                    res = res2; r = len(res)

        # ---------------- acceptance ----------------
        # SA with reheat: uphill moves are accepted on a cooling schedule, and
        # the temperature resets whenever a new best has gone missing for
        # sa_reheat iterations (campaign: acceptance-schedule; equal drift to
        # the kick-restart variant, and it composes with the cost classes).
        d = r - nu
        if use_sa:
            accept = d <= 0 or rng.random() < math.exp(-d / max(Temp, 1e-6))
            Temp *= sa_cool
            if iters - last_record_it > sa_reheat:
                Temp = sa_T0; last_record_it = iters
        else:
            accept = (d <= 0) or (d <= k["up_slack"] and rng.random() < k["up_prob"])
        if accept:
            for m in res:
                if m not in accumulate:
                    accumulate.add(m); pool.append(m)
                if m not in keptset and len(hot) < 200000:
                    hot.append(m)             # reintroduced by a rebuild: hot
            Ucur = res
            # Surface both fewer-gate AND equal-gate-shallower circuits to ctx.
            # ctx.improve applies the Pareto tie-break (accept iff fewer gates, or
            # equal gates at strictly lower depth), so an 89@5 found while the best
            # is 89@6 is no longer silently discarded.
            if len(Ucur) <= len(Ubest):
                fz = frozenset(Ucur)
                if fz in peel_seen:
                    cand2 = list(Ucur)
                else:
                    if len(peel_seen) < 200000:
                        peel_seen.add(fz)
                    cand2 = _peel(Ucur, rng, cap)
                    Ucur = cand2
                harv.add(cand2)
                if len(cand2) < len(Ubest):
                    Ubest = list(cand2); last_record_it = iters
                    ctx.improve(indexpairs_from_masks(cand2, cap), set(cand2),
                                note="it=%d" % iters)
                elif len(cand2) == len(Ubest):
                    if ctx.improve(indexpairs_from_masks(cand2, cap), set(cand2),
                                   note="depth-tiebreak it=%d" % iters):
                        Ubest = list(cand2)   # keep the shallower equal-gate set
        if len(Ucur) > len(Ubest) + k["snapback"]:
            Ucur = list(Ubest)
        if harv.glob_pat and time.time() - t0 >= next_pop:
            next_pop += harv.period_s
            n_new = harv.merge_into(pool, accumulate)
            if n_new:
                ctx.log("[lns] cross-pollinated %d masks (pool=%d)" % (n_new, len(pool)))
        if iters % 20000 == 0:
            ctx.log("[lns] %.0fs iters=%d cur=%d best=%d pool=%d hot=%d harv=%d peelgain=%d"
                    % (time.time() - t0, iters, len(Ucur), len(Ubest),
                       len(pool), len(hot), len(harv.seen), n_peel_gain))


# ==========================================================================
# ENGINE  "walk"  --  value-set remove-1 / remove-2-add-1 hub moves
# ==========================================================================
def _repair(S2, rng, avail=None, forbid=()):
    """Add ONE mask that makes S2 build all targets again -- by complete
    enumeration, not by guessing.

    Let A = closure(S2) and stuck = (S2 | TSET) - A.  A single mask w can only
    help if it is itself buildable now, i.e. w is a pair-sum of A, and w must
    unlock some stuck mask, so w = v ^ a for some stuck v and available a.
    Enumerating C = {v ^ a} intersected with the pair-sums of A therefore covers
    EVERY possible single-mask repair (campaign: repair-move); the v1 engine
    sampled random candidates and gave up after `tries`, which is why its 88
    plateau looked frozen -- exact repair made it move (~7x plateau mobility,
    and it is how all five 88s were reached).  `forbid` holds the masks just
    removed: re-adding one is a no-op ping-pong.  Among valid repairs, prefer
    the one that trims smallest, tie-broken by low weight then reuse."""
    if avail is None:
        avail, _, _ = closure(S2)
    if TSET <= avail:
        return S2
    stuck = (set(S2) | TSET) - avail
    al = list(avail); na = len(al)
    P2 = set()                             # all pair-sums of A, O(1) membership
    for i in range(na):
        a = al[i]
        for b in al[i + 1:]:
            P2.add(a ^ b)
    cands = set()                          # C ∩ P2 (complete; stuck ∩ P2 = empty)
    for v in stuck:
        for a in al:
            w = v ^ a
            if w in P2:
                cands.add(w)
    valid = []
    av = set(avail)                        # shared, rolled back per candidate
    for w in cands:
        if w in av or w in forbid:
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
    if not valid:
        return None
    if len(valid) == 1:
        return set(S2) | {valid[0]}
    reuse = {w: sum(1 for p in al if (w ^ p) in avail) for w in valid}
    rng.shuffle(valid)
    valid.sort(key=lambda w: (wt(w), -reuse[w]))
    scored = [(len(trim_masks(set(S2) | {w})), w) for w in valid[:4]]
    tmin = min(s for s, _ in scored)
    return set(S2) | {rng.choice([w for s, w in scored if s == tmin])}


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
    """Remove a mask (or two) and repair; keep any reduction that still builds
    all targets and (if a cap is set) stays within depth.

    Knobs (see ladder_parallel.py WALK_KNOBS for the shipped values):
      hub_move_p        probability of a remove-2-add-1 hub move
      close_hamming     half the hub moves pick a second victim within this
                        Hamming distance of the first
      plateau_slack_p   probability of accepting a +1 move near the best (drift)
      harvest_path      write distinct plateau states here (None = off)
    """
    rng = random.Random(seeds[0] if seeds else 1)
    if start_masks is None:
        start_masks = core.naive_masks()
    if cap is not None and not feasible_at(start_masks, cap):
        ctx.log("[walk] start not feasible at depth cap %s -- aborting stage" % cap)
        return

    def ok_cap(mset):
        return cap is None or feasible_at(mset, cap)

    harv = _Harvester(k.get("harvest_path"))
    cur = trim_masks(start_masks)
    if not ok_cap(cur):
        ctx.log("[walk] trimmed start exceeds depth cap -- aborting"); return
    best = set(cur)
    ctx.improve(_walk_gates(best, cap), set(best))
    harv.add(best)
    st = _WalkState(cur)
    t0 = time.time(); iters = 0
    while (time_limit is None or time.time() - t0 < time_limit) and \
          (target is None or len(best) > target):
        iters += 1
        nont = [v for v in cur if v not in TSET]
        if len(nont) < 2:
            break
        moved = False
        if rng.random() < k["hub_move_p"]:                 # remove-2-add-1
            v1 = rng.choice(nont)
            if rng.random() < 0.5:
                cand = [u for u in nont if u != v1 and wt(u ^ v1) <= k["close_hamming"]]
                v2 = rng.choice(cand) if cand else rng.choice([u for u in nont if u != v1])
            else:
                v2 = rng.choice([u for u in nont if u != v1])
            S2 = cur - {v1, v2}
            ok, avail2, _ = st.remove_query((v1, v2))
            if ok:
                nxt = trim_masks(S2)
                if ok_cap(nxt):
                    cur = nxt; moved = True
            else:
                fixed = _repair(S2, rng, avail2, forbid=(v1, v2))
                if fixed is not None:
                    nxt = trim_masks(fixed)
                    if len(nxt) < len(cur) and ok_cap(nxt):
                        cur = nxt; moved = True
        else:                                              # remove-1
            v = rng.choice(nont); S2 = cur - {v}
            ok, avail2, _ = st.remove_query((v,))
            if ok:
                nxt = trim_masks(S2)
                if ok_cap(nxt):
                    cur = nxt; moved = True
            else:
                fixed = _repair(S2, rng, avail2, forbid=(v,))
                if fixed is not None:
                    nxt = trim_masks(fixed)
                    slack = 1 if (rng.random() < k["plateau_slack_p"]
                                  and len(cur) < len(best) + 2) else 0
                    if len(nxt) <= len(cur) + slack and ok_cap(nxt):
                        cur = nxt; moved = True
        # Only an iteration that actually changed cur can produce a new
        # candidate; re-verifying an unchanged set was ~40% of v1's walk time.
        if moved:
            st.reset(cur)
            # Pareto tie-break: surface fewer-gate OR equal-gate-shallower to ctx.
            if len(cur) < len(best):
                best = set(cur)
                harv.add(best)
                ctx.improve(_walk_gates(best, cap), set(best), note="it=%d" % iters)
            elif len(cur) == len(best):
                harv.add(cur)
                if ctx.improve(_walk_gates(cur, cap), set(cur),
                               note="depth-tiebreak it=%d" % iters):
                    best = set(cur)
        if iters % 20000 == 0:
            ctx.log("[walk] %.0fs iters=%d cur=%d best=%d harv=%d" %
                    (time.time() - t0, iters, len(cur), len(best), len(harv.seen)))


# ==========================================================================
# ENGINE  "anneal3"  --  depth-3 partition annealer (from scratch)
# ==========================================================================
def engine_anneal3(start_masks, cap, target, time_limit, seeds, k, ctx):
    if cap not in (3, None):
        ctx.log("[anneal3] note: this engine only produces depth-3 circuits "
                "(ignoring cap=%s)" % cap)
    from itertools import combinations

    def gen_splits(t):
        bs = bits_of(t); S = set()
        if len(bs) == 7:
            for c in combinations(bs, 4):
                A = sum(1 << b for b in c); S.add((A, t ^ A))
        else:
            for c in combinations(bs, 4):
                A = sum(1 << b for b in c); S.add((A, t ^ A))
            for c in combinations(bs, 3):
                A = sum(1 << b for b in c); S.add((A, t ^ A))
            ext = [e for e in range(32) if not (t >> e) & 1]
            for c in combinations(bs, 3):
                base = sum(1 << b for b in c)
                for e in ext:
                    A = base | (1 << e); S.add((A, t ^ A))
        return sorted(S)

    SPLITS = [gen_splits(t) for t in T]
    PAIRINGS = {}

    def get_pairings(m):
        pr = PAIRINGS.get(m)
        if pr is None:
            bs = bits_of(m)
            if len(bs) == 3:
                pr = []
                for i in range(3):
                    r = [bs[j] for j in range(3) if j != i]
                    pr.append(((1 << r[0]) | (1 << r[1]),))
            else:
                a, b, c, d = bs
                pr = [((1 << a) | (1 << b), (1 << c) | (1 << d)),
                      ((1 << a) | (1 << c), (1 << b) | (1 << d)),
                      ((1 << a) | (1 << d), (1 << b) | (1 << c))]
            PAIRINGS[m] = pr
        return pr

    class State:
        __slots__ = ('rng', 'choice', 'big', 'pairs', 'pairing', 'cost')
        def __init__(s, seed):
            s.rng = random.Random(seed); s.choice = [None] * 32
            s.big = {}; s.pairs = {}; s.pairing = {}; s.cost = 32
            for o in range(32):
                s.set_choice(o, s.rng.randrange(len(SPLITS[o])))
        def pair_add(s, p):
            c = s.pairs.get(p, 0); s.pairs[p] = c + 1
            if c == 0: s.cost += 1
        def pair_del(s, p):
            c = s.pairs[p]
            if c == 1: del s.pairs[p]; s.cost -= 1
            else: s.pairs[p] = c - 1
        def _best_pairing(s, m):
            best = None; bestnew = 99; opts = get_pairings(m); n = len(opts)
            start = s.rng.randrange(n)
            for kk in range(n):
                pr = opts[(start + kk) % n]
                new = sum(1 for p in pr if s.pairs.get(p, 0) == 0)
                if new < bestnew: bestnew = new; best = pr
            return best
        def part_add(s, m):
            w = wt(m)
            if w == 1: return
            if w == 2: s.pair_add(m); return
            c = s.big.get(m, 0); s.big[m] = c + 1
            if c == 0:
                s.cost += 1; best = s._best_pairing(m); s.pairing[m] = best
                for p in best: s.pair_add(p)
        def part_del(s, m):
            w = wt(m)
            if w == 1: return
            if w == 2: s.pair_del(m); return
            c = s.big[m]
            if c == 1:
                del s.big[m]; s.cost -= 1
                for p in s.pairing[m]: s.pair_del(p)
                del s.pairing[m]
            else: s.big[m] = c - 1
        def set_choice(s, o, idx):
            old = s.choice[o]
            if old is not None:
                A, B = SPLITS[o][old]; s.part_del(A); s.part_del(B)
            s.choice[o] = idx
            if idx is not None:
                A, B = SPLITS[o][idx]; s.part_add(A); s.part_add(B)
        def repair(s, m):
            if m not in s.big: return
            for p in s.pairing[m]: s.pair_del(p)
            best = s._best_pairing(m); s.pairing[m] = best
            for p in best: s.pair_add(p)
        def delta_add(s, m):
            w = wt(m)
            if w == 1: return 0
            if w == 2: return 0 if s.pairs.get(m, 0) > 0 else 1
            if s.big.get(m, 0) > 0: return 0
            best = 3
            for pr in get_pairings(m):
                n = sum(1 for p in pr if s.pairs.get(p, 0) == 0)
                if n < best: best = n
            return 1 + best
        def greedy_rechoice(s, o):
            old = s.choice[o]; A, B = SPLITS[o][old]
            s.choice[o] = None; s.part_del(A); s.part_del(B)
            best = []; bestd = 999
            for idx, (A2, B2) in enumerate(SPLITS[o]):
                d = s.delta_add(A2) + s.delta_add(B2)
                if d < bestd: bestd = d; best = [idx]
                elif d == bestd: best.append(idx)
            idx = s.rng.choice(best); s.choice[o] = idx
            A2, B2 = SPLITS[o][idx]; s.part_add(A2); s.part_add(B2)
        def snapshot(s):
            return (list(s.choice), dict(s.pairing), s.cost)
        def _forced(s, m, pg):
            w = wt(m)
            if w == 1: return
            if w == 2: s.pair_add(m); return
            c = s.big.get(m, 0); s.big[m] = c + 1
            if c == 0:
                s.cost += 1; best = pg.get(m) or get_pairings(m)[0]; s.pairing[m] = best
                for p in best: s.pair_add(p)
        def restore(s, snap):
            ch, pg, _ = snap
            for o in range(32): s.set_choice(o, None)
            s.pairing = {}
            for o in range(32):
                idx = ch[o]; s.choice[o] = idx
                A, B = SPLITS[o][idx]; s._forced(A, pg); s._forced(B, pg)

    def descend(s):
        improved = True
        while improved:
            improved = False; order = list(range(32)); s.rng.shuffle(order)
            for o in order:
                c0 = s.cost; s.greedy_rechoice(o)
                if s.cost < c0: improved = True
            for m in list(s.big.keys()):
                if m in s.big:
                    c0 = s.cost; s.repair(m)
                    if s.cost < c0: improved = True

    def anneal(s, iters, T0, T1):
        rng = s.rng; best = s.snapshot()
        for it in range(iters):
            temp = T0 * (T1 / T0) ** (it / iters); r = rng.random()
            if r < 0.60:
                o = rng.randrange(32); old = s.choice[o]; c0 = s.cost
                idx = rng.randrange(len(SPLITS[o]))
                if idx == old: continue
                s.set_choice(o, idx); d = s.cost - c0
                if d > 0 and rng.random() > math.exp(-d / temp):
                    s.set_choice(o, old)
            elif r < 0.85:
                if s.big: s.repair(rng.choice(list(s.big.keys())))
            else:
                s.greedy_rechoice(rng.randrange(32))
            if s.cost < best[2]: best = s.snapshot()
        return best

    def kick(s, kk):
        for _ in range(kk):
            o = s.rng.randrange(32); s.set_choice(o, s.rng.randrange(len(SPLITS[o])))

    def emit(snap):
        choices, pairing, _ = snap
        pairing = {int(x): tuple(v) for x, v in pairing.items()}
        bigs = {}; pairs = set(); finals = []
        for o in range(32):
            A, B = SPLITS[o][choices[o]]; finals.append((T[o], A, B))
            for m in (A, B):
                w = wt(m)
                if w == 2: pairs.add(m)
                elif w >= 3 and m not in bigs:
                    bigs[m] = pairing.get(m) or get_pairings(m)[0]
        for m, pg in bigs.items():
            for p in pg: pairs.add(p)
        si = {(1 << b): b for b in range(32)}; gates = []
        def add(mask, am, bm):
            gates.append([si[am], si[bm]]); si[mask] = 32 + len(gates) - 1
        for p in sorted(pairs):
            i, j = bits_of(p); add(p, 1 << i, 1 << j)
        for m in sorted(bigs):
            pg = bigs[m]
            if wt(m) == 3:
                p = pg[0]; add(m, p, m ^ p)
            else:
                p1, p2 = pg; add(m, p1, p2)
        for t, A, B in finals:
            add(t, A, B)
        return gates

    def seed_stream():
        yielded = set()
        for sd in (seeds or [6]):
            yielded.add(sd); yield sd
        for sd in itertools.count(1):
            if sd not in yielded:
                yield sd

    t0 = time.time(); gbest = None
    for sd in seed_stream():
        if time_limit is not None and time.time() - t0 >= time_limit:
            break
        if target is not None and gbest is not None and gbest[2] <= target:
            break
        s = State(sd * 100003 + 17)
        b = anneal(s, k["anneal_iters"], k["sa_T0"], k["sa_T1"])
        s.restore(b); descend(s); cur = s.snapshot()
        deadline = INF if time_limit is None else t0 + time_limit
        for r in range(k["ils_rounds"]):
            if (r & 63) == 0 and time.time() > deadline: break
            if target is not None and cur[2] <= target: break
            s.restore(cur); kick(s, s.rng.randrange(2, 7)); descend(s)
            if s.cost <= cur[2]: cur = s.snapshot()
        if gbest is None or cur[2] < gbest[2]:
            gbest = cur
            gates = emit(gbest)
            sig = [1 << i for i in range(32)]
            for a, bb in gates: sig.append(sig[a] ^ sig[bb])
            ctx.improve(gates, set(sig[32:]), note="seed=%d" % sd)


ENGINES = {
    "lns": engine_lns,
    "walk": engine_walk,
    "anneal3": engine_anneal3,
}


def run_engine(name, start_masks, cap, target, time_limit, seeds, knobs, ctx):
    if name not in ENGINES:
        raise SystemExit("unknown engine %r (choose from %s)" % (name, list(ENGINES)))
    ENGINES[name](start_masks, cap, target, time_limit, seeds, knobs, ctx)
