# Vendored for xorsearch from search/engines/vendor_v3/deadline_search.py
# Origin sha256: d7bcaf55db77a6b99d23d27ebe6463c0e3c0319b76e2e632609a16c47a8f4ebb
# FIX: reconstruct() used the names objective and gate_limit without
# declaring them (NameError on its first ranking comparison); they are now
# keyword parameters with the v2 defaults (objective="gates", gate_limit=None).
# Used by xorsearch/moves/structural.py (and v2 optimize_depth3 is the reference for
# xorsearch/moves/depth3.py).  Do not edit except to fix bugs; record every change here.
"""Bounded, deadline-aware construction of a shared XOR value bank.

The old extractor permits only a value's fastest recipes in the whole bank.
This module instead gives every demanded value a deadline and propagates that
deadline through the *chosen* recipes.  A slower shared construction is legal
when it meets the actual output cap.  Every returned result is replayable and
contains only live, distinct, non-input values.

``reconstruct`` is a heuristic with a bounded beam, not an optimality solver.
``optimize_depth3`` is a branch-and-bound solver for the finite pair choices of
fixed weight-three/four parents; its ``complete`` field reports whether its
optimality search finished.  Time limits bound search; constructing and
validating a fallback adds small, finite O(bank_size**2) overhead.

Only Python's standard library is required.  Inputs are supplied masks at
depth zero, in the same order used by returned index-pair gates.  The usual
caller supplies the 32 original AES input bits, rather than treating an
unbuilt or late intermediate as a free input.
"""

from collections import deque
import math
import random
import time


_DEFAULT_INPUTS = tuple(1 << i for i in range(32))


def _normalise(mask_bank, targets, inputs):
    inputs = tuple(_DEFAULT_INPUTS if inputs is None else inputs)
    targets = tuple(dict.fromkeys(targets))
    bank = set(mask_bank) | set(targets)
    for m in bank | set(inputs):
        if not isinstance(m, int) or isinstance(m, bool) or not 0 < m < (1 << 64):
            raise ValueError("masks must be nonzero unsigned 64-bit integers")
    if len(inputs) != len(set(inputs)):
        raise ValueError("input masks must be distinct")
    return bank - set(inputs), targets, inputs


def _check_cap(cap):
    if cap is not None and (not isinstance(cap, int) or isinstance(cap, bool) or cap < 0):
        raise ValueError("cap must be a nonnegative integer or None")


def _earliest(bank, inputs):
    """Exact finite-bank earliest availability, with one acyclic witness."""
    levels = {m: 0 for m in inputs}
    parents = {}
    resolved = set(inputs)
    frontier = list(inputs)
    unresolved = sorted(set(bank) - resolved)
    level = 1
    while frontier and unresolved:
        newly = []
        remaining = []
        for value in unresolved:
            for a in frontier:
                b = value ^ a
                if b in resolved:
                    parents[value] = (a, b) if a < b else (b, a)
                    levels[value] = level
                    newly.append(value)
                    break
            else:
                remaining.append(value)
        resolved.update(newly)
        frontier = newly
        unresolved = remaining
        level += 1
    return levels, parents


def _emit(recipes, targets, inputs, cap):
    """Prune, topologically order and independently replay a chosen recipe DAG.

    Iterative traversal avoids Python recursion limits for uncapped banks.
    An incomplete, cyclic, algebraically invalid or over-cap DAG returns None.
    """
    index = {m: i for i, m in enumerate(inputs)}
    depths = {m: 0 for m in inputs}
    colours = {m: 2 for m in inputs}
    gates = []
    live_recipes = {}
    for target in targets:
        stack = [(target, False)]
        while stack:
            value, exiting = stack.pop()
            colour = colours.get(value, 0)
            if exiting:
                pair = recipes.get(value)
                if pair is None:
                    return None
                a, b = pair
                if a not in index or b not in index or a == b or (a ^ b) != value:
                    return None
                depth = 1 + max(depths[a], depths[b])
                if cap is not None and depth > cap:
                    return None
                index[value] = len(inputs) + len(gates)
                depths[value] = depth
                gates.append([index[a], index[b]])
                live_recipes[value] = (a, b)
                colours[value] = 2
                continue
            if colour == 2:
                continue
            if colour == 1:
                return None
            pair = recipes.get(value)
            if pair is None or len(pair) != 2:
                return None
            a, b = pair
            if a == b or (a ^ b) != value:
                return None
            colours[value] = 1
            stack.append((value, True))
            stack.append((b, False))
            stack.append((a, False))
    if any(t not in index for t in targets):
        return None
    return {
        "masks": set(live_recipes),
        "gates": gates,
        "depths": depths,
        "recipes": live_recipes,
        "output_indices": [index[t] for t in targets],
        "depth": max(depths.values(), default=0),
        "stats": {},
    }


