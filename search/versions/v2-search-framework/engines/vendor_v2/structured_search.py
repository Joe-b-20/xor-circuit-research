"""Bounded, algebraically coordinated XOR-circuit proposals.

``translate`` moves output-parent roles together.  An edge partition may give
different copies of an old shared parent different XOR translations, thereby
changing the sharing topology.  ``cores`` simultaneously reconstructs several
triple / weight-five values through pair / quartet cores.  Both operations
construct a complete chronological witness, keep all outside consumers, and
then price its actual live gate union.

These are heuristic proposal families, not completeness or optimality claims.
The generic LNS / walk remain responsible for other forms of cancellation,
output reuse, arbitrary masks, and unrestricted-depth exploration.
"""

from __future__ import annotations

import itertools
import random
import time
from collections import defaultdict

from .deadline_search import earliest_witness, optimize_depth3, reconstruct


class _BudgetExpired(Exception):
    pass


def _check_time(deadline):
    if time.monotonic() >= deadline:
        raise _BudgetExpired


def _bits(mask):
    out = []
    while mask:
        bit = mask & -mask
        out.append(bit)
        mask ^= bit
    return out


def _ceil_log2(weight):
    return (weight - 1).bit_length() if weight > 0 else 0


def _finish(recipes, targets, inputs, cap=None):
    """Prune and replay a fixed recipe DAG, rejecting cycles and bad equations.

    Every gate which still serves an outside output is retained by the DFS.
    Existing masks are never assumed to have zero physical construction cost.
    """
    inputs = list(inputs)
    if len(set(inputs)) != len(inputs) or 0 in inputs:
        return None
    index = {m: i for i, m in enumerate(inputs)}
    depths = {m: 0 for m in inputs}
    active = set()
    gates = []
    live_recipes = {}

    def visit(mask):
        if mask in index:
            return True
        if mask == 0 or mask in active or mask not in recipes:
            return False
        a, b = recipes[mask]
        if a == b or a ^ b != mask:
            return False
        active.add(mask)
        if not visit(a) or not visit(b):
            active.discard(mask)
            return False
        active.remove(mask)
        d = 1 + max(depths[a], depths[b])
        if cap is not None and d > cap:
            return False
        gates.append([index[a], index[b]])
        index[mask] = len(inputs) + len(gates) - 1
        depths[mask] = d
        live_recipes[mask] = (a, b)
        return True

    try:
        if not all(visit(t) for t in targets):
            return None
    except (RecursionError, KeyError, TypeError, ValueError):
        return None
    return {"masks": set(live_recipes), "gates": gates,
            "depths": depths, "recipes": live_recipes,
            "outputSignals": [index[t] for t in targets]}


def parent_edges(recipes, targets):
    """Return (target mask, left parent mask, right parent mask) edges."""
    return [(t, *recipes[t]) for t in targets if t in recipes]


def edge_components(edges):
    """Connected components of an edge-labelled parent graph."""
    at = defaultdict(list)
    for i, (_, a, b) in enumerate(edges):
        at[a].append(i)
        at[b].append(i)
    unseen = set(range(len(edges)))
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        todo = [first]
        group = []
        while todo:
            i = todo.pop()
            group.append(edges[i])
            for v in edges[i][1:]:
                for j in at[v]:
                    if j in unseen:
                        unseen.remove(j)
                        todo.append(j)
        components.append(group)
    return components


def translated_output_recipes(groups, deltas):
    """Translate both parent roles of each retained output edge.

    A shared vertex in different groups is a separate logical role, so unequal
    deltas split it.  Equal resulting masks across groups merge roles.  Every
    selected output edge must occur exactly once.  This function establishes
    the XOR identities only; ``_finish`` establishes an executable circuit.
    """
    if len(groups) != len(deltas):
        raise ValueError("one translation is required for each edge group")
    out = {}
    for group, delta in zip(groups, deltas):
        if (not isinstance(delta, int) or isinstance(delta, bool)
                or not 0 <= delta < (1 << 32)):
            raise ValueError("translations must be unsigned 32-bit integer masks")
        for target, a, b in group:
            if any(not isinstance(m, int) or isinstance(m, bool)
                   or not 0 < m < (1 << 32) for m in (target, a, b)):
                raise ValueError("edge masks must be nonzero unsigned 32-bit integers")
            if target in out or a ^ b != target:
                raise ValueError("edges must be valid and have unique targets")
            na, nb = a ^ delta, b ^ delta
            if not na or not nb or na == nb:
                return None
            out[target] = (na, nb)
    return out


