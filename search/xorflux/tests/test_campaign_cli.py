"""CLI: argument parsing, plan/status/verify output, knob explanation, error reporting."""
import contextlib
import io
import json
import math
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from xorflux import cli
from xorflux.campaign.freeze import freeze, load_campaign, resolve
from xorflux.campaign.records import RecordWriter
from xorflux.tests.test_campaign_stub import (BACKEND, LADDER, StubBackend, circuit, toy_campaign,
                                                write_campaign)


def run_cli(*argv):
    """(exit code, stdout, stderr) of one CLI call."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class ParserTest(unittest.TestCase):
    def parse(self, *argv):
        return cli.build_parser().parse_args(list(argv))

    def test_commands(self):
        args = self.parse("run", "c.toml", "--out", "d", "--seconds", "2h", "--set", "a.b=1", "--set", "c=x")
        self.assertEqual((args.campaign, args.out, args.seconds, args.set), ("c.toml", "d", 7200.0, ["a.b=1", "c=x"]))
        self.assertEqual(self.parse("resume", "d").seconds, None)           # plan duration
        for unbounded in ("0", "none", "inf"):                               # until stopped
            self.assertEqual(self.parse("resume", "d", "--seconds", unbounded).seconds, math.inf)
        self.assertTrue(self.parse("run", "c.toml", "--out", "d", "--detach").detach)
        self.assertTrue(self.parse("resume", "d", "--detach").detach)
        self.assertIsNone(self.parse("config", "explain").key)
        self.assertEqual(self.parse("stop", "d", "--wait", "5").wait, 5.0)
        self.assertTrue(self.parse("status", "d", "--json").json)
        self.assertTrue(self.parse("plan", "c.toml", "--settings").settings)
        self.assertEqual(self.parse("verify", "x.json", "--target", "t", "--cap", "3").cap, 3)
        args = self.parse("config", "show", "--profile", "large", "--non-default", "--set", "k=1")
        self.assertEqual((args.profile, args.non_default, args.set), (["large"], True, ["k=1"]))
        self.assertEqual(self.parse("config", "explain", "sharing").key, "sharing")
        self.assertEqual(self.parse("targets", "show", "toy4").name, "toy4")
        args = self.parse("quick", "toy4", "--seconds", "30", "--seed", "4", "--depth-cap", "2")
        self.assertEqual((args.seconds, args.seed, args.depth_cap, args.objective), (30.0, 4, 2, "gates"))
        self.assertEqual(self.parse("_worker", "d", "w", "tok", "--cpu", "3").cpu, 3)

    def test_bad_arguments_exit_with_usage(self):
        for argv in (["run", "c.toml"], ["quick"], ["config"], ["run", "c.toml", "--out", "d", "--seconds", "soon"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as ctx, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.parse(*argv)
            self.assertEqual(ctx.exception.code, 2)

    def test_hidden_commands_not_listed(self):
        help_text = cli.build_parser().format_help()
        self.assertIn("quick", help_text)
        self.assertNotIn("_worker", help_text)


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.campaign = write_campaign(self.dir, toy_campaign())

    def tearDown(self):
        self.tmp.cleanup()

    def test_plan_prints_workers_and_settings(self):
        code, out, _ = run_cli("plan", str(self.campaign), "--settings", "--set", "sharing.mode=off")
        self.assertEqual(code, 0)
        self.assertIn("a-00", out)
        self.assertIn("a-01", out)
        self.assertIn("sharing.mode = \"off\"  # cli", out)
        self.assertIn("worker.status_seconds = 0.3  # campaign:set", out)
        code, out, _ = run_cli("plan", str(self.campaign), "--json")
        self.assertIn('"workers"', out)

    def test_errors_are_reported_not_raised(self):
        code, _, err = run_cli("plan", str(self.dir / "missing.toml"))
        self.assertEqual(code, 1)
        self.assertIn("campaign file not found", err)
        code, _, err = run_cli("plan", str(self.campaign), "--set", "sharing.mood=pull")
        self.assertEqual(code, 1)
        self.assertIn("did you mean sharing.mode", err)
        code, _, err = run_cli("status", str(self.dir))
        self.assertIn("not a xorflux run directory", err)

    def test_status_and_verify_on_run_directory(self):
        run = self.dir / "run"
        plan = freeze(resolve(load_campaign(self.campaign), campaign_path=self.campaign), run, freeze_source=False)
        code, out, _ = run_cli("status", str(run))
        self.assertEqual(code, 0)
        self.assertIn("prepared (never started)", out)
        spec = plan["workers"][1]
        backend = StubBackend()
        target = backend.load_target(str(run / "targets" / "toy4.json"))
        context = {"run_id": plan["run_id"], "worker": spec["id"], "group": "a", "target": "toy4",
                   "matrix_sha256": plan["targets"]["toy4"]["matrix_sha256"]}
        writer = RecordWriter(run / "workers" / spec["id"], run, context, backend, target, spec, 4, 32, True)
        entry = writer.add({"circuit": circuit(LADDER[3])})
        code, out, _ = run_cli("verify", str(run))
        self.assertEqual(code, 0, out)
        self.assertIn("records verified: 1   failed: 0", out)
        (run / entry["path"]).with_suffix(".ncff").write_text("tampered\n")
        code, out, _ = run_cli("verify", str(run))
        self.assertEqual(code, 1)
        self.assertIn("NCFF export differs", out)
        code, out, _ = run_cli("report", str(run))
        self.assertIn("report.txt", out)

    def test_quick_runs_in_process(self):
        out_dir = self.dir / "quick"
        code, out, err = run_cli("quick", "toy4", "--seconds", "0.5", "--seed", "3", "--out", str(out_dir),
                                 "--backend", BACKEND, "--set", "worker.status_seconds=0.2")
        self.assertEqual(code, 0, out + err)
        self.assertIn("stopped:", out)
        self.assertIn("best 3@3", out)
        self.assertTrue((out_dir / "workers" / "quick-00" / "checkpoint.json").is_file())
        self.assertFalse((out_dir / "source").exists())
        code, out, _ = run_cli("verify", str(out_dir))
        self.assertEqual(code, 0, out)
        code, out, _ = run_cli("status", str(out_dir))
        self.assertIn("standalone (quick) run, stopped", out)
        self.assertIn("frontier 3@3 (quick-00)", out)

    def test_config_show_and_targets(self):
        with mock.patch.object(cli, "Backend", StubBackend):
            code, out, _ = run_cli("config", "show", "--prefix", "sharing", "--flat")
            self.assertEqual(code, 0)
            self.assertIn('sharing.mode = "pull"  # default', out)
            profile = self.dir / "mine.toml"
            profile.write_text("[worker]\ncheckpoint_seconds = 10.0\n")
            code, out, _ = run_cli("config", "show", "--profile", str(profile), "--non-default",
                                   "--set", "sharing.mode=off", "--flat")
            self.assertIn("worker.checkpoint_seconds = 10.0  # profile:mine", out)
            self.assertIn('sharing.mode = "off"  # cli', out)
            self.assertNotIn("# default", out)
            # Default output: a commented TOML profile with one table per section.
            code, out, _ = run_cli("config", "show", "--prefix", "sharing", "--set", "sharing.mode=off")
            self.assertEqual(code, 0)
            self.assertIn("[sharing]\n", out)
            self.assertIn('mode = "off"  # cli', out)
            self.assertIn("# How workers share elites", out)
            self.assertEqual(tomllib.loads(out)["sharing"]["mode"], "off")
            code, out, _ = run_cli("config", "explain", "campaign.pin_cpus")
            self.assertIn("legal values: bool", out)
            code, out, _ = run_cli("config", "explain")
            self.assertIn("sharing", out)
            self.assertIn("knobs", out)
            code, out, _ = run_cli("targets", "list")
            self.assertIn("toy4", out)
            code, out, _ = run_cli("targets", "show", "toy4")
            self.assertIn("seed s0: 6 gates, depth 3, verified", out)
            code, out, _ = run_cli("verify", str(self.dir / "c.json"), "--target", "toy4")
            self.assertEqual(code, 1)
            (self.dir / "c.json").write_text(json.dumps(circuit(LADDER[3])))
            code, out, _ = run_cli("verify", str(self.dir / "c.json"), "--target", "toy4", "--cap", "3")
            self.assertEqual(code, 0, out)
            self.assertIn('"gate_count": 3', out)

    def test_explain(self):
        schema = StubBackend().schema()
        text = cli.explain_text(schema, "sharing.mode")
        self.assertIn("one of pull | off", text)
        self.assertIn('default: "pull"', text)
        text = cli.explain_text(schema, "worker")
        self.assertIn("checkpoint_seconds = 60.0  [float >= 1]", text)
        with self.assertRaisesRegex(Exception, "did you mean"):
            cli.explain_text(schema, "worker.checkpoint_second")


if __name__ == "__main__":
    unittest.main()
