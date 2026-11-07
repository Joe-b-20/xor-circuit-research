#!/usr/bin/env python3
"""(1) How well does the v3 signature track exact plateau identity, by plateau type
(all radices 3 vs a larger factor)?  (2) Exact plateaus (PES compress, single thread) of the
states behind the 5 multi-chain signatures."""
import json, os, sys, collections, time
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
sig = json.load(open(os.path.join(HUNT, "sigs2.json")))
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2p, PL = store["states"], store["plateaus"]

by_key = collections.defaultdict(set)
for h, (s, arm, w, wall) in sig.items():
    k = h2p.get(h)
    if k:
        by_key[k].add(s)
stats = collections.defaultdict(lambda: [0, 0, 0])
for k, ss in by_key.items():
    p = PL[k]
    typ = "giant" if p["kind"] != "product" else ("all-3" if all(r == 3 for r in p["radices"]) else
                                                   ("size<1e5" if p["size"] < 1e5 else "size>=1e5"))
    st = stats[typ]
    st[0] += 1
    st[1] += len(ss)
    st[2] += len(ss) > 1
for typ, (n, ns, nsplit) in sorted(stats.items()):
    print(f"type {typ:10s}: {n} exact plateaus -> {ns} signatures ({ns / n:.2f}x), {nsplit} split")

if len(sys.argv) > 1 and sys.argv[1] == "compress":
    sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
    import pes_lib
    sp = pes_lib.make_space("mc", None)
    cnt = collections.Counter(s for s, *_ in sig.values())
    vals = {}
    for spth in ("samples.jsonl", "samplesC/samples.jsonl"):
        for line in open(os.path.join(HUNT, spth)):
            r = json.loads(line)
            if r["gates"] == 88:
                vals[r["hash"]] = r["values"]
    # multi-chain signatures (from sigs.out)
    targets = [16808807829820689797, 7013781479831445689, 15988330789515842449, 10544030193955951398, 3258225461569467747]
    for s in targets:
        for h, (ss, arm, w, wall) in sig.items():
            if ss != s:
                continue
            helpers = [v for v in vals[h] if v not in sp.tset]
            st = sp.state(helpers)
            hk = sp.hkey(st)
            t0 = time.time()
            pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=3000, time_limit=120)
            allv = sorted(pl.allv) if pl.kind == "product" else None
            key = None
            if allv:
                key = min(sp.rot(tuple(allv), x) if x else tuple(allv) for x in sp.shifts)
                key = "p" + pes_lib.h64(key).to_bytes(8, "big").hex()
            print(f"sig {s} state {h} {arm}/{w}: kind {pl.kind} size {pl.size()} radices {pl.radices()} key {key} "
                  f"depth {st.depth()} ({time.time() - t0:.0f} s)", flush=True)
