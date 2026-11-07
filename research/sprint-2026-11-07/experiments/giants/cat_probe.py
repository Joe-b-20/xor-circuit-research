#!/usr/bin/env python3
"""Quick membership pass on a random subset of the queued samples (no compress, writes nothing to
the shards): fraction already on a known plateau -> number of states the catalogue must compress.
Usage: cat_probe.py [n=200] [seed=1]"""
import json, random, sys, time, collections
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants")
import cat_lib as C  # noqa: E402
n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
t0 = time.time()
known = C.Known()
Q = [json.loads(l) for l in open(C.CAT + "/queue.jsonl")]
S = [q for q in Q if q["kind"] == "sample"]
pick = random.sample(S, min(n, len(S)))
c = collections.Counter()
per_arm = collections.defaultdict(collections.Counter)
tm = []
for q in pick:
    t = time.time()
    hk = C.state_of_values(q["values"])
    if hk is None:
        r = "bad"
    else:
        r = "member" if known.member(hk)[0] else "compress"
    tm.append(time.time() - t)
    c[r] += 1
    per_arm[q["arm"]][r] += 1
f = c["compress"] / len(pick)
lo = max(0.0, f - 1.96 * (f * (1 - f) / len(pick)) ** 0.5)
hi = min(1.0, f + 1.96 * (f * (1 - f) / len(pick)) ** 0.5)
print(f"known plateaus {len(known.pl)}; queued samples {len(S)}, giants {len(Q) - len(S)}; probe {len(pick)}: {dict(c)}")
print("per arm:", {a: dict(v) for a, v in per_arm.items()})
print(f"fraction needing compress {f:.3f} (95% {lo:.3f}-{hi:.3f}) -> ~{f * len(S):.0f} states ({lo * len(S):.0f}-{hi * len(S):.0f}) "
      f"before within-run lookups; lookup {sum(tm) / len(tm):.3f} s/state; total {time.time() - t0:.0f} s")
