#!/usr/bin/env python3
"""controls_q3.py -- the controls of PILOT_BRIEF.md section 3, run against verify_q3 (the rule checker) and enum_q3.

Positive: (P1) real circuits: the label configuration of every phase of the 13 package controls and the 303 real circuits
(4 orbit steps each; extraction as qhub/qh_circ.py) must pass R1-R7 (R8 is not applicable: G != 75), and so must every
sub-configuration keeping any 3 of its labels (hereditary, PILOT_SPEC.md 3.8).  (P2) the independent two-hub witnesses of
../scope/share_pairs.json (hub-only sharing) must pass.  (P3) the realizable limit-hub pairs sharing a full helper at
different labels (Addendum D.3, qjointcheck's jc_j1_Mt.json examples) must pass.  (P4) R8 accepts the (r,u) counts of an
integer solution of leaves_int.json for its leaf.
Negative: (N1) finite fact J1: every pair of limit configurations sharing a hub-only label (J1b) or a full-met label (J1a)
must be rejected by R7 (counts reproduced: 208,272 / 14,816 for M^T).  (N2) a helper carrying a label twice -> R2.
(N3) two hubs sharing two labels -> R5.  (N4) 4 - r full helpers at one hub (H2) -> R7, for every limit configuration
extended by one more full value of N(h).  (N5) counts violating a row -> R8.
Brute force: (BF) the smallest sub-case, two (2,2) hubs sharing one label and nothing else: naive_q3.py enumerates all
realizations by nested loops over the whole domain and checks R7 only at the end; enum_q3's Realizer (with and without the
rotation reduction) must produce exactly the same set of canonical configurations.
usage: python3 controls_q3.py [--nreal N] [--skip-bf]
"""
import sys, json, time, glob, itertools, argparse
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geo_q3, verify_q3 as V, enum_q3 as E  # noqa: E402
SPRINT = Path.home() / "xs-campaigns/2026-11-07-sprint"
sys.path.insert(0, str(SPRINT / "lb76/pkg_copy/source/lower_bounds/checks"))
sys.path.insert(0, str(SPRINT / "bridge"))

OUT = {}


def obj_from_parts(geo, labels, helpers):
    """labels: list of (value, status); helpers: list of (mask, r, triples, label indices)."""
    return dict(ori=geo.ori, labels=[dict(value=v, status=s) for v, s in labels],
                helpers=[dict(mask=h, r=r, triples=list(T), labels=list(L)) for h, r, T, L in helpers])


def statuses(helpers, nlab):
    st = []
    for j in range(nlab):
        at_full = any(j in L and r == 3 for h, r, T, L in helpers)
        anch = any(j in L and r >= 1 for h, r, T, L in helpers)
        st.append("F" if at_full else ("B" if anch else "D"))
    return st


# ------------------------------------------------------------------------------------------- P1: real circuits
def phase_object(C, I, geo):
    B = I["B"]; H = set(I["H"])
    edges = []
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e))
    bb = {}
    for p, q_, e in edges:
        if p in B and q_ in B: bb[e] = (p, q_)
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    missing = [e for e in evens if e not in bb]
    midx = {e: j for j, e in enumerate(missing)}
    hedges = defaultdict(list)
    for p, q_, e in edges:
        for v in (p, q_):
            if v in H: hedges[v].append((q_ if v == p else p, e))
    helpers = []
    for v in sorted(H):
        T = []; L = []
        for o, e in hedges[v]:
            if o in B and e in bb:
                b1, b2 = bb[e]
                T.append((1 << geo.Bidx[C.mask[o]]) | (1 << geo.Bidx[C.mask[b1]]) | (1 << geo.Bidx[C.mask[b2]]))
            elif o in B: L.append(midx[e])
        if L: helpers.append((C.mask[v], len(T), T, sorted(L)))
    labels = [(C.mask[e], s) for e, s in zip(missing, statuses(helpers, len(missing)))]
    return obj_from_parts(geo, labels, helpers)


