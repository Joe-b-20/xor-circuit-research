"""Engine integration tests over fakes: dossiers, phases, repair, restarts, records, checkpoint
and resume."""
import json
import random
import unittest

from xorflux.core.budget import Budget
from xorflux.engine import Engine
from xorflux.engine.loop import _seed_values
from xorflux.engine.phase import BURST, PLATEAU, REPAIR
from xorflux.moves.base import MoveContext
from xorflux.tests.test_engine_fakes import (
    BAD, FakeConstruct, FakeObjective, FakePlateau, FakePool, FakeRecorder, FakeState,
    FakeTarget, NoopMove, RandomMove, ScriptMove, fake_factory, make_engine, mk, move_section,
    settings_for)

QUIET = {"restart.stall_seconds": 0.0, "restart.root_seconds": 0.0}


def build(specs, overrides=None, **kw):
    """Engine from ``specs``: (name, weight, factory(settings, name)) per move."""
    over = dict(QUIET)
    over.update(overrides or {})
    sections = [move_section(name, weight) for name, weight, _ in specs]
    settings = settings_for(sections, over)
    moves = [factory(settings, name) for name, _, factory in specs]
    kw.setdefault("seed", mk(10, 3))
    return make_engine(settings, moves, **kw), moves, settings


def script(*items, family="walk"):
    return lambda settings, name: ScriptMove(settings, name, items, family=family)


def noop(settings, name):
    return NoopMove(settings, name)


