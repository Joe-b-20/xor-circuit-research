"""Positive controls for the local moves: each must find a known improvement on a small circuit.

DESIGN section 5: every move ships with a small circuit where it must find a known one-gate
improvement before it gets fleet budget.  The instances were checked by brute force (exact
optimum over all value subsets) and, where the point is that *this* move is needed, the
simpler moves are shown to fail from the same start.

* 4-input toy: targets 0111, 1110 built through 0011 and 1100 (4 gates); optimum 3 through the
  shared 0110.  remove1 and LNS must find it.
* expand: 5 inputs, targets 30, 28, 27 from {6, 7, 22, 27, 28, 30} (6 gates, optimum 5): remove1
  cannot improve; remove-one/add-two can.
* deadline rebuild: 6 inputs, targets 31, 47 at cap 4 over the bank {3, 7, 15, 24, 40}: the
  greedy extract must use the fast unshared recipes (6 gates); the deadline beam builds both
  targets from the slower shared 15 = 7 ^ 8 at depth 4 (5 gates).
* depth repair: targets 31, 47 built as the chain 3, 7, 15 (5 gates, depth 4); at real cap 3 the
  repair finds 3, 12, 15 (5 gates, depth 3).
"""
import random
import unittest

from xorsearch.core.budget import Budget
from xorsearch.core.objective import Objective
from xorsearch.core.valueset import ValueSet
from xorsearch.moves import depth, lns, rebuild, walk
from xorsearch.tests.test_moves_local_util import (context, make_state, propose_many,
                                                   settings)

SEEDS = range(30)

TOY = (4, [0b0111, 0b1110], [0b0011, 0b0111, 0b1100, 0b1110])
EXPAND = (5, [30, 28, 27], [6, 7, 22, 27, 28, 30])
DEADLINE_ROWS = [31, 47]
DEADLINE_BANK = [3, 7, 15, 24, 40]
DEADLINE_CHAIN = [3, 7, 24, 40]          # the 6-gate greedy circuit (15 not in U)
DEPTH_CHAIN = [3, 7, 15]                 # 5 gates, depth 4


def gates_found(results):
    return sorted({g for g, _ in results})


class ToyControls(unittest.TestCase):
    """The 4-input toy: 4 -> 3 gates through the shared value 0110."""

    def test_remove1_finds_shared_value(self):
        n, rows, values = TOY
        self.assertEqual(make_state(n, rows, values).size(), 4)
        res = propose_many(self, walk.RemoveOne, n, rows, values, SEEDS)
        # Every victim works once the redundant old operand is peeled locally.
        self.assertEqual(len(res), len(SEEDS))
        self.assertEqual(gates_found(res), [3])

    def test_remove1_needs_local_peel_less_often_without_it(self):
        n, rows, values = TOY
        with_peel = propose_many(self, walk.RemoveOne, n, rows, values, SEEDS)
        without = propose_many(self, walk.RemoveOne, n, rows, values, SEEDS,
                               overrides={"moves.walk.repair.local_peel": False})
        hits_with = sum(g == 3 for g, _ in with_peel)
        hits_without = sum(g == 3 for g, _ in without)
        self.assertGreater(hits_with, hits_without)

    def test_lns_finds_shared_value(self):
        n, rows, values = TOY
        res = propose_many(self, lns.LNSRebuild, n, rows, values, SEEDS)
        self.assertIn(3, gates_found(res))


class ExpandControl(unittest.TestCase):
    """Remove one, add two: 6 -> 5 where no remove-one or remove-two step improves."""

    def test_simpler_moves_fail(self):
        n, rows, values = EXPAND
        for cls in (walk.RemoveOne,):
            res = propose_many(self, cls, n, rows, values, SEEDS)
            self.assertTrue(all(g >= 6 for g, _ in res), cls.name)

    def test_expand_finds_it(self):
        n, rows, values = EXPAND
        self.assertEqual(make_state(n, rows, values).size(), 6)
        res = propose_many(self, walk.Expand, n, rows, values, SEEDS)
        self.assertIn(5, gates_found(res))
        self.assertTrue(all(g <= 7 for g, _ in res), "expand may cost at most one gate")


class DeadlineControls(unittest.TestCase):
    """Slower shared recipes within the cap: 6 -> 5 at cap 4."""

    def test_greedy_cannot_but_deadline_can(self):
        params = rebuild.DeadlineParams(settings().view("moves.rebuild"))
        for seed in SEEDS:
            vs = ValueSet(6, DEADLINE_ROWS, DEADLINE_BANK, cap=4)
            chosen = rebuild.greedy(vs, {}, random.Random(seed), 0.0625)
            self.assertEqual(len(chosen), 6)
            result, stats = rebuild.reconstruct(vs, random.Random(seed), params, Budget(10 ** 6),
                                                cap=4)
            self.assertEqual(len(result), 5, stats)
            self.assertEqual(stats["baseline"], 6)
            # Applying the choice gives a valid 5-gate circuit at depth 4.
            j = vs.journal()
            rebuild.commit_choice(vs, result)
            self.assertTrue(vs.ok())
            self.assertEqual((vs.size(), vs.depth()), (5, 4))
            vs.rollback(j)

    def test_lns_deadline_strategy(self):
        res = propose_many(self, lns.LNSRebuild, 6, DEADLINE_ROWS, DEADLINE_CHAIN, SEEDS, cap=4,
                           overrides={"moves.lns.rebuild.strategy": "deadline"})
        self.assertIn(5, gates_found(res))


