"""c3_p2.py: recheck of prediction P2. Collect every 90-gate depth-4 MixColumns state on disk whose
level-1 set is the 89's 26-pair set up to byte rotation (records from c1 + 'best' events of the pinned
completion jsonl files), rotate into L0's frame, and test: (a) is it in B1 = one expand-envelope (+1) step
from an L0 member (pes_lib env_outcomes at search cap 4); (b) does pes_lib remove1 at cap 4 give a down move
(into L0?); (c) bounded BFS over non-increasing remove1 moves (limit 3000) reaching <= 89 / L0.
Output c3.out, c3_result.json. nice -n 10 python3 -I c3_p2.py
"""
import glob, json, os, sys, time
from collections import Counter, deque
HOME = os.path.expanduser("~")
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{HOME}/xs-campaigns/2026-11-05-exit/pes")
from pes_lib import make_space, fan, env_outcomes  # noqa: E402
sys.path.insert(0, OUT)
from c1_census import least_levels, rot, TSET, ISET, canon  # noqa: E402

D = json.load(open(f"{OUT}/c1_states_89.json"))
L1_89 = frozenset(D["L1_89"])
ROTS = [frozenset(rot(v, s) for v in L1_89) for s in (0, 8, 16, 24)]
L0 = None

def helpers_of_values(vals):
    vs = set(vals) - ISET
    if not TSET <= vs:
        return None
    return frozenset(vs - TSET)

