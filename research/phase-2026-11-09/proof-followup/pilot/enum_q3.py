#!/usr/bin/env python3
"""enum_q3.py -- complete depth-first enumeration of the label configurations of the M^T, q = 3 leaves at G = 75
(PILOT_SPEC.md sections 3 and 8).  Exact arithmetic (GF(2) on python ints); the LP filter R8 (scipy HiGHS) prunes only
on status 2.

Step S: skeletons (multisets of roles (r, L)) with R4, R5, R6, (B-1), the column set of the case and R8 (monotone at
prefixes, exact at the complete skeleton), canonical under status-preserving slot permutations.
Step G: per skeleton, the anchored roles are planned breadth-first from the root slot; every maximal run of anchored roles
reachable from one root is a SEGMENT.  One segment (2,314 of 2,790 skeletons): a single DFS over the whole order.  Several
segments: each segment is enumerated separately (all its realizations stored, up to a cap), then the product of the
segment lists is searched lazily for a combination that passes R1 (masks and labels distinct), R7 on the union, and the
placement of the r = 0, u >= 2 helpers; the first combination found is a witness; an exhausted product without one is an
exclusion of the skeleton; a segment with no realization excludes the skeleton outright (every realization of the whole
restricts to one of each segment).  Caps and CPU deadlines turn a result into UNRESOLVED, never into EXCLUDED.

usage:  python3 enum_q3.py [--workers N] [--estimate-only] [--max-store 20] [--leaf-cpu 60] [--out results]
        python3 enum_q3.py --leaf "(15, 1, 0, 'Mt', 3, 3)" 0 0        (one leaf, verbose)
"""
import sys, json, time, itertools, argparse, os
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geo_q3  # noqa: E402
REPO = Path.home() / "xor-circuit-research"
CHK = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases/checkers"
sys.path.insert(0, str(CHK))
import check_combined75 as CC  # noqa: E402

GEO = None            # geo_q3.GeoQ('Mt'), built once per process
ORI = "Mt"


class Timeout(Exception):
    pass


# ----------------------------------------------------------------------------------------------------------- R8: the LP
class LeafLP:
    """the combined case system S(K, a, d) (check_combined75.matrix) with count rows on the (r, u) classes, u >= 1."""
    def __init__(self, key, a, d):
        b, cols, *_ = CC.matrix(key, ("eq", a), d)
        self.key, self.a, self.d = key, a, d
        self.labels = [lab for lab, _ in cols]
        self.A = np.array([col for _, col in cols], float).T
        self.b = np.array(b, float)
        self.classes = sorted({(lab[0], lab[1]) for lab in self.labels if isinstance(lab, tuple) and lab[1] >= 1})
        self.ind = {c: np.array([1.0 if isinstance(lab, tuple) and (lab[0], lab[1]) == c else 0.0 for lab in self.labels])
                    for c in self.classes}
        self.cache = {}; self.ncalls = 0; self.status = Counter(); self.pruned = []

    def feasible(self, counts, exact):
        """counts: {(r,u): n}.  exact: sum_v n_(r,u,v) = n for every class (absent classes = 0); else >= n."""
        k = (tuple(sorted(counts.items())), exact)
        if k in self.cache: return self.cache[k]
        rows = []; rhs = []
        for c, n in counts.items():
            if c not in self.ind:
                if n:                               # a type deleted by HUB2 in this hub case cannot occur
                    self.cache[k] = False; return False
                continue
            rows.append(-self.ind[c]); rhs.append(-float(n))
            if exact: rows.append(self.ind[c]); rhs.append(float(n))
        if exact:
            for c in self.classes:
                if c not in counts: rows.append(self.ind[c]); rhs.append(0.0)
        A = np.vstack([self.A] + rows) if rows else self.A
        b = np.concatenate([self.b, np.array(rhs)]) if rows else self.b
        res = linprog(np.zeros(A.shape[1]), A_ub=A, b_ub=b, bounds=(0, None), method="highs")
        self.ncalls += 1; self.status[int(res.status)] += 1
        ok = res.status != 2                        # prune ONLY on proved infeasibility
        if not ok: self.pruned.append((tuple(sorted(counts.items())), exact))
        self.cache[k] = ok
        return ok


# ------------------------------------------------------------------------------------------------- step S: skeletons
def slot_status(a, d):
    return ["F"] * a + ["B"] * (3 - a - d) + ["D"] * d


def canonical_skeleton(roles, status):
    perms = [p for p in itertools.permutations(range(3)) if all(status[p[s]] == status[s] for s in range(3))]
    best = None
    for p in perms:
        img = tuple(sorted((r, tuple(sorted(p[s] for s in L))) for r, L in roles))
        if best is None or img < best: best = img
    return best


