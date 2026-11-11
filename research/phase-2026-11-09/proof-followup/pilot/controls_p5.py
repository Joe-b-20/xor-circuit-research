#!/usr/bin/env python3
"""controls_p5.py -- P5, the SEARCH-level positive control: valid three-label objects that do not come from the enumerator
must be REACHED by step G of enum_q3 (run on their own skeleton, R8 and R8-int off), up to the byte rotation and the
renaming of helpers and labels.  A miss is a completeness bug.

Objects (all validated by verify_q3, rules R1-R7, before use):
  real    hereditary 3-label sub-configurations of the phases of the 13 package controls and 303 real circuits (both
          orientations; each orientation is searched with its own geometry), at most d <= 1 dark label (the enumerator's
          domain; every open leaf of the block has q_D <= 1), selected to cover as many distinct skeleton shapes as possible;
  planted (M^T) objects with full-met labels, which no real phase has (A = 0 everywhere):
          lim3   a limit hub (r = 0) with three full helpers (A = 3),
          pair   3-label sub-configurations of two limit hubs sharing a full helper at different labels (Addendum D.3),
          mixA1  a hub with one full-met label and one hub-only label shared with a second anchored hub (A = 1),
          mixA2  a limit hub (r = 1, two full-met labels) sharing a hub-only label with a second anchored hub (A = 2).
For each object: (S) its canonical skeleton must be produced by enum_q3.skeleton_enum when the LP is replaced by the
object's own counts (monotone: <=, exact: =); (G) run_skeleton on that skeleton, with the search GUIDED to the object (the
hooks only discard branches that differ from the target; every pruning rule of the search still runs on the path), must
return the object's constrained part exactly, for at least one of its four rotations (the search roots on orbit
representatives).  Free parts (Lemmas 3.9, 3.10 of PILOT_SPEC.md) are not searched by design; objects whose skeleton is free
only are counted separately and do not count towards the 500.  (U) For a sample of single-segment objects the search is
also run UNGUIDED and complete (when it finishes within the cap) and the object must be among its survivors.
usage: python3 controls_p5.py [--per-shape 6] [--unguided 80]
"""
import sys, json, time, glob, itertools, random, argparse
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geo_q3, verify_q3 as V, enum_q3 as E, controls_q3 as C  # noqa: E402
SPRINT = Path.home() / "xs-campaigns/2026-11-07-sprint"
ORDER = {"F": 0, "B": 1, "D": 2}


def make_geo(ori):
    g = geo_q3.GeoQ(ori)
    g.ge = {k: sorted(l for l, rk in g.rankC.items() if rk >= k) for k in range(1, 8)}; g.ge[0] = g.ge[1]
    g.ge_reps = {k: [l for l in g.ge[k] if g.is_rep(l)] for k in g.ge}
    return g


def skeleton_of(obj):
    """canonical skeleton (as enum_q3.canonical_skeleton) and the map label index -> slot."""
    labs = obj["labels"]; assert len(labs) == 3
    base = sorted(range(3), key=lambda j: ORDER[labs[j]["status"]])
    status = [labs[j]["status"] for j in base]
    best = None
    for p in itertools.permutations(range(3)):
        if any(status[p[s]] != status[s] for s in range(3)): continue
        slot_of = {base[s]: p[s] for s in range(3)}
        roles = tuple(sorted((hp["r"], tuple(sorted(slot_of[j] for j in hp["labels"]))) for hp in obj["helpers"]))
        if best is None or roles < best[0]: best = (roles, slot_of)
    roles, slot_of = best
    skel = dict(roles=[[r, list(L)] for r, L in roles], status=status, W=[sum(r for r, L in roles if s in L) for s in range(3)])
    return skel, slot_of


class Guide:
    def __init__(self, labels, helpers):
        self.labels = labels; self.by_mask = {h: (role, R) for role, h, R in helpers}
    def ok_root(self, s, l): return self.labels[s] == l
    def ok_label(self, s, l): return self.labels[s] == l
    def ok_mask(self, role, h): return h in self.by_mask and self.by_mask[h][0] == role
    def ok_helper(self, role, h, R): return h in self.by_mask and self.by_mask[h] == (role, frozenset(R))


def rot_triple(geo, T):
    return sum(1 << geo.Bidx[geo_q3.rot(geo.B[k])] for k in range(64) if T >> k & 1)


def rotate(geo, labels, helpers):
    return ([None if l is None else geo_q3.rot(l) for l in labels],
            [(role, geo_q3.rot(h), frozenset(rot_triple(geo, T) for T in R)) for role, h, R in helpers])


