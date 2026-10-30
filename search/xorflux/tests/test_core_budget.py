"""``core.budget``: work limits, gated clock and stop-flag polls, child budgets."""
import time
import unittest

from xorflux.core.budget import Budget


class BudgetTest(unittest.TestCase):
    def test_work_limit(self):
        b = Budget(3)
        self.assertTrue(b.tick())
        self.assertTrue(b.tick())
        self.assertFalse(b.tick())          # the tick that reaches the limit reports it
        self.assertTrue(b.exhausted())
        self.assertTrue(Budget(0).exhausted())
        self.assertFalse(Budget(None).exhausted())

    def test_polls_are_gated(self):
        calls = []
        b = Budget(None, stop=lambda: calls.append(1) or len(calls) >= 2, check_every=4)
        for _ in range(3):
            self.assertTrue(b.tick())
        self.assertEqual(calls, [])         # no poll before check_every ticks
        self.assertTrue(b.tick())           # first poll: not stopped yet
        for _ in range(3):
            b.tick()
        self.assertFalse(b.tick())          # second poll sets the flag
        self.assertTrue(b.exhausted())
        self.assertEqual(len(calls), 2)

    def test_deadline(self):
        b = Budget(None, deadline=time.monotonic() - 1.0, check_every=1)
        self.assertFalse(b.exhausted())     # the clock is only read on a poll
        self.assertFalse(b.tick())
        self.assertTrue(b.exhausted())

    def test_child(self):
        parent = Budget(10)
        parent.tick(7)
        self.assertEqual(parent.child(None).limit, 3)
        self.assertEqual(parent.child(2).limit, 2)
        self.assertEqual(parent.child(5).limit, 3)
        self.assertIsNone(Budget(None).child(None).limit)
        child = parent.child(2)
        child.tick(2)
        self.assertEqual(parent.used, 7)     # not charged automatically

    def test_child_of_expired_parent_is_expired(self):
        # Regression: an expired parent (deadline or stop flag seen) gave a fresh child that
        # ran until its own first poll.
        parent = Budget(None, stop=lambda: True, check_every=1)
        parent.tick()
        self.assertTrue(parent.exhausted())
        child = parent.child(1000)
        self.assertTrue(child.exhausted())
        self.assertFalse(child.tick())


if __name__ == '__main__':
    unittest.main()
