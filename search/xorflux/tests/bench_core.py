"""Benchmark of the core kernel primitives on the real seeds (not run by the test suite).

Reproduces the primitive timings measured for earlier versions for ``ValueSet`` so
later optimisations can be measured against fixed numbers:

    python3 -m xorflux.tests.bench_core                  # all four cases
    python3 -m xorflux.tests.bench_core invmc88 foxmu8_540

Cases (live value sets of the seeds in search/seeds/ and tests/data/):
    joltik44     joltik          16 inputs,  44 values
    invmc88      aes-invmixcolumns 32 inputs,  88 values (depth 19)
    foxmu4_130   fox-mu4         32 inputs, 130 values
    foxmu8_540   fox-mu8         64 inputs, 540 values

Times are best-of-5 per call.  "bank" is an LNS-style bank: the seed minus 3 victims plus 30
random pair sums of kept values, built with the same RNG recipe as the evidence report.
"""
import random
import sys
import time
import timeit

from xorflux.core.circuit import Circuit, normalise, verify
from xorflux.core.target import load_target
from xorflux.tests import fixtures
from xorflux.core.valueset import ValueSet, earliest_scan

CASES = {  # name -> (catalog target, seed gate count, seed index among equal gate counts)
    'joltik44': ('joltik', 44, 0),
    'invmc88': ('aes-invmixcolumns', 88, -1),
    'foxmu4_130': ('fox-mu4', 130, 0),
    'foxmu8_540': ('fox-mu8', 540, 0),
}


def best(fn, number=None, repeat=5):
    """Best-of-``repeat`` seconds per call; ``number`` calls per repeat (auto: ~0.2 s)."""
    if number is None:
        t0 = time.perf_counter()
        fn()
        one = time.perf_counter() - t0
        number = max(1, min(200, int(0.2 / max(one, 1e-6))))
    return min(timeit.repeat(fn, number=number, repeat=repeat)) / number


def fmt(s):
    return '%9.3f ms' % (s * 1e3) if s >= 1e-3 else '%9.1f us' % (s * 1e6)


def row(label, s):
    print('  %-62s %s' % (label, fmt(s)), flush=True)
    return s


def load_case(name):
    """(target, seed circuit, sorted live seed values)."""
    tid, gates, which = CASES[name]
    target = load_target(tid)
    seed = [s for s in fixtures.seeds(target) if s.gates == gates][which]
    circuit = seed.load(target.n_inputs)
    vs = ValueSet(target.n_inputs, target.rows, circuit.masks())
    vs.trim()
    return target, circuit, vs.values()


