#!/usr/bin/env python3
"""X2: exercise GoalScheduler.goal_met (found/ NCFF + sidecar + aes_check.py + GOAL-MET event) with a FAKE test goal
'Z' (caps loose enough that an archived circuit meets it), on a scratch copy of an archive.

    python3 test_goalmet.py SCRATCH_CAMPAIGN_DIR
The fake goal exists only inside this process; nothing is written outside SCRATCH_CAMPAIGN_DIR."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import goals as GL              # noqa: E402

Z = GL.Goal('Z', 40, 6, 200, 40, 'TEST ONLY')
GL.GOALS = GL.GOALS + (Z,); GL.BY_NAME['Z'] = Z; GL.NAMES = GL.NAMES + ('Z',)
from boolflux.hub import scheduler_goal as SG     # noqa: E402

d = Path(sys.argv[1])
a = argparse.Namespace(dir=str(d), seed=1, ops='polish', seconds=None, eps=0.25, near=0, near_gap=3, nursery=0.0,
                       goal_share='', generic_share=0.0, found=str(d / 'found-test'), cpus='11', hours=0.0)
s = SG.GoalScheduler(SG._Args(a))
print('met at start (fake goal Z expected):', sorted(s.met))
i = s.gbest['Z'][2]; m = s.gbest['Z'][1]
s.goal_met('Z', i, m, {'goal': 'Z', 'goal_caps': None})
fs = sorted((d / 'found-test').glob('*'))
print('found files:', [f.name for f in fs])
side = json.loads([f for f in fs if f.name.endswith('.json') and 'aes_check' not in f.name][0].read_text())
print('sidecar aes_check_ok:', side['aes_check_ok'], 'metrics', side['metrics'])
print('GOALS-MET.txt:', (d / 'GOALS-MET.txt').read_text().strip())
assert side['aes_check_ok'] and side['metrics'] == list(m)
print('goal_met ok')
