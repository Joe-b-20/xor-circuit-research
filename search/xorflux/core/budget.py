"""Work budgets with cheap, gated clock checks.

Moves are bounded by work units by default so a proposal replays exactly from its RNG state.
A wall-clock deadline can be added; it is checked only every ``check_every`` ticks because
``time.monotonic()`` plus a closure call was 35% of one old engine's time.
"""
from __future__ import annotations

import time

from ..config.schema import Knob, Section

KNOBS = Section("budget", "How moves and phases are bounded.", {
    "mode": Knob("work", "work: bound by work units (replayable). time: also stop at a wall-clock "
                 "deadline (not replayable).", choices=("work", "time")),
    "check_every": Knob(128, "Ticks between clock and stop-flag checks.", min=1),
})


class Budget:
    """Counts work units and answers ``exhausted()`` cheaply.

    ``limit`` is the work allowed (None = unbounded).  ``deadline`` is a ``time.monotonic()``
    value or None.  ``stop`` is an optional callable polled with the clock.
    """
    __slots__ = ("limit", "used", "deadline", "stop", "check_every", "_next_check", "_expired")

    def __init__(self, limit=None, deadline=None, stop=None, check_every=128):
        self.limit = limit
        self.used = 0
        self.deadline = deadline
        self.stop = stop
        self.check_every = check_every
        self._next_check = check_every
        self._expired = False

    def tick(self, units: int = 1) -> bool:
        """Spend ``units``; return True while the budget lasts (False once the work limit is
        reached, including by this tick, or the deadline / stop flag has been seen)."""
        self.used += units
        if self.limit is not None and self.used >= self.limit:
            return False
        if self.used >= self._next_check:
            self._next_check = self.used + self.check_every
            self._poll()
        return not self._expired

    def exhausted(self) -> bool:
        """True once the work limit has been reached or a poll saw the deadline / stop flag
        (the clock itself is only read every ``check_every`` ticks)."""
        return self._expired or (self.limit is not None and self.used >= self.limit)

    def child(self, limit) -> "Budget":
        """A sub-budget of at most ``limit`` units (None: what remains here), sharing this
        budget's deadline and stop flag.  An expired parent gives an expired child.  Work
        spent in the child is not charged here: callers ``tick(child.used)`` afterwards."""
        if self.limit is not None:
            remaining = max(0, self.limit - self.used)
            limit = remaining if limit is None else min(limit, remaining)
        sub = Budget(limit, self.deadline, self.stop, self.check_every)
        sub._expired = self._expired
        return sub

    def _poll(self):
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self._expired = True
        elif self.stop is not None and self.stop():
            self._expired = True
