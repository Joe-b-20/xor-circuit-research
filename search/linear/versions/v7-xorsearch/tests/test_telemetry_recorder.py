"""Recorder, NullRecorder and EventLog: files, ids, ring, counters, follow-ups, rotation."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from xorsearch.config.schema import Schema
from xorsearch.config.settings import for_sections
from xorsearch.telemetry.recorder import (COUNTERS, KNOBS, EventLog, NullRecorder, Recorder,
                                          cap_trace, iter_jsonl, log_segments, read_log)
from xorsearch.tests.test_telemetry_report import FakeClock


def settings(**telemetry):
    """Settings over the telemetry sections with ``telemetry.*`` overrides."""
    return for_sections(*KNOBS, overrides={"telemetry": telemetry} if telemetry else None)


def rec(it, move="walk.remove1", accepted=False, neutral=False, d_gates=1, d_depth=0, **kw):
    """A proposal record as the engine passes it."""
    r = {"it": it, "move": move, "accepted": accepted, "neutral": neutral, "d_gates": d_gates,
         "d_depth": d_depth, "gates": 100, "depth": 7, "work": 10,
         "components": ["remove1", "repair"]}
    r.update(kw)
    return r


def dossier(**kw):
    d = {"kind": "gates", "before": {"gates": 101, "depth": 7},
         "after": {"gates": 100, "depth": 7}, "move": "lns.cone", "phase": "plateau",
         "trace": {"components": ["destroy.cone", "rebuild.deadline"], "removed": list(range(50)),
                   "added": [1, 2]},
         "values_before": [3, 5, 6, 9], "values_after": [3, 5, 10],
         "state_before": {"plateau": {"age_it": 40, "age_s": 2.5, "distinct_states": 7}},
         "verification": {"ok": True}}
    d.update(kw)
    return d


def events(directory):
    return list(read_log(Path(directory) / "events.jsonl"))


class RecorderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "w01"
        self.clock = FakeClock(100.0)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, **knobs):
        return Recorder(self.dir, "w01", settings(**knobs), clock=self.clock, t0=100.0,
                        wall=lambda: 1.8e9 + self.clock.t, process_time=lambda: self.clock.t)

    def test_knobs_are_a_valid_schema(self):
        schema = Schema(KNOBS)
        for key in ("telemetry.epoch_seconds", "telemetry.ring_size",
                    "telemetry.trace_values_max", "telemetry.followup_iterations",
                    "telemetry.dossier_detail", "telemetry.fsync", "telemetry.rotate_mb",
                    "telemetry.plateau.distinct_cap", "telemetry.diversity.max_pairs"):
            self.assertIn(key, schema.knobs)
        with self.assertRaises(ValueError):
            settings(fsync="sometimes")

    def test_start_envelope_and_clock(self):
        r = self.make()
        self.clock.t = 112.5
        r.begin("start", {"seed": 42, "source_hash": "abc"})
        r.close()
        evs = events(self.dir)
        start = evs[0]
        self.assertEqual(start["ev"], "start")
        self.assertEqual(start["t"], 12.5)
        self.assertEqual(start["worker"], "w01")
        self.assertEqual(start["seed"], 42)
        self.assertIn("python", start["env"])
        self.assertTrue(start["utc"].endswith("Z"))
        self.assertEqual(start["chain"], "w01-c0001")
        self.assertEqual(evs[-1]["ev"], "stop")

    def test_ring_buffer_keeps_last_n_in_order(self):
        r = self.make(ring_size=8)
        for it in range(1, 21):
            r.proposal(rec(it, accepted=it % 2 == 0, neutral=it % 2 == 0, d_gates=0))
        ring = r.ring()
        self.assertEqual([x["it"] for x in ring], list(range(13, 21)))
        self.assertEqual(ring[-1], {"it": 20, "move": "walk.remove1", "phase": None, "valid": True,
                                    "gates": 100, "depth": 7, "d_gates": 0, "d_depth": 0,
                                    "accepted": True, "neutral": True,
                                    "components": ["remove1", "repair"]})
        r.close()

    def test_counters_epoch_and_reset(self):
        r = self.make(epoch_seconds=10.0)
        r.begin("start", {})
        r.proposal(rec(1))                                            # rejected
        r.proposal(rec(2, accepted=True, neutral=True, d_gates=0))    # neutral
        r.proposal(rec(3, accepted=True, d_gates=1))                  # uphill
        r.proposal(rec(4, accepted=True, d_gates=-1, improved_chain=True, cpu_s=0.5))
        r.proposal(rec(5, move="lns.cone", valid=False))
        self.assertFalse(r.epoch_due())
        self.clock.t += 10.0
        self.assertTrue(r.epoch_due())
        r.epoch({"phase": "plateau", "weights": {"walk.remove1": 1.0}})
        self.assertFalse(r.epoch_due())
        r.proposal(rec(6))
        r.close()
        epochs = [e for e in events(self.dir) if e["ev"] == "epoch"]
        self.assertEqual(len(epochs), 2)            # one full, one partial at close
        first, last = epochs
        walk = first["moves"]["walk.remove1"]
        self.assertEqual((walk["proposals"], walk["valid"], walk["accepted"], walk["neutral"],
                          walk["uphill"], walk["improved_chain"], walk["work"]),
                         (4, 4, 3, 1, 1, 1, 40))
        self.assertEqual(walk["cpu_s"], 0.5)
        self.assertEqual(first["moves"]["lns.cone"]["valid"], 0)
        self.assertEqual(first["phase"], "plateau")
        self.assertEqual(first["its"], 5)
        self.assertTrue(last["partial"])
        self.assertEqual(last["moves"]["walk.remove1"]["proposals"], 1)
        stop = events(self.dir)[-1]
        self.assertEqual(stop["totals"]["walk.remove1"]["proposals"], 5)
        combos = {(c["move"], tuple(c["components"])): c for c in first["combos"]}
        self.assertEqual(combos[("walk.remove1", ("remove1", "repair"))]["improved_chain"], 1)

    def test_cpu_is_apportioned_by_work_when_not_measured(self):
        r = self.make(epoch_seconds=1.0)
        r.proposal(rec(1, work=30))
        r.proposal(rec(2, move="lns.cone", work=10))
        self.clock.t += 4.0                         # process_time follows the fake clock
        r.epoch({})
        r.close()
        ep = [e for e in events(self.dir) if e["ev"] == "epoch"][0]
        self.assertTrue(ep["cpu_est"])
        self.assertAlmostEqual(ep["moves"]["walk.remove1"]["cpu_s"], 3.0)
        self.assertAlmostEqual(ep["moves"]["lns.cone"]["cpu_s"], 1.0)

    def test_improvement_dossier_and_event(self):
        r = self.make(trace_values_max=8)
        r.begin("start", {"root": {"id": "naive#3"}, "source": "fresh"})
        for it in range(1, 6):
            r.proposal(rec(it))
        self.clock.t += 3
        r.proposal(rec(6, move="lns.cone", accepted=True, d_gates=-1, improved_worker=True))
        did = r.improvement(dossier())
        self.assertEqual(did, "w01-000001")
        path = self.dir / "dossiers" / f"{did}.json"
        d = json.loads(path.read_text())
        self.assertEqual(d["id"], did)
        self.assertEqual(d["it"], 6)
        self.assertEqual(d["chain"]["id"], "w01-c0001")
        self.assertEqual(d["chain"]["root"], {"id": "naive#3"})
        self.assertEqual(d["lineage"], {"parent": None, "chain_origin": "fresh"})
        self.assertEqual(len(d["trace"]["removed"]), 8)
        self.assertEqual(d["trace"]["removed_n"], 50)
        self.assertEqual(d["symdiff"], {"removed": [6, 9], "added": [10]})
        self.assertEqual(d["ring"][-1]["move"], "lns.cone")
        self.assertEqual(d["timing"]["it_since_root"], 6)
        did2 = r.improvement(dossier(before={"gates": 100, "depth": 7},
                                     after={"gates": 99, "depth": 7}))
        r.close()
        ev = [e for e in events(self.dir) if e["ev"] == "improve"]
        self.assertEqual([e["id"] for e in ev], [did, did2])
        self.assertEqual(ev[0]["dossier"], f"dossiers/{did}.json")
        self.assertEqual(ev[0]["components"], ["destroy.cone", "rebuild.deadline"])
        self.assertEqual(ev[0]["plateau_age_s"], 2.5)
        self.assertEqual(ev[0]["root"], "naive#3")
        self.assertEqual(ev[0]["root_source"], "fresh")
        self.assertEqual(ev[0]["symdiff"], 3)
        self.assertTrue(ev[0]["verified"])
        self.assertEqual(ev[1]["parent"], did)     # lineage continues on the same chain
        self.assertEqual(events(self.dir)[-1]["best"], {"gates": 99, "depth": 7})

    def test_dossier_detail_levels(self):
        r = self.make(dossier_detail="standard")
        did = r.improvement(dossier(gates_after=[[0, 1]]))
        d = json.loads((self.dir / "dossiers" / f"{did}.json").read_text())
        self.assertNotIn("values_before", d)
        self.assertIn("values_after", d)
        r.close()
        m = NullRecorder(None, "w9", settings(dossier_detail="minimal"))
        did = m.improvement(dossier(gates_after=[[0, 1]]))
        d = m.dossiers[did]
        for key in ("values_before", "values_after", "gates_after"):
            self.assertNotIn(key, d)
        self.assertEqual(d["symdiff"], {"removed_n": 2, "added_n": 1})

    def test_restart_and_plateau_ids(self):
        r = self.make()
        r.begin("start", {})
        r.proposal(rec(10))
        r.event("restart", reason="stall_seconds", source="shared", parent="w02-000004",
                donor="w02", root={"id": "rec-17"})
        r.proposal(rec(20, accepted=True, d_gates=-1, improved_worker=True))
        did = r.improvement(dossier())
        r.event("plateau", level=[100, 7], age_it=10, exit="improve")
        r.event("plateau", level=[99, 7], age_it=1, exit="restart")
        r.close()
        evs = events(self.dir)
        restart = next(e for e in evs if e["ev"] == "restart")
        self.assertEqual(restart["chain"], "w01-c0002")
        self.assertEqual(restart["prev"]["chain"], "w01-c0001")
        self.assertEqual(restart["prev"]["age_it"], 10)
        imp = next(e for e in evs if e["ev"] == "improve")
        self.assertEqual(imp["chain"], "w01-c0002")
        self.assertEqual(imp["parent"], "w02-000004")      # chain parent from the shared pull
        self.assertEqual(imp["root_source"], "shared")
        plats = [e for e in evs if e["ev"] == "plateau"]
        self.assertEqual([p["id"] for p in plats], ["w01-p000001", "w01-p000002"])
        self.assertEqual(plats[0]["improvement"], did)
        self.assertNotIn("improvement", plats[1])

    def test_followups(self):
        r = self.make(followup_iterations=[5, 10])
        r.proposal(rec(100, accepted=True, d_gates=-1, improved_worker=True, improved_chain=True))
        did = r.improvement(dossier())
        for it in range(101, 107):
            r.proposal(rec(it, accepted=it == 103, neutral=it == 103, d_gates=0))
        evs = [e for e in events(self.dir) if e["ev"] == "followup"]
        self.assertEqual(evs, [])                   # buffered: not flushed yet
        r.event("pull", ok=False)                   # a FLUSH_NOW event writes the buffer
        fu = [e for e in events(self.dir) if e["ev"] == "followup"]
        self.assertEqual(len(fu), 1)
        f = fu[0]
        self.assertEqual((f["id"], f["horizon"], f["it"], f["complete"]), (did, 5, 105, True))
        self.assertEqual((f["proposals"], f["accepted"], f["neutral"], f["later"]), (5, 1, 1, 0))
        self.assertEqual(f["plateau_it"], 5)
        r.close()                                    # horizon 10 not reached: incomplete
        fu = [e for e in events(self.dir) if e["ev"] == "followup"]
        self.assertEqual([(e["horizon"], e["complete"]) for e in fu], [(5, True), (10, False)])

    def test_resume_continues_ids_time_and_followups(self):
        r = self.make(followup_iterations=[10])
        r.begin("start", {})
        r.proposal(rec(1, accepted=True, d_gates=-1, improved_worker=True))
        r.improvement(dossier())
        r.event("restart", reason="manual", source="fresh")
        r.event("plateau", level=[1, 1], exit="stop")
        self.clock.t = 160.0                         # t = 60
        r.close()
        # New process: a fresh monotonic clock and no t0 -> continue at the last t.
        clock = FakeClock(5.0)
        r2 = Recorder(self.dir, "w01", settings(followup_iterations=[10]), clock=clock)
        self.assertAlmostEqual(r2.now(), 60.0)
        r2.begin("resume", {})
        r2.proposal(rec(2, accepted=True, d_gates=-1, improved_worker=True))
        self.assertEqual(r2.improvement(dossier()), "w01-000002")
        r2.event("restart", reason="manual", source="elite")
        r2.event("plateau", level=[1, 1], exit="stop")
        for it in range(3, 13):
            r2.proposal(rec(it))
        r2.close()
        evs = events(self.dir)
        self.assertEqual([e["chain"] for e in evs if e["ev"] == "restart"],
                         ["w01-c0002", "w01-c0003"])
        self.assertEqual([e["id"] for e in evs if e["ev"] == "plateau"],
                         ["w01-p000001", "w01-p000002"])
        resume = next(e for e in evs if e["ev"] == "resume")
        self.assertEqual(resume["chain"], "w01-c0002")
        fu = [(e["id"], e["complete"]) for e in evs if e["ev"] == "followup"]
        self.assertIn(("w01-000001", True), fu)       # survived the restart of the process
        stop = evs[-1]
        self.assertEqual(stop["totals"]["walk.remove1"]["proposals"], 12)   # cumulative
        ts = [e["t"] for e in evs]
        self.assertEqual(ts, sorted(ts))

    def test_dead_move_warning(self):
        r = self.make(epoch_seconds=1.0, warn_dead_epochs=2)
        for k in range(3):
            r.proposal(rec(k, move="xover", valid=False))
            self.clock.t += 1
            r.epoch({})
        r.close()
        warns = [e for e in events(self.dir) if e["ev"] == "warn"]
        self.assertEqual(len(warns), 1)
        self.assertEqual((warns[0]["kind"], warns[0]["move"]), ("move_dead", "xover"))

    def test_cap_trace(self):
        t = cap_trace({"components": list("abcdef"), "removed": [5, 4, 3], "k": 3}, 2)
        self.assertEqual(t, {"components": list("abcdef"), "removed": [5, 4], "removed_n": 3,
                             "k": 3})


class NullRecorderTest(unittest.TestCase):
    def script(self, r):
        """The same call sequence for parity checks."""
        r.begin("start", {"seed": 1})
        for it in range(1, 30):
            r.proposal(rec(it, accepted=it % 3 == 0, neutral=it % 6 == 0,
                           d_gates=0 if it % 6 == 0 else -1, improved_worker=it == 15))
            if it == 15:
                r.improvement(dossier())
        r.event("restart", reason="stall_seconds", source="fresh")
        r.epoch({"phase": "plateau"})
        r.close()

    def test_parity_with_recorder(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock_a, clock_b = FakeClock(), FakeClock()
            s = settings(followup_iterations=[4])
            a = Recorder(Path(tmp) / "w", "w", s, clock=clock_a, t0=0.0, wall=lambda: 1.0,
                         process_time=lambda: 0.0)
            b = NullRecorder(None, "w", s, clock=clock_b, t0=0.0, wall=lambda: 1.0,
                             process_time=lambda: 0.0)
            self.script(a)
            self.script(b)
            self.assertEqual(a.ring(), b.ring())
            self.assertEqual(a._cumulative(), b._cumulative())
            file_events = list(read_log(Path(tmp) / "w" / "events.jsonl"))
            null_events = json.loads(json.dumps(list(b.events)))
            strip = lambda evs: [{k: v for k, v in e.items() if k != "env"} for e in evs]  # noqa
            self.assertEqual(strip(file_events), strip(null_events))
            on_disk = json.loads((Path(tmp) / "w" / "dossiers" / "w-000001.json").read_text())
            self.assertEqual(on_disk, json.loads(json.dumps(b.dossiers["w-000001"])))
            self.assertEqual(list(Path(tmp).glob("*")), [Path(tmp) / "w"])

    def test_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = NullRecorder(Path(tmp) / "never", "w")
            self.script(r)
            self.assertFalse((Path(tmp) / "never").exists())
            self.assertEqual(r.events[-1]["ev"], "stop")


class EventLogTest(unittest.TestCase):
    def test_flush_policy_and_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign.jsonl"
            clock = FakeClock(50.0)
            log = EventLog(path, clock=clock, t0=0.0, flush_seconds=100.0)
            log.write("pool", point={"gates": 9, "depth": 3}, size=2)    # FLUSH_NOW
            self.assertEqual(len(list(iter_jsonl(path))), 1)
            log.write("phase", it=None)                                    # buffered
            self.assertEqual(len(list(iter_jsonl(path))), 1)
            clock.t += 200                                                 # old buffer
            log.write("note")
            self.assertEqual(len(list(iter_jsonl(path))), 3)
            log.close()
            first = next(iter_jsonl(path))
            self.assertEqual((first["v"], first["t"], first["worker"], first["it"], first["ev"]),
                             (1, 50.0, "coord", None, "pool"))

    def test_rotation_keeps_every_line_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            log = EventLog(path, "w", rotate_mb=2048 / 2**20, flush_bytes=0)
            for i in range(200):
                log.write("record", i, payload="x" * 40)
            log.close()
            segs = log_segments(path)
            self.assertGreater(len(segs), 3)
            self.assertEqual(segs[-1], path)
            self.assertEqual(segs[0].name, "events-000001.jsonl")
            self.assertEqual([e["it"] for e in read_log(path)], list(range(200)))
            for seg in segs[:-1]:
                self.assertLess(seg.stat().st_size, 2048 + 200)

    def test_rotate_keep_prunes_oldest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            log = EventLog(path, "w", rotate_mb=1024 / 2**20, rotate_keep=2, flush_bytes=0)
            for i in range(200):
                log.write("record", i, payload="y" * 40)
            log.close()
            self.assertEqual(len(log_segments(path)), 3)
            its = [e["it"] for e in read_log(path)]
            self.assertEqual(its, list(range(its[0], 200)))

    def test_cut_last_line_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            log = EventLog(path, "w")
            log.write("start", 0)
            log.write("stop", 1)
            log.close()
            with open(path, "a", encoding="utf-8") as handle:
                handle.write('{"v":1,"t":3,"ev":"impr')
            errors = []
            self.assertEqual([e["ev"] for e in iter_jsonl(path, errors)], ["start", "stop"])
            self.assertEqual(errors, [(str(path), 3)])

    def test_counter_names_are_stable(self):
        self.assertEqual(COUNTERS, ("proposals", "valid", "accepted", "neutral", "uphill",
                                    "improved_chain", "improved_worker", "work", "cpu_s"))


class ReviewFixesTest(unittest.TestCase):
    """Verification in dossiers, frontier vs best, richer follow-ups, combos, close epoch."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "w01"
        self.clock = FakeClock(100.0)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, **knobs):
        return Recorder(self.dir, "w01", settings(**knobs), clock=self.clock, t0=100.0,
                        wall=lambda: 1.8e9 + self.clock.t, process_time=lambda: self.clock.t)

    def test_verify_callback_fills_dossier_and_event(self):
        r = self.make()
        r.proposal(rec(1, accepted=True, d_gates=-1, improved_worker=True, cpu_s=0.5))
        seen_on_disk = []

        def verify(did):
            # The dossier already exists (the id is reserved) but is not verified yet.
            path = self.dir / "dossiers" / f"{did}.json"
            seen_on_disk.append(json.loads(path.read_text())["verification"])
            return {"ok": True, "saved": True, "record": "workers/w01/records/r.json"}
        did = r.improvement(dossier(verification=None), verify=verify)
        r.close()
        self.assertEqual(seen_on_disk, [None])
        d = json.loads((self.dir / "dossiers" / f"{did}.json").read_text())
        self.assertEqual(d["verification"]["record"], "workers/w01/records/r.json")
        imp = next(e for e in events(self.dir) if e["ev"] == "improve")
        self.assertIs(imp["verified"], True)
        self.assertEqual(imp["record"], "workers/w01/records/r.json")
        self.assertIn("ring_summary", d)
        self.assertEqual(d["ring_summary"]["proposals"], 1)

    def test_rejected_candidate_is_not_an_improvement(self):
        r = self.make(followup_iterations=[5])
        r.proposal(rec(1, accepted=True, d_gates=-1, improved_worker=True))
        did = r.improvement(dossier(), verify=lambda did: {"ok": False, "reason": "bad"})
        self.assertEqual(r._improvements, 0)
        r.close()
        d = json.loads((self.dir / "dossiers" / f"{did}.json").read_text())
        self.assertTrue(d["rejected"])
        evs = events(self.dir)
        self.assertFalse([e for e in evs if e["ev"] in ("improve", "followup")])
        self.assertIsNone(next(e for e in evs if e["ev"] == "stop")["best"])
        r2 = self.make()
        self.assertEqual(r2.improvement(dossier()), "w01-000002")  # the id is not reused
        r2.close()

    def test_frontier_point_does_not_change_best(self):
        r = self.make()
        r.proposal(rec(1, accepted=True, d_gates=-1, improved_worker=True))
        r.improvement(dossier())
        r.proposal(rec(2, accepted=True, d_gates=1))
        r.improvement(dossier(kind="frontier", after={"gates": 102, "depth": 5}))
        r.close()
        stop = next(e for e in events(self.dir) if e["ev"] == "stop")
        self.assertEqual(stop["best"], {"gates": 100, "depth": 7})
        self.assertEqual(stop["improvements"], 2)

    def test_followup_reports_what_came_first(self):
        r = self.make(followup_iterations=[20])
        r.begin("start", {})
        r.proposal(rec(10, accepted=True, d_gates=-1, improved_worker=True, improved_chain=True))
        first = r.improvement(dossier(after={"gates": 100, "depth": 7}))
        r.proposal(rec(13, accepted=True, d_gates=0, neutral=True))
        r.proposal(rec(14, accepted=True, d_gates=-1, improved_chain=True))
        r.proposal(rec(16, accepted=True, d_gates=-1, improved_chain=True, improved_worker=True))
        second = r.improvement(dossier(after={"gates": 98, "depth": 7}))
        r.event("restart", reason="stall_seconds", source="fresh", it=25)
        for it in range(26, 31):
            r.proposal(rec(it))
        r.close()
        fu = {e["id"]: e for e in events(self.dir) if e["ev"] == "followup"}
        f = fu[first]
        self.assertTrue(f["complete"])
        self.assertEqual((f["next"], f["next_it_since"]), (second, 6))
        self.assertEqual(f["next_chain_best_it_since"], 4)     # the plateau after lasted 4 its
        self.assertEqual(f["restart_it_since"], 15)
        self.assertTrue(f["chain_changed"])
        self.assertEqual(f["best_gain"], {"gates": 2, "depth": 0})
        g = fu[second]                                         # still open at close
        self.assertFalse(g["complete"])
        self.assertIsNone(g["next"])
        self.assertIsNone(g["next_chain_best_it_since"])
        self.assertEqual(g["restart_it_since"], 9)

    def test_followup_logs_survive_resume(self):
        r = self.make(followup_iterations=[20])
        r.begin("start", {})
        r.proposal(rec(10, accepted=True, d_gates=-1, improved_worker=True, improved_chain=True))
        first = r.improvement(dossier())
        r.proposal(rec(12, accepted=True, d_gates=-1, improved_chain=True))
        r.epoch({})                                            # writes the sidecar
        r._log.close()                                         # crash: no close()
        r2 = self.make(followup_iterations=[20])
        r2.begin("resume", {})
        for it in range(13, 31):
            r2.proposal(rec(it))
        r2.close()
        fu = [e for e in events(self.dir) if e["ev"] == "followup" and e["id"] == first]
        self.assertEqual(fu[-1]["next_chain_best_it_since"], 2)

    def test_combos_carry_every_counter_and_sum_to_moves(self):
        r = self.make()
        r.proposal(rec(1, accepted=True, neutral=True, d_gates=0, cpu_s=0.25))
        r.proposal(rec(2, components=["remove2"], cpu_s=0.5, valid=False))
        r.proposal(rec(3, move="lns.cone", components=None, cpu_s=1.0))
        r.epoch({})
        r.close()
        ep = next(e for e in events(self.dir) if e["ev"] == "epoch")
        combos = {(c["move"], tuple(c["components"])): c for c in ep["combos"]}
        self.assertEqual(set(combos), {("walk.remove1", ("remove1", "repair")),
                                       ("walk.remove1", ("remove2",)), ("lns.cone", ())})
        c = combos[("walk.remove1", ("remove2",))]
        self.assertEqual((c["proposals"], c["valid"], c["cpu_s"]), (1, 0, 0.5))
        walk = ep["moves"]["walk.remove1"]
        self.assertEqual((walk["proposals"], walk["valid"], walk["neutral"], walk["cpu_s"]),
                         (2, 1, 1, 0.75))

    def test_combo_counters_off_keeps_move_counters(self):
        r = self.make(combo_counters=False)
        r.proposal(rec(1, accepted=True, neutral=True, d_gates=0))
        r.proposal(rec(2, components=["remove2"]))
        r.epoch({})
        r.close()
        ep = next(e for e in events(self.dir) if e["ev"] == "epoch")
        self.assertEqual(ep["combos"], [])
        self.assertEqual(ep["moves"]["walk.remove1"]["proposals"], 2)

    def test_close_epoch_uses_epoch_source(self):
        r = self.make()
        r.set_epoch_source(lambda: {"phase": "burst", "weights": {"a": 1.0}})
        r.proposal(rec(1))
        r.close()
        ep = [e for e in events(self.dir) if e["ev"] == "epoch"][-1]
        self.assertEqual((ep["partial"], ep["phase"]), (True, "burst"))

    def test_close_survives_a_broken_epoch_source(self):
        r = self.make()
        r.set_epoch_source(lambda: 1 / 0)
        r.proposal(rec(1))
        r.close("error")
        evs = events(self.dir)
        self.assertIn("ZeroDivisionError", evs[-2]["source_error"])
        self.assertEqual(evs[-1]["ev"], "stop")

    def test_cpu_timing_since_previous_and_root(self):
        r = self.make()
        r.begin("start", {})
        r.proposal(rec(1, accepted=True, d_gates=-1, improved_worker=True, cpu_s=2.0))
        r.improvement(dossier())
        r.proposal(rec(2, accepted=True, d_gates=-1, improved_worker=True, cpu_s=3.0))
        did = r.improvement(dossier())
        r.close()
        d = json.loads((self.dir / "dossiers" / f"{did}.json").read_text())
        self.assertEqual(d["timing"]["cpu_s_since_prev"], 3.0)
        self.assertEqual(d["timing"]["cpu_s_since_root"], 5.0)

    def test_null_recorder_strips_envelope_keys(self):
        n = NullRecorder()
        n.proposal(rec(7))
        n.event("restart", it=99, t=-1, utc="bogus", source="fresh")
        e = n.events[-1]
        self.assertEqual((e["ev"], e["it"]), ("restart", 99))
        self.assertGreaterEqual(e["t"], 0)
        self.assertNotEqual(e["utc"], "bogus")
        n.epoch({"it": 123, "phase": "plateau"})
        self.assertEqual(n.events[-1]["it"], 7)


if __name__ == "__main__":
    unittest.main()