def earliest_witness(mask_bank, targets, inputs=None, cap=None):
    """Return a live minimum-arrival witness, or None if a target cannot meet cap.

    Minimum arrival is exact for the supplied finite bank.  The gate count of
    the selected witness is not claimed minimal.  Targets themselves are added
    to the bank as demands; no additional intermediate masks are invented.
    """
    _check_cap(cap)
    started = time.monotonic()
    bank, targets, inputs = _normalise(mask_bank, targets, inputs)
    levels, parents = _earliest(bank, inputs)
    if any(t not in levels or (cap is not None and levels[t] > cap) for t in targets):
        return None
    result = _emit(parents, targets, inputs, cap)
    if result is not None:
        result["stats"] = {"method": "earliest_witness", "elapsed_s": time.monotonic() - started}
    return result


def _would_cycle(value, a, b, recipes):
    stack = [a, b]
    seen = set()
    while stack:
        node = stack.pop()
        if node == value:
            return True
        if node in seen:
            continue
        seen.add(node)
        if node in recipes:
            stack.extend(recipes[node])
    return False


def _extend(recipes, demands, value, pair, levels, input_set):
    """Choose one recipe and propagate all affected deadlines consistently."""
    a, b = pair
    if _would_cycle(value, a, b, recipes):
        return None
    chosen = dict(recipes)
    chosen[value] = pair
    deadlines = dict(demands)
    queue = deque([value])
    while queue:
        node = queue.popleft()
        if node not in chosen:
            continue
        parent_deadline = deadlines[node] - 1
        for parent in chosen[node]:
            if parent not in levels or levels[parent] > parent_deadline:
                return None
            if parent in input_set:
                continue
            previous = deadlines.get(parent)
            if previous is None or parent_deadline < previous:
                deadlines[parent] = parent_deadline
                if parent in chosen:
                    queue.append(parent)
    return chosen, deadlines


def objective_key(witness, objective="gates", gate_limit=None):
    """Rank complete physical witnesses; a scoped gate budget is not a proof."""
    if objective not in ("gates", "depth_then_gates"):
        raise ValueError("unknown objective")
    count = len(witness["gates"])
    depth = witness["depth"] if "depth" in witness else max(witness["depths"].values(), default=0)
    feasible = int(gate_limit is not None and count > gate_limit)
    return (feasible, depth, count) if objective == "depth_then_gates" else (feasible, count, depth)