class DossierTest(unittest.TestCase):
    def test_worker_best_dossier_contents(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(9, 3, 1)))], recorder=rec)
        records = []
        eng.on_record(lambda r: records.append(r) or {"path": "records/x.json"})
        res = eng.step()
        self.assertTrue(res.improved_worker and res.improved_chain and res.accepted)
        self.assertEqual(res.after, (9, 3))
        self.assertTrue(res.improved)
        self.assertEqual(len(rec.improvements), 1)
        d = rec.improvements[0]
        self.assertEqual(d["kind"], "gates")
        self.assertEqual(d["it"], 1)
        self.assertEqual(d["chain"]["engine_chain"], 1)
        self.assertEqual(d["chain"]["root"], {"id": "seed"})
        self.assertEqual(d["chain"]["source"], "seed")
        self.assertEqual(d["before"], {"gates": 10, "depth": 3})
        self.assertEqual(d["after"], {"gates": 9, "depth": 3})
        self.assertEqual(d["worker_best_before"], {"gates": 10, "depth": 3})
        self.assertEqual(d["values_before"], sorted(mk(10, 3)))
        self.assertEqual(d["values_after"], sorted(mk(9, 3, 1)))
        self.assertEqual(len(d["gates_after"]), 9)
        self.assertEqual(d["outputs"], [0])
        self.assertIsInstance(d["shape_after"], dict)
        self.assertEqual((d["move"], d["family"], d["phase"]), ("a", "walk", BURST))
        self.assertEqual(d["trace"]["components"], ["a", "edit"])
        self.assertEqual(d["trace"]["params"], {"n": 9})
        self.assertTrue(d["deterministic"])
        self.assertIsInstance(d["rng"]["seed"], int)
        self.assertEqual(d["rng"]["engine_seed"], 1)
        m = d["state_before"]
        for key in ("phase", "plateau", "neutral_rate", "acceptance", "weights",
                    "cur", "chain_best", "worker_best", "dist_chain_best", "dist_root",
                    "dist_elites", "chain_age"):
            self.assertIn(key, m)
        self.assertEqual(m["dist_chain_best"], 0.0)
        self.assertEqual(m["worker_best"], {"gates": 10, "depth": 3})
        self.assertEqual(set(m["weights"]), {"a"})
        self.assertTrue(json.dumps(d))                            # JSON-safe
        # The ring was taken after recorder.proposal, so it holds the improving proposal.
        self.assertEqual(rec.ring()[-1]["it"], 1)
        self.assertTrue(rec.ring()[-1]["improved_worker"])
        # The record goes to the callback after the dossier, carrying its id.
        r = records[0]
        self.assertEqual((r["kind"], r["dossier"], r["gate_count"], r["depth"]),
                         ("gates", "imp1", 9, 3))
        self.assertEqual(r["circuit"]["gateCount"], 9)
        self.assertEqual(r["circuit"]["inputCount"], 4)
        self.assertEqual(r["circuit"]["outputSignals"], [0])
        self.assertEqual(eng.snapshot()["worker_best"], [9, 3])
        self.assertEqual(eng.last_improvement, "imp1")

    def test_dossier_seed_replays_the_proposal(self):
        rec = FakeRecorder()
        eng, moves, settings = build(
            [("rw", 1.0, lambda s, n: RandomMove(s, n, p_remove=0.5, p_add=0.1))],
            seed=mk(30, 3), recorder=rec)
        for _ in range(200):
            eng.step()
            if rec.improvements:
                break
        d = rec.improvements[0]
        state = FakeState(d["values_before"])
        replay = RandomMove(settings, "rw", p_remove=0.5, p_add=0.1)
        ctx = MoveContext(state=state, target=FakeTarget(), objective=FakeObjective(),
                          best_key=(), rng=random.Random(d["rng"]["seed"]),
                          cfg=replay.cfg, budget=Budget(None))
        replay.propose(ctx)
        self.assertEqual(sorted(state.vals), d["values_after"])

    def test_verifier_rejection_reverts(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(9, 3, 1)))], recorder=rec)
        eng.on_record(lambda r: {"equivalent": False, "error": "mismatch"})
        res = eng.step()
        self.assertFalse(res.improved_worker)
        self.assertEqual(eng.snapshot()["cur"], [10, 3])
        self.assertEqual(eng.snapshot()["worker_best"], [10, 3])
        self.assertEqual(eng.frontier, [(10, 3)])
        self.assertEqual(sorted(eng.state.vals), sorted(mk(10, 3)))
        self.assertIsNone(eng.last_improvement)
        self.assertEqual(rec.of("verify_fail")[0]["id"], "imp1")
        self.assertEqual(rec.of("restart")[0]["reason"], "verify_fail")
        self.assertEqual(eng.snapshot()["chain_best"], [10, 3])

    def test_frontier_point(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(11, 2, 1)))], recorder=rec,
                          overrides={"acceptance.threshold.uphill_p": 1.0},
                          objective=FakeObjective(depth_cap=5), seed=mk(10, 4))
        eng.step()
        self.assertEqual(rec.improvements[0]["kind"], "frontier")
        self.assertEqual(eng.frontier, [(10, 4), (11, 2)])
        self.assertEqual(eng.snapshot()["worker_best"], [10, 4])

    def test_depth_tie_break_kind(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(mk(10, 2, 1)))], recorder=rec,
                          objective=FakeObjective(depth_cap=5))
        eng.step()
        self.assertEqual(rec.improvements[0]["kind"], "depth")
        self.assertEqual(eng.frontier, [(10, 2)])


