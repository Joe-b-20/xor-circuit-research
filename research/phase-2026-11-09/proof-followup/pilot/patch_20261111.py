#!/usr/bin/env python3
"""patch_20261111.py -- the edits applied to enum_q3.py on 2026-11-11 (the pass-1 code is kept as enum_q3_pass1_snapshot.py).

1. guide hooks (P5 control only; guide=None in every enumeration, behaviour unchanged);
2. FIX: in multi-segment skeletons the product phase placed EVERY r = 0, u >= 2 helper of the order, including those already
   placed inside a segment (placed twice -> a possible false 'no combination', i.e. a possible false exclusion of the
   skeleton).  Now it places only the deferred ones (pl['riders2']);
3. the internal stops 'no_concrete_role' / 'rider_no_concrete_slot' give status 'error' (never 'done').
Run once; it asserts that every pattern occurs exactly once.
"""
from pathlib import Path
p = Path(__file__).with_name("enum_q3.py"); s = p.read_text()


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


rep("    def __init__(self, geo, pl, order, max_store=20, max_survivors=None, deadline=None, init=None):\n        self.geo = geo; self.pl = pl",
    "    def __init__(self, geo, pl, order, max_store=20, max_survivors=None, deadline=None, init=None, guide=None):\n        self.geo = geo; self.pl = pl\n"
    "        self.guide = guide       # P5 control only: restricts branches to a planted target (never used in the enumeration)")
rep("            for l in cand:\n                if l in self.labset: continue\n                self.lab[s0] = l; self.labset.add(l)\n                self.attach(k, i, self.viable(i, -1), rest)",
    "            for l in cand:\n                if l in self.labset: continue\n                if self.guide is not None and not self.guide.ok_root(s0, l): continue\n"
    "                self.lab[s0] = l; self.labset.add(l)\n                self.attach(k, i, self.viable(i, -1), rest)")
rep("        for b, h, T, ends in cands or []:\n            Rs = [tuple(T)] if r == 3 else ([()] if r == 0 else list(itertools.combinations(T, r)))\n            for R in Rs:\n                vs = [t | hk for t in R]",
    "        g = self.guide\n        for b, h, T, ends in cands or []:\n            if g is not None and not g.ok_mask(self.roles[i], h): continue\n"
    "            Rs = [tuple(T)] if r == 3 else ([()] if r == 0 else list(itertools.combinations(T, r)))\n            for R in Rs:\n"
    "                if g is not None and not g.ok_helper(self.roles[i], h, R): continue\n                vs = [t | hk for t in R]")
rep('            if not dark and rankC.get(l, 0) < W: st["prune_rank"] += 1; continue\n            self.lab[s] = l;',
    '            if not dark and rankC.get(l, 0) < W: st["prune_rank"] += 1; continue\n            if self.guide is not None and not self.guide.ok_label(s, l): continue\n            self.lab[s] = l;')
rep("def run_skeleton(geo, pl, max_store, max_survivors, deadline, seg_cap=300_000, combo_cap=300_000):",
    "def run_skeleton(geo, pl, max_store, max_survivors, deadline, seg_cap=300_000, combo_cap=300_000, guide=None):")
rep('    rider_entries = [e for e in pl["order"] if pl["roles"][e[0]][0] == 0]\n    if len(segs) <= 1:',
    "    # FIX (2026-11-11): the product phase places ONLY the deferred r = 0, u >= 2 helpers (pl['riders2']); those placed\n"
    "    # inside a segment are already part of the segment realizations.  The pass-1 code took every r = 0 entry of the\n"
    "    # order and so placed in-segment riders twice (a possible false 'no combination').\n"
    '    n_seg_entries = sum(len(seg["order"]) for seg in segs)\n'
    '    rider_entries = list(pl["order"][n_seg_entries:])\n'
    '    assert all(pl["roles"][e[0]][0] == 0 for e in rider_entries) and [e[0] for e in rider_entries] == list(pl["riders2"])\n'
    '    def bad(R): return bool(R.stats.get("no_concrete_role") or R.stats.get("rider_no_concrete_slot"))\n'
    "    if len(segs) <= 1:")
rep('        R = Realizer(geo, pl, pl["order"], max_store=max_store, max_survivors=max_survivors, deadline=deadline); R.run()\n'
    '        return dict(mode="single", survivors=R.stats["survivors"], snaps=R.survivors, stats=dict(R.stats), depth=dict(R.depth_nodes),\n'
    '                    deepest=R.deepest, status="timeout" if R.timed_out else "done", seg_counts=[R.stats["survivors"]])',
    '        R = Realizer(geo, pl, pl["order"], max_store=max_store, max_survivors=max_survivors, deadline=deadline, guide=guide); R.run()\n'
    '        return dict(mode="single", survivors=R.stats["survivors"], snaps=R.survivors, stats=dict(R.stats), depth=dict(R.depth_nodes),\n'
    '                    deepest=R.deepest, status="error" if bad(R) else ("timeout" if R.timed_out else "done"), seg_counts=[R.stats["survivors"]])')
rep('        R = Realizer(geo, pl, seg["order"], max_store=seg_cap, max_survivors=seg_cap, deadline=deadline); R.run()\n'
    '        for k2, v in R.stats.items(): st["seg_" + k2] += v\n        deepest += R.deepest\n        if R.timed_out:',
    '        R = Realizer(geo, pl, seg["order"], max_store=seg_cap, max_survivors=seg_cap, deadline=deadline, guide=guide); R.run()\n'
    '        for k2, v in R.stats.items(): st["seg_" + k2] += v\n        deepest += R.deepest\n'
    '        if bad(R): return dict(mode="segments", survivors=0, snaps=[], stats=dict(st), depth={}, deepest=deepest, status="error", seg_counts=seg_counts)\n'
    "        if R.timed_out:")
rep('        R = Realizer(geo, pl, rider_entries, max_store=max_store, max_survivors=1, deadline=deadline, init=dict(labels=labels, helpers=helpers))\n'
    '        if not R.init_ok: st["combo_R7"] += 1; continue\n        R.run()\n        for k2, v in R.stats.items(): st["prod_" + k2] += v\n        if R.timed_out: status = "timeout"; break',
    '        R = Realizer(geo, pl, rider_entries, max_store=max_store, max_survivors=1, deadline=deadline, init=dict(labels=labels, helpers=helpers), guide=guide)\n'
    '        if not R.init_ok: st["combo_R7"] += 1; continue\n        R.run()\n        for k2, v in R.stats.items(): st["prod_" + k2] += v\n'
    '        if bad(R): status = "error"; break\n        if R.timed_out: status = "timeout"; break')
p.write_text(s)
print("patched enum_q3.py")