def reconstruct(mask_bank, targets, inputs=None, cap=None, preferred=None,
                rng=None, max_seconds=0.05, beam_width=8, max_states=1000,
                fallback_masks=None, ranking_weight=0.45, objective="gates", gate_limit=None):
    """Construct a small shared XOR circuit from a finite bank, within a budget.

    All targets receive ``cap`` as their allowed deadline.  With no cap, the
    finite bank size is a safe DAG-depth bound, so no depth-five/six restriction
    is introduced.  Earliest arrival only filters impossible choices.

    ``preferred`` is a mask set or a mapping of masks to nonnegative ranking
    costs; it affects tie/ranking choices, never the physical gate objective.
    ``fallback_masks`` supplies a valid incumbent value set.  Its masks are
    added to the bank and its witness competes with the beam results, ensuring
    that a newly enlarged bank cannot silently discard a smaller incumbent.
    Every returned result is a complete replayable live DAG.  Search failure
    or exhaustion returns the best valid witness already available, or None.
    """
    _check_cap(cap)
    started = time.monotonic()
    seconds = float(max_seconds)
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("max_seconds must be finite and nonnegative")
    ranking_weight = float(ranking_weight)
    if not math.isfinite(ranking_weight) or ranking_weight < 0:
        raise ValueError("ranking_weight must be finite and nonnegative")
    beam_width = max(1, int(beam_width))
    max_states = max(0, int(max_states))
    rng = random.Random(0) if rng is None else rng
    fallback = None if fallback_masks is None else set(fallback_masks)
    permitted = set(mask_bank)
    if fallback is not None:
        permitted.update(fallback)
    bank, targets, inputs = _normalise(permitted, targets, inputs)
    input_set = set(inputs)
    if preferred is None:
        preference = {}
    elif hasattr(preferred, "get"):
        preference = preferred
    else:
        preference = {m: 0 for m in preferred}

    levels, earliest_recipes = _earliest(bank, inputs)
    best = None
    if all(t in levels and (cap is None or levels[t] <= cap) for t in targets):
        best = _emit(earliest_recipes, targets, inputs, cap)
    if fallback is not None:
        fallback_result = earliest_witness(fallback, targets, inputs=inputs, cap=cap)
        if fallback_result is not None and (best is None or
                objective_key(fallback_result, objective, gate_limit) <
                objective_key(best, objective, gate_limit)):
            best = fallback_result
    baseline_count = None if best is None else len(best["masks"])
    states = 0
    recipe_count = 0
    completion_attempts = 0
    completed_candidates = 0
    improving_completions = 0
    completed_value_sets = set()
    cutoff = started + seconds
    time_hit = False
    state_hit = False

    def finish():
        if best is not None:
            best["stats"] = {
                "method": "deadline_beam",
                "elapsed_s": time.monotonic() - started,
                "states": states,
                "candidate_recipes": recipe_count,
                "completion_attempts": completion_attempts,
                "completed_candidates": completed_candidates,
                "distinct_completed_value_sets": len(completed_value_sets),
                "improving_completions": improving_completions,
                "baseline_gates": baseline_count,
                "gates": len(best["masks"]),
                "deadline_slack_values": sum(best["depths"][m] > levels.get(m, best["depths"][m])
                                             for m in best["masks"]),
                "beam_width": beam_width,
                "time_limit_hit": time_hit,
                "state_limit_hit": state_hit,
                "search_exhaustive": False,
            }
        return best

    def consider(candidate):
        nonlocal best, completed_candidates, improving_completions
        if candidate is None:
            return
        completed_candidates += 1
        completed_value_sets.add(frozenset(candidate["masks"]))
        if objective_key(candidate, objective, gate_limit) < \
                objective_key(best, objective, gate_limit):
            best = candidate
            improving_completions += 1

    def complete_partial(chosen):
        """Turn early beam branches into fully validated whole circuits.

        A 32-output branch would otherwise need roughly ninety consecutive
        recipe assignments before yielding any candidate.  Complete missing
        definitions from valid full-bank or incumbent witnesses immediately.
        Overriding an earliest recipe with a slower chosen recipe can create a
        dependency cycle; _emit checks the complete resulting DAG and rejects
        it.  An incumbent fill can also exceed the cap; the same replay checks
        all actual depths.  No cost estimate is treated as a circuit.
        """
        nonlocal completion_attempts
        for use_incumbent in (True, False):
            if time.monotonic() >= cutoff:
                return
            full = dict(earliest_recipes)
            if use_incumbent:
                full.update(best["recipes"])
            full.update(chosen)
            completion_attempts += 1
            consider(_emit(full, targets, inputs, cap))

    if best is None:
        # A finite-bank minimum-arrival closure is an exact feasibility test.
        return None
    if not targets or not bank or max_states == 0 or time.monotonic() >= cutoff:
        time_hit = time.monotonic() >= cutoff
        state_hit = max_states == 0
        return finish()

    # Generate all legal recipes over the reachable bank.  Unreachable values
    # cannot become available merely by picking a different chronology.
    values = sorted(levels)
    value_set = set(values)
    alternatives = {}
    for value in sorted(bank & value_set):
        choices = []
        for a in values:
            b = value ^ a
            if a < b and b in value_set:
                choices.append((a, b))
        alternatives[value] = choices
        recipe_count += len(choices)
        if time.monotonic() >= cutoff:
            time_hit = True
            return finish()

    deadline = len(bank) if cap is None else cap
    demands = {t: deadline for t in targets if t not in input_set}
    beam = [({}, demands)]
    seen = set()
    # Each expansion fixes one distinct value recipe.  A full branch has at
    # most len(bank) expansions; cycle checks and deadlines prevent recursion.
    while beam and states < max_states:
        if time.monotonic() >= cutoff:
            time_hit = True
            break
        next_beam = []
        for chosen, needed in beam:
            if states >= max_states:
                state_hit = True
                break
            if time.monotonic() >= cutoff:
                time_hit = True
                break
            pending = [m for m in needed if m not in chosen]
            if not pending:
                completion_attempts += 1
                consider(_emit(chosen, targets, inputs, cap))
                continue
            # Tight-deadline and deep demands expose infeasible branches early.
            value = min(pending, key=lambda m: (needed[m] - levels[m], -levels[m], m))
            parent_deadline = needed[value] - 1
            choices = [pair for pair in alternatives[value]
                       if levels[pair[0]] <= parent_deadline and levels[pair[1]] <= parent_deadline]
            rng.shuffle(choices)

            def rank_pair(pair):
                new = [m for m in pair if m not in input_set and m not in needed]
                return (len(new), sum(float(preference.get(m, 1)) for m in new),
                        max(levels[pair[0]], levels[pair[1]]))

            choices.sort(key=rank_pair)
            for pair in choices:
                if states >= max_states:
                    state_hit = True
                    break
                states += 1
                extended = _extend(chosen, needed, value, pair, levels, input_set)
                if extended is None:
                    continue
                selected, demands2 = extended
                if len(demands2) > (len(best["masks"]) if objective == "gates" else (gate_limit if gate_limit is not None else len(bank))):
                    continue
                signature = (tuple(sorted(selected.items())), tuple(sorted(demands2.items())))
                if signature in seen:
                    continue
                seen.add(signature)
                pending2 = [m for m in demands2 if m not in selected]
                if not pending2:
                    completion_attempts += 1
                    consider(_emit(selected, targets, inputs, cap))
                    continue
                # Complete every shallow branch, then periodically thereafter.
                # This makes a short whole-AES call productive even when its
                # beam cannot assign every gate recipe within the budget.
                if states <= 4 * beam_width or states % max(4, beam_width) == 0:
                    complete_partial(selected)
                # This is a heuristic rank, not a claimed lower bound.  The
                # only cost pruning above is the actual already-demanded union.
                min_additions = 0
                for m in pending2:
                    limit = demands2[m] - 1
                    costs = [sum(p not in demands2 and p not in input_set for p in recipe)
                             for recipe in alternatives[m]
                             if levels[recipe[0]] <= limit and levels[recipe[1]] <= limit]
                    if not costs:
                        break
                    min_additions += min(costs)
                else:
                    score = (len(demands2) + ranking_weight * min_additions,
                             len(demands2),
                             sum(float(preference.get(m, 1)) for m in demands2),
                             rng.random())
                    next_beam.append((score, selected, demands2))
                if time.monotonic() >= cutoff:
                    time_hit = True
                    break
            if time_hit:
                break
        if time_hit:
            break
        next_beam.sort(key=lambda row: row[0])
        beam = [(chosen, needed) for _, chosen, needed in next_beam[:beam_width]]
    state_hit = state_hit or states >= max_states
    return finish()