class PhaseFlowTest(unittest.TestCase):
    def test_burst_after_new_best_then_plateau(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, script(*(["noop"] * 5), mk(9, 3, 1), *(["noop"] * 8)))],
                          recorder=rec, overrides={"phase.burst_budget": 5})
        self.assertEqual(eng.phase.phase, BURST)                 # a fresh chain starts bursting
        for _ in range(4):
            eng.step()
        self.assertEqual(eng.phase.phase, BURST)
        eng.step()
        self.assertEqual(eng.phase.phase, PLATEAU)               # initial budget spent
        eng.step()                                              # the improvement
        self.assertEqual(eng.phase.phase, BURST)
        for _ in range(5):
            eng.step()
        self.assertEqual(eng.phase.phase, PLATEAU)
        reasons = [e["reason"] for e in rec.of("phase")]
        self.assertEqual(reasons[-2:], ["chain best", "budget"])

    def test_repair_flow_to_feasible_record(self):
        rec = FakeRecorder()
        specs = [("g", 1.0, script(mk(9, 5, 1))),
                 ("d", 0.0, script(mk(9, 4, 2), mk(9, 3, 3), family="depth"))]
        eng, _, _ = build(specs, recorder=rec, objective=FakeObjective(depth_cap=3,
                                                                       soft_depth_slack=2),
                          overrides={"scheduler.mode": "fixed", "phase.repair_share": 1.0})
        cands = []
        eng.on_record(lambda c: cands.append(c) or {"ok": True})
        r1 = eng.step()                                          # 9/5: beats 10/3, too deep
        self.assertEqual(r1.move, "g")
        self.assertTrue(r1.improved_chain and not r1.improved_worker)
        self.assertEqual(eng.phase.phase, REPAIR)
        # Too deep for the cap, but a valid circuit: recorded as a frontier point.
        self.assertEqual([(c["kind"], c["depth"]) for c in cands], [("frontier", 5)])
        r2 = eng.step()                                          # 9/4: still too deep
        self.assertEqual(r2.move, "d")
        self.assertEqual(eng.phase.phase, REPAIR)
        r3 = eng.step()                                          # 9/3: feasible
        self.assertTrue(r3.improved_worker)
        self.assertEqual(eng.phase.phase, BURST)
        self.assertEqual([(c["gate_count"], c["depth"]) for c in cands], [(9, 5), (9, 4), (9, 3)])
        self.assertEqual(rec.improvements[-1]["after"], {"gates": 9, "depth": 3})
        self.assertEqual(rec.improvements[-1]["state_before"]["phase"], REPAIR)

    def test_repair_rejects_deepening_sideways_moves(self):
        specs = [("g", 1.0, script(mk(9, 4, 1))),
                 ("d", 0.0, script(mk(9, 5, 2), family="depth"))]
        eng, _, _ = build(specs, objective=FakeObjective(depth_cap=3, soft_depth_slack=2),
                          overrides={"scheduler.mode": "fixed", "phase.repair_share": 1.0})
        eng.step()
        res = eng.step()
        self.assertEqual(res.move, "d")
        self.assertFalse(res.accepted)
        self.assertEqual(eng.snapshot()["cur"], [9, 4])

    def test_soft_cap_bound_and_gate_limit(self):
        eng, _, _ = build([("a", 1.0, script(mk(9, 6, 1), "bad", mk(11, 3, 2)))],
                          objective=FakeObjective(depth_cap=3, soft_depth_slack=2,
                                                  gate_limit=10),
                          overrides={"acceptance.threshold.uphill_p": 1.0})
        for _ in range(3):
            self.assertFalse(eng.step().accepted)
        self.assertEqual(eng.counters["infeasible"], 2)          # depth 6 > 5, and BAD
        self.assertEqual(eng.counters["gate_limit"], 1)
        self.assertEqual(sorted(eng.state.vals), sorted(mk(10, 3)))


class AcceptanceFlowTest(unittest.TestCase):
    def test_commit_on_plain_accept(self):
        eng, _, _ = build([("a", 1.0, script(mk(10, 3, 1)))])
        eng.step()
        self.assertEqual(eng.state.commits, 1)


