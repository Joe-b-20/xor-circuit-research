"""Bounded, replayed structural neighborhoods for XOR straight-line programs.

Public API: ``propose(kind, steps, targets, n_inputs, depth_cap, rng, knobs=None)``.
Every result is a complete chronological circuit, never an algebraic cost claim.
See docs/ADVANCED_MOVES.md for scope and every configuration default.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
import itertools
import math
import random
import time

try:
    from .deadline_search import _emit, objective_key
except ImportError:
    from deadline_search import _emit, objective_key


DEFAULT_KNOBS = {
    "max_seconds": 0.15,
    "max_nodes": 3000,
    "max_trials": 24,
    "max_merge_pairs": 48,
    "max_merge_vertices": 16,
    "max_interface_sets": 12,
    "interface_sizes": (2, 3),
    "interface_signal_limit": 18,
    "basis_matrix_limit": 168,
    "interface_sets": None,
    "basis_matrices": None,
    "package_sizes": (2, 3),
    "package_anchor_limit": 48,
    "package_group_limit": 24,
    "constructor_branch_factor": 12,
    "constructor_known_limit": 64,
    "constructor_raw_splits": 12,
    "constructor_max_new": 32,
    "constructor_attempts": 2,
    "focus_outputs": None,
}


class _SearchLimit(Exception):
    pass


class _Budget:
    def __init__(self, knobs, metrics):
        self.deadline = time.monotonic() + knobs["max_seconds"]
        self.limit = knobs["max_nodes"]
        self.metrics = metrics
        self.should_stop = None

    def check(self):
        if (self.should_stop and self.should_stop()) or time.monotonic() >= self.deadline:
            self.metrics["limit_reason"] = "time_limit"
            raise _SearchLimit

    def spend(self):
        self.check()
        if self.metrics["nodes"] >= self.limit:
            self.metrics["limit_reason"] = "node_limit"
            raise _SearchLimit
        self.metrics["nodes"] += 1


def _configuration(knobs, targets):
    supplied = {} if knobs is None else dict(knobs)
    unknown = set(supplied) - set(DEFAULT_KNOBS)
    if unknown:
        raise ValueError("unknown advanced-move knobs: " + ", ".join(sorted(unknown)))
    out = dict(DEFAULT_KNOBS)
    out.update(supplied)
    value = out["max_seconds"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("max_seconds must be finite and nonnegative")
    out["max_seconds"] = float(value)
    scalar = set(DEFAULT_KNOBS) - {"max_seconds", "interface_sizes", "interface_sets",
                                 "basis_matrices", "package_sizes", "focus_outputs"}
    for key in scalar:
        if isinstance(out[key], bool) or not isinstance(out[key], int) or out[key] < 0:
            raise ValueError(key + " must be a nonnegative integer")
    for key in ("interface_sizes", "package_sizes"):
        values = tuple(out[key])
        if not values or any(isinstance(x, bool) or not isinstance(x, int) or
                             x not in (2, 3) for x in values):
            raise ValueError(key + " must contain only 2 and/or 3")
        out[key] = tuple(dict.fromkeys(values))
    if out["focus_outputs"] is not None:
        focus = tuple(dict.fromkeys(out["focus_outputs"]))
        if any(isinstance(x, bool) or not isinstance(x, int) or x not in targets for x in focus):
            raise ValueError("focus_outputs must be masks of required outputs")
        out["focus_outputs"] = focus
    return out


def verify_steps(steps, targets, n_inputs, depth_cap=None, require_live=False):
    """Independent symbolic replay; raise ValueError for an invalid program.

    The returned masks/depths are calculated from operand indices, never taken
    from a proposal's bookkeeping. ``depth`` is maximum required-output depth.
    Duplicate/zero gates are rejected because proposals use a distinct-value
    representation. With ``require_live``, every gate must feed a target.
    """
    if isinstance(n_inputs, bool) or not isinstance(n_inputs, int) or not 1 <= n_inputs <= 64:
        raise ValueError("n_inputs must be between 1 and 64")
    if depth_cap is not None and (isinstance(depth_cap, bool) or
            not isinstance(depth_cap, int) or depth_cap < 0):
        raise ValueError("depth_cap must be a nonnegative integer or None")
    targets = tuple(targets)
    if any(isinstance(t, bool) or not isinstance(t, int) or not 0 < t < (1 << n_inputs)
           for t in targets):
        raise ValueError("targets must be nonzero masks in the input width")
    values = [1 << i for i in range(n_inputs)]
    depths = [0] * n_inputs
    index = {m: i for i, m in enumerate(values)}
    recipes = {}
    clean_steps = []
    for pair in steps:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("a gate must contain two operand indices")
        a, b = pair
        if any(isinstance(p, bool) or not isinstance(p, int) or not 0 <= p < len(values)
               for p in pair) or a == b:
            raise ValueError("gate operands must be distinct earlier signals")
        m = values[a] ^ values[b]
        if not m or m in index:
            raise ValueError("zero or duplicate gate value")
        recipes[m] = (values[a], values[b])
        index[m] = len(values)
        values.append(m)
        depths.append(1 + max(depths[a], depths[b]))
        clean_steps.append([a, b])
    if any(t not in index for t in targets):
        raise ValueError("program does not produce every target")
    output_indices = [index[t] for t in targets]
    output_depth = max((depths[i] for i in output_indices), default=0)
    if depth_cap is not None and output_depth > depth_cap:
        raise ValueError("program exceeds depth cap")
    live = set()
    pending = list(output_indices)
    while pending:
        i = pending.pop()
        if i < n_inputs or i in live:
            continue
        live.add(i)
        pending.extend(clean_steps[i - n_inputs])
    if require_live and len(live) != len(clean_steps):
        raise ValueError("program contains dead gates")
    return {"gates": clean_steps, "masks": set(values[n_inputs:]),
            "values": values, "recipes": recipes,
            "depths": dict(zip(values, depths)), "depth": output_depth,
            "output_indices": output_indices, "live_gates": len(live)}


def _normalise(steps, targets, n_inputs, cap):
    initial = verify_steps(steps, targets, n_inputs, cap)
    inputs = tuple(1 << i for i in range(n_inputs))
    witness = _emit(initial["recipes"], targets, inputs, cap)
    if witness is None:
        raise ValueError("starting circuit cannot be replayed")
    verify_steps(witness["gates"], targets, n_inputs, cap, require_live=True)
    return witness, inputs


def _rank(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


@lru_cache(maxsize=2)
def invertible_binary_bases(k):
    """All ordered row bases of GF(2)^k: exactly 6 for k=2, 168 for k=3."""
    if isinstance(k, bool) or not isinstance(k, int) or k not in (2, 3):
        raise ValueError("only two- and three-signal interfaces are supported")
    return tuple(rows for rows in itertools.permutations(range(1, 1 << k), k)
                 if _rank(rows) == k)


def _linear_combination(values, coefficients):
    out = 0
    for i, value in enumerate(values):
        if coefficients & (1 << i):
            out ^= value
    return out


def _inverse_coordinates(rows):
    coordinates = {_linear_combination(rows, c): c for c in range(1, 1 << len(rows))}
    return tuple(coordinates[1 << i] for i in range(len(rows)))


def _unaffected(witness, inputs, changed, budget):
    safe = set(inputs)
    # _emit orders gates topologically, but its recipe dict is not a public
    # ordering promise. Closure here explicitly checks every prerequisite.
    pending = set(witness["recipes"]) - set(changed)
    while pending:
        budget.check()
        newly = set()
        for m in pending:
            budget.check()
            if all(p in safe for p in witness["recipes"][m]):
                newly.add(m)
        if not newly:
            break
        safe.update(newly)
        pending -= newly
    return safe


def _focus_ancestors(witness, focus, budget):
    relevant = set()
    pending = list(focus or ())
    while pending:
        budget.check()
        m = pending.pop()
        if m in relevant:
            continue
        relevant.add(m)
        pending.extend(witness["recipes"].get(m, ()))
    return relevant


def _raw_splits(mask, limit, rng, budget):
    bits = [1 << i for i in range(mask.bit_length()) if mask & (1 << i)]
    if len(bits) < 2 or not limit:
        return []
    splits = []
    seen = set()

    def add(left):
        pair = tuple(sorted((left, mask ^ left)))
        if 0 not in pair and pair not in seen:
            seen.add(pair)
            splits.append(pair)

    add(sum(bits[:len(bits) // 2]))
    for bit in bits:
        budget.check()
        if len(splits) >= limit:
            break
        add(bit)
    # Each trial is bounded even when duplicate partitions are sampled.
    for _ in range(limit):
        budget.check()
        if len(splits) >= limit:
            break
        work = list(bits)
        rng.shuffle(work)
        add(sum(work[:rng.randrange(1, len(work))]))
    return splits[:limit]


class _Constructor:
    """Backtracking construction from physical retained signals.

    Missing complements may have any weight. Weight is used only for ranking
    and the universally valid support bound wt(value) <= 2**depth.
    """
    def __init__(self, witness, inputs, safe, hints, forced, forbidden,
                 cap, rng, knobs, budget, metrics):
        self.inputs = set(inputs)
        self.recipes = {m: ab for m, ab in witness["recipes"].items() if m in safe}
        self.depths = {m: witness["depths"][m] for m in safe}
        self.original = witness["recipes"]
        self.initial = set(self.recipes)
        self.hints = set(hints)
        self.forced = dict(forced)
        self.forbidden = set(forbidden)
        self.active = set()
        self.cap = cap
        self.rng = rng
        self.knobs = knobs
        self.budget = budget
        self.metrics = metrics
        self.should_stop = None
        self.latest = cap if cap is not None else max(self.depths.values(), default=0) + knobs["constructor_max_new"]

    def ensure(self, mask, latest=None):
        self.budget.spend()
        latest = self.latest if latest is None else latest
        if not mask or latest < 0 or mask in self.forbidden or mask in self.active:
            return False
        if mask in self.inputs:
            return True
        if mask in self.depths and self.depths[mask] <= latest:
            return True
        if latest == 0 or mask.bit_count() > (1 << min(latest, 64)):
            return False
        if mask not in self.initial and mask not in self.recipes and \
                len(set(self.recipes) - self.initial) >= self.knobs["constructor_max_new"]:
            self.metrics["constructor_gate_limits"] += 1
            return False
        self.active.add(mask)
        try:
            if mask in self.forced:
                options = [self.forced[mask]]
            else:
                options = []
                if mask in self.original:
                    options.append(self.original[mask])
                anchors = list((set(self.depths) | self.hints) - self.active - self.forbidden)
                self.rng.shuffle(anchors)
                ranked = []
                for a in anchors:
                    self.budget.check()
                    if a in self.depths and self.depths[a] >= latest:
                        continue
                    b = mask ^ a
                    if not b or b in self.active or b in self.forbidden:
                        continue
                    if any(p.bit_count() > (1 << min(latest - 1, 64)) for p in (a, b)):
                        continue
                    rank = (int(b not in self.depths) + int(a not in self.depths),
                            sum(max(0, p.bit_count() - 1) for p in (a, b) if p not in self.depths))
                    ranked.append((rank, a, b))
                ranked.sort(key=lambda item: item[0])
                options.extend((a, b) for _, a, b in ranked[:self.knobs["constructor_known_limit"]])
                options.extend(_raw_splits(mask, self.knobs["constructor_raw_splits"],
                                           self.rng, self.budget))
            unique = []
            seen = set()
            for a, b in options:
                self.budget.check()
                pair = tuple(sorted((a, b)))
                if not a or not b or a == b or a ^ b != mask or pair in seen or \
                        a in self.active or b in self.active or \
                        a in self.forbidden or b in self.forbidden:
                    continue
                seen.add(pair)
                unique.append(pair)
            if mask not in self.forced:
                self.rng.shuffle(unique)
                unique.sort(key=lambda ab: (
                    sum(p not in self.depths for p in ab),
                    max(self.depths.get(p, (p.bit_count() - 1).bit_length()) for p in ab),
                    sum(max(0, p.bit_count() - 1) for p in ab if p not in self.depths)))
            for a, b in unique[:self.knobs["constructor_branch_factor"]]:
                self.budget.spend()
                old_recipes = dict(self.recipes)
                old_depths = dict(self.depths)
                if self.ensure(a, latest - 1) and self.ensure(b, latest - 1):
                    depth = 1 + max(self.depths.get(a, 0), self.depths.get(b, 0))
                    new_count = len(set(self.recipes) - self.initial)
                    if mask not in self.initial and mask not in self.recipes:
                        new_count += 1
                    if depth <= latest and new_count <= self.knobs["constructor_max_new"]:
                        self.recipes[mask] = (a, b)
                        self.depths[mask] = depth
                        return True
                    if new_count > self.knobs["constructor_max_new"]:
                        self.metrics["constructor_gate_limits"] += 1
                self.recipes = old_recipes
                self.depths = old_depths
            return False
        finally:
            self.active.remove(mask)


def _compose_overrides(witness, overrides, targets, inputs, cap, rng, knobs, budget, metrics):
    safe = _unaffected(witness, inputs, overrides, budget)
    hints = {p for ab in overrides.values() for p in ab}
    for _ in range(knobs["constructor_attempts"]):
        budget.spend()
        builder = _Constructor(witness, inputs, safe, hints, overrides, (), cap,
                               rng, knobs, budget, metrics)
        order = list(overrides)
        rng.shuffle(order)
        if not all(builder.ensure(m) for m in order):
            metrics["construction_failures"] += 1
            continue
        recipes = dict(witness["recipes"])
        recipes.update(builder.recipes)
        recipes.update(overrides)
        result = _emit(recipes, targets, inputs, cap)
        if result is not None:
            yield result


def _edge_components(witness, targets, budget):
    edges = [(t, *witness["recipes"][t]) for t in dict.fromkeys(targets)
             if t in witness["recipes"]]
    at = {}
    for i, (_, a, b) in enumerate(edges):
        budget.check()
        at.setdefault(a, []).append(i)
        at.setdefault(b, []).append(i)
    unseen = set(range(len(edges)))
    groups = []
    while unseen:
        budget.check()
        first = min(unseen)
        unseen.remove(first)
        pending = [first]
        group = []
        while pending:
            budget.check()
            i = pending.pop()
            group.append(edges[i])
            for p in edges[i][1:]:
                for j in at[p]:
                    if j in unseen:
                        unseen.remove(j)
                        pending.append(j)
        groups.append(group)
    return groups


def _component_merges(witness, targets, inputs, cap, rng, knobs, budget, metrics):
    groups = _edge_components(witness, targets, budget)
    focus = set(knobs["focus_outputs"] or ())
    pairs = []
    for i, moving in enumerate(groups):
        for j, fixed in enumerate(groups):
            budget.check()
            if i != j:
                score = sum(t in focus for t, _, _ in moving + fixed)
                pairs.append((-score, rng.random(), i, j))
    pairs.sort()
    seen = set()
    for _, _, i, j in pairs[:knobs["max_merge_pairs"]]:
        budget.check()
        moving, fixed = groups[i], groups[j]
        left = list({p for _, a, b in moving for p in (a, b)})
        right = list({p for _, a, b in fixed for p in (a, b)})
        rng.shuffle(left)
        rng.shuffle(right)
        options = []
        for a in left[:knobs["max_merge_vertices"]]:
            for b in right[:knobs["max_merge_vertices"]]:
                budget.check()
                delta = a ^ b
                if not delta or (i, delta) in seen:
                    continue
                seen.add((i, delta))
                values = {p ^ delta for _, x, y in moving for p in (x, y)}
                if 0 in values:
                    continue
                if cap is not None and (cap == 0 or any(v.bit_count() > 1 << (cap - 1) for v in values)):
                    continue
                fresh = values - witness["masks"] - set(inputs)
                options.append((len(fresh), sum(v.bit_count() for v in fresh), rng.random(), delta))
        options.sort()
        for _, _, _, delta in options:
            if metrics["trials"] >= knobs["max_trials"]:
                return
            budget.spend()
            metrics["trials"] += 1
            overrides = {t: (a ^ delta, b ^ delta) for t, a, b in moving}
            metrics["deliberate_collisions"] += 1
            yield from _compose_overrides(witness, overrides, targets, inputs, cap,
                                         rng, knobs, budget, metrics)


def _xor_terms(terms):
    parity = Counter(terms)
    return {m for m, count in parity.items() if count & 1}


def _lower_expression(target, terms, recipes, depths, inputs, cap, rng, budget):
    """Lower an exact XOR expression, reusing concrete values across consumers."""
    terms = _xor_terms(terms)
    if _linear_combination(tuple(terms), (1 << len(terms)) - 1) != target:
        raise ValueError("consumer substitution changed its value")
    if target in depths:
        return True
    while len(terms) > 1:
        budget.spend()
        options = []
        for a, b in itertools.combinations(sorted(terms), 2):
            budget.check()
            value = a ^ b
            depth = depths.get(value, 1 + max(depths[a], depths[b]))
            if not value or (cap is not None and depth > cap):
                continue
            options.append((int(value not in depths), depth, rng.random(), a, b, value))
        if not options:
            return False
        _, depth, _, a, b, value = min(options)
        if value not in depths:
            recipes[value] = (a, b)
            depths[value] = depth
        terms.remove(a)
        terms.remove(b)
        if value in terms:
            terms.remove(value)
        else:
            terms.add(value)
        if target in depths:
            return True
    return bool(terms) and next(iter(terms)) == target and target in depths


def _basis_candidate(witness, interface, rows, targets, inputs, cap,
                     rng, knobs, budget, metrics):
    """Construct a new basis upstream, substitute every old downstream use."""
    if len(set(interface)) != len(interface) or _rank(interface) != len(interface):
        return
    k = len(interface)
    if len(rows) != k or any(isinstance(r, bool) or not isinstance(r, int) or
                            not 0 < r < (1 << k) for r in rows) or _rank(rows) != k:
        raise ValueError("basis matrix must be invertible and match the interface")
    safe = _unaffected(witness, inputs, interface, budget)
    basis = tuple(_linear_combination(interface, r) for r in rows)
    inverse = _inverse_coordinates(rows)
    substitutions = {m: tuple(basis[j] for j in range(k) if inverse[i] & (1 << j))
                     for i, m in enumerate(interface)}
    forbidden = set(interface) - set(basis)
    for _ in range(knobs["constructor_attempts"]):
        budget.spend()
        builder = _Constructor(witness, inputs, safe, basis, {}, forbidden, cap,
                               rng, knobs, budget, metrics)
        order = list(basis)
        rng.shuffle(order)
        if not all(builder.ensure(m) for m in order):
            metrics["construction_failures"] += 1
            continue
        recipes = dict(builder.recipes)
        depths = dict(builder.depths)
        okay = True
        # Replay the old chronological order so every non-interface consumer
        # refers to a previously rebuilt signal. No old interface is free.
        old_values = list(inputs)
        for ai, bi in witness["gates"]:
            budget.check()
            a, b = old_values[ai], old_values[bi]
            m = a ^ b
            old_values.append(m)
            if m in safe or m in interface or m in depths:
                continue
            terms = list(substitutions.get(a, (a,))) + list(substitutions.get(b, (b,)))
            if not all(p in depths for p in terms) or not _lower_expression(
                    m, terms, recipes, depths, inputs, cap, rng, budget):
                okay = False
                break
        if not okay:
            metrics["consumer_failures"] += 1
            continue
        # An interface signal which is itself an output remains mandatory.
        for m in set(interface) & set(targets):
            if not _lower_expression(m, substitutions[m], recipes, depths, inputs,
                                     cap, rng, budget):
                okay = False
                break
        if okay:
            result = _emit(recipes, targets, inputs, cap)
            if result is not None:
                metrics["basis_reconstructions"] += 1
                yield result


def _interface_sets(witness, targets, rng, knobs, budget):
    explicit = knobs["interface_sets"]
    if explicit is not None:
        for group in itertools.islice(explicit, knobs["max_interface_sets"]):
            budget.check()
            group = tuple(group)
            if len(group) not in (2, 3) or len(set(group)) != len(group) or \
                    any(isinstance(m, bool) or not isinstance(m, int) or m not in witness["masks"] for m in group):
                raise ValueError("interface_sets must contain distinct existing gate masks")
            if _rank(group) == len(group):
                yield group
        return
    focus = _focus_ancestors(witness, knobs["focus_outputs"], budget)
    fan = Counter(p for ab in witness["recipes"].values() for p in ab)
    values = list(witness["masks"])
    rng.shuffle(values)
    values.sort(key=lambda m: (m not in focus if focus else False,
                               m in targets, -fan[m], witness["depths"][m]))
    values = values[:knobs["interface_signal_limit"]]
    streams = [iter(itertools.combinations(values, k)) for k in knobs["interface_sizes"]]
    count = 0
    while streams and count < knobs["max_interface_sets"]:
        next_streams = []
        for stream in streams:
            budget.check()
            for group in stream:
                budget.check()
                if _rank(group) == len(group):
                    yield group
                    count += 1
                    next_streams.append(stream)
                    break
            if count >= knobs["max_interface_sets"]:
                return
        streams = next_streams


def _interface_bases(witness, targets, inputs, cap, rng, knobs, budget, metrics):
    for group in _interface_sets(witness, targets, rng, knobs, budget):
        budget.check()
        k = len(group)
        matrices = list(invertible_binary_bases(k)) if knobs["basis_matrices"] is None \
            else [tuple(rows) for rows in knobs["basis_matrices"] if len(rows) == k]
        if knobs["basis_matrices"] is None:
            rng.shuffle(matrices)
        for rows in matrices[:knobs["basis_matrix_limit"]]:
            if metrics["trials"] >= knobs["max_trials"]:
                return
            budget.spend()
            metrics["trials"] += 1
            metrics["basis_matrices"] += 1
            yield from _basis_candidate(witness, group, rows, targets, inputs, cap,
                                       rng, knobs, budget, metrics)


def _output_groups(witness, targets, rng, knobs, budget):
    values = list(dict.fromkeys(t for t in targets if t in witness["recipes"]))
    rng.shuffle(values)
    focus = set(knobs["focus_outputs"] or ())
    values.sort(key=lambda m: m not in focus if focus else False)
    streams = [iter(itertools.combinations(values, k)) for k in knobs["package_sizes"]]
    count = 0
    while streams and count < knobs["package_group_limit"]:
        following = []
        for stream in streams:
            budget.check()
            group = next(stream, None)
            if group is not None:
                yield group
                count += 1
                following.append(stream)
            if count >= knobs["package_group_limit"]:
                return
        streams = following


def _backward_packages(witness, targets, inputs, cap, rng, knobs, budget, metrics):
    for group in _output_groups(witness, targets, rng, knobs, budget):
        budget.check()
        safe = _unaffected(witness, inputs, group, budget)
        anchors = []
        for a in safe:
            budget.check()
            first = group[0] ^ a
            if not first:
                continue
            forced = [t ^ first for t in group[1:]]
            if 0 in forced:
                continue
            score = sum(m not in safe for m in [first] + forced)
            anchors.append((score, sum(m.bit_count() for m in [first] + forced if m not in safe),
                            rng.random(), a))
        anchors.sort()
        for _, _, _, a in anchors[:knobs["package_anchor_limit"]]:
            first = group[0] ^ a
            # Two/three demanded roles may collapse into existing values or
            # raw inputs. Construction gates, including any extra ancestors,
            # are always counted by the full final replay.
            topologies = (False, True) if len(group) == 3 else (False,)
            for chain in topologies:
                if metrics["trials"] >= knobs["max_trials"]:
                    return
                budget.spend()
                metrics["trials"] += 1
                overrides = {group[0]: (a, first)}
                previous = first
                roles = [first]
                for t in group[1:]:
                    parent = previous if chain else first
                    companion = t ^ parent
                    overrides[t] = (parent, companion)
                    roles.append(companion)
                    previous = companion
                if 0 in roles:
                    continue
                metrics["package_roles"] += len(roles)
                metrics["foreign_parent_roles"] += sum(bool(m & ~t) for t, ab in overrides.items() for m in ab)
                yield from _compose_overrides(witness, overrides, targets, inputs,
                                             cap, rng, knobs, budget, metrics)


def propose(kind, steps, targets, n_inputs, depth_cap, rng, knobs=None, should_stop=None, objective="gates", gate_limit=None, source_depth_cap=None):
    """Return ``(new_steps_or_none, metrics)`` for one bounded neighborhood.

    Kinds: ``component_merge``, ``interface_basis``, ``backward_package``.
    Input and output are chronological operand-index pairs. Every required
    target remains demanded; every returned gate is live. The caller owns
    acceptance, so a returned distinct proposal may be neutral or uphill.

    ``UNKNOWN`` means no distinct completed proposal was found within this
    bounded family. It never means impossibility. Even a FOUND result carries
    ``search_exhaustive=False``; this API does not provide optimality proofs.
    Invalid input/configuration raises ValueError rather than being hidden.
    """
    started = time.monotonic()
    kinds = {"component_merge": _component_merges, "interface_basis": _interface_bases,
             "backward_package": _backward_packages}
    if kind not in kinds:
        raise ValueError("unknown advanced move: " + str(kind))
    targets = tuple(targets)
    knobs = _configuration(knobs, targets)
    witness, inputs = _normalise(steps, targets, n_inputs,
                                 depth_cap if source_depth_cap is None else source_depth_cap)
    rng = random.Random(0) if rng is None else rng
    metrics = {"operator": kind, "status": "UNKNOWN", "search_exhaustive": False,
               "limit_reason": None, "nodes": 0, "trials": 0,
               "candidates_verified": 0, "unchanged": 0,
               "construction_failures": 0, "consumer_failures": 0,
               "constructor_gate_limits": 0, "basis_matrices": 0,
               "basis_reconstructions": 0, "deliberate_collisions": 0,
               "package_roles": 0, "foreign_parent_roles": 0,
               "before_gates": len(witness["gates"]), "before_depth": witness["depth"],
               "after_gates": None, "after_depth": None}
    budget = _Budget(knobs, metrics)
    budget.should_stop = should_stop
    best = None
    original = frozenset((m, tuple(sorted(ab))) for m, ab in witness["recipes"].items())
    try:
        budget.check()
        if knobs["max_nodes"] == 0 or knobs["max_trials"] == 0:
            metrics["limit_reason"] = "node_limit" if knobs["max_nodes"] == 0 else "trial_limit"
        else:
            for candidate in kinds[kind](witness, targets, inputs, depth_cap, rng, knobs, budget, metrics):
                budget.check()
                checked = verify_steps(candidate["gates"], targets, n_inputs, depth_cap, require_live=True)
                metrics["candidates_verified"] += 1
                signature = frozenset((m, tuple(sorted(ab))) for m, ab in checked["recipes"].items())
                if signature == original:
                    metrics["unchanged"] += 1
                    continue
                if best is None or objective_key(checked, objective, gate_limit) < \
                        objective_key(best, objective, gate_limit):
                    best = checked
            if metrics["trials"] >= knobs["max_trials"] and metrics["limit_reason"] is None:
                metrics["limit_reason"] = "trial_limit"
    except _SearchLimit:
        pass
    if best is not None:
        metrics["status"] = "FOUND"
        metrics["after_gates"] = len(best["gates"])
        metrics["after_depth"] = best["depth"]
    metrics["elapsed_seconds"] = time.monotonic() - started
    return (None if best is None else best["gates"]), metrics

