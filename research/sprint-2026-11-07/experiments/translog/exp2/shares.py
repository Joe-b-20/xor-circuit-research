#!/usr/bin/env python3
"""exp2 per-worker time shares at 88/89/>=90, longest stretch away from 88, wall span, steps."""
import glob, json, os
E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp2")
for f in sorted(glob.glob(os.path.join(E, "runs/E2/workers/*/translog.jsonl"))):
    w = os.path.basename(os.path.dirname(f))
    rows = [json.loads(l) for l in open(f)]
    body = [r for r in rows if r.get("k") in ("step", "chain")]
    op = [r for r in rows if r.get("k") == "open"]
    cl = [r for r in rows if r.get("k") == "close"]
    t_end = cl[-1]["t"] if cl else body[-1]["t"]
    share = {88: 0.0, 89: 0.0, 90: 0.0}
    away, longest, t_left = 0.0, 0.0, None
    for i, r in enumerate(body):
        t1 = body[i + 1]["t"] if i + 1 < len(body) else t_end
        g = min(max(r["g"], 88), 90)
        share[g] += t1 - r["t"]
        if r["g"] > 88 and (r.get("p") or 0) <= 88:
            t_left = r["t"]
        if r["g"] <= 88 and t_left is not None:
            longest = max(longest, r["t"] - t_left)
            t_left = None
    if t_left is not None:
        longest = max(longest, t_end - t_left)
    tot = sum(share.values())
    st = json.load(open(os.path.join(os.path.dirname(f), "status.json")))
    print(w, "t_end", round(t_end), "wall", round(cl[-1]["w"] - op[0]["w"]) if cl else None,
          "share 88/89/90+ %", [round(100 * share[k] / tot) for k in (88, 89, 90)],
          "longest away from 88 s", round(longest),
          "status", {k: st.get(k) for k in ("steps", "best", "best_gates", "best_depth", "it") if k in st})
