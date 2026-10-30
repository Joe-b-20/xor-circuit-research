"""Configuration audit: every knob is documented and valid, every shipped profile and example
loads and resolves against the full schema, ``config show`` output is itself a valid profile."""
import contextlib
import io
import tempfile
import tomllib
import unittest
from pathlib import Path

from xorsearch import cli
from xorsearch.campaign.freeze import load_campaign, resolve
from xorsearch.config.registry import schema
from xorsearch.config.schema import Knob
from xorsearch.config.settings import PROFILE_DIR, Settings, build, builtin_profiles, to_toml
from xorsearch.tests.test_campaign_stub import StubBackend, toy_target, toy_campaign, write_campaign

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
SHIPPED = {"default", "quick", "large", "depth"}
CAMPAIGNS = Path(__file__).resolve().parents[2] / "campaigns"


class CatalogStub(StubBackend):
    """The full knob schema with every catalog name mapped to the toy target (no search runs)."""

    def schema(self):
        return schema()

    def load_target(self, spec):
        return toy_target()


def resolve_example(path: Path, *assignments):
    return resolve(load_campaign(path), campaign_path=path, backend=CatalogStub(),
                   assignments=["campaign.allow_oversubscription=true", *assignments])


class KnobAuditTest(unittest.TestCase):
    def test_every_knob_is_documented_and_its_default_is_legal(self):
        for key, knob in schema().knobs.items():
            with self.subTest(key=key):
                self.assertGreater(len(knob.doc), 15, "doc string too short to be useful")
                self.assertEqual(knob.validate(key, knob.default), knob.default)
                self.assertTrue(knob.constraint())
                if knob.choices is not None:
                    self.assertIn(knob.default, knob.choices)
        for path, section in schema().sections.items():
            with self.subTest(section=path):
                self.assertTrue(section.doc and section.knobs)

    def test_null_words_and_list_elements(self):
        cap = Knob(None, "a nullable cap for this test", kind=int, nullable=True)
        self.assertIsNone(cap.validate("k", "none"))
        self.assertIsNone(cap.validate("k", "NULL"))
        self.assertEqual(cap.validate("k", 7), 7)
        self.assertEqual(Knob("max", "a string knob for this test").validate("k", "none"), "none")
        with self.assertRaisesRegex(ValueError, "expected int"):
            Knob(3, "an int knob for this test").validate("k", "none")
        floats = Knob([0.5, 0.5], "a float list for this test")
        self.assertEqual(floats.validate("k", [1, 0]), [1.0, 0.0])
        with self.assertRaisesRegex(ValueError, "list elements must be float"):
            floats.validate("k", [0.5, "a"])
        ints = Knob([2, 3], "an int list for this test")
        for bad in ([2.0], [True]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ints.validate("k", bad)
        self.assertEqual(Knob(["a"], "a string list for this test").validate("k", []), [])
        self.assertEqual(floats.constraint(), "list of float")
        self.assertEqual(Knob(0.5, "p", min=0, max=1).constraint(), "float in [0, 1]")
        self.assertEqual(cap.constraint(), 'int, or "none"')

    def test_defaults_are_never_shared(self):
        a, b = Settings(schema()), Settings(schema())
        a.values["phase.burst_families"].append("x")
        self.assertNotIn("x", b.values["phase.burst_families"])
        self.assertNotIn("x", schema().knobs["phase.burst_families"].default)

    def test_null_from_the_command_line(self):
        settings = build(assignments=["objective.depth_cap=7", "objective.depth_cap=none"])
        self.assertIsNone(settings["objective.depth_cap"])
        self.assertEqual(settings.origin("objective.depth_cap"), "cli")


class ProfileTest(unittest.TestCase):
    def test_every_profile_loads_and_says_what_it_is(self):
        names = set(builtin_profiles())
        self.assertLessEqual(SHIPPED, names)
        for name in sorted(names):
            with self.subTest(profile=name):
                text = (PROFILE_DIR / f"{name}.toml").read_text()
                self.assertTrue(text.startswith(f"# {name} profile -- "), "first line names the purpose")
                settings = build(["default", name])
                self.assertTrue(all(origin == f"profile:{name}"
                                    for _, origin in settings.non_default().values()))

    def test_profiles_do_what_their_names_say(self):
        defaults = Settings(schema())
        quick = build(["default", "quick"]).non_default()
        self.assertTrue(quick)
        self.assertTrue(all(k.split(".")[0] in ("campaign", "worker", "sharing", "telemetry") for k in quick),
                        "quick must not change the search itself")
        large = build(["default", "large"])
        self.assertEqual(large["campaign.on_worker_failure"], "restart")
        self.assertGreater(large["worker.checkpoint_seconds"], defaults["worker.checkpoint_seconds"])
        depth = build(["default", "depth"])
        self.assertGreater(depth["moves.depth.repair.weight"], defaults["moves.depth.repair.weight"])

    def test_every_example_resolves(self):
        examples = sorted(EXAMPLES.glob("*.toml"))
        self.assertGreaterEqual(len(examples), 4)
        for path in examples:
            with self.subTest(example=path.name):
                resolved = resolve_example(path)
                self.assertTrue(resolved.plan["workers"])
                self.assertTrue(path.read_text().startswith("#"), "examples start with a comment")

    @unittest.skipUnless(CAMPAIGNS.is_dir(), "no search/campaigns/")
    def test_every_campaign_file_resolves_on_the_real_maps(self):
        # Real targets and seeds: every seed file must verify against its map.
        from xorsearch.core.target import catalog
        files = sorted(CAMPAIGNS.glob("*.toml"))
        self.assertTrue(files)
        self.assertLessEqual({p.stem for p in files}, set(catalog()), "one campaign per map name")
        for path in files:
            with self.subTest(campaign=path.name):
                resolved = resolve(load_campaign(path), campaign_path=path,
                                   assignments=["campaign.allow_oversubscription=true"])
                self.assertTrue(resolved.plan["workers"])
                self.assertEqual(set(resolved.plan["targets"]), {path.stem})

    def test_group_profile_cannot_change_campaign_wide_knobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            groups = '[[workers]]\nname = "g"\ntarget = "toy4"\nprofiles = ["large"]\n'
            path = write_campaign(tmp, toy_campaign(groups, sets=""))
            resolved = resolve(load_campaign(path), campaign_path=path, backend=CatalogStub())
        worker = resolved.settings["g-00"]
        self.assertEqual(worker["campaign.collect_seconds"], 2.0)          # the campaign value
        self.assertEqual(worker.origin("campaign.collect_seconds"), "default")
        self.assertEqual(worker["worker.checkpoint_seconds"], 300.0)       # worker knobs do apply
        self.assertTrue(any("campaign-wide knob campaign.collect_seconds" in n
                            for n in resolved.plan["notes"]))


class ConfigShowTest(unittest.TestCase):
    def test_to_toml_round_trips(self):
        settings = build(["default", "large"], assignments=["objective.depth_cap=9",
                                                            "moves.walk.expand.weight=2"])
        text = to_toml(settings)
        again = Settings(schema()).apply(tomllib.loads(text), "file")
        self.assertEqual(again.values, settings.values)
        self.assertIn("weight = 2.0  # cli", text)
        self.assertIn("checkpoint_seconds = 300.0  # profile:large", text)

    def test_cli_output_is_a_starting_profile(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["config", "show"]), 0)
        text = out.getvalue()
        self.assertIn("[moves.walk.expand]", text)
        self.assertIn("# Remove one helper, add two values (up to +1).", text)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "start.toml"
            path.write_text(text)
            settings = build([str(path)])
        self.assertEqual(settings.values, Settings(schema()).values)       # defaults, reproduced


if __name__ == "__main__":
    unittest.main()
