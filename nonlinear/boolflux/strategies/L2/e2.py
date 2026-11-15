"""Lineage of every admitted circuit in track E long1/low1 (pre-hub).  Read-only."""
import json, os, sys, hashlib, glob
sys.path.insert(0, os.path.expanduser("~/xcr-boolflux/nonlinear/boolflux/strategies/E"))
from common import core, load, metrics, correct
B = os.path.expanduser("~/xs-campaigns/2026-11-13-aes/E/")
inp = {}   # hash -> (file, m)
for fl in ("long1/files.list", "low1/files.list"):
    for f in open(B + fl).read().split():
        try:
            c = load(f)
        except Exception as x:
            print("LOADFAIL", f, x); continue
        h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:16]
        inp.setdefault(h, (f, tuple(metrics(c))))
print("inputs hashed", len(inp))
adm = {}
for arm in ("long1/splice", "long1/control", "low1/run"):
    for j in glob.glob(B + arm + "/admitted/*.json"):
        h = os.path.basename(j)[:-5]
        d = json.load(open(j)); d["arm"] = arm
        adm.setdefault(h, d)
def short(f):
    f = os.path.basename(f)
    return f.replace(".circ.txt", "").replace("aes-sbox-", "N:").replace("aes-nist-", "R:")
def name(h, depth=0):
    if h in adm and depth < 12:
        return "[%s %s]" % ("/".join(map(str, adm[h]["metrics"])), desc(adm[h]["origin"], depth + 1))
    if h in inp:
        return "{%s %s}" % (short(inp[h][0]), "/".join(map(str, inp[h][1])))
    return "<%s?>" % h
def desc(o, depth=0):
    k = o["kind"]
    if k == "input": return "input " + short(o["file"])
    if k == "splice":
        return "JOIN(front=%s LX=%s, back=%s LY=%s, if=%s)" % (name(o["front"], depth), o["LX"], name(o["back"], depth), o["LY"], o["interface"])
    if k == "polish":
        caps = o.get("caps") or {}
        kind = "PULL" if caps.get("tag") else "POLISH"
        return "%s(seed=%s caps=%s t=%s of %ss from %s <- %s)" % (kind, o["seed"], {a: b for a, b in caps.items() if a != "tag"}, o.get("time_to_result_s"), o.get("seconds"), "/".join(map(str, o.get("from_m", []))), desc(o["from_origin"], depth + 1) if "from_origin" in o else name(o["from"], depth))
    return str(o)
json.dump({h: {"file": v[0], "m": v[1]} for h, v in inp.items()}, open(B.replace("2026-11-13-aes/E/", "2026-11-15-study/L2/") + "e_inputs.json", "w"))
rows = sorted(adm.items(), key=lambda kv: tuple(kv[1]["metrics"]))
for h, d in rows:
    print("%s  %s  %s\n     %s" % ("/".join(map(str, d["metrics"])), d["arm"], h, desc(d["origin"])))
