"""per cut: least far among circuits with no exit at that cut (and least far overall), witnesses."""
import sys, os, glob, json
import olib
HOME = os.path.expanduser("~/xor-circuit-research")
KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")

def sources():
    for f in ("xor88-depth5", "xor89-depth4", "xor97-depth3"):
        p = HOME + "/circuits/aes-mixcolumns/aes-mixcolumns-%s.circ.txt" % f
        yield "circuits/aes-mixcolumns/" + os.path.basename(p), 0, olib.parse_ncff(p)
    rot = HOME + "/research/structure-2026-11-11/rotation"
    for p in sorted(glob.glob(rot + "/**/*", recursive=True)):
        if not os.path.isfile(p) or not (p.endswith(".ncff") or p.endswith(".txt")):
            continue
        try:
            txt = open(p, errors="replace").read(200000)
        except Exception:
            continue
        if "XOR " not in txt or "x31" not in txt:
            continue
        try:
            g = olib.parse_ncff(p)
        except Exception:
            continue
        if g:
            yield os.path.relpath(p, HOME), 0, g
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
            if line.strip():
                yield "kste/" + fn, ln, olib.parse_pairs(line)

WP = [olib.W_info(olib.ROWS, olib.PBLOCK[b]) for b in range(8)]
WM = [olib.W_info(olib.MROWS, olib.MBLOCK[k]) for k in range(8)]
best = {}; bestany = {}; stats = dict(seen=0, mc=0, reduced=0, rot_mc=0)
def upd(d, key, cand):
    if key not in d or cand[0] < d[key][0]:
        d[key] = cand
for src, ln, g in sources():
    stats["seen"] += 1
    comp, red, _ = olib.check(g, olib.ROWS)
    if not comp:
        continue
    stats["mc"] += 1
    if src.startswith("research"):
        stats["rot_mc"] += 1
    if not red:
        continue
    stats["reduced"] += 1
    G = len(g)
    vals = olib.values(g)
    ops = [(vals[a], vals[b]) for a, b in g]
    cases = [("P", b, "-", vals, ops, olib.PBLOCK[b], WP[b]) for b in range(8)]
    for order in ("fwd", "rev"):
        Tm, Tops, outs = olib.transpose(g, olib.ROWS, order=order)
        rv, rops, rg = olib.reduce_mirror(Tm, Tops)
        cases += [("M", k, order, rv, rops, olib.MBLOCK[k], WM[k]) for k in range(8)]
    for kind, k, order, vv, oo, low, W in cases:
        st = olib.split(vv, oo, 32, low)
        assert olib.rank(st["labels"]) >= W["dimW"] and all(olib.in_span(st["labels"], s) for s in W["spart"])
        cand = (st["far"], src, ln, order, G, len(vv) - 32, st["f"], st["h"], st["e"], st["N"], st["x"],
                olib.rank(st["labels"]), st["e"] - W["dimW"])
        upd(bestany, (kind, k), cand)
        if st["x"] == 0:
            upd(best, (kind, k), cand)
print(json.dumps(stats))
print("W:", [(w["rows"], w["dimW"], w["oms"], w["nonunit_oms"]) for w in WP], [(w["rows"], w["dimW"], w["oms"], w["nonunit_oms"]) for w in WM])
print("fields: far src line order G |mirror| f h e N x labelrank sigma")
for key in sorted(best):
    print("exitfree", key, best[key])
    print("   any  ", key, bestany[key])
