"""c9_table.py -- branch table from all c3_*.json in this folder (markdown)."""
import json, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for f in sorted(glob.glob(os.path.join(HERE, "c3_*.json"))):
    r = json.load(open(f)); tag = r["tag"]
    if tag.startswith("smoke"): continue
    a = r.get("args", {})
    ub = r.get("ub"); st = r["status"]; bd = r.get("bound"); obj = r.get("objective")
    if st == "INFEASIBLE" or (bd is not None and bd >= 31):
        verdict = "CLOSED: no circuit with h2+h3 <= 30 (" + ("INFEASIBLE" if st == "INFEASIBLE" else f"core bound {bd:.0f} >= 31") + ")"
    elif st in ("OPTIMAL", "FEASIBLE"):
        verdict = (f"SAT: h2+h3 = {obj:.0f} !!! (<= 30)" if obj is not None and obj <= 30 else
                   (f"optimum {obj:.0f}" if st == "OPTIMAL" else f"feasible {obj:.0f}, bound {bd:.0f}"))
    else:
        verdict = f"timeout, bound reached {bd:.0f}" if bd is not None else st
    fix3 = r.get("fix3", []); fix4 = r.get("fix4", [])
    scope = []
    if sorted(fix3) == sorted([0, 2, 5, 6, 7, 8, 10, 13, 14, 15, 16, 18, 21, 22, 23, 24, 26, 29, 30, 31]): scope.append("Y3 = W5")
    elif fix3: scope.append(f"fix3={fix3}")
    w7fix4 = sorted(set(fix4) - {1, 4, 11, 17, 20, 27})
    if len(w7fix4) == 6: scope.append("Y4 = W7")
    elif w7fix4: scope.append(f"fix4+={w7fix4}")
    for k in ("sumx", "sumxmin", "sumxmax", "m5", "m5min", "m5max", "w7l3", "u2", "strict"):
        if k in a: scope.append(f"{k}={a[k]}")
    cuts = [k for k in ("hmin", "pc5") if k in a]
    mode = ("max-HS" if a.get("maxhs") == "1" else "core" if a.get("core") == "1" else
            f"portfolio {a.get('workers')} threads" + (" + hint 89" if a.get("hint") == "89" else "") if int(a.get("workers", 1)) > 1 else f"default lin={a.get('lin', 1)}")
    rows.append((tag, "; ".join(scope) or "none (full scope C)", ub, mode, a.get("time"), ",".join(cuts), st, bd, obj, verdict, r.get("wall")))
print("| tag | restriction | ub | mode | limit s | cuts | status | bound | obj | verdict | wall s |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for t in rows:
    print("| " + " | ".join("" if v is None else (f"{v:.0f}" if isinstance(v, float) else str(v)) for v in t) + " |")