def skeleton_enum(lp, a, d):
    status = slot_status(a, d)
    full_slots = {s for s in range(3) if status[s] == "F"}; dark = {s for s in range(3) if status[s] == "D"}
    roles = []
    for r in range(4):
        for m in range(1, 8):
            L = tuple(s for s in range(3) if m >> s & 1)
            if r == 3 and not set(L) <= full_slots: continue
            if r >= 1 and set(L) & dark: continue
            if (r, len(L)) not in lp.ind: continue
            roles.append((r, L))
    roles.sort(key=lambda x: (-x[0], -len(x[1]), x[1]))
    stats = Counter(); seen = {}; out = []

    def complete(chosen, fullcover):
        if any(fullcover[s] != 1 for s in full_slots): return False
        for s in range(3):
            if status[s] == "B" and not any(r >= 1 and s in L for r, L in chosen): return False
        return True

    def rec(idx, chosen, counts, Wslot, fullcover):
        stats["nodes"] += 1
        if complete(chosen, fullcover):
            stats["lp_exact_checks"] += 1
            if lp.feasible(counts, True):
                ck = canonical_skeleton(chosen, status)
                if ck not in seen:
                    seen[ck] = True
                    out.append(dict(roles=[list(x) for x in ck], status=status, W=[sum(r for r, L in ck if s in L) for s in range(3)],
                                    counts={f"{r},{u}": n for (r, u), n in sorted(counts.items())}))
                else: stats["duplicates"] += 1
            else: stats["lp_exact_pruned"] += 1
        for j in range(idx, len(roles)):
            r, L = roles[j]
            if any(len(set(L) & set(L2)) >= 2 for _, L2 in chosen): stats["prune_R5"] += 1; continue
            if any(Wslot[s] + r > 7 for s in L): stats["prune_B1"] += 1; continue
            if r == 3 and any(fullcover[s] for s in L): stats["prune_R4"] += 1; continue
            c2 = dict(counts); c2[(r, len(L))] = c2.get((r, len(L)), 0) + 1
            stats["lp_mono_checks"] += 1
            if not lp.feasible(c2, False): stats["lp_mono_pruned"] += 1; continue
            W2 = list(Wslot); fc = list(fullcover)
            for s in L:
                W2[s] += r
                if r == 3: fc[s] += 1
            rec(j, chosen + [(r, L)], c2, W2, fc)

    rec(0, [], {}, [0, 0, 0], [0, 0, 0])
    return out, stats


# ------------------------------------------------------------------------------------------- step G: planning a skeleton
def plan(skel, sym_first_root=True):
    roles = [(r, tuple(L)) for r, L in skel["roles"]]; status = skel["status"]; W = skel["W"]
    parent = list(range(3))
    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for r, L in roles:
        for s in L[1:]: parent[find(s)] = find(L[0])
    comps = defaultdict(set)
    for s in range(3): comps[find(s)].add(s)
    comp_list = []
    for cs in comps.values():
        cro = [i for i, (r, L) in enumerate(roles) if L[0] in cs]
        anchored = [i for i in cro if roles[i][0] >= 1]
        edges = sum(len(roles[i][1]) for i in cro); verts = len(cs) + len(cro)
        free = len(anchored) <= 1 and edges == verts - 1
        comp_list.append(dict(slots=sorted(cs), roles=cro, anchored=anchored, free=free, maxW=max(W[s] for s in cs)))
    constrained = sorted([c for c in comp_list if not c["free"]], key=lambda c: (-c["maxW"], c["slots"]))
    segments = []; riders2 = []; concrete = set(); first = True
    for c in constrained:
        remaining = [i for i in c["roles"] if roles[i][0] >= 1]
        pending_riders = sorted(i for i in c["roles"] if roles[i][0] == 0 and len(roles[i][1]) >= 2)
        while remaining or any(set(roles[i][1]) <= concrete and segments and set(roles[i][1]) <= segments[-1]["slots"] for i in pending_riders):
            touching = [i for i in remaining if set(roles[i][1]) & concrete]
            # r = 0, u >= 2 helpers whose slots are all concrete INSIDE the current segment are placed as soon as possible
            # (at most two candidates each, (D-2)); the others wait for the end (riders2)
            ready_riders = [i for i in pending_riders if segments and set(roles[i][1]) <= segments[-1]["slots"]]
            if touching or ready_riders:
                # fail-first order: most concrete slots, then largest |L| (creates slots), then largest r (fewest candidates)
                i = min(touching + ready_riders, key=lambda i: (-len(set(roles[i][1]) & concrete), -len(roles[i][1]), -roles[i][0], roles[i][1]))
                s = max((s for s in roles[i][1] if s in concrete), key=lambda s: (W[s], -s))
                assert s in segments[-1]["slots"], ("plan: attach to a slot of an earlier segment", skel)
                segments[-1]["order"].append((i, "attach", s, False))
            else:
                i = min(remaining, key=lambda i: (-max(W[s] for s in roles[i][1]), -roles[i][0], roles[i][1]))
                s = max(roles[i][1], key=lambda s: (W[s], -s))
                segments.append(dict(order=[(i, "root", s, first and sym_first_root)], slots=set(), root_slot=s)); first = False
            concrete |= set(roles[i][1]); segments[-1]["slots"] |= set(roles[i][1])
            if i in remaining: remaining.remove(i)
            else: pending_riders.remove(i)
        riders2 += pending_riders
    riders1 = [i for c in constrained for i in c["roles"] if roles[i][0] == 0 and len(roles[i][1]) == 1]
    def rider_slot(i):
        bright = [s for s in roles[i][1] if status[s] != "D"]
        return max(bright, key=lambda s: (W[s], -s)) if bright else roles[i][1][0]
    order = [e for seg in segments for e in seg["order"]] + [(i, "attach", rider_slot(i), False) for i in riders2]
    return dict(roles=roles, status=status, W=W, order=order, segments=segments, riders2=riders2, free=[c for c in comp_list if c["free"]],
                constrained=constrained, riders=riders1)


