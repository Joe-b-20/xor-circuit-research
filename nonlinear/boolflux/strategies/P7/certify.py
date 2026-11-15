#!/usr/bin/env python3
"""P7: add path_certified to every found/ sidecar (COMPLIANCE-1820).
true  = no kernel in the lineage (construction only), or every kernel stage started inside ALL caps:
        fdrive gate mode restarts each stage from the job's best, which is feasible when the start is;
        the kernel never leaves the caps from a feasible start.  Checked: start file metrics within caps.
false = otherwise (osc/mix/trb stages or a start outside a cap)."""
import json, glob, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p7job
for f in sorted(glob.glob(str(Path.home() / 'xs-campaigns/2026-11-15-targets/P7/found/*.json'))):
    d = json.load(open(f)); m = d.get('method', {})
    if 'path_certified' in d and '--all' not in sys.argv: continue
    if not isinstance(m, dict): m = {'engine': m}
    eng = json.dumps(m)
    st = d['start']['path']
    if 'fdrive' not in eng and 'kernel' not in eng:
        cert, note = True, 'construction only (bopt/bbuild), no kernel'
    else:
        mode = m.get('mode', 'gate'); caps = m.get('caps', {})
        A, AD, G, GD = p7job.metr(st)
        inside = A <= caps.get('A', 99) and AD <= caps.get('AD', 4) and GD <= caps.get('GD', 99)
        insideAD = A <= caps.get('A', 99) and AD <= caps.get('AD', 4)
        cert = ((mode == 'gate') and inside) or ('fdrive_p7' in eng and insideAD)
        note = 'fdrive %s, start %d/%d/%d/%d %s caps %s' % (mode, A, AD, G, GD, 'inside' if inside else 'OUTSIDE', caps)
        # parent lineage: the start itself must be certified (a found/ build or a NIST/archive file)
    d['path_certified'] = cert; d['path_note'] = note
    json.dump(d, open(f, 'w'), indent=1); open(f, 'a').write('\n')
    print(cert, Path(f).name[:62], note)
