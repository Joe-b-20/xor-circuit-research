#!/usr/bin/env python3
"""Recompute pes_lib.fan on a random 100 (or all, arg) of the 1,869 sampled 88 states; report downs,
neutral counts, and how often the TOPK repair cut binds (binds > 0 means remove1 was NOT exhaustive)."""
import json, os, sys, random, time, collections
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib
import bt_lib_copy
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
sp = pes_lib.make_space("mc", None)
print("TOPK =", bt_lib_copy.TOPK, "PEEL =", bt_lib_copy.PEEL)
states = {}
for p in ("samples.jsonl", "samplesC/samples.jsonl"):
    for line in open(os.path.join(HUNT, p)):
        r = json.loads(line)
        if r["gates"] == 88:
            states[r["hash"]] = r["values"]
print("distinct sampled 88 states:", len(states))
hs = sorted(states)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
random.seed(20261107)
pick = hs if n >= len(hs) else random.sample(hs, n)
t0 = time.time()
downs_tot = 0
binds_states = 0
neutral = collections.Counter()
kinds = collections.Counter()
for h in pick:
    helpers = [v for v in states[h] if v not in sp.tset]
    st = sp.state(helpers)
    assert st.count() == 88, st.count()
    S = frozenset(sp.hkey(st))
    g, d, neu, downs, binds = pes_lib.fan(sp, S)
    downs_tot += len(downs)
    binds_states += binds > 0
    neutral[len(neu)] += 1
    # kinds of the neutral outcomes: sure / maybe / free
    r1, _ = sp.remove1(st)
    for k, dg, hh, w, kind, dep in r1:
        kinds[kind] += 1
print(f"{len(pick)} states in {time.time() - t0:.0f} s: states with downs > 0: {downs_tot and 'YES' or 0} (total downs {downs_tot}); "
      f"states where the TOPK cut binds: {binds_states}; neutral counts: {sorted(neutral.items())}; outcome kinds: {dict(kinds)}")
