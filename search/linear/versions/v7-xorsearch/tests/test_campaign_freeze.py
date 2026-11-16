"""Freezing a run directory: source copy, reproducible tarball, snapshots, integrity checks."""
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from xorsearch.campaign.checkpoint import digest, file_hash, read_json
from xorsearch.campaign.freeze import (CLAIM_NAME, PACKAGE_ROOT, FreezeError, PlanError, freeze,
                                       frozen_campaign_value, frozen_settings, frozen_target, git_info,
                                       load_campaign, reproducible_tar, resolve, source_manifest,
                                       verify_freeze)
from xorsearch.tests.test_campaign_stub import StubBackend, toy_campaign, write_campaign


class FreezeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        path = write_campaign(self.dir, toy_campaign())
        self.resolved = resolve(load_campaign(path), campaign_path=path)
        self.run = self.dir / "run"
        self.plan = freeze(self.resolved, self.run)

    def tearDown(self):
        self.tmp.cleanup()

    def test_layout_and_hashes(self):
        for name in ("plan.json", "freeze.json", "environment.json", "campaign.toml", "source.tar.gz",
                     "settings/campaign.json", "settings/a-00.json", "settings/a-01.json", "targets/toy4.json"):
            self.assertTrue((self.run / name).is_file(), name)
        meta = read_json(self.run / "freeze.json")
        self.assertEqual(meta["plan_sha256"], digest(read_json(self.run / "plan.json")))
        self.assertEqual(meta["source"]["files"], source_manifest(PACKAGE_ROOT))
        self.assertFalse(any(k.startswith("tests/") for k in meta["source"]["files"]))
        self.assertFalse(any("__pycache__" in k for k in meta["source"]["files"]))
        for relative, sha in meta["snapshots"].items():
            self.assertEqual(file_hash(self.run / relative), sha)
        self.assertIsNone(meta["source"]["git"]["dirty"])  # git_status disabled in the test campaign
        seed = next(iter(self.plan["seeds"].values()))
        self.assertTrue((self.run / seed["snapshot"]).is_file())
        verify_freeze(self.run)

    def test_tarball_matches_source_and_is_reproducible(self):
        files = read_json(self.run / "freeze.json")["source"]["files"]
        with tarfile.open(self.run / "source.tar.gz") as tar:
            names = sorted(m.name for m in tar.getmembers())
            self.assertEqual(names, sorted("xorsearch/" + k for k in files))
            member = tar.getmember("xorsearch/campaign/freeze.py")
            self.assertEqual(member.mtime, 0)
            self.assertEqual(tar.extractfile(member).read(), (PACKAGE_ROOT / "campaign/freeze.py").read_bytes())
        blobs = {"b": b"2", "a": b"1"}
        self.assertEqual(reproducible_tar(blobs), reproducible_tar(dict(reversed(list(blobs.items())))))

    def test_settings_and_target_round_trip(self):
        backend = StubBackend()
        spec = self.plan["workers"][0]
        settings = frozen_settings(self.run, spec["settings"], backend.schema(), spec["settings_sha256"])
        self.assertEqual(settings.values, self.resolved.settings["a-00"].values)
        self.assertEqual(settings.origin("worker.status_seconds"), "campaign:set")
        target = frozen_target(self.run, self.plan, "toy4", backend)
        self.assertEqual(target.rows, [3, 7, 15])

    def test_tampering_is_detected(self):
        frozen = self.run / "source" / "xorsearch" / "campaign" / "worker.py"
        original = frozen.read_bytes()
        frozen.write_bytes(original + b"\n# edited\n")
        with self.assertRaisesRegex(FreezeError, "campaign/worker.py"):
            verify_freeze(self.run)
        frozen.write_bytes(original)
        verify_freeze(self.run)
        settings = self.run / "settings" / "a-00.json"
        data = json.loads(settings.read_text())
        data["values"]["worker.status_seconds"] = 9.0
        settings.write_text(json.dumps(data))
        with self.assertRaisesRegex(FreezeError, "settings/a-00.json"):
            verify_freeze(self.run)
        plan = self.run / "plan.json"
        plan.write_text(plan.read_text().replace('"seed": 11', '"seed": 12'))
        with self.assertRaisesRegex(FreezeError, "plan.json"):
            verify_freeze(self.run)

    def test_refuses_non_empty_directory(self):
        with self.assertRaisesRegex(PlanError, "not empty"):
            freeze(self.resolved, self.run)

    def test_concurrent_freeze_is_refused(self):
        # A second `run --out DIR` that passed the emptiness check loses the exclusive claim.
        other = self.dir / "other"
        other.mkdir()
        (other / CLAIM_NAME).write_text("pid 1\n")
        with self.assertRaisesRegex(PlanError, "being frozen by another process"):
            freeze(self.resolved, other, freeze_source=False)
        self.assertTrue((other / CLAIM_NAME).is_file())                    # the owner's claim stays
        self.assertTrue((self.run / CLAIM_NAME).is_file())                 # kept: marks a run dir

    def test_failed_freeze_leaves_nothing_behind(self):
        target = self.dir / "broken"
        with mock.patch("xorsearch.campaign.freeze.environment", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                freeze(self.resolved, target, freeze_source=False)
        self.assertFalse(target.exists())
        target.mkdir()                                                      # pre-existing and empty:
        with mock.patch("xorsearch.campaign.freeze.environment", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                freeze(self.resolved, target, freeze_source=False)
        self.assertEqual(list(target.iterdir()), [])                        # emptied, not removed
        freeze(self.resolved, target, freeze_source=False)                  # and usable again

    def test_run_directory_inside_package_is_refused(self):
        with self.assertRaisesRegex(PlanError, "inside the xorsearch package"):
            freeze(self.resolved, PACKAGE_ROOT / "runs" / "x", freeze_source=False)
        self.assertFalse((PACKAGE_ROOT / "runs" / "x").exists())

    def test_launch_ignores_live_schema(self):
        # Resume after a source edit: the live tree may have gained knobs since the freeze.  The
        # launcher reads run_frozen without a schema and points PYTHONPATH at the frozen copy.
        from xorsearch import cli
        from xorsearch.campaign.records import Backend
        with mock.patch.object(Backend, "schema", side_effect=AssertionError("live schema used")), \
                mock.patch.object(cli, "load_backend", side_effect=AssertionError("backend loaded")):
            command, env, frozen = cli._coordinator_launch(self.run, self.plan, True, 5.0)
        self.assertTrue(frozen)
        self.assertEqual(env["PYTHONPATH"].split(os.pathsep)[0], str(self.run / "source"))
        self.assertEqual(command[-3:], ["--resume", "--seconds", "5.0"])
        self.assertEqual(frozen_campaign_value(self.run, self.plan, "campaign.run_frozen"), True)
        self.assertEqual(frozen_campaign_value(self.run, self.plan, "campaign.no_such_knob", 7), 7)

    def test_quick_freeze_without_source(self):
        plan = freeze(self.resolved, self.dir / "quick", freeze_source=False)
        self.assertIsNone(plan["source_manifest_sha256"])
        self.assertFalse((self.dir / "quick" / "source").exists())
        verify_freeze(self.dir / "quick")

    def test_git_head_without_running_git(self):
        info = git_info(PACKAGE_ROOT, probe_status=False)
        self.assertIsNone(info["dirty"])
        if info["error"] is None:
            self.assertRegex(info["commit"] or "", r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
