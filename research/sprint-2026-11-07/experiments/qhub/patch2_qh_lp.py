#!/usr/bin/env python3
"""Second patch of qh_lp.py: packing rows for q = 4, 5 (variant PK) and the linear aggregate of H2 (variant HUB2L)."""
from pathlib import Path
P = Path.home()/'xs-campaigns/2026-11-07-sprint/qhub/qh_lp.py'
s = P.read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("    if q == 7: LE('L23 seven packing', lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0), 14)\n",
    "    if q == 7: LE('L23 seven packing', lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0), 14)\n"
    "    if 'PK' in variant:\n"
    "        # Lemma 10.4's argument at q = 4, 5: the missing-label sets of the helpers with u >= 3 are subsets of a q-set\n"
    "        # pairwise intersecting in <= 1 element.  q = 4: two 3-subsets of a 4-set share 2, so N_3 <= 1 (N_j = #{u >= j}).\n"
    "        # q = 5: three 3-sets pairwise sharing <= 1 need >= 6 points; a 4- or 5-set excludes every other set of size >= 3.\n"
    "        if q == 4: LE('PK4: N3 <= 1', lambda r, u, v: 1 if u >= 3 else 0, 1)\n"
    "        if q == 5: LE('PK5: N3 + 2 N4 <= 2', lambda r, u, v: {3: 1, 4: 2, 5: 2}.get(u, 0), 2)\n")
rep("    if hub_case:\n        if hub_case[0] == 'd':\n            EQ(f'HUB case A = q - {hub_case[1]}', lambda r, u, v: u if r == 3 else 0, q - hub_case[1])\n",
    "    if hub_case:\n        if hub_case[0] == 'd':\n            EQ(f'HUB case A = q - {hub_case[1]}', lambda r, u, v: u if r == 3 else 0, q - hub_case[1])\n"
    "            if 'HUB2L' in variant:\n"
    "                # linear aggregate of H2 in the case A = q - d: m_i >= u_i - d for non-full helpers; the (non-full helper,\n"
    "                # full-met label) incidences at a full-met label l number <= 3 + 2 f_l ((3.2) minus the full helper's edge);\n"
    "                # summed over the A full-met labels: sum_{r<3} (u - d)_+ n <= 3 A + 2 (F - F_H).\n"
    "                dd = hub_case[1]\n"
    "                LE(f'HUB2L: sum_(r<3) (u-{dd})_+ n + 2 F_H <= 3 (q-{dd}) + 2F', lambda r, u, v, dd=dd: (max(0, u - dd) if r < 3 else 0) + 2 * f_min(r, u, v), 3 * (q - dd) + 2 * F)\n")
P.write_text(s)
print('patched')