# ---------------------------------------------------------------------------------------- step G: realization (DFS)
class Realizer:
    """depth-first realization of a list of order entries (roles with modes); helper k of the order uses bit 64 + k."""
    def __init__(self, geo, pl, order, max_store=20, max_survivors=None, deadline=None, init=None, guide=None):
        self.geo = geo; self.pl = pl
        self.guide = guide       # P5 control only: restricts branches to a planted target (never used in the enumeration)
        self.roles = pl["roles"]; self.W = pl["W"]; self.status = pl["status"]; self.order = order
        self.n = len(order)
        self.max_store = max_store; self.max_survivors = max_survivors; self.deadline = deadline
        self.stats = Counter(); self.deepest = []; self.survivors = []; self.stop = False; self.timed_out = False; self.deep_k = 0
        if not hasattr(geo, "cand_cache"): geo.cand_cache = {}
        # identical roles (same (r, L)) are interchangeable helpers of the object (PILOT_SPEC.md section 1: I is a SET):
        # canonical order = increasing mask among them (viable(): h > hmin, the largest mask of a placed identical role)
        self.lab = [None] * 3; self.hel = [None] * self.n; self.firstc = {}; self.masks = set(); self.labset = set(); self.piv = {}
        self.depth_nodes = Counter(); self.base = 0
        if init is not None:                        # product phase: start from realized helpers (list of (h, R, ends, role)), labels
            self.lab = list(init["labels"]); self.labset = {l for l in self.lab if l is not None}
            self.base = len(init["helpers"]); self.prefix = init["helpers"]
            vecs = []
            for k, (h, R, ends, i) in enumerate(init["helpers"]):
                self.masks.add(h)
                for t in R: vecs.append(t | (1 << (64 + k)))
                for s, b in ends.items():
                    if s not in self.firstc: self.firstc[s] = (k, b)
                    else:
                        c, bc = self.firstc[s]
                        vecs.append((1 << (64 + k)) | (1 << (64 + c)) | (1 << geo.Bidx[b]) | (1 << geo.Bidx[bc]))
            self.init_ok = self.add_vecs(vecs) is not None
        else:
            self.prefix = []; self.init_ok = True

    def add_vecs(self, vs):
        piv = self.piv; added = []
        for v in vs:
            while v:
                lb = v & -v
                p = piv.get(lb)
                if p is None:
                    piv[lb] = v; added.append(lb); break
                v ^= p
            else:
                for lb in added: del piv[lb]
                return None
        return added

    def undo(self, added):
        for lb in added: del self.piv[lb]

    def candidates(self, l, r):
        """anchored-carrier candidates of a concrete label l: [(b, h, T)] with h = l + b not in B and T = triples of h
        (non-empty); cached per label (the same label recurs at many nodes).  r = 0 roles iterate over all of B."""
        c = self.geo.cand_cache.get(l)
        if c is None:
            geo = self.geo; c = []
            for b in geo.B:
                h = l ^ b
                if h in geo.Bset: continue
                T = geo.trip.get(h)
                if T: c.append((b, h, T))
            if len(geo.cand_cache) > 400_000: geo.cand_cache.clear()
            geo.cand_cache[l] = c
        return c

    def record_deepest(self, k, h, R, reason):
        if k < self.deep_k: return
        if len(self.deepest) < 5 or k > self.deepest[-1][0]:
            self.deep_k = k
            entry = (k, reason, hex(h), [hex(t) for t in R], [None if l is None else hex(l) for l in self.lab],
                     [None if x is None else hex(x[0]) for x in self.hel[:k]])
            self.deepest.append(entry); self.deepest.sort(key=lambda e: -e[0]); del self.deepest[5:]

    def run(self):
        if not self.init_ok: self.stats["init_dependent"] += 1; return
        try:
            self.dfs(0)
        except Timeout:
            self.timed_out = True

    def viable(self, i, hmin):
        """the viable candidates (b, h, T, ends) of role i given the concrete slots: R1 (mask new, > hmin for identical
        roles), (D-h)/R3 (enough triples), (D-b)/(D-2) on every concrete slot of the role.  None if no slot is concrete."""
        r, L = self.roles[i]; lab = self.lab; geo = self.geo; Bset = geo.Bset
        conc = [s for s in L if lab[s] is not None]
        if not conc: return None
        s0 = max(conc, key=lambda s: (self.W[s], -s)); l0 = lab[s0]
        if r >= 1: base = [(b, h, T) for b, h, T in self.candidates(l0, r) if len(T) >= r]
        else: base = [(b, l0 ^ b, ()) for b in geo.B if (l0 ^ b) not in Bset]
        out = []
        for b, h, T in base:
            if h in self.masks or h <= hmin: continue
            ends = {s0: b}; ok = True
            for s in conc:
                if s == s0: continue
                bb = h ^ lab[s]
                if bb not in Bset: ok = False; break
                ends[s] = bb
            if ok: out.append((b, h, T, ends))
        return out

    def dfs(self, k, remaining=None):
        """k = number of helpers placed; remaining = role entries of the order not yet placed (dynamic order: the role with
        the fewest viable candidates is branched on next; a role with none prunes the node at once)."""
        if self.stop: return
        if remaining is None: remaining = list(range(self.n))
        self.stats["nodes"] += 1; self.depth_nodes[k] += 1
        if self.deadline is not None and (self.stats["nodes"] & 1023) == 0 and time.process_time() > self.deadline: raise Timeout()
        if not remaining:
            self.stats["survivors"] += 1
            if len(self.survivors) < self.max_store: self.survivors.append(self.snapshot())
            if self.max_survivors and self.stats["survivors"] >= self.max_survivors: self.stop = True
            return
        # the first entry of the order is the root (static); afterwards dynamic choice
        e0 = remaining[0]
        i, mode, s0, use_reps = self.order[e0]
        if mode == "root":
            r, L = self.roles[i]
            cand = self.geo.ge_reps[self.W[s0]] if use_reps else self.geo.ge[self.W[s0]]
            self.stats["root_candidates"] += len(cand)
            rest = remaining[1:]
            for l in cand:
                if l in self.labset: continue
                if self.guide is not None and not self.guide.ok_root(s0, l): continue
                self.lab[s0] = l; self.labset.add(l)
                self.attach(k, i, self.viable(i, -1), rest)
                self.labset.discard(l); self.lab[s0] = None
                if self.stop: return
            return
        best = None
        for e in remaining:
            i = self.order[e][0]
            same = [x[0] for x in self.hel[:k] if x is not None and self.roles[x[3]] == self.roles[i]]
            hmin = max(same) if same else -1
            v = self.viable(i, hmin)
            if v is None: continue
            score = (len(v), -len(self.roles[i][1]), -self.roles[i][0])
            if best is None or score < best[0]: best = (score, e, v)
            if not v: break
        if best is None:                           # no remaining role touches a concrete slot: cannot happen within a segment
            self.stats["no_concrete_role"] += 1; self.stop = True; return
        score, e, v = best
        if not v: self.stats["prune_dead_role"] += 1; return
        rest = [x for x in remaining if x != e]
        self.attach(k, self.order[e][0], v, rest)

    def attach(self, k, i, cands, rest):
        geo = self.geo; Bidx = geo.Bidx; lab = self.lab; st = self.stats
        r, L = self.roles[i]
        conc = [s for s in L if lab[s] is not None]; newslots = [s for s in L if lab[s] is None]
        hk = 1 << (64 + self.base + k)
        g = self.guide
        for b, h, T, ends in cands or []:
            if g is not None and not g.ok_mask(self.roles[i], h): continue
            Rs = [tuple(T)] if r == 3 else ([()] if r == 0 else list(itertools.combinations(T, r)))
            for R in Rs:
                if g is not None and not g.ok_helper(self.roles[i], h, R): continue
                vs = [t | hk for t in R]
                for s in conc:
                    fc = self.firstc.get(s)
                    if fc is not None:
                        c, bc = fc
                        vs.append(hk | (1 << (64 + c)) | (1 << Bidx[ends[s]]) | (1 << Bidx[bc]))
                added = self.add_vecs(vs)
                if added is None: st["prune_R7"] += 1; self.record_deepest(k, h, R, "R7"); continue
                self.masks.add(h); self.hel[k] = (h, R, dict(ends), i)
                newfirst = [s for s in conc if s not in self.firstc]
                for s in newfirst: self.firstc[s] = (self.base + k, ends[s])
                self.assign_new(k, newslots, 0, h, dict(ends), rest)
                for s in newfirst: del self.firstc[s]
                self.masks.discard(h); self.hel[k] = None
                self.undo(added)
                if self.stop: return

    def assign_new(self, k, newslots, j, h, ends, rest):
        if j == len(newslots):
            self.hel[k] = (h, self.hel[k][1], dict(ends), self.hel[k][3])
            self.dfs(k + 1, rest); return
        s = newslots[j]; st = self.stats; rankC = self.geo.rankC; dark = self.status[s] == "D"; W = self.W[s]
        for b in self.geo.B:
            if b in ends.values(): continue
            l = h ^ b
            if l in self.labset: st["prune_R1lab"] += 1; continue
            if not dark and rankC.get(l, 0) < W: st["prune_rank"] += 1; continue
            if self.guide is not None and not self.guide.ok_label(s, l): continue
            self.lab[s] = l; self.labset.add(l); ends[s] = b; self.firstc[s] = (self.base + k, b)
            self.assign_new(k, newslots, j + 1, h, ends, rest)
            del self.firstc[s]; del ends[s]; self.labset.discard(l); self.lab[s] = None
            if self.stop: return

    def snapshot(self):
        return dict(labels=list(self.lab), helpers=list(self.prefix) + [(x[0], tuple(x[1]), dict(x[2]), x[3]) for x in self.hel])


