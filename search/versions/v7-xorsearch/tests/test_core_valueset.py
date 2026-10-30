"""Correctness of the incremental kernel ``core.valueset`` against from-scratch recomputation.

Ported from the profiling prototype's suite (an earlier version) with the legacy
kernels replaced by small, obviously-correct references written here:

* ``naive_levels``: a plain fixpoint over all pairs (no index, no BFS tricks);
* brute-force repair: try every possible useful value with a fresh level computation;
* fresh rebuilds: because witnesses are canonical, a ValueSet rebuilt from ``values()`` must
  equal the incrementally edited one exactly (levels, parents, children).

Random sequences of remove / add / trim / restore / repair / extract / peel run on the real
seeds (joltik 44, aes-invmixcolumns 88@19, fox-mu4 130, fox-mu8 540) under several caps,
inside journals that are randomly committed or rolled back.
"""
import random
import unittest

from xorsearch.core.budget import Budget
from xorsearch.core.circuit import Circuit, verify
from xorsearch.core.target import Target, load_target, random_target
from xorsearch.tests import fixtures
from xorsearch.core.valueset import ValueSet, earliest_scan

INF = float('inf')


def naive_levels(values, n, cap=None):
    """Reference earliest-arrival levels: iterate level[v] = 1 + min max(level a, level b)."""
    U = set(1 << i for i in range(n)) | {v for v in values if v}
    level = {1 << i: 0 for i in range(n)}
    rest = [v for v in U if v not in level]
    changed = True
    while changed:
        changed = False
        for v in rest:
            best = level.get(v, INF)
            for a in level:
                b = v ^ a
                lb = level.get(b)
                if lb is not None:
                    m = 1 + max(level[a], lb)
                    if m < best and (cap is None or m <= cap):
                        best = m
            if best < level.get(v, INF):
                level[v] = best
                changed = True
    return level


def seed_state(name, gates, cap=None, pairsums=False):
    target = load_target(name)
    seed = next(s for s in fixtures.seeds(target) if s.gates == gates)
    vs = ValueSet(target.n_inputs, target.rows, seed.load(target.n_inputs).masks(), cap=cap,
                  pairsums=pairsums)
    vs.trim()
    return target, vs


def stuck_of(vs):
    """Values of U without a level."""
    return {v for v in vs.tri if v not in vs.level}


def emitted(vs):
    """The live witness DAG as a ``core.circuit.Circuit``."""
    return Circuit(vs.n, *vs.gates())


def frozen(vs):
    """Deep copy of the observable state, for exact before/after comparisons."""
    return (dict(vs.level), dict(vs.par), {k: frozenset(v) for k, v in vs.kids.items()},
            {k: frozenset(v) for k, v in vs.tri.items()}, vs.cap)


def assert_fresh_equal(tc, vs):
    """The edited state equals a fresh build from its values (canonical witnesses).  The
    constructor always adds the targets, so targets the edits removed are removed again."""
    fresh = ValueSet(vs.n, vs.rows, vs.values(), cap=vs.cap)
    missing = [t for t in vs.targets if t not in vs.tri]
    if missing:
        fresh.remove(missing)
    tc.assertEqual(fresh.level, vs.level)
    tc.assertEqual(fresh.par, vs.par)
    tc.assertEqual(fresh.kids, vs.kids)
    tc.assertEqual(fresh.tri, vs.tri)


def assert_circuit(tc, vs, target):
    """The emitted circuit verifies independently and matches the kernel's metrics."""
    v = verify(emitted(vs), target, cap=vs.cap)
    tc.assertTrue(v.ok, v.reason)
    tc.assertEqual(v.gate_count, vs.size())
    tc.assertEqual(v.dead_gates, 0)
    tc.assertEqual(v.depth, vs.depth())


