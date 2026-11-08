"""Why part of a coupled factor's choice is locally core: for every value v of the coupled factor's
choice at S, the minimum number of choice values that must leave together with v to reach another
listed choice of the factor (1 = v can be moved by a remove1-neutral step alone, >= 2 = v is only
movable together with other values, so the local fan does not see it).  Also: how many other choices
are at symmetric difference 2 (one-for-one swaps) from the current one.  python3 coupling.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fac, mob2
from fac import rot

CASES = [("kste:3146", "kste:43"), ("kste:2229", "kste:34"), ("kste:1557", "kste:41"),
         ("sampleA:109", "hunt:p943c008e56986b92"), ("sampleA:48", "hunt:pce9227a62d5504c7"),
         ("sampleA:781", "file:../giants/pl_p80424727ddf34e79.json"),
         ("sampleC:131", "file:../giants/pl_p55f9dc07f8b3409b.json")]
for cid, spec in CASES:
    order = mob2.load(cid)
    p = fac.load_plateau(spec)
    s, core, choices = fac.align(order, p)
    f = p["factors"][0]
    cur = set(choices[0]["choice"])
    others = [set(rot(v, s) for v in c) for c in f["choices"]]
    others = [o for o in others if o != cur]
    comp = json.load(open(os.path.join(HERE, "comp_%s.json" % cid.replace(":", "_"))))
    loc_mobile = set(comp["fan"]["mobile"])
    dist_hist = {}
    for o in others:
        d = len(cur - o)
        dist_hist[d] = dist_hist.get(d, 0) + 1
    per_v = []
    for v in sorted(cur):
        dmin = min(len(cur - o) for o in others if v not in o)
        per_v.append((v, dmin, v in loc_mobile))
    print("%s %s: radix %d, choice %d; other choices by #values leaving: %s" % (cid, spec, len(f["choices"]), len(cur), dict(sorted(dist_hist.items()))))
    for v, dmin, mob in per_v:
        print("   %08x  min values leaving with it: %d   local fan moves it: %s" % (v, dmin, mob))
    bad = [v for v, dmin, mob in per_v if (dmin == 1) != mob]
    print("   consistent (dmin == 1 <=> locally mobile): %s" % (not bad))
