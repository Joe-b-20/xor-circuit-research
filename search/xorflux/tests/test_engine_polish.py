"""Own-depth polish (engine/polish.py): exact on small states, and every record the engine
writes below its search cap is already minimal at its own depth."""
import itertools
import json
import random
import unittest

from xorflux.config.settings import build
from xorflux.core.circuit import verify
from xorflux.core.objective import Objective
from xorflux.core.target import random_target
from xorflux.core.valueset import ValueSet
from xorflux.engine import Engine
from xorflux.engine.polish import polish
from xorflux.engine.replay import replay_dossier
from xorflux.telemetry.recorder import NullRecorder


def most_removable(n, rows, values, cap):
    """Brute force: the largest set of helpers whose removal keeps every row within ``cap``."""
    state = ValueSet(n, rows, values, cap=cap)
    state.trim()
    helpers = sorted(v for v in state.tri if v not in state.iset and v not in state.tset)
    for k in range(len(helpers), 0, -1):
        for drop in itertools.combinations(helpers, k):
            u = state.remove(drop)
            ok = state.ok()
            state.restore(u)
            if ok:
                return k
    return 0


class PolishTest(unittest.TestCase):
    def test_exact_on_small_states(self):
        rng = random.Random(5)
        shrunk = 0
        for case in range(60):
            n = 5
            rows = random_target(n, 4, seed=case).rows
            helpers = {rng.randrange(1, 1 << n) for _ in range(12)}
            values = sorted((helpers | set(rows)) - {1 << j for j in range(n)})
            loose = ValueSet(n, rows, values, cap=None)
            if not loose.ok():
                continue
            cap = loose.depth() + rng.randrange(2)
            state = ValueSet(n, rows, values, cap=cap)
            state.trim()
            if not state.ok():
                continue
            key = state.key()
            removed, exact, _ = polish(state)
            self.assertEqual(state.key(), key)          # the state is left as it was
            state.check()
            self.assertTrue(exact)
            self.assertEqual(len(removed), most_removable(n, rows, values, cap), case)
            u = state.remove(removed)
            self.assertTrue(state.ok())
            state.restore(u)
            if removed:
                shrunk += 1
                # Stopped at once, it still returns a valid (single) removal.
                some, exact, _ = polish(state, node_limit=1)
                self.assertFalse(exact)
                u = state.remove(some)
                self.assertTrue(some and state.ok())
                state.restore(u)
        self.assertGreater(shrunk, 0, "no case had a removable helper: the test checks nothing")


class EnginePolishTest(unittest.TestCase):
    def run_engine(self, objective, steps, assignments=()):
        settings = build(assignments=("restart.stall_seconds=0.0", "restart.root_seconds=0.0",
                                      "restart.stall_proposals=150", "debug.check_every=25",
                                      "scheduler.cost=work", *assignments))
        target = random_target(12, 12, seed=3)
        recorder = NullRecorder(None, "w0", settings)
        engine = Engine(target, objective, settings, rng_seed=11, recorder=recorder,
                        worker_id="w0")
        records = []

        def save(record):
            verdict = verify(record["circuit"], target)
            records.append(record)
            return {"equivalent": verdict.equivalent, "gate_count": verdict.gate_count,
                    "depth": verdict.depth}
        engine.on_record(save)
        for _ in range(steps):
            engine.step()
        return engine, records, target, settings, recorder

    def test_records_below_the_search_cap_are_minimal_at_their_depth(self):
        obj = Objective("gates", depth_cap=4, soft_depth_slack=2)
        engine, records, target, settings, recorder = self.run_engine(obj, 800)
        below = [r for r in records if r["kind"] != "record" and r["depth"] < obj.search_cap]
        self.assertTrue(below)
        for r in below:
            state = ValueSet(target.n_inputs, target.rows, r["values"], cap=r["depth"])
            state.trim()
            self.assertEqual(polish(state)[0], [], (r["gate_count"], r["depth"]))
        for d in recorder.dossiers.values():
            if "polish" in d:
                self.assertLess(d["after"]["gates"], d["polish"]["from"]["gates"])
        self.assertEqual(engine.counters["verify_fail"], 0)

    def test_polished_dossiers_replay(self):
        obj = Objective("gates", depth_cap=None)
        off = [f"moves.structural.{name}.{knob}=0.0" for name in ("translate", "cores")
               for knob in ("weight", "burst_weight")]
        engine, _, target, settings, recorder = self.run_engine(obj, 800, off)
        polished = [d for d in recorder.dossiers.values() if "polish" in d]
        self.assertLessEqual(len(polished), engine.counters["polished"])   # + chain starts
        self.assertTrue(polished, "no polish in 800 uncapped proposals")
        for d in polished:
            d = json.loads(json.dumps(d))
            out = replay_dossier(d, target, obj, settings)
            self.assertTrue(out["match"], (d["id"], d["move"], out.get("symdiff")))

    def test_off(self):
        obj = Objective("gates", depth_cap=None)
        engine, *_ = self.run_engine(obj, 300, ("engine.record_polish_nodes=0",))
        self.assertEqual(engine.counters["polished"], 0)


if __name__ == "__main__":
    unittest.main()
