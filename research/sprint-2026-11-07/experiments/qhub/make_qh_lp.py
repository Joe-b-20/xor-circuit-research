#!/usr/bin/env python3
"""Derive qh_lp.py from qreal/qr_lp.py: per-r hub capacity (finite fact H2, hub2.py) as variant HUB2."""
from pathlib import Path
SP = Path.home()/'xs-campaigns/2026-11-07-sprint'
s = (SP/'qreal/qr_lp.py').read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'",
    "OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhub'\nQREAL = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'")
rep("d = json.load(open(OUT/f'fullsets_{ori}.json'))", "d = json.load(open(QREAL/f'fullsets_{ori}.json'))")
rep("FULLMET[ori] = json.load(open(OUT/f'fullmet_{ori}.json'))", "FULLMET[ori] = json.load(open(QREAL/f'fullmet_{ori}.json'))")
rep("KAPPA = 4            # hub.py: kappa_0 = kappa_1 = 4 for M and Mt",
    "KAPPA = 4            # hub.py: kappa_0 = kappa_1 = 4 for M and Mt\n"
    "KR2 = {0: 3, 1: 2, 2: 1}   # hub2.py (H2): a helper with r <= 2 has at most 3 - r full-met missing labels (M and Mt)\n"
    "def kr(variant, r):\n    return KR2[r] if 'HUB2' in variant else KAPPA")
rep("        types = [t for t in types if not (t[0] < 3 and t[1] > KAPPA + d)]",
    "        types = [t for t in types if not (t[0] < 3 and t[1] > kr(variant, t[0]) + d)]")
rep("            LE(f'HUB case A <= {KAPPA}', lambda r, u, v: u if r == 3 else 0, KAPPA)",
    "            LE(f'HUB case A <= {hub_case[1]}', lambda r, u, v: u if r == 3 else 0, hub_case[1])")
rep("""    if 'HUB' in variant and 'HUBlin' not in variant and q > KAPPA:
        hubs = [('d', d) for d in range(0, q - KAPPA)] + [('low',)]""",
    """    kmin = min(kr(variant, r) for r in (0, 1, 2))
    if 'HUB' in variant and 'HUBlin' not in variant and q > kmin:
        hubs = [('d', d) for d in range(0, q - kmin)] + [('low', kmin)]""")
rep('"""qreal LP: qbound\'s qb_lp.py (package rows L1-L23 + G* + N1) extended with the qreal rows.',
    '"""qhub LP: qreal\'s qr_lp.py with the per-r hub capacity of finite fact H2 (hub2.py): variant HUB2 =\n'
    'exact case split on A = sum_{r=3} u n with u <= (3 - r) + (q - A) for every type with r <= 2.\n'
    'Original header follows.\n\nqreal LP: qbound\'s qb_lp.py (package rows L1-L23 + G* + N1) extended with the qreal rows.')
(SP/'qhub/qh_lp.py').write_text(s)
print('written', len(s))