def run_skeleton(geo, pl, max_store, max_survivors, deadline, seg_cap=300_000, combo_cap=300_000, guide=None):
    """returns dict(survivors, stored snapshots, stats, mode, status in {'done','timeout','capped'})."""
    segs = pl["segments"]; st = Counter(); deepest = []
    # FIX (2026-11-11): the product phase places ONLY the deferred r = 0, u >= 2 helpers (pl['riders2']); those placed
    # inside a segment are already part of the segment realizations.  The pass-1 code took every r = 0 entry of the
    # order and so placed in-segment riders twice (a possible false 'no combination').
    n_seg_entries = sum(len(seg["order"]) for seg in segs)
    rider_entries = list(pl["order"][n_seg_entries:])
    assert all(pl["roles"][e[0]][0] == 0 for e in rider_entries) and [e[0] for e in rider_entries] == list(pl["riders2"])
    def bad(R): return bool(R.stats.get("no_concrete_role") or R.stats.get("rider_no_concrete_slot"))
    if len(segs) <= 1:
        R = Realizer(geo, pl, pl["order"], max_store=max_store, max_survivors=max_survivors, deadline=deadline, guide=guide); R.run()
        return dict(mode="single", survivors=R.stats["survivors"], snaps=R.survivors, stats=dict(R.stats), depth=dict(R.depth_nodes),
                    deepest=R.deepest, status="error" if bad(R) else ("timeout" if R.timed_out else "done"), seg_counts=[R.stats["survivors"]])
    # several segments: enumerate each separately (a segment without realization excludes the skeleton outright)
    seg_lists = []; seg_counts = []; capped = False
    for seg in segs:
        R = Realizer(geo, pl, seg["order"], max_store=seg_cap, max_survivors=seg_cap, deadline=deadline, guide=guide); R.run()
        for k2, v in R.stats.items(): st["seg_" + k2] += v
        deepest += R.deepest
        if bad(R): return dict(mode="segments", survivors=0, snaps=[], stats=dict(st), depth={}, deepest=deepest, status="error", seg_counts=seg_counts)
        if R.timed_out: return dict(mode="segments", survivors=0, snaps=[], stats=dict(st), depth={}, deepest=deepest, status="timeout", seg_counts=seg_counts)
        seg_counts.append(R.stats["survivors"])
        if R.stats["survivors"] >= seg_cap: capped = True
        seg_lists.append(R.survivors)
    if any(c == 0 for c in seg_counts):
        return dict(mode="segments", survivors=0, snaps=[], stats=dict(st), depth={}, deepest=deepest, status="done", seg_counts=seg_counts)
    if capped:
        return dict(mode="segments", survivors=0, snaps=[], stats=dict(st), depth={}, deepest=deepest, status="capped", seg_counts=seg_counts)
    # lazy product over the segment lists: R1 across segments, R7 on the union, then the riders with u >= 2
    n_combo = 0; found = []; status = "done"
    for combo in itertools.product(*seg_lists):
        n_combo += 1
        if n_combo > combo_cap: status = "capped"; break
        if deadline is not None and (n_combo & 255) == 0 and time.process_time() > deadline: status = "timeout"; break
        labels = [None] * 3; helpers = []; masks = set(); ok = True; labset = set()
        for snap in combo:
            for s in range(3):
                if snap["labels"][s] is not None:
                    if labels[s] is not None or snap["labels"][s] in labset: ok = False
                    labels[s] = snap["labels"][s]; labset.add(labels[s])
            for h, R, ends, i in snap["helpers"]:
                if h in masks: ok = False
                masks.add(h); helpers.append((h, R, ends, i))
        if not ok: st["combo_R1"] += 1; continue
        R = Realizer(geo, pl, rider_entries, max_store=max_store, max_survivors=1, deadline=deadline, init=dict(labels=labels, helpers=helpers), guide=guide)
        if not R.init_ok: st["combo_R7"] += 1; continue
        R.run()
        for k2, v in R.stats.items(): st["prod_" + k2] += v
        if bad(R): status = "error"; break
        if R.timed_out: status = "timeout"; break
        if R.stats["survivors"]:
            found = R.survivors; break
    st["combinations_tried"] = n_combo
    return dict(mode="segments", survivors=len(found), snaps=found, stats=dict(st), depth={}, deepest=deepest, status=status, seg_counts=seg_counts)