def brute_repairs(vs, forbid):
    """Every single value whose insertion makes all targets realizable, by brute force.

    A useful value must itself be realizable, so it is a XOR of two realized values; trying
    every such pair sum with a fresh level computation is therefore complete.
    """
    avail = sorted(v for v in vs.tri if v in vs.level)
    U = set(vs.tri)
    out = set()
    for i, a in enumerate(avail):
        for b in avail[i + 1:]:
            w = a ^ b
            if w in U or w in forbid or w in out:
                continue
            lev, _, _ = earliest_scan(list(U) + [w], vs.n, vs.cap)
            if all(t in lev for t in vs.targets):
                out.add(w)
    return out


class EarliestScanTest(unittest.TestCase):
    def test_matches_naive_on_random_banks(self):
        rng = random.Random(1)
        for trial in range(60):
            n = rng.randint(3, 9)
            bank = {rng.randrange(1, 1 << n) for _ in range(rng.randint(1, 40))}
            for cap in (None, 0, 1, 2, 3):
                lev, par, unres = earliest_scan(bank, n, cap, parents=True)
                ref = naive_levels(bank, n, cap)
                self.assertEqual(lev, ref)
                self.assertEqual(set(unres), {v for v in bank if v not in ref})
                for v, a in par.items():
                    self.assertEqual(max(ref[a], ref[v ^ a]), ref[v] - 1)

    def test_real_seed_levels(self):
        target, vs = seed_state('fox-mu4', 130)
        self.assertEqual(earliest_scan(vs.values(), vs.n)[0],
                         naive_levels(vs.values(), vs.n))

    def test_values_outside_the_inputs_are_unresolved(self):
        # Regression: 1 | 1 << n has popcount 2 and used to get level 1 over n inputs.
        n = 4
        foreign = [1 | 1 << n, 1 << n, -3]
        lev, _, unres = earliest_scan([0b0011, 0b0111, 0] + foreign, n)
        self.assertEqual(lev, {1: 0, 2: 0, 4: 0, 8: 0, 0b0011: 1, 0b0111: 2})
        self.assertEqual(sorted(unres), sorted(foreign))
        self.assertEqual(sorted(earliest_scan(foreign, n, cap=0)[2]), sorted(foreign))


