"""Report tests on a synthetic run directory.

``make_synthetic_run`` drives the real ``Recorder``/``EventLog`` with fake clocks to produce a
small campaign (2-3 workers, coordinator events, dossiers, restarts from every source, shared
lineage).  It is also handy for previewing the report:
``python3 -c "from xorflux.tests.test_telemetry_report import make_synthetic_run as m; m('RUN')"``.
"""
from __future__ import annotations

import csv
import random
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from xorflux.config.settings import for_sections
from xorflux.telemetry import metrics
from xorflux.telemetry.recorder import KNOBS, EventLog, Recorder, read_log
from xorflux.telemetry.report import build_report

MOVES = ("walk.remove1", "walk.expand", "lns.cone", "lns.small", "depth.repair")
WEIGHTS = (5, 2, 3, 1, 1)
COMPONENTS = {
    "walk.remove1": [["remove1", "repair.exact"]],
    "walk.expand": [["remove2", "add1"], ["remove1", "add2"]],
    "lns.cone": [["destroy.cone", "inject", "rebuild.deadline", "peel"],
                 ["destroy.cone", "rebuild.greedy", "peel"]],
    "lns.small": [["destroy.small", "rebuild.greedy"]],
    "depth.repair": [["rebuild.cap", "reschedule"]],
}


class FakeClock:
    """Manually advanced monotonic clock."""

    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def _fake_gates(n_inputs: int, count: int, rng: random.Random):
    """A random index-pair circuit with ``count`` gates (only its shape matters here)."""
    gates = []
    for k in range(count):
        top = n_inputs + k
        i = rng.randrange(top)
        j = rng.randrange(top - 1)
        gates.append([i, j + (j >= i)])
    return gates, [n_inputs + count - 1]