def restrict(obj, keep):
    """sub-object keeping the labels with indices in `keep` (hereditary control)."""
    idx = {j: n for n, j in enumerate(keep)}
    hs = []
    for hp in obj["helpers"]:
        L = [idx[j] for j in hp["labels"] if j in idx]
        if L: hs.append((hp["mask"], hp["r"], hp["triples"], L))
    labs = [(obj["labels"][j]["value"], s) for j, s in zip(keep, statuses(hs, len(keep)))]
    return dict(ori=obj["ori"], labels=[dict(value=v, status=s) for v, s in labs], helpers=[dict(mask=h, r=r, triples=T, labels=L) for h, r, T, L in hs])


def control_real(geos, nreal):
    from stress import Circuit
    from profile_real import reconstruct
    t0 = time.time(); phases = 0; fails = Counter(); subs = 0; subfails = Counter(); helpers = 0; qs = Counter(); As = Counter()
    gates_list = []
    for fn in sorted(glob.glob(str(SPRINT / "lb76/pkg_copy/source/circuits/*.json"))):
        dd = json.load(open(fn)); gates_list.append(("ctrl:" + Path(fn).name, dd["gates"] if isinstance(dd, dict) else dd))
    d = json.load(open(SPRINT / "bridge/profiles.json"))
    for r in [r for r in d["results"] if "error" not in r][:nreal]:
        gates, order, info = reconstruct(r["values"], "ymax", 0, True); gates_list.append((r["tag"], gates))
    for tag, gates in gates_list:
        C = Circuit(gates, "M")
        for step in range(4):
            I = C.analyse(); geo = geos[C.ori]
            obj = phase_object(C, I, geo); phases += 1; helpers += len(obj["helpers"]); qs[len(obj["labels"])] += 1
            As[sum(1 for l in obj["labels"] if l["status"] == "F")] += 1
            rep = V.verify(obj, geo, lp_check=False)
            for k, v in rep.items():
                if k != "all" and not v[0]: fails[k] += 1
            for keep in itertools.combinations(range(len(obj["labels"])), 3):
                sub = restrict(obj, list(keep)); subs += 1
                rep2 = V.verify(sub, geo, lp_check=False)
                for k, v in rep2.items():
                    if k != "all" and not v[0]: subfails[k] += 1
            if step < 3: C, _ = C.canonical_transpose(I)
    res = dict(circuits=len(gates_list), phases=phases, helpers_with_u=helpers, q_hist=dict(qs), A_hist=dict(As), rule_failures=dict(fails),
               sub_configurations=subs, sub_failures=dict(subfails), passed=(not fails and not subfails), seconds=round(time.time() - t0))
    print("P1 real circuits:", res, flush=True)
    return res


# ------------------------------------------------------------------------------------------- P2, P3: synthetic positives
def control_share_pairs(geo):
    d = json.load(open(HERE.parent / "scope/share_pairs.json"))["Mt"]
    n = 0; ok = 0; detail = {}
    for cls, v in d.items():
        if not cls.startswith("("): continue
        for h, hp, R, Rp, P in v["witnesses"]:
            bits = [k for k in range(64) if P >> k & 1]; assert len(bits) == 2
            for b in (geo.B[bits[0]], geo.B[bits[1]]):
                l = h ^ b
                assert (hp ^ l) in geo.Bset
                helpers = [(h, len(R), R, [0]), (hp, len(Rp), Rp, [0])]
                obj = obj_from_parts(geo, [(l, "B")], helpers)
                rep = V.verify(obj, geo, lp_check=False); n += 1; ok += rep["all"][0]
                detail.setdefault(cls, []).append(rep["all"][0])
    res = dict(tested=n, accepted=ok, passed=(n == ok)); print("P2 share_pairs witnesses:", res, flush=True); return res


