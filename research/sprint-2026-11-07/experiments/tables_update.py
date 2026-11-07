#!/usr/bin/env python3
"""After harvest_sprint.py --apply: update circuits/README.md map rows and circuits/SEARCH-TIME.md
(run rows, circuit rows) from git status + each new circuit's logs/<name>/found.json.
Run from the repository root.  Usage: tables_update.py [--write]
"""
import glob, json, os, re, subprocess, sys

REPO = os.path.expanduser("~/xor-circuit-research")
os.chdir(REPO)
WRITE = "--write" in sys.argv
RUN_DIRS = {}
for base in ("x1/runs/x1a", "x1/runs/x1b", "predtest/runs/pt1", "predtest/runs/pt2", "sweep/runs/sw1", "sweep/runs/sw2"):
    p = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/" + base)
    if os.path.exists(p + "/plan.json"):
        RUN_DIRS[json.load(open(p + "/plan.json"))["name"]] = p

st = subprocess.run(["git", "status", "--porcelain", "circuits"], capture_output=True, text=True).stdout
adds, removes = [], []
for line in st.splitlines():
    code, f = line[:2], line[3:]
    m = re.search(r"circuits/([^/]+)/\1-xor(\d+)-depth(\d+)\.circ\.txt$", f)
    if not m:
        continue
    item = (m.group(1), int(m.group(2)), int(m.group(3)))
    if code.strip() == "??" or code[0] == "A":
        adds.append(item)
    elif "D" in code:
        removes.append(item)
print("adds", len(adds), "removes", len(removes))


def fmt_t(sec):
    if sec is None:
        return "?"
    if sec < 60:
        return f"{sec:.0f} s"
    if sec < 3600:
        return f"{sec / 60:.0f} min"
    return f"{sec / 3600:.1f} h"


def fmt_cpu(sec):
    if sec is None:
        return "?"
    if sec < 60:
        return "< 1 min"
    return fmt_t(sec)


_ev = {}


def events(run, w):
    k = (run, w)
    if k not in _ev:
        _ev[k] = [json.loads(l) for l in open(f"{RUN_DIRS[run]}/workers/{w}/events.jsonl")]
    return _ev[k]


# ---------------- runs
runs_info = {}
for name, p in RUN_DIRS.items():
    sess = [json.load(open(f)) for f in glob.glob(p + "/sessions/*.json")]
    ws = os.listdir(p + "/workers")
    wall = sum(s.get("elapsed_seconds") or 0 for s in sess)
    start = min(s["started_utc"] for s in sess)[:16].replace("T", " ")
    cpu = sum(max((e.get("cpu_s") or 0) for e in events(name, w)) for w in ws)
    runs_info[name] = dict(start=start, wall=wall, workers=len(ws), wh=len(ws) * wall / 3600, cpu=cpu / 3600, circuits=0)

# ---------------- circuits
rows = {}
for m, g, d in adds:
    name = f"{m}-xor{g}-depth{d}"
    fd = json.load(open(f"circuits/{m}/logs/{name}/found.json"))
    run, w, t = fd["run"], fd["worker"], fd["seconds_into_run"]
    ev = events(run, w)
    c = sum(e["cpu_s"] for e in ev if e.get("ev") == "epoch" and e["t"] <= t)
    nxt = [e for e in ev if e.get("ev") == "epoch" and e["t"] > t][:1]
    c += nxt[0]["cpu_s"] * 0.5 if nxt else 0
    seed = fd.get("seed") or {}
    root = fd.get("chain_root", "")
    if seed.get("kind") == "file":
        note = f"from {'NIST' if seed.get('by') == 'NIST' else 'our'} {seed.get('point')}"
        if root not in ("seed", "") and "#" not in str(root):
            note += f", restarted from the worker's {root}"
    else:
        note = "fresh roots"
    runs_info[run]["circuits"] += 1
    rows[(m, g, d)] = (f"| [{m} {g}@{d}]({m}/{name}.circ.txt) | v8 | {run} | {fmt_t(t)} | {fmt_cpu(c)} | "
                       f"{runs_info[run]['wh']:.1f} | exact | {note} |")
