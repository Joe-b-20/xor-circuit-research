"""Root constructors (``moves/construct.py``): correctness, caps, budgets, mixture choice.

Every root must be a verified-correct circuit (checked here with the independent
``core.circuit.verify``), must respect a depth cap or fall back to naive, must be a pure function
of its RNG seed, and must cope with 1 to 64+ inputs, dense rows and odd rows (zero, unit,
repeated). The BP control checks the reason the upper-bound fallback exists: on InvMixColumns
(rows of weight 11 to 19) the greedy must actually run and beat naive by a wide margin.
"""
import random
import unittest

from xorflux.config.settings import for_sections
from xorflux.core.budget import Budget
from xorflux.core.circuit import verify
from xorflux.core.target import load_target, mixcolumns, random_target
from xorflux.core.valueset import ValueSet
from xorflux.moves import construct, depth3

ROOT_NAMES = ("naive", "paar", "bp", "anneal3")


def settings(**overrides):
    """Settings over the constructor sections only, with ``a.b.c`` overrides."""
    return for_sections(*construct.KNOBS, depth3.ROOT_KNOBS,
                        overrides={k.replace("__", "."): v for k, v in overrides.items()})


def check_root(case, n, rows, values, info, cap=None):
    """The root is correct: verified gates, a realizable ValueSet, depth within cap."""
    verdict = verify(info["gates"], (n, rows), cap)
    case.assertTrue(verdict.ok, verdict.reason)
    case.assertEqual(info["gate_count"], len(info["gates"]))
    case.assertEqual(len(values), len(set(values)))
    state = ValueSet(n, rows, values, cap=cap)
    case.assertTrue(state.ok())
    if cap is not None:
        case.assertLessEqual(state.depth(), cap)
    state.trim()
    case.assertLessEqual(state.size(), info["gate_count"])


class VerifyGates(unittest.TestCase):
    def test_rejections(self):
        rows = [0b0111, 0b0011]
        good = [[0, 1], [4, 2]]                    # 3, then 3 ^ 4 = 7
        self.assertEqual(construct.verify_gates(4, rows, good), 2)
        bad = {"non-topological": [[0, 4], [4, 2]], "self pair": [[0, 0]],
               "not a pair": [[0, 1, 2]], "not ints": [[0.0, 1]],
               "duplicate": [[0, 1], [4, 2], [0, 1]], "row missing": [[0, 1]]}
        for label, gates in bad.items():
            with self.subTest(label):
                with self.assertRaises(AssertionError):
                    construct.verify_gates(4, rows, gates)
        with self.assertRaises(AssertionError):
            construct.verify_gates(4, rows, good, cap=1)

    def test_emit_order_is_canonical(self):
        # Gates come out in (level, mask) order whatever order the recipes were recorded in.
        triples = [(0b0011, 1, 2), (0b1100, 4, 8), (0b0110, 2, 4), (0b1111, 3, 12)]
        rows = [0b1111, 0b0110]
        a = construct.emit(4, rows, triples)
        b = construct.emit(4, rows, list(reversed(triples)))
        self.assertEqual(a, b)
        self.assertEqual(a[1], [0b0011, 0b0110, 0b1100, 0b1111])


class RootCorrectness(unittest.TestCase):
    def test_every_root_on_real_targets(self):
        cfg = settings(construct__anneal3__iterations=3000, construct__bp__work=3_000_000)
        for name in ("joltik", "fox-mu4", "aes-invmixcolumns"):
            target = load_target(name)
            for root in ROOT_NAMES:
                with self.subTest(target=name, root=root):
                    values, info = construct.build_root(root, target, random.Random(5), cfg=cfg)
                    check_root(self, target.n_inputs, target.rows, values, info)
                    expect = root if construct.root_reason(root, target) is None else "naive"
                    self.assertEqual(info["built"], expect)

    def test_caps_are_respected(self):
        cfg = settings(construct__anneal3__iterations=2000)
        target = mixcolumns()
        for cap in (3, 4, 6):
            for root in ROOT_NAMES:
                with self.subTest(cap=cap, root=root):
                    values, info = construct.build_root(root, target, random.Random(cap), cap=cap,
                                                        cfg=cfg)
                    check_root(self, target.n_inputs, target.rows, values, info, cap)
                    self.assertLessEqual(info["depth"], cap)
                    self.assertIsNone(info["fallback"])

    def test_tight_cap_on_dense_rows(self):
        # InvMixColumns needs depth 5 (weight 19); paar and bp must still fit cap 5.
        target = load_target("aes-invmixcolumns")
        for root in ("naive", "paar", "bp"):
            with self.subTest(root=root):
                values, info = construct.build_root(root, target, random.Random(1), cap=5,
                                                    cfg=settings(construct__bp__work=2_000_000))
                check_root(self, target.n_inputs, target.rows, values, info, 5)

    def test_impossible_cap_raises(self):
        with self.assertRaises(ValueError):
            construct.build_root("paar", (4, [15]), random.Random(0), cap=1)

    def test_naive_reaches_minimum_depth(self):
        for seed in range(5):
            target = random_target(20, 12, density=0.6, seed=seed)
            values, info = construct.build_root("naive", target, random.Random(seed))
            self.assertEqual(info["depth"], target.min_depth)

    def test_same_seed_same_root(self):
        target = load_target("joltik")
        cfg = settings(construct__anneal3__iterations=2000)
        for root in ROOT_NAMES:
            with self.subTest(root=root):
                a, _ = construct.build_root(root, target, random.Random(11), cap=3, cfg=cfg)
                b, _ = construct.build_root(root, target, random.Random(11), cap=3, cfg=cfg)
                self.assertEqual(a, b)

    def test_odd_rows(self):
        # zero rows, unit rows, repeated rows, one input, all-free targets
        cases = [(5, [0, 1, 31, 31, 6, 4]), (1, [1, 0]), (3, [1, 2, 4]), (2, [3, 3, 0])]
        for n, rows in cases:
            for root in ROOT_NAMES:
                with self.subTest(rows=rows, root=root):
                    values, info = construct.build_root(root, (n, rows), random.Random(2))
                    check_root(self, n, rows, values, info)

    def test_wide_dense_target(self):
        target = random_target(70, 24, density=0.5, seed=3)
        cfg = settings(construct__bp__work=1_000_000)
        for root in ("naive", "paar", "bp"):
            with self.subTest(root=root):
                values, info = construct.build_root(root, target, random.Random(4), cfg=cfg)
                check_root(self, 70, target.rows, values, info)
            with self.subTest(root=root, cap=target.min_depth + 1):
                cap = target.min_depth + 1
                values, info = construct.build_root(root, target, random.Random(4), cap=cap, cfg=cfg)
                check_root(self, 70, target.rows, values, info, cap)


