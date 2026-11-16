"""Dossiers, verification, replay and the engine fixes of the telemetry review.

Covers: the verifier's verdict reaching the dossier (and a rejection undoing what was counted),
records carrying the dossier id as ``ref``, the ``replay`` block and ``replay_dossier``, the
plateau event naming the improvement that closed it, score objects in epoch fields, the final
partial epoch carrying engine fields, chain timers starting after a slow root build, the
frontier domination cache, and plateau drift surviving a resume.
"""
import json
import random
import tempfile
import unittest
from pathlib import Path

from xorflux.engine import Engine
from xorflux.engine.replay import replay_dossier
from xorflux.telemetry.metrics import PlateauTracker
from xorflux.telemetry.recorder import NullRecorder, Recorder, read_log
from xorflux.tests.test_engine_fakes import (
    FakeConstruct, FakeObjective, FakeRecorder, FakeTarget, RandomMove, ScriptMove,
    fake_factory, make_engine, mk, move_section, settings_for)

QUIET = {"restart.stall_seconds": 0.0, "restart.root_seconds": 0.0}


def build(specs, overrides=None, **kw):
    """Engine from ``specs``: (name, weight, factory(settings, name))."""
    over = dict(QUIET)
    over.update(overrides or {})
    settings = settings_for([move_section(name, w) for name, w, _ in specs], over)
    moves = [factory(settings, name) for name, _, factory in specs]
    kw.setdefault("seed", mk(10, 3))
    return make_engine(settings, moves, **kw), moves, settings


def script(*items, family="walk"):
    return lambda settings, name: ScriptMove(settings, name, items, family=family)


class VerificationTest(unittest.TestCase):
    def test_verdict_reaches_dossier_and_record_links_back(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(9, 3, 1)))], recorder=rec)
        seen = []
        eng.on_record(lambda r: seen.append(dict(r)) or {"ok": True, "saved": True,
                                                         "record": "records/g9.json"})
        eng.step()
        d = rec.improvements[0]
        self.assertEqual(d["verification"], {"ok": True, "saved": True,
                                             "record": "records/g9.json"})
        self.assertEqual(seen[0]["ref"], "imp1")          # the dossier id
        self.assertEqual(seen[0]["dossier"], "imp1")
        self.assertEqual(eng.last_improvement, "imp1")

    def test_rejection_undoes_counts_and_keeps_rejected_dossier(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(9, 3, 1)))], recorder=rec)
        eng.on_record(lambda r: {"ok": False, "reason": "not equivalent"})
        res = eng.step()
        self.assertFalse(res.improved_worker)
        self.assertEqual(rec.improvements, [])
        self.assertEqual(len(rec.rejected), 1)
        self.assertTrue(rec.rejected[0]["rejected"])
        self.assertEqual(eng.counters["improvements"], 0)   # was left at 1 before the fix
        self.assertEqual(eng.counters["verify_fail"], 1)
        self.assertEqual(eng.snapshot()["worker_best"], [10, 3])
        self.assertEqual(rec.of("verify_fail")[0]["id"], "imp1")

    def test_frontier_rejection_undoes_frontier_count(self):
        rec = FakeRecorder()
        # 11/2 is worse in gates but nondominated: a frontier point.
        eng, _, _ = build([("a", 1.0, script(mk(11, 2, 1)))], recorder=rec,
                          overrides={"acceptance.threshold.uphill_p": 1.0})
        eng.on_record(lambda r: {"ok": False})
        eng.step()
        self.assertEqual(eng.counters["frontier"], 0)
        self.assertEqual(eng.frontier, [(10, 3)])

    def test_real_recorder_writes_verified_dossier_and_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = Recorder(Path(tmp) / "w0", "w0")
            rec.begin("start", {})
            eng, _, _ = build([("a", 1.0, script(mk(9, 3, 1)))], recorder=rec)
            eng.on_record(lambda r: {"ok": True, "record": "workers/w0/records/x.json"})
            eng.step()
            rec.close()
            evs = list(read_log(Path(tmp) / "w0" / "events.jsonl"))
            imp = next(e for e in evs if e["ev"] == "improve")
            self.assertTrue(imp["verified"])
            self.assertEqual(imp["record"], "workers/w0/records/x.json")
            self.assertEqual(imp["replayable"], "exact")
            d = json.loads((Path(tmp) / "w0" / imp["dossier"]).read_text())
            self.assertTrue(d["verification"]["ok"])