class FakeLP:
    """stands for R8 in step S: the object's own counts (monotone: <=, exact: =)."""
    def __init__(self, counts):
        self.t = {k: v for k, v in counts.items() if v}; self.ind = {(r, u): 1 for r in range(4) for u in range(1, 4)}
    def feasible(self, counts, exact):
        if exact: return {k: v for k, v in counts.items() if v} == self.t
        return all(self.t.get(k, 0) >= v for k, v in counts.items())


def features(obj, skel, pl):
    roles = pl["roles"]; f = []
    croles = [roles[e[0]] for e in pl["order"]]
    f.append("segments=%d" % len(pl["segments"]))
    if any(len(L) == 2 for r, L in croles): f.append("u2")
    if any(len(L) == 3 for r, L in croles): f.append("u3")
    if sum(1 for r, L in croles if len(L) >= 2) >= 3: f.append("triangle")
    if any(r == 0 for r, L in croles): f.append("r0_u>=2_constrained")
    if pl["riders"]: f.append("r0_u1_rider")
    if pl["free"]: f.append("free_component")
    if "D" in skel["status"]: f.append("dark_label")
    a = skel["status"].count("F")
    if a: f.append("A=%d" % a)
    if any(r == 3 and len(L) == 2 for r, L in roles): f.append("full_u2")
    for s in range(3):
        if sum(1 for r, L in croles if s in L) >= 3: f.append("label_with_>=3_carriers"); break
    if any(r == 1 for r, L in croles): f.append("r1")
    if any(r == 2 for r, L in croles): f.append("r2")
    return f


def check_object(geo, obj, unguided=False, cap=10.0):
    skel, slot_of = skeleton_of(obj)
    a = skel["status"].count("F"); d = skel["status"].count("D")
    # (S) the skeleton is produced by step S
    lp = FakeLP(dict(V.counts_of(obj)))
    sk_list, _ = E.skeleton_enum(lp, a, d)
    s_ok = any(json.dumps(sk["roles"]) == json.dumps(skel["roles"]) for sk in sk_list)   # (run 1 compared tuples with lists: every object was flagged)
    pl = E.plan(skel, sym_first_root=True)
    feats = features(obj, skel, pl)
    if not pl["order"]: return dict(kind="free_only", S=s_ok, features=feats, skel=skel)
    croles = {pl["roles"][e[0]] for e in pl["order"]}
    labels = [None] * 3
    for j, s in slot_of.items(): labels[s] = obj["labels"][j]["value"]
    helpers = [((hp["r"], tuple(sorted(slot_of[j] for j in hp["labels"]))), hp["mask"], frozenset(hp["triples"])) for hp in obj["helpers"]]
    chelp = [h for h in helpers if h[0] in croles]
    cslots = sorted({s for role, _, _ in chelp for s in role[1]})
    found = False; statuses = []; tl, th = labels, chelp
    rots = []
    for j in range(4):
        rots.append((tl, th))
        res = E.run_skeleton(geo, pl, 5, 5, None, guide=Guide(tl, th))
        statuses.append(res["status"])
        for snap in res["snaps"]:
            got = {(pl["roles"][i], h, frozenset(R)) for h, R, ends, i in snap["helpers"]}
            # a dark slot whose only constrained carriers are deferred may stay symbolic: compare the slots the search made concrete
            if got == set(th) and all(snap["labels"][s] == tl[s] for s in cslots if snap["labels"][s] is not None) and \
               all(snap["labels"][s] is not None for s in cslots):
                found = True
        if found: break
        tl, th = rotate(geo, tl, th)
    out = dict(kind="constrained", S=s_ok, G=found, features=feats, skel=skel, statuses=statuses, mode="segments" if len(pl["segments"]) > 1 else "single")
    if unguided and len(pl["segments"]) == 1:
        while len(rots) < 4:
            tl, th = rotate(geo, *rots[-1]); rots.append((tl, th))
        deadline = time.process_time() + cap
        res = E.run_skeleton(geo, pl, 200000, 200000, deadline)
        if res["status"] == "done" and res["survivors"] < 200000:
            targets = [(frozenset(th_), tuple(tl_[s] for s in cslots)) for tl_, th_ in rots]
            hit = False
            for snap in res["snaps"]:
                got = (frozenset((pl["roles"][i], h, frozenset(R)) for h, R, ends, i in snap["helpers"]), tuple(snap["labels"][s] for s in cslots))
                if got in targets: hit = True; break
            out["U"] = hit; out["U_survivors"] = res["survivors"]
        else:
            out["U"] = None; out["U_status"] = res["status"]
    return out


