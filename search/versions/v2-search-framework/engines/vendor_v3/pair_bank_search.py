"""Depth-three pair-bank search and scoped, rational construction bounds.

The search changes depth-one input pairs first, then reconsiders every output
split against the changed bank.  Its objective is the exact live union:
``number of outputs + number of pairs + number of weight-three/four parents``.
No heuristic search failure is an impossibility result.  Only
``solve_fixed_parents`` can report UNSAT, using a verified rational bound or a
completed exact search under explicit fixed-parent / retained-pair / budget
assumptions.  A decision certificate does not imply an exact optimum.
"""

from collections import Counter
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product
import math
import random
import time

from .deadline_search import earliest_witness, optimize_depth3


DEFAULT_KNOBS = {
    "persist_state": True,
    "checkpoint_seconds": 10.0,
    "max_iterations": None,
    "proposal_seconds": 0.08,
    "selection_sweeps": 2,
    "selection_restarts": 1,
    "constructor_sweeps": 1,
    "mutation_weights": {"swap": 0.50, "add": 0.25, "remove": 0.15, "shake": 0.10},
    "shake_remove": 2,
    "shake_add": 3,
    "addition_sample": 32,
    "addition_random_p": 0.35,
    "sa_T0": 0.8,
    "sa_T1": 0.08,
    "anneal_period": 1000,
    "max_uphill_gates": 4,
    "restart_patience": 500,
    "fixed_parent_every": 80,
    "fixed_parent_seconds": 0.02,
    "fixed_parent_nodes": 1500,
    "dual_passes": 3,
    "max_obstruction_cores": 24,
    "obstruction_focus_p": 0.65,
    "obstruction_tiebreak": True,
    "rotation_cache": True,
    "fixed_cache_limit": 128,
}