class EdgeTargetTest(unittest.TestCase):
    """Unit-vector rows, repeated rows and zero rows."""

    def setUp(self):
        n = 6
        a, b = 0b000111, 0b111000
        self.rows = [1, 4, 0, a, a, b, 4, a ^ b]
        self.target = Target.make('edge', n, self.rows)
        self.vs = ValueSet(n, self.rows, [0b11, 0b11000, a, b, a ^ b])

    def test_realized_and_emitted(self):
        vs = self.vs
        vs.check()
        self.assertTrue(vs.ok())
        self.assertEqual(vs.targets, (1, 4, self.rows[3], self.rows[5], self.rows[7]))
        gates, outputs = vs.gates()
        self.assertEqual(outputs[0], 0)            # unit row: input 0
        self.assertEqual(outputs[1], 2)            # unit row: input 2
        self.assertEqual(outputs[2], -1)           # zero row: constant
        self.assertEqual(outputs[3], outputs[4])   # repeated row: same signal
        self.assertEqual(outputs[1], outputs[6])
        v = verify(emitted(vs), self.target)
        self.assertTrue(v.ok, v.reason)
        self.assertEqual(v.gate_count, vs.size())

    def test_inputs_never_removed(self):
        vs = self.vs
        before = frozen(vs)
        u = vs.remove(vs.inputs)
        self.assertEqual(u.removed, ())
        self.assertEqual(frozen(vs), before)
        vs.trim()
        vs.peel(random.Random(0))
        self.assertTrue(all(i in vs.tri for i in vs.inputs))

    def test_only_free_rows(self):
        vs = ValueSet(4, [0, 2, 8, 0])
        self.assertTrue(vs.ok())
        self.assertEqual(vs.depth(), 0)
        self.assertEqual(vs.size(), 0)
        self.assertEqual(vs.gates(), ([], [-1, 1, 3, -1]))

    def test_targets_always_in_u(self):
        vs = ValueSet(6, self.rows, [])
        self.assertTrue(all(t in vs.tri for t in vs.targets))
        self.assertFalse(vs.ok())
        self.assertIsNone(vs.depth())
        with self.assertRaises(ValueError):
            vs.gates()

    def test_bad_values_rejected(self):
        with self.assertRaises(ValueError):
            ValueSet(3, [1 << 3])
        with self.assertRaises(ValueError):
            ValueSet(3, [3], [64])


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.target, self.vs = seed_state('joltik', 44, pairsums=True)

    def test_rollback_exact_and_commit(self):
        vs = self.vs
        rng = random.Random(5)
        before = frozen(vs)
        j = vs.journal()
        vals = [v for v in vs.values() if v not in vs.tset]
        vs.remove(rng.sample(vals, 3))
        allv = list(vs.tri)
        for _ in range(5):
            vs.add(rng.choice(allv) ^ rng.choice(allv))
        vs.trim()
        added, removed = j.changes()
        self.assertTrue(added or removed)
        vs.rollback(j)
        self.assertEqual(frozen(vs), before)
        self.assertIsNone(vs._log)
        vs.check()
        j = vs.journal()
        vs.remove(vals[:1])
        vs.commit(j)
        self.assertNotIn(vals[0], vs.tri)
        with self.assertRaises(ValueError):
            vs.rollback(j)

    def test_nested_and_changes(self):
        vs = self.vs
        vals = [v for v in vs.values() if v not in vs.tset]
        outer = vs.journal()
        vs.remove(vals[:2])
        mid = frozen(vs)
        inner = vs.journal()
        w = vals[0]
        vs.add(w)
        vs.remove(vals[2:3])
        vs.rollback(inner)
        self.assertEqual(frozen(vs), mid)
        inner = vs.journal()
        vs.add(w)
        vs.commit(inner)
        added, removed = outer.changes()
        self.assertEqual(added, [])
        self.assertEqual(removed, [vals[1]])
        self.assertTrue(outer.open)
        vs.rollback(outer)
        self.assertIn(vals[1], vs.tri)

    def test_restore_inside_journal(self):
        vs = self.vs
        before = frozen(vs)
        j = vs.journal()
        u = vs.remove([v for v in vs.values() if v not in vs.tset][:2])
        vs.restore(u)
        self.assertEqual(len(vs._log), j.mark)       # the restore cancelled the remove
        u = vs.remove([v for v in vs.values() if v not in vs.tset][:1])
        vs.add(vs.inputs[0] ^ vs.inputs[5])
        with self.assertRaises(ValueError):
            vs.restore(u)                    # not the most recent journaled edit
        vs.rollback(j)
        self.assertEqual(frozen(vs), before)


class HelpersTest(unittest.TestCase):
    def test_size_count_live(self):
        target, vs = seed_state('joltik', 44)
        self.assertEqual(vs.size(), 44)
        self.assertEqual(vs.count(), 44)
        vals = vs.values()
        w = next(a ^ b for a in vals for b in vals if a ^ b and a ^ b not in vs.tri)
        self.assertTrue(vs.add(w))
        self.assertEqual(vs.count(), 45)
        self.assertEqual(vs.size(), 44)
        vs.trim()
        self.assertEqual(vs.count(), 44)
        self.assertEqual(vs.key(), frozenset(vs.values()))

    def test_seed_circuits(self):
        target = load_target('aes-invmixcolumns')
        for seed in target.seeds[:4]:
            vs = ValueSet(target.n_inputs, target.rows, seed.load().masks())
            vs.trim()
            self.assertEqual(vs.size(), seed.gates)
            self.assertLessEqual(vs.depth(), seed.depth)
            assert_circuit(self, vs, target)
            vs.check()