for r in sorted(rows):
    print(rows[r])
for name, ri in sorted(runs_info.items()):
    print(f"| {name} | v8 | {ri['start']} | {fmt_t(ri['wall'])} | {ri['workers']} | {ri['wh']:.1f} | {ri['cpu']:.1f} | yes (shared machine) | {ri['circuits']} |")
if not WRITE:
    sys.exit(0)

# ---------------- README
p = "circuits/README.md"
s = open(p, encoding="utf-8").read()
maps = sorted({m for m, _, _ in adds} | {m for m, _, _ in removes})
for m in maps:
    assert m not in ("aes-mixcolumns", "aes-invmixcolumns"), m
    i = s.index(f"| [{m}]({m}/) |")
    j = s.index("\n", i)
    cells = s[i:j].split(" | ")
    items = cells[3].split(", ")
    rem = {f"{g}@{d}" for mm, g, d in removes if mm == m}
    items = [it for it in items if re.match(r"\[(\d+@\d+)\]", it).group(1) not in rem]
    for mm, g, d in adds:
        if mm == m:
            items.append(f"[{g}@{d}]({m}/{m}-xor{g}-depth{d}.circ.txt)")
    items.sort(key=lambda it: int(re.match(r"\[\d+@(\d+)\]", it).group(1)))
    cells[3] = ", ".join(items)
    found = [v.strip() for v in cells[4].rstrip(" |").split(",")]
    if any(mm == m for mm, _, _ in adds) and "v8" not in found:
        found.append("v8")
    cells[4] = ", ".join(found) + " |"
    s = s[:i] + " | ".join(cells) + s[j:]
n_circ = len(glob.glob("circuits/*/*-xor*-depth*.circ.txt"))
n_maps = len({os.path.dirname(f) for f in glob.glob("circuits/*/*-xor*-depth*.circ.txt")})
s = re.sub(r"\d+ circuits for \d+ maps", f"{n_circ} circuits for {n_maps} maps", s, count=1)
open(p, "w", encoding="utf-8", newline="\n").write(s)

# ---------------- SEARCH-TIME
p = "circuits/SEARCH-TIME.md"
s = open(p, encoding="utf-8").read()
for m, g, d in removes:
    key = f"| [{m} {g}@{d}]("
    i = s.find(key)
    assert i >= 0, key
    s = s[:i] + s[s.index("\n", i) + 1:]
lines = s.split("\n")
ci = lines.index("## Circuits")
for (m, g, d), row in sorted(rows.items()):
    idx = None
    k = ci + 3
    while k < len(lines) and lines[k].startswith("| ["):
        mm = re.match(r"\| \[([^ ]+) (\d+)@(\d+)\]", lines[k])
        name, dd = mm.group(1), int(mm.group(3))
        if name == m and dd > d:
            idx = k
            break
        if name > m:
            idx = k
            break
        k += 1
    if idx is None:
        idx = k
    lines.insert(idx, row)
s = "\n".join(lines)
anchor = "| adopt | v9 prototype | 2026-10-31 15:00 | 45.5 h | 10 | 454.8 | 449.3 | no | 1 |\n"
assert anchor in s
new_rows = "".join(f"| {name} | v8 | {ri['start']} | {fmt_t(ri['wall'])} | {ri['workers']} | {ri['wh']:.1f} | {ri['cpu']:.1f} | yes (shared machine) | {ri['circuits']} |\n"
                   for name, ri in sorted(runs_info.items(), key=lambda kv: kv[1]["start"]) if ri["circuits"])
s = s.replace(anchor, anchor + new_rows)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("written; the totals paragraph ('Together: ...') still needs a manual edit:",
      {k: (round(v["wh"], 1), v["circuits"]) for k, v in runs_info.items()})