def _connected_subset(edges, limit, rng):
    """Grow an edge subset without assuming a path-shaped component."""
    if len(edges) <= limit:
        return list(edges)
    remaining = list(edges)
    selected = [remaining.pop(rng.randrange(len(remaining)))]
    vertices = set(selected[0][1:])
    while remaining and len(selected) < limit:
        choices = [i for i, e in enumerate(remaining)
                   if e[1] in vertices or e[2] in vertices]
        if not choices:
            break
        edge = remaining.pop(rng.choice(choices))
        selected.append(edge)
        vertices.update(edge[1:])
    return selected


def _partition_edges(edges, rng):
    """Partition edges while retaining every output equation.

    The first group is a connected prefix.  The remainder is split into its
    connected components, duplicating boundary parent roles where necessary.
    """
    if len(edges) < 2:
        return [list(edges)]
    n = rng.randrange(1, len(edges))
    first = _connected_subset(edges, n, rng)
    first_targets = {e[0] for e in first}
    rest = [e for e in edges if e[0] not in first_targets]
    return [first] + edge_components(rest)


def _choose_delta(vertices, anchors, known, cap, rng):
    """Rank aligned root choices by inexpensive, explicitly heuristic costs.

    The full gate ledger is evaluated later.  This ranking prevents a large
    majority of depth-capped calls being spent on algebraic families whose
    parents are already too heavy to arrive in time.
    """
    max_weight = (1 << (cap - 1)) if cap is not None and cap > 0 else None
    deltas = {v ^ a for v in vertices for a in anchors}
    deltas.discard(0)
    ranked = []
    for delta in deltas:
        proposed = [v ^ delta for v in vertices]
        if 0 in proposed:
            continue
        if max_weight is not None and any(v.bit_count() > max_weight for v in proposed):
            continue
        fresh = [v for v in proposed if v not in known]
        score = (len(fresh), sum(max(1, v.bit_count() - 1) for v in fresh))
        ranked.append((score, delta))
    if not ranked:
        return None
    rng.shuffle(ranked)
    ranked.sort(key=lambda item: item[0])
    # Retain broad exploration; the score is not a necessary-condition filter.
    return rng.choice(ranked if rng.random() < .12 else ranked[:8])[1]


def _outside_values(recipes, targets, cut_values, inputs):
    """Values required outside a cut, with cut values treated as exits."""
    inputs = set(inputs)
    needed = set()
    todo = list(targets)
    while todo:
        value = todo.pop()
        if value in inputs or value in needed:
            continue
        needed.add(value)
        if value not in cut_values and value in recipes:
            todo.extend(recipes[value])
    return needed


def _unaffected_values(recipes, inputs, changed):
    """Existing signals whose old constructions do not depend on changed roots."""
    safe = set(inputs)
    pending = set(recipes) - set(changed)
    while pending:
        newly = {m for m in pending if all(p in safe for p in recipes[m])}
        if not newly:
            break
        safe.update(newly)
        pending -= newly
    return safe


