"""L1 analysis library: campaign replay, value model, lineage.  See WHAT-WORKS.md section 0."""
import json
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
import os
OUT = Path(os.environ.get('L1_OUT', str(HOME / 'xs-campaigns' / '2026-11-15-study' / 'L1')))
CAMPS = ['abhub', 'long', 'ab2base', 'ab2gen', 'ab3gen', 'ab3lin', 'ab4base', 'ab4ad3']
try:      # a cache made from other hub directories carries its own campaign list
    CAMPS[:] = json.loads((OUT / 'cache.json').read_text()).get('camps', CAMPS)
except Exception:
    pass
GENERATORS = {'gen_skel', 'gen_joinplus', 'gen_inv3', 'gen_bottom'}

# ---- the user's goals (addendum 01:35 UTC).  (name, A cap, AD cap, G cap, GD cap) ---------------
GOALS = [('B', 28, 4, 130, 22), ('C', 28, 5, 127, 19), ('D', 32, 4, 116, 19), ('E', 32, 6, 102, 31),
         ('F', 35, 3, 138, 26), ('G', 44, 4, 140, 11)]


def leq(u, m):
    return all(a <= b for a, b in zip(u, m))


def tier(A, AD):
    """value-model tier weight: one AND less doubles the weight down to 28; AND depth is the second key
    (factor 1.4 per level below 5, < 2 so it never outranks an AND)."""
    wa = {28: 64, 29: 32, 30: 16, 31: 8, 32: 4}.get(A, 1000 if A <= 27 else (2 if A <= 35 else 1))
    wd = {3: 1.96, 4: 1.4}.get(AD, 1.0 if AD == 5 else (2.744 if AD < 3 else 0.7))
    return wa * wd


def improvement(m, pts):
    """cap-box improvement of a non-dominated tuple m against the prior points pts (archive + published).
    Box of m = prior points with A <= m.A, AD <= m.AD, GD <= m.GD (the caps BEST.md compares under).
      box non-empty                      -> ('G', dG)   fewer gates under the same caps, dG = best prior G - m.G
      box empty, class (A<=, AD<=) not   -> ('GD', d)   the class reaches a smaller gate depth (d levels)
      class empty, (A<=) not             -> ('AD', d)   new smallest AND depth at this AND count
      nothing with A <= m.A              -> ('A', d)    AND-count record
    The most conservative (lowest-priority) explanation is taken.  Size: G min(dG,6)/2, GD 1.5, AD 4, A 8.
    Returns (kind, size, delta) or None if m is dominated (equality counts as dominated)."""
    if any(leq(q, m) for q in pts): return None
    box = [q[2] for q in pts if q[0] <= m[0] and q[1] <= m[1] and q[3] <= m[3]]
    if box:
        d = min(box) - m[2]
        return 'G', min(d, 6) * 0.5, d
    cls = [q[3] for q in pts if q[0] <= m[0] and q[1] <= m[1]]
    if cls: return 'GD', 1.5, min(cls) - m[3]
    ca = [q[1] for q in pts if q[0] <= m[0]]
    if ca: return 'AD', 4.0, min(ca) - m[1]
    return 'A', 8.0, min(q[0] for q in pts) - m[0]


def hub_kind(m, pts):
    """the archive's own gain rule (Archive.gain): highest-priority coordinate k such that some prior
    point is no worse on the other three coordinates"""
    for k, name in enumerate('A AD G GD'.split()):
        if any(all(q[j] <= m[j] for j in range(4) if j != k) for q in pts): return name
    return 'new'


def goal_near(m, goal, gw=6, dw=4):
    """m is inside the goal class (A, AD caps) and within gw gates / dw levels of the goal box"""
    _, A, AD, G, GD = goal
    return m[0] <= A and m[1] <= AD and m[2] <= G + gw and m[3] <= GD + dw


def goal_dist(m, goal):
    """distance of tuple m to a goal: None if the hard A/AD caps are violated, else G excess + GD excess"""
    _, A, AD, G, GD = goal
    if m[0] > A or m[1] > AD: return None
    return max(0, m[2] - G) + max(0, m[3] - GD)