class ReplayTest(unittest.TestCase):
    def test_replay_block_kinds(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(9, 3, 1)))], recorder=rec)
        eng.step()
        r = rec.improvements[0]["replay"]
        self.assertEqual((r["replayable"], r["reasons"]), ("exact", []))
        self.assertIsInstance(r["seed"], int)
        self.assertEqual(r["seed"], rec.improvements[0]["rng"]["seed"])

        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, lambda s, n: ScriptMove(s, n, [mk(9, 3, 1)]))],
                          recorder=rec, overrides={"engine.replay_seeds": False})
        eng.step()
        self.assertEqual(rec.improvements[0]["replay"]["replayable"], "no")
        self.assertIn("no_seed", rec.improvements[0]["replay"]["reasons"])

    def test_wall_clock_proposal_is_not_replayable(self):
        class Clocked(ScriptMove):
            def propose(self, ctx):
                prop = super().propose(ctx)
                if prop is not None:
                    prop.deterministic = False
                return prop
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, lambda s, n: Clocked(s, n, [mk(9, 3, 1)]))], recorder=rec)
        eng.step()
        r = rec.improvements[0]["replay"]
        self.assertEqual(r["replayable"], "no")
        self.assertEqual(r["reasons"], ["wall_clock"])

    def test_move_memory_snapshot_and_replay_reproduces(self):
        rec = FakeRecorder()
        eng, moves, settings = build([("rw", 1.0, lambda s, n: RandomMove(s, n, p_remove=0.6))],
                                     recorder=rec, seed=mk(30, 3))
        for _ in range(400):
            eng.step()
            if rec.improvements:
                break
        self.assertTrue(rec.improvements)
        d = json.loads(json.dumps(rec.improvements[0]))
        r = d["replay"]
        self.assertEqual(r["replayable"], "move_state")
        self.assertEqual(r["move_state"], {"counter": moves[0].counter})
        self.assertEqual(len(r["move_state_sha256"]), 64)
        out = replay_dossier(d, FakeTarget(), FakeObjective(), settings,
                             move=RandomMove(settings, "rw", p_remove=0.6),
                             state_factory=fake_factory)
        self.assertTrue(out["match"], out)
        # A wrong seed does not reproduce it.
        d["replay"]["seed"] += 1
        out = replay_dossier(d, FakeTarget(), FakeObjective(), settings,
                             move=RandomMove(settings, "rw", p_remove=0.6),
                             state_factory=fake_factory)
        self.assertFalse(out["match"])

    def test_digest_mode_and_replay_without_inputs(self):
        rec = FakeRecorder()
        eng, _, settings = build([("rw", 1.0, lambda s, n: RandomMove(s, n, p_remove=0.6))],
                                 recorder=rec, seed=mk(30, 3),
                                 overrides={"engine.replay_move_state": "digest"})
        while not rec.improvements:
            eng.step()
        r = rec.improvements[0]["replay"]
        self.assertNotIn("move_state", r)
        self.assertIn("move_state_sha256", r)
        out = replay_dossier({"values_before": None, "replay": {"seed": 1}}, FakeTarget(),
                             FakeObjective(), settings)
        self.assertFalse(out["match"])
        self.assertIn("values_before", out["reason"])

    def test_seed_reseeding_matches_random_random(self):
        """The fast C-level reseed gives exactly ``random.Random(seed)``, gauss cache too."""
        draws = []

        class Drawing(ScriptMove):
            def propose(self, ctx):
                draws.append((ctx.rng.gauss(0, 1), ctx.rng.random(), ctx.rng.getrandbits(40)))
                return super().propose(ctx)
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, lambda s, n: Drawing(s, n, [mk(9, 3, 1)]))], recorder=rec)
        eng._prng.gauss(0, 1)               # leaves a cached gauss value behind
        eng.step()
        ref = random.Random(rec.improvements[0]["replay"]["seed"])
        self.assertEqual(draws[0], (ref.gauss(0, 1), ref.random(), ref.getrandbits(40)))


class PreProposalStateTest(unittest.TestCase):
    def test_lns_peel_cache_is_undone_only_when_the_proposal_peeled(self):
        from xorflux.engine.replay import pre_proposal_state

        class Lns:
            name = "lns.rebuild"
        snap = {"pool": [3, 5], "hot": [3], "peel_seen": [11, 12], "pending": [[7], [], [5]]}
        peeled = pre_proposal_state(Lns(), snap, {"components": ["destroy.big", "peel"]})
        self.assertEqual(peeled["peel_seen"], [])
        self.assertEqual(peeled["pending"], [[], [], []])
        self.assertEqual(peeled["pool"], [3, 5])
        kept = pre_proposal_state(Lns(), snap, {"components": ["destroy.small", "bank"]})
        self.assertEqual(kept["peel_seen"], [11, 12])
        self.assertEqual(snap["peel_seen"], [11, 12])          # the dossier is not modified

        class Hooked:
            name = "x"

            def replay_state(self, snapshot, trace):
                return {"hooked": True}
        self.assertEqual(pre_proposal_state(Hooked(), snap, {}), {"hooked": True})


