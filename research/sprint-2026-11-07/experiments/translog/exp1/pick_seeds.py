#!/usr/bin/env python3
"""Pick 6 hunt-D 88 records with distinct v3 plateau signatures and distinct roots (one per
hunt-D worker where possible).  Writes seeds.json: [{path, arm, worker, root, sig, depth}]."""
import glob, json, os, sys
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
import plateau_sig as ps  # noqa: E402

H = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/hunt/runsD")


def values_of(d):
    if d.get("values"):
        return sorted(set(int(v) for v in d["values"]))
    n = d.get("inputCount", 32)
    masks = [1 << i for i in range(n)]
    for a, b in d["gates"]:
        masks.append(masks[a] ^ masks[b])
    return sorted(set(masks[n:]))


cands = []
for arm in ("D0", "D4", "DN"):
    for w in sorted(glob.glob(f"{H}/{arm}/workers/*")):
        recs = sorted(glob.glob(f"{w}/records/g88-*.json"))
        recs = [r for r in recs if not r.endswith(".verification.json")]
        if not recs:
            continue
        for rec in (recs[0], recs[len(recs) // 2]):
            d = json.load(open(rec))
            if "gates" not in d or not isinstance(d["gates"], list):
                continue
            try:
                values = values_of(d)
                sig, info = ps.sig_of(values)
            except Exception as exc:  # noqa: BLE001
                print("skip", rec, exc)
                continue
            if len(values) != 88:
                continue
            meta = d.get("metadata", {})
            cands.append({"path": rec, "arm": arm, "worker": os.path.basename(w),
                          "root": meta.get("root"), "sig": sig, "depth": d.get("depth"),
                          "chain": meta.get("chain")})
print(len(cands), "candidates")
chosen, sigs, roots = [], set(), set()
for c in cands:
    if c["sig"] in sigs or c["root"] in roots or c["sig"] is None:
        continue
    chosen.append(c)
    sigs.add(c["sig"])
    roots.add(c["root"])
    if len(chosen) == 6:
        break
for c in chosen:
    print(c["arm"], c["worker"], c["root"], c["sig"], "depth", c["depth"], os.path.basename(c["path"]))
json.dump(chosen, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seeds.json"), "w"), indent=1)