class RecordTest(unittest.TestCase):
    def test_distinct_dags_at_best_point(self):
        rec = FakeRecorder()
        states = [mk(10, 3, v) for v in range(1, 40)]
        eng, _, _ = build([("a", 1.0, script(*states))], recorder=rec,
                          overrides={"engine.record_stride": 2,
                                     "engine.records_per_point": 5})
        records = []
        eng.on_record(lambda r: records.append(r) or {"dag_sha256": f"d{len(records)}",
                                                      "path": f"p{len(records)}"})
        for _ in range(39):
            eng.step()
        events = rec.of("record")
        self.assertEqual(len(events), 4)                         # 5 incl. the worker best
        self.assertEqual({r["kind"] for r in records}, {"record"})
        self.assertEqual({r["dossier"] for r in records}, {None})
        self.assertEqual(len({frozenset(r["values"]) for r in records}), 4)
        self.assertEqual(events[0]["point"], {"gates": 10, "depth": 3})
        self.assertEqual((events[0]["dag"], events[0]["record"]), ("d1", "p1"))
        self.assertEqual(events[-1]["distinct_at_point"], 5)
        self.assertGreaterEqual(len(eng.archive), 5)
        self.assertEqual(rec.improvements, [])                  # records are not improvements


class RestartTest(unittest.TestCase):
    # The seed chain holds the worker best, so the incumbent allowance is switched off here.
    STALL = {"restart.stall_proposals": 20, "engine.periodic_every": 1,
             "restart.incumbent_factor": 1.0}

    def test_stall_restarts_from_fresh_root(self):
        rec = FakeRecorder()
        con = FakeConstruct(gates=20, depth=3)
        over = dict(self.STALL, **{"restart.w_fresh": 1.0, "restart.w_elite": 0.0,
                                   "restart.w_shared": 0.0, "restart.w_best": 0.0})
        eng, _, _ = build([("a", 1.0, noop)], recorder=rec, construct=con, overrides=over)
        for _ in range(20):
            eng.step()
        ev = rec.of("restart")
        self.assertEqual(len(ev), 1)
        self.assertEqual((ev[0]["reason"], ev[0]["source"]), ("stall_proposals", "fresh"))
        root = ev[0]["root"]
        self.assertTrue(root["id"].startswith("naive#"))
        self.assertEqual((root["constructor"], root["gates"], root["depth"]), ("naive", 20, 3))
        self.assertIsInstance(root["seed"], int)
        self.assertEqual(ev[0]["prev"]["best"], {"gates": 10, "depth": 3})
        self.assertEqual(ev[0]["engine_chain"], 2)
        self.assertEqual(eng.chain_seq, 2)
        self.assertEqual(eng.snapshot()["cur"], [20, 3])
        self.assertEqual(eng.snapshot()["worker_best"], [10, 3])  # kept across restarts
        self.assertIn(frozenset(mk(10, 3)), eng.archive)
        self.assertEqual(eng.phase.phase, BURST)
        self.assertEqual(len(con.calls), 1)

    def test_elite_source(self):
        rec = FakeRecorder()
        over = dict(self.STALL, **{"restart.w_fresh": 0.0, "restart.w_elite": 1.0,
                                   "restart.w_shared": 0.0, "restart.w_best": 0.0})
        eng, _, _ = build([("a", 1.0, noop)], recorder=rec, overrides=over)
        elite = frozenset(mk(11, 3, 5))
        eng.archive.offer(elite, 11, 3, (11, 3), True, "test")
        for _ in range(20):
            eng.step()
        self.assertEqual(rec.of("restart")[0]["source"], "elite")
        self.assertEqual(eng.state.key(), elite)

    def test_shared_pull_and_fallback(self):
        rec = FakeRecorder()
        over = dict(self.STALL, **{"restart.w_fresh": 0.0, "restart.w_elite": 0.0,
                                   "restart.w_shared": 1.0, "restart.w_best": 1e-9})
        pool = FakePool([mk(11, 3, 7)])
        eng, _, _ = build([("a", 1.0, noop)], recorder=rec, pool=pool, overrides=over)
        for _ in range(20):
            eng.step()
        restart = rec.of("restart")[0]
        self.assertEqual((restart["source"], restart["donor"], restart["record"]),
                         ("shared", "w9", "rec0"))
        pull = rec.of("pull")[0]
        self.assertEqual((pull["record"], pull["donor"], pull["point"]), ("rec0", "w9", {"gates": 11, "depth": 3}))
        for _ in range(40):                    # the pool's only elite is now in the archive
            eng.step()
        sources = [e["source"] for e in rec.of("restart")]
        self.assertEqual(set(sources[1:]), {"best"})
        self.assertEqual(len(rec.of("pull")), 1)
        self.assertEqual(eng.counters["pull_empty"], len(sources) - 1)

    def test_pulled_better_elite_becomes_worker_best_without_dossier(self):
        rec = FakeRecorder()
        over = dict(self.STALL, **{"restart.w_fresh": 0.0, "restart.w_elite": 0.0,
                                   "restart.w_shared": 1.0, "restart.w_best": 0.0})
        eng, _, _ = build([("a", 1.0, noop)], recorder=rec, pool=FakePool([mk(8, 3, 7)]),
                          overrides=over)
        for _ in range(20):
            eng.step()
        self.assertEqual(eng.snapshot()["worker_best"], [8, 3])
        self.assertEqual(rec.improvements, [])
        self.assertEqual(len(rec.of("adopt_best")), 1)

    def test_seconds_trigger_uses_recorder_clock(self):
        rec = FakeRecorder()
        over = {"restart.stall_seconds": 100.0, "engine.periodic_every": 1,
                "restart.root_seconds": 0.0, "restart.incumbent_factor": 1.0}
        sections = [move_section("a", 1.0)]
        settings = settings_for(sections, over)
        eng = make_engine(settings, [NoopMove(settings, "a")], seed=mk(10, 3), recorder=rec)
        eng.step()
        rec.clock.advance(99.0)
        eng.step()
        self.assertEqual(rec.of("restart"), [])
        rec.clock.advance(1.0)
        eng.step()
        self.assertEqual(rec.of("restart")[0]["reason"], "stall_seconds")

    def test_no_source_gives_another_stall_period(self):
        rec = FakeRecorder()
        eng, _, _ = build([("a", 1.0, noop)], recorder=rec, overrides=dict(
            self.STALL, **{"restart.w_fresh": 0.0, "restart.w_elite": 0.0,
                           "restart.w_shared": 1.0, "restart.w_best": 0.0}),
            pool=FakePool([]))
        eng._construct = None
        eng.worker_best_values = None
        for _ in range(20):
            eng.step()
        self.assertEqual(len(rec.of("restart_failed")), 1)
        self.assertEqual(eng.chain_seq, 1)