class RepairTest(unittest.TestCase):
    """Complete single-value repair enumeration against brute force."""

    def run_states(self, vs, rng, states):
        done = 0
        tries = 0
        while done < states and tries < 400:
            tries += 1
            vals = [v for v in vs.values() if v not in vs.tset]
            D = rng.sample(vals, min(len(vals), rng.randint(1, 2)))
            u = vs.remove(D)
            if u.stuck & vs.tset:
                ref = brute_repairs(vs, set(D))
                self.assertEqual(set(vs.valid_repairs(u.stuck, D)), ref)
                cands = vs.repair_candidates(u.stuck, D)
                saved = vs.p2
                vs.p2 = None
                self.assertEqual(set(vs.valid_repairs(u.stuck, D)), ref)
                self.assertEqual(vs.repair_candidates(u.stuck, D), cands)   # counter == scan
                vs.p2 = saved
                self.assertEqual(cands, sorted(cands))
                self.assertTrue(ref <= set(cands))
                done += 1
            vs.restore(u)
        self.assertEqual(done, states)

    def test_joltik_uncapped_and_capped(self):
        rng = random.Random(11)
        for cap in (None, 7, 6):
            target, vs = seed_state('joltik', 44, cap=cap, pairsums=True)
            self.run_states(vs, rng, 6)
            vs.check()

    def test_random_small_targets(self):
        rng = random.Random(12)
        for k in range(4):
            target = random_target(7, 6, density=0.5, seed=k)
            bank = set()
            while True:
                bank |= {rng.randrange(3, 1 << 7) for _ in range(6)}
                vs = ValueSet(7, target.rows, bank, pairsums=True)
                if vs.ok():
                    break
            vs.peel(rng)
            if all(v in vs.tset for v in vs.values()):
                continue                     # no helper values: nothing to remove
            cap = vs.depth() if k % 2 else None
            vs = ValueSet(7, target.rows, vs.values(), cap=cap, pairsums=True)
            self.run_states(vs, rng, 3)


class PairSumCounterTest(unittest.TestCase):
    """The lazy counter path of ``repair_candidates`` equals the plain scan with any mix of
    pending (unsynced) adds and removes, inside nested journals."""

    def scan(self, vs, stuck, forbid=()):
        saved = vs.p2
        vs.p2 = None
        try:
            return vs.repair_candidates(stuck, forbid), vs.valid_repairs(set(stuck), forbid)
        finally:
            vs.p2 = saved

    def test_pending_changes_match_scan(self):
        rng = random.Random(31)
        checked = 0
        for trial in range(40):
            n = rng.randint(5, 9)
            target = random_target(n, rng.randint(2, 5), density=0.5, seed=200 + trial)
            bank = {rng.randrange(3, 1 << n) for _ in range(rng.randint(8, 30))}
            vs = ValueSet(n, target.rows, bank, cap=rng.choice((None, 3, 4)), pairsums=True)
            outer = vs.journal()               # syncs nothing: the counter was just built
            for it in range(12):
                inner = vs.journal()
                vals = vs.values()
                if vals:
                    vs.remove(rng.sample(vals, min(len(vals), rng.randint(1, 3))))
                for _ in range(rng.randint(0, 3)):
                    vs.add(rng.randrange(1, 1 << n))
                stuck = stuck_of(vs)
                if stuck:
                    forbid = tuple(rng.sample(sorted(vs.p2_removed), min(1, len(vs.p2_removed))))
                    got = vs.repair_candidates(stuck, forbid), vs.valid_repairs(stuck, forbid)
                    self.assertEqual(got, self.scan(vs, stuck, forbid))
                    if vs.p2_added or vs.p2_removed:
                        checked += 1
                if rng.random() < 0.5:
                    vs.rollback(inner)
                else:
                    vs.commit(inner)
            vs.rollback(outer)
            vs.check()                           # the counter itself is still exact
        self.assertGreater(checked, 100)

    def test_outermost_journal_syncs_committed_changes(self):
        target, vs = seed_state('joltik', 44, pairsums=True)
        vals = [v for v in vs.values() if v not in vs.tset]
        j = vs.journal()
        vs.remove(vals[:2])
        vs.add(vals[0] ^ vals[5])
        vs.commit(j)
        self.assertTrue(vs.p2_removed or vs.p2_added)
        j = vs.journal()
        self.assertFalse(vs.p2_removed or vs.p2_added)
        vs.rollback(j)
        vs.check()

    def test_duplicate_and_realized_stuck_values(self):
        # Regression: a repeated stuck value was counted twice as a touched pair, which hid
        # real candidates on the counter path.
        rng = random.Random(32)
        target, vs = seed_state('joltik', 44, pairsums=True)
        vals = [v for v in vs.values() if v not in vs.tset]
        seen = 0
        for v in rng.sample(vals, len(vals)):
            u = vs.remove((v,))
            if u.stuck & vs.tset:
                stuck = sorted(u.stuck)
                ref = vs.repair_candidates(stuck, (v,))
                noisy = stuck + stuck + vals[:3]     # repeats and realized values
                self.assertEqual(vs.repair_candidates(noisy, (v,)), ref)
                self.assertEqual(self.scan(vs, noisy, (v,))[0], ref)
                self.assertEqual(vs.valid_repairs(stuck, (v,)),
                                 vs.valid_repairs(set(stuck), (v,)))
                seen += 1
            vs.restore(u)
            if seen >= 5:
                break
        self.assertEqual(seen, 5)


