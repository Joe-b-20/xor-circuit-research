#!/usr/bin/env python3
"""Idea-04 paired A/B: treatment (new kernel + options) and control (08012e1 kernel, or new kernel + options) run AT
THE SAME TIME on CPUs 6 and 7 (placement alternates with the seed), same start, same seed, same CPU budget (clock cpu).

    python3 ab.py LABEL SECONDS SEEDS "k=v,..." ["k=v,..." control] [starts] [control_binary: base|new]
Rows -> runs/LABEL.jsonl; run dirs kept in runs/LABEL/ (configs, logs, out.bfx, keep_bests for the treatment).
"""
import json, re, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
label, secs, nseeds = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
kv = lambda x: dict(p.split("=", 1) for p in x.split(",") if p) if x else {}
treat = kv(sys.argv[4]); control = kv(sys.argv[5]) if len(sys.argv) > 5 else {}
want = sys.argv[6].split(",") if len(sys.argv) > 6 and sys.argv[6] else None
cbin = H / "bin" / ("bfx-" + (sys.argv[7] if len(sys.argv) > 7 else "base"))
tbin = H / "bin/bfx-new"
DEF = {"T0": 0.6, "Tperiod_it": 20000, "stall_it": 60000, "uphill": 1.0, "max_excess": 8, "mv.resub1": 1, "mv.resub2": 2,
       "mv.resub3": 1, "dmax": 220, "pdiv": 90, "nl_samples": 12, "cand_cap": 40, "fraig": 1, "repair_keep": 1,
       "cost.8": 1, "cost.6": 1, "cost.9": 1, "cost.3": 1, "lex": "cost,gd", "w.cost": 1, "w.gd": 1e-4}
def starts():
    S = {}
    w1 = {}
    for ln in (H / "smoke/w1.base.cfg").read_text().splitlines():
        a, b = ln.split(None, 1); w1[a] = b.strip()
    S["W1"] = ((H / "smoke/w1.start.bfx").read_text(), w1)
    for p in sorted((H / "starts").glob("*.bfx")):
        c = dict(DEF)
        for ln in p.with_suffix(".caps").read_text().splitlines():
            a, b = ln.split(); c[a] = b
        S[p.stem] = (p.read_text(), c)
    return S
D = H / "runs" / label; D.mkdir(parents=True, exist_ok=True)
def launch(binp, text, cfg, extra, seed, cpu, tag):
    d = D / tag; d.mkdir(exist_ok=True)
    (d / "in.bfx").write_text(text)
    c = dict(cfg); c.update({"in": d / "in.bfx", "out": d / "out.bfx", "seed": seed, "seconds": secs, "clock": "cpu"})
    c.update(extra)
    (d / "k.cfg").write_text("".join("%s %s\n" % x for x in c.items()))
    f = open(d / "log", "w")
    return subprocess.Popen(["taskset", "-c", str(cpu), str(binp), str(d / "k.cfg")], stdout=f, stderr=subprocess.STDOUT), d, f
def parse(d):
    t = (d / "log").read_text()
    st = re.search(r"^start cost (\S+) G (\d+) A (\d+) GD (\d+) AD (\d+) feas (\d)", t, re.M)
    fi = re.search(r"^final cost (\S+) G (\d+) A (\d+) GD (\d+) AD (\d+) obj (\S+) feas (\d) iters (\d+)", t, re.M)
    bl = re.findall(r"^best t \S+ it (\d+) mv (\S+) cost \S+ G (\d+) A (\d+) GD (\d+) AD (\d+).*\nkstat best it \d+ treal \S+ cpu (\S+)", t, re.M)
    key = lambda feas, A, AD, G, GD: [1 - int(feas), int(A), int(AD), int(G), int(GD)]
    ch = re.search(r"^kstat chain .*", t, re.M)
    return {"start": key(st.group(6), st.group(3), st.group(5), st.group(2), st.group(4)),
            "final": key(fi.group(7), fi.group(3), fi.group(5), fi.group(2), fi.group(4)), "iters": int(fi.group(8)),
            "bests": [(int(b[0]), b[1], int(b[2]), int(b[4]), float(b[6])) for b in bl], "chain": ch.group(0) if ch else None}
S = starts(); names = [n for n in S if (n in want if want else True)]
out = open(H / "runs" / (label + ".jsonl"), "a")
print("A/B %s: T %s (%s) vs C %s (%s), %g CPU-s, %d seeds, starts %s" % (label, treat, tbin.name, control, cbin.name, secs, nseeds, ",".join(names)), flush=True)
rows = []
for seed in range(1, nseeds + 1):
    for n in names:
        text, cfg = S[n]
        tc, cc = (6, 7) if seed % 2 else (7, 6)
        pt, dt, ft = launch(tbin, text, cfg, treat, 200 + seed, tc, "%s-s%d-T" % (n, seed))
        pc, dc, fc = launch(cbin, text, cfg, control, 200 + seed, cc, "%s-s%d-C" % (n, seed))
        pt.wait(); pc.wait(); ft.close(); fc.close()
        rt, rc = parse(dt), parse(dc)
        r = {"label": label, "start": n, "seed": seed, "T": rt, "C": rc, "treat": treat, "control": control}
        rows.append(r); out.write(json.dumps(r) + "\n"); out.flush()
        cmp = "T" if rt["final"] < rc["final"] else "C" if rc["final"] < rt["final"] else "="
        print("%-3s s%d start %s  T %s C %s  %s  it T %d C %d  nbest T %d C %d  %s" % (n, seed, rt["start"], rt["final"], rc["final"], cmp,
              rt["iters"], rc["iters"], len(rt["bests"]), len(rc["bests"]), (rt["chain"] or "")[12:150]), flush=True)
w = sum(r["T"]["final"] < r["C"]["final"] for r in rows); l = sum(r["T"]["final"] > r["C"]["final"] for r in rows)
ti = sum(r["T"]["final"] < r["T"]["start"] for r in rows); ci = sum(r["C"]["final"] < r["C"]["start"] for r in rows)
print("SUMMARY %s: pairs %d, T better %d, worse %d, equal %d; improved over start T %d C %d" % (label, len(rows), w, l, len(rows) - w - l, ti, ci))
