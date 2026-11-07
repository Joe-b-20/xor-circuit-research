#!/usr/bin/env python3
"""Print the stored hunt plateaus: key, kind, size, radices, depth, first sighting, members, and
for size-1 closures the state and whether the fan really has no neutral move."""
import json, sys

sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

HUNT = sys.argv[1] if len(sys.argv) > 1 else "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
store = json.load(open(HUNT + "/plateaus.json"))
sp = pes_lib.make_space("mc", None)
for key, info in sorted(store["plateaus"].items(), key=lambda kv: kv[1]["first"]["wall"]):
    pl = info["plateau"]
    print(key, info["kind"], info["size"], info["radices"], "depth", info["depth"], info["first"]["arm"],
          info["first"]["worker"], "members", info["members_seen"], "core", len(pl["core"]))
    if info["size"] == 1:
        S = pl["states"][0] if pl.get("states") else pl["core"]
        st = sp.state(list(S))
        g, d, neutral, downs, binds = pes_lib.fan(sp, frozenset(sp.hkey(st)))
        print("   size-1: gates", g, "depth", d, "neutral moves", len(neutral), "downs", len(downs),
              "helpers", len(sp.hkey(st)))
        print("   meta", pl.get("meta"))
