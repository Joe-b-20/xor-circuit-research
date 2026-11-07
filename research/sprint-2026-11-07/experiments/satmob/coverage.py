import json, os, sys, glob, collections
sys.path.insert(0, "../sat"); import sat87
rows = [json.loads(l) for l in open("results.jsonl") if l.strip()]
by = collections.defaultdict(list)
for r in rows: by[r["circuit"]].append(r)
for cid, rs in by.items():
    uns = [r for r in rs if r["result"]=="UNSAT" and r.get("pool","full")=="full"]
    info = json.load(open("comp_%s.json" % cid.replace(":","_")))
    core = set(info["fan"]["core"]); mob = set(info["fan"]["mobile"])
    union = set()
    for r in uns: union |= set(r["W"])
    core_hit = core & union
    newW = sum(1 for r in uns if not r.get("prior_sat_campaign"))
    newW_vs_prior_timeout = sum(1 for r in uns if r.get("prior_sat_campaign") and r["prior_sat_campaign"][0]=="TIMEOUT")
    print("%s: %d UNSAT full-pool windows; union of W = %d of 88 values (mobile %d/%d, core %d/%d, outputs %d/32); %d windows with no identical sat/ record, %d where sat/ had only a TIMEOUT" % (cid, len(uns), len(union), len(mob&union), len(mob), len(core_hit), len(core), len(union & sat87.TSET), newW, newW_vs_prior_timeout))
