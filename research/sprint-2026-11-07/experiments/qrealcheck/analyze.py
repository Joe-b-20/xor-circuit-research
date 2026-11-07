#!/usr/bin/env python3
"""qrealcheck: verify the survivor statements of qreal/REPORT.md sections 4.2 and 6 from the scan files,
and compare the recount / independent scans with qreal's."""
import json, sys
from collections import Counter
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
Q = SPRINT/'qreal'; C = SPRINT/'qrealcheck'
def load(p): return json.load(open(p))
ref = load(Q/'scan_GstarN1HUBDARKM_q0_g75.json')
keys = [tuple(k) for k in ref['keys_still_feasible']]; surv = ref['survivors']
print('qreal final: keys', len(keys), 'by q', sorted(Counter(k[3] for k in keys).items()), 'by ori', dict(Counter(k[5] for k in keys)))
print('  survivors', len(surv), 'by ori', dict(Counter(s['ori'] for s in surv)), 'shortfall', sorted(Counter(s['shortfall'] for s in surv).items()))
print('  survivors by h_e', sorted(Counter(s['state'][4] for s in surv).items()))
q3 = sorted(k for k in keys if k[3] <= 3)
print('  keys with q <= 3:', len(q3)); [print('    ', k) for k in q3]
claimed = {(18,1,1,1,4,'Mt'), (19,0,0,1,5,'Mt'), (7,11,4,2,6,'Mt'), (7,12,3,2,5,'Mt'), (9,10,1,3,2,'Mt'), (10,8,1,3,2,'Mt'), (11,6,1,3,2,'Mt'), (19,0,4,3,3,'M')}
for k in [(5,13,7,3,7), (5,14,6,3,6), (5,14,7,3,6), (6,13,5,3,5), (6,13,6,3,5)]:
    claimed.add(k + ('M',)); claimed.add(k + ('Mt',))
print('  claimed q<=3 list matches:', set(q3) == claimed, '; only-claimed', sorted(claimed - set(q3)), '; only-file', sorted(set(q3) - claimed))
for k in [(12,5,5,2,3,'M'), (10,6,6,6,0,'M'), (11,5,5,5,0,'Mt'), (13,4,4,4,1,'M'), (12,4,4,5,1,'Mt')]:
    print('  key', k, 'feasible in final:', k in set(keys))
hub = load(Q/'scan_GstarN1HUB_q0_g75.json'); hk = {tuple(k) for k in hub['keys_still_feasible']}
q1_hub = sorted(k for k in hk if k[3] == 1); q1_fin = sorted(k for k in keys if k[3] == 1)
print('  q=1 keys after HUB:', len(q1_hub), '-> after DARK:', q1_fin)
# q = 1 cluster: every q=1 key with y+z <= 4 and z <= 2 should be dead (bright: z>=3; dark: y+z+D0>=5 with D0<=0)
viol = [k for k in q1_fin if k[1] + k[4] <= 4 and k[4] <= 2]
print('  q=1 survivors violating the stated kill rule (must be none):', viol)
# compare recount and independent scans
for name, mine_file in (('HUB', C/'lp_qrc_scan_GstarN1HUB.json'), ('HUBDARK', C/'lp_qrc_scan_GstarN1HUBDARK.json')):
    if mine_file.exists():
        mine = load(mine_file); ms = {(tuple(st), ori) for st, ori, k, ell in mine}
        rf = load(Q/('scan_GstarN1HUB_q0_g75.json' if name == 'HUB' else 'scan_GstarN1HUBDARKM_q0_g75.json'))
        rs = {(tuple(s['state']), s['ori']) for s in rf['survivors']}
        # bounds k, ell must agree too
        rb = {(tuple(s['state']), s['ori']): (s['k'], s['ell']) for s in rf['survivors']}
        mb = {(tuple(st), ori): (k, ell) for st, ori, k, ell in mine}
        print(f'independent scan {name}: mine {len(ms)} ref {len(rs)} symdiff {len(ms ^ rs)}; (k,ell) differ on', sum(1 for x in ms & rs if rb[x] != mb[x]))
for name in ('scan_GstarN1HUB_q0_g75.json', 'scan_GstarN1HUBDARKM_q0_g75.json'):
    if (C/name).exists():
        a = load(C/name); b = load(Q/name)
        sa = {(tuple(s['state']), s['ori'], s['k'], s['ell']) for s in a['survivors']}; sb = {(tuple(s['state']), s['ori'], s['k'], s['ell']) for s in b['survivors']}
        ka = {tuple(k) for k in a['keys_still_feasible']}; kb = {tuple(k) for k in b['keys_still_feasible']}
        print(f'recount {name}: survivors {len(sa)} vs {len(sb)} symdiff {len(sa ^ sb)}; keys {len(ka)} vs {len(kb)} symdiff {len(ka ^ kb)}')
