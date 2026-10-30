"""Randomized invariants of the local moves (walk, lns, depth) on random and real targets.

For every proposal that edits the state:

* the state verifies through the independent ``core.circuit.verify`` replay, passes the kernel's
  from-scratch ``check()`` and is trimmed (DESIGN 4.3 move contract);
* the depth respects the state's (search) cap;
* ``rollback`` restores levels, witnesses, children and the triple index exactly;
* the trace is JSON-safe, names its components and clips its value lists.

Chains randomly commit or roll back, so moves also run on states with an edit history.  Replay:
a proposal on a state rebuilt from its values with the same RNG seed gives the same trace and the
same result, independent of the original state's dict/set history.
"""
import json
import random
import unittest

from xorflux.core.budget import Budget
from xorflux.core.objective import Objective
from xorflux.core.target import load_target, random_target
from xorflux.core.valueset import ValueSet
from xorflux.moves import lns
from xorflux.moves.rebuild import trace_limit
from xorflux.tests.test_moves_local_util import (MOVES, check_state, context, frozen,
                                                   settings)


def naive_values(target, rng):
    """Every row built as a random left-to-right chain of its input bits (a weak start)."""
    out = set()
    for row in target.rows:
        bits = [1 << i for i in range(target.n_inputs) if row >> i & 1]
        rng.shuffle(bits)
        acc = 0
        for b in bits:
            acc ^= b
            if acc.bit_count() > 1:
                out.add(acc)
    return out


def rebuilt(vs):
    """The state rebuilt from its values (as checkpoints and replays build states)."""
    return ValueSet(vs.n, vs.rows, vs.values(), cap=vs.cap, pairsums=vs.p2 is not None)


def check_trace(case, prop, limit):
    trace = prop.trace
    json.dumps(trace)
    json.dumps(prop.work)
    case.assertIsInstance(trace.get("components"), list)
    for key in ("removed", "added", "victims"):
        if key in trace:
            case.assertLessEqual(len(trace[key]), limit, key)
    case.assertGreaterEqual(prop.work, 0)


class RandomChains(unittest.TestCase):
    """Chains of random local moves with random commit/rollback, each step verified."""

    def run_chain(self, target, cap, steps, seed, objective=None):
        rng = random.Random(seed)
        s = settings()
        limit = trace_limit(s)
        moves = [cls(s) for cls in MOVES.values()]
        vs = ValueSet(target.n_inputs, target.rows, naive_values(target, rng), cap=cap,
                      pairsums=True)
        vs.trim()
        if not vs.ok():
            self.skipTest("naive start exceeds the cap")
        edited = 0
        for step in range(steps):
            move = moves[rng.randrange(len(moves))]
            before = frozen(vs)
            key = vs.key()
            prop = move.propose(context(move, vs, rng.getrandbits(32), objective, target=target))
            self.assertIsNotNone(prop, move.name)
            check_trace(self, prop, limit)
            if prop.journal is None:
                self.assertEqual(frozen(vs), before, move.name)
                continue
            edited += 1
            check_state(self, target, vs, cap)
            self.assertNotEqual(vs.key(), key, move.name + " returned an unchanged state")
            if rng.random() < 0.5:
                vs.commit(prop.journal)
            else:
                vs.rollback(prop.journal)
                self.assertEqual(frozen(vs), before, move.name + " rollback not exact")
        self.assertGreater(edited, 0)
        return vs

    def test_uncapped(self):
        for seed in range(4):
            target = random_target(7, 5, density=0.5, seed=seed)
            self.run_chain(target, None, 120, seed)

    def test_capped(self):
        for seed in range(4):
            target = random_target(7, 5, density=0.5, seed=10 + seed)
            start = ValueSet(target.n_inputs, target.rows,
                             naive_values(target, random.Random(seed)))
            cap = start.depth() + 1
            self.run_chain(target, cap, 120, seed, Objective(depth_cap=cap - 1,
                                                            soft_depth_slack=1))

    def test_depth_first_objective(self):
        target = random_target(8, 6, density=0.5, seed=99)
        self.run_chain(target, None, 80, 5, Objective(kind="depth_then_gates"))

    def test_tiny_budgets(self):
        """A proposal cut short by its budget still leaves a valid state or none at all."""
        target = random_target(8, 6, density=0.5, seed=3)
        s = settings()
        rng = random.Random(1)
        for cls in MOVES.values():
            move = cls(s)
            for seed in range(15):
                vs = ValueSet(target.n_inputs, target.rows, naive_values(target, rng),
                              pairsums=True)
                vs.trim()
                before = frozen(vs)
                ctx = context(move, vs, seed, target=target)
                ctx.budget = Budget(1 + seed % 4)
                prop = move.propose(ctx)
                if prop.journal is None:
                    self.assertEqual(frozen(vs), before)
                else:
                    check_state(self, target, vs, None)


