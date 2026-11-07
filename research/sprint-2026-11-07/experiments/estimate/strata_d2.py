#!/usr/bin/env python3
"""Assumption-light bound: inverse-Simpson D2 by size stratum (exact catalogue, cross-chain pairs).
N >= D2 for any landing distribution (Hill numbers are ordered), so the lower Poisson limit on
D2 is a lower bound on N that needs only independent chains."""
import json, collections, os, sys
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
sys.path.insert(0, EST)
from estimate_lib import d2
L = json.load(open(EST + "/landings.json"))
for nm, f in (("all product", lambda s: True), ("size<1e5", lambda s: s < 1e5), ("size>=1e5", lambda s: s >= 1e5)):
    inc = {r["key"]: {c for c in r["chain_ids"]} for r in L["rows"] if r["kind"] == "product" and f(r["size"])}
    pc = collections.Counter(c for v in inc.values() for c in v)
    D, lo, hi, pairs, coin = d2(inc, pc)
    print(f"{nm:12s}: plateaus {len(inc)}, cross-chain incidence pairs {pairs:,.0f}, coincidences {coin}, "
          f"D2 = {D:.0f}, 95% CI [{lo:.0f}, {hi:.0f}]")
