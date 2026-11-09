"""Foundation restarts (restart.w_foundation, restart.foundation.*): the level-1 restriction of
the ValueSet, the restricted root builder, the pinned phase on the real stack, and the default
path left exactly as it was.

The level-1 set of a circuit is its set of weight-2 values (XORs of two inputs).  Evidence for
the mechanism: ~/xs-campaigns/2026-11-02-why/foundations/REPORT.md.
"""
import hashlib
import json
import random
import unittest
from unittest import mock

from xorflux.config.settings import build
from xorflux.core.objective import Objective
from xorflux.core.target import load_map, random_target
from xorflux.core.valueset import ValueSet
from xorflux.engine import Engine
from xorflux.engine.restart import OPT_IN, RestartController
from xorflux.moves import construct
from xorflux.moves.base import load_all
from xorflux.telemetry.recorder import NullRecorder
from xorflux.tests.test_engine_fakes import settings_for

#: Structural moves run under wall-clock budgets; off, a fixed seed fixes the whole run.
DETERMINISTIC = tuple(f"moves.structural.{name}.{knob}=0.0" for name in ("translate", "cores")
                      for knob in ("weight", "burst_weight")) + ("scheduler.cost=work",)

#: Trajectory digest of ``default_run`` computed on the code before foundation restarts existed
#: (2026-11-09, commit 89b758d).  The default path must stay on exactly this trajectory; a later
#: deliberate change of the default search may update it (and say so in its commit).
GOLDEN_DEFAULT = "2fd16afc0105f80d9b32407d132ffd2b1086982dbd4b903c153389b4dc442e1d"

#: The move order of ``moves.base.load_all()`` in a fresh process.  The registry is filled in
#: import order, so after other test modules imported move modules first it can differ (e.g.
#: depth.repair first), and the scheduler's move indices with it; the run passes its moves in
#: this fixed order so the digest does not depend on which tests ran or were imported before.
FRESH_MOVE_ORDER = ("walk.remove1", "walk.expand", "lns.rebuild", "depth.repair",
                    "structural.translate", "structural.cores", "depth3.anneal")


def level1(values):
    return {v for v in values if v.bit_count() == 2}


def default_run(steps=1500, seed=11):
    """Digest of every StepResult, the final values and the restart sources of a 1,500-proposal
    run on small-scale-aes at cap 4 with default knobs (replayable triggers only)."""
    settings = build(assignments=("restart.stall_seconds=0.0", "restart.root_seconds=0.0",
                                  "restart.stall_proposals=150", *DETERMINISTIC))
    registry = load_all()
    moves = [registry[name](settings) for name in FRESH_MOVE_ORDER]
    engine = Engine(load_map("small-scale-aes"), Objective("gates", depth_cap=4), settings,
                    rng_seed=seed, recorder=NullRecorder(None, "w0", settings), worker_id="w0",
                    moves=moves)
    engine.on_record(lambda record: None)
    h = hashlib.sha256()
    for _ in range(steps):
        r = engine.step()
        h.update(json.dumps([r.it, r.move, r.phase, r.gates_after, r.depth_after, r.accepted,
                             r.improved_chain, r.improved_worker, r.work]).encode())
    h.update(json.dumps(sorted(engine.state.key())).encode())
    h.update(json.dumps(engine.restarter.by_source, sort_keys=True).encode())
    return h.hexdigest(), engine


class DefaultPathTest(unittest.TestCase):
    def test_default_run_is_unchanged_and_never_restricts(self):
        calls = []
        real = ValueSet.restrict_level1

        def spy(self, allowed):
            calls.append(allowed)
            return real(self, allowed)
        with mock.patch.object(ValueSet, "restrict_level1", spy), \
                mock.patch.object(Engine, "_foundation_source",
                                  side_effect=AssertionError("foundation source used")):
            digest, engine = default_run()
        self.assertGreaterEqual(engine.counters["restarts"], 2)     # the restart path ran
        self.assertEqual(calls, [])
        self.assertIsNone(engine._pin)
        self.assertIsNone(engine.state.l1allow)
        self.assertNotIn("foundation", engine.restarter.by_source)
        self.assertNotIn("foundation_pin", engine.checkpoint())
        self.assertEqual(digest, GOLDEN_DEFAULT)