def make_synthetic_run(root, workers=("w00", "w01", "w02"), iterations=2500, seed=7,
                       settings=None) -> dict:
    """Write a synthetic campaign into ``root``; returns expected counts for assertions."""
    root = Path(root)
    rng = random.Random(seed)
    settings = settings or for_sections(*KNOBS, overrides={"telemetry": {
        "epoch_seconds": 10.0, "followup_iterations": [50, 200], "ring_size": 32}})
    expected = {"improvements": 0, "restarts": 0, "plateaus": 0, "epochs": 0,
                "workers": len(workers), "frontier": 0, "diversity": 0}
    published = []          # (t, worker, improvement id, gates, depth)
    chains_at = []          # (t, worker, frozenset) for the diversity panel
    n_inputs = 12
    for wi, w in enumerate(workers):
        clock = FakeClock()
        rec = Recorder(root / "workers" / w, w, settings, clock=clock, t0=0.0,
                       wall=lambda c=clock: 1.8e9 + c.t, process_time=lambda c=clock: 0.97 * c.t)
        gates, depth = 140 + 3 * wi, 9
        values = set(rng.sample(range(n_inputs + 1, 1 << n_inputs), gates))
        rec.begin("start", {"seed": seed + wi, "source_hash": "f00d", "target": "synthetic",
                            "root": {"id": f"seed#{wi}", "constructor": "seed"}, "source": "seed"})
        best = (gates, depth)
        tracker = metrics.PlateauTracker()
        tracker.enter((gates, depth), frozenset(values), 0, 0.0)
        phase = "plateau"
        for it in range(1, iterations + 1):
            clock.t += rng.uniform(0.01, 0.05) * (1 + 0.25 * wi)
            move = rng.choices(MOVES, WEIGHTS)[0]
            comps = rng.choice(COMPONENTS[move])
            p_imp = 0.03 * (gates - 110) / 40 if gates > 112 else 0.0005
            improved = rng.random() < max(0.0005, p_imp)
            depth_gain = (not improved and move == "depth.repair" and depth > 6
                          and rng.random() < 0.01)
            accepted = improved or depth_gain or rng.random() < 0.35
            neutral = accepted and not improved and not depth_gain and rng.random() < 0.7
            d_gates = -1 if improved else (0 if accepted and (neutral or depth_gain) else 1)
            d_depth = -1 if depth_gain else 0
            before_vals = frozenset(values)
            if accepted:
                victim = rng.choice(sorted(values))
                values.discard(victim)
                while not improved:   # neutral / depth moves swap one value for a new one
                    fresh = rng.randrange(n_inputs + 1, 1 << n_inputs)
                    if fresh not in values and fresh != victim:
                        values.add(fresh)
                        break
                gates = len(values)
                depth += d_depth
            key = frozenset(values) if accepted else None
            new_worker_best = ((improved or depth_gain) and (gates, depth) < best
                               and (gates < best[0] or depth < best[1]))
            r = {"it": it, "move": move, "accepted": accepted, "neutral": neutral,
                 "d_gates": d_gates, "d_depth": d_depth, "gates": gates, "depth": depth,
                 "work": rng.randint(5, 40), "components": comps,
                 "valid": move != "walk.expand" or rng.random() < 0.6,
                 "improved_chain": improved or depth_gain, "improved_worker": new_worker_best}
            rec.proposal(r)
            tracker.observe(key, accepted, neutral, it, clock.t)
            if improved or depth_gain:
                if new_worker_best:
                    snap = tracker.snapshot(it, clock.t)
                    kind = "gates" if gates < best[0] else "depth"
                    g, outs = _fake_gates(n_inputs, gates, rng)
                    sd = metrics.symmetric_difference(before_vals, values)
                    did = rec.improvement({
                        "kind": kind, "before": {"gates": best[0], "depth": best[1]},
                        "after": {"gates": gates, "depth": depth}, "move": move,
                        "phase": phase, "deterministic": True,
                        "trace": {"components": comps, "params": {"k": rng.randint(2, 12)},
                                  "removed": sd["removed"], "added": sd["added"]},
                        "state_before": {"plateau": snap, "neutral_rate": snap["neutral_rate"],
                                         "phase": phase,
                                         "weights": dict(zip(MOVES, WEIGHTS))},
                        "values_before": sorted(before_vals), "values_after": sorted(values),
                        "gates_after": g, "outputs": outs,
                        "shape_after": metrics.shape_from_gates(g, outs, n_inputs),
                        "rng": {"seed": seed + wi, "state": f"{rng.getrandbits(64):x}"},
                        "verification": {"ok": True},
                    })
                    best = (gates, depth)
                    published.append((clock.t, w, did, gates, depth, kind))
                    expected["improvements"] += 1
                rec.event("plateau", **tracker.close("improve", it, clock.t))
                expected["plateaus"] += 1
                tracker.enter((gates, depth), frozenset(values), it, clock.t)
                if phase != "burst":
                    rec.event("phase", **{"from": phase, "to": "burst", "reason": "new best"})
                    phase = "burst"
            elif phase == "burst" and rng.random() < 0.02:
                rec.event("phase", **{"from": "burst", "to": "plateau", "reason": "budget"})
                phase = "plateau"
            if it % 800 == 0:
                source = ("fresh", "elite", "shared")[(it // 800 + wi) % 3]
                donors = [p for p in published if p[1] != w and p[0] < clock.t]
                parent = donor = None
                if source == "shared" and donors:
                    _, donor, parent, gates, depth, _ = donors[-1]
                elif source == "fresh":
                    gates, depth = best[0] + rng.randint(8, 25), 9
                else:
                    gates, depth = best[0] + rng.randint(0, 3), best[1]
                values = set(rng.sample(range(n_inputs + 1, 1 << n_inputs), gates))
                rec.event("plateau", **tracker.close("restart", it, clock.t))
                expected["plateaus"] += 1
                rec.event("restart", reason="stall_seconds", source=source, parent=parent,
                          donor=donor, root={"id": f"{source}#{it}", "constructor": "naive",
                                             "seed": it, "gates": gates},
                          prev={"best": {"gates": best[0], "depth": best[1]}})
                expected["restarts"] += 1
                tracker.enter((gates, depth), frozenset(values), it, clock.t)
            if it % 250 == 0:
                chains_at.append((clock.t, w, frozenset(values)))
            if rec.epoch_due():
                rec.epoch({"phase": phase, "plateau": tracker.snapshot(),
                           "weights": dict(zip(MOVES, WEIGHTS)),
                           "acceptance": {"kind": "threshold", "threshold": 0}})
                expected["epochs"] += 1
        if rec._combos:            # close() writes a partial epoch for an open one
            expected["epochs"] += 1
        rec.close()

    # Coordinator: frontier changes and diversity snapshots.
    cclock = FakeClock()
    log = EventLog(root / "campaign.jsonl", "coord", settings=settings, clock=cclock, t0=0.0)
    best_g = None
    for t, w, did, g, d, kind in sorted(published):
        if best_g is None or g < best_g:
            cclock.t = t + 0.5
            best_g = g
            log.write("frontier", point={"gates": g, "depth": d}, by=w, improvement=did,
                      kind=kind, record=f"rec-{did}", dag=f"{hash(did) & 0xffff:04x}",
                      frontier=[{"gates": g, "depth": d}])
            expected["frontier"] += 1
    chains_at.sort(key=lambda x: x[0])
    latest = {}
    for t, w, s in chains_at:
        latest[w] = s
        if len(latest) == len(workers):
            cclock.t = t
            div = metrics.diversity(list(latest.values()))
            log.write("fleet_diversity", scope="chains", workers=sorted(latest), **div)
            expected["diversity"] += 1
    log.close()
    return expected


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class _Balance(HTMLParser):
    """Checks every non-void tag is closed in order."""
    VOID = {"meta", "br", "img", "input", "link", "hr", "col", "wbr", "source"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors, self.tags = [], [], set()

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        for name, value in attrs:
            if name in ("src", "href") and value and value.startswith(("http:", "https:", "//")):
                self.errors.append(f"external resource {value}")
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.tags.add(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> with open {self.stack[-3:]}")
        else:
            self.stack.pop()


class ReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.rundir = Path(cls.tmp.name) / "run"
        cls.expected = make_synthetic_run(cls.rundir)
        cls.page = build_report(cls.rundir)
        cls.out = cls.page.parent

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_tables_written(self):
        for name in ("improvements", "epochs", "moves", "combos", "plateaus", "restarts",
                     "restart_sources", "frontier", "fleet_diversity"):
            self.assertTrue((self.out / f"{name}.csv").exists(), name)

    def test_row_counts_match_the_run(self):
        e = self.expected
        self.assertGreater(e["improvements"], 10)
        self.assertEqual(len(_read_csv(self.out / "improvements.csv")), e["improvements"])
        self.assertEqual(len(_read_csv(self.out / "restarts.csv")), e["restarts"])
        self.assertEqual(len(_read_csv(self.out / "plateaus.csv")), e["plateaus"])
        self.assertEqual(len(_read_csv(self.out / "epochs.csv")), e["epochs"])
        self.assertEqual(len(_read_csv(self.out / "frontier.csv")), e["frontier"])
        self.assertEqual(len(_read_csv(self.out / "fleet_diversity.csv")), e["diversity"])

    def test_improvement_attribution_columns(self):
        rows = _read_csv(self.out / "improvements.csv")
        for col in ("id", "worker", "move", "components", "phase", "chain", "root",
                    "root_source", "parent", "plateau_age_s", "plateau_distinct",
                    "s_since_root", "dossier", "fu50_later", "fu200_plateau_it"):
            self.assertIn(col, rows[0])
        for r in rows:
            self.assertTrue(r["move"] and r["components"] and r["chain"])
            self.assertTrue((self.rundir / r["dossier"]).exists(), r["dossier"])
        # Shared restarts produce cross-worker lineage parents.
        cross = [r for r in rows if r["parent"] and not r["parent"].startswith(r["worker"])]
        self.assertTrue(cross, "expected at least one improvement descended from another worker")

    def test_moves_totals_and_rates(self):
        rows = _read_csv(self.out / "moves.csv")
        fleet = {r["move"]: r for r in rows if r["scope"] == "all"}
        self.assertEqual(set(fleet), set(MOVES))
        imps = _read_csv(self.out / "improvements.csv")
        self.assertEqual(sum(int(r["improvements"]) for r in fleet.values()), len(imps))
        # improved_worker counters agree with the improvement events
        self.assertEqual(sum(int(r["improved_worker"]) for r in fleet.values()), len(imps))
        for r in fleet.values():
            self.assertGreater(float(r["cpu_h"]), 0)
            if int(r["improvements"]):
                self.assertGreater(float(r["improvements_per_cpu_h"]), 0)
        per_worker = [r for r in rows if r["scope"] != "all"]
        self.assertEqual({r["scope"] for r in per_worker}, {"w00", "w01", "w02"})

    def test_html_is_well_formed_and_self_contained(self):
        text = self.page.read_text(encoding="utf-8")
        parser = _Balance()
        parser.feed(text)
        parser.close()
        self.assertEqual(parser.errors, [])
        self.assertEqual(parser.stack, [])
        self.assertIn("svg", parser.tags)
        self.assertIn("prefers-color-scheme:dark", text)
        self.assertNotIn("<script src", text)
        self.assertIn("dossiers/w00-000001.json", text)

    def test_tolerates_crash_cut_line_and_missing_event(self):
        """A truncated last line is skipped; a dossier whose improve line was lost is
        recovered from the dossier itself."""
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            make_synthetic_run(run, workers=("a0", "a1"), iterations=900, seed=3)
            log = run / "workers" / "a0" / "events.jsonl"
            lines = log.read_text(encoding="utf-8").splitlines(True)
            dropped = [ln for ln in lines if '"ev":"improve"' in ln][-1]
            kept = [ln for ln in lines if ln is not dropped]
            log.write_text("".join(kept) + '{"v":1,"t":99,"ev":"epo', encoding="utf-8")
            page = build_report(run, Path(tmp) / "out")
            rows = _read_csv(page.parent / "improvements.csv")
            recovered = [r for r in rows if r["recovered"] == "True"]
            self.assertEqual(len(recovered), 1)
            self.assertIn("undecodable", page.read_text(encoding="utf-8"))

    def test_before_during_after_columns(self):
        rows = _read_csv(self.out / "improvements.csv")
        for col in ("move_weight", "ring_accept_rate", "ring_moves", "plateau_after_s",
                    "plateau_after_exit", "fu50_next", "fu50_next_chain_best_it_since",
                    "fu200_restart_it_since", "fu200_best_gain_gates", "cpu_s_since_root",
                    "verified", "replayable"):
            self.assertIn(col, rows[0])
        self.assertTrue(any(r["ring_accept_rate"] for r in rows))
        self.assertTrue(any(r["plateau_after_s"] for r in rows))
        self.assertTrue(any(r["fu200_next"] for r in rows))
        self.assertTrue(all(r["verified"] == "True" for r in rows))

    def test_restart_sources_summarise_restarts(self):
        rows = _read_csv(self.out / "restart_sources.csv")
        self.assertEqual({r["source"] for r in rows}, {"fresh", "elite", "shared"})
        self.assertEqual(sum(int(r["restarts"]) for r in rows), self.expected["restarts"])
        restarts = _read_csv(self.out / "restarts.csv")
        self.assertIn("chain_best_gates", restarts[0])
        self.assertTrue(any(r["chain_best_gates"] for r in restarts))

    def test_combos_have_cpu_rates(self):
        rows = _read_csv(self.out / "combos.csv")
        self.assertIn("chain_improvements_per_cpu_h", rows[0])
        self.assertIn("cpu_h", rows[0])

    def test_html_has_new_sections(self):
        text = self.page.read_text(encoding="utf-8")
        for title in ("Plateau shape", "Search state over time", "Restarts",
                      "Before, during and after each improvement",
                      "Sub-operation combinations: chain bests per CPU-hour"):
            self.assertIn(title, text)

    def test_rejected_dossier_is_not_recovered_and_list_scores_parse(self):
        """A verifier-rejected dossier is no improvement; epochs written by an older engine
        with ``[gates, depth]`` lists still give score columns."""
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            clock = FakeClock()
            rec = Recorder(run / "workers" / "x0", "x0", clock=clock, t0=0.0)
            rec.begin("start", {})
            rec.proposal({"it": 1, "move": "m", "accepted": True, "neutral": False,
                          "d_gates": -1, "d_depth": 0, "gates": 9, "depth": 3, "work": 1,
                          "components": ["m"], "improved_worker": True})
            rec.improvement({"kind": "gates", "after": {"gates": 9, "depth": 3}, "move": "m",
                             "trace": {"components": ["m"]}},
                            verify=lambda did: {"ok": False})
            clock.t = 5.0
            rec.epoch({"chain": [9, 3], "chain_best": [9, 3], "worker_best": None})
            rec.close()
            page = build_report(run, Path(tmp) / "out")
            self.assertEqual(_read_csv(page.parent / "improvements.csv"), [])
            ep = _read_csv(page.parent / "epochs.csv")[0]
            self.assertEqual((ep["chain_gates"], ep["chain_best_gates"]), ("9", "9"))

    def test_logs_are_ordered_and_enveloped(self):
        for w in ("w00", "w01", "w02"):
            evs = list(read_log(self.rundir / "workers" / w / "events.jsonl"))
            ts = [e["t"] for e in evs]
            self.assertEqual(ts, sorted(ts))
            for e in evs:
                self.assertEqual(set(("v", "t", "utc", "worker", "it", "ev")) - set(e), set())
            self.assertEqual(evs[0]["ev"], "start")
            self.assertEqual(evs[-1]["ev"], "stop")


if __name__ == "__main__":
    unittest.main()