class EdgeTargets(unittest.TestCase):
    """1-input and 70-input targets, unit / zero / repeated rows, caps of 1."""

    def propose_all(self, target, values, cap=None, objective=None, seeds=range(6)):
        s = settings()
        edited = 0
        for cls in MOVES.values():
            move = cls(s)
            for seed in seeds:
                vs = ValueSet(target.n_inputs, target.rows, values, cap=cap, pairsums=True)
                vs.trim()
                before = frozen(vs)
                prop = move.propose(context(move, vs, seed, objective, target=target))
                self.assertIsNotNone(prop, move.name)
                json.dumps(prop.trace)
                if prop.journal is None:
                    self.assertEqual(frozen(vs), before, move.name)
                    continue
                edited += 1
                check_state(self, target, vs, cap)
                vs.rollback(prop.journal)
                self.assertEqual(frozen(vs), before, move.name)
        return edited

    def test_one_input(self):
        from xorflux.core.target import Target
        target = Target.make("one", 1, [1, 0, 1])
        self.assertEqual(self.propose_all(target, []), 0)
        self.assertEqual(self.propose_all(target, [], cap=0), 0)

    def test_only_free_rows(self):
        from xorflux.core.target import Target
        target = Target.make("free", 5, [0, 1, 4, 4, 16, 0])
        self.assertEqual(self.propose_all(target, [3, 12]), 0)    # helpers are dead: trimmed

    def test_cap_one_with_repeats(self):
        from xorflux.core.target import Target
        target = Target.make("pairs", 6, [3, 6, 12, 3, 1, 0, 48])
        self.propose_all(target, [3, 6, 12, 48, 5], cap=1, objective=Objective(depth_cap=1))

    def test_seventy_inputs(self):
        target = random_target(70, 8, density=0.06, seed=4)
        values = naive_values(target, random.Random(4))
        self.assertGreater(self.propose_all(target, values, seeds=range(4)), 0)
        self.propose_all(target, values, cap=ValueSet(70, target.rows, values).depth(),
                         seeds=range(3))


class Replay(unittest.TestCase):
    """Same values + same RNG seed => same proposal, whatever the state's edit history."""

    def test_replay_on_rebuilt_state(self):
        target = random_target(8, 6, density=0.5, seed=7)
        s = settings()
        rng = random.Random(3)
        vs = ValueSet(target.n_inputs, target.rows, naive_values(target, rng), pairsums=True)
        vs.trim()
        # Give the state a history of committed edits.
        walker = MOVES["walk.remove1"](s)
        for i in range(30):
            prop = walker.propose(context(walker, vs, i, target=target))
            if prop.journal is not None:
                vs.commit(prop.journal)
        for name, cls in MOVES.items():
            for seed in range(5):
                copy = rebuilt(vs)
                results = []
                for state in (vs, copy):
                    move = cls(s)
                    prop = move.propose(context(move, state, 1000 + seed, target=target))
                    results.append((prop.trace, state.key()))
                    if prop.journal is not None:
                        state.rollback(prop.journal)
                self.assertEqual(results[0], results[1], name)


class LNSState(unittest.TestCase):
    """The LNS pool / hot list survive a checkpoint round trip and stay bounded."""

    def test_state_round_trip_and_bounds(self):
        target = random_target(8, 6, density=0.5, seed=11)
        s = settings({"moves.lns.rebuild.pool_limit": 50, "moves.lns.rebuild.hot_limit": 10})
        move = lns.LNSRebuild(s)
        rng = random.Random(2)
        vs = ValueSet(target.n_inputs, target.rows, naive_values(target, rng))
        vs.trim()
        for i in range(60):
            prop = move.propose(context(move, vs, i, target=target))
            if prop.journal is not None:
                vs.commit(prop.journal)
        data = json.loads(json.dumps(move.state()))
        self.assertLessEqual(len(data["pool"]), 50)
        self.assertLessEqual(len(data["hot"]), 10)
        self.assertGreater(len(data["hot"]), 0)
        other = lns.LNSRebuild(s)
        other.load_state(data)
        self.assertEqual(other.state(), move.state())
        copy = rebuilt(vs)
        a = move.propose(context(move, vs, 777, target=target))
        b = other.propose(context(other, copy, 777, target=target))
        self.assertEqual(a.trace, b.trace)
        self.assertEqual(vs.key(), copy.key())


class RealSeeds(unittest.TestCase):
    """A few verified proposals of every move on a real seed (Joltik 44 gates, depth 7)."""

    def test_joltik(self):
        target = load_target("joltik")
        seed = next(sd for sd in target.seeds if sd.gates == 44)
        s = settings()
        for cap in (None, 9):
            for name, cls in MOVES.items():
                move = cls(s)
                for i in range(6):
                    vs = ValueSet(target.n_inputs, target.rows,
                                  seed.load(target.n_inputs).masks(), cap=cap, pairsums=True)
                    vs.trim()
                    before = frozen(vs)
                    prop = move.propose(context(move, vs, i, Objective(depth_cap=7),
                                                target=target))
                    if prop.journal is None:
                        continue
                    check_state(self, target, vs, cap)
                    if name.startswith("walk.") and name != "walk.expand":
                        self.assertLessEqual(vs.size(), 44, name)
                    vs.rollback(prop.journal)
                    self.assertEqual(frozen(vs), before, name)


if __name__ == "__main__":
    unittest.main()
