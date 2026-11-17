"""TimedValueSet: per-input arrivals and per-target deadlines (core/timed.py)."""
import random
import unittest

from xorflux.core.timed import TimedValueSet
from xorflux.core.valueset import ValueSet


def _random_problem(rng, n=10, m=8, extra=30):
    rows = [rng.randrange(1, 1 << n) for _ in range(m)]
    vals = [rng.randrange(1, 1 << n) for _ in range(extra)]
    return rows, vals


def _timed_levels(n, values, arrival, dl, cap):
    """Reference: timed earliest arrival over the bank by fixpoint iteration."""
    INF = 1 << 30
    lev = {1 << i: arrival[i] for i in range(n)}
    bank = set(values) - set(lev)
    lim = INF if cap is None else cap
    changed = True
    while changed:
        changed = False
        for v in bank:
            best = INF
            for x in list(lev):
                if v ^ x in lev:
                    best = min(best, max(lev[x], lev[v ^ x]) + 1)
            if best <= min(lim, dl.get(v, INF)) and best < lev.get(v, INF):
                lev[v] = best
                changed = True
    return lev


class TimedTest(unittest.TestCase):
    def test_trivial_timing_equals_base(self):
        rng = random.Random(1)
        for _ in range(20):
            rows, vals = _random_problem(rng)
            for cap in (None, 3, 5):
                a = ValueSet(10, rows, vals, cap=cap)
                b = TimedValueSet(10, rows, vals, cap=cap)
                self.assertEqual(a.level, b.level)
                self.assertEqual(a.par, b.par)

    def test_levels_match_reference_under_edits(self):
        rng = random.Random(2)
        for trial in range(30):
            n = 10
            rows, vals = _random_problem(rng, n)
            arrival = [rng.randrange(0, 4) for _ in range(n)]
            dl = [rng.choice([None, 4, 5, 6, 7]) for _ in rows]
            cap = rng.choice([None, 7, 8])
            st = TimedValueSet(n, rows, vals, cap=cap, pairsums=bool(trial % 2),
                               arrival=arrival, deadline=dl)
            dmap = {}
            for t, d in zip(rows, dl):
                if d is not None:
                    dmap[t] = min(d, dmap.get(t, 99))
            for step in range(40):
                j = st.journal()
                if rng.random() < 0.5:
                    st.add(rng.randrange(1, 1 << n))
                else:
                    vs = st.values()
                    if vs:
                        st.remove([rng.choice(vs)])
                ref = _timed_levels(n, list(st.tri), arrival, dmap, cap)
                self.assertEqual(ref, st.level)
                st.check()
                if rng.random() < 0.5:
                    st.rollback(j)
                else:
                    st.commit(j)
                ref = _timed_levels(n, list(st.tri), arrival, dmap, cap)
                self.assertEqual(ref, st.level)
                for i, a in enumerate(arrival):
                    self.assertEqual(st.level[1 << i], a)

    def test_ok_means_deadlines_met(self):
        # x0 ^ x1 at level 1, but x1 arrives at 3: realized at 4; deadline 3 -> stuck
        st = TimedValueSet(2, [3], [], cap=None, arrival=[0, 3], deadline=[3])
        self.assertFalse(st.ok())
        st = TimedValueSet(2, [3], [], cap=None, arrival=[0, 3], deadline=[4])
        self.assertTrue(st.ok())
        self.assertEqual(st.level[3], 4)


if __name__ == '__main__':
    unittest.main()
