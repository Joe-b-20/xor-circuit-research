#!/usr/bin/env python3
"""Fast staircase scan (E, K, sink, d_1, m_1, waste lower/upper) of .bfx / .circ.txt circuits.
For sink-layer circuits waste = K - d_1 - 7 exactly [P]; for non-sink ones the full staircase is
computed with staircase.py.  usage: arch_scan.py OUT.jsonl FILE...   (.bfx converted via core)"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boolflux import core
import staircode as SC
import staircase as ST

model = core.Model.load('nist')
out = open(sys.argv[1], 'a')
for f in sys.argv[2:]:
    tmp = None
    try:
        if f.endswith('.bfx'):
            c = core.from_kernel(open(f).read())
            tmp = tempfile.NamedTemporaryFile('w', suffix='.circ.txt', delete=False)
            tmp.write(core.write_ncff(c, model)); tmp.close()
            path = tmp.name
        else:
            path = f
        r = SC.core_and_code(path)
        cols = r['cols']
        d1 = min(bin(sum(1 << j for j, v in enumerate(cols) if bin(cc & v).count('1') & 1)).count('1') for cc in range(1, 256))
        lv = r['lvl']
        per = [sum(1 for x in lv if x == L) for L in range(1, max(lv) + 1)]
        rec = dict(file=f, A=r['A'], levels=per, E=r['E'], K=len(r['Lidx']), sink=r['sink'], d1=d1,
                   m1=r['E'] + d1)
        if r['sink']:
            rec['waste'] = len(r['Lidx']) - d1 - 7
        else:
            m = ST.analyse(path)['m']
            rec['m'] = m; rec['m1'] = m[0]; rec['waste'] = m[7] - m[0] - 7
    except Exception as e:
        rec = dict(file=f, error=repr(e)[:200])
    finally:
        if tmp is not None:
            os.unlink(tmp.name)
    out.write(json.dumps(rec) + '\n'); out.flush()