def _bits(mask):
    out = []
    while mask:
        bit = mask & -mask
        out.append(bit)
        mask ^= bit
    return out


def optimize_depth3(parents, existing_pairs=(), rng=None, max_seconds=0.05,
                    max_nodes=5000):
    """Jointly minimize new pair gates for fixed weight <=4 depth-two parents.

    Triples choose one of three contained pairs; quartets choose one of three
    two-pair partitions.  ``existing_pairs`` are genuinely retained outside
    gates whose marginal cost is zero.  The result's ``pairs`` is the union
    actually required by these parents (not unrelated existing pairs), and
    ``new_pairs`` is that union minus existing_pairs.  ``recipes`` contains
    literal XOR operand masks for the parents and every required pair.

    ``complete=True`` certifies an optimum of THIS FIXED-PARENT finite problem,
    not an unrestricted circuit optimum.  A timeout/node cutoff still returns
    a valid incumbent and marks ``complete=False``.
    """
    started = time.monotonic()
    seconds = float(max_seconds)
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("max_seconds must be finite and nonnegative")
    max_nodes = max(0, int(max_nodes))
    rng = random.Random(0) if rng is None else rng
    parents = sorted(set(parents))
    free = set(existing_pairs)
    for m in parents + list(free):
        if not isinstance(m, int) or isinstance(m, bool) or not 0 < m < (1 << 64):
            raise ValueError("masks must be nonzero unsigned 64-bit integers")
    if any(m.bit_count() != 2 for m in free):
        raise ValueError("existing_pairs must contain only weight-two masks")
    if any(m.bit_count() > 4 for m in parents):
        return None
    direct = {m for m in parents if m.bit_count() == 2}
    choices = {}
    for m in parents:
        bits = _bits(m)
        if len(bits) == 3:
            choices[m] = [((m ^ bit,), (m ^ bit, bit)) for bit in bits]
        elif len(bits) == 4:
            a, b, c, d = bits
            choices[m] = [((a | b, c | d), (a | b, c | d)),
                          ((a | c, b | d), (a | c, b | d)),
                          ((a | d, b | c), (a | d, b | c))]
    popularity = {}
    for opts in choices.values():
        for pairset, _ in opts:
            for p in pairset:
                popularity[p] = popularity.get(p, 0) + 1
    # Parents with useful shared choices are encountered early by both the
    # greedy incumbent and the exact bounded branch-and-bound traversal.
    order = sorted(choices, key=lambda m: (-max(sum(popularity[p] for p in ps)
                                               for ps, _ in choices[m]), m))
    greedy_pairs = set(direct)
    greedy_recipes = {}
    for m in order:
        opts = list(choices[m])
        rng.shuffle(opts)
        opts.sort(key=lambda item: (len(set(item[0]) - greedy_pairs - free),
                                   -sum(popularity[p] for p in item[0])))
        pairset, recipe = opts[0]
        greedy_pairs.update(pairset)
        greedy_recipes[m] = recipe
    best_pairs = greedy_pairs
    best_recipes = greedy_recipes
    best_cost = len(best_pairs - free)
    nodes = 0
    complete = True
    cutoff = started + seconds
    seen = set()

    # Use an explicit stack so large fixed-parent calls remain portable and
    # bounded without depending on Python's recursion limit.
    stack = [(0, set(direct), {})]
    while stack:
        if nodes >= max_nodes or time.monotonic() >= cutoff:
            complete = False
            break
        i, required, recipes = stack.pop()
        nodes += 1
        paid = required - free
        if len(paid) >= best_cost:
            continue
        if i == len(order):
            best_cost = len(paid)
            best_pairs = required
            best_recipes = recipes
            continue
        signature = (i, frozenset(paid))
        if signature in seen:
            continue
        seen.add(signature)
        # A safe bound: the maximum individual shortfall, never the sum of
        # shortfalls that might share the same physical new pair.
        additional = max(min(len(set(ps) - required - free) for ps, _ in choices[m])
                         for m in order[i:])
        if len(paid) + additional >= best_cost:
            continue
        m = order[i]
        opts = list(choices[m])
        rng.shuffle(opts)
        opts.sort(key=lambda item: (len(set(item[0]) - required - free),
                                   -sum(popularity[p] for p in item[0])))
        for pairset, recipe in reversed(opts):
            next_recipes = dict(recipes)
            next_recipes[m] = recipe
            stack.append((i + 1, required | set(pairset), next_recipes))
    for p in best_pairs:
        a = p & -p
        best_recipes[p] = (a, p ^ a)
    return {
        "pairs": set(best_pairs),
        "new_pairs": set(best_pairs) - free,
        "recipes": best_recipes,
        "marginal_pair_count": best_cost,
        "complete": complete,
        "nodes": nodes,
        "elapsed_s": time.monotonic() - started,
    }