def main():
    global L0
    try:
        os.nice(10)
    except OSError:
        pass
    t0 = time.time()
    sp = make_space("mc", 4)
    # L0 from the repo state (closure, as in c2)
    S0 = frozenset(D["repo_helpers"])
    seen = {S0}; q = deque([S0])
    while q:
        S = q.popleft()
        for R, A, hk, dd in fan(sp, S)[2]:
            K = frozenset(hk)
            if K not in seen:
                seen.add(K); q.append(K)
    L0 = seen
    print("L0 size", len(L0), flush=True)
    # closure vs records, classified by first layer relative to the repo's L1 (c1's rotclass was the canonicalising shift, not this)
    rec_same = {frozenset(r["helpers"]) for r in D["states"] if frozenset(r["L1"]) == L1_89}
    rec_other = {frozenset(r["helpers"]) for r in D["states"]} - rec_same
    rot_other = Counter()
    for h in rec_other:
        for s in (8, 16, 24):
            if frozenset(rot(v, (32 - s) % 32) for v in h) in L0:
                rot_other[s] += 1
    print(f"record states with the repo's L1: {len(rec_same)}; L0 == that set: {L0 == rec_same}; other record states: {len(rec_other)}, "
          f"of which a byte-rotation of an L0 member: {dict(rot_other)} (total {sum(rot_other.values())})", flush=True)
    json.dump({"L0": [sorted(S) for S in L0], "L0_equals_records_with_repo_L1": L0 == rec_same, "rotated_records_in_rot_L0": dict(rot_other)},
              open(f"{OUT}/c3_L0.json", "w"))
    # ---- candidates
    cands = {}  # helper set in L0 frame -> list of sources
    def consider(h, src):
        if h is None or len(h) + 32 != 90:
            return
        lev, un = least_levels(set(h) | TSET)
        if un or max(lev.values()) != 4:
            return
        L1 = frozenset(v for v in h if lev[v] == 1)
        if L1 not in ROTS:
            return
        s = ROTS.index(L1) * 8
        hr = frozenset(rot(v, (32 - s) % 32) for v in h)  # rotate back into L0's frame
        assert frozenset(v for v in hr if bin(v).count("1") == 2) == L1_89
        cands.setdefault(hr, []).append((src, s))
    # records
    n90 = 0
    for r in json.load(open(f"{OUT}/c1_states_90.json"))["states"]:
        n90 += 1
        consider(frozenset(r["helpers"]), "record:" + r["file"])
    print("record 90@4 states checked:", n90, " with the 89's L1 (any rotation):", len(cands), flush=True)
    # pinned completion outputs: jsonl 'best' events with g 90 d 4 and values
    files = glob.glob(f"{HOME}/xs-campaigns/2026-11-02-why/foundations/out/*.jsonl")
    for d in ("2026-11-03-12h/foundation/run/runs", "2026-11-04-12h/foundation2/run/runs", "2026-11-03-waits/repair/run/runs"):
        files += glob.glob(f"{HOME}/xs-campaigns/{d}/*.jsonl")
    nev = 0; nfiles = 0; sources = Counter()
    for f in files:
        nfiles += 1
        try:
            fh = open(f)
        except Exception:
            continue
        for line in fh:
            if '"values"' not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            vals = r.get("values")
            g = r.get("g", r.get("gates")); dd = r.get("d", r.get("depth"))
            if not vals or g != 90 or dd != 4:
                continue
            nev += 1
            before = len(cands)
            consider(helpers_of_values(vals), f.replace(HOME, "~"))
            if len(cands) > before:
                sources[f.split("xs-campaigns/")[1].split("/")[0]] += 1
    print(f"jsonl files scanned {nfiles}, 90@4 'values' events {nev}; distinct candidate states with the 89's L1: {len(cands)} (new ones by campaign {dict(sources)})", flush=True)
    for h, srcs in cands.items():
        print("   candidate:", len(srcs), "events, e.g.", srcs[0][0], "rotation", srcs[0][1], " core overlap with L0 intersection:",
              len(h & frozenset.intersection(*L0)))
    # ---- B1: envelope +1 outcomes from all L0 members
    t1 = time.time(); B1 = set(); dgh = Counter()
    for S in L0:
        for hk, dg, dep, _ in env_outcomes(sp, S):
            dgh[dg] += 1
            if dg == 1:
                B1.add(frozenset(hk))
    print(f"B1 (one envelope step, dgates +1, from the {len(L0)} L0 members): {len(B1)} distinct states; envelope dgates histogram {dict(dgh)} ({time.time()-t1:.0f}s)", flush=True)
    # ---- tests per candidate
    rows = []
    for h, srcs in cands.items():
        g, d, neutral, downs, binds = fan(sp, h)
        down_into_L0 = sum(1 for hk, dg, dep in downs if frozenset(hk) in L0)
        # bounded BFS over non-increasing R1 moves
        seen = {h}; q = deque([h]); exp = 0; hit = None; best = g
        while q and exp < 3000:
            S = q.popleft(); gg, dd, neu, dn, b = fan(sp, S); exp += 1
            for hk, dg, dep in dn:
                K = frozenset(hk)
                best = min(best, gg + dg)
                hit = ("L0" if K in L0 else f"{gg+dg}g"); q.clear(); break
            if hit:
                break
            for R, A, hk, dep in neu:
                K = frozenset(hk)
                if K not in seen:
                    seen.add(K); q.append(K)
        row = {"gates": g, "depth": d, "in_B1": h in B1, "neutral": len(neutral), "downs": len(downs), "downs_into_L0": down_into_L0,
               "bfs_expanded": exp, "bfs_seen": len(seen), "bfs_exhausted": not q and hit is None, "bfs_hit": hit, "sources": len(srcs), "example": srcs[0][0]}
        rows.append(row)
        print("  ", {k: v for k, v in row.items() if k != "example"}, flush=True)
    print("summary: candidates", len(rows), " in B1:", sum(r["in_B1"] for r in rows), " with any R1 down:", sum(r["downs"] > 0 for r in rows),
          " BFS reached <=89:", sum(1 for r in rows if r["bfs_hit"]), " BFS exhausted without exit:", sum(r["bfs_exhausted"] for r in rows))
    # also: how many of B1 states carry the 89's L1 exactly (sanity on what '+1 band' means)
    json.dump({"B1_size": len(B1), "candidates": rows}, open(f"{OUT}/c3_result.json", "w"), indent=1)
    print("total", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
