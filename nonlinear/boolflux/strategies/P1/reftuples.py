#!/usr/bin/env python3
"""Reference tuple set for P1's 'new on archive' test: pinned NIST tuples + every hub archive record +
BEST.json tuples + the survey rows (starts.json) + every found/ circuit of this campaign.

    python3 reftuples.py STARTS.json OUT.json
"""
import glob
import json
import sys
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / 'xcr-boolflux/nonlinear'))
from boolflux.hub.common import published  # noqa: E402

ref = set(tuple(t) for t in published())
for f in glob.glob(str(HOME / 'xs-campaigns/2026-11-14-hub/*/archive/*.json')):
    try:
        r = json.loads(Path(f).read_text()); ref.add((r['A'], r['AD'], r['G'], r['GD']))
    except Exception:
        pass
for row in json.loads((HOME / 'xs-campaigns/2026-11-15-study/best-1400/BEST.json').read_text())['rows']:
    ref.add(tuple(row['tuple_A_AD_G_GD']))
for r in json.loads(Path(sys.argv[1]).read_text()):
    ref.add((r['A'], r['AD'], r['G'], r['GD']))
json.dump(sorted(ref), open(sys.argv[2], 'w'))
print(len(ref), 'tuples;', 'A<=28 AD<=5:', sorted(t for t in ref if t[0] <= 28 and t[1] <= 5 and t[2] <= 135))