# ------------------------------------------------------------------------------------------------- object sources
def real_objects(geos, per_shape):
    from stress import Circuit
    from profile_real import reconstruct
    gates_list = []
    for fn in sorted(glob.glob(str(SPRINT / "lb76/pkg_copy/source/circuits/*.json"))):
        dd = json.load(open(fn)); gates_list.append(dd["gates"] if isinstance(dd, dict) else dd)
    d = json.load(open(SPRINT / "bridge/profiles.json"))
    for r in [r for r in d["results"] if "error" not in r]:
        gates, order, info = reconstruct(r["values"], "ymax", 0, True); gates_list.append(gates)
    by_shape = defaultdict(list); n_sub = 0; n_dark2 = 0
    for ci, gates in enumerate(gates_list):
        Cc = Circuit(gates, "M")
        for step in range(4):
            I = Cc.analyse(); geo = geos[Cc.ori]
            obj = C.phase_object(Cc, I, geo)
            for keep in itertools.combinations(range(len(obj["labels"])), 3):
                sub = C.restrict(obj, list(keep)); n_sub += 1
                if sum(1 for l in sub["labels"] if l["status"] == "D") >= 2: n_dark2 += 1; continue
                skel, _ = skeleton_of(sub)
                key = (Cc.ori, json.dumps(skel["roles"]), "".join(skel["status"]))
                lst = by_shape[key]
                if len(lst) < per_shape and all(c != ci for c, _ in lst): lst.append((ci, sub))
            if step < 3: Cc, _ = Cc.canonical_transpose(I)
    return by_shape, n_sub, n_dark2


