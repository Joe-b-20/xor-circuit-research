"""Overhead of ``Recorder.proposal`` (the only telemetry call on the hot path).

The budget is well under 2 µs per call; the test takes the best of several runs so a busy
machine does not make it flaky, and prints the measured cost.
"""
from __future__ import annotations

import tempfile
import time
import unittest

from xorsearch.telemetry.recorder import NullRecorder, Recorder

CALLS = 100_000
RUNS = 5
BUDGET_US = 2.0


def _records(n):
    moves = ("walk.remove1", "walk.expand", "lns.rebuild", "depth.repair")
    comps = (["remove1", "repair", "trim"], ["remove1", "first.unlock", "second.repair", "trim"],
             ["destroy.cone", "inject", "rebuild.deadline", "peel"],
             ["depth.repair", "inject", "rebuild.deadline", "trim"])
    out = []
    for i in range(n):
        acc = i % 5 == 0
        out.append({"it": i, "move": moves[i % 4], "accepted": acc, "neutral": acc and i % 10 == 0,
                    "d_gates": (i % 3) - 1, "d_depth": 0, "gates": 300, "depth": 9, "work": 17,
                    "components": comps[i % 4], "improved_chain": i % 997 == 0})
    return out


def per_call_us(recorder, records) -> float:
    """Best-of-RUNS microseconds per ``proposal`` call (loop overhead subtracted)."""
    proposal = recorder.proposal
    best = float("inf")
    for _ in range(RUNS):
        t = time.perf_counter()
        for r in records:
            proposal(r)
        best = min(best, time.perf_counter() - t)
    t = time.perf_counter()
    for r in records:
        pass
    loop = time.perf_counter() - t
    return max(0.0, best - loop) / len(records) * 1e6


class ProposalOverheadTest(unittest.TestCase):
    def test_proposal_under_budget(self):
        records = _records(CALLS)
        with tempfile.TemporaryDirectory() as tmp:
            r = Recorder(tmp, "bench")
            us = per_call_us(r, records)
            r.close()
        null_us = per_call_us(NullRecorder(), records)
        print(f"\nRecorder.proposal: {us:.3f} us/call; NullRecorder: {null_us:.3f} us/call")
        self.assertLess(us, BUDGET_US)
        self.assertLess(null_us, BUDGET_US)


if __name__ == "__main__":
    unittest.main()
