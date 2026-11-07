"""c2d_ownmodel.py: independent value-set remove1 model at depth cap 4, cross-checked against pes_lib.
Model: a state is a set of non-input values containing the 32 targets; it is admissible at cap c when every
value gets a least level <= c (inputs 0; v at level L when v = a ^ b with a, b of level < L). remove1(h): drop
helper h; the values that no longer have a level <= c are 'stuck'; a repair is ONE new value w such that the
set minus h plus w is admissible; then trim greedily (drop any helper whose removal keeps admissibility, in
ascending order). Outcome gate count = number of values. All admissible repairs are enumerated (no top_k cut,
no smallest-size preference), so the neutral set here is a superset of any engine variant that adds one value.
Run on the repo 89@4 and two other L0 members; compares with pes_lib fan at cap 4.
"""
import json, os, sys, time
from collections import Counter
HOME = os.path.expanduser("~")
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{HOME}/xs-campaigns/2026-11-05-exit/pes")
from pes_lib import make_space, fan  # noqa: E402
N = 32
INPUTS = [1 << i for i in range(N)]
ISET = set(INPUTS)
D = json.load(open(f"{OUT}/c1_states_89.json"))
TSET = set(D["targets"])
L0 = [frozenset(s) for s in json.load(open(f"{OUT}/c3_L0.json"))["L0"]] if os.path.exists(f"{OUT}/c3_L0.json") else None

def names(v):
    return "+".join(f"x{i}" for i in range(N) if v >> i & 1)

def levels_capped(U, cap):
    """least levels up to cap; returns (lev dict incl. inputs, set of values of U with no level <= cap)."""
    lev = {v: 0 for v in INPUTS}
    todo = set(U)
    for L in range(1, cap + 1):
        if not todo:
            break
        known = list(lev)
        new = [v for v in todo if any((v ^ a) in lev for a in known)]
        if not new:
            break
        for v in new:
            lev[v] = L
        todo.difference_update(new)
    return lev, todo

def trim(U, cap):
    U = set(U)
    for g in sorted(U - TSET):
        if not levels_capped(U - {g}, cap)[1]:
            U.discard(g)
    return frozenset(U)

def own_remove1(S, cap):
    U = set(S) | TSET
    g0 = len(U)
    out = {}
    stats = Counter()
    for h in sorted(S):
        V = U - {h}
        lev, stuck = levels_capped(V, cap)
        if not stuck:
            T = trim(V, cap)
            out[frozenset(T - TSET)] = len(T) - g0
            stats["free"] += 1
            continue
        stats[f"stuck={len(stuck)}"] += 1
        low = [a for a in lev if lev[a] <= cap - 1]      # a and w must both be at level <= cap-1 to give s level <= cap
        VW = V | ISET
        # the repair w directly rebuilds SOME stuck value s (s = w ^ a, a levelled); the other stuck values
        # recover transitively, so the candidate set is the UNION over stuck s, filtered by: w new, and w itself
        # buildable from two levelled values (w = b ^ c, b, c levelled <= cap-1).
        cands = set()
        for s in stuck:
            for a in low:
                w = s ^ a
                if w in VW or w == h or w == 0 or w in cands:
                    continue
                if any((w ^ b) in lev for b in low):
                    cands.add(w)
        stats["cands"] += len(cands)
        for w in cands:
            lev2, un2 = levels_capped(V | {w}, cap)
            if un2:
                stats["inadmissible"] += 1
                continue
            T = trim(V | {w}, cap)
            dg = len(T) - g0
            stats[f"dg={dg}"] += 1
            out[frozenset(T - TSET)] = dg
    return out, stats

def main():
    try:
        os.nice(10)
    except OSError:
        pass
    sp4 = make_space("mc", 4)
    S0 = frozenset(D["repo_helpers"])
    members = [S0]
    if L0:
        members += sorted(set(L0) - {S0}, key=sorted)[:2]
    res = []
    for S in members:
        t0 = time.time()
        own, stats = own_remove1(S, 4)
        own_neu = {K for K, dg in own.items() if dg == 0 and K != S}
        own_down = {K for K, dg in own.items() if dg < 0}
        g, d, neutral, downs, binds = fan(sp4, S)
        pes_neu = {frozenset(hk) for _, _, hk, _ in neutral}
        pes_down = {frozenset(hk) for hk, _, _ in downs}
        print(f"member ({'repo' if S == S0 else 'L0'}): own neutral {len(own_neu)} own down {len(own_down)} | pes_lib neutral {len(pes_neu)} down {len(pes_down)} | "
              f"own==pes (neutral) {own_neu == pes_neu}; own-pes {len(own_neu - pes_neu)}; pes-own {len(pes_neu - own_neu)}; "
              f"own neutral in L0: {len(own_neu & set(L0)) if L0 else 'n/a'}; stats {dict(stats)}; {time.time()-t0:.0f}s", flush=True)
        for K in own_neu - pes_neu:
            print("   own-only neutral: removed", [names(v) for v in S - K], "added", [names(v) for v in K - S],
                  "in L0" if (L0 and K in set(L0)) else "NOT in L0")
        for K in own_down:
            print("   own DOWN move:", [names(v) for v in S - K], "->", [names(v) for v in K - S], "gates", len(K) + 32)
        for K in own_neu & pes_neu:
            pass
        res.append({"own_neutral": len(own_neu), "own_down": len(own_down), "pes_neutral": len(pes_neu), "equal": own_neu == pes_neu,
                    "moves": [[[names(v) for v in S - K], [names(v) for v in K - S]] for K in sorted(own_neu, key=sorted)]})
    print("neutral moves of the repo state (own model):")
    for R, A in res[0]["moves"]:
        print("   -", R, "+", A)
    json.dump(res, open(f"{OUT}/c2d_result.json", "w"), indent=1)

if __name__ == "__main__":
    main()
