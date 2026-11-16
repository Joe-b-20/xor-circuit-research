"""Worker process logic in-process: start, records, checkpoint, resume, failures, coordinator link."""
import json
import tempfile
import time
import unittest
from pathlib import Path

from xorsearch.campaign.checkpoint import CampaignLock, atomic_json, read_json, read_jsonl, request_stop
from xorsearch.campaign.freeze import freeze, load_campaign, resolve
from xorsearch.campaign.worker import CoordinatorLink, DeadlineLink, WorkerProcess
from xorsearch.tests.test_campaign_stub import StubBackend, toy_campaign, write_campaign


def records_of(worker_dir):
    """Record index entries (recovery markers excluded)."""
    return [e for e in read_jsonl(worker_dir / "records.jsonl")[0] if "path" in e]


class CrashingBackend(StubBackend):
    """Engine whose 50th step raises."""

    def engine(self, *args, **kwargs):
        engine = super().engine(*args, **kwargs)
        step = engine.step

        def failing_step():
            if engine.it == 50:
                raise RuntimeError("boom in step")
            return step()
        engine.step = failing_step
        return engine


class WorkerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        path = write_campaign(base, toy_campaign())
        self.run = base / "run"
        self.plan = freeze(resolve(load_campaign(path), campaign_path=path), self.run, freeze_source=False)
        self.wdir = self.run / "workers" / "a-01"

    def tearDown(self):
        self.tmp.cleanup()

    def work(self, seconds=0.5, backend=None, wid="a-01"):
        worker = WorkerProcess(self.run, wid, DeadlineLink(seconds), backend=backend or StubBackend(),
                               standalone_pool=True)
        return worker, worker.run()

    def test_run_checkpoint_resume(self):
        worker, code = self.work()
        self.assertEqual(code, 0)
        status = read_json(self.wdir / "status.json")
        self.assertEqual(status["phase"], "stopped")
        self.assertGreater(status["steps"], 50)
        first_steps = status["steps"]
        envelope = read_json(self.wdir / "checkpoint.json")
        self.assertEqual(envelope["binding"]["worker"], "a-01")
        self.assertEqual(envelope["engine"]["it"], first_steps)
        records = records_of(self.wdir)
        self.assertEqual(records[0]["kind"], "seed")                     # verified seed baseline
        self.assertEqual((records[0]["gates"], records[0]["depth"]), (6, 3))
        chain = read_json(self.wdir / "chain.json")
        self.assertTrue(chain["best_values"] and chain["chain_values"])

        resumed, code = self.work(0.3)
        self.assertEqual(code, 0)
        self.assertTrue(getattr(resumed.engine, "resumed", False))
        status = read_json(self.wdir / "status.json")
        self.assertGreater(status["steps"], first_steps)
        self.assertEqual(read_json(self.wdir / "checkpoint.json")["engine"]["it"], status["steps"])
        events = [e["ev"] for e in read_jsonl(self.wdir / "events.jsonl")[0]]
        self.assertEqual(events.count("start"), 1)
        self.assertEqual(events.count("resume"), 1)
        self.assertEqual(events.count("stop"), 2)
        # No duplicate records after resume: the writer recovered its index.
        records = records_of(self.wdir)
        self.assertEqual(len({r["dag_sha256"] for r in records}), len(records))

    def test_capped_worker_best_is_within_cap(self):
        self.work(0.5, wid="a-00")                                        # a-00 has depth_cap 2
        records = records_of(self.run / "workers" / "a-00")
        self.assertTrue(any(r["depth"] <= 2 for r in records))
        best = read_json(self.run / "workers" / "a-00" / "status.json")["best"]
        self.assertLessEqual(best["depth"], 2)

    def test_checkpoint_for_other_settings_is_refused(self):
        self.work(0.2)
        path = self.wdir / "checkpoint.json"
        envelope = read_json(path)
        envelope["binding"]["settings_sha256"] = "0" * 64
        from xorsearch.campaign.checkpoint import digest
        envelope["sha256"] = digest({k: v for k, v in envelope.items() if k != "sha256"})
        atomic_json(path, envelope)
        _, code = self.work(0.2)
        self.assertEqual(code, 1)
        error = read_json(self.wdir / "error.json")
        self.assertEqual(error["type"], "CheckpointError")
        self.assertIn("settings_sha256", error["message"])
        self.assertEqual(read_json(self.wdir / "status.json")["phase"], "failed")

    def test_crash_writes_error_file(self):
        _, code = self.work(5.0, backend=CrashingBackend())
        self.assertEqual(code, 1)
        error = read_json(self.wdir / "error.json")
        self.assertEqual(error["message"], "boom in step")
        self.assertIn("Traceback", error["traceback"])

    def test_coordinator_link(self):
        with self.assertRaisesRegex(RuntimeError, "no live coordinator"):
            CoordinatorLink(self.run, "nope")
        lock = CampaignLock(self.run)
        owner = lock.acquire()
        atomic_json(self.run / "sessions" / f"{owner['token']}.json", {"t0": time.monotonic() - 5.0})
        link = CoordinatorLink(self.run, owner["token"])
        self.assertIsNone(link.lost())
        self.assertGreater(link.clock(), 5.0)
        request_stop(self.run, "test")
        self.assertIn("stop requested", link.lost())
        (self.run / "STOP").unlink()
        lock.release()
        self.assertEqual(link.lost(), "campaign lock lost")

    def test_lock_is_exclusive_and_reclaims_dead_owner(self):
        lock = CampaignLock(self.run)
        lock.acquire()
        from xorsearch.campaign.checkpoint import LockError
        with self.assertRaises(LockError):
            CampaignLock(self.run).acquire()
        lock.release()
        # A lock left by a dead process (impossible pid) is reclaimed.
        (self.run / "campaign.lock").write_text(json.dumps({"pid": 2 ** 22 + 7, "host": __import__("socket").gethostname(),
                                                            "token": "old", "start_ticks": "1"}))
        self.assertNotEqual(CampaignLock(self.run).acquire()["token"], "old")


if __name__ == "__main__":
    unittest.main()
