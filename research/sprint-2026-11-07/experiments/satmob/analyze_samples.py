import mob, collections, json, sys
cids = sys.argv[1:]
for cid in cids:
    order, info = mob.analyze(cid, write=True)
    for lv in ["1", "2", "3"]:
        items = mob.items_for(order, info["components"], [lv])
        c = collections.Counter((len(r["W"]), len(r["W"]) - 1 - r["tW"]) for r in items)
        print("   level", lv, len(items), "instances; (k,free)", sorted(c.items()))
