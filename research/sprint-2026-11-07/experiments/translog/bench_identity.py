#!/usr/bin/env python3
"""Microbenchmark of the per-row cost: identity hash (with and without rotation), a row's
json.dumps with and without values, on the 88@6 seed state.  Prints microseconds per call."""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "xs-campaigns/2026-11-07-sprint/translog/xorflux-translog"))
from xorflux.engine.translog import _identity  # noqa: E402

seed = json.load(open(Path.home() / "xs-campaigns/2026-11-07-sprint/hunt/runsD/D0/workers/free-00/"
                      "records/g88-d6-0f7bfd6b155e8d61.json"))
n = seed["inputCount"]
masks = [1 << i for i in range(n)]
for a, b in seed["gates"]:
    masks.append(masks[a] ^ masks[b])
values = sorted(set(masks[n:]))
print("values", len(values))


def bench(label, fn, reps=5000):
    fn()
    t0 = time.perf_counter()
    for _ in range(reps):
        fn()
    us = (time.perf_counter() - t0) / reps * 1e6
    print(f"{label:48s} {us:8.1f} us")
    return us


a = bench("identity, rotate 8", lambda: _identity(values, n, 8))
b = bench("identity, no rotation", lambda: _identity(values, n, 0))
row = {"k": "step", "it": 123456789, "t": 1234.567, "w": time.time(), "p": 89, "g": 88, "d": 6,
       "m": "walk.remove1", "c": 1, "id": "0123456789abcdef"}
c = bench("json.dumps row without values", lambda: json.dumps(row, separators=(",", ":")))
row["v"] = values
d = bench("json.dumps row with 88 values", lambda: json.dumps(row, separators=(",", ":")))
e = bench("sorted(frozenset of 88)", lambda: sorted(frozenset(values)))
print(f"entry row total (sorted + identity + dumps with values): {a + d + e:.1f} us")
print(f"at 12 entries/s + 12 departures/s: {(12 * (a + d + e) + 12 * c) / 1e6 * 100:.3f} % of a second")
