#!/usr/bin/env python3
"""Identify the 88-gate plateaus reached by the hunt: every distinct 88 state in samples.jsonl
(and the g88 records) is compressed with the PES plateau compression (remove1-neutral closure
as core + independent factors), and plateaus are keyed modulo byte rotation.  Writes
plateaus.json (key -> first arm/worker/time, size, factor radices, members seen) and prints the
discovery curve per arm: new plateaus against 88-arrivals, in order of discovery.
Usage: plateaus.py HUNT_DIR [max_states]
"""
import glob, json, os, sys, time

HUNT = sys.argv[1]
MAXN = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
out_path = os.path.join(HUNT, "plateaus.json")
store = json.load(open(out_path)) if os.path.exists(out_path) else {"plateaus": {}, "states": {}}
P = store["plateaus"]
seen_states = store["states"]
PL = {}  # key -> Plateau object cache


def plateau_obj(key):
    if key not in PL:
        PL[key] = pes_lib.Plateau.from_json(P[key]["plateau"])
    return PL[key]


def key_of(pl):
    allv = sorted(pl.allv) if pl.kind == "product" else sorted(set().union(*pl.states))
    k = min(sp.rot(tuple(allv), s) if s else tuple(allv) for s in sp.shifts)
    return "p" + pes_lib.h64(k).to_bytes(8, "big").hex()


# pre-sprint plateaus (PES store) enter the catalogue once, so overlaps with them are detected
if not store.get("pre_loaded"):
    for f in sorted(glob.glob("/home/joebachir20/xs-campaigns/2026-11-05-exit/runs/*/mc/plateaus/P*.json")):
        d = json.load(open(f))
        if d.get("cost") != 88 or d.get("kind") != "product":
            continue
        pl = pes_lib.Plateau.from_json(d)
        key = key_of(pl)
        if key in P:
            P[key]["also_pre"] = os.path.basename(f)
            continue
        P[key] = {"plateau": pl.to_json(), "size": pl.size(), "radices": pl.radices(), "kind": pl.kind,
                  "depth": None, "first": {"arm": "pre", "worker": os.path.basename(f), "wall": 0},
                  "members_seen": 0, "arms": {}}
    store["pre_loaded"] = True

# collect 88 states: samples first (time ordered), then records
cands = []
for sp_path in (os.path.join(HUNT, "samples.jsonl"), os.path.join(HUNT, "samplesC", "samples.jsonl")):
    if os.path.exists(sp_path):
        for line in open(sp_path):
            r = json.loads(line)
            if r["gates"] == 88:
                cands.append((r["wall"], r["arm"], r["worker"], r["hash"], r["values"]))
for rec in sorted(glob.glob(os.path.join(HUNT, "runs", "*", "workers", "*", "records", "g88-*.json"))):
    parts = rec.split(os.sep)
    arm, w = parts[-5], parts[-3]
    cands.append((os.path.getmtime(rec), arm, w, os.path.basename(rec)[:20], rec))
cands.sort()
ARMS = os.environ.get("ARMS")
if ARMS:
    cands = [c for c in cands if c[1] in ARMS.split(",")]