def limit_pair_object(geo, c1, c2, shared=None):
    """two limit configurations (h, R, S); full helpers S1 u S2; labels one per (hub, f) with the hub's end chosen as the
    smaller element of the pair unless `shared` says which (for J1a the common element c, for J1b the hub-only label)."""
    labels = []; lab_idx = {}; helpers = []
    hubs = [c1, c2]
    hub_labels = [[], []]; full_labels = defaultdict(list)
    for k, (h, R, S) in enumerate(hubs):
        for f in S:
            P = geo.PM[h ^ f]; bits = [geo.B[i] for i in range(64) if P >> i & 1]
            if shared and shared[0] == "J1a" and f == shared[1]:
                c = shared[2]; b = bits[0] if bits[1] == c else bits[1]
            else:
                b = min(bits)
            l = h ^ b
            assert (f ^ l) in geo.Bset
            if l not in lab_idx: lab_idx[l] = len(labels); labels.append((l, "F"))
            hub_labels[k].append(lab_idx[l]); full_labels[f].append(lab_idx[l])
    if shared and shared[0] == "J1b":
        l = shared[1]
        if l not in lab_idx: lab_idx[l] = len(labels); labels.append((l, "B"))
        hub_labels[0].append(lab_idx[l]); hub_labels[1].append(lab_idx[l])
    for k, (h, R, S) in enumerate(hubs):
        helpers.append((h, len(R), list(R), sorted(set(hub_labels[k]))))
    for f, L in full_labels.items():
        helpers.append((f, 3, list(geo.trip[f]), sorted(set(L))))
    return obj_from_parts(geo, labels, helpers)


def control_limit_pairs(geo):
    """P3 (realizable different-label pairs from jc_j1_Mt.json) and N1 (J1a / J1b over all limit configurations)."""
    t0 = time.time()
    lim, h2viol = geo.limit_configs()
    allc = [c for r in (0, 1, 2) for c in lim[r]]
    res = dict(limit_configs={r: len(lim[r]) for r in lim}, h2_violations=h2viol)
    # P3
    ex = json.load(open(SPRINT / "qjointcheck/jc_j1_Mt.json"))["examples_diff"]
    p3 = []
    for cls, e in ex.items():
        c1 = (int(e["c1"]["h"], 16), tuple(int(x, 16) for x in e["c1"]["R"]), tuple(int(x, 16) for x in e["c1"]["S"]))
        c2 = (int(e["c2"]["h"], 16), tuple(int(x, 16) for x in e["c2"]["R"]), tuple(int(x, 16) for x in e["c2"]["S"]))
        obj = limit_pair_object(geo, c1, c2)
        rep = V.verify(obj, geo, lp_check=False)
        p3.append([cls, rep["all"][0], len(obj["labels"]), {k: v[0] for k, v in rep.items()}])
    res["P3_examples"] = p3; res["P3_passed"] = all(x[1] for x in p3)
    print("P3 limit pairs at different labels:", p3, flush=True)
    # N1 (J1b): pairs with h1 + h2 a pair value, shared hub-only label
    nb = 0; rej_b = 0; r7_b = 0
    for c1, c2 in itertools.combinations(allc, 2):
        h1, R1, S1 = c1; h2, R2, S2 = c2
        if h1 == h2 or (h1 ^ h2) not in geo.PM: continue
        nb += 1
        P = geo.PM[h1 ^ h2]; bits = [geo.B[i] for i in range(64) if P >> i & 1]
        l = h1 ^ bits[0]
        obj = limit_pair_object(geo, c1, c2, shared=("J1b", l))
        rep = V.verify(obj, geo, lp_check=False)
        rej_b += (not rep["all"][0]); r7_b += (not rep["R7"][0])
    # N1 (J1a): pairs sharing f with intersecting pairs (counted per common f)
    na = 0; rej_a = 0; r7_a = 0
    byf = defaultdict(list)
    for i, c in enumerate(allc):
        for f in c[2]: byf[f].append(i)
    for f, lst in byf.items():
        for i, j in itertools.combinations(lst, 2):
            c1 = allc[i]; c2 = allc[j]
            if c1[0] == c2[0]: continue
            inter = geo.PM[c1[0] ^ f] & geo.PM[c2[0] ^ f]
            if not inter: continue
            na += 1
            c = geo.B[[k for k in range(64) if inter >> k & 1][0]]
            obj = limit_pair_object(geo, c1, c2, shared=("J1a", f, c))
            rep = V.verify(obj, geo, lp_check=False)
            rej_a += (not rep["all"][0]); r7_a += (not rep["R7"][0])
    res.update(J1b_pairs=nb, J1b_rejected=rej_b, J1b_rejected_by_R7=r7_b, J1a_pairs=na, J1a_rejected=rej_a, J1a_rejected_by_R7=r7_a,
               N1_passed=(nb == 208272 and na == 14816 and r7_b == nb and r7_a == na), seconds=round(time.time() - t0))
    print("N1 J1:", {k: v for k, v in res.items() if k.startswith("J1") or k == "N1_passed"}, f"{res['seconds']}s", flush=True)
    # N4: H2 -- every limit configuration extended by one more full value of N(h) must be rejected by R7
    n4 = 0; rej4 = 0
    for h, R, S in allc:
        for f in geo.N[h]:
            if f in S: continue
            n4 += 1
            helpers = []; labels = []
            S2 = tuple(S) + (f,)
            for ff in S2:
                P = geo.PM[h ^ ff]; b = min(geo.B[i] for i in range(64) if P >> i & 1)
                labels.append((h ^ b, "F"))
            helpers.append((h, len(R), list(R), list(range(len(S2)))))
            for j, ff in enumerate(S2): helpers.append((ff, 3, list(geo.trip[ff]), [j]))
            rep = V.verify(obj_from_parts(geo, labels, helpers), geo, lp_check=False)
            rej4 += (not rep["R7"][0])
    res.update(N4_tested=n4, N4_rejected_by_R7=rej4, N4_passed=(n4 == rej4))
    print("N4 H2 (4 - r full helpers at a limit hub):", n4, "tested,", rej4, "rejected by R7", flush=True)
    return res


