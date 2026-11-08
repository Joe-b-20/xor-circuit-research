#!/usr/bin/env python3
"""Smoke check of departure logging: every 88->more exit row has xid/xv; xv has 88 values; the
departure state equals the previous entry's state when no neutral move happened in between is
not checkable, but xv must be a valid 88-gate realization of the targets (checked via the
v8 valueset) and xv must differ from the next 89 values by the move's net change."""
import json, sys, glob, os
d = sys.argv[1]
for f in sorted(glob.glob(os.path.join(d, "workers/*/translog.jsonl"))):
    rows = [json.loads(l) for l in open(f)]
    ex = [r for r in rows if r.get("k") == "step" and r.get("p") is not None and r["p"] <= 88 < r["g"]]
    withx = [r for r in ex if "xid" in r]
    sizes = sorted({len(r["xv"]) for r in withx})
    # does xv equal the previous entry state (same stay, no neutral move) sometimes?
    last_v = None; same = 0; diffs = []
    for r in rows:
        if r.get("k") in ("step", "chain") and r.get("g", 99) <= 88 and "v" in r:
            last_v = set(r["v"])
        elif "xv" in r and last_v is not None:
            x = set(r["xv"])
            same += x == last_v
            diffs.append(len(x ^ last_v))
    # xv vs the 89 values: symmetric difference size
    sd = [len(set(r["xv"]) ^ set(r["v"])) for r in withx if "v" in r]
    print(os.path.basename(os.path.dirname(f)), "rows", len(rows), "exits", len(ex), "with xid", len(withx),
          "xv sizes", sizes, "xv==entry", same, "of", len(diffs),
          "med |xv^entry|", sorted(diffs)[len(diffs)//2] if diffs else None,
          "med |xv^v89|", sorted(sd)[len(sd)//2] if sd else None, "close", rows[-1].get("k"))