def _integer(value, name, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError("%s must be an integer in the permitted range" % name)
    return value


def _seconds(value, name="max_seconds"):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("%s must be finite and nonnegative" % name)
    return float(value)


def validate_knobs(knobs=None):
    """Return a fresh validated configuration; unknown keys are errors."""
    supplied = {} if knobs is None else dict(knobs)
    unknown = set(supplied) - set(DEFAULT_KNOBS)
    if unknown:
        raise ValueError("unknown pairbank3 knobs: %s" % ", ".join(sorted(unknown)))
    cfg = dict(DEFAULT_KNOBS)
    cfg["mutation_weights"] = dict(DEFAULT_KNOBS["mutation_weights"])
    cfg.update(supplied)
    for name in ("persist_state", "obstruction_tiebreak", "rotation_cache"):
        if type(cfg[name]) is not bool:
            raise ValueError("%s must be boolean" % name)
    for name in ("selection_sweeps", "constructor_sweeps", "shake_remove", "shake_add",
                 "max_uphill_gates", "restart_patience", "fixed_parent_every",
                 "fixed_parent_nodes", "max_obstruction_cores", "fixed_cache_limit"):
        _integer(cfg[name], name)
    for name in ("selection_restarts", "addition_sample", "anneal_period", "dual_passes"):
        _integer(cfg[name], name, 1)
    if cfg["max_iterations"] is not None:
        _integer(cfg["max_iterations"], "max_iterations")
    for name in ("checkpoint_seconds", "proposal_seconds", "fixed_parent_seconds", "sa_T0", "sa_T1"):
        cfg[name] = _seconds(cfg[name], name)
    if cfg["checkpoint_seconds"] <= 0 or cfg["sa_T0"] <= 0 or cfg["sa_T1"] <= 0:
        raise ValueError("checkpoint_seconds and temperatures must be positive")
    for name in ("addition_random_p", "obstruction_focus_p"):
        cfg[name] = _seconds(cfg[name], name)
        if cfg[name] > 1:
            raise ValueError("%s must be a probability" % name)
    weights = cfg["mutation_weights"]
    if not isinstance(weights, dict) or set(weights) != {"swap", "add", "remove", "shake"}:
        raise ValueError("mutation_weights must specify swap, add, remove and shake")
    cfg["mutation_weights"] = {name: _seconds(value, "mutation weight") for name, value in weights.items()}
    if sum(cfg["mutation_weights"].values()) <= 0:
        raise ValueError("at least one mutation weight must be positive")
    return cfg


def _masks(values, n_inputs=32, weights=None):
    _integer(n_inputs, "n_inputs", 1, 32)
    raw = list(values)
    for value in raw:
        if type(value) is not int or not 0 < value < (1 << n_inputs):
            raise ValueError("masks must be nonzero integers in the input universe")
        if weights is not None and value.bit_count() not in weights:
            raise ValueError("mask has a weight outside this scoped model")
    return set(raw)


@lru_cache(maxsize=32)
def all_input_pairs(n_inputs=32):
    _integer(n_inputs, "n_inputs", 1, 32)
    return tuple((1 << a) | (1 << b) for a, b in combinations(range(n_inputs), 2))


@lru_cache(maxsize=4096)
def parent_pairings(parent):
    """All depth-one pair requirements for one depth-two triple/quartet."""
    if type(parent) is not int or not 0 < parent < (1 << 32):
        raise ValueError("invalid parent mask")
    bits = [1 << bit for bit in range(32) if parent & (1 << bit)]
    if len(bits) == 3:
        return tuple((parent ^ bit,) for bit in bits)
    if len(bits) == 4:
        a, b, c, d = bits
        return ((a | b, c | d), (a | c, b | d), (a | d, b | c))
    raise ValueError("constructor parent must have weight three or four")


@lru_cache(maxsize=2048)
def enumerate_output_splits(target, n_inputs=32):
    """All normalized depth-three final splits, including foreign cancellation.

    Weight five: disjoint 1+4, disjoint 2+3, and 3+4 overlapping in
    one foreign input.  Weight seven: disjoint 3+4.  At n_inputs=32
    these are respectively 285 and 35 unordered split choices.
    """
    _masks([target], n_inputs, {5, 7})
    bits = [1 << bit for bit in range(n_inputs) if target & (1 << bit)]
    result = set()
    for size in ((4,) if len(bits) == 7 else (4, 3)):
        for chosen in combinations(bits, size):
            a = sum(chosen)
            result.add(tuple(sorted((a, target ^ a))))
    if len(bits) == 5:
        for chosen in combinations(bits, 3):
            base = sum(chosen)
            for bit in range(n_inputs):
                foreign = 1 << bit
                if not target & foreign:
                    a = base | foreign
                    result.add(tuple(sorted((a, target ^ a))))
    return tuple(sorted(result))


@lru_cache(maxsize=16)
def _catalogue(targets, n_inputs):
    menus = tuple(enumerate_output_splits(target, n_inputs) for target in targets)
    large = sorted({m for menu in menus for split in menu for m in split if m.bit_count() >= 3})
    return menus, tuple(large)


def _targets(targets, n_inputs):
    result = tuple(dict.fromkeys(targets))
    _masks(result, n_inputs, {5, 7})
    if not result:
        raise ValueError("at least one target is required")
    return result


def _fixed_problem(parents, retained_pairs, direct_pairs, n_inputs):
    parents = _masks(parents, n_inputs, {1, 2, 3, 4})
    retained = _masks(retained_pairs, n_inputs, {2})
    direct = _masks(direct_pairs, n_inputs, {2}) | {m for m in parents if m.bit_count() == 2}
    large = sorted(m for m in parents if m.bit_count() >= 3)
    paid_direct = direct - retained
    available = retained | direct
    rows = []
    for parent in large:
        options = parent_pairings(parent)
        # Credit only the largest retained subset of ONE legal construction.
        # Two overlapping retained pairs need not build a quartet for free.
        demand = min(len(set(option) - available) for option in options)
        eligible = set().union(*(set(option) for option in options)) - available
        if demand:
            rows.append((parent, demand, tuple(sorted(eligible))))
    return parents, retained, direct, paid_direct, rows


def rational_pair_bound(parents, retained_pairs=(), direct_pairs=(), n_inputs=32, passes=3):
    """A feasible rational packing dual for NEW pairs, under fixed requirements.

    A triple needs one constructor pair; a quartet needs a legal two-pair
    matching.  Each row's residual demand is the smallest new-pair count of
    any legal construction after retained and directly required pairs are
    credited.  For each still-unpaid pair p, sum(y_r : p in row_r) <= 1.
    Thus forced_direct + ceil(sum(demand_r*y_r)) is a safe lower bound.
    The packing heuristic need not find the best dual; validity is exact.
    """
    _integer(passes, "passes", 1)
    parent_set, retained, direct, forced, rows = _fixed_problem(parents, retained_pairs, direct_pairs, n_inputs)
    degrees = Counter(pair for _, _, eligible in rows for pair in eligible)
    best_weights = {parent: Fraction(0) for parent, _, _ in rows}
    best_value = Fraction(0)
    orderings = [
        sorted(rows, key=lambda row: (-row[1], len(row[2]), row[0])),
        sorted(rows, key=lambda row: (sum(degrees[p] for p in row[2]), -row[1], row[0])),
        list(reversed(rows)),
    ]
    for attempt in range(passes):
        order = orderings[attempt % len(orderings)]
        weights = {parent: Fraction(0) for parent, _, _ in rows}
        if attempt % 2:
            for parent, _, eligible in rows:
                weights[parent] = Fraction(1, max(degrees[p] for p in eligible))
        loads = Counter()
        for parent, _, eligible in rows:
            for pair in eligible:
                loads[pair] += weights[parent]
        for parent, _, eligible in order:
            slack = min(Fraction(1) - loads[pair] for pair in eligible)
            if slack > 0:
                weights[parent] += slack
                for pair in eligible:
                    loads[pair] += slack
        value = sum((demand * weights[parent] for parent, demand, _ in rows), Fraction(0))
        if value > best_value:
            best_value, best_weights = value, weights
    lower = len(forced) + math.ceil(best_value)
    certificate = {
        "schema_version": 1,
        "scope": "fixed parents at depth at most two; original unit inputs",
        "n_inputs": n_inputs,
        "parents": sorted(parent_set),
        "retained_pairs": sorted(retained),
        "direct_pairs": sorted(direct),
        "forced_new_pairs": sorted(forced),
        "rows": [{"parent": parent, "demand": demand, "eligible_pairs": list(eligible),
                  "weight": [best_weights[parent].numerator, best_weights[parent].denominator]}
                 for parent, demand, eligible in rows],
        "fractional_residual_bound": [best_value.numerator, best_value.denominator],
        "additional_pair_lower_bound": lower,
        "total_retained_pair_union_lower_bound": len(retained) + lower,
    }
    if not verify_rational_pair_bound(certificate):
        raise AssertionError("internal rational certificate failed validation")
    return certificate


def verify_rational_pair_bound(certificate):
    """Independently recompute row requirements and every rational capacity."""
    try:
        if (certificate.get("schema_version") != 1
                or certificate.get("scope") != "fixed parents at depth at most two; original unit inputs"):
            return False
        _, retained, _, forced, expected = _fixed_problem(
            certificate["parents"], certificate["retained_pairs"], certificate["direct_pairs"], certificate["n_inputs"])
        rows = certificate["rows"]
        if len(rows) != len(expected) or certificate["forced_new_pairs"] != sorted(forced):
            return False
        loads = Counter()
        value = Fraction(0)
        for row, (parent, demand, eligible) in zip(rows, expected):
            if (row["parent"], row["demand"], tuple(row["eligible_pairs"])) != (parent, demand, eligible):
                return False
            numerator, denominator = row["weight"]
            if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
                return False
            weight = Fraction(numerator, denominator)
            if weight < 0:
                return False
            value += demand * weight
            for pair in eligible:
                loads[pair] += weight
        if any(load > 1 for load in loads.values()):
            return False
        lower = len(forced) + math.ceil(value)
        return (certificate["fractional_residual_bound"] == [value.numerator, value.denominator]
                and certificate["additional_pair_lower_bound"] == lower
                and certificate["total_retained_pair_union_lower_bound"] == len(retained) + lower)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def fixed_parent_key(parents, retained_pairs=(), direct_pairs=(), n_inputs=32, byte_rotation=False):
    """Canonical construction-problem key, rotating ALL assumptions together.

    The key is for the optimal marginal construction count, independent of
    a later query budget.  It includes retained and direct pairs, input
    universe, and depth-two construction scope.  Cached witnesses require an
    inverse rotation; this module caches only completed scalar optima.
    """
    parent_set, retained, direct, _, _ = _fixed_problem(parents, retained_pairs, direct_pairs, n_inputs)
    if type(byte_rotation) is not bool:
        raise ValueError("byte_rotation must be boolean")
    if byte_rotation and n_inputs != 32:
        raise ValueError("byte rotation applies only to the complete 32-input universe")
    def rotate(mask, shift):
        return mask if not shift else ((mask << shift) | (mask >> (32 - shift))) & 0xFFFFFFFF
    variants = []
    for shift in ((0, 8, 16, 24) if byte_rotation else (0,)):
        variants.append(("pair-construction-v1", n_inputs, 2,
                         tuple(sorted(rotate(m, shift) for m in parent_set)),
                         tuple(sorted(rotate(m, shift) for m in retained)),
                         tuple(sorted(rotate(m, shift) for m in direct))))
    return min(variants)


def solve_fixed_parents(parents, max_new_pairs, retained_pairs=(), direct_pairs=(),
                        n_inputs=32, rng=None, max_seconds=0.05, max_nodes=1500, dual_passes=3):
    """Decide a fixed-parent new-pair budget, returning SAT/UNSAT/UNKNOWN.

    A replayable construction is SAT even if optimality search timed out.
    A verified rational lower bound above the budget proves conditional
    UNSAT immediately.  Otherwise a completed exact optimization can prove
    UNSAT; a cutoff without a fitting witness is UNKNOWN.  ``complete`` and
    ``optimal_complete`` mean an exact optimum was computed, whereas
    ``proof_complete`` means the SAT/UNSAT budget decision was certified.
    Obstruction cores are complete assumption sets, not necessarily minimal
    cores, and never imply an unrestricted AES impossibility.
    """
    _integer(max_new_pairs, "max_new_pairs")
    _integer(max_nodes, "max_nodes")
    max_seconds = _seconds(max_seconds)
    parent_set, retained, direct, _, _ = _fixed_problem(parents, retained_pairs, direct_pairs, n_inputs)
    bound = rational_pair_bound(parent_set, retained, direct, n_inputs, dual_passes)
    assumptions = {"n_inputs": n_inputs, "parent_depth_cap": 2, "parents": sorted(parent_set),
                   "retained_pairs": sorted(retained), "direct_pairs": sorted(direct),
                   "max_new_pairs": max_new_pairs}
    if (verify_rational_pair_bound(bound)
            and bound["additional_pair_lower_bound"] > max_new_pairs):
        return {"status": "UNSAT", "scope": "conditional fixed-parent construction only",
                "status_reason": "verified_rational_lower_bound_exceeds_budget",
                "assumptions": assumptions, "complete": False, "optimal_complete": False,
                "proof_complete": True, "best_new_pair_count": None,
                "minimum_new_pair_count": None, "construction": None, "bound": bound,
                "obstruction_core": assumptions}
    result = optimize_depth3(parent_set | direct, existing_pairs=retained, rng=rng,
                             max_seconds=max_seconds, max_nodes=max_nodes)
    if result is None:
        raise AssertionError("validated fixed-parent instance unexpectedly rejected")
    count = result["marginal_pair_count"]
    status = "SAT" if count <= max_new_pairs else ("UNSAT" if result["complete"] else "UNKNOWN")
    reasons = {"SAT": "verified_construction_within_budget",
               "UNSAT": "completed_exact_minimum_exceeds_budget",
               "UNKNOWN": "search_cutoff_without_budget_decision"}
    return {"status": status, "scope": "conditional fixed-parent construction only",
            "status_reason": reasons[status], "assumptions": assumptions,
            "complete": bool(result["complete"]), "optimal_complete": bool(result["complete"]),
            "proof_complete": status != "UNKNOWN",
            "best_new_pair_count": count, "minimum_new_pair_count": count if result["complete"] else None,
            "construction": result, "bound": bound,
            "obstruction_core": assumptions if status == "UNSAT" else None}


class _Selection:
    def __init__(self, targets, constructors, rng):
        self.targets, self.constructors, self.rng = targets, constructors, rng
        self.choices = [None] * len(targets)
        self.big = Counter()
        self.pairs = Counter()
        self.pairings = {}

    @property
    def cost(self):
        return len(self.targets) + len(self.big) + len(self.pairs)

    def _pair_change(self, pair, delta):
        self.pairs[pair] += delta
        if not self.pairs[pair]:
            del self.pairs[pair]

    def remove(self, output):
        old = self.choices[output]
        if old is None:
            return
        for parent in old:
            weight = parent.bit_count()
            if weight == 2:
                self._pair_change(parent, -1)
            elif weight >= 3:
                self.big[parent] -= 1
                if not self.big[parent]:
                    del self.big[parent]
                    for pair in self.pairings.pop(parent):
                        self._pair_change(pair, -1)
        self.choices[output] = None

    def extension(self, split, preferred=None):
        direct = {m for m in split if m.bit_count() == 2}
        new_big = [m for m in split if m.bit_count() >= 3 and m not in self.big]
        options = [self.constructors[m] for m in new_big]
        best = None
        for selection in product(*options):
            required = direct | set().union(*(set(pairing) for pairing in selection))
            delta = len(new_big) + len(required - self.pairs.keys())
            preferred_hits = sum(tuple(pairing) == tuple((preferred or {}).get(m, ()))
                                 for m, pairing in zip(new_big, selection))
            rank = (delta, -preferred_hits, self.rng.random())
            if best is None or rank < best[0]:
                best = (rank, dict(zip(new_big, selection)))
        return best[0][0], best[1]

    def add(self, output, split, pairings):
        if self.choices[output] is not None:
            raise AssertionError("output must be removed before replacement")
        self.choices[output] = tuple(split)
        for parent in split:
            weight = parent.bit_count()
            if weight == 2:
                self._pair_change(parent, 1)
            elif weight >= 3:
                if parent not in self.big:
                    self.pairings[parent] = tuple(pairings[parent])
                    for pair in self.pairings[parent]:
                        self._pair_change(pair, 1)
                self.big[parent] += 1

    def repair_constructors(self):
        order = list(self.big)
        self.rng.shuffle(order)
        for parent in order:
            old = self.pairings[parent]
            for pair in old:
                self._pair_change(pair, -1)
            options = list(self.constructors[parent])
            self.rng.shuffle(options)
            chosen = min(options, key=lambda option: len(set(option) - self.pairs.keys()))
            self.pairings[parent] = tuple(chosen)
            for pair in chosen:
                self._pair_change(pair, 1)

    def emit(self, n_inputs):
        index = {1 << bit: bit for bit in range(n_inputs)}
        depths = {1 << bit: 0 for bit in range(n_inputs)}
        gates, recipes = [], {}
        def add(mask, a, b):
            if mask in index or a not in index or b not in index or (a ^ b) != mask:
                raise AssertionError("invalid pair-bank recipe")
            gates.append([index[a], index[b]])
            index[mask] = n_inputs + len(gates) - 1
            depths[mask] = 1 + max(depths[a], depths[b])
            recipes[mask] = (a, b)
        for pair in sorted(self.pairs):
            bit = pair & -pair
            add(pair, bit, pair ^ bit)
        for parent in sorted(self.big):
            pair = self.pairings[parent][0]
            add(parent, pair, parent ^ pair)
        for target, split in zip(self.targets, self.choices):
            if split is None:
                raise AssertionError("cannot emit an incomplete assignment")
            add(target, *split)
        if len(gates) != self.cost or max(depths.values()) > 3:
            raise AssertionError("physical gate/depth accounting disagrees")
        return {"gates": gates, "masks": set(recipes), "recipes": recipes,
                "depths": depths, "depth": max(depths.values()),
                "output_indices": [index[t] for t in self.targets],
                "cost": self.cost, "pair_bank": set(self.pairs), "parents": set(self.big),
                "choices": list(self.choices), "pairings": dict(self.pairings)}


def decode_masks(mask_set, targets, n_inputs=32):
    """Recover a live normalized assignment from a chronological depth-3 bank."""
    targets = _targets(targets, n_inputs)
    masks = _masks(mask_set, n_inputs)
    if not set(targets) <= masks:
        raise ValueError("warm start is missing target masks")
    witness = earliest_witness(masks, targets, inputs=[1 << bit for bit in range(n_inputs)], cap=3)
    if witness is None:
        raise ValueError("warm start does not realize every target at depth three")
    choices = [tuple(sorted(witness["recipes"][target])) for target in targets]
    pairings = {}
    for output, split in enumerate(choices):
        if split not in enumerate_output_splits(targets[output], n_inputs):
            raise ValueError("warm start has a non-normalized depth-three output split")
        for parent in split:
            if parent.bit_count() >= 3:
                pairing = tuple(sorted(p for p in witness["recipes"][parent] if p.bit_count() == 2))
                if set(pairing) not in [set(option) for option in parent_pairings(parent)]:
                    raise ValueError("warm-start constructor is not a depth-one pair recipe")
                pairings[parent] = pairing
    constructors = {m: (pr,) for m, pr in pairings.items()}
    state = _Selection(targets, constructors, random.Random(0))
    for output, split in enumerate(choices):
        state.add(output, split, pairings)
    return state.emit(n_inputs)


def _restore_assignment(targets, choices, pairings, n_inputs=32):
    """Replay a complete snapshot without silently selecting different recipes."""
    if len(choices) != len(targets):
        raise ValueError("snapshot output count differs from target count")
    pairings = {int(parent): tuple(pr) for parent, pr in pairings.items()}
    constructors = {}
    for output, split in enumerate(choices):
        split = tuple(sorted(split))
        if split not in enumerate_output_splits(targets[output], n_inputs):
            raise ValueError("snapshot contains an illegal output split")
        for parent in split:
            if parent.bit_count() >= 3:
                pairing = pairings.get(parent)
                if pairing is None or set(pairing) not in [set(option) for option in parent_pairings(parent)]:
                    raise ValueError("snapshot contains an illegal constructor")
                constructors[parent] = (pairing,)
    state = _Selection(targets, constructors, random.Random(0))
    for output, split in enumerate(choices):
        state.add(output, tuple(sorted(split)), pairings)
    return state.emit(n_inputs)


def solve_pair_bank(pair_bank, targets, n_inputs=32, rng=None, incumbent=None,
                    max_seconds=0.08, sweeps=2, restarts=1, constructor_sweeps=1,
                    focus_outputs=(), obstructions=(), should_stop=None):
    """Choose all output splits from a proposed pair bank; return a live DAG.

    Every legal output split is considered for feasibility.  Output selection
    is bounded coordinate search, not exhaustive global optimization.  None
    means this call produced no complete candidate, never unrestricted UNSAT.
    Initial catalogue construction and one full valid assignment are finite
    setup/fallback work outside the local-improvement deadline.
    """
    started = time.monotonic()
    max_seconds = _seconds(max_seconds)
    _integer(sweeps, "sweeps")
    _integer(restarts, "restarts", 1)
    _integer(constructor_sweeps, "constructor_sweeps")
    targets = _targets(targets, n_inputs)
    bank = _masks(pair_bank, n_inputs, {2})
    focus = tuple(dict.fromkeys(focus_outputs))
    for output in focus:
        _integer(output, "focus output", 0, len(targets) - 1)
    rng = random.Random(0) if rng is None else rng
    all_menus, large = _catalogue(targets, n_inputs)
    constructors = {m: tuple(pr for pr in parent_pairings(m) if all(p in bank for p in pr)) for m in large}
    available = set(bank) | {1 << bit for bit in range(n_inputs)} | {m for m, choices in constructors.items() if choices}
    menus = [[split for split in menu if split[0] in available and split[1] in available] for menu in all_menus]
    if any(not menu for menu in menus):
        return None
    cores = [set(core.get("parents", ())) for core in obstructions if core.get("parents")]
    cutoff = started + max_seconds
    stopped = lambda: time.monotonic() >= cutoff or bool(should_stop and should_stop())
    best = None
    if incumbent is not None:
        checked = _restore_assignment(targets, incumbent["choices"], incumbent["pairings"], n_inputs)
        if checked["pair_bank"] <= bank:
            best = checked
    considered = completed_sweeps = 0
    for restart in range(restarts):
        if restart and stopped():
            break
        state = _Selection(targets, constructors, rng)
        order = list(range(len(targets)))
        rng.shuffle(order)
        order.sort(key=lambda o: (o not in focus, len(menus[o])))
        preferred = incumbent.get("pairings", {}) if incumbent is not None and restart == 0 else {}
        for output in order:
            old = tuple(incumbent["choices"][output]) if incumbent is not None and restart == 0 else None
            options = [old] if old in menus[output] else menus[output]
            chosen = min(((*state.extension(split, preferred), rng.random(), split) for split in options),
                         key=lambda row: (row[0], row[2]))
            state.add(output, chosen[3], chosen[1])
        candidate = state.emit(n_inputs)
        if best is None or candidate["cost"] < best["cost"]:
            best = candidate
        for _ in range(sweeps):
            if stopped():
                break
            order = list(range(len(targets)))
            rng.shuffle(order)
            order.sort(key=lambda o: o not in focus)
            for output in order:
                if stopped():
                    break
                state.remove(output)
                ranked = []
                for split in menus[output]:
                    delta, pairing = state.extension(split)
                    selected = {m for current_split in state.choices if current_split is not None for m in current_split} | set(split)
                    hit = sum(core <= selected for core in cores)
                    ranked.append((delta, hit, rng.random(), split, pairing))
                    considered += 1
                _, _, _, split, pairing = min(ranked, key=lambda row: row[:3])
                state.add(output, split, pairing)
            for _ in range(constructor_sweeps):
                if stopped():
                    break
                state.repair_constructors()
            candidate = state.emit(n_inputs)
            if candidate["cost"] <= best["cost"]:
                best = candidate
            completed_sweeps += 1
    best["stats"] = {"method": "pair-bank-first", "proposal_bank_pairs": len(bank),
                     "live_pairs": len(best["pair_bank"]), "eligible_splits": sum(map(len, menus)),
                     "considered_splits": considered, "sweeps_started": completed_sweeps,
                     "elapsed_s": time.monotonic() - started, "optimality_proved": False}
    return best


def _tuple_tree(value):
    return tuple(_tuple_tree(v) for v in value) if isinstance(value, list) else value


def engine_pairbank3(start_masks, cap, target, time_limit, seeds, knobs, ctx):
    """Campaign-compatible complementary depth-three pair-bank engine."""
    if type(cap) is not int or cap != 3:
        raise ValueError("pairbank3 requires the explicit depth cap 3")
    cfg = validate_knobs(knobs)
    if time_limit is not None:
        time_limit = _seconds(time_limit, "time_limit")
    if target is not None:
        _integer(target, "target")
    import mixcolumns_core as core
    targets = tuple(core.TARGETS)
    saved = getattr(ctx, "engine_states", {}).get("pairbank3", {}) if cfg["persist_state"] else {}
    rng = random.Random(seeds[0] if seeds else 1)
    if saved.get("rng_state") is not None:
        rng.setstate(_tuple_tree(saved["rng_state"]))
    initial = start_masks if start_masks is not None else saved.get("current_masks")
    current = decode_masks(core.naive_masks() if initial is None else initial, targets)
    if (saved.get("choices") is not None and saved.get("pairings") is not None
            and initial is not None and set(initial) == set(saved.get("current_masks", ()))):
        restored = _restore_assignment(targets, saved["choices"], saved["pairings"])
        if restored["masks"] != set(initial):
            raise ValueError("checkpoint assignment disagrees with its current masks")
        current = restored
    best = current
    old_best = saved.get("best_masks") or getattr(ctx, "best_masks", None)
    if old_best is not None:
        decoded = decode_masks(old_best, targets)
        if decoded["cost"] < best["cost"]:
            best = decoded
    ctx.improve(best["gates"], best["masks"], note="pairbank3 entry")
    iterations = int(saved.get("iterations", 0))
    last_improvement = int(saved.get("last_improvement", iterations))
    cores = list(saved.get("obstruction_cores", ()))[:cfg["max_obstruction_cores"]]
    # Completed scalar optima only.  Rebuilt each chunk; no checkpoint-provided
    # proof is trusted as a new exact result.  Saved cores affect ranking only.
    fixed_cache = {}
    all_pairs = all_input_pairs(32)
    _, large = _catalogue(targets, 32)
    popularity = Counter(p for m in large for pr in parent_pairings(m) for p in pr)
    started = time.monotonic()
    deadline = float("inf") if time_limit is None else started + time_limit
    next_checkpoint = started + cfg["checkpoint_seconds"]
    local_iterations = 0
    stats = Counter()
    def halted():
        callback = getattr(ctx, "should_stop", None)
        return time.monotonic() >= deadline or bool(callback and callback())
    def metric(name, amount=1):
        stats[name] += amount
        callback = getattr(ctx, "metric", None)
        if callback:
            callback("pairbank3." + name, amount)
        elif hasattr(ctx, "metrics"):
            key = "pairbank3." + name
            ctx.metrics[key] = ctx.metrics.get(key, 0) + amount
    def save():
        state = {"version": 1, "engine": "pairbank3", "current_masks": sorted(current["masks"]),
                 "best_masks": sorted(best["masks"]), "pair_bank": sorted(current["pair_bank"]),
                 "choices": [list(split) for split in current["choices"]],
                 "pairings": {str(m): list(pr) for m, pr in current["pairings"].items()},
                 "rng_state": rng.getstate(), "iterations": iterations,
                 "last_improvement": last_improvement, "obstruction_cores": cores,
                 "chunk_metrics": dict(stats), "scope": "depth-three heuristic search"}
        if hasattr(ctx, "engine_states"):
            ctx.engine_states["pairbank3"] = state
        callback = getattr(ctx, "checkpoint_engine", None)
        if callback:
            callback("pairbank3", state)
        return state
    def added_pair(bank):
        absent = [p for p in all_pairs if p not in bank]
        if not absent:
            return None
        if rng.random() < cfg["addition_random_p"]:
            return rng.choice(absent)
        sample = rng.sample(absent, min(cfg["addition_sample"], len(absent)))
        # The ranking is guidance only; a random branch keeps all 496 pairs
        # eligible across proposals.  No pair is removed from the universe.
        return max(sample, key=lambda p: (popularity[p], rng.random()))
    try:
        while not halted() and (target is None or best["cost"] > target):
            if cfg["max_iterations"] is not None and local_iterations >= cfg["max_iterations"]:
                break
            iterations += 1
            local_iterations += 1
            metric("iterations")
            proposal = None
            if cfg["fixed_parent_every"] and iterations % cfg["fixed_parent_every"] == 0:
                fixed = {m for split in current["choices"] for m in split}
                budget = max(0, len(current["pair_bank"]) - 1)
                key = fixed_parent_key(fixed, byte_rotation=cfg["rotation_cache"])
                metric("fixed_parent_calls")
                cached = fixed_cache.get(key)
                if cached is not None and cached > budget:
                    outcome = {"status": "UNSAT", "complete": True, "optimal_complete": True,
                        "proof_complete": True, "minimum_new_pair_count": cached,
                        "status_reason": "cached_completed_exact_minimum_exceeds_budget", "obstruction_core": {
                        "n_inputs": 32, "parent_depth_cap": 2, "parents": sorted(fixed),
                        "retained_pairs": [], "direct_pairs": sorted(m for m in fixed if m.bit_count() == 2),
                        "max_new_pairs": budget}, "cached_completed_optimum": cached}
                    metric("fixed_cache_hits")
                else:
                    outcome = solve_fixed_parents(fixed, budget, rng=rng,
                        max_seconds=min(cfg["fixed_parent_seconds"], max(0.0, deadline - time.monotonic())),
                        max_nodes=cfg["fixed_parent_nodes"], dual_passes=cfg["dual_passes"])
                    if outcome["optimal_complete"] and cfg["fixed_cache_limit"]:
                        fixed_cache[key] = outcome["minimum_new_pair_count"]
                        while len(fixed_cache) > cfg["fixed_cache_limit"]:
                            fixed_cache.pop(next(iter(fixed_cache)))
                metric("fixed_parent_" + outcome["status"].lower())
                if outcome["status"] == "UNSAT" and cfg["max_obstruction_cores"]:
                    obstruction = outcome["obstruction_core"]
                    if obstruction not in cores:
                        cores.append(obstruction)
                        cores = cores[-cfg["max_obstruction_cores"]:]
                elif outcome["status"] == "SAT":
                    bank = outcome["construction"]["pairs"]
                    proposal = solve_pair_bank(bank, targets, rng=rng, incumbent=current,
                        max_seconds=min(cfg["proposal_seconds"], max(0.0, deadline - time.monotonic())),
                        sweeps=cfg["selection_sweeps"], restarts=cfg["selection_restarts"],
                        constructor_sweeps=cfg["constructor_sweeps"], should_stop=halted)
            else:
                bank = set(current["pair_bank"])
                names, weights = zip(*cfg["mutation_weights"].items())
                operation = rng.choices(names, weights=weights, k=1)[0]
                remove = 1 if operation in ("swap", "remove") else (cfg["shake_remove"] if operation == "shake" else 0)
                add = 1 if operation in ("swap", "add") else (cfg["shake_add"] if operation == "shake" else 0)
                removed = set(rng.sample(sorted(bank), min(remove, len(bank))))
                bank.difference_update(removed)
                for _ in range(add):
                    pair = added_pair(bank)
                    if pair is not None:
                        bank.add(pair)
                focus = [o for o, split in enumerate(current["choices"]) if any(
                    (m in removed if m.bit_count() == 2 else bool(set(current["pairings"].get(m, ())) & removed))
                    for m in split)]
                if cores and rng.random() < cfg["obstruction_focus_p"]:
                    selected_core = set(rng.choice(cores)["parents"])
                    focus += [o for o, split in enumerate(current["choices"]) if selected_core.intersection(split)]
                metric("proposal_" + operation)
                proposal = solve_pair_bank(bank, targets, rng=rng, incumbent=current,
                    max_seconds=min(cfg["proposal_seconds"], max(0.0, deadline - time.monotonic())),
                    sweeps=cfg["selection_sweeps"], restarts=cfg["selection_restarts"],
                    constructor_sweeps=cfg["constructor_sweeps"], focus_outputs=focus,
                    obstructions=cores if cfg["obstruction_tiebreak"] else (), should_stop=halted)
            if proposal is None:
                metric("no_candidate")
            else:
                delta = proposal["cost"] - current["cost"]
                temperature = cfg["sa_T0"] * (cfg["sa_T1"] / cfg["sa_T0"]) ** ((iterations % cfg["anneal_period"]) / cfg["anneal_period"])
                accepted = delta <= 0 or (proposal["cost"] <= best["cost"] + cfg["max_uphill_gates"]
                                          and rng.random() < math.exp(-delta / temperature))
                if accepted:
                    current = proposal
                    metric("accepted")
                    if delta > 0:
                        metric("uphill")
                    if current["cost"] < best["cost"]:
                        best = current
                        last_improvement = iterations
                        ctx.improve(best["gates"], best["masks"], note="pairbank3 it=%d" % iterations)
                        metric("improvements")
            if cfg["restart_patience"] and iterations - last_improvement >= cfg["restart_patience"]:
                current = best
                last_improvement = iterations
                metric("snapbacks")
            if time.monotonic() >= next_checkpoint:
                save()
                next_checkpoint = time.monotonic() + cfg["checkpoint_seconds"]
    finally:
        result = save()
    return result
