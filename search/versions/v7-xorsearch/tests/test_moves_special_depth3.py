"""Depth-3 specialist (``moves/depth3.py``): model completeness, exact accounting, the move.

* the split lists cover every depth-3 recipe of a weight-5..8 row (brute force);
* the partition's cost is the emitted circuit's exact gate count, and undo is exact;
* ``optimize_pairs`` matches brute force when it reports ``complete``;
* the move resyncs from the chain, proposes valid depth-3 circuits inside a journal, resumes
  exactly from ``state()`` and finds the known improvement on a small target;
* slow positive control (``XORSEARCH_SLOW=1``): MixColumns at depth 3 in <= 97 gates.
"""
import itertools
import json
import os
import random
import unittest

from xorsearch.config.settings import for_sections
from xorsearch.core.budget import Budget
from xorsearch.core.circuit import verify
from xorsearch.core.objective import Objective
from xorsearch.core.target import load_target, mixcolumns
from xorsearch.core.valueset import ValueSet
from xorsearch.moves import construct, depth3
from xorsearch.moves.base import MoveContext

SLOW = os.environ.get("XORSEARCH_SLOW") == "1"


def move_settings(**overrides):
    return for_sections(depth3.MOVE_KNOBS, overrides={
        "moves.depth3.anneal." + k: v for k, v in overrides.items()})


def context(state, move, seed, budget=None):
    return MoveContext(state=state, target=(state.n, state.rows), objective=None,
                       best_key=(state.size(),), rng=random.Random(seed), cfg=move.cfg,
                       budget=budget if budget is not None else Budget(None))


def naive_state(target, cap, seed):
    values, _ = construct.build_root("naive", target, random.Random(seed), cap=cap)
    n, rows = construct.target_rows(target)
    state = ValueSet(n, rows, values, cap=cap)
    state.trim()
    return state


class Model(unittest.TestCase):
    def test_splits_cover_every_depth3_recipe(self):
        n = 8
        rng = random.Random(1)
        for w in range(5, 9):
            t = sum(1 << i for i in rng.sample(range(n), w))
            model = depth3.Depth3Model(n, [t])
            brute = {tuple(sorted((a, t ^ a))) for a in range(1, 1 << n)
                     if a != t and a.bit_count() <= 4 and (t ^ a).bit_count() <= 4}
            self.assertEqual(set(model.splits[0]), brute, f"weight {w}")
            no_cancel = depth3.Depth3Model(n, [t], cancel_splits=False)
            self.assertEqual(set(no_cancel.splits[0]), {s for s in brute if not s[0] & s[1]})

    def test_row_classes(self):
        model = depth3.Depth3Model(6, [0, 1, 3, 7, 15, 31, 31, 63])
        self.assertEqual(model.T, [31, 63])
        self.assertEqual(model.forced_pairs, [3])
        self.assertEqual(model.forced_bigs, [7, 15])
        self.assertIsNotNone(depth3.root_reason(10, [1023], None))
        self.assertIsNotNone(depth3.root_reason(6, [63], 2))
        self.assertIsNone(depth3.root_reason(6, [63], None))