class CompletionCounter(unittest.TestCase):
    """The beam's incremental completion count against the full evaluation."""

    def test_upper_bound_on_random_overrides(self):
        """Random overrides (cycles allowed): never below the true size, usually equal."""
        from xorsearch.core.target import random_target
        checked = equal = 0
        for seed in range(6):
            target = random_target(7, 5, density=0.5, seed=seed)
            rng = random.Random(seed)
            extra = {rng.randrange(3, 1 << 7) for _ in range(40)}
            vs = ValueSet(7, target.rows, {v for v in extra if v.bit_count() > 1})
            targets = [t for t in vs.targets if t not in vs.iset]
            for layer in (None, {v: vs.par[v] for v in vs.live()}):
                fill = rebuild._Completer(targets, layer, vs.par, vs.iset)
                for _ in range(60):
                    chosen = {}
                    for v in rng.sample(sorted(vs.par), min(6, len(vs.par))):
                        alts = sorted(x for x in vs.tri[v] if x < v ^ x and x in vs.level
                                      and (v ^ x) in vs.level)
                        if alts:
                            chosen[v] = rng.choice(alts)
                    full = rebuild._evaluate(targets, chosen, layer, vs.par, vs.iset, 1 << 30)
                    if full is not None:
                        count = fill.count_with(chosen)
                        self.assertGreaterEqual(count, full[0])
                        checked += 1
                        equal += count == full[0]
        self.assertGreater(checked, 100)
        self.assertGreater(equal, 0.8 * checked)

    def test_exact_on_beam_completions(self):
        """Every completion the beam asks for on a real LNS bank (Joltik) is counted exactly."""
        from unittest import mock
        from xorsearch.core.target import load_target
        target = load_target("joltik")
        seed = next(sd for sd in target.seeds if sd.gates == 44)
        start = ValueSet(target.n_inputs, target.rows, seed.load(target.n_inputs).masks())
        start.trim()
        values = sorted(start.key())
        params = rebuild.DeadlineParams(settings().view("moves.rebuild"), max_states=200)
        seen = []
        original = rebuild._Completer.count_with

        def spy(fill, chosen):
            count = original(fill, chosen)
            full = rebuild._evaluate(fill.targets, chosen, fill.inc, fill.base, fill.iset,
                                     1 << 30)
            if full is not None:
                seen.append((count, full[0]))
            return count

        with mock.patch.object(rebuild._Completer, "count_with", spy):
            for i in range(8):
                rng = random.Random(i)
                pop = values + list(start.inputs)
                extra = {rng.choice(pop) ^ rng.choice(pop) for _ in range(30)}
                vs = ValueSet(target.n_inputs, target.rows,
                              values + [m for m in extra if m.bit_count() > 1])
                rebuild.reconstruct(vs, rng, params, Budget(10 ** 6),
                                    incumbents=[{v: start.par[v] for v in start.live()}])
        self.assertGreater(len(seen), 50)
        for count, true in seen:
            self.assertEqual(count, true)


class DepthControl(unittest.TestCase):
    """Same gates, one level shallower: 5/4 -> 5/3 at real cap 3."""

    def test_repair_to_real_cap(self):
        vs = make_state(6, DEADLINE_ROWS, DEPTH_CHAIN)
        self.assertEqual((vs.size(), vs.depth()), (5, 4))
        res = propose_many(self, depth.DepthRepair, 6, DEADLINE_ROWS, DEPTH_CHAIN, SEEDS,
                           objective=Objective(depth_cap=3))
        self.assertIn((5, 3), res)
        self.assertTrue(all(d <= 3 for _, d in res), "a repair never exceeds its goal")

    def test_squeeze_without_cap(self):
        res = propose_many(self, depth.DepthRepair, 6, DEADLINE_ROWS, DEPTH_CHAIN, SEEDS)
        self.assertIn((5, 3), res)

    def test_inapplicable_without_squeeze_or_cap(self):
        move = depth.DepthRepair(settings({"moves.depth.repair.squeeze": False}))
        self.assertIsNotNone(move.applicable(None, Objective()))
        self.assertIsNone(move.applicable(None, Objective(depth_cap=5)))
        self.assertIsNone(move.applicable(None, Objective(kind="depth_then_gates")))

    def test_free_rows_have_no_goal(self):
        # Regression: a depth-0 state (every row a unit or zero row) squeezed to goal -1 and
        # ran a rebuild; now it is a clean no-op.
        res = propose_many(self, depth.DepthRepair, 4, [1, 2, 0, 8], [], SEEDS[:2])
        self.assertEqual(res, [])
        move = depth.DepthRepair(settings())
        vs = make_state(4, [1, 2, 0, 8], [])
        prop = move.propose(context(move, vs, 1))
        self.assertEqual(prop.trace["reason"], "no_goal")


if __name__ == "__main__":
    unittest.main()
