#!/usr/bin/env python3
"""E2.toml (exp2, pre-registered in DESIGN.md): exp1's settings (hunt D0 = v8 defaults, uncapped
MixColumns, sharing off, restarts off, translog band 89 / id 88 / rotate 8 / values entry /
values_gates 89) + translog.departure = true; four 2-worker groups q0..q3, each pair on one of the
four seeds.json records (different rng seeds per worker from the campaign seed).
usage: make_toml.py DURATION OUT.toml [N_GROUPS]"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
dur, out = sys.argv[1], sys.argv[2]
ng = int(sys.argv[3]) if len(sys.argv) > 3 else 4
seeds = json.load(open(HERE / "seeds.json"))[:ng]
head = f"""# exp2: {dur}, {2*ng} MixColumns workers, uncapped, v8 defaults as hunt D0, translog on (+ departure
# keys), restarts off.  {ng} 2-worker groups q0..q{ng-1}, each pair started on one hunt-D 88 record.

[campaign]
name = "translog-exp2"
seed = 20261110
duration = "{dur}"
profiles = ["default"]
sharing = "off"

[set]
"scheduler.reference" = [[97, 3], [89, 4], [88, 5]]
"engine.records_per_point" = 100000
"engine.record_stride" = 4096
"worker.records_per_point" = 100000
"restart.enabled" = false
"restart.w_fresh" = 1.0
"restart.w_elite" = 0.0
"restart.w_shared" = 0.0
"restart.w_best" = 0.0
"translog.enabled" = true
"translog.band_gates" = 89
"translog.id_gates" = 88
"translog.rotate_bits" = 8
"translog.values" = "entry"
"translog.values_gates" = 89
"translog.departure" = true
"""
groups = ""
for i, s in enumerate(seeds):
    groups += f"""
# {s['arm']} {s['worker']} root {s['root']} v3 {s['sig']} depth {s['depth']}
[[workers]]
name = "q{i}"
target = "aes-mixcolumns"
count = 2
objective = "gates"
depth_cap = "none"
seeds = ["{s['path']}"]
"""
Path(out).write_text(head + groups)
print("wrote", out)