class PartitionAccounting(unittest.TestCase):
    def setUp(self):
        self.target = load_target("joltik")
        self.model = depth3.Depth3Model(16, self.target.rows)

    def check_exact(self, part):
        model = self.model
        snap = part.snapshot()
        gates, values, depth = construct.emit(16, self.target.rows, model.recipes(snap), cap=3)
        self.assertTrue(verify(gates, self.target, 3).ok)
        self.assertEqual(len(model.values(snap)), part.cost)
        self.assertEqual(part.cost, len(model.T) + len(part.big) + len(part.pairs))
        self.assertLessEqual(len(gates), part.cost)

    def test_cost_is_gate_count_and_undo_is_exact(self):
        rng = random.Random(3)
        part = depth3.Partition(self.model)
        part.restore(None, rng)
        self.check_exact(part)
        for _ in range(300):
            before = (part.snapshot(), dict(part.big), dict(part.pairs), part.cost)
            log = []
            part.log = log
            for _ in range(rng.randint(1, 4)):
                r = rng.random()
                o = rng.randrange(len(self.model.T))
                if r < 0.4:
                    part.set_choice(o, rng.randrange(len(self.model.splits[o])), rng)
                elif r < 0.7 and part.big:
                    part.repair(rng.choice(sorted(part.big)), rng)
                else:
                    part.greedy_rechoice(o, rng)
            part.log = None
            self.check_exact(part)
            if rng.random() < 0.5:
                part.undo(log, before[3])
                self.assertEqual((part.snapshot(), part.big, part.pairs, part.cost), before)

    def test_decode_round_trip(self):
        rng = random.Random(4)
        part = depth3.Partition(self.model)
        part.restore(None, rng)
        snap = part.snapshot()
        gates, _, _ = construct.emit(16, self.target.rows, self.model.recipes(snap), cap=3)
        decoded = self.model.decode(gates, 16)
        self.assertIsNotNone(decoded)
        self.assertLessEqual(len(self.model.values(decoded)), part.cost)
        # A circuit outside the model (a row built at depth 4) does not decode.
        values, info = construct.build_root("paar", self.target, random.Random(1))
        if info["depth"] > 3:
            self.assertIsNone(self.model.decode(info["gates"], 16))


