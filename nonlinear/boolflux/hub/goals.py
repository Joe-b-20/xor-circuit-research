"""User goal list (BRIEF-ADDENDUM-0135, 2026-11-15) as data, and a goal value function for circuits and
archive states.  Used by hub/scheduler_goal.py and strategies/X2/ab_compare.py.  Pure Python, no hub imports.

A metric tuple is m = (A, AD, G, GD) (#AND, AND depth, #gates, gate depth; NIST library, every gate counted).

Goal g = caps (A, AD, G, GD), None = unconstrained; a circuit MEETS g iff every coordinate is <= its cap.
Goals are in the user's priority order A > B > ... > G; inside one circuit the user's order is lexicographic
#AND > AND depth > #gates > gate depth.

Distance of a circuit to a goal (design choice, [H]):
    deficit d = (dA, dAD, dG, dGD), dX = max(0, X - cap_X)
    key(g, m) = (dA, dAD, dG + dGD, dG)      compared lexicographically (0,0,0,0) = goal met
  An AND over the cap outranks any AND-depth excess, which outranks any gate excess.  G and GD excess are
  added (both must reach 0, and on the A28 fronts one GD level costs about 1-3 gates), ties broken by G.
  scalar(g, m) = 1000 dA + 100 dAD + dG + dGD  (order-preserving while dG + dGD < 100, true for every
  circuit within reach of a goal).
State value of an archive (a set of tuples): for every goal in priority order, the min key over the
archive; two states are compared lexicographically over the goals, so progress on a higher-priority goal
outranks any progress on a lower one (state_key).  Secondary (reported, not ranked): the number of distinct
stepping-stone tuples per goal.

Stepping stone for g: a circuit that violates at most ONE coordinate of g, by at most REACH[coordinate]
(A 1, AD 1, G 15, GD 4).  Example (brief): 28-AND circuits at AD4 with GD <= 22 and any G within 15 are
stepping stones for goal B.  For goal A (A <= 27) the stepping stones are the 28-AND circuits.
"""
from __future__ import annotations

from dataclasses import dataclass, field

COORD = ('A', 'AD', 'G', 'GD')
REACH = {'A': 1, 'AD': 1, 'G': 15, 'GD': 4}


@dataclass(frozen=True)
class Goal:
    name: str
    A: int | None = None
    AD: int | None = None
    G: int | None = None
    GD: int | None = None
    note: str = ''
    best_known: tuple = field(default=(), compare=False)

    def caps(self):
        return (self.A, self.AD, self.G, self.GD)

    def label(self):
        return '/'.join('*' if v is None else ('<=%d' % v) for v in self.caps())


# The user's ordered list (addendum 01:35 UTC). best_known = the brief's "best now" tuples (for reference).
GOALS = (
    Goal('A', 27, None, None, None, 'ultimate goal: 27 ANDs or fewer', ((28, 4, 131, 23), (28, 5, 127, 22))),
    Goal('B', 28, 4, 130, 22, '28/4/G<=130/GD<=22', ((28, 4, 131, 23), (28, 4, 133, 20), (29, 4, 130, 22))),
    Goal('C', 28, 5, 127, 19, '28/5/G<=127/GD<=19', ((28, 5, 127, 22), (28, 5, 130, 19))),
    Goal('D', 32, 4, 116, 19, 'A<=32/AD4/G<=116/GD<=19', ((32, 4, 116, 20), (32, 4, 119, 18), (33, 4, 108, 19))),
    Goal('E', 32, 6, 102, 31, 'A<=32/AD<=6/G<=102/GD<=31', ((32, 5, 104, 29),)),
    Goal('F', 35, 3, 138, 26, 'A<=35/AD3/G<=138/GD<=26', ((35, 3, 140, 25), (35, 3, 141, 24))),
    Goal('G', 44, 4, 140, 11, 'A<=44/AD<=4/G<=140/GD<=11', ((48, 4, 151, 11), (43, 4, 141, 12))),
)
BY_NAME = {g.name: g for g in GOALS}
NAMES = tuple(g.name for g in GOALS)


def goal(name):
    return BY_NAME[name]


def deficit(g, m):
    return tuple(0 if c is None else max(0, x - c) for x, c in zip(m, g.caps()))


def key(g, m):
    dA, dAD, dG, dGD = deficit(g, m)
    return (dA, dAD, dG + dGD, dG)


def scalar(g, m):
    dA, dAD, dG, dGD = deficit(g, m)
    return 1000 * dA + 100 * dAD + dG + dGD


def meets(g, m):
    return deficit(g, m) == (0, 0, 0, 0)


def met_goals(m):
    return [g.name for g in GOALS if meets(g, m)]


def stepping(g, m):
    """violates at most one coordinate of g, by at most REACH of that coordinate (a goal-meeting circuit is not a
    stepping stone)"""
    d = deficit(g, m)
    bad = [(k, v) for k, v in zip(COORD, d) if v > 0]
    return len(bad) == 1 and bad[0][1] <= REACH[bad[0][0]]


def best(g, points):
    """(key, tuple) of the point nearest to g (lexicographic key, ties by the tuple itself)"""
    b = None
    for m in points:
        k = (key(g, m), tuple(m))
        if b is None or k < b: b = k
    return b


def state(points):
    """goal-by-goal value of an archive state: {name: {'key', 'm', 'scalar', 'met', 'stones'}}"""
    pts = {tuple(m) for m in points}
    out = {}
    for g in GOALS:
        b = best(g, pts)
        out[g.name] = {'key': b[0] if b else None, 'm': b[1] if b else None,
                       'scalar': scalar(g, b[1]) if b else None, 'met': bool(b) and meets(g, b[1]),
                       'stones': sum(1 for m in pts if stepping(g, m))}
    return out


def state_key(st):
    """total order on archive states: goal keys in priority order (smaller = better)"""
    return tuple(st[n]['key'] for n in NAMES)


def step_gain(k_from, k_to):
    """bandit reward for moving from goal key k_from to k_to (0 if not closer): tiered like the hub's 8/4/2/1,
    lexicographic in the deficit: lower dA 8, lower dAD 4, else 1 per unit of dG + dGD (at most 4), and 0.25
    for a pure G-for-GD trade that lowers dG at the same sum"""
    if k_from is None or k_to >= k_from: return 0.0
    if k_to[0] < k_from[0]: return 8.0
    if k_to[1] < k_from[1]: return 4.0
    if k_to[2] < k_from[2]: return float(min(4, k_from[2] - k_to[2]))
    return 0.25


def parse_shares(s):
    """'A=0.1,B=0.2,...' -> dict"""
    out = {}
    for kv in (s or '').split(','):
        if kv.strip():
            k, v = kv.split('='); out[k.strip()] = float(v)
    return out
