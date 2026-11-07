"""c2_plateau.py: cap-4 remove1 plateau of the repo 89@4 (claims 1b and 3), with pes_lib's exact remove1
(make_space('mc', 4) -> ValueSet search cap 4, so fan() is already capped; verified in c0b) and, as an
independent cross-check, my own value-set remove1 model at cap 4 on a few members.
Output: c2.out (stdout), c2_result.json. nice -n 10 python3 -I c2_plateau.py
"""
import json, os, sys, time
from collections import Counter, deque, defaultdict
HOME = os.path.expanduser("~")
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{HOME}/xs-campaigns/2026-11-05-exit/pes")
from pes_lib import make_space, fan  # noqa: E402

N = 32
INPUTS = [1 << i for i in range(N)]
ISET = set(INPUTS)
D = json.load(open(f"{OUT}/c1_states_89.json"))
TSET = set(D["targets"])
S0 = frozenset(D["repo_helpers"])
REC81 = {frozenset(r["helpers"]) for r in D["states"] if r["rotclass"] == 0}
REC9 = {frozenset(r["helpers"]) for r in D["states"] if r["rotclass"] != 0}
res = {}

def names(v):
    return "+".join(f"x{i}" for i in range(N) if v >> i & 1)

# ---------------------------------------------------------------- own value-set model
def closed_missing(U):
    """values of U (non-inputs) with no decomposition a ^ b, a, b in U | inputs."""
    W = U | ISET
    return {v for v in U if not any((v ^ a) in W and (v ^ a) != a for a in W)}

def levels(U):
    lev = {v: 0 for v in INPUTS}
    todo = set(U)
    L = 0
    while todo:
        L += 1
        known = list(lev)
        new = [v for v in todo if any((v ^ a) in lev for a in known)]
        if not new:
            return lev, todo
        for v in new:
            lev[v] = L
        todo.difference_update(new)
    return lev, set()

def depth_ok(U, cap):
    lev, un = levels(U)
    return not un and max(lev[t] for t in TSET) <= cap

def trim(U, cap):
    """greedy one pass (ascending): drop a helper if closure and the target depth cap survive."""
    U = set(U)
    for g in sorted(U - TSET):
        V = U - {g}
        if closed_missing(V):
            continue
        if depth_ok(V, cap):
            U = V
    return frozenset(U)

def own_remove1(S, cap):
    """all single-helper removals with at most one repair value; returns dict outcome helper-set -> dgates."""
    U = set(S) | TSET
    g0 = len(U)
    out = {}
    W = U | ISET
    for h in sorted(S):
        V = U - {h}
        stuck = closed_missing(V)
        if not stuck:
            T = trim(V, cap)
            if depth_ok(T, cap):
                out[frozenset(T - TSET)] = len(T) - g0
            continue
        VW = V | ISET
        cands = None
        for s in stuck:
            c = {s ^ a for a in VW} - VW - {0}
            cands = c if cands is None else cands & c
            if not cands:
                break
        if not cands:
            continue
        for w in cands:
            if not any((w ^ a) in VW for a in VW):
                continue  # w itself not buildable
            V2 = V | {w}
            if not depth_ok(V2, cap):
                continue
            T = trim(V2, cap)
            out[frozenset(T - TSET)] = len(T) - g0
    return out