class RandomEditTest(unittest.TestCase):
    """Long random edit sequences on real seeds, checked from scratch."""

    def run_case(self, name, gates, iters, check_every, naive):
        rng = random.Random(gates)
        target, base = seed_state(name, gates)
        depth = base.depth()
        for cap in (None, depth, depth + 1):
            vs = ValueSet(base.n, base.rows, base.values(), cap=cap, pairsums=True)
            vs.check()
            for it in range(iters):
                before = frozen(vs)
                j = vs.journal()
                vals = [v for v in vs.values() if v not in vs.tset]
                D = rng.sample(vals, min(len(vals), rng.randint(1, 4)))
                pre_stuck = stuck_of(vs) - set(D)
                u = vs.remove(D)
                # Exact stuck set against a from-scratch level computation.
                ref = (naive_levels(vs.tri, vs.n, cap) if naive and it % 5 == 0
                       else earliest_scan(vs.values(), vs.n, cap)[0])
                self.assertEqual(u.stuck | pre_stuck, {v for v in vs.tri if v not in ref})
                if u.stuck & vs.tset and rng.random() < 0.7:
                    repairs = vs.valid_repairs(u.stuck | pre_stuck, D)
                    if repairs:
                        vs.add(rng.choice(repairs))
                        self.assertTrue(vs.ok())
                allv = list(vs.tri)
                for _ in range(rng.randint(0, 3)):
                    vs.add(rng.choice(allv) ^ rng.choice(allv))
                if rng.random() < 0.5:
                    vs.trim()
                    self.assertEqual(vs.count(), vs.size())
                if it % check_every == 0:
                    vs.check()
                    assert_fresh_equal(self, vs)
                if rng.random() < 0.4 and vs.ok():
                    vs.trim()
                    vs.commit(j)
                    if it % check_every == 0:
                        assert_circuit(self, vs, target)
                else:
                    vs.rollback(j)
                    self.assertEqual(frozen(vs), before)
            # Greedy rebuild, then peel to 1-minimal, all inside one rolled-back journal.
            for k in range(max(2, iters // 20)):
                before = frozen(vs)
                j = vs.journal()
                kept = set(vs.values())
                allv = list(vs.tri)
                for _ in range(20):
                    vs.add(rng.choice(allv) ^ rng.choice(allv))
                cost = {v: (1 if v in kept else 2) for v in vs.values()}
                chosen = vs.extract(cost, random.Random(k), noise=0.0625)
                self.assertEqual(chosen, vs.extract(cost, random.Random(k), noise=0.0625))
                vs.retain(chosen)
                vs.trim()
                self.assertTrue(vs.ok())
                self.assertTrue(set(vs.values()) <= chosen)
                assert_circuit(self, vs, target)
                vs.peel(random.Random(k))
                vs.check()
                assert_circuit(self, vs, target)
                if naive:
                    for v in vs.values():
                        if v not in vs.tset:
                            rest = [x for x in vs.values() if x != v]
                            lev = earliest_scan(rest, vs.n, cap)[0]
                            self.assertFalse(all(x in lev for x in rest), 'peel not 1-minimal')
                vs.rollback(j)
                self.assertEqual(frozen(vs), before)

    def test_joltik(self):
        self.run_case('joltik', 44, 300, 10, naive=True)

    def test_invmixcolumns(self):
        self.run_case('aes-invmixcolumns', 88, 250, 20, naive=False)

    def test_fox_mu4(self):
        self.run_case('fox-mu4', 130, 200, 20, naive=False)

    def test_fox_mu8(self):
        self.run_case('fox-mu8', 540, 30, 10, naive=False)


class DenseBankTest(unittest.TestCase):
    """Small dense random banks: many tied recipes, tight caps, dead chains.

    Real seeds have few alternative recipes per value, so canonical tie-breaking, cap pruning
    and trim cascades are exercised much harder here.
    """

    def test_random_dense_banks(self):
        rng = random.Random(21)
        for trial in range(60):
            n = rng.randint(4, 7)
            target = random_target(n, rng.randint(1, 5), density=0.6, seed=trial)
            bank = {rng.randrange(1, 1 << n) for _ in range(rng.randint(5, 3 << n >> 1))}
            cap = rng.choice((None, 1, 2, 3, 4))
            vs = ValueSet(n, target.rows, bank, cap=cap, pairsums=trial % 2 == 0)
            vs.check()
            assert_fresh_equal(self, vs)
            for it in range(25):
                before = frozen(vs)
                j = vs.journal()
                vals = vs.values()
                if vals:
                    vs.remove(rng.sample(vals, min(len(vals), rng.randint(1, 5))))
                for _ in range(rng.randint(0, 4)):
                    vs.add(rng.randrange(1, 1 << n))
                if rng.random() < 0.5:
                    vs.trim()
                    self.assertEqual(vs.count(), vs.size())
                    self.assertTrue(stuck_of(vs) <= vs.tset)
                vs.check()
                assert_fresh_equal(self, vs)
                stuck = stuck_of(vs)
                if stuck & vs.tset and it % 3 == 0:
                    self.assertEqual(set(vs.valid_repairs(stuck)), brute_repairs(vs, set()))
                if vs.ok():
                    assert_circuit(self, vs, target)
                if rng.random() < 0.5:
                    vs.rollback(j)
                    self.assertEqual(frozen(vs), before)
                else:
                    vs.commit(j)

    def test_wide_dense_banks(self):
        # With n <= 7 every mask is below the hash-table size, so set iteration happens to be
        # ascending and order-dependent tie-breaking would go unnoticed.  Wider masks scramble
        # the iteration order; dense banks make tied recipes and values at the cap common.
        rng = random.Random(22)
        for trial in range(14):
            n = rng.randint(10, 11)
            target = random_target(n, 4, density=0.5, seed=100 + trial)
            sub = [rng.randrange(1, 1 << n) for _ in range(7)]
            bank = set()
            for _ in range(140):             # sums of a few generators: many triples
                v = 0
                for g in rng.sample(sub, rng.randint(1, 4)):
                    v ^= g
                bank.add(v ^ (1 << rng.randrange(n)) if rng.random() < 0.3 else v)
            bank.update(rng.randrange(1, 1 << n) for _ in range(40))
            cap = rng.choice((None, 2, 3, 4))
            vs = ValueSet(n, target.rows, bank, cap=cap)
            for it in range(20):
                before = frozen(vs)
                j = vs.journal()
                vs.remove(rng.sample(vs.values(), 3))
                for _ in range(3):
                    vs.add(rng.choice(list(vs.tri)) ^ rng.choice(list(vs.tri)))
                vs.check()
                if rng.random() < 0.5:
                    vs.rollback(j)
                    self.assertEqual(frozen(vs), before)
                else:
                    vs.commit(j)

    def test_trim_cascade(self):
        # A dead chain x -> y -> z hanging off a target: trim removes all of it at once.
        n = 5
        x, y, z = 0b00011, 0b00111, 0b01111
        vs = ValueSet(n, [0b11000], [x, y, z])
        self.assertEqual(vs.count(), 4)
        vs.trim()
        self.assertEqual(vs.values(), [0b11000])
        self.assertEqual(vs.count(), vs.size())


class DeterminismTest(unittest.TestCase):
    def test_history_independent(self):
        """Two different edit histories reaching the same U give identical states, gates and
        RNG-driven results."""
        target, a = seed_state('aes-invmixcolumns', 88)
        rng = random.Random(3)
        vals = a.values()
        rest = vals[1::2]
        rng.shuffle(rest)
        b = ValueSet(a.n, a.rows, vals[::2])
        extra = sorted({rng.choice(vals) ^ rng.choice(vals) for _ in range(40)} - set(a.tri))
        for w in extra[:20] + rest + extra[20:]:
            b.add(w)
        b.remove(extra)
        self.assertEqual(frozen(a), frozen(b))
        self.assertEqual(a.gates(), b.gates())
        cost = {v: 1 + (v & 3) for v in a.values()}
        self.assertEqual(a.extract(cost, random.Random(9), 0.1), b.extract(cost, random.Random(9), 0.1))
        a.peel(random.Random(4))
        b.peel(random.Random(4))
        self.assertEqual(a.key(), b.key())

    def test_peel_quick_reject_is_exact(self):
        """peel() skips trials that must fail; the result equals the plain trial loop."""
        def plain_peel(vs, rng):
            progress = True
            while progress:
                progress = False
                order = sorted(v for v in vs.tri if v not in vs.iset and v not in vs.tset)
                rng.shuffle(order)
                for v in order:
                    if v in vs.tri:
                        u = vs.remove((v,))
                        if u.stuck:
                            vs.restore(u)
                        else:
                            progress = True
        for name, gates in (('aes-invmixcolumns', 88), ('fox-mu4', 130)):
            target, base = seed_state(name, gates)
            rng = random.Random(gates)
            vals = base.values()
            extra = [rng.choice(vals) ^ rng.choice(vals) for _ in range(25)]
            for cap in (None, base.depth()):
                a = ValueSet(base.n, base.rows, vals + extra, cap=cap)
                b = ValueSet(base.n, base.rows, vals + extra, cap=cap)
                a.peel(random.Random(7))
                plain_peel(b, random.Random(7))
                self.assertEqual(a.key(), b.key())
                a.check()

    def test_strands_screen_matches_trial_removal(self):
        rng = random.Random(23)
        for trial in range(40):
            n = rng.randint(4, 9)
            target = random_target(n, rng.randint(1, 5), density=0.6, seed=300 + trial)
            bank = {rng.randrange(1, 1 << n) for _ in range(rng.randint(5, 40))}
            cap = rng.choice((None, None, 2, 3, 4))
            vs = ValueSet(n, target.rows, bank, cap=cap)
            before = frozen(vs)
            for v in vs.values():
                screen = vs.strands(v)
                screen_t = vs.strands(v, vs.tset)
                u = vs.remove((v,))
                fails = bool(u.stuck)
                fails_t = bool(u.stuck & vs.tset)
                vs.restore(u)
                if cap is None:
                    self.assertEqual(screen, fails, v)
                    self.assertEqual(screen_t, fails_t, v)
                else:
                    if screen:
                        self.assertTrue(fails, v)
                    if screen_t:
                        self.assertTrue(fails_t, v)
            self.assertEqual(frozen(vs), before)

    def test_peel_budget(self):
        target, vs = seed_state('fox-mu4', 130)
        vals = vs.values()
        for k in range(20):
            vs.add(vals[k] ^ vals[-1 - k])
        budget = Budget(limit=5)
        vs.peel(random.Random(0), budget)
        self.assertEqual(budget.used, 5)


if __name__ == '__main__':
    unittest.main()