class OptimizePairs(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(7)
        n = 7
        for trial in range(40):
            parents = set()
            while len(parents) < rng.randint(2, 5):
                parents.add(sum(1 << i for i in rng.sample(range(n), rng.choice((3, 4)))))
            existing = {sum(1 << i for i in rng.sample(range(n), 2)) for _ in range(rng.randint(0, 3))}
            pairs, pairings, complete = depth3.optimize_pairs(parents, existing, rng, 10_000)
            self.assertTrue(complete)
            model = depth3.Depth3Model(n, [])
            options = [model.pairing_options(m) for m in sorted(parents)]
            best = min(len(set().union(*map(set, combo)) - existing)
                       for combo in itertools.product(*options))
            self.assertEqual(len(pairs - existing), best)
            for m, pr in pairings.items():
                self.assertIn(pr, model.pairing_options(m))
                self.assertTrue(set(pr) <= pairs)


class Depth3Move(unittest.TestCase):
    def test_applicable(self):
        move = depth3.Depth3Anneal(move_settings())
        self.assertIsNone(move.applicable(mixcolumns(), Objective("gates", 3, None, 0)))
        # The real cap decides: the default soft slack (search cap 5) keeps the move on.
        self.assertIsNone(move.applicable(mixcolumns(), Objective("gates", 3, None, 2)))
        self.assertIsNotNone(move.applicable(mixcolumns(), Objective("gates", 4, None, 0)))
        self.assertIsNotNone(move.applicable(mixcolumns(), Objective("gates", None)))
        self.assertIsNotNone(move.applicable(load_target("fox-mu4"), Objective("gates", 3, None, 0)))

    def test_positive_control_small(self):
        # The chain builds 31 = (1^2 ^ 4^8) ^ 16 and 62 = (2^4) ^ (8^16 ^ 32): 8 gates, nothing
        # removable. Sharing 30 = 6 ^ 24 gives 31 = 30 ^ 1 and 62 = 30 ^ 32: 5 gates (optimal).
        state = ValueSet(6, [31, 62], [3, 12, 15, 6, 24, 56], cap=3)
        state.trim()
        before, key = state.size(), state.key()
        self.assertEqual(before, 8)
        move = depth3.Depth3Anneal(move_settings(iterations=500))
        proposal = move.propose(context(state, move, 1))
        self.assertIsNotNone(proposal.journal)
        self.assertTrue(state.ok())
        self.assertEqual(state.size(), 5)
        self.assertLessEqual(state.depth(), 3)
        state.rollback(proposal.journal)
        self.assertEqual(state.key(), key)
        state.check()

    def test_mixcolumns_chain_improves_and_stays_valid(self):
        state = naive_state(mixcolumns(), 3, 2)
        move = depth3.Depth3Anneal(move_settings(iterations=3000))
        sizes = [state.size()]
        for seed in range(3):
            proposal = move.propose(context(state, move, seed))
            self.assertTrue(proposal.deterministic)
            self.assertTrue(state.ok())
            self.assertLessEqual(state.depth(), 3)
            gates, _ = state.gates()
            self.assertTrue(verify(gates, mixcolumns(), 3).ok)
            if proposal.journal is not None:
                state.commit(proposal.journal)
            sizes.append(state.size())
            # The naive chain is larger than the seed's greedy start: never read back.
            self.assertFalse(proposal.trace["synced"])
        self.assertLess(sizes[-1], sizes[0] - 20)
        state.check()

    def test_resume_replays_exactly(self):
        target = load_target("joltik")
        first = depth3.Depth3Anneal(move_settings(iterations=400))
        a = naive_state(target, 3, 1)
        p = first.propose(context(a, first, 1))
        a.commit(p.journal)
        saved = json.loads(json.dumps(first.state()))
        second = depth3.Depth3Anneal(move_settings(iterations=400))
        second.load_state(saved)
        b = ValueSet(16, target.rows, a.values(), cap=3)
        pa = first.propose(context(a, first, 9))
        pb = second.propose(context(b, second, 9))
        self.assertEqual(pa.trace, pb.trace)
        self.assertEqual(a.key(), b.key())

    def test_budget_bounds_the_segment(self):
        state = naive_state(load_target("joltik"), 3, 1)
        move = depth3.Depth3Anneal(move_settings(iterations=5000))
        budget = Budget(640)
        proposal = move.propose(context(state, move, 1, budget))
        self.assertLessEqual(proposal.work, 640)
        self.assertTrue(state.ok())

    def test_other_caps_are_not_touched(self):
        state = naive_state(mixcolumns(), 4, 1)
        move = depth3.Depth3Anneal(move_settings())
        key = state.key()
        self.assertIsNone(move.propose(context(state, move, 1)))
        self.assertEqual(state.key(), key)
        # A real cap of 4 stays off even when the chain's own cap would allow depth 3.
        ctx = context(state, move, 1)
        ctx.objective = Objective("gates", 4, None, 0)
        self.assertIsNone(move.propose(ctx))

    def test_runs_under_the_soft_slack(self):
        # Regression: applicable() accepts a real cap of 3 with the default soft slack (search
        # cap 5), but propose() used to demand state.cap == 3, so the move never acted.
        objective = Objective("gates", 3, None, 2)
        state = ValueSet(6, [31, 62], [3, 12, 15, 6, 24, 56], cap=objective.search_cap)
        state.trim()
        move = depth3.Depth3Anneal(move_settings(iterations=500))
        self.assertIsNone(move.applicable((6, [31, 62]), objective))
        ctx = context(state, move, 1)
        ctx.objective = objective
        proposal = move.propose(ctx)
        self.assertIsNotNone(proposal)
        self.assertIsNotNone(proposal.journal)
        self.assertEqual(state.size(), 5)
        self.assertLessEqual(state.depth(), 3)
        state.rollback(proposal.journal)
        state.check()


@unittest.skipUnless(SLOW, "slow positive control: set XORSEARCH_SLOW=1 (about 100 s)")
class MixColumnsDepth3Control(unittest.TestCase):
    def test_97_at_depth_3(self):
        cfg = for_sections(*construct.KNOBS, depth3.ROOT_KNOBS, overrides={
            "construct.anneal3.iterations": 3_000_000})
        values, info = construct.build_root("anneal3", mixcolumns(), random.Random(1), cap=3,
                                            cfg=cfg)
        self.assertTrue(verify(info["gates"], mixcolumns(), 3).ok)
        self.assertLessEqual(info["gate_count"], 97)


if __name__ == "__main__":
    unittest.main()