# ------------------------------------------------------------------------------------------- N2, N3, N5, P4
def control_small(geo):
    res = {}
    d = json.load(open(HERE.parent / "scope/share_pairs.json"))["Mt"]["(2, 2)"]["witnesses"][0]
    h, hp, R, Rp, P = d
    bits = [geo.B[k] for k in range(64) if P >> k & 1]; l = h ^ bits[0]
    # N2: a helper carrying a label twice
    obj = obj_from_parts(geo, [(l, "B")], [(h, 2, R, [0, 0]), (hp, 2, Rp, [0])])
    rep = V.verify(obj, geo, lp_check=False); res["N2_label_twice"] = dict(R2=rep["R2"][0], all=rep["all"][0], passed=not rep["R2"][0])
    # N3: two hubs sharing two labels: l and l' = h ^ b' = hp ^ b'' needs h + hp = b' + b'' -> same pair -> l' = h ^ bits[1]
    l2 = h ^ bits[1]; assert (hp ^ l2) in geo.Bset
    obj = obj_from_parts(geo, [(l, "B"), (l2, "B")], [(h, 2, R, [0, 1]), (hp, 2, Rp, [0, 1])])
    rep = V.verify(obj, geo, lp_check=False); res["N3_two_shared_labels"] = dict(R5=rep["R5"][0], R7=rep["R7"][0], passed=not rep["R5"][0])
    # N5 / P4: R8 on count vectors
    key = (15, 1, 0, "Mt", 3, 3); lp = E.LeafLP(key, 0, 0)
    bad = lp.feasible({(3, 1): 1}, True)                     # a full-met label in the case A = 0
    bad2 = lp.feasible({(2, 1): 8}, False)                   # W >= 16 at eight labels... (L5)/(L7)/(L9) etc.
    li = json.load(open(HERE.parent / "scope/leaves_int.json"))
    good = None
    for lf in li["leaves"]:
        if tuple(lf["key"]) == key and lf["A"] == 0 and lf["qD"] == 0 and lf["distinct_solutions"]:
            sol = lf["distinct_solutions"][0]
            counts = Counter()
            for lab, n in sol.items():
                if lab.startswith("("):
                    r, u, v = eval(lab)
                    if u >= 1: counts[(r, u)] += n
            good = (dict(counts), lp.feasible(dict(counts), True))
    res["N5_counts_violating_rows"] = dict(full_met_label_in_A0=bad, eight_r2_u1=bad2, passed=(not bad))
    ms = V.milp_status(key, 0, 0, good[0])
    res["P4_integer_solution_counts_accepted"] = dict(counts={str(k): v for k, v in good[0].items()}, accepted_LP=good[1], milp_status=ms["status"], milp_cls=ms["cls"],
                                                      passed=(good[1] and ms["cls"] == "feasible"))
    print("N2/N3/N5/P4:", res, flush=True)
    return res


