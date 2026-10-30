"""The engine on the real stack: ValueSet, registered moves, constructors, PlateauTracker,
NullRecorder and the independent verifier.

Skipped when a sibling module cannot be imported (the package is built in parallel); the fake
tests in test_engine_loop.py cover the engine on its own.
"""
import json
import unittest

try:
    from xorsearch.config.settings import build
    from xorsearch.core.circuit import verify
    from xorsearch.core.objective import Objective
    from xorsearch.core.target import random_target
    from xorsearch.engine import Engine
    from xorsearch.telemetry.recorder import NullRecorder
    MISSING = None
except Exception as exc:          # noqa: BLE001 - any import failure means "not built yet"
    MISSING = repr(exc)


@unittest.skipIf(MISSING, f"stack not importable: {MISSING}")
class RealStackTest(unittest.TestCase):
    def run_engine(self, objective, steps=400, seed=None, assignments=()):
        settings = build(assignments=("restart.stall_seconds=0.0", "restart.root_seconds=0.0",
                                      "restart.stall_proposals=150", "debug.check_every=25",
                                      *assignments))
        target = random_target(8, 8, seed=3)
        recorder = NullRecorder(None, "w0", settings)
        engine = Engine(target, objective, settings, rng_seed=7, recorder=recorder,
                        worker_id="w0", seed_circuit=seed)
        records = []

        def save(record):
            verdict = verify(record["circuit"], target)
            records.append((record, verdict))
            return {"equivalent": verdict.equivalent, "gate_count": verdict.gate_count,
                    "depth": verdict.depth}
        engine.on_record(save)
        start = engine.snapshot()
        for _ in range(steps):
            engine.step()
        return engine, records, start, target, settings, recorder

    def test_gates_objective_records_verify(self):
        obj = Objective("gates", depth_cap=None)
        engine, records, start, *_ = self.run_engine(obj)
        self.assertTrue(records, "a fresh root should improve within 400 proposals")
        for record, verdict in records:
            self.assertTrue(verdict.equivalent, verdict.reason)
            self.assertEqual(verdict.gate_count, record["gate_count"])
            self.assertEqual(verdict.depth, record["depth"])
        best = engine.snapshot()["worker_best"]
        self.assertLessEqual(best, start["worker_best"])
        self.assertEqual(engine.counters["verify_fail"], 0)

    def test_depth_capped_records_meet_the_cap(self):
        obj = Objective("gates", depth_cap=4, soft_depth_slack=2)
        engine, records, *_ = self.run_engine(obj)
        for record, verdict in records:
            self.assertTrue(verdict.equivalent)
            if record["kind"] != "frontier":     # deeper frontier points are valid records
                self.assertLessEqual(verdict.depth, 4)

    def test_checkpoint_resume_on_real_state(self):
        # Structural moves run under wall-clock budgets (deterministic=False), so exact
        # continuation is only promised for the deterministic moves, and only when the
        # scheduler charges work units: measured seconds shape every phase's probabilities.
        off = [f"moves.structural.{name}.{knob}=0.0" for name in ("translate", "cores")
               for knob in ("weight", "burst_weight")] + ["scheduler.cost=work"]
        obj = Objective("gates", depth_cap=5, soft_depth_slack=2)
        a, _, _, target, settings, _ = self.run_engine(obj, steps=200, assignments=off)
        self.assertFalse(any(m.family == "structural" for m in a._moves))
        data = json.loads(json.dumps(a.checkpoint()))
        b = Engine.resume(data, target, obj, settings,
                          recorder=NullRecorder(None, "w0", settings))
        for _ in range(200):
            self.assertEqual(a.step(), b.step())
        self.assertEqual(a.state.key(), b.state.key())
        self.assertEqual(a.rng.getstate(), b.rng.getstate())

    def test_dossiers_replay_on_real_moves(self):
        """Every improvement a real move made reproduces from its dossier alone (seed, values
        before, cap, move memory), with the verifier's verdict inside the dossier."""
        from xorsearch.engine.replay import replay_dossier
        obj = Objective("gates", depth_cap=None)
        engine, records, _, target, settings, recorder = self.run_engine(obj, steps=600)
        dossiers = [d for d in recorder.dossiers.values() if d["replay"]["seed"] is not None]
        self.assertTrue(dossiers)
        for d in dossiers:
            self.assertTrue(d["verification"]["equivalent"])
            d = json.loads(json.dumps(d))                     # as read back from disk
            if d["replay"]["replayable"] == "no":
                continue                                      # wall-clock moves: no promise
            out = replay_dossier(d, target, obj, settings)
            self.assertTrue(out["match"], (d["id"], d["move"], d["trace"]["components"],
                                           out.get("reason"), out.get("symdiff")))

    def deep_circuit(self):
        """The deepest record of an uncapped run, as circuit JSON."""
        _, records, *_ = self.run_engine(Objective("gates", depth_cap=None), steps=300)
        record = max((r for r, _ in records), key=lambda r: r["depth"])
        return record["circuit"], record["depth"]

    def test_seed_deeper_than_the_cap_is_repaired(self):
        from xorsearch.core.target import min_depth
        circuit, depth = self.deep_circuit()
        target = random_target(8, 8, seed=3)
        cap = depth - 1
        self.assertGreaterEqual(cap, min_depth(target.rows))
        obj = Objective("gates", depth_cap=cap, soft_depth_slack=0)
        engine, records, *_ = self.run_engine(obj, steps=50, seed=circuit)
        self.assertEqual(engine.source, "seed")
        self.assertTrue(engine.root.get("repaired"))
        for record, verdict in records:
            self.assertTrue(verdict.equivalent)
        # Off: the seed is replaced by a fresh root, as before.
        engine, *_ = self.run_engine(obj, steps=1, seed=circuit,
                                     assignments=("engine.seed_repair_tries=0",))
        self.assertEqual(engine.source, "fresh")

    def test_chain_without_feasible_best_exits_after_failed_repairs(self):
        obj = Objective("gates", depth_cap=4, soft_depth_slack=2)
        engine, *_ = self.run_engine(obj, steps=1, assignments=("restart.repair_exit=3",))
        restarts = engine.counters["restarts"]
        for i in range(3):
            engine.worker_best_key = engine.worker_best_values = None
            engine.chain_best_g, engine.chain_best_d = 40, 6           # over the cap
            engine._repair_expired = True
            engine._periodic()
            self.assertEqual(engine.counters["restarts"], restarts + (i == 2))
        self.assertEqual(engine.restarter.by_reason.get("repair_exhausted"), 1)
        self.assertEqual(engine._repair_misses, 0)

    def test_remove1_skips_dead_victims_until_the_state_changes(self):
        import random
        from xorsearch.core.budget import Budget
        from xorsearch.moves.base import MoveContext
        from xorsearch.moves.walk import RemoveOne
        obj = Objective("gates", depth_cap=3, soft_depth_slack=0)
        engine, _, _, target, settings, _ = self.run_engine(obj, steps=300)
        state = engine.state
        move = RemoveOne(settings)
        ctx = MoveContext(state=state, target=target, objective=obj, best_key=(),
                          rng=random.Random(1), cfg=move.cfg, budget=None)
        key = state.key()
        for _ in range(300):
            dead = set(move.dead)
            ctx.budget = Budget()
            prop = move.propose(ctx)
            victims = prop.trace.get("victims") or []
            for v in victims:
                self.assertNotIn(v, dead)
            if prop.journal is not None:
                state.rollback(prop.journal)
        self.assertEqual(state.key(), key)
        self.assertTrue(move.dead, "no remove1 victim was dead on a cap-3 state")
        self.assertEqual(move.dead_on, hash(key))
        data = json.loads(json.dumps(move.state()))
        other = RemoveOne(settings)
        other.load_state(data)
        self.assertEqual((other.dead_on, other.dead), (move.dead_on, move.dead))


if __name__ == "__main__":
    unittest.main()