class PlateauAndEpochTest(unittest.TestCase):
    def test_plateau_closed_by_improvement_names_it(self):
        rec = FakeRecorder()
        items = [mk(10, 3, k) for k in range(1, 6)] + [mk(9, 3, 7)]
        eng, _, _ = build([("a", 1.0, script(*items))], recorder=rec,
                          overrides={"engine.plateau_event_min": 3})
        for _ in range(len(items)):
            eng.step()
        plats = rec.of("plateau")
        self.assertEqual(len(plats), 1)
        self.assertEqual(plats[0]["exit"], "improve")
        # Before the fix the event went out before the improvement existed, without its id.
        self.assertEqual(plats[0]["improvement"], "imp1")

    def test_epoch_scores_are_objects(self):
        rec = FakeRecorder()
        rec.epoch_flag = True
        eng, _, _ = build([("a", 1.0, lambda s, n: RandomMove(s, n))], recorder=rec,
                          overrides={"engine.periodic_every": 1})
        eng.step()
        f = rec.epochs[0]
        for key in ("chain", "chain_best", "worker_best"):
            self.assertEqual(set(f[key]), {"gates", "depth"}, key)
        self.assertTrue(all(set(p) == {"gates", "depth"} for p in f["frontier"]))
        self.assertNotIn("it", f)            # the envelope carries it

    def test_close_epoch_has_engine_fields(self):
        rec = NullRecorder()
        eng, _, _ = build([("a", 1.0, lambda s, n: RandomMove(s, n))], recorder=rec)
        for _ in range(20):
            eng.step()
        rec.close()
        epoch = [e for e in rec.events if e["ev"] == "epoch"][-1]
        self.assertTrue(epoch["partial"])
        self.assertIn("phase", epoch)
        self.assertIn("weights", epoch)
        self.assertEqual(set(epoch["chain_best"]), {"gates", "depth"})

    def test_chain_timers_start_after_root_build(self):
        rec = FakeRecorder()

        class SlowConstruct(FakeConstruct):
            def build_root(self, name, target, rng, cap=None, budget=None, cfg=None):
                rec.clock.advance(50.0)                    # a slow constructor
                return super().build_root(name, target, rng, cap, budget, cfg)
        eng, _, _ = build([("a", 1.0, script())], recorder=rec, construct=SlowConstruct(),
                          overrides={"restart.w_fresh": 1.0, "restart.w_elite": 0.0,
                                     "restart.w_shared": 0.0, "restart.w_best": 0.0})
        rec.clock.advance(10.0)
        self.assertTrue(eng._restart("manual"))
        self.assertEqual(eng.restarter.root_t, rec.clock.t)   # 60, not 10
        self.assertEqual(eng.restarter.ages(eng.it, 0, rec.clock.t)["root_s"], 0.0)


class FrontierCacheTest(unittest.TestCase):
    def test_dominated_points_are_cached_and_cleared(self):
        eng, _, _ = build([("a", 1.0, script())])
        self.assertEqual(eng.frontier, [(10, 3)])
        self.assertFalse(eng._new_frontier_point(10, 4))
        self.assertIn((10, 4), eng._dominated)
        self.assertFalse(eng._new_frontier_point(10, 4))     # cached
        self.assertTrue(eng._new_frontier_point(11, 2))
        self.assertNotIn((11, 2), eng._dominated)


class ResumeDriftTest(unittest.TestCase):
    def test_drift_measurable_after_resume(self):
        over = dict(QUIET, **{"scheduler.cost": "work"})
        settings = settings_for([move_section("rw", 1.0)], over)
        rec = FakeRecorder()
        a = Engine(FakeTarget(), FakeObjective(), settings, rng_seed=3, recorder=rec,
                   worker_id="w", seed_circuit=mk(30, 3), moves=[RandomMove(settings, "rw")],
                   state_factory=fake_factory, construct=FakeConstruct(),
                   plateau_tracker=PlateauTracker)
        for _ in range(100):
            a.step()
        data = json.loads(json.dumps(a.checkpoint()))
        b = Engine.resume(data, FakeTarget(), FakeObjective(), settings, recorder=FakeRecorder(),
                          moves=[RandomMove(settings, "rw")], state_factory=fake_factory,
                          construct=FakeConstruct(), plateau_tracker=PlateauTracker)
        self.assertIsNotNone(b._plateau.snapshot()["drift"])
        self.assertEqual(b._plateau.entry_key, b.chain_best_values)


class SharedLineageTest(unittest.TestCase):
    def test_shared_root_links_donor_improvement(self):
        root = Engine._shared_root({"record": "r1", "donor": "w9", "ref": "w9-000004"})
        self.assertEqual(root["improvement"], "w9-000004")
        root = Engine._shared_root({"record": "r2", "donor": "w9", "ref": "w9:it120"})
        self.assertIsNone(root["improvement"])                # a sampled DAG, not a dossier


if __name__ == "__main__":
    unittest.main()