# ---------------------------------------------------------------------------------- witnesses: completing the free parts
def complete_witness(geo, pl, snap, key, a, d, tries=30):
    """add the free riders and free components (PILOT_SPEC.md 3.9, 3.10) with explicit values, verify, return (obj, report)."""
    import verify_q3 as V
    roles = pl["roles"]; status = pl["status"]
    lab = list(snap["labels"]); helpers = []
    masks = set(); labset = {l for l in lab if l is not None}
    for h, R, ends, i in snap["helpers"]:
        helpers.append((i, h, list(R))); masks.add(h)
    Bset = geo.Bset
    trip_vals = {r: [v for v, t in geo.trip.items() if len(t) >= r] for r in (1, 2, 3)}
    last = None

    def realize_free(attempt):
        add = []; lab2 = list(lab); masks2 = set(masks); labset2 = set(labset)
        odd_iter = itertools.count(1 + 2 * attempt, 2)
        def fresh_odd():
            for v in odd_iter:
                if v not in Bset and v not in masks2 and bin(v).count("1") % 2 == 1: return v
        def fresh_even():
            for v in itertools.count(2, 2):
                if v not in labset2 and v not in geo.PM: return v
        def new_end_label(h, used):
            for b in geo.B:
                if b in used: continue
                l = h ^ b
                if l in labset2: continue
                return b, l
            return None, None
        for c in pl["free"]:
            cro = sorted(c["roles"], key=lambda i: (-roles[i][0], -len(roles[i][1]), roles[i][1]))
            for i in cro:
                r, L = roles[i]
                conc = [s for s in L if lab2[s] is not None]
                if r >= 1:
                    pool = trip_vals[r]; off = (attempt * 7919) % len(pool); h = None
                    for v in pool[off:] + pool[:off]:
                        if v in masks2: continue
                        if conc and any((v ^ lab2[s]) not in Bset for s in conc): continue
                        h = v; break
                    if h is None: return None
                    R = list(geo.trip[h][:r]) if r < 3 else list(geo.trip[h])
                else:
                    if conc:
                        h = None
                        for b in geo.B:
                            v = lab2[conc[0]] ^ b
                            if v in Bset or v in masks2: continue
                            if any((v ^ lab2[s]) not in Bset for s in conc[1:]): continue
                            h = v; break
                        if h is None: return None
                    else:
                        h = fresh_odd()
                    R = []
                masks2.add(h)
                used = {h ^ lab2[s] for s in conc}
                for s in L:
                    if lab2[s] is None:
                        b, l = new_end_label(h, used)
                        if b is None: return None
                        lab2[s] = l; labset2.add(l); used.add(b)
                add.append((i, h, R))
        for i in pl["riders"]:
            r, L = roles[i]; s = L[0]
            if lab2[s] is None:
                h = fresh_odd(); masks2.add(h)
                b, l = new_end_label(h, set())
                if b is None: return None
                lab2[s] = l; labset2.add(l)
            else:
                h = None
                for b in geo.B:
                    v = lab2[s] ^ b
                    if v in Bset or v in masks2: continue
                    h = v; break
                if h is None: return None
                masks2.add(h)
            add.append((i, h, []))
        for s in range(3):
            if lab2[s] is None: lab2[s] = fresh_even(); labset2.add(lab2[s])
        return add, lab2

    for attempt in range(tries):
        out = realize_free(attempt)
        if out is None: continue
        add, lab2 = out
        allh = helpers + add
        obj = dict(ori=ORI, labels=[dict(value=lab2[s], status=status[s]) for s in range(3)],
                   helpers=[dict(mask=h, r=roles[i][0], triples=list(R), labels=list(roles[i][1]), role=i) for i, h, R in allh])
        rep = V.verify(obj, geo, key, a, d, lp_check=True)
        if rep["all"][0]: return obj, rep
        last = rep
    return dict(incomplete=True, partial=dict(labels=snap["labels"], helpers=[[h, list(R), {str(s): b for s, b in e.items()}, i] for h, R, e, i in snap["helpers"]])), \
        {"all": (False, "free-part completion failed"), "last": {k: [v[0], v[1]] for k, v in last.items()} if last else None}