class ValueSetRestrictionTest(unittest.TestCase):
    def setUp(self):
        self.target = random_target(8, 8, seed=3)
        values, _ = construct.build_root("naive", self.target, random.Random(1), cap=None)
        self.state = ValueSet(8, self.target.rows, values)
        self.state.trim()
        self.allowed = frozenset(level1(self.state.key()))
        self.pairs = [(1 << i) | (1 << j) for i in range(8) for j in range(i + 1, 8)]

    def test_never_gains_a_pair_outside_the_allowed_set(self):
        st, allowed = self.state, self.allowed
        st.restrict_level1(allowed)
        outside = [m for m in self.pairs if m not in allowed]
        self.assertTrue(outside)
        before = st.key()
        for m in outside:
            self.assertFalse(st.add(m))
        self.assertEqual(st.key(), before)
        rng = random.Random(5)
        for _ in range(300):                       # random edits inside journals
            j = st.journal()
            victims = rng.sample(sorted(st.key() - st.tset), 2) if len(st.key()) > 10 else []
            st.remove(victims)
            stuck = [v for v in st.tri if v not in st.level]
            for w in st.repair_candidates(stuck):
                self.assertTrue(w.bit_count() != 2 or w in allowed, w)
            for w in rng.sample(self.pairs, 3) + [rng.randrange(1, 256) for _ in range(3)]:
                st.add(w)
            self.assertLessEqual(level1(st.key()), allowed)
            if rng.random() < 0.5:
                st.rollback(j)
            else:
                st.commit(j)
            self.assertLessEqual(level1(st.key()), allowed)
        self.assertTrue(st.check())

    def test_members_may_be_dropped_and_re_added(self):
        st, allowed = self.state, self.allowed
        st.restrict_level1(allowed)
        member = min(allowed - st.tset)
        st.remove((member,))
        self.assertNotIn(member, st.key())
        self.assertTrue(st.add(member))
        self.assertIn(member, st.key())

    def test_violating_state_and_lifting(self):
        st = self.state
        with self.assertRaises(ValueError):
            st.restrict_level1(frozenset())           # its own pairs are outside
        st.restrict_level1(self.allowed)
        st.restrict_level1(None)
        outside = next(m for m in self.pairs if m not in self.allowed)
        self.assertTrue(st.add(outside))


class RestrictedRootTest(unittest.TestCase):
    def setUp(self):
        self.target = load_map("small-scale-aes")
        values, _ = construct.build_root("paar", self.target, random.Random(2), cap=4)
        self.allowed = frozenset(level1(values))

    def check_root(self, values, info, allowed, cap):
        n, rows = self.target.n_inputs, list(self.target.rows)
        self.assertLessEqual(construct.verify_gates(n, rows, info["gates"], cap), cap)
        self.assertLessEqual(level1(values), allowed | {t for t in rows if t.bit_count() == 2})
        st = ValueSet(n, rows, values, cap=cap)
        self.assertTrue(st.ok())

    def test_l1tree_respects_the_allowed_set(self):
        for seed in range(5):
            values, info = construct.build_restricted_root(
                ["l1tree"], self.target, self.allowed, random.Random(seed), cap=4)
            self.assertEqual(info["built"], "l1tree")
            self.check_root(values, info, self.allowed, 4)

    def test_generic_constructor_under_the_restriction(self):
        n, rows = self.target.n_inputs, list(self.target.rows)
        useful = frozenset(m for m in ((1 << i) | (1 << j) for i in range(n)
                                       for j in range(i + 1, n))
                           if any(t & m == m for t in rows))
        # naive pairs only bits of one row, so every useful pair allowed lets it complete.
        values, info = construct.build_restricted_root(["naive"], self.target, useful,
                                                       random.Random(3), cap=4)
        self.assertEqual(info["built"], "naive")
        self.check_root(values, info, useful, 4)
        # Falling back in order: naive cannot complete without pairs, nor can l1tree.
        with self.assertRaises(ValueError):
            construct.build_restricted_root(["naive", "l1tree"], self.target, frozenset(),
                                            random.Random(3), cap=4)
        values, info = construct.build_restricted_root(["naive", "l1tree"], self.target,
                                                       self.allowed, random.Random(4), cap=4)
        self.check_root(values, info, self.allowed, 4)
        if info["built"] == "l1tree":
            self.assertEqual(info["tried"][0][0], "naive")

    def test_unknown_constructor(self):
        with self.assertRaises(ValueError):
            construct.build_restricted_root(["nope"], self.target, self.allowed,
                                            random.Random(0), cap=4)


