#!/usr/bin/env python3
"""E1.toml: the pre-registered 1 h / 12-worker experiment (translog/REPORT.md): hunt D0
settings (v8 defaults, uncapped MixColumns, sharing off) + translog on + restarts off; six
2-worker groups, each on one of the six distinct hunt-D 88 records in seeds.json (the two
workers of a group get different rng seeds from the campaign seed)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
seeds = json.load(open(HERE / "seeds.json"))
assert len(seeds) == 6
head = """# exp1: 1 h, 12 MixColumns workers, uncapped, v8 defaults as hunt D0, translog on, restarts off.
# Six 2-worker groups p0..p5, each pair started on the same hunt-D 88 record (same-start pairs are
# the positive control for meeting/separation; the 15 cross pairs test trail meetings).

[campaign]
name = "translog-exp1"
seed = 20261109
duration = "60m"
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
"""
groups = ""
for i, s in enumerate(seeds):
    groups += f"""
# {s['arm']} {s['worker']} root {s['root']} v3 {s['sig']} depth {s['depth']}
[[workers]]
name = "p{i}"
target = "aes-mixcolumns"
count = 2
objective = "gates"
depth_cap = "none"
seeds = ["{s['path']}"]
"""
(HERE / "E1.toml").write_text(head + groups)
print("wrote E1.toml")