n_new = 0
t0 = time.time()
for wall, arm, w, h, values in cands:
    if h in seen_states:
        continue
    if n_new >= MAXN:
        break
    if isinstance(values, str):
        d = json.load(open(values))
        if d.get("values"):
            values = d["values"]
        elif d.get("circuit"):
            c = d["circuit"]
            masks = [1 << i for i in range(c["inputCount"])]
            for a, b in c["gates"]:
                masks.append(masks[a] ^ masks[b])
            values = masks[c["inputCount"]:]
        else:
            seen_states[h] = None
            continue
    helpers = [v for v in values if v not in sp.tset]
    st = sp.state(helpers)
    if st.count() != 88:
        seen_states[h] = None
        continue
    hk = sp.hkey(st)
    # quick membership test against known plateaus (any rotation)
    found = None
    for s in sp.shifts:
        rk = sp.rot(hk, s) if s else hk
        S = frozenset(rk)
        for key in list(P):
            if plateau_obj(key).contains(S):
                found = key
                break
        if found:
            break
    if found is None:
        pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=3000, time_limit=180)
        if info.get("downs"):
            print("DOWN EXIT FOUND", arm, w, h, info["downs"][:3], flush=True)
            with open(os.path.join(HUNT, "DOWN_EXITS.txt"), "a") as f:
                f.write(json.dumps({"arm": arm, "worker": w, "hash": h, "downs": [str(x) for x in info["downs"]]}) + "\n")
        truncated = pl.kind != "product" and (pl.meta or {}).get("verified") == "closure-truncated"
        if truncated:
            # giant coupled plateau: identity approximated by its seed state (membership inexact)
            key = "giant-" + h
        else:
            key = key_of(pl)
        if key not in P:
            P[key] = {"plateau": pl.to_json(), "size": pl.size(), "radices": pl.radices(),
                      "kind": "giant" if truncated else pl.kind, "depth": st.depth(),
                      "first": {"arm": arm, "worker": w, "wall": wall}, "members_seen": 0, "arms": {}}
            n_new += 1
        found = key
    P[found]["members_seen"] += 1
    P[found]["arms"][arm] = P[found]["arms"].get(arm, 0) + 1
    seen_states[h] = found
    if time.time() - t0 > 3000:
        break

json.dump(store, open(out_path + ".tmp", "w"))
os.replace(out_path + ".tmp", out_path)

print(f"states seen {len(seen_states)}, plateaus {len(P)}")


def rot(v, s, n=32):
    s %= n
    return ((v << s) | (v >> (n - s))) & ((1 << n) - 1)


def rk1(v):
    return min(rot(v, s) for s in (0, 8, 16, 24))


# discovery curve: in order of first sighting, cumulative plateaus and vocabulary (mod rotation)
known_vocab = set()
import glob as _g
for f in _g.glob("/home/joebachir20/xs-campaigns/2026-11-05-exit/runs/*/mc/plateaus/P*.json"):
    d = json.load(open(f))
    if d.get("cost") != 88:
        continue
    for v in d["core"]:
        known_vocab.add(rk1(v))
    for fac in d["factors"]:
        for ch in fac["choices"]:
            for v in ch:
                known_vocab.add(rk1(v))
print(f"vocabulary of the 52 pre-sprint plateaus: {len(known_vocab)} values mod rotation")
order = sorted(((k, v) for k, v in P.items() if v["first"]["arm"] != "pre"),
               key=lambda kv: kv[1]["first"]["wall"])
pre_hits = sum(v["members_seen"] for v in P.values() if v["first"]["arm"] == "pre")
print(f"arrivals that landed on one of the pre-sprint plateaus: {pre_hits}")
vocab = set(known_vocab)
t_first = order[0][1]["first"]["wall"] if order else 0
print("  #  arm  worker   t(min)  size   radices        new words  cum words  members")
for i, (key, info) in enumerate(order, 1):
    pl = info["plateau"]
    vals = set(pl["core"])
    for fac in pl["factors"]:
        for ch in fac["choices"]:
            vals |= set(ch)
    if pl.get("states"):
        for s in pl["states"]:
            vals |= set(s)
    words = {rk1(v) for v in vals}
    new = words - vocab
    vocab |= words
    f = info["first"]
    print(f"  {i:2d}  {f['arm']}    {f['worker']}  {(f['wall'] - t_first) / 60:6.1f}  {info['size']:5d}  "
          f"{str(info['radices']):14s} {len(new):4d}      {len(vocab):5d}   {info['members_seen']}")
by_arm = {}
for key, info in P.items():
    by_arm.setdefault(info["first"]["arm"], []).append((info["first"]["wall"], key))
for arm, lst in sorted(by_arm.items()):
    lst.sort()
    print(f"  {arm}: {len(lst)} plateaus first seen here")
sizes = {}
for info in P.values():
    sizes[(info["kind"], info["size"])] = sizes.get((info["kind"], info["size"]), 0) + 1
print("  plateau sizes:", dict(sorted(sizes.items(), key=lambda kv: -kv[1])))
print("  radices:", sorted({tuple(info["radices"]) for info in P.values()}))