def planted_objects(geo, rng, n_each=150):
    out = defaultdict(list)
    lim, _ = geo.limit_configs()
    def full_helper(f, L): return (f, 3, list(geo.trip[f]), L)
    def accept(kind, labels, helpers):
        obj = C.obj_from_parts(geo, [(l, s) for l, s in zip(labels, C.statuses(helpers, len(labels)))], helpers)
        if len({l for l in labels}) != len(labels): return False
        rep = V.verify(obj, geo, lp_check=False)
        if rep["all"][0] and sum(1 for l in obj["labels"] if l["status"] == "D") <= 1:
            out[kind].append(obj); return True
        return False
    # lim3: limit hubs with r = 0 and three full helpers
    for h, R, S in rng.sample(lim[0], min(n_each // 2, len(lim[0]))):
        labels = []; helpers = []
        for j, f in enumerate(S):
            P = geo.PM[h ^ f]; b = min(geo.B[i] for i in range(64) if P >> i & 1); labels.append(h ^ b); helpers.append(full_helper(f, [j]))
        helpers.append((h, 0, [], [0, 1, 2])); accept("lim3", labels, helpers)
    # pair: two limit hubs sharing a full helper at different labels (independent), 3-label sub-configurations
    allc = [c for r in (0, 1, 2) for c in lim[r]]
    byf = defaultdict(list)
    for i, c in enumerate(allc):
        for f in c[2]: byf[f].append(i)
    pairs = []
    for f, lst in byf.items():
        for i, j in itertools.combinations(lst, 2):
            c1, c2 = allc[i], allc[j]
            if c1[0] == c2[0] or (geo.PM[c1[0] ^ f] & geo.PM[c2[0] ^ f]): continue
            pairs.append((c1, c2))
    rng.shuffle(pairs); n = 0
    for c1, c2 in pairs:
        if n >= n_each: break
        if not geo_q3.indep(geo.joint([c1, c2])): continue
        obj = C.limit_pair_object(geo, c1, c2)
        if not V.verify(obj, geo, lp_check=False)["all"][0]: continue
        keeps = list(itertools.combinations(range(len(obj["labels"])), 3)); rng.shuffle(keeps)
        for keep in keeps[:3]:
            sub = C.restrict(obj, list(keep))
            if sum(1 for l in sub["labels"] if l["status"] == "D") <= 1 and V.verify(sub, geo, lp_check=False)["all"][0]:
                out["pair"].append(sub); n += 1
    # mixA1 / mixA2: a hub with full-met label(s) and a hub-only label shared with a second anchored hub
    def mix(kind, cfgs, nS):
        tries = 0
        cfgs = list(cfgs); rng.shuffle(cfgs)
        for h, R, S in cfgs:
            if len(out[kind]) >= n_each or tries > 40000: break
            S = list(S)[:nS]
            labels = []; helpers = []; ends = set()
            for j, f in enumerate(S):
                P = geo.PM[h ^ f]; b = min(geo.B[i] for i in range(64) if P >> i & 1); labels.append(h ^ b); ends.add(b); helpers.append(full_helper(f, [j]))
            done = False
            for b2 in rng.sample(geo.B, 64):
                if done: break
                if b2 in ends: continue
                lB = h ^ b2
                if geo.rankC.get(lB, 0) < 2 or lB in labels: continue
                for b3 in rng.sample(geo.B, 64):
                    h2 = lB ^ b3
                    if h2 == h or h2 in geo.Bset or not geo.trip.get(h2) or h2 in S: continue
                    tries += 1
                    T2 = rng.choice(geo.trip[h2]); r2 = 1
                    labs = labels + [lB]; hs = list(helpers) + [(h, len(R), list(R), list(range(nS + 1)))]
                    if nS == 1:                    # third label: private hub-only label of the second hub
                        b4 = next(b for b in geo.B if b != b3 and (h2 ^ b) not in labs)
                        labs = labs + [h2 ^ b4]; hs.append((h2, r2, [T2], [nS, nS + 1]))
                    else:
                        hs.append((h2, r2, [T2], [nS]))
                    if accept(kind, labs, hs): done = True; break
    r1cfg = [c for c in lim[1]]
    mix("mixA1", [(h, R, S) for h, R, S in r1cfg] + [(h, R, S) for h, R, S in lim[2]], 1)
    mix("mixA2", r1cfg, 2)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--per-shape", type=int, default=6); ap.add_argument("--unguided", type=int, default=80)
    args = ap.parse_args()
    t0 = time.time(); cpu0 = time.process_time(); rng = random.Random(20261111)
    geos = {"M": make_geo("M"), "Mt": make_geo("Mt")}
    by_shape, n_sub, n_dark2 = real_objects(geos, args.per_shape)
    print(f"real phases: {n_sub} 3-label sub-configurations, {n_dark2} with >= 2 dark labels (outside the domain, skipped), {len(by_shape)} distinct (orientation, skeleton) shapes with d <= 1; {time.time()-t0:.0f}s", flush=True)
    planted = planted_objects(geos["Mt"], rng)
    print("planted (M^T):", {k: len(v) for k, v in planted.items()}, f"{time.time()-t0:.0f}s", flush=True)
    items = [("real", ori, sub) for (ori, _, _), lst in by_shape.items() for _, sub in lst] + [("planted:" + k, "Mt", o) for k, lst in planted.items() for o in lst]
    res = []; miss = []; feat = Counter(); kinds = Counter(); modes = Counter(); shapes = set(); ung = Counter()
    ung_budget = args.unguided; order_ = list(range(len(items))); rng.shuffle(order_); ung_set = set()
    for n, idx in enumerate(order_):
        src, ori, obj = items[idx]
        r = check_object(geos[ori], obj, unguided=(ung_budget > 0))
        r["source"] = src; r["ori"] = ori
        kinds[(src, r["kind"])] += 1
        if r["kind"] == "constrained":
            modes[r["mode"]] += 1; shapes.add((ori, json.dumps(r["skel"]["roles"]), "".join(r["skel"]["status"])))
            for f in r["features"]: feat[f] += 1
            if "U" in r:
                ung_budget -= 1; ung[str(r["U"])] += 1
                if r["U"] is False: miss.append(("U", src, ori, obj, r))
            if not r["G"]: miss.append(("G", src, ori, obj, r))
        if not r["S"]: miss.append(("S", src, ori, obj, r))
        res.append({k: v for k, v in r.items() if k != "skel"} | {"roles": r["skel"]["roles"], "status": r["skel"]["status"]})
    n_con = sum(v for (s, k), v in kinds.items() if k == "constrained")
    summ = dict(objects=len(items), constrained=n_con, free_only=len(items) - n_con, by_source={f"{s}|{k}": v for (s, k), v in sorted(kinds.items())},
                distinct_constrained_shapes=len(shapes), modes=dict(modes), feature_counts=dict(sorted(feat.items())),
                step_S_misses=sum(1 for m in miss if m[0] == "S"), step_G_misses=sum(1 for m in miss if m[0] == "G"),
                unguided=dict(ung), unguided_misses=sum(1 for m in miss if m[0] == "U"),
                real_subconfigurations_scanned=n_sub, skipped_two_dark=n_dark2, passed=(not miss and n_con >= 500),
                seconds=round(time.time() - t0), cpu_seconds=round(time.process_time() - cpu0))
    json.dump(dict(summary=summ, results=res, misses=[[m[0], m[1], m[2], m[3], {k: v for k, v in m[4].items()}] for m in miss[:50]]), open(HERE / "controls_p5.json", "w"))
    print(json.dumps(summ, indent=1))
    for m in miss[:10]:
        print("MISS", m[0], m[1], m[2], "skeleton", m[4]["skel"]["roles"], m[4]["skel"]["status"], "features", m[4]["features"], "statuses", m[4].get("statuses"))
        print("     object", json.dumps(m[3]))
    sys.exit(0 if summ["passed"] else 2)
