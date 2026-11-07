import json, sys, time
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib
sp = pes_lib.make_space("mc", None)
E = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants/entries.json"))
for e in E[:3]:
    S = frozenset(e["seed"])
    t = time.time(); g, d, n, dn, b = pes_lib.fan(sp, S); dt = time.time() - t
    print(e["key"], "gates", g, "depth", d, "neutral", len(n), "downs", len(dn), "fan s %.3f" % dt,
          "moved-value sizes", sorted(len(R | A) for R, A, k, dep in n)[:30], flush=True)