# -------------------------------------------------------------------------------------------------------- estimates
def candidate_counts(geo, l):
    c = [0, 0, 0, 0]
    for b in geo.B:
        h = l ^ b
        if h in geo.Bset: continue
        t = len(geo.trip.get(h, ()))
        c[0] += 1
        for r in (1, 2, 3):
            if t >= r: c[r] += comb(t, r)
    return c


def estimate_skeleton(geo, pl, avg):
    """(upper bound, refined estimate) of the geometric nodes of a skeleton without R7 pruning; for several segments the
    segments are summed (they are enumerated separately) and the product phase is counted as the product of the segment
    estimates capped by the combination cap."""
    roles = pl["roles"]; W = pl["W"]
    def seg_est(order):
        ub = 1; est = 1.0
        for i, mode, s0, use_reps in order:
            r, L = roles[i]
            if mode == "root":
                cand = geo.ge_reps[W[s0]] if use_reps else geo.ge[W[s0]]
                ub *= len(cand); est *= len(cand)
            per = 64 * (comb(3, r) if r else 1)
            ub *= per * 63 ** (len(L) - 1)
            f = avg[r][min(W[s0], 7)]
            for s in L:
                if s == s0: continue
                f *= 63 * (avg["pr"][max(r, 1)][min(W[s], 7)] if pl["status"][s] != "D" else 1.0)
            est *= f
        return ub, est
    if len(pl["segments"]) <= 1:
        return seg_est(pl["order"])
    from math import prod
    ubs, ests = zip(*(seg_est(seg["order"]) for seg in pl["segments"]))
    rub, rest = seg_est([e for e in pl["order"] if roles[e[0]][0] == 0]) if any(roles[e[0]][0] == 0 for e in pl["order"]) else (1, 1.0)
    return sum(ubs) + min(300_000, prod(ubs)) * rub, sum(ests) + min(300_000.0, float(prod(ests))) * rest


