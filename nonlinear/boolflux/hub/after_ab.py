#!/usr/bin/env python3
"""Pre-registered decision after an A/B: wait until both arms logged 'end', compare (compare2.py), and if the
test arm has at least as many new frontier points as the base arm and at least one, merge TEST_CONTROL into
the long campaign's control.json; in any case add the A/B CPUs to the long campaign.  Logs the decision.

    python3 after_ab.py HUB SNAPSHOT BASE_ARM TEST_ARM LONG TEST_CONTROL_JSON CPUS_TO_ADD
"""
import json, subprocess, sys, time
from pathlib import Path

hub, snap, base, test, long_, tctl, cpus = sys.argv[1:8]
H = Path(hub)


def ended(d):
    f = Path(d) / 'events.jsonl'
    return f.exists() and '"ev": "end"' in f.read_text()[-2000:]


while not (ended(base) and ended(test)):
    time.sleep(60)
out = Path(hub) / ('decision-%s.json' % Path(test).name)
r = subprocess.run([sys.executable, str(Path(__file__).with_name('compare2.py')), snap, 'base=%s:1' % base, 'test=%s:1' % test,
                    '--check', '--json', str(out.with_suffix('.compare.json'))], capture_output=True, text=True)
res = json.loads(out.with_suffix('.compare.json').read_text())
nb, nt = res['base']['new_frontier_points'], res['test']['new_frontier_points']
adopt = nt >= 1 and nt >= nb
cf = Path(long_) / 'control.json'
c = json.loads(cf.read_text()) if cf.exists() else {}
if adopt: c.update(json.loads(tctl))
c['cpus'] = sorted(set(c.get('cpus', [])) | {int(x) for x in cpus.split(',')})
c['note'] = '%s: after A/B %s (base %d vs test %d new frontier points): %s; cpus %s added' % (
    time.strftime('%H:%M UTC', time.gmtime()), Path(test).name, nb, nt, 'ADOPTED ' + tctl if adopt else 'not adopted', cpus)
cf.write_text(json.dumps(c, indent=1))
out.write_text(json.dumps({'base_points': nb, 'test_points': nt, 'adopted': adopt, 'control': c,
                           'compare_stdout': r.stdout[-4000:]}, indent=1))
print(c['note'])