class RootBudgets(unittest.TestCase):
    def test_exhausted_budget_still_gives_a_circuit(self):
        target = load_target("aes-invmixcolumns")
        for root in ("paar", "bp"):
            with self.subTest(root=root):
                parent = Budget(5000)
                values, info = construct.build_root(root, target, random.Random(1), budget=parent)
                check_root(self, 32, target.rows, values, info)
                self.assertTrue(info["budget_exhausted"])
                self.assertGreaterEqual(parent.used, info["work"])

    def test_anneal3_iterations_bound_work(self):
        cfg = settings(construct__anneal3__iterations=500)
        values, info = construct.build_root("anneal3", mixcolumns(), random.Random(1), cap=3, cfg=cfg)
        self.assertEqual(info["iterations"], 500)
        check_root(self, 32, mixcolumns().rows, values, info, 3)


class BoyarPeralta(unittest.TestCase):
    def test_upper_bound_fallback_works_on_dense_rows(self):
        # The exact-tier-only clean-room BP produced no circuits on these rows (evidence).
        target = load_target("aes-invmixcolumns")
        naive, _ = construct.build_root("naive", target, random.Random(1))
        values, info = construct.build_root("bp", target, random.Random(1))
        check_root(self, 32, target.rows, values, info)
        self.assertGreater(info["steps"], 100)
        self.assertLess(info["gate_count"], 160)
        self.assertLess(info["gate_count"], len(naive) * 0.5)

    def test_every_tier_and_fallback_setting_is_valid(self):
        target = load_target("joltik")
        for tiers in (2, 3):
            for fallback in (0, 1, 2):
                for norm in ("max", "min", "none"):
                    cfg = settings(construct__bp__exact_tiers=tiers, construct__bp__fallback=fallback,
                                   construct__bp__norm=norm)
                    values, info = construct.build_root("bp", target, random.Random(3), cfg=cfg)
                    check_root(self, 16, target.rows, values, info)


class Emit(unittest.TestCase):
    def test_shallowest_recipe_wins_and_cycles_are_harmless(self):
        # 7 has a deep recipe (3 ^ 4 at level 3, via 3 = 5 ^ 6), a shallow one (6 ^ 1 at
        # level 2) and 6 also has a cyclic recipe through 7.
        triples = [(5, 1, 4), (3, 5, 6), (7, 3, 4), (6, 7, 1), (7, 6, 1), (6, 2, 4)]
        gates, values, depth = construct.emit(3, [7, 6], triples)
        self.assertTrue(verify(gates, (3, [7, 6])).ok)
        self.assertEqual(depth, 2)
        self.assertEqual(sorted(values), [6, 7])     # 3 and 5 are dead once 7 = 6 ^ 1

    def test_cap_failure_returns_none(self):
        self.assertIsNone(construct.emit(3, [7], [(3, 1, 2), (7, 3, 4)], cap=1))


class Mixture(unittest.TestCase):
    def test_weights_and_applicability(self):
        cfg = settings(construct__mix__naive=0.0, construct__mix__paar=0.0, construct__mix__bp=0.0)
        rng = random.Random(0)
        self.assertEqual(construct.choose_root(rng, cfg, mixcolumns(), 3), "anneal3")
        # rows of weight > 8: anneal3 is filtered out, nothing else has weight -> naive
        self.assertEqual(construct.choose_root(rng, cfg, load_target("fox-mu8"), None), "naive")
        counts = {}
        cfg = settings()
        for _ in range(2000):
            name = construct.choose_root(rng, cfg, load_target("aes-invmixcolumns"))
            counts[name] = counts.get(name, 0) + 1
        self.assertNotIn("anneal3", counts)
        self.assertGreater(counts["naive"], counts["paar"])

    def test_default_cfg_and_settings_object(self):
        name = construct.choose_root(random.Random(1))
        self.assertIn(name, construct.ROOTS)
        values, info = construct.build_root("paar", (4, [7, 11]), random.Random(1), cfg=None)
        self.assertEqual(info["built"], "paar")
        values, info = construct.build_root("anneal3", (4, [7, 11]), random.Random(1),
                                            cfg=settings())
        self.assertEqual(info["built"], "anneal3")


if __name__ == "__main__":
    unittest.main()
