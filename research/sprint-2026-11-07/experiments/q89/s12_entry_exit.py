"""s12_entry_exit.py: (a) the shelf member v9c mc-cap4-04 restarted onto before reaching 89@4 (08226d6b72c8): its
level-1 set vs the 89's under the 4 byte rotations; (b) the restart time; (c) the first layers of the uncapped
mc87 from89 workers' 88-gate records (depth 6-9) vs the 89's L1. Pure python, seconds."""
import glob
import gzip
import json
import os
from collections import Counter

HOME = os.path.expanduser("~")
Q = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")
N = 32
st = json.load(open(os.path.join(Q, "s7_structure.json")))
L1_main = set(st["L1_main"])
INPUTS = [1 << i for i in range(N)]
MAT = os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
lines = [l.strip() for l in open(MAT) if l.strip()]
T = []
for l in lines[2:2 + 32]:
    v = 0
    for j, ch in enumerate(l.replace(" ", "")):
        if ch == "1":
            v |= 1 << j
    T.append(v)
TSET = set(T)


def rot(v, s):
    return ((v << s) | (v >> (N - s))) & ((1 << N) - 1)


def vals(rec):
    g = rec.get("gates") or rec.get("circuit")
    val = list(INPUTS)
    for a, b in g:
        val.append(val[a] ^ val[b])
    return val[N:]


def name(v):
    return "x" + "+x".join(str(i) for i in range(N) if v >> i & 1)


def l1_of(rec):
    return {v for v in vals(rec) if bin(v).count("1") == 2}


def l1_report(tag, L1):
    best = max(((len(L1 & {rot(v, s) for v in L1_main}), s) for s in (0, 8, 16, 24)))
    print(f"{tag}: |L1|={len(L1)} best overlap with 89 L1 = {best[0]} at rotation {best[1]}; "
          f"missing {[name(v) for v in {rot(v, best[1]) for v in L1_main} - L1]} extra {[name(v) for v in L1 - {rot(v, best[1]) for v in L1_main}]}")


# (a) shelf member
hits = [f for f in glob.glob(os.path.join(HOME, "xs-campaigns/2026-11-04-12h/runs/v9c/**/*08226d6b72c8*"), recursive=True)]
print("shelf member files:", hits[:5])
for f in hits[:2]:
    try:
        d = json.load(open(f))
    except Exception as e:
        print("  unreadable", f, e)
        continue
    rec = d.get("record") or d.get("circuit") or d
    if "gates" in rec or "circuit" in rec:
        print("  gates", rec.get("gateCount"), "depth", rec.get("depth"), "keys", list(d.keys())[:12])
        l1_report("  shelf 08226d6b72c8", l1_of(rec))
    else:
        print("  keys", list(d.keys())[:20])
# the shelf directory in general
sh = glob.glob(os.path.join(HOME, "xs-campaigns/2026-11-04-12h/runs/v9c/shelf*")) + glob.glob(os.path.join(HOME, "xs-campaigns/2026-11-04-12h/runs/v9c/*/shelf*"))
print("shelf dirs:", sh[:5])

# (b) restart time of mc-cap4-04
w = os.path.join(HOME, "xs-campaigns/2026-11-04-12h/runs/v9c/workers/mc-cap4-04")
ev = os.path.join(w, "events.jsonl")
opener = gzip.open if ev.endswith(".gz") else open
if not os.path.exists(ev) and os.path.exists(ev + ".gz"):
    ev += ".gz"
    opener = gzip.open
n = 0
if os.path.exists(ev):
    with opener(ev, "rt") as fh:
        for line in fh:
            if "08226d6b72c8" in line or '"restart"' in line or "shelf" in line:
                e = json.loads(line)
                t = e.get("t")
                if t is None or t > 7000:
                    continue
                if t > 6000:
                    print("  event", json.dumps(e)[:400])
                    n += 1
                    if n > 12:
                        break
print("chain.json:", json.dumps(json.load(open(os.path.join(w, "chain.json"))))[:800] if os.path.exists(os.path.join(w, "chain.json")) else "none")

# (c) from89 88-gate records
fs = [f for f in glob.glob(os.path.join(HOME, "xs-campaigns/2026-11-04-mc87/runs/mc87/workers/from89-*/records/g88-d*.json")) if not f.endswith(".verification.json")]
print("from89 88-gate records:", len(fs))
ov = Counter()
sizes = Counter()
first = {}
for f in fs:
    d = json.load(open(f))
    L1 = l1_of(d)
    best = max(len(L1 & {rot(v, s) for v in L1_main}) for s in (0, 8, 16, 24))
    ov[best] += 1
    sizes[len(L1)] += 1
    wname = f.split("workers/")[1].split("/")[0]
    t = (d.get("metadata") or {}).get("t")
    if wname not in first or (t is not None and t < first[wname][0]):
        first[wname] = (t, d.get("depth"), best, len(L1), (d.get("metadata") or {}).get("move"))
print("  |L1| hist:", dict(sorted(sizes.items())), " best overlap with 89 L1 hist:", dict(sorted(ov.items())))
print("  first 88 per worker (t, depth, overlap, |L1|, move):", first)
# and the from89 89@4 records: in L0? (L1 equal?)
fs89 = [f for f in glob.glob(os.path.join(HOME, "xs-campaigns/2026-11-04-mc87/runs/mc87/workers/from89-*/records/g89-d4-*.json")) if not f.endswith(".verification.json")]
print("  from89 89@4 records with exactly the 89 L1:", sum(1 for f in fs89 if l1_of(json.load(open(f))) == L1_main), "of", len(fs89))