class SetupTest(unittest.TestCase):
    def test_moves_filtered(self):
        class Never(NoopMove):
            def applicable(self, target, objective):
                return "needs a depth cap"
        rec = FakeRecorder()
        sections = [move_section("a", 1.0), move_section("b", 1.0), move_section("z", 0.0)]
        settings = settings_for(sections, QUIET)
        moves = [NoopMove(settings, "a"), Never(settings, "b"), NoopMove(settings, "z")]
        eng = make_engine(settings, moves, seed=mk(10, 3), recorder=rec)
        self.assertEqual([m.name for m in eng._moves], ["a"])
        status = {e["move"]: e["status"] for e in rec.of("move")}
        self.assertEqual(status, {"b": "inapplicable", "z": "off"})

    def test_root_when_no_seed_and_rejected_seed(self):
        rec = FakeRecorder()
        con = FakeConstruct(gates=15, depth=2)
        eng, _, _ = build([("a", 1.0, noop)], recorder=rec, construct=con,
                          seed=mk(10, 3) + [BAD])
        self.assertEqual(len(rec.of("seed_rejected")), 1)
        self.assertTrue(eng.root["id"].startswith("naive#"))
        self.assertEqual(eng.snapshot()["worker_best"], [15, 2])

    def test_seed_forms(self):
        self.assertEqual(_seed_values({"gates": [[0, 1], [2, 4]]}, 4), [3, 7])
        self.assertEqual(_seed_values({"values": [5, 6]}, 4), [5, 6])
        self.assertEqual(_seed_values([9, 10], 4), [9, 10])

    def test_epoch_and_debug_check(self):
        rec = FakeRecorder()
        rec.epoch_flag = True
        eng, _, _ = build([("a", 1.0, lambda s, n: RandomMove(s, n))], recorder=rec,
                          overrides={"engine.periodic_every": 2, "debug.check_every": 3})
        for _ in range(6):
            eng.step()
        self.assertEqual(len(rec.epochs), 3)
        for key in ("weights", "acceptance", "plateau", "archive", "counters",
                    "chain_best", "worker_best", "phase"):
            self.assertIn(key, rec.epochs[0])
        self.assertTrue(json.dumps(rec.epochs))
        self.assertGreaterEqual(eng.state.checks, 1)