class Data:
    def __init__(self):
        d = json.loads((OUT / 'cache.json').read_text())
        self.recs = d['recs']; self.inarch = d['inarch']; self.runs = d['runs']; self.events = d['events']
        self.published = [tuple(p) for p in d['published']]
        self.m = {i: (r['A'], r['AD'], r['G'], r['GD']) for i, r in self.recs.items()}
        # which campaign/run made each record
        self.made = {}
        self.runby = {}
        for c in CAMPS:
            for r in self.runs[c]:
                self.runby[(c, r['run_id'])] = r
                for o in r['outcome']:
                    if o['status'] == 'admitted':
                        self.made[o['id']] = (c, r['run_id'])
        self.span = {}
        for c in CAMPS:
            st = [e['ts'] for e in self.events[c] if e['ev'] == 'start']
            en = [e['ts'] for e in self.events[c] if e['ev'] == 'end']
            last = max([r['ts_end'] or 0 for r in self.runs[c]] + en)
            self.span[c] = (min(st), last)
        self._replay()

    def op(self, i):
        o = self.recs[i]['operator']
        return 'base' if o in ('seed', 'ingest') else o

    def phase(self, c, ts):
        """sub-phase of the long directory by time"""
        if c != 'long': return c
        st = sorted(e['ts'] for e in self.events['long'] if e['ev'] == 'start')
        names = ['long1', 'long2', 'long3', 'long4a', 'long4']
        k = sum(1 for s in st if ts >= s) - 1
        return names[max(k, 0)]

    def _replay(self):
        """per campaign, in t_admit order: for every record admitted during the campaign compute the
        improvement against everything that was in that archive before it plus the published set"""
        self.val = {}       # (camp, id) -> dict(kind,size,delta,V)   only for records made in camp
        self.goalev = []    # goal-distance reductions
        for c in CAMPS:
            ids = sorted(self.inarch[c], key=lambda i: self.recs[i]['t_admit'])
            pts = list(self.published)
            gpts = {g[0]: [(p[2], p[3]) for p in pts if p[0] <= g[1] and p[1] <= g[2]] for g in GOALS}
            for i in ids:
                m = self.m[i]
                mine = self.made.get(i, (None,))[0] == c or (self.recs[i]['operator'] == 'ingest' and self.recs[i]['t_admit'] >= self.span[c][0])
                if mine:
                    imp = improvement(m, pts)
                    if imp:
                        self.val[(c, i)] = {'kind': imp[0], 'size': imp[1], 'delta': imp[2], 'V': tier(m[0], m[1]) * imp[1],
                                            'hub_kind': hub_kind(m, pts)}
                for g in GOALS:
                    if m[0] <= g[1] and m[1] <= g[2]:
                        gm = (m[2], m[3])
                        if not any(q[0] <= gm[0] and q[1] <= gm[1] for q in gpts[g[0]]):
                            if mine and goal_near(m, g):
                                self.goalev.append({'camp': c, 'id': i, 'goal': g[0], 'm': m, 'dist': goal_dist(m, g)})
                        gpts[g[0]].append(gm)
                pts.append(m)

    # ---- lineage ----------------------------------------------------------------------------
    def chain(self, i, depth=3):
        r = self.recs[i]; o = self.op(i)
        if o == 'base' or depth == 0: return o if o == 'base' else o + '(..)'
        ps = [p for p in r['parents'] if p in self.recs]
        if not ps: return o + '(?)'
        return o + '(' + ','.join(sorted(self.chain(p, depth - 1) for p in ps)) + ')'

    def ancestors(self, i):
        seen = set(); st = [i]
        while st:
            x = st.pop()
            for p in self.recs[x]['parents']:
                if p in self.recs and p not in seen:
                    seen.add(p); st.append(p)
        return seen

    def full_chain(self, i, memo=None):
        return self.chain(i, depth=99)


def fmt(m):
    return '%d/%d/%d/%d' % tuple(m)


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join('---' for _ in head) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(x) for x in r) + ' |')
    return '\n'.join(out)