def _raw_splits(mask, rng, limit=16):
    """Bounded support partitions; larger/cancelling recipes come from reuse."""
    bits = _bits(mask)
    n = len(bits)
    if n < 2:
        return []
    out = set()
    if n <= 5:
        for k in range(1, n // 2 + 1):
            for comb in itertools.combinations(bits, k):
                a = sum(comb)
                out.add(tuple(sorted((a, mask ^ a))))
    else:
        work = list(bits)
        for _ in range(limit):
            rng.shuffle(work)
            k = n // 2 if rng.random() < .75 else rng.randrange(1, n)
            a = sum(work[:k])
            out.add(tuple(sorted((a, mask ^ a))))
    ans = list(out)
    rng.shuffle(ans)
    return ans[:limit]


def _build_translated(witness, overrides, targets, inputs, cap, rng,
                      deadline, max_new=96):
    """Supply new parent values, then reconstruct every affected outside user.

    Existing unaffected values may be reused, but their entire old ancestry
    remains in ``recipes`` and is charged if live.  A changed output may also
    be used as a parent: recursion follows its *new* equation and checks cycles.
    """
    old = witness["recipes"]
    recipes = dict(old)
    recipes.update(overrides)
    safe = _unaffected_values(old, inputs, overrides)
    depths = {m: witness["depths"][m] for m in safe}
    input_set = set(inputs)
    computing = set()
    calls = 0
    parent_deadline = (cap - 1) if cap is not None else len(old) + max_new + 1
    if parent_deadline < 0:
        return None

    # Prepare small demanded parents jointly.  This explicitly generates their
    # missing pair constructors, rather than putting unbuildable masks in a pool.
    demands = {p for ab in overrides.values() for p in ab}
    small = {p for p in demands if 2 <= p.bit_count() <= 4
             and p not in overrides}
    outside = _outside_values(old, targets, set(overrides), inputs)
    free_pairs = {m for m in outside if m.bit_count() == 2}
    if small and parent_deadline >= 2:
        remaining = deadline - time.monotonic()
        if remaining > .002:
            joint = optimize_depth3(small, existing_pairs=free_pairs, rng=rng,
                                    max_seconds=min(.012, remaining * .2),
                                    max_nodes=1000)
            if joint is not None:
                # Solver recipes are physical XORs of raw inputs / pairs.
                for m, ab in joint.get("recipes", {}).items():
                    if m not in input_set and m not in overrides:
                        recipes[m] = tuple(ab)
                        safe.discard(m)
                        depths.pop(m, None)

    def ensure(mask, latest):
        nonlocal calls
        calls += 1
        if calls % 8 == 0:
            _check_time(deadline)
        if mask == 0 or latest < 0 or mask in computing:
            return False
        if mask in input_set:
            return True
        if mask in depths and depths[mask] <= latest:
            return True
        if latest == 0 or len(set(recipes) - set(old)) > max_new:
            return False
        if mask.bit_count() > (1 << min(latest, 32)):
            return False
        computing.add(mask)
        forced = mask in overrides
        choices = []
        if mask in recipes:
            choices.append(tuple(recipes[mask]))
        if not forced:
            usable = [m for m, d in depths.items()
                      if d < latest and m not in computing]
            rng.shuffle(usable)
            usable_set = set(usable)
            # Exact reuse and one-known-plus-new-complement, including foreign
            # cancellation when it makes a manageable complement.
            for a in usable:
                b = mask ^ a
                if not b or b in computing:
                    continue
                if b in usable_set or (b.bit_count() < mask.bit_count()
                                      and _ceil_log2(b.bit_count()) < latest):
                    choices.append((a, b))
            choices.extend(_raw_splits(mask, rng))
        unique = []
        seen = set()
        for a, b in choices:
            key = tuple(sorted((a, b)))
            if key in seen or not a or not b or a == b or a ^ b != mask:
                continue
            if a in computing or b in computing:
                continue
            seen.add(key)
            unique.append((a, b))
        if not forced:
            rng.shuffle(unique)
            def estimate(ab):
                extra = sum(0 if p in depths and depths[p] < latest
                            else max(1, p.bit_count() - 1) for p in ab)
                return extra
            unique.sort(key=estimate)
        # A bounded constructor attempt.  Backtracking rolls recipes and depth
        # promises together; failed choices never certify availability.
        for a, b in unique[:8]:
            _check_time(deadline)
            saved_recipes = dict(recipes)
            saved_depths = dict(depths)
            if ensure(a, latest - 1) and ensure(b, latest - 1):
                da, db = depths.get(a, 0), depths.get(b, 0)
                if max(da, db) + 1 <= latest:
                    recipes[mask] = (a, b)
                    depths[mask] = max(da, db) + 1
                    computing.remove(mask)
                    return True
            recipes.clear(); recipes.update(saved_recipes)
            depths.clear(); depths.update(saved_depths)
        computing.remove(mask)
        return False

    # Building changed outputs first allows output reuse through their new
    # definitions.  Outside consumers are then checked against the same DAG.
    latest_output = cap if cap is not None else len(old) + max_new + 2
    for target in overrides:
        if not ensure(target, latest_output):
            return None
    return _finish(recipes, targets, inputs, cap)


def _clean_candidate(candidate, targets, inputs, cap, rng, deadline,
                     constructor_budget):
    """Jointly optimize the actual candidate bank, with its witness as fallback."""
    left = deadline - time.monotonic()
    if left <= .002:
        return candidate
    res = reconstruct(candidate["masks"], targets, inputs=inputs, cap=cap,
                      preferred=candidate["masks"], rng=rng,
                      max_seconds=min(constructor_budget, left * .7),
                      beam_width=4, max_states=250,
                      fallback_masks=candidate["masks"])
    if res is not None and len(res["masks"]) <= len(candidate["masks"]):
        # Independently replay selected recipes before crossing module boundary.
        checked = _finish(res["recipes"], targets, inputs, cap)
        if checked is not None:
            return checked
    return candidate


def _translations(witness, targets, inputs, cap, rng, deadline, trials,
                  max_parent_edges, constructor_budget, stats):
    edges = parent_edges(witness["recipes"], targets)
    components = edge_components(edges)
    if not components:
        return None
    best = None
    for _ in range(trials):
        if time.monotonic() >= deadline:
            stats["timed_out"] = 1
            break
        # Prefer actual shared-parent groups while retaining singleton moves.
        sizes = [min(len(c), max_parent_edges) for c in components]
        component = rng.choices(components, weights=sizes, k=1)[0]
        selected = _connected_subset(component, max_parent_edges, rng)
        groups = (_partition_edges(selected, rng)
                  if len(selected) > 1 and rng.random() < .6 else [selected])
        # A second component occasionally allows a root choice to join roles
        # which did not previously share a parent.
        others = [c for c in components if c is not component]
        if others and rng.random() < .25:
            groups.append(_connected_subset(rng.choice(others),
                          max(1, max_parent_edges // 2), rng))
        changed = {e[0] for g in groups for e in g}
        safe = _unaffected_values(witness["recipes"], inputs, changed)
        max_d = cap - 1 if cap is not None else len(witness["masks"]) + 1
        anchors = sorted(m for m in safe if witness["depths"][m] <= max_d)
        if not anchors:
            continue
        deltas = []
        for group in groups:
            vertices = sorted({v for edge in group for v in edge[1:]})
            delta = _choose_delta(vertices, anchors, safe, cap, rng)
            if delta is None:
                deltas = []
                break
            # A raw pair / foreign bit perturbation is another bounded source;
            # it does not restrict the other search engines' mask universe.
            if rng.random() < .12:
                delta = rng.choice(inputs) ^ rng.choice(inputs)
            deltas.append(delta)
        stats["attempted"] += 1
        stats["partitioned"] += int(len(groups) > 1)
        if not deltas:
            stats["weight_rejected"] += 1
            continue
        overrides = translated_output_recipes(groups, deltas)
        if overrides is None or all(overrides[t] == witness["recipes"][t]
                                    for t in overrides):
            stats["degenerate"] += 1
            continue
        if cap is not None and any(p.bit_count() > 1 << (cap - 1)
                                  for ab in overrides.values() for p in ab):
            stats["weight_rejected"] += 1
            continue
        try:
            candidate = _build_translated(witness, overrides, targets, inputs, cap,
                                          rng, deadline)
        except _BudgetExpired:
            stats["timed_out"] = 1
            break
        if candidate is None:
            stats["construction_rejected"] += 1
            continue
        stats["constructible"] += 1
        candidate = _clean_candidate(candidate, targets, inputs, cap, rng,
                                     deadline, constructor_budget)
        if candidate["masks"] == witness["masks"]:
            stats["unchanged"] += 1
            continue
        if best is None or len(candidate["masks"]) < len(best["masks"]):
            best = candidate
        if best is not None and len(best["masks"]) < len(witness["masks"]):
            break
    return best


def _core_moves(witness, targets, inputs, cap, rng, deadline, trials,
                constructor_budget, stats, max_roots=4):
    roots = [m for m in witness["masks"] if m.bit_count() in (3, 5)]
    if not roots:
        return None
    best = None
    for _ in range(trials):
        if time.monotonic() >= deadline:
            stats["timed_out"] = 1
            break
        first = rng.choice(roots)
        others = [m for m in roots if m != first]
        rng.shuffle(others)
        others.sort(key=lambda m: -(m & first).bit_count())
        upper = max(1, min(max_roots, len(roots)))
        count = rng.randrange(2 if upper >= 2 else 1, upper + 1)
        selected = [first] + others[:count - 1]
        cores = {}
        for root in selected:
            bits = _bits(root)
            # Triple -> pair + input; W5 -> quartet + input.
            missing = rng.choice(bits)
            cores[root] = root ^ missing
        outside = _outside_values(witness["recipes"], targets, set(selected), inputs)
        free_pairs = {m for m in outside if m.bit_count() == 2}
        stats["attempted"] += 1
        stats["joint_roots"] += len(selected)
        left = deadline - time.monotonic()
        if left <= .002:
            break
        joint = optimize_depth3(set(cores.values()), existing_pairs=free_pairs,
                                rng=rng, max_seconds=min(.025, left * .35),
                                max_nodes=2000)
        if joint is None:
            stats["construction_rejected"] += 1
            continue
        recipes = dict(witness["recipes"])
        recipes.update({m: tuple(ab) for m, ab in joint["recipes"].items()})
        for root, parent in cores.items():
            recipes[root] = (parent, root ^ parent)
        candidate = _finish(recipes, targets, inputs, cap)
        if candidate is None:
            stats["construction_rejected"] += 1
            continue
        stats["constructible"] += 1
        candidate = _clean_candidate(candidate, targets, inputs, cap, rng,
                                     deadline, constructor_budget)
        if candidate["masks"] == witness["masks"]:
            stats["unchanged"] += 1
            continue
        if best is None or len(candidate["masks"]) < len(best["masks"]):
            best = candidate
        if best is not None and len(best["masks"]) < len(witness["masks"]):
            break
    return best


def propose(current_masks, cap, rng=None, max_seconds=.15, max_parent_edges=6,
            root_trials=8, constructor_budget=.05, kind="translate", **kwargs):
    """Return a verified coordinated proposal, or None after a bounded attempt.

    Optional ``stats`` is updated even when no proposal is returned.  Optional
    ``targets`` / ``inputs`` support small deterministic tests; production uses
    the exact 32 AES targets and raw inputs.  Gate counts refer to the complete
    live physical circuit.  A returned candidate may be neutral or uphill;
    the calling engine owns acceptance and preservation of the best record.
    """
    started = time.monotonic()
    out_stats = kwargs.get("stats")
    stats = {"operator": kind, "attempted": 0, "constructible": 0,
             "partitioned": 0, "joint_roots": 0, "degenerate": 0,
             "weight_rejected": 0, "construction_rejected": 0,
             "unchanged": 0, "timed_out": 0, "before": len(set(current_masks))}
    result = None
    rng = rng or random.Random()
    targets = list(kwargs["targets"])
    inputs = list(kwargs["inputs"])
    seconds = max(0.0, float(max_seconds))
    deadline = started + seconds
    try:
        if kind not in ("translate", "cores"):
            raise ValueError("unknown structured proposal kind: %s" % kind)
        if seconds <= 0 or root_trials <= 0 or max_parent_edges <= 0:
            return None
        witness = earliest_witness(set(current_masks), targets, inputs=inputs, cap=cap)
        if witness is None:
            stats["invalid_start"] = 1
            return None
        _check_time(deadline)
        if kind == "translate":
            result = _translations(witness, targets, inputs, cap, rng, deadline,
                                   int(root_trials), int(max_parent_edges),
                                   max(0.0, constructor_budget), stats)
        else:
            result = _core_moves(witness, targets, inputs, cap, rng, deadline,
                                 int(root_trials), max(0.0, constructor_budget),
                                 stats, max_roots=int(kwargs.get("max_roots", 4)))
        if result is not None:
            # Recheck the final witness after all cross-module transformations.
            result = _finish(result["recipes"], targets, inputs, cap)
            if result is not None:
                stats["after"] = len(result["masks"])
                stats["added"] = len(result["masks"] - set(current_masks))
                stats["released"] = len(set(current_masks) - result["masks"])
                stats["depth"] = max(result["depths"].values(), default=0)
                result["stats"] = stats
    except _BudgetExpired:
        stats["timed_out"] = 1
        # Every returned result must already have a complete witness.  A partial
        # constructor on timeout is deliberately not returned as a candidate.
        result = None
    finally:
        stats["elapsed_seconds"] = time.monotonic() - started
        if out_stats is not None:
            out_stats.update(stats)
    return result
