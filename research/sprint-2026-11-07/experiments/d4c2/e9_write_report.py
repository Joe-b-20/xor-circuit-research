"""e9_write_report.py -- assemble d4c2/REPORT.md from the run files (numbers read from e3_TAG.json / .log via
e8_table.py's parser) and the verdict text below.
usage: python3 e9_write_report.py
"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TAGS = ["K24", "H6", "B0", "FULLnoR2", "BJnoR2", "MnoR2", "M1noR2", "M2noR2", "BJ", "M", "Mw2", "K23"]
TAGS = [t for t in TAGS if os.path.exists(os.path.join(HERE, f"e3_{t}.log"))]
subprocess.run([sys.executable, os.path.join(HERE, "e8_table.py")] + TAGS, capture_output=True, text=True)
rows = {r["tag"]: r for r in json.load(open(os.path.join(HERE, "e8_table.json")))}

DESC = {
    "K24": ("B0 (89's level pattern: 20 weight-5 outputs at level 3, 12 weight-7 at level 4), |L2| = 24",
            "helpers restricted to N6 (26,024 masks), sound: section 3 (a)", "|L2|+|H3|", 31),
    "H6": ("B0, |H3| = 6 (subsumes the <= 30 part of K24)",
           "helpers restricted to N6, sound: section 3 (b)", "|L2| only", 25),
    "B0": ("B0, two-helper recipes allowed, |L2| free (covers every k = |L2|, in particular k = 23, 24)",
           "none", "|L2|+|H3|", 31),
    "FULLnoR2": ("full scope C (every level pattern), no two-helper level-4 recipe", "none", "|L2|+|H3|", 31),
    "BJnoR2": ("m = 0, j >= 1, no two-helper level-4 recipe", "none", "|L2|+|H3|", 31),
    "MnoR2": ("m >= 1 (j free), no two-helper level-4 recipe", "none", "|L2|+|H3|", 31),
    "M1noR2": ("m = 1, no two-helper recipe (part of MnoR2; queued before MnoR2's result was known)", "none",
               "|L2|+|H3|", 31),
    "M2noR2": ("m >= 2, no two-helper recipe (part of MnoR2; interrupted as redundant once MnoR2 closed)", "none",
               "|L2|+|H3|", 31),
    "BJ": ("m = 0 (all weight-5 outputs at level 3), j >= 1 realisable weight-7 outputs at level 3", "none",
           "|L2|+|H3|", 31),
    "M": ("m >= 1 (at least one weight-5 output at level 4), j free; interrupted at 257 s for memory (6.4 GB)",
          "none", "|L2|+|H3|", 31),
    "Mw2": ("same branch as M, 2 core workers (core_b, core_e), memory watchdog; interrupted at 813 s to end the "
            "session", "none", "|L2|+|H3|", 31),
    "K23": ("B0, |L2| = 23", "at most one helper outside N6, sound: section 3 (c)", "|L2|+|H3|", 31),
}


def row_md(t):
    r = rows[t]; d, rest, obj, target = DESC[t]
    d, obj = d.replace("|", "\\|"), obj.replace("|", "\\|")      # pipes inside a markdown table cell
    pts = [f"{b:.0f} at {tt:.0f} s" for tt, b in r["traj"] if b > 0]
    traj = ", ".join(pts) if len(pts) <= 7 else ", ".join(pts[:1] + ["..."] + pts[-6:])
    b = r["bound"]
    if b >= target - 1e-6:
        verdict = f"**CLOSED** (bound {b:.0f} >= {target})"
    else:
        verdict = f"open at bound {b:.0f} (needs {target})"
    wall = r.get("wall")
    wall_s = f"{wall:.0f}" if isinstance(wall, (int, float)) else "?"
    status = r["status"]
    js = os.path.join(HERE, f"e3_{t}.json")
    mix = "2" if os.path.exists(js) and json.load(open(js)).get("core4") else "1"
    return (f"| {t} | {d} | {rest} | {obj} | {target} | {mix} | {status} | {b:.0f} | {verdict} | {wall_s} | {traj} |")


table = ["| tag | branch (scope C = weight-2 set exactly P89) | helper-universe restriction | objective | "
         "closes at | worker mix | status | final proved bound | verdict | solver wall s | bound trajectory (time from solver start) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
table += [row_md(t) for t in TAGS]
TABLE = "\n".join(table)

found = sorted(os.listdir(os.path.join(HERE, "found")))
FOUND = os.path.exists(os.path.join(HERE, "FOUND_88AT4"))

text = open(os.path.join(HERE, "e9_text.md")).read()
text = text.replace("@@TABLE@@", TABLE)
for t, r in rows.items():           # @@B:TAG@@ = final bound, @@T:TAG@@ = time of the last improvement (s)
    text = text.replace(f"@@B:{t}@@", f"{r['bound']:.0f}")
    text = text.replace(f"@@T:{t}@@", f"{r['t_last']:.0f}" if r.get("t_last") is not None else "?")
    w = r.get("wall")
    text = text.replace(f"@@W:{t}@@", f"{w:.0f}" if isinstance(w, (int, float)) else "?")
mb = [rows[t]["bound"] for t in ("M", "Mw2") if t in rows]
text = text.replace("@@MBEST@@", f"{max(mb):.0f}" if mb else "?")
text = text.replace("@@FOUND@@", ("**A circuit with <= 88 gates was found: see FOUND_88AT4 and found/.**" if FOUND else
                                  "No run met any feasible point at all (pure core search; solution count 0 in every "
                                  "run json), so in particular none with `|L2| + |H3| <= 30`; `found/` is empty"
                                  + (f" (contains: {found})" if found else "") + " and `FOUND_88AT4` does not exist."))
left = re.findall(r"@@[A-Z]+(?::[A-Za-z0-9]+)?@@", text)
if left:
    print("WARNING: unfilled placeholders", sorted(set(left)))
open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="\n").write(text)
print("wrote REPORT.md", len(text), "chars")