# ------------------------------------------------------------------------------------------- BF: brute force
def canon(obj_helpers, labvals):
    """canonical form of a configuration: frozenset of (mask, frozenset(triples), frozenset(label values))."""
    return frozenset((h, frozenset(R), frozenset(labvals[s] for s in L)) for h, R, L in obj_helpers)


def control_bruteforce(geo):
    import naive_q3
    t0 = time.time()
    cache = HERE / "naive_two22.json"
    if cache.exists():
        naive = {frozenset((h, frozenset(R), frozenset(L)) for h, R, L in cfg) for cfg in json.load(open(cache))}
        print("naive set loaded from cache:", len(naive), flush=True)
    else:
        naive = naive_q3.enumerate_two_22(geo)
        json.dump([[[h, sorted(R), sorted(L)] for h, R, L in cfg] for cfg in naive], open(cache, "w"))
    t1 = time.time()
    skel = dict(roles=[[2, [0, 1]], [2, [0, 2]]], status=["B", "B", "B"], W=[4, 2, 2], counts={"2,2": 2})
    out = {}
    for sym in (False, True):
        pl = E.plan(skel, sym_first_root=sym)
        R = E.Realizer(geo, pl, pl["order"], max_store=10 ** 8, max_survivors=None); R.run()
        forms = set()
        for snap in R.survivors:
            hs = [(h, tuple(Rr), tuple(pl["roles"][i][1])) for h, Rr, ends, i in snap["helpers"]]
            labs = snap["labels"]
            if sym:
                for j in range(4):
                    labs_j = [geo_q3.rot(l) if l is not None else None for l in labs]
                    hs_j = [(geo_q3.rot(h), tuple(rot_triple(geo, T) for T in Rr), L) for h, Rr, L in hs]
                    forms.add(canon(hs_j, labs_j))
                    labs = labs_j; hs = hs_j
            else:
                forms.add(canon(hs, labs))
        out["sym" if sym else "nosym"] = dict(survivor_nodes=R.stats["survivors"], distinct=len(forms), stats=dict(R.stats), equal_to_naive=(forms == naive))
        if forms != naive:
            out["sym" if sym else "nosym"]["only_naive"] = len(naive - forms); out["sym" if sym else "nosym"]["only_pruned"] = len(forms - naive)
    out["naive_distinct"] = len(naive); out["naive_seconds"] = round(t1 - t0); out["pruned_seconds"] = round(time.time() - t1)
    out["passed"] = out["sym"]["equal_to_naive"] and out["nosym"]["equal_to_naive"]
    print("BF brute force:", out, flush=True)
    return out


def rot_triple(geo, T):
    bits = [k for k in range(64) if T >> k & 1]
    return sum(1 << geo.Bidx[geo_q3.rot(geo.B[k])] for k in bits)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--nreal", type=int, default=10 ** 9); ap.add_argument("--skip-bf", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    t0 = time.time()
    geos = {"M": geo_q3.GeoQ("M"), "Mt": geo_q3.GeoQ("Mt")}; geo = geos["Mt"]
    E.GEO = geo; E.build_geo()
    which = set(args.only.split(",")) if args.only else {"small", "share", "limit", "real", "bf"}
    if "small" in which: OUT["small"] = control_small(geo)
    if "share" in which: OUT["P2_share_pairs"] = control_share_pairs(geo)
    if "limit" in which: OUT["limit_pairs"] = control_limit_pairs(geo)
    if "real" in which: OUT["P1_real_circuits"] = control_real(geos, args.nreal)
    if "bf" in which and not args.skip_bf: OUT["BF"] = control_bruteforce(geo)
    OUT["seconds"] = round(time.time() - t0)
    json.dump(OUT, open(HERE / ("controls_%s.json" % (args.only.replace(",", "_") or "all")), "w"), indent=1)
    print("controls done", OUT["seconds"], "s")
