"""c0_probe.py: learn file locations and record formats (read-only)."""
import glob, json, os, sys
from collections import Counter
HOME = os.path.expanduser("~")

def census(g):
    fs = glob.glob(f"{HOME}/xs-campaigns/**/g{g}-d4-*.json", recursive=True)
    fs = [f for f in fs if "/import/" not in f and not f.endswith(".verification.json")]
    c = Counter(f.split("xs-campaigns/")[1].split("/")[0] for f in fs)
    print(f"g{g}-d4 files total {len(fs)}:", dict(c))
    return fs

f89 = census(89)
f90 = census(90)
# sample record formats
seen = set()
for f in f89 + f90:
    camp = f.split("xs-campaigns/")[1].split("/")[0]
    if camp in seen:
        continue
    seen.add(camp)
    try:
        r = json.load(open(f))
    except Exception as e:
        print("UNREADABLE", f, e); continue
    desc = {k: (v if not isinstance(v, (list, dict)) else type(v).__name__ + str(len(v))) for k, v in r.items()}
    print("SAMPLE", camp, os.path.basename(f), desc)
    g = r.get("gates") or r.get("circuit")
    print("   gates[:3]", str(g)[:120] if g else None, " values[:3]", str(r.get("values"))[:80])

# repo circ
p = f"{HOME}/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt"
lines = [l.rstrip("\n") for l in open(p)]
body = [l for l in lines if l.strip() and not l.lstrip().startswith("%") and not l.startswith("##")]
print("CIRC body lines", len(body)); print("\n".join(body[:6])); print("..."); print("\n".join(body[-4:]))
print("CIRC header-ish lines with 'input' or 'output':")
for l in lines:
    if "nput" in l or "utput" in l:
        print("  ", l[:120])

for d in ["2026-11-02-why/foundations/out", "2026-11-03-waits/repair", "2026-11-06-89at4", "2026-11-03-12h/foundation", "2026-11-04-12h/foundation2"]:
    full = f"{HOME}/xs-campaigns/{d}"
    print("DIR", d, os.path.isdir(full))
    if os.path.isdir(full):
        ents = sorted(os.listdir(full))
        print("   ", len(ents), ents[:25])
# any json with 90 gates depth 4 in the foundation-type dirs
for d in ["2026-11-02-why/foundations/out", "2026-11-03-waits/repair", "2026-11-03-12h/foundation", "2026-11-04-12h/foundation2", "2026-11-06-89at4"]:
    full = f"{HOME}/xs-campaigns/{d}"
    js = glob.glob(full + "/**/*.json", recursive=True)
    names = Counter(os.path.basename(x).split("-")[0] if "-" in os.path.basename(x) else os.path.basename(x) for x in js)
    print("JSON in", d, len(js), dict(list(names.items())[:15]))
    for x in js[:3]:
        print("     e.g.", x.replace(HOME, "~"))
