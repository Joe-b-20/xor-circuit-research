#!/usr/bin/env python3
"""One catalogue shard.  Takes queue items in order, claiming each with an exclusive create of
catalogue/claims/<id> (so shards never share a seed); skips ids that already have a result in any
shard file.  Per item: exact membership (4 rotations) in all known plateaus (refreshed from the pl
files other shards write), else pes_lib.compress(verify_limit 20000, closure_limit 3e5,
time_limit 900 s; 1800 s for giant seeds).  Writes one line per item to catalogue/shard_<k>.jsonl
and new plateaus to catalogue/pl/<key>.json.  Checks giants/STOP between items (a compress already
running is finished first, at most time_limit + one factor group).
Usage: cat_worker.py SHARD"""
import json, os, sys, time
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants")
import cat_lib as C  # noqa: E402
pes_lib = C.pes_lib

K = int(sys.argv[1])
VL, CL = 20000, 300000
out = os.path.join(C.CAT, f"shard_{K:02d}.jsonl")
known = C.Known()
done = set(C.done_ids())
queue = [json.loads(l) for l in open(os.path.join(C.CAT, "queue.jsonl"))]
t0 = time.time()
n = {"lookup": 0, "compress": 0, "unresolved": 0, "bad": 0}


def emit(rec):
    rec["shard"] = K
    rec["wall"] = round(time.time() - t0, 1)
    with open(out, "a") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())


for q in queue:
    if os.path.exists(C.STOP):
        print(f"shard {K}: STOP seen", flush=True)
        break
    if q["id"] in done:
        continue
    try:
        fd = os.open(os.path.join(C.CAT, "claims", q["id"]), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(K).encode())
        os.close(fd)
    except FileExistsError:
        continue
    rec = {"id": q["id"], "kind": q["kind"]}
    for f in ("entry", "arm", "worker", "t"):
        if f in q:
            rec[f] = q[f]
    hk = tuple(sorted(q["seed"])) if q["kind"] == "giant" else C.state_of_values(q["values"])
    if hk is None:
        rec.update(resolved=False, how="does not trim to 88")
        n["bad"] += 1
        emit(rec)
        continue
    known.refresh()
    k, s = known.member(hk)
    if k:
        p = known.pl[k]
        rec.update(resolved=True, how="membership", key=k, shift=s, size=p.size(), radices=p.radices(),
                   verified=(p.meta or {}).get("verified"))
        n["lookup"] += 1
        emit(rec)
        continue
    t = time.time()
    pl, info = pes_lib.compress(C.space(), hk, verify_limit=VL, closure_limit=CL, time_limit=q["time_limit"])
    downs = info.pop("downs", None) or []
    rec["info"] = {a: b for a, b in info.items() if a != "depth_hist"}
    rec["seconds"] = round(time.time() - t, 1)
    if downs:
        rec["downs"] = [str(x) for x in downs[:5]]
        with open(os.path.join(C.CAT, "DOWN_EXITS.txt"), "a") as f:
            f.write(json.dumps({"id": q["id"], "downs": rec["downs"]}) + "\n")
    v = info.get("verified")
    if pl.kind == "product" or v == "closure-complete":
        key = C.key_of(pl)
        rec.update(resolved=True, how="compress-" + str(v), key=key, size=pl.size(), radices=pl.radices(), verified=v)
        path = os.path.join(C.PLDIR, key + ".json")
        if not os.path.exists(path):
            tmp = path + f".tmp{K}"
            json.dump(pl.to_json(), open(tmp, "w"))
            os.replace(tmp, path)
        known.pl.setdefault(key, pl)
        n["compress"] += 1
    else:
        rec.update(resolved=False, how=f"{v}; {info.get('note')}", lower_bound=info.get("fans"))
        n["unresolved"] += 1
    emit(rec)
print(f"shard {K} finished in {time.time() - t0:.0f} s: {n}", flush=True)
