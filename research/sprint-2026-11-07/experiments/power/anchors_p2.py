#!/usr/bin/env python3
"""Extra anchors: the q89check P2 population, 90@4 states carrying the 89@4's exact first layer, some of
which step down into the L0 family by one remove1 move (downs_into_L0 > 0) or by bounded BFS
(bfs_hit == 'L0').  Improvement = the nearest recorded 89@4 (q89check/c1_states_89.json, 90 states, all
rotations).  Appends up to 6 anchors (nearest first) with their sprint windows to anchors.json and
windows.json.  Run after anchors.py.  Usage: nice -n 8 python3 anchors_p2.py
"""
import sys, os, json, collections, time, hashlib
H = os.path.expanduser("~")
S = H + "/xs-campaigns/2026-11-07-sprint"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/sat")
sys.path.insert(0, HERE)
import sat87, run_scopes  # noqa: E402
from anchors import helpers, rotset, vkey, dist_stats, TSET, INPUTSET  # noqa: E402

REPO = H + "/xor-circuit-research/circuits/aes-mixcolumns"


def main():
    anchors = json.load(open(os.path.join(HERE, "anchors.json")))
    windows = json.load(open(os.path.join(HERE, "windows.json")))
    have = {a["id"] for a in anchors}
    repo89 = sat87.values_of(sat87.load_repo_circ(REPO + "/aes-mixcolumns-xor89-depth4.circ.txt"))
    L1 = frozenset(v for v in helpers(repo89) if bin(v).count("1") == 2)
    L1r = {s: rotset(L1, s) for s in range(4)}
    s89 = json.load(open(S + "/q89check/c1_states_89.json"))["states"]
    fam89 = {}
    for st in s89:
        v = sorted(set(st["helpers"]) | TSET)
        if len(v) == 89 and sat87.wiring_from_values(v) is not None:
            fam89[vkey(v)] = v
    cands = json.load(open(S + "/q89check/c3_result.json"))["candidates"]
    states = {}
    for c in cands:
        f = c["example"].replace("~", H)
        last = None
        for line in open(f):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if "values" in e and e.get("g") == 90 and e.get("d") == 4:
                vals = e["values"]
                hv = helpers(vals)
                l1 = frozenset(v for v in hv if bin(v).count("1") == 2)
                for s in range(4):
                    if l1 == L1r[s]:
                        # rotate into the repo frame (rot by -s)
                        vr = sorted(rotset(vals, (4 - s) % 4))
                        if len(set(vr)) == 90 and TSET <= set(vr) and sat87.wiring_from_values(vr) is not None:
                            last = vr
        if last is None:
            print("no matching 90@4 state in", f)
            continue
        states[vkey(last)] = (last, c)
    print("P2 states loaded:", len(states))
    rows = []
    for k, (vals, c) in states.items():
        best = None
        for name, v in fam89.items():
            d = dist_stats(vals, v)
            if best is None or (d["need_min"], d["sd_min"]) < (best[1]["need_min"], best[1]["sd_min"]):
                best = (name, d)
        rows.append((best[1]["need_min"], c["downs_into_L0"], k, best, c))
    rows.sort(key=lambda r: (-(r[1] > 0), r[0]))
    print("P2 anchors (k_needed to nearest 89@4, downs_into_L0, bfs_hit):", [(r[0], r[1], r[4]["bfs_hit"]) for r in rows])
    new = []
    for need, downs, k, best, c in rows[:6]:
        aid = "p2_90@4:" + k
        if aid in have:
            continue
        a = {"id": aid, "kind": "p2", "gates": 90, "values": states[k][0], "truth": {"id": "fam89:" + best[0], "values": fam89[best[0]]},
             "dist": best[1], "imp_note": "nearest recorded 89@4 (downs_into_L0=%d, bfs_hit=%s, in_B1=%s)" % (downs, c["bfs_hit"], c["in_B1"]),
             "n_imps": len(fam89)}
        new.append(a)
    log = []
    for a in new:
        vals = a["values"]
        order = sat87.wiring_from_values(vals)
        g, d, nd = sat87.check_circuit(order)
        assert g == 90 and nd == 90
        a["depth_anypair"] = d
        ah = helpers(vals)
        Mall = []
        for name, v in fam89.items():
            for s in range(4):
                M = ah - rotset(helpers(v), s)
                if len(M) <= 12:
                    Mall.append((name, s, M))
        Mtruth = [ah - rotset(helpers(a["truth"]["values"]), s) for s in range(4)]
        a["n_corpus_within12"] = len(Mall)
        seen = set()
        wrows = []
        for fam, kmax in (("A", 10), ("C", 12), ("B", 9)):
            t1 = time.time()
            for name, W in run_scopes.scopes(order, fam, None):
                kk = len(W)
                if kk > kmax or W in seen:
                    continue
                seen.add(W)
                Wh = frozenset(W) - TSET
                tw = sum(1 for t in sat87.TARGETS if t in W)
                cont_truth = any(M <= Wh for M in Mtruth)
                cc = [(n, s) for n, s, M in Mall if M <= Wh]
                wrows.append({"anchor": a["id"], "scope": name, "fam": fam, "k": kk, "tW": tw, "free": kk - 1 - tw, "W": sorted(W),
                              "contained_truth": cont_truth, "n_contained_corpus": len(cc), "contained_corpus_example": cc[0] if cc else None})
            a["n_%s" % fam] = sum(1 for r in wrows if r["fam"] == fam)
            a["sec_%s" % fam] = round(time.time() - t1, 1)
        a["n_windows"] = len(wrows)
        a["n_contained_truth"] = sum(r["contained_truth"] for r in wrows)
        a["n_contained_corpus"] = sum(1 for r in wrows if r["n_contained_corpus"])
        a["kmax_A"] = max([r["k"] for r in wrows if r["fam"] == "A"] or [0])
        windows += wrows
        anchors.append(a)
        msg = ("%-28s %s g=%d need0=%d sd0=%d need_min=%d | windows A=%d C=%d B=%d | contained(truth)=%d contained(any 89@4)=%d | %s"
               % (a["id"], a["kind"], a["gates"], a["dist"]["need0"], a["dist"]["sd0"], a["dist"]["need_min"], a["n_A"], a["n_C"], a["n_B"],
                  a["n_contained_truth"], a["n_contained_corpus"], a["imp_note"]))
        print(msg); log.append(msg)
    json.dump(anchors, open(os.path.join(HERE, "anchors.json"), "w"))
    json.dump(windows, open(os.path.join(HERE, "windows.json"), "w"))
    with open(os.path.join(HERE, "part1.txt"), "a") as f:
        for m in log:
            f.write("[p2] " + m + "\n")
    print("anchors now", len(anchors), "windows", len(windows))


if __name__ == "__main__":
    main()
