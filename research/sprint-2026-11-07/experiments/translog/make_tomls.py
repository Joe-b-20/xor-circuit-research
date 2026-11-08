#!/usr/bin/env python3
"""Write the campaign files: T0 (translog off) and T1 (translog on), identical otherwise
(modelled on hunt/D0.toml: v8 defaults, 1 MixColumns worker, uncapped, 20 min, same rng seed,
same 88@6 seed circuit from hunt D so the 20 minutes are spent on the 88+89 band), and S1,
a 75 s smoke test of T1."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = (Path.home() / "xs-campaigns/2026-11-07-sprint/hunt/runsD/D0/workers/free-00/records/"
        "g88-d6-0f7bfd6b155e8d61.json")
assert SEED.exists(), SEED

BASE = """# translog test, arm {arm}: v8 defaults as hunt D0, ONE MixColumns worker, uncapped, {dur},
# started on an 88@6 record of hunt D0 (free-00) so the run sits on the 88+89 band from t = 0
# (incumbent stall allowance 2 x 900 s > 20 min: one chain).  {note}

[campaign]
name = "translog-{arm}"
seed = 20261108
duration = "{dur}"
profiles = ["default"]
sharing = "off"

[set]
"scheduler.reference" = [[97, 3], [89, 4], [88, 5]]
"engine.records_per_point" = 100000
"engine.record_stride" = 4096
"worker.records_per_point" = 100000
"restart.w_fresh" = 1.0
"restart.w_elite" = 0.0
"restart.w_shared" = 0.0
"restart.w_best" = 0.0
{extra}
[[workers]]
name = "free"
target = "aes-mixcolumns"
count = 1
objective = "gates"
depth_cap = "none"
seeds = ["{seed}"]
"""

ON = ('"translog.enabled" = true\n"translog.rotate_bits" = 8\n'
      '"translog.values" = "entry"\n')

for arm, dur, extra, note in (
        ("T0", "20m", "", "Transition log OFF (control for the overhead measurement)."),
        ("T1", "20m", ON, "Transition log ON: band 89, identities + values at <= 88, byte rotation."),
        ("S1", "75s", ON, "Smoke test of the T1 configuration.")):
    text = BASE.format(arm=arm, dur=dur, extra=extra, note=note, seed=SEED)
    (HERE / f"{arm}.toml").write_text(text)
    print("wrote", arm)
