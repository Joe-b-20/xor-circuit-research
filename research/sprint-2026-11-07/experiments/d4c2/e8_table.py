"""e8_table.py -- collect the d4c2 runs (e3_TAG.json / .log / .out) into a branch table (markdown) and a json.
For a run without a json (killed), status/bound are read from its log.  Bound trajectory = the '#Bound' lines.
usage: python3 e8_table.py TAG1 TAG2 ...   -> prints the table, writes e8_table.json
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for tag in sys.argv[1:]:
    js = os.path.join(HERE, f"e3_{tag}.json"); lg = os.path.join(HERE, f"e3_{tag}.log"); out = os.path.join(HERE, f"e3_{tag}.out")
    r = {"tag": tag}
    if os.path.exists(js):
        d = json.load(open(js))
        r.update(status=d["status"], bound=d["bound"], wall=d["wall"], args=d["args"], target=d.get("target", 31),
                 closed=d.get("closed"), objective=d.get("objective"), total=d.get("total"), src="json")
    traj = []; t_model = None
    if os.path.exists(lg):
        for line in open(lg):
            m = re.match(r"#Bound\s+([\d.]+)s\s+best:(\S+)\s+next:\[(-?[\d.]+),", line)
            if m: traj.append((float(m.group(1)), float(m.group(3))))
            m2 = re.match(r"#Model\s+([\d.]+)s", line)
            if m2 and t_model is None: t_model = float(m2.group(1))
            m3 = re.match(r"walltime: ([\d.]+)", line)
            if m3: r.setdefault("wall", float(m3.group(1)))
    r["traj"] = traj
    if "bound" not in r:
        r.update(status="killed (no json)", bound=max((b for _, b in traj), default=0.0), src="log")
        if os.path.exists(out):
            for line in open(out):
                m = re.search(r"python3 e3_run.py \S+ (.*)$", line)
        r["args"] = {}
    # last improvement time
    r["t_last"] = traj[-1][0] if traj else None
    rows.append(r)
json.dump(rows, open(os.path.join(HERE, "e8_table.json"), "w"), indent=1)
for r in rows:
    tr = ", ".join(f"{int(b)}@{int(t)}s" for t, b in r["traj"] if b > 0)
    print(f"{r['tag']}: status {r['status']} bound {r['bound']} target {r.get('target')} closed {r.get('closed')} "
          f"wall {r.get('wall')} last-improvement {r['t_last']} traj [{tr}]")
