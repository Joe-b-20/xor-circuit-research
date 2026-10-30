"""Campaign file resolution: layering, provenance, worker plan, errors."""
import tempfile
import unittest
from pathlib import Path

from xorsearch.campaign.freeze import PlanError, load_campaign, parse_duration, resolve
from xorsearch.campaign.records import Backend
from xorsearch.tests.test_campaign_stub import (LADDER, StubBackend, circuit, toy_campaign, toy_target,
                                                write_campaign)

GROUPS = """
[[workers]]
name = "capped"
target = "toy4"
count = 3
depth_cap = [2, 3, "none"]
gate_limit = 6
seeds = ["target", "root:paar"]
profiles = ["fast.toml"]          # a profile file next to the campaign file
per_worker = [{}, { "worker.records_per_point" = 5 }]
[workers.set]
"sharing.sample_points" = 2

[[workers]]
name = "free"
target = "toy4"
objective = "depth_then_gates"
seeds = ["better.json"]
"""


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "better.json").write_text(__import__("json").dumps(circuit(LADDER[2])))
        (self.dir / "fast.toml").write_text("[worker]\ncheckpoint_seconds = 10.0\n"
                                            "[sharing]\nexclude_own = false\n")

    def tearDown(self):
        self.tmp.cleanup()

    def resolve(self, text, assignments=()):
        path = write_campaign(self.dir, text)
        return resolve(load_campaign(path), campaign_path=path, assignments=assignments)

    def test_workers_and_cycles(self):
        r = self.resolve(toy_campaign(GROUPS))
        workers = r.plan["workers"]
        self.assertEqual([w["id"] for w in workers], ["capped-00", "capped-01", "capped-02", "free-00"])
        self.assertEqual([w["depth_cap"] for w in workers], [2, 3, None, None])
        self.assertEqual([w["seed"]["kind"] for w in workers], ["file", "root", "file", "file"])
        self.assertEqual(workers[1]["seed"]["constructor"], "paar")
        self.assertEqual([w["rng_seed"] for w in workers], [11, 11 + 1000003, 11 + 2 * 1000003, 11 + 3 * 1000003])
        self.assertEqual(workers[3]["objective"], "depth_then_gates")
        seed = r.plan["seeds"][workers[3]["seed"]["sha256"]]
        self.assertEqual((seed["gates"], seed["depth"]), (4, 2))
        self.assertEqual(len(r.plan["targets"]), 1)  # one target key shared by both groups

    def test_provenance_of_every_layer(self):
        r = self.resolve(toy_campaign(GROUPS, head='sharing = "off"'), ["worker.status_seconds=0.7"])
        s0, s1, free = r.settings["capped-00"], r.settings["capped-01"], r.settings["free-00"]
        self.assertEqual(s0.origin("campaign.git_status"), "campaign:set")
        self.assertEqual(s0.origin("sharing.mode"), "campaign")
        self.assertEqual(s0["sharing.mode"], "off")
        self.assertEqual(s0.origin("worker.checkpoint_seconds"), "campaign:set")  # set beats profile
        self.assertEqual(s0.origin("sharing.exclude_own"), "profile:fast")
        self.assertEqual(s0.origin("worker.status_seconds"), "cli")               # cli beats all
        self.assertEqual(s0.origin("sharing.sample_points"), "group:capped")
        self.assertEqual(s1.origin("worker.records_per_point"), "worker:capped-01")
        self.assertEqual(s0.origin("worker.records_per_point"), "default")
        self.assertEqual(free.origin("sharing.sample_points"), "default")
        self.assertEqual(r.campaign_settings.origin("worker.status_seconds"), "cli")
        self.assertNotEqual(r.plan["workers"][0]["settings_sha256"], r.plan["workers"][1]["settings_sha256"])

    def test_profile_layer_label(self):
        text = toy_campaign(GROUPS, sets="")
        r = self.resolve(text)
        self.assertEqual(r.settings["capped-00"].origin("worker.checkpoint_seconds"), "profile:fast")
        self.assertEqual(r.settings["free-00"].origin("worker.checkpoint_seconds"), "default")

    def test_notes_for_seed_above_cap(self):
        r = self.resolve(toy_campaign(GROUPS))
        self.assertTrue(any("capped-00" in n and "above its real cap" in n for n in r.plan["notes"]))

    def test_errors_are_specific(self):
        cases = [
            (toy_campaign('[[workers]]\ntarget = "toy4"\ncont = 2\n'), "did you mean count"),
            (toy_campaign('[[workers]]\ntarget = "nope"\n'), "target 'nope'"),
            (toy_campaign('[[workers]]\ntarget = "toy4"\n[workers.set]\n"campaign.pin_cpus" = true\n'),
             "campaign-wide"),
            (toy_campaign('[[workers]]\ntarget = "toy4"\n[workers.set]\n"sharing.mode" = "pul"\n'), "not in"),
            (toy_campaign('[[workers]]\ntarget = "toy4"\n[workers.set]\n"sharing.mod" = "pull"\n'),
             "did you mean sharing.mode"),
            (toy_campaign('[[workers]]\ntarget = "toy4"\nobjective = "fast"\n'), "objective 'fast'"),
            (toy_campaign('[[workers]]\ntarget = "toy4"\ndepth_cap = -1\n'), "depth_cap"),
            (toy_campaign('[[workers]]\ntarget = "toy4"\ncount = 500\n'), "available CPUs"),
            (toy_campaign('[[workers]]\nname="x"\ntarget = "toy4"\n[[workers]]\nname="x"\ntarget="toy4"\n'),
             "used twice"),
            (toy_campaign(""), "at least one [[workers]]"),
        ]
        for text, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(PlanError) as ctx:
                    self.resolve(text)
                self.assertIn(message, str(ctx.exception))

    def test_bad_seed_is_rejected(self):
        (self.dir / "bad.json").write_text('{"gates": [[0, 1]]}')
        with self.assertRaisesRegex(PlanError, "does not compute"):
            self.resolve(toy_campaign('[[workers]]\ntarget = "toy4"\nseeds = ["bad.json"]\n'))

    def test_oversubscription_can_be_allowed(self):
        text = toy_campaign('[[workers]]\ntarget = "toy4"\ncount = 64\n')
        r = self.resolve(text, ["campaign.allow_oversubscription=true"])
        self.assertEqual(len(r.plan["workers"]), 64)

    def test_examples_resolve(self):
        # Every shipped example must be valid against the campaign runtime's schema.  Catalog
        # names are mapped to the toy target (the real catalog is core's).
        class AnyTarget(StubBackend):
            def schema(self):  # examples use profiles with engine and move knobs
                return Backend().schema()

            def load_target(self, spec):
                return toy_target()
        examples = Path(__file__).resolve().parents[1] / "examples"
        for path in sorted(examples.glob("*.toml")):
            with self.subTest(example=path.name):
                r = resolve(load_campaign(path), campaign_path=path, backend=AnyTarget(),
                            assignments=["campaign.allow_oversubscription=true"])
                self.assertTrue(r.plan["workers"])
        r = resolve(load_campaign(examples / "three_targets.toml"), campaign_path=examples / "three_targets.toml",
                    backend=AnyTarget(), assignments=["campaign.allow_oversubscription=true"])
        self.assertEqual([w["depth_cap"] for w in r.plan["workers"][:4]], [5, 6, None, None])
        self.assertEqual(r.settings["joltik-depth-01"].origin("worker.records_per_point"), "worker:joltik-depth-01")
        self.assertEqual(r.settings["joltik-depth-00"].origin("sharing.sample_points"), "group:joltik-depth")
        self.assertEqual(r.settings["aes-00"].origin("sharing.scope"), "campaign")

    def test_parse_duration(self):
        self.assertIsNone(parse_duration(None))
        self.assertIsNone(parse_duration(0))
        self.assertEqual(parse_duration(90), 90.0)
        self.assertEqual(parse_duration("45m"), 2700.0)
        self.assertEqual(parse_duration("2h30m"), 9000.0)
        self.assertEqual(parse_duration("1d"), 86400.0)
        for bad in ("2 hours", "h", True, -1):
            with self.subTest(bad=bad), self.assertRaises(PlanError):
                parse_duration(bad)


if __name__ == "__main__":
    unittest.main()
