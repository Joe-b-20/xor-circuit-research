#!/usr/bin/env python3
"""One budgeted ABC run: a sequence of ABC processes ("steps"), each = optimisation body +
a portfolio of four standard-cell mappings, all pinned to one CPU by the caller.

Every mapped netlist is converted to NCFF (netconv.py) and, if it beats the current best,
checked with the independent verifier (verify.py, exhaustive, with the cost model).
Only verified netlists count. Time to best = mtime of the winning mapped BLIF - run start.

Flows (state between steps = one AIG file, cur_k.aig):
  classic  step 0: strash(start).  step k>=1: read best mapped netlist so far; strash; dc2;
           resyn2; compress2rs; dc2.  Deterministic: stops after 3 consecutive steps without a new best.
  deepsyn  step 0 as above. step k>=1: &r cur_{k-1}; &deepsyn -T <chunk> -S (20*seed+k)%101
  eslim    step 0 as above. step 1: dc2; resyn2 first; every step k>=1:
           &eslim -x -t -f -Z 1000*seed+k -T <chunk> -V 0
Mapping portfolio on cur_k.aig (each from a fresh &r):
  m1: &put; map -a            m2: &put; dch -f; map -a
  m3: &put; dch -f; amap      m4: &dch -f; &nf -p; &put
  m5: &nf -p -k; &put   (last: it aborts ABC with an assertion on many inputs)
"""
import shutil
import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MAPPERS = {
    "m1": "&put; map -a",
    "m2": "&put; dch -f; map -a",
    "m3": "&put; dch -f; amap",
    "m4": "&dch -f; &nf -p; &put",
    "m5": "&nf -p -k; &put",  # XOR/MUX coarsening; often hits an assertion in giaNf.c, so last
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--abc", required=True)
    ap.add_argument("--rc", required=True)
    ap.add_argument("--lib", required=True)
    ap.add_argument("--start", required=True, help="BLIF to start from")
    ap.add_argument("--fn", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--verify", required=True)
    ap.add_argument("--flow", choices=["classic", "deepsyn", "eslim"], required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--chunk", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra-verify", default="", help="extra verify.py flag, e.g. --aes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    out = os.path.abspath(a.out)
    t0 = time.time()
    best = {"G": None}
    events, peak_kb, k, stale, eval_cost = [], 0, 0, 0, 1.0
    killed_steps = 0
    rcs = []

    def P(name):
        return os.path.join(out, name)

    while True:
        rem = a.budget - (time.time() - t0)
        if rem < 0.5:
            break
        cur = P(f"cur_{k}.aig")
        if k == 0:
            body = f"read_blif {a.start}; strash; &get -n; &w {cur}"
        elif a.flow == "classic":
            body = f"read_blif {best['blif']}; strash; dc2; resyn2; compress2rs; dc2; &get -n; &w {cur}"
        else:
            T = max(1, int(min(a.chunk, rem - eval_cost - 1)))
            prev = P(f"cur_{k-1}.aig")
            if a.flow == "deepsyn":
                body = f"&r {prev}; &deepsyn -T {T} -S {(20 * a.seed + k) % 101}; &w {cur}"
            else:
                pre = "&put; dc2; resyn2; &get -n; " if k == 1 else ""
                body = (f"&r {prev}; {pre}&eslim -x -t -f -Z {1000 * a.seed + k} -T {T} -V 0; "
                        f"&w {cur}")
        evals = "; ".join(f"&r {cur}; {cmd}; write_blif {P(f'step{k}_{m}.blif')}"
                          for m, cmd in MAPPERS.items())
        script = f"source {a.rc}; read_library {a.lib}; {body}; {evals}; quit\n"
        with open(P(f"step{k}.abc"), "w", encoding="utf-8", newline="\n") as f:
            f.write(script)
        ts = time.time()
        # GNU time records peak memory; without it the step runs untimed and memory is not recorded
        time_bin = "/usr/bin/time" if os.path.exists("/usr/bin/time") else shutil.which("time")
        cmd = ([time_bin, "-v", "-o", P(f"step{k}.time")] if time_bin else []) + [
            "timeout", "-s", "KILL", f"{max(rem, 0.5):.2f}", a.abc, "-f", P(f"step{k}.abc")]
        with open(P(f"step{k}.log"), "w") as lf:
            rc = subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT)
        te = time.time()
        if rc != 0:
            killed_steps += 1
            rcs.append([k, rc])
        try:
            tv = open(P(f"step{k}.time")).read()
            m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", tv)
            if m:
                peak_kb = max(peak_kb, int(m.group(1)))
        except OSError:
            pass
        improved = False
        for mname in MAPPERS:
            bl = P(f"step{k}_{mname}.blif")
            if not os.path.exists(bl) or not open(bl).read().rstrip().endswith(".end"):
                continue
            nc = bl[:-5] + ".circ.txt"
            r = subprocess.run([sys.executable, os.path.join(HERE, "netconv.py"), "blif2ncff", bl, nc],
                               capture_output=True, text=True)
            if r.returncode != 0:
                events.append({"step": k, "mapper": mname, "error": r.stdout + r.stderr})
                continue
            nlines = sum(1 for ln in open(nc) if ln.split() and ln.split()[0] in
                         ("AND", "OR", "XOR", "XNOR", "NAND", "NOR", "NOT"))
            tbest = os.path.getmtime(bl) - t0
            ev = {"step": k, "mapper": mname, "G_lines": nlines, "t": round(tbest, 2)}
            if best["G"] is None or nlines < best["G"]:
                vcmd = [sys.executable, a.verify, nc, "--fn", a.fn, "--model", a.model, "--json"]
                if a.extra_verify:
                    vcmd.append(a.extra_verify)
                    vcmd = [x for x in vcmd if x not in ("--fn", a.fn)]
                vr = subprocess.run(vcmd, capture_output=True, text=True)
                res = json.loads(vr.stdout)[0]
                ev["verified"] = res["ok"]
                if res["ok"] and (best["G"] is None or res["metrics"]["G"] < best["G"]):
                    best = {"G": res["metrics"]["G"], "t": round(tbest, 2), "step": k,
                            "mapper": mname, "blif": bl, "ncff": nc, "metrics": res["metrics"],
                            "notes": [ln.strip() for ln in open(nc) if ln.startswith("% note")]}
                    improved = True
                elif not res["ok"]:
                    ev["errors"] = res["errors"]
            events.append(ev)
        eval_cost = max(1.0, min(30.0, te - ts if k == 0 else eval_cost))
        stale = 0 if improved else stale + 1
        k += 1
        if a.flow == "classic" and stale >= 3:
            break
        if best["G"] is None and k == 1:
            break  # step 0 failed entirely
    summary = {"flow": a.flow, "seed": a.seed, "budget": a.budget, "chunk": a.chunk,
               "lib": os.path.basename(a.lib), "start": a.start, "steps": k,
               "killed_steps": killed_steps, "nonzero_rc": rcs,
               "total_time": round(time.time() - t0, 2), "peak_rss_kb": peak_kb,
               "best": best, "events": events}
    with open(P("summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({x: summary[x] for x in ("flow", "seed", "steps", "total_time")} |
                     {"G": best.get("G"), "t_best": best.get("t")}))


if __name__ == "__main__":
    main()
