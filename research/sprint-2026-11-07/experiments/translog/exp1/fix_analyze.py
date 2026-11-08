#!/usr/bin/env python3
"""Small fixes: sampler record index for adjacency; tolerant JSONL reading in translog/analyze.py."""
from pathlib import Path
p = Path.home() / "xs-campaigns/2026-11-07-sprint/translog/exp1/analyze_exp1.py"
t = p.read_text()
old = '    mine = [r for r in recs if r["worker"] == w]\n    s88 = [r for r in mine if r["gates"] == 88]\n'
new = ('    mine = [r for r in recs if r["worker"] == w]\n    for k, r in enumerate(mine):\n        r["idx"] = k\n'
       '    s88 = [r for r in mine if r["gates"] == 88]\n')
assert t.count(old) == 1
t = t.replace(old, new)
p.write_text(t)
p2 = Path.home() / "xs-campaigns/2026-11-07-sprint/translog/analyze.py"
t = p2.read_text()
old = '    rows = [json.loads(line) for line in open(path)]\n'
new = ('    rows = []\n    for line in open(path):\n        try:\n            rows.append(json.loads(line))\n'
       '        except ValueError:\n            pass                                 # partial last line of a live log\n')
assert t.count(old) == 1
p2.write_text(t.replace(old, new))
print("fixed")
