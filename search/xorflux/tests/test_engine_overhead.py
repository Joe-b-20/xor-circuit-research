"""Engine per-step overhead with moves that cost (almost) nothing.

Moves run at ~100-4,000 proposals/s (250 us - 10 ms each), so the loop must add only a few
microseconds.  Two fake moves bracket the engine's paths:

* ``none``     returns None (scheduler, budget, RNG reseed, recorder and plateau bookkeeping);
* ``neutral``  returns a Proposal on a constant-score state, so every step also scores, runs the
               acceptance decision, commits, credits the scheduler and samples plateau keys.

The numbers are printed (run this module directly for a longer measurement); the assertion is
deliberately loose so a busy machine does not fail the suite.
"""
import sys
import time
import unittest

from xorflux.moves.base import Proposal
from xorflux.tests.test_engine_fakes import (
    FakeMove, FakeRecorder, make_engine, move_section, settings_for)

LIMIT_US = 60.0


class ConstState:
    """A state whose score never changes; edits are free."""

    def __init__(self, values, cap=None):
        self._key = frozenset(values)
        self.n = len(self._key)

    def ok(self):
        return True

    def size(self):
        return self.n

    def depth(self):
        return 3

    def rollback(self, journal):
        pass

    def commit(self, journal):
        pass

    def values(self):
        return list(self._key)

    def key(self):
        return self._key

    def gates(self):
        return [], []

    def check(self):
        return True


class NoneMove(FakeMove):
    def propose(self, ctx):
        return None


class NeutralMove(FakeMove):
    def propose(self, ctx):
        return Proposal(self.name, True, {"components": ["x"]}, 1)


def per_step_us(move_cls, steps, replay_seeds=True):
    settings = settings_for([move_section("m", 1.0)], {
        "engine.replay_seeds": replay_seeds, "restart.stall_seconds": 0.0,
        "restart.root_seconds": 0.0})
    eng = make_engine(settings, [move_cls(settings, "m")], seed=list(range(3, 103)),
                      recorder=FakeRecorder())
    eng._make_state = lambda values, cap: ConstState(values, cap)
    eng._set_state(ConstState(eng.state.values()))
    step = eng.step
    for _ in range(1000):                      # warm up
        step()
    t0 = time.perf_counter()
    for _ in range(steps):
        step()
    return (time.perf_counter() - t0) / steps * 1e6


def report(steps):
    rows = []
    for label, cls in (("none", NoneMove), ("neutral", NeutralMove)):
        for seeds in (True, False):
            rows.append((label, seeds, min(per_step_us(cls, steps, seeds) for _ in range(3))))
    return rows


class OverheadTest(unittest.TestCase):
    def test_per_step_overhead(self):
        rows = report(20000)
        for label, seeds, us in rows:
            print(f"\n  engine overhead, {label:7s} move, replay_seeds={seeds!s:5s}: "
                  f"{us:6.2f} us/step", end="", file=sys.stderr)
        print(file=sys.stderr)
        for _, _, us in rows:
            self.assertLess(us, LIMIT_US)


if __name__ == "__main__":
    for label, seeds, us in report(200000):
        print(f"{label:7s} replay_seeds={seeds!s:5s} {us:6.2f} us/step")