def averages(geo, seed=1):
    import random
    avg = {r: {} for r in range(4)}
    for k in range(1, 8):
        vals = geo.ge[k]
        if k == 1: vals = vals[::max(1, len(vals) // 20000)]
        tot = [0, 0, 0, 0]
        for l in vals:
            c = candidate_counts(geo, l)
            for r in range(4): tot[r] += c[r]
        for r in range(4): avg[r][k] = tot[r] / max(1, len(vals))
    rng = random.Random(seed); pr = {}
    for t in (1, 2, 3):
        hs = [h for h, T in geo.trip.items() if len(T) == t]
        sample = rng.sample(hs, min(2000, len(hs)))
        cnt = Counter(); n = 0
        for h in sample:
            for b in geo.B:
                cnt[geo.rankC.get(h ^ b, 0)] += 1; n += 1
        pr[t] = {W: sum(v for k, v in cnt.items() if k >= W) / n for W in range(0, 8)}
    avg["pr"] = pr
    return avg


# ---------------------------------------------------------------------------------------------------------- per leaf
def build_geo():
    global GEO
    if GEO is None:
        GEO = geo_q3.GeoQ(ORI)
        GEO.ge = {k: sorted(l for l, rk in GEO.rankC.items() if rk >= k) for k in range(1, 8)}
        GEO.ge[0] = GEO.ge[1]
        GEO.ge_reps = {k: [l for l in GEO.ge[k] if GEO.is_rep(l)] for k in GEO.ge}
    return GEO


def run_leaf(key, a, d, max_store=20, max_survivors=200, estimate_only=False, avg=None, sym=True, verbose=False, leaf_cpu=None, milp_limit=20.0, skel_cpu=25.0):
    import verify_q3 as V
    geo = build_geo(); t0 = time.time(); cpu0 = time.process_time()
    lp = LeafLP(key, a, d)
    skels_lp, sstats = skeleton_enum(lp, a, d)
    # R8-int: the type vector of a circuit is integral; a complete skeleton whose counts admit no integer solution of the
    # case system cannot occur (scipy HiGHS MILP, prunes ONLY on status 2; status recorded) [measured]
    skels = []; milp_hist = Counter(); milp_killed = []
    for sk in skels_lp:
        ms = V.milp_status(key, a, d, {tuple(int(x) for x in c.split(",")): n for c, n in sk["counts"].items()}, time_limit=milp_limit)
        sk["milp"] = dict(status=ms["status"], cls=ms["cls"]); milp_hist[ms["status"]] += 1
        if ms["status"] == 2: milp_killed.append(sk["roles"])
        else: skels.append(sk)
    out = dict(key=list(key), A=a, qD=d, skeletons_lp=len(skels_lp), skeletons=len(skels), skeletons_milp_infeasible=len(milp_killed),
               milp_status_hist=dict(milp_hist), skeletons_milp_killed=milp_killed, skeleton_stats=dict(sstats), lp_calls=lp.ncalls, lp_status=dict(lp.status),
               lp_pruned_vectors=[[list(map(list, cv)), ex] for cv, ex in lp.pruned], skeleton_list=[])
    deadline = (time.process_time() + leaf_cpu) if leaf_cpu else None
    tot_ub = 0; tot_est = 0.0
    geo_stats = Counter(); depth_nodes = Counter(); survivors_total = 0; witnesses = []; deepest = []; unresolved = []
    plans = []
    for sk in skels:
        pl = plan(sk, sym_first_root=sym)
        ub, est = estimate_skeleton(geo, pl, avg) if avg else (None, None)
        plans.append((est if est is not None else 0, sk, pl, ub, est))
    plans.sort(key=lambda x: x[0])                 # cheapest (by estimate) first, so that a cap leaves as few skeletons unrun as possible
    for _, sk, pl, ub, est in plans:
        if ub is not None: tot_ub += ub; tot_est += est
        entry = dict(roles=sk["roles"], W=sk["W"], counts=sk["counts"], order=[[pl["roles"][i], m, s, bool(u)] for i, m, s, u in pl["order"]],
                     segments=len(pl["segments"]), free_components=[c["slots"] for c in pl["free"]], riders=len(pl["riders"]), riders2=len(pl["riders2"]), est_ub=ub, est=est)
        if not estimate_only:
            if deadline is not None and time.process_time() > deadline:
                out["skeletons_not_run"] = len(skels) - len(out["skeleton_list"]); unresolved.append(dict(roles=sk["roles"], status="not_run")); break
            sk_deadline = min(deadline, time.process_time() + skel_cpu) if (deadline is not None and skel_cpu) else (deadline if deadline is not None else ((time.process_time() + skel_cpu) if skel_cpu else None))
            res = run_skeleton(geo, pl, max_store, max_survivors, sk_deadline)
            entry.update(mode=res["mode"], geo_stats=res["stats"], depth_nodes=res["depth"], deepest_pruned=res["deepest"], status=res["status"], seg_counts=res["seg_counts"], survivors=res["survivors"])
            geo_stats.update(res["stats"]); depth_nodes.update(res["depth"])
            survivors_total += res["survivors"]
            if res["status"] != "done": unresolved.append(dict(roles=sk["roles"], status=res["status"]))
            if res["survivors"]:
                wl = []
                for snap in res["snaps"]:
                    obj, rep = complete_witness(geo, pl, snap, key, a, d)
                    w = dict(skeleton=sk["roles"], object=obj, verify={k: [v[0], v[1]] for k, v in rep.items() if isinstance(v, tuple)})
                    if rep["all"][0]:
                        w["milp"] = V.milp_status(key, a, d, dict(V.counts_of(obj)))
                    else:
                        w["completion_failed"] = rep.get("last")
                    wl.append(w)
                entry["witnesses"] = wl; witnesses.extend(wl)
            deepest.extend(res["deepest"])
        out["skeleton_list"].append(entry)
    out.update(est_ub=tot_ub, est_refined=tot_est)
    if not estimate_only:
        deepest.sort(key=lambda e: -e[0])
        out.update(geo_stats=dict(geo_stats), depth_nodes=dict(depth_nodes), survivors=survivors_total,
                   witnesses=witnesses, deepest_pruned=deepest[:5], unresolved_skeletons=unresolved,
                   result=("SURVIVING" if survivors_total else ("UNRESOLVED" if unresolved else "EXCLUDED")),
                   witness_verify_all=all(w["verify"]["all"][0] for w in witnesses) if witnesses else None)
        if survivors_total and unresolved: out["result"] = "SURVIVING (some skeletons unresolved)"
        # how the exclusion was obtained: by step S alone (LP), by step S with the integer filter, or by the geometry
        if out["result"] == "EXCLUDED":
            out["excluded_by"] = "step S (LP)" if not skels_lp else ("step S (LP + MILP)" if not skels else "step G (geometry)")
    out["seconds"] = round(time.time() - t0, 1); out["cpu_seconds"] = round(time.process_time() - cpu0, 1)
    if verbose: print(json.dumps({k: v for k, v in out.items() if k not in ("skeleton_list", "witnesses", "lp_pruned_vectors")}, indent=1))
    return out


def all_leaves():
    keys = [tuple(k) for k in json.load(open(HERE.parent / "scope/hypo_kill_Mt3.json"))["killed_keys_list"]]
    bounds = json.load(open(HERE / "lp_bounds.json"))
    tasks = []
    for key in keys:
        for a, d in bounds[str(key)]["open_leaves"]: tasks.append((key, a, d))
    return tasks


def _worker(task):
    key, a, d, opts = task
    res = run_leaf(key, a, d, max_store=opts["max_store"], max_survivors=opts["max_survivors"], estimate_only=opts["estimate_only"], avg=opts["avg"], leaf_cpu=opts["leaf_cpu"], skel_cpu=opts.get("skel_cpu", 25.0))
    outdir = Path(opts["out"]); outdir.mkdir(exist_ok=True)
    fn = outdir / ("leaf_%d_%d_%d_%d_a%d_d%d.json" % (key[0], key[1], key[2], key[5], a, d))
    json.dump(res, open(fn, "w"))
    return {k: v for k, v in res.items() if k not in ("skeleton_list", "witnesses", "lp_pruned_vectors", "deepest_pruned")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--max-store", type=int, default=20)
    ap.add_argument("--max-survivors", type=int, default=200)
    ap.add_argument("--leaf-cpu", type=float, default=60.0, help="CPU seconds per leaf for step G (0 = none); exceeding it gives UNRESOLVED")
    ap.add_argument("--skel-cpu", type=float, default=25.0, help="CPU seconds per skeleton (0 = none); a capped skeleton is recorded as timeout")
    ap.add_argument("--out", default=str(HERE / "results"))
    ap.add_argument("--leaf", nargs=3)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    geo = build_geo()
    t0 = time.time(); avg = averages(geo)
    print("candidate-count averages c_r over labels with rank >= k:", json.dumps({str(r): {str(k): round(v, 3) for k, v in d.items()} for r, d in avg.items() if r != "pr"}),
          "P(rank >= W | t triples):", json.dumps({str(t): {str(W): round(v, 5) for W, v in d.items()} for t, d in avg["pr"].items()}), f"({time.time()-t0:.0f}s)", flush=True)
    leaf_cpu = args.leaf_cpu if args.leaf_cpu > 0 else None
    if args.leaf:
        key = eval(args.leaf[0]); a = int(args.leaf[1]); d = int(args.leaf[2])
        res = run_leaf(key, a, d, max_store=args.max_store, max_survivors=args.max_survivors, estimate_only=args.estimate_only, avg=avg, verbose=True, leaf_cpu=leaf_cpu, skel_cpu=args.skel_cpu if args.skel_cpu > 0 else None)
        Path(args.out).mkdir(exist_ok=True)
        json.dump(res, open(Path(args.out) / ("leaf_%d_%d_%d_%d_a%d_d%d.json" % (key[0], key[1], key[2], key[5], a, d)), "w"))
        return
    tasks = all_leaves()
    if args.limit: tasks = tasks[:args.limit]
    opts = dict(max_store=args.max_store, max_survivors=args.max_survivors, estimate_only=args.estimate_only, avg=avg, out=args.out, leaf_cpu=leaf_cpu, skel_cpu=args.skel_cpu if args.skel_cpu > 0 else None)
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    results = []
    with ctx.Pool(args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(_worker, [(k, a, d, opts) for k, a, d in tasks])):
            results.append(res)
            print(f"[{i+1}/{len(tasks)}] {tuple(res['key'])} A={res['A']} qD={res['qD']} skeletons {res['skeletons']} "
                  f"{'est_ub %.3g est %.3g' % (res['est_ub'], res['est_refined']) if args.estimate_only else res['result'] + ' survivors ' + str(res['survivors']) + ' nodes ' + str(res['geo_stats'].get('nodes', 0) + res['geo_stats'].get('seg_nodes', 0))} "
                  f"cpu {res['cpu_seconds']}s", flush=True)
    summ = dict(tasks=len(tasks), results=results, wall_seconds=round(time.time() - t0), cpu_seconds=round(sum(r["cpu_seconds"] for r in results), 1))
    json.dump(summ, open(Path(args.out) / ("estimate_summary.json" if args.estimate_only else "run_summary.json"), "w"), indent=1)
    print("total cpu seconds", summ["cpu_seconds"], "wall", summ["wall_seconds"])
    if args.estimate_only:
        print("total est_ub %.4g  total est_refined %.4g" % (sum(r["est_ub"] for r in results), sum(r["est_refined"] for r in results)))
    else:
        print(Counter(r["result"] for r in results))


if __name__ == "__main__":
    main()
