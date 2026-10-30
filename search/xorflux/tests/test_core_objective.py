"""``core.objective``: score keys, caps, feasibility and settings defaults."""
import unittest

from xorflux.config.settings import for_sections
from xorflux.core.objective import KNOBS, Objective


class ObjectiveTest(unittest.TestCase):
    def test_keys(self):
        g = Objective('gates', depth_cap=9)
        self.assertLess(g.key(88, 12), g.key(89, 5))
        self.assertLess(g.key(88, 5), g.key(88, 6))
        d = Objective('depth_then_gates')
        self.assertLess(d.key(120, 5), d.key(88, 6))
        self.assertLess(d.key(119, 5), d.key(120, 5))

    def test_feasible_and_search_cap(self):
        o = Objective('gates', depth_cap=7, gate_limit=100, soft_depth_slack=2)
        self.assertTrue(o.feasible(100, 7))
        self.assertFalse(o.feasible(100, 8))
        self.assertFalse(o.feasible(101, 7))
        self.assertEqual(o.search_cap, 9)
        self.assertIsNone(Objective('gates', soft_depth_slack=3).search_cap)
        self.assertTrue(Objective().feasible(10 ** 6, 10 ** 3))

    def test_validation(self):
        for bad in (dict(kind='size'), dict(depth_cap=-1), dict(gate_limit=1.5),
                    dict(soft_depth_slack=-1)):
            with self.assertRaises(ValueError):
                Objective(**bad)

    def test_settings_defaults(self):
        s = for_sections(KNOBS)
        o = Objective.from_settings(s)
        self.assertEqual((o.kind, o.depth_cap, o.gate_limit, o.soft_depth_slack),
                         ('gates', None, None, 1))
        s = for_sections(KNOBS, overrides={'objective': {'kind': 'depth_then_gates',
                                                         'depth_cap': 5}})
        o = Objective.from_settings(s)
        self.assertEqual((o.soft_depth_slack, o.search_cap), (0, 5))
        s = for_sections(KNOBS, overrides={'objective.depth_cap': 9,
                                           'objective.soft_depth_slack': 3})
        self.assertEqual(Objective.from_settings(s).search_cap, 12)
        o = Objective.from_settings(for_sections(KNOBS), depth_cap=4)
        self.assertEqual(o.search_cap, 5)
        with self.assertRaises(ValueError):
            for_sections(KNOBS, overrides={'objective.kind': 'size'})


if __name__ == '__main__':
    unittest.main()
