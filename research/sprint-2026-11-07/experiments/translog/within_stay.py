#!/usr/bin/env python3
"""Is the v3 signature constant along an 88 stay?  For each sampler 88 record of T1/free-00,
find the log's 88 segment containing its chain.json time and compare the signature of the
sampled (mid-stay) state with the signature of that stay's entry state."""
import json, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/translog")
import plateau_sig as ps  # noqa: E402

rows = [json.loads(l) for l in open("runs/T1/workers/free-00/translog.jsonl")]
body = sorted([r for r in rows if r["k"] in ("step", "chain")], key=lambda r: r["it"])
segs = []
for i, r in enumerate(body):
    nxt = body[i + 1] if i + 1 < len(body) else None
    segs.append((r["t"], nxt["t"] if nxt else 1e9, r))
recs = [json.loads(l) for l in open("samples/samples.jsonl")]
mine = [r for r in recs if r["arm"] == "T1" and r["worker"] == "free-00" and r["gates"] == 88]
same = diff = unmatched = 0
details = []
for r in mine:
    seg = next(((a, b, x) for a, b, x in segs if a <= r["t"] < b), None)
    if seg is None or seg[2]["g"] != 88:
        unmatched += 1
        continue
    e = seg[2]
    s_entry, _ = ps.sig_of(e["v"])
    s_samp, _ = ps.sig_of(r["values"])
    A, B = set(e["v"]), set(r["values"])
    details.append((round(r["t"] - seg[0], 2), round(seg[1] - seg[0], 2), len(A - B), s_entry == s_samp))
    if s_entry == s_samp:
        same += 1
    else:
        diff += 1
print(f"sampler 88 records: {len(mine)}; matched to an 88 stay: {same + diff}; unmatched (chain.json lag): {unmatched}")
print(f"signature equal to the stay's entry signature: {same}; different: {diff}")
print("(seconds into stay, stay length s, values replaced since entry, same signature):")
for d in details:
    print("  ", d)
