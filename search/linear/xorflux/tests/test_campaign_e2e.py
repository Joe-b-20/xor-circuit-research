"""End-to-end smoke: `python -m xorflux run/stop/resume/verify/status` with 2 real worker
processes running the stub engine from the frozen source copy (a few seconds of wall time)."""
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from xorflux.campaign.checkpoint import identity_alive, read_json, read_jsonl
from xorflux.tests.test_campaign_stub import CRASH_BACKEND, FAST_SET, toy_campaign, write_campaign

REPO = Path(__file__).resolve().parents[2]
SETS = FAST_SET + '"campaign.freeze_tests" = true\n'   # the stub backend lives in xorflux/tests


def clean_env() -> dict:
    """This environment without PYTHONPATH (the CLI must find the frozen copy by itself)."""
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def xorflux(*argv, timeout=90):
    """Run the CLI as a separate process from the repository root."""
    return subprocess.run([sys.executable, "-m", "xorflux", *map(str, argv)], cwd=REPO, env=clean_env(),
                          capture_output=True, text=True, timeout=timeout)


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.campaign = write_campaign(self.dir, toy_campaign(sets=SETS))
        self.run = self.dir / "run"

    def tearDown(self):
        self.tmp.cleanup()

    def events(self):
        return read_jsonl(self.run / "campaign.jsonl")[0]

    def test_run_resume_verify(self):
        done = xorflux("run", self.campaign, "--out", self.run, "--seconds", 4)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        status = read_json(self.run / "status.json")
        self.assertEqual(status["phase"], "stopped")
        self.assertEqual(status["stop_reason"], "duration elapsed")
        names = [e["ev"] for e in self.events()]
        for ev in ("start", "worker_start", "frontier", "pool", "fleet_diversity", "stop"):
            self.assertIn(ev, names)
        frontier = [e for e in self.events() if e["ev"] == "frontier"]
        self.assertTrue(all(e["by"] in ("a-00", "a-01") and e["worker"] == "coord" for e in frontier))
        self.assertTrue(any(e["improvement"] for e in frontier))          # dossier ids from refs
        points = {(p["gates"], p["depth"]) for p in status["frontier"]["toy4"]}
        self.assertTrue(points & {(4, 2), (3, 3)}, points)               # the stub ladder made progress
        session = next((self.run / "sessions").glob("*.json"))
        frozen = str(self.run / "source")
        self.assertTrue(all(w["pythonpath"] == frozen for w in read_json(session)["workers"]))
        steps = {}
        for wid in ("a-00", "a-01"):
            worker_status = read_json(self.run / "workers" / wid / "status.json")
            self.assertEqual(worker_status["phase"], "stopped")
            steps[wid] = worker_status["steps"]
            self.assertTrue((self.run / "workers" / wid / "checkpoint.json").is_file())
            self.assertFalse((self.run / "workers" / wid / "error.json").exists())

        again = xorflux("run", self.campaign, "--out", self.run)
        self.assertEqual(again.returncode, 1)
        self.assertIn("not empty", again.stderr)

        resumed = xorflux("resume", self.run, "--seconds", 2)
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        starts = [e for e in self.events() if e["ev"] in ("start", "resume")]
        self.assertEqual([e["ev"] for e in starts], ["start", "resume"])
        self.assertGreater(starts[1]["t"], starts[0]["t"] + 3.5)          # campaign clock continues
        for wid in ("a-00", "a-01"):
            self.assertGreater(read_json(self.run / "workers" / wid / "status.json")["steps"], steps[wid])
            worker_events = [e["ev"] for e in read_jsonl(self.run / "workers" / wid / "events.jsonl")[0]]
            self.assertEqual(worker_events.count("resume"), 1)

        verified = xorflux("verify", self.run)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertIn("failed: 0", verified.stdout)
        shown = xorflux("status", self.run)
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("toy4: frontier", shown.stdout)

    def test_stop_command(self):
        process = subprocess.Popen([sys.executable, "-m", "xorflux", "run", str(self.campaign), "--out",
                                    str(self.run)], cwd=REPO, env=clean_env(), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                status = read_json(self.run / "status.json", {}) if (self.run / "freeze.json").exists() else {}
                if status.get("phase") == "running":
                    break
                time.sleep(0.2)
            self.assertEqual(status.get("phase"), "running")
            stopped = xorflux("stop", self.run, "--reason", "test", "--wait", 30)
            self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
            out, err = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, out + err)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
        status = read_json(self.run / "status.json")
        self.assertEqual(status["stop_reason"], "stop requested: test")
        self.assertFalse((self.run / "campaign.lock").exists())
        self.assertEqual(xorflux("stop", self.run).returncode, 1)       # nothing left to stop

    def wait_for(self, condition, timeout=30.0):
        """Poll ``condition()`` until it is truthy (returns it) or fail after ``timeout``."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = condition()
            if value:
                return value
            time.sleep(0.2)
        self.fail("condition not reached in time")

    def test_detached_coordinator_outlives_its_launcher(self):
        # The launcher runs in its own process group so the test can do to it what a closing
        # terminal or an ending WSL shell session does: kill the whole group.
        launcher = subprocess.Popen([sys.executable, "-m", "xorflux", "run", str(self.campaign),
                                     "--out", str(self.run), "--seconds", "60", "--detach"],
                                    cwd=REPO, env=clean_env(), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, start_new_session=True)
        out, err = launcher.communicate(timeout=60)
        self.assertEqual(launcher.returncode, 0, out + err)
        self.assertIn("running detached as pid", out)
        owner = read_json(self.run / "campaign.lock")
        try:
            self.assertNotEqual(owner["pid"], launcher.pid)
            self.assertEqual(os.getsid(owner["pid"]), owner["pid"])         # own session: no SIGHUP
            try:
                os.killpg(launcher.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass                                                        # nothing left in it
            time.sleep(1.0)
            self.assertTrue(identity_alive(owner), "detached coordinator died with its launcher")
            self.wait_for(lambda: (read_json(self.run / "status.json", {}) or {}).get("phase") == "running")
            shown = xorflux("status", self.run)
            self.assertIn("running  pid", shown.stdout)
            self.assertIn("coordinator.log", shown.stdout)
            stopped = xorflux("stop", self.run, "--reason", "detach-test", "--wait", 30)
            self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
            self.wait_for(lambda: not identity_alive(owner))
            self.assertEqual(read_json(self.run / "status.json")["stop_reason"], "stop requested: detach-test")
            self.assertIn("launched by pid", (self.run / "coordinator.log").read_text())

            resumed = xorflux("resume", self.run, "--seconds", 2, "--detach")
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
            self.wait_for(lambda: not (self.run / "campaign.lock").exists()
                          and read_json(self.run / "status.json")["phase"] == "stopped")
            self.assertEqual([e["ev"] for e in self.events() if e["ev"] in ("start", "resume")],
                             ["start", "resume"])
            verified = xorflux("verify", self.run)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        finally:
            if identity_alive(owner):
                os.kill(owner["pid"], signal.SIGTERM)

    def test_crashed_workers_restart_from_checkpoint(self):
        sets = SETS + '"campaign.on_worker_failure" = "restart"\n"campaign.max_worker_restarts" = 1\n'
        campaign = write_campaign(self.dir, toy_campaign(sets=sets, backend=CRASH_BACKEND), "crash.toml")
        done = xorflux("run", campaign, "--out", self.run, "--seconds", 4)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        restarts = [e for e in self.events() if e["ev"] == "worker_restart"]
        self.assertEqual(sorted(e["worker_id"] for e in restarts), ["a-00", "a-01"])
        self.assertTrue(all("deliberate test crash" in e["error"] for e in restarts))
        status = read_json(self.run / "status.json")
        self.assertEqual(status["phase"], "stopped")
        self.assertEqual({w: s["restarts"] for w, s in status["workers"].items()}, {"a-00": 1, "a-01": 1})
        self.assertEqual(len(list((self.run / "errors").glob("*/restart-*/workers/*/error.json"))), 2)
        self.assertFalse(list((self.run / "workers").glob("*/error.json")))

        # Same crash under the default policy: fail fast, exit 1, the error is kept.
        other = self.dir / "run-stop"
        sets = SETS
        campaign = write_campaign(self.dir, toy_campaign(sets=sets, backend=CRASH_BACKEND), "crash2.toml")
        failed = xorflux("run", campaign, "--out", other, "--seconds", 4)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(read_json(other / "status.json")["phase"], "failed")
        self.assertIn("deliberate test crash", read_json(other / "error.json")["message"])


if __name__ == "__main__":
    unittest.main()