def bench(name):
    rng = random.Random(3)
    target, circuit, S = load_case(name)
    n, rows = target.n_inputs, list(target.rows)
    tset = set(rows)
    Sset = set(S)
    nont = [v for v in S if v not in tset]
    base = ValueSet(n, rows, S)
    print('=' * 100)
    print('%s: n=%d targets=%d |S|=%d depth=%d' % (name, n, len(rows), len(S), base.depth()))
    victims = rng.sample(nont, 3)
    kept = [v for v in S if v not in victims]
    extras = set()
    while len(extras) < 30:
        m = rng.choice(kept) ^ rng.choice(kept)
        if m.bit_count() > 1 and m not in Sset:
            extras.add(m)
    bank = sorted(set(kept) | extras | set(victims))

    print(' [1] earliest-arrival levels')
    for label, B in (('S', S), ('bank', bank)):
        row('%s: earliest_scan' % label, best(lambda: earliest_scan(B, n)))
        row('%s: ValueSet build (triple index + levels)' % label,
            best(lambda: ValueSet(n, rows, B), repeat=3))
        c = ValueSet(n, rows, B)

        def relevel():
            c.level = dict.fromkeys(c.inputs, 0)
            c.par = {}
            c.kids = {v: set() for v in c.tri}
            c._resolve(set(c.values()))
        row('%s: re-level all from the index (_resolve)' % label, best(relevel))

    print(' [3] remove k values -> exact stuck set (80 queries, k = 1 or 2)')
    Ds = [rng.sample(nont, k) for k in (1, 2) for _ in range(40)]
    for label, ps in (('p2 OFF', False), ('p2 ON', True)):
        c = ValueSet(n, rows, S, pairsums=ps)

        def rr():
            for D in Ds:
                c.restore(c.remove(D))
        row('remove + restore, %s' % label, best(rr) / len(Ds))

        def rj():
            for D in Ds:
                j = c.journal()
                c.remove(D)
                c.rollback(j)
        row('journal + remove + rollback, %s' % label, best(rj) / len(Ds))

    print(' [4] complete single-value repair enumeration (states with a stuck target)')
    c_on = ValueSet(n, rows, S, pairsums=True)
    c_off = ValueSet(n, rows, S)
    states = []
    for D in Ds:
        u = c_on.remove(D)
        if u.stuck & c_on.tset:
            states.append(D)
        c_on.restore(u)
    states = states[:12]
    if states:
        stuck_sizes = []
        for D in states:
            u = c_on.remove(D)
            stuck_sizes.append(len(u.stuck))
            c_on.restore(u)
        print('    %d states, mean stuck %.1f' % (len(states), sum(stuck_sizes) / len(states)))

        def rep(cc):
            total = 0
            for D in states:
                u = cc.remove(D)
                total += len(cc.valid_repairs(u.stuck, D))
                cc.restore(u)
            return total
        assert rep(c_on) == rep(c_off)
        row('remove + valid_repairs + restore, p2 ON', best(lambda: rep(c_on)) / len(states))
        row('remove + valid_repairs + restore, p2 OFF',
            best(lambda: rep(c_off), repeat=3) / len(states))

        # The expand pattern: inside one proposal, insert a first value and query
        # again, several times, rolling each insertion back (the counter sees pending adds).
        def rep_nested(cc):
            total = 0
            for D in states:
                j = cc.journal()
                u = cc.remove(D)
                for w in cc.repair_candidates(u.stuck, D)[:4]:
                    m = cc.journal()
                    cc.add(w)
                    st2 = {s for s in u.stuck if s not in cc.level}
                    total += len(cc.valid_repairs(st2, tuple(D) + (w,)))
                    cc.rollback(m)
                cc.rollback(j)
            return total
        assert rep_nested(c_on) == rep_nested(c_off)
        row('remove + 4 x (add first + valid_repairs + rollback), p2 ON',
            best(lambda: rep_nested(c_on)) / len(states))

    print(' [5] greedy top-down rebuild from the LNS bank (cost classes 1/2/3)')
    vset = set(victims)
    kset = set(kept)
    cost = {m: (1 if m in kset else 3 if m in vset else 2) for m in bank}
    cur = ValueSet(n, rows, S)

    def ext_inc():
        j = cur.journal()
        for m in extras:
            cur.add(m)
        res = cur.extract(cost, rng, 0.0625)
        cur.rollback(j)
        return res
    row('incremental: journal + add 30 extras + extract + rollback', best(ext_inc))

    def ext_full():
        j = cur.journal()
        for m in extras:
            cur.add(m)
        res = cur.extract(cost, rng, 0.0625)
        cur.retain(res)
        cur.trim()
        size = cur.size()
        cur.rollback(j)
        return size
    row('  + retain + trim + size (full LNS proposal body)', best(ext_full))
    cb = ValueSet(n, rows, bank)
    row('  extract alone on an indexed bank', best(lambda: cb.extract(cost, rng, 0.0625)))
    fresh = set()
    while len(fresh) < 30:
        m = rng.choice(bank) ^ rng.choice(bank)
        if m.bit_count() > 1 and m not in cb.tri:
            fresh.add(m)
    row('  add one value (scan) [30 adds + rollback]/30', best(lambda: _addrem(cb, fresh)) / 30)
    cbp = ValueSet(n, rows, bank, pairsums=True)
    row('  add one value, p2 ON [30 adds + rollback]/30', best(lambda: _addrem(cbp, fresh)) / 30)

    print(' [6] peel (1-minimal) and trim on an extract result + 6 redundant values')
    res = sorted(cb.extract(cost, random.Random(1), 0.0625))
    red = list(res)
    for m in sorted(extras)[:6]:
        if m not in red:
            red.append(m)

    def peel():
        cc = ValueSet(n, rows, red)
        cc.peel(random.Random(2))
        cc.trim()
        return cc
    row('ValueSet(set) + peel + trim', best(peel, number=1, repeat=3))
    c0 = ValueSet(n, rows, red)
    row('live()', best(c0.live))
    row('size()', best(c0.size))

    print(' [7] emit, verify, rebuild (per candidate)')
    cs = ValueSet(n, rows, S)
    row('gates() (level-ordered emission)', best(cs.gates))
    row('key() = frozenset (dedupe identity)', best(lambda: hash(cs.key())))
    emitted = Circuit(n, *cs.gates())
    row('core.circuit.verify(emitted)', best(lambda: verify(emitted, target)))
    row('core.circuit.normalise(seed circuit)', best(lambda: normalise(circuit, target)))
    row('ValueSet(values()) (rebuild, as checkpoints do)',
        best(lambda: ValueSet(n, rows, cs.values()), repeat=3))

    print(' [8] index statistics')
    triples = sum(len(v) for v in cs.tri.values()) // 6
    degs = sorted(len(v) // 2 for k, v in cs.tri.items() if k not in cs.iset)
    print('    triples=%d  triples/value: mean %.2f median %d max %d'
          % (triples, sum(degs) / len(degs), degs[len(degs) // 2], degs[-1]))


def _addrem(cc, extras):
    j = cc.journal()
    for m in extras:
        cc.add(m)
    cc.rollback(j)


if __name__ == '__main__':
    for case in (sys.argv[1:] or list(CASES)):
        bench(case)
