#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qcert
# restore the generator log (truncated by an import side effect of the first crosscheck run) from the captured stdout
{ echo "# gen_certs.py stdout, captured by s01_gen.sh on 2026-11-07 (the original gen_certs.log was truncated by an import side effect, since fixed)"; grep -v '^exit' s01_gen.out; } > gen_certs.log
( time nice -n 8 python3 crosscheck.py ) > s04_cross.out 2>&1; echo "exit $?" >> s04_cross.out
cat s04_cross.out
rm -rf __pycache__
python3 - <<'EOF'
import json
d=json.load(open('CERTIFICATES_EXT75.json'))
from collections import Counter
c=d['certificates']
print('certificates by kind', Counter(x['kind'] for x in c))
print('killed keys by q', sorted(Counter(k[4] for k in d['killed_keys']).items()))
print('killed keys by ori', Counter(k[3] for k in d['killed_keys']))
cl=d['claims']; print('claims by ori', Counter(x['orientation'] for x in cl))
print('claims: shortfall under package rows', sorted(Counter(x['state'][10]-(x['package_lower_even']+x['package_lower_odd']) for x in cl).items()))
print('claims: how excluded', Counter(('k>Se' if x['lower_even']>x['state'][8] else '')+('l>So' if x['lower_odd']>x['state'][9] else '')+('k+l>budget' if x['lower_even']+x['lower_odd']>x['state'][10] else '') for x in cl))
ws=[w for x in c for w in x['weights']]; print('multipliers total', len(ws), 'nonzero', sum(1 for w in ws if w), 'max weight', max(ws))
import statistics; print('rows per certificate min/max', min(len(x['weights']) for x in c), max(len(x['weights']) for x in c))
# which new rows are used by the 666 new certificates (by name, via gen_certs.ext_system names)
import sys; sys.path.insert(0,'.')
import gen_certs as g
use=Counter()
for x in c:
    if x['kind']!='new': continue
    key=tuple(x['key']); types,A,B,names=g.ext_system(key,True); npk=len(g.certify75.system(key)[1])
    for nm,w in zip(names[npk:],x['weights'][npk:]):
        if w: use[nm]+=1
print('new rows used (number of new certificates using each):'); [print('  ',k,v) for k,v in use.most_common()]
s=json.load(open('scan_ext75.json'))
from collections import Counter as C2
sf=C2(st[10]-(e[0]+e[1]) for st,o in [(tuple(x['state']),x['orientation']) for x in s['claims'] if not x['ext'][2]] for e in [next(y['ext'] for y in s['claims'] if tuple(y['state'])==st and y['orientation']==o)])
print('surviving 1313 claims: shortfall budget-(k+l) under the extended system', sorted(sf.items()))
EOF
rm -rf __pycache__
sha256sum CERTIFICATES_EXT75.json scan_ext75.json PROOF_ADDENDUM.md gen_certs.py check_ext75.py mutate_test.py stress_ext.py crosscheck.py stress_pkg.py profile_real_copy.py stress_ext.json mutate_test.json CHECKED_EXT75.json > SHA256SUMS.txt
cat SHA256SUMS.txt
