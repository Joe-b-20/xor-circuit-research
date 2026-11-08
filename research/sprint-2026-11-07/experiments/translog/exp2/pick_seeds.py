#!/usr/bin/env python3
"""exp2 seeds: 4 hunt-D 88 records not used in exp1: roots and v3 signatures distinct from
exp1's six and from each other, from 4 different (arm, worker) slots, arms D4/DN/D0 round-robin.
Among each slot's eligible records the latest one is taken. Writes seeds.json."""
import glob, json, os, sys
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
import plateau_sig as ps  # noqa: E402

H = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/hunt/runsD")
HERE = os.path.dirname(os.path.abspath(__file__))
old = json.load(open(os.path.join(HERE, "..", "exp1", "seeds.json")))
used_paths = {o["path"] for o in old}
used_sigs = {o["sig"] for o in old}
used_roots = {o["root"] for o in old}


def values_of(d):
    if d.get("values"):
        return sorted(set(int(v) for v in d["values"]))
    n = d.get("inputCount", 32)
    masks = [1 << i for i in range(n)]
    for a, b in d["gates"]:
        masks.append(masks[a] ^ masks[b])
    return sorted(set(masks[n:]))


slots = {}
for arm in ("D4", "DN", "D0"):
    for w in sorted(glob.glob(f"{H}/{arm}/workers/*")):
        recs = [r for r in sorted(glob.glob(f"{w}/records/g88-*.json"), key=os.path.getmtime)
                if not r.endswith(".verification.json") and r not in used_paths]
        lst = []
        for rec in recs:
            d = json.load(open(rec))
            if "gates" not in d or not isinstance(d["gates"], list):
                continue
            meta = d.get("metadata", {})
            if meta.get("root") in used_roots:
                continue
            lst.append((rec, d, meta))
        slots[(arm, os.path.basename(w))] = lst
order = []
for i in range(4):  # worker index i, arm rotating -> 4 different workers and >= 3 arms
    for arm in ("D4", "DN", "D0", "D4", "DN", "D0")[i % 3:i % 3 + 3]:
        order.append((arm, f"free-{i:02d}"))
chosen, sigs, roots = [], set(used_sigs), set(used_roots)
for slot in order:
    if len(chosen) == 4:
        break
    if any(c["worker"] == slot[1] for c in chosen):
        continue
    for rec, d, meta in reversed(slots.get(slot, [])):
        if meta.get("root") in roots:
            continue
        values = values_of(d)
        if len(values) != 88:
            continue
        sig, info = ps.sig_of(values)
        if sig is None or sig in sigs:
            continue
        chosen.append({"path": rec, "arm": slot[0], "worker": slot[1], "root": meta.get("root"),
                       "sig": sig, "depth": d.get("depth"), "chain": meta.get("chain"),
                       "values": values})
        sigs.add(sig); roots.add(meta.get("root"))
        break
for c in chosen:
    print(c["arm"], c["worker"], c["root"], c["sig"], "depth", c["depth"], os.path.basename(c["path"]))
for i in range(len(chosen)):
    for j in range(i + 1, len(chosen)):
        a, b = set(chosen[i]["values"]), set(chosen[j]["values"])
        print("seed jaccard distance", i, j, round(1 - len(a & b) / len(a | b), 3))
for c in chosen:
    del c["values"]
assert len(chosen) == 4, len(chosen)
json.dump(chosen, open(os.path.join(HERE, "seeds.json"), "w"), indent=1)