class CheckpointTest(unittest.TestCase):
    def run_pair(self, overrides):
        # Exact continuation needs replayable scheduling: charge work units, not seconds.
        over = dict(QUIET, **{"restart.stall_proposals": 300, "engine.periodic_every": 16,
                              "phase.burst_budget": 50, "scheduler.cost": "work"})
        over.update(overrides)
        sections = [move_section("rw", 1.0), move_section("big", 0.5)]
        settings = settings_for(sections, over)

        def moves():
            return [RandomMove(settings, "rw"),
                    RandomMove(settings, "big", family="lns", p_remove=0.4, p_add=0.4)]

        def cb(cand):
            return {"ok": True}

        clock_a = FakeRecorder().clock
        rec_a = FakeRecorder(clock_a)
        a = make_engine(settings, moves(), seed=mk(40, 3), recorder=rec_a, rng_seed=11,
                        pool=FakePool([mk(25, 3, 50)]))
        a.on_record(cb)
        for _ in range(700):
            a.step()
            clock_a.advance(0.01)
        data = json.loads(json.dumps(a.checkpoint()))
        rec_b = FakeRecorder()
        rec_b.clock.t = clock_a.t
        b = Engine.resume(data, FakeTarget(), FakeObjective(), settings, recorder=rec_b,
                          pool=FakePool([mk(25, 3, 50)]), moves=moves(),
                          state_factory=fake_factory, construct=FakeConstruct(),
                          plateau_tracker=FakePlateau)
        b.on_record(cb)
        n_imp_a = len(rec_a.improvements)
        n_restart_a = len(rec_a.of("restart"))
        for _ in range(1500):
            ra, rb = a.step(), b.step()
            self.assertEqual(ra, rb)
            clock_a.advance(0.01)
            rec_b.clock.advance(0.01)
        self.assertEqual(a.rng.getstate(), b.rng.getstate())
        self.assertEqual(a.snapshot(), b.snapshot())
        self.assertEqual(a.counters, b.counters)
        self.assertEqual(a.archive.keys(), b.archive.keys())
        self.assertEqual(a.scheduler.weights(), b.scheduler.weights())
        self.assertEqual(a._moves[0].counter, b._moves[0].counter)
        self.assertEqual([d["ref"] for d in rec_a.improvements[n_imp_a:]],
                         [d["ref"] for d in rec_b.improvements])
        return len(rec_a.of("restart")) - n_restart_a, len(rec_b.improvements)

    def test_resume_continues_identically(self):
        restarts, _ = self.run_pair({})
        self.assertGreater(restarts, 0)                         # restarts were exercised

    def test_checkpoint_is_json_safe(self):
        eng, _, _ = build([("a", 1.0, lambda s, n: RandomMove(s, n))])
        for _ in range(50):
            eng.step()
        text = json.dumps(eng.checkpoint())
        self.assertIn('"version": 1', text)


if __name__ == "__main__":
    unittest.main()