def main():
    try:
        os.nice(10)
    except OSError:
        pass
    t0 = time.time()
    sp4 = make_space("mc", 4)
    print("pes_lib space cap_real 4 -> search cap", sp4.cap, flush=True)
    # sanity: repo state is 89 gates, depth 4 in pes_lib
    g, d, neutral, downs, binds = fan(sp4, S0)
    print("repo state via pes_lib: gates", g, "depth", d, "neutral", len(neutral), "downs", len(downs), "topk binds", binds, flush=True)
    # closure at cap 4
    seen = {S0}; q = deque([S0]); per = {}; down_total = 0; dep = Counter(); expanded = 0
    while q:
        S = q.popleft()
        g, d, neutral, downs, binds = fan(sp4, S)
        assert g == 89 and d == 4, (g, d)
        expanded += 1
        per[S] = (len(neutral), len(downs), binds)
        down_total += len(downs)
        for R, A, hk, dd in neutral:
            dep[dd] += 1
            K = frozenset(hk)
            if K not in seen:
                seen.add(K); q.append(K)
        if expanded > 5000:
            print("closure exceeded 5000, stopping"); break
    L0 = set(seen)
    nm = Counter(v[0] for v in per.values())
    print(f"cap-4 closure of repo 89@4: {len(L0)} states, complete={not q}, neutral moves per state {dict(nm)}, "
          f"down moves total {down_total}, outcome depths {dict(dep)}, binds {sum(v[2] for v in per.values())}, {time.time()-t0:.0f}s", flush=True)
    print("closure == the 81 unrotated record states:", L0 == REC81, " |L0 & REC81| =", len(L0 & REC81),
          " rotated record states in L0:", len(L0 & REC9))
    res["cap4_closure"] = {"size": len(L0), "complete": not q, "neutral_per_state": dict(nm), "downs": down_total,
                           "equals_records": L0 == REC81}
    # structure: constant helpers, slots
    inter = frozenset.intersection(*L0); union = frozenset.union(*L0)
    var = union - inter
    cnt = Counter(v for S in L0 for v in var if v in S)
    print(f"constant helpers in all {len(L0)} states: {len(inter)}; variable values: {len(var)}; occurrences: {dict(Counter(cnt.values()))}")
    # slots: group variable values by mutual exclusivity (never co-occur)
    co = {v: {u for u in var if u != v and any(v in S and u in S for S in L0)} for v in var}
    slots = []; left = set(var)
    while left:
        v = min(left); slot = {v} | {u for u in left if u not in co[v] and u != v}
        # verify mutual exclusivity inside the slot
        assert all(u not in co[x] for u in slot for x in slot if u != x), "slot not mutually exclusive"
        slots.append(sorted(slot)); left -= slot
    tuples = {tuple(next(v for v in slot if v in S) for slot in slots) for S in L0}
    print("slots (mutually exclusive groups):", [len(s) for s in slots], " distinct choice tuples:", len(tuples), "of", len(L0))
    for s in slots:
        print("   slot:", [names(v) for v in s])
    # levels of the variable values
    lev, _ = levels(set(S0) | TSET)
    print("levels of variable values in repo state:", {names(v): lev.get(v) for v in var if v in S0})
    res["structure"] = {"constant": len(inter), "variable": len(var), "slot_sizes": [len(s) for s in slots], "tuples": len(tuples)}

    # cap 5 and none fans on 3 members, and bounded closures
    members = [S0] + sorted(L0 - {S0}, key=sorted)[:2]
    for cap in (5, None):
        sp = make_space("mc", cap)
        print(f"\nspace cap_real {cap} -> search cap {sp.cap}", flush=True)
        for S in members:
            g, d, neutral, downs, binds = fan(sp, S)
            print(f"  member fan: gates {g} depth {d} neutral {len(neutral)} by outcome depth {dict(Counter(x[3] for x in neutral))} downs {len(downs)} binds {binds}", flush=True)
            res.setdefault(f"fan_cap{cap}", []).append({"neutral": len(neutral), "downs": len(downs), "by_depth": dict(Counter(x[3] for x in neutral))})
        # bounded closure
        t1 = time.time(); seen = {S0}; q = deque([S0]); expanded = 0; downs_seen = 0; dh = Counter()
        while q and expanded < 400 and time.time() - t1 < 240:
            S = q.popleft(); g, d, neutral, downs, binds = fan(sp, S); expanded += 1; downs_seen += len(downs); dh[d] += 1
            for R, A, hk, dd in neutral:
                K = frozenset(hk)
                if K not in seen:
                    seen.add(K); q.append(K)
        print(f"  bounded closure at cap {cap}: reached {len(seen)} after {expanded} expansions ({time.time()-t1:.0f}s), complete={not q}, downs seen {downs_seen}, depths of expanded {dict(dh)}", flush=True)
        res[f"closure_cap{cap}"] = {"reached": len(seen), "expanded": expanded, "complete": not q, "downs": downs_seen}

    # own model cross-check on 3 members at cap 4
    print("\nown value-set remove1 model at cap 4 (all admissible single repairs, greedy trim):", flush=True)
    for S in members:
        t1 = time.time()
        own = own_remove1(S, 4)
        own_neu = {K for K, dg in own.items() if dg == 0}; own_down = {K for K, dg in own.items() if dg < 0}
        g, d, neutral, downs, binds = fan(sp4, S)
        pes_neu = {frozenset(hk) for _, _, hk, _ in neutral}
        print(f"  member: own neutral {len(own_neu)}, own down {len(own_down)}, pes_lib neutral {len(pes_neu)}; own==pes {own_neu == pes_neu}; own-pes {len(own_neu - pes_neu)} pes-own {len(pes_neu - own_neu)}; own neutral in L0: {len(own_neu & L0)}  ({time.time()-t1:.0f}s)", flush=True)
        for K in own_neu - pes_neu:
            print("     own-only neutral outcome: removed", [names(v) for v in S - K], "added", [names(v) for v in K - S], "in L0" if K in L0 else "NOT in L0")
        res.setdefault("own_model", []).append({"own_neutral": len(own_neu), "own_down": len(own_down), "pes_neutral": len(pes_neu), "equal": own_neu == pes_neu})
    json.dump(res, open(f"{OUT}/c2_result.json", "w"), indent=1)
    print("total", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