class FoundationRestartTest(unittest.TestCase):
    PIN = 300

    def engine(self, *assignments):
        settings = build(assignments=(
            "restart.stall_seconds=0.0", "restart.root_seconds=0.0",
            "restart.stall_proposals=100000", "restart.w_foundation=1.0",
            "restart.w_fresh=0.0", "restart.w_elite=0.0", "restart.w_shared=0.0",
            "restart.w_best=0.0", f"restart.foundation.pin_proposals={self.PIN}",
            "debug.check_every=50", "telemetry.null_keep_events=100000", *DETERMINISTIC,
            *assignments))
        target = load_map("small-scale-aes")
        obj = Objective("gates", depth_cap=4)
        engine = Engine(target, obj, settings, rng_seed=5,
                        recorder=NullRecorder(None, "w0", settings), worker_id="w0")
        engine.on_record(lambda record: None)
        return engine, target, obj, settings

    def events(self, engine, name):
        return [e for e in engine.recorder.events if e.get("ev") == name]

    def test_pinned_chain_stays_within_the_allowed_set_then_unpins(self):
        engine, *_ = self.engine("restart.foundation.swap_pairs=1",
                                 "restart.foundation.drop_pairs=1")
        for _ in range(200):
            engine.step()
        self.assertTrue(engine._restart("test"))
        self.assertEqual(engine.source, "foundation")
        restart = self.events(engine, "restart")[-1]
        root = restart["root"]
        self.assertEqual(restart["source"], "foundation")
        self.assertIn(root["donor_kind"], ("best", "elite"))
        self.assertEqual((len(root["swapped_out"]), len(root["dropped"])), (1, 1))
        self.assertEqual(root["pin_proposals"], self.PIN)
        allowed = engine._pin["allowed"]
        self.assertEqual(allowed, (set(root["level1"]) - set(root["swapped_out"])
                                   - set(root["dropped"])) | set(root["swapped_in"]))
        start = engine.it
        while engine._pin is not None:
            engine.step()
            self.assertLessEqual(level1(engine.state.key()), allowed)
            if engine._pin is not None:                  # (the last step may unpin)
                self.assertIs(engine.state.l1allow, allowed)
        self.assertGreaterEqual(engine.it - start, self.PIN)
        self.assertLess(engine.it - start, self.PIN + engine._periodic_every)
        unpin = self.events(engine, "foundation_unpin")
        self.assertEqual(len(unpin), 1)
        self.assertEqual(unpin[0]["reason"], "proposals")
        self.assertIn("level1_equals_allowed", unpin[0])
        self.assertIsNone(engine.state.l1allow)
        self.assertEqual(engine.restarter.by_source, {"foundation": 1})
        # Improvements made while pinned carry the restriction and replay under it.
        from xorflux.engine.replay import replay_dossier
        for d in engine.recorder.dossiers.values():
            replay = d["replay"]
            if replay.get("level1_allowed") is None or replay["replayable"] == "no":
                continue
            self.assertEqual(set(replay["level1_allowed"]), allowed)
            out = replay_dossier(json.loads(json.dumps(d)), engine.target, engine.objective,
                                 engine.settings)
            self.assertTrue(out["match"], out.get("reason"))

    def test_restart_during_the_pin_ends_it(self):
        engine, *_ = self.engine()
        for _ in range(100):
            engine.step()
        engine._restart("test")
        for _ in range(50):
            engine.step()
        engine._restart("test2")
        unpin = self.events(engine, "foundation_unpin")
        self.assertEqual([e["reason"] for e in unpin], ["restart"])
        self.assertIsNotNone(engine._pin)                # the new chain is pinned again

    def test_checkpoint_resume_keeps_the_pin(self):
        engine, target, obj, settings = self.engine()
        for _ in range(100):
            engine.step()
        engine._restart("test")
        for _ in range(64):
            engine.step()
        data = json.loads(json.dumps(engine.checkpoint()))
        self.assertIn("foundation_pin", data)
        other = Engine.resume(data, target, obj, settings,
                              recorder=NullRecorder(None, "w0", settings))
        self.assertEqual(other._pin["allowed"], engine._pin["allowed"])
        self.assertEqual(other.state.l1allow, engine._pin["allowed"])
        for _ in range(100):
            self.assertEqual(engine.step(), other.step())
        self.assertEqual(engine.state.key(), other.state.key())

    def test_no_constructor_completes_falls_back(self):
        engine, *_ = self.engine("restart.foundation.constructors=[\"naive\"]",
                                 "restart.foundation.drop_pairs=1000", "restart.w_best=0.001")
        for _ in range(100):
            engine.step()
        self.assertTrue(engine._restart("test"))
        self.assertEqual(engine.source, "best")
        self.assertTrue(self.events(engine, "foundation_failed"))
        self.assertIsNone(engine._pin)


class ControllerTest(unittest.TestCase):
    def make(self, **overrides):
        return RestartController(settings_for(
            overrides={f"restart.{k}": v for k, v in overrides.items()}).view("restart"))

    def test_foundation_only_with_weight_and_availability(self):
        avail = {"fresh": True, "elite": True, "shared": False, "best": True,
                 "foundation": True}
        rc = self.make()
        self.assertEqual(rc.weights["foundation"], 0.0)
        self.assertIn("foundation", OPT_IN)
        rng = random.Random(1)
        for _ in range(200):
            self.assertNotIn("foundation", rc.order(rng, avail))
        # All weights zero: the last-resort list still leaves the opt-in source out.
        zero = self.make(w_fresh=0.0, w_elite=0.0, w_shared=0.0, w_best=0.0)
        self.assertEqual(zero.order(rng, avail), ["fresh", "elite", "best"])
        rc = self.make(w_foundation=1.0)
        orders = [rc.order(rng, avail) for _ in range(300)]
        self.assertTrue(all("foundation" in o for o in orders))
        self.assertTrue(any(o[0] == "foundation" for o in orders))
        self.assertNotIn("foundation", rc.order(rng, {**avail, "foundation": False}))

    def test_default_order_draws_are_unchanged(self):
        """The new zero-weight source draws nothing extra from the RNG."""
        avail = {"fresh": True, "elite": True, "shared": True, "best": True}
        a, b = random.Random(9), random.Random(9)
        rc = self.make()
        got = [rc.order(a, {**avail, "foundation": True}) for _ in range(100)]
        legacy = [rc.order(b, avail) for _ in range(100)]
        self.assertEqual(got, legacy)
        self.assertEqual(a.getstate(), b.getstate())


if __name__ == "__main__":
    unittest.main()
