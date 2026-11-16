"""Structural moves (``moves/structural.py``) and the vendored kernels (``xorsearch/vendor``).

* vendoring: each copy names its origin and the hash of the file it was copied from;
* move positive controls: on small 1-minimal value sets (nothing removable) each move finds a
  smaller circuit; the edit is journaled (rollback restores the state exactly), verified,
  within the cap and marked ``deterministic=False``;
* defaults: translate 0.2, cores 0.2, neither in the burst phase.
"""
import random
import unittest
from pathlib import Path

from xorsearch.config.settings import for_sections
from xorsearch.core.budget import Budget
from xorsearch.core.circuit import verify
from xorsearch.core.valueset import ValueSet
from xorsearch.moves import structural
from xorsearch.moves.base import REGISTRY, MoveContext

PACKAGE = Path(__file__).resolve().parents[1]
VENDOR = PACKAGE / "vendor"
MOVES = {"translate": structural.Translate, "cores": structural.Cores}

# Small 1-minimal chains where each move must find a smaller circuit:
# (n, rows, cap, values, gates). Found by random search over 4..7 inputs; each succeeded for
# at least 4 of 5 RNG seeds.
CONTROLS = {
    "translate": [(6, [27, 11, 29], None, [3, 11, 20, 27, 28, 29], 6),
                  (5, [21, 13, 28, 15], 3, [13, 15, 17, 19, 20, 21, 28], 7)],
    "cores": [(5, [19, 31], 3, [3, 19, 24, 28, 31], 5),
              (5, [14, 29], 4, [6, 7, 14, 18, 21, 29], 6)],
}


def settings(**overrides):
    return for_sections(*structural.KNOBS, overrides=overrides)


def generous():
    """Longer kernel limits so the controls do not depend on machine speed."""
    return settings(**{f"moves.structural.{name}.max_seconds": 1.0 for name in MOVES})


def run(move, state, seed):
    ctx = MoveContext(state=state, target=(state.n, state.rows), objective=None,
                      best_key=(state.size(),), rng=random.Random(seed), cfg=move.cfg,
                      budget=Budget(None))
    return move.propose(ctx)


class Vendoring(unittest.TestCase):
    def test_headers_name_origin_and_hash(self):
        # The origins (an earlier version's kernels) are not part of this repository; each copy
        # must still name its origin and the SHA-256 of the file it was copied from.
        paths = sorted(VENDOR.glob("v*_*.py"))
        self.assertEqual(len(paths), 2)
        for path in paths:
            with self.subTest(file=path.name):
                head = path.read_text().splitlines()[:3]
                self.assertRegex(head[0], r"^# Vendored for xorsearch from \S+$")
                self.assertRegex(head[1], r"^# Origin sha256: [0-9a-f]{64}$")


class MoveControls(unittest.TestCase):
    def test_each_move_finds_its_known_improvement(self):
        cfg = generous()
        for name, cases in CONTROLS.items():
            move = MOVES[name](cfg)
            for n, rows, cap, values, gates in cases:
                with self.subTest(move=name, rows=rows, cap=cap):
                    state = ValueSet(n, rows, values, cap=cap)
                    state.trim()
                    self.assertEqual(state.size(), gates)
                    self.assert_one_minimal(state)
                    key = state.key()
                    improved = 0
                    for seed in range(5):
                        proposal = run(move, state, seed)
                        self.assertIsNotNone(proposal)
                        self.assertFalse(proposal.deterministic)
                        self.assertEqual(proposal.move, move.name)
                        self.assertIn(move.kernel, proposal.trace["components"])
                        if proposal.journal is None:
                            self.assertEqual(state.key(), key)
                            continue
                        self.assertTrue(state.ok())
                        if cap is not None:
                            self.assertLessEqual(state.depth(), cap)
                        out, _ = state.gates()
                        self.assertTrue(verify(out, (n, rows), cap).ok)
                        improved += state.size() < gates
                        state.rollback(proposal.journal)
                        self.assertEqual(state.key(), key)
                        self.assertEqual(state.size(), gates)
                    state.check()
                    self.assertGreater(improved, 0)

    def assert_one_minimal(self, state):
        """No single non-target value can be removed (so walk's remove-1 cannot help)."""
        for v in state.values():
            if v in state.tset:
                continue
            j = state.journal()
            state.remove([v])
            ok = state.ok()
            state.rollback(j)
            self.assertFalse(ok, f"{v} is removable")

    def test_commit_keeps_the_edit(self):
        n, rows, cap, values, gates = CONTROLS["translate"][0]
        state = ValueSet(n, rows, values, cap=cap)
        move = structural.Translate(generous())
        for seed in range(5):
            proposal = run(move, state, seed)
            if proposal.journal is not None and state.size() < gates:
                state.commit(proposal.journal)
                break
        self.assertLess(state.size(), gates)
        state.check()
        self.assertEqual(ValueSet(n, rows, state.values(), cap=cap).size(), state.size())

    def test_trace_and_work(self):
        n, rows, cap, values, gates = CONTROLS["cores"][0]
        state = ValueSet(n, rows, values, cap=cap)
        move = structural.Cores(generous())
        proposal = run(move, state, 0)
        self.assertGreaterEqual(proposal.work, 1)
        for key in ("components", "params", "kernel", "kernel_seconds"):
            self.assertIn(key, proposal.trace)
        self.assertEqual(proposal.trace["params"]["max_roots"], 4)
        if proposal.journal is not None:
            self.assertTrue(proposal.trace["added"] or proposal.trace["removed"])

    def test_real_seed_proposals_are_valid(self):
        from xorsearch.core.target import load_target
        target = load_target("joltik")
        masks = target.seeds[0].load(target.n_inputs).masks()
        cfg = settings()
        for name, cls in MOVES.items():
            move = cls(cfg)
            for cap in (None, 8):
                with self.subTest(move=name, cap=cap):
                    state = ValueSet(target.n_inputs, target.rows, masks, cap=cap)
                    state.trim()
                    key = state.key()
                    for seed in range(2):
                        proposal = run(move, state, seed)
                        if proposal is None or proposal.journal is None:
                            continue
                        self.assertTrue(state.ok())
                        if cap is not None:
                            self.assertLessEqual(state.depth(), cap)
                        state.rollback(proposal.journal)
                        self.assertEqual(state.key(), key)


class Configuration(unittest.TestCase):
    def test_registered_with_default_weights(self):
        cfg = settings()
        expect = {"translate": 0.2, "cores": 0.2}
        for name, weight in expect.items():
            self.assertIs(REGISTRY[f"structural.{name}"], MOVES[name])
            self.assertEqual(cfg[f"moves.structural.{name}.weight"], weight)
            self.assertEqual(cfg[f"moves.structural.{name}.burst_weight"], 0.0)

    def test_wide_targets_are_not_applicable(self):
        move = structural.Translate(settings())
        self.assertIsNotNone(move.applicable((65, [3]), None))
        self.assertIsNone(move.applicable((64, [3]), None))

    def test_search_cap(self):
        from xorsearch.core.objective import Objective
        self.assertEqual(structural.search_cap(Objective("gates", 4, None, 2)), 6)
        self.assertIsNone(structural.search_cap(Objective("gates")))
        self.assertIsNone(structural.search_cap(None))


if __name__ == "__main__":
    unittest.main()
