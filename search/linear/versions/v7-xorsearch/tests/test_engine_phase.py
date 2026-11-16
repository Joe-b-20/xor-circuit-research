"""Phase priors and the burst / plateau / repair controller."""
import unittest

from xorsearch.engine.phase import BURST, PLATEAU, REPAIR, PhaseController, phase_priors
from xorsearch.tests.test_engine_fakes import NoopMove, move_section, settings_for


def setup(specs, **overrides):
    """``specs``: (name, family, weight, burst_weight, repair_weight) per move."""
    sections = [move_section(n, w, bw, rw) for n, _, w, bw, rw in specs]
    settings = settings_for(sections, {f"phase.{k}": v for k, v in overrides.items()})
    moves = [NoopMove(settings, n, family=f) for n, f, *_ in specs]
    return settings.view("phase"), moves


class PriorsTest(unittest.TestCase):
    def test_burst_is_near_uniform_over_local_moves(self):
        cfg, moves = setup([("walk", "walk", 6.0, None, None), ("lns", "lns", 2.0, None, None),
                            ("x", "other", 1.0, None, None)], burst_uniform=0.8)
        pri = phase_priors(moves, cfg)
        self.assertEqual(pri[PLATEAU], [6.0, 2.0, 1.0])
        self.assertAlmostEqual(pri[BURST][0], 0.2 * 0.75 + 0.4)
        self.assertAlmostEqual(pri[BURST][1], 0.2 * 0.25 + 0.4)
        self.assertEqual(pri[BURST][2], 0.0)                     # not a burst family

    def test_burst_weight_knob_and_zero_weight_moves(self):
        cfg, moves = setup([("walk", "walk", 1.0, 3.0, None), ("cores", "structural", 0.0,
                                                               None, None)])
        pri = phase_priors(moves, cfg)
        self.assertGreater(pri[BURST][0], 0)
        self.assertEqual(pri[BURST][1], 0.0)                     # switched off stays off

    def test_repair_share(self):
        cfg, moves = setup([("walk", "walk", 3.0, None, None), ("lns", "lns", 1.0, None, None),
                            ("dep", "depth", 0.0, None, 2.0)], repair_share=0.8)
        pri = phase_priors(moves, cfg)
        self.assertAlmostEqual(pri[REPAIR][2], 0.8)
        self.assertAlmostEqual(pri[REPAIR][0], 0.15)
        self.assertAlmostEqual(pri[REPAIR][1], 0.05)

    def test_repair_default_weight(self):
        cfg, moves = setup([("walk", "walk", 1.0, None, None), ("dep", "depth", 0.0, None,
                                                                None)])
        self.assertGreater(phase_priors(moves, cfg)[REPAIR][1], 0)


class ControllerTest(unittest.TestCase):
    def controller(self, **overrides):
        cfg, moves = setup([("walk", "walk", 1.0, None, None), ("dep", "depth", 1.0, None,
                                                                None)], **overrides)
        return PhaseController(cfg, phase_priors(moves, cfg))

    def test_burst_then_plateau(self):
        pc = self.controller(burst_budget=3)
        self.assertEqual(pc.phase, PLATEAU)
        self.assertTrue(pc.on_chain_best(False))
        self.assertEqual(pc.phase, BURST)
        self.assertFalse(pc.tick(1))
        self.assertFalse(pc.on_chain_best(False))               # renewed, same phase
        self.assertEqual(pc.left, 3)
        pc.tick(1), pc.tick(1)
        self.assertTrue(pc.tick(1))
        self.assertEqual(pc.phase, PLATEAU)

    def test_work_unit_budget(self):
        pc = self.controller(burst_budget=10, unit="work")
        pc.on_chain_best(False)
        self.assertFalse(pc.tick(9))
        self.assertTrue(pc.tick(1))

    def test_repair_keeps_budget_until_resolved(self):
        pc = self.controller(repair_budget=5)
        self.assertTrue(pc.on_chain_best(True))
        self.assertEqual(pc.phase, REPAIR)
        pc.tick(1)
        self.assertFalse(pc.on_chain_best(True))                # still repairing, budget kept
        self.assertEqual(pc.left, 4)
        self.assertTrue(pc.on_chain_best(False))                # feasible best -> burst
        self.assertEqual(pc.phase, BURST)

    def test_no_repair_moves_means_no_repair_phase(self):
        cfg, moves = setup([("walk", "walk", 1.0, None, None)])
        pc = PhaseController(cfg, phase_priors(moves, cfg))
        self.assertFalse(pc.can_repair)
        pc.on_chain_best(True)
        self.assertEqual(pc.phase, BURST)

    def test_zero_repair_budget_means_no_repair_phase(self):
        pc = self.controller(repair_budget=0)
        self.assertFalse(pc.can_repair)
        pc.on_chain_best(True)
        self.assertEqual(pc.phase, BURST)

    def test_restart_burst_knob(self):
        pc = self.controller(burst_on_restart=False)
        pc.on_restart()
        self.assertEqual(pc.phase, PLATEAU)
        pc = self.controller()
        pc.on_restart()
        self.assertEqual(pc.phase, BURST)

    def test_state_round_trip(self):
        pc = self.controller(burst_budget=7)
        pc.on_chain_best(False)
        pc.tick(1)
        other = self.controller(burst_budget=7)
        other.load_state(pc.state())
        self.assertEqual((other.phase, other.left), (BURST, 6))


if __name__ == "__main__":
    unittest.main()
