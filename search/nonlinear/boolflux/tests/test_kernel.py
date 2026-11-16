"""Gate kernel (kernel/bfx.c): config reader, exact traces, edge cases, default-off options, and golden
trajectories that pin the default search.

    python3 -m unittest search/nonlinear/boolflux/tests/test_kernel.py     (from the repository root)

The tests drive the kernel binary directly with hand-written configs, so they do not depend on
cli.py / workflow.py.
"""
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))

from boolflux import core, starts, targets   # noqa: E402


def build():
    d = Path(tempfile.mkdtemp(prefix='bft-bfx-'))
    subprocess.run(['gcc', '-O2', '-o', str(d / 'bfx'), str(PKG / 'kernel' / 'bfx.c'), '-lm'], check=True)
    return d / 'bfx'


BIN = build()
NIST = PKG.parent / 'seeds' / 'aes-sbox'
BASE = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
        'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
        'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
NIST_LIB = {'cost.8': 1, 'cost.6': 1, 'cost.9': 1, 'cost.3': 1}
BGC_LIB = {'cost.8': 1, 'cost.14': 1, 'cost.6': 1, 'cost.3': 1}
LEX_A = {'lex': 'a,ad,cost,gd', 'w.a': 1, 'w.ad': 1e-4, 'w.cost': 1e-8, 'w.gd': 1e-12}
LEX_COST = {'lex': 'cost,gd', 'w.cost': 1, 'w.gd': 1e-4}


def present_start():
    n, m, tab, _ = targets.load('present')
    return core.to_kernel(starts.anf(n, m, tab, [8, 14, 6, 3]))


def aes(name):
    return core.to_kernel(core.read_ncff(str(NIST / name)))


def run(circuit_text, settings, raw_cfg=None, d=None):
    """Run the kernel; returns (returncode, stdout, stderr, workdir)."""
    d = Path(d or tempfile.mkdtemp(prefix='bft-k-'))
    (d / 'in.bfx').write_text(circuit_text)
    if raw_cfg is None:
        cfg = {'in': d / 'in.bfx', 'out': d / 'out.bfx', 'seed': 1, 'seconds': 600}
        cfg.update(settings)
        raw_cfg = ''.join('%s %s\n' % kv for kv in cfg.items())
    (d / 'k.cfg').write_text(raw_cfg)
    r = subprocess.run([str(BIN), str(d / 'k.cfg')], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr, d


def final(log):
    ln = [x for x in log.splitlines() if x.startswith('final ')][-1].split()
    return {ln[i]: float(ln[i + 1]) for i in range(1, len(ln) - 1, 2)}


def trajectory(log, d):
    """Everything the kernel reports except wall-clock fields, plus the result circuit."""
    t = re.sub(r' (t|seconds|time) [0-9.]+', '', log)
    out = '\n'.join(x for x in (d / 'out.bfx').read_text().splitlines() if not x.startswith('#'))
    return hashlib.md5((t + out).encode()).hexdigest()[:12]


def check_same_function(test, a_text, b_text):
    a, b = core.from_kernel(a_text), core.from_kernel(b_text)
    test.assertEqual(a.value_table(), b.value_table())


class TestConfigParsing(unittest.TestCase):
    """Config reader."""

    def test_one_word_comment_does_not_eat_next_line(self):
        d = Path(tempfile.mkdtemp(prefix='bft-k-'))
        cfg = ('#note\niters 0\n# two words\n\nin %s\nout %s\nseed 1\nseconds 0.3\ncost.8 1\ncost.14 1\ncost.6 1\ncost.3 1\n'
               % (d / 'in.bfx', d / 'out.bfx'))
        rc, out, err, _ = run(present_start(), None, cfg, d)
        self.assertEqual(rc, 0, err)
        self.assertEqual(final(out)['iters'], 0)       # the old reader dropped `iters 0` and searched for 0.3 s

    def test_bad_op_number_rejected(self):
        for key in ('cost.99', 'cost.-1', 'cost.8x', 'gdw.16'):
            s = dict(BASE); s.update(BGC_LIB); s.update({key: 1, 'iters': 10})
            rc, out, err, _ = run(present_start(), s)
            self.assertEqual(rc, 2, key)
            self.assertIn('bad op number', err)

    def test_unknown_move_and_missing_value_rejected(self):
        s = dict(BASE); s.update(BGC_LIB); s.update({'mv.resub9': 1, 'iters': 10})
        rc, out, err, _ = run(present_start(), s)
        self.assertEqual(rc, 2); self.assertIn('unknown move', err)
        rc, out, err, _ = run(present_start(), None, 'iters\n')
        self.assertEqual(rc, 2); self.assertIn('no value', err)

    def test_path_with_space(self):
        d = Path(tempfile.mkdtemp(prefix='bft-k sp-'))
        s = dict(BASE); s.update(BGC_LIB); s.update(LEX_COST)
        s.update({'in': d / 'in.bfx', 'out': d / 'out file.bfx', 'seed': 1, 'seconds': 600, 'iters': 200})
        rc, out, err, _ = run(present_start(), None, ''.join('%s %s\n' % kv for kv in s.items()), d)
        self.assertEqual(rc, 0, err)
        check_same_function(self, present_start(), (d / 'out file.bfx').read_text())

    def test_stats_without_file(self):
        r = subprocess.run([str(BIN), '--stats'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)             # was a NULL strcpy (segfault)

    def test_cand_cap_bounds(self):
        s = dict(BASE); s.update(BGC_LIB); s.update(LEX_COST); s.update({'cand_cap': 0, 'iters': 10})
        self.assertEqual(run(present_start(), s)[0], 2)
        # more than 1024 kept candidates are all evaluated (not silently only the first 1024)
        s.update({'cand_cap': 5000, 'iters': 300})
        rc, out, err, d = run(present_start(), s)
        self.assertEqual(rc, 0, err)
        check_same_function(self, present_start(), (d / 'out.bfx').read_text())


class TestTraceAndEdges(unittest.TestCase):
    def test_trace_costs_exact(self):
        """Trace / tracemoves costs are printed exactly (were %.4f / %.2f)."""
        d = Path(tempfile.mkdtemp(prefix='bft-k-'))
        s = dict(BASE); s.update(LEX_COST)
        s.update({'cost.8': 1.5, 'cost.6': 0.123456789, 'cost.3': 0.123456789, 'iters': 1500,
                  'trace': d / 'tr.txt', 'tracemoves': d / 'mv.txt'})
        n, m, tab, _ = targets.load('present')
        rc, out, err, _ = run(core.to_kernel(starts.anf(n, m, tab, [8, 6, 3])), s, d=d)
        self.assertEqual(rc, 0, err)
        rows = [x.split() for x in (d / 'tr.txt').read_text().splitlines()]
        self.assertTrue(rows)
        for r in rows:
            cost, g, a = float(r[3]), int(r[4]), int(r[5])
            self.assertAlmostEqual(cost, 1.5 * a + 0.123456789 * (g - a), delta=1e-7)
        for ln in (d / 'mv.txt').read_text().splitlines():
            mm = re.search(r'after cost (\S+) G (\d+) A (\d+)', ln)
            self.assertAlmostEqual(float(mm.group(1)), 1.5 * int(mm.group(3)) + 0.123456789 * (int(mm.group(2)) - int(mm.group(3))), delta=1e-7)

    def test_degenerate_circuits(self):
        """Empty circuit, outputs that are inputs / repeated, a single NOT: the kernel must end cleanly."""
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s['iters'] = 200
        for text, g in (('n 3\nm 2\ng 0\no 0 2\n', 0),
                        ('n 2\nm 3\ng 1\n3 0 0\no 2 2 1\n', 1),
                        ('n 2\nm 2\ng 3\n6 0 1\n6 2 1\n8 0 1\no 3 4\n', 1)):      # (x^y)^y = x
            rc, out, err, d = run(text, s)
            self.assertEqual(rc, 0, err)
            self.assertEqual(final(out)['G'], g)
            check_same_function(self, text, (d / 'out.bfx').read_text())
        rc, out, err, d = run('n 2\nm 1\ng -1\no 0\n', s)
        self.assertEqual(rc, 2)


def parity_from_ands(k):
    """x0 ^ ... ^ x(k-1) built from AND and NOT only (a ^ b = ~(~(a & ~b) & ~(~a & b))): 3 ANDs per XOR."""
    gates = []; n = k

    def add(op, a, b):
        gates.append((op, a, b)); return n + len(gates) - 1
    acc = 0
    for i in range(1, k):
        na, nb = add(3, acc, acc), add(3, i, i)
        p, q = add(8, acc, nb), add(8, na, i)
        r = add(8, add(3, p, p), add(3, q, q))
        acc = add(3, r, r)
    return 'n %d\nm 1\ng %d\n%s\no %d\n' % (k, len(gates), '\n'.join('%d %d %d' % g for g in gates), acc)


class TestOptions(unittest.TestCase):
    """fraig 2, xspan, repair_keep: options that are off by default (TestTrajectory checks that the default is untouched)."""

    def test_fraig2_reverse_merge(self):
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A)
        s.update({'cap.a': 29, 'cap.ad': 5, 'cap.gd': 20, 'iters': 300, 'fraig': 2})
        text = aes('aes-sbox-a29-ad5-g182-gd16-xx153-29.circ.txt')
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        self.assertGreater(int(out.split('fraig_reverse_merges')[1].split()[0]), 0)
        f = final(out)
        self.assertEqual(f['feas'], 1); self.assertLessEqual(f['G'], 182)
        check_same_function(self, text, (d / 'out.bfx').read_text())

    def test_xspan_removes_all_ands_of_a_parity(self):
        text = parity_from_ands(7)                       # 18 ANDs; the output is the XOR of the 7 inputs
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A)
        s.update({'mv.resub1': 0, 'mv.resub2': 0, 'mv.resub3': 0, 'mv.xspan': 1, 'iters': 400, 'T0': 0})
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        f = final(out)
        self.assertEqual(f['A'], 0); self.assertLessEqual(f['G'], 21)
        self.assertIn('move xspan', out)
        self.assertGreater(int(out.split('xspan_solutions')[1].split()[0]), 0)
        check_same_function(self, text, (d / 'out.bfx').read_text())

    def test_sweep_tests_every_gate_once(self):
        # sweep 1: gates in index order; one pass over an unchanged circuit is an exact scan
        text = aes('aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt')
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A)
        s.update({'mv.resub1': 0, 'mv.resub2': 0, 'mv.resub3': 0, 'mv.xspan': 1, 'iters': 153, 'T0': 0, 'sweep': 1})
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        self.assertIn('move xspan prop 153 acc 0', out)       # no AND of this NIST 28 is in the span of the rest
        self.assertEqual(final(out)['A'], 28)

    def test_xspan_complemented_and_caps(self):
        # complement of a parity (needs the constant), under a gate-depth cap the balanced tree can meet
        base = parity_from_ands(8).splitlines()
        g = int(base[2].split()[1]); out_sig = int(base[-1].split()[1])
        text = '\n'.join(base[:2] + ['g %d' % (g + 1)] + base[3:-1] + ['3 %d %d' % (out_sig, out_sig), 'o %d' % (8 + g)]) + '\n'
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A)
        s.update({'mv.xspan': 3, 'iters': 1500, 'cap.gd': 3})
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        f = final(out)
        self.assertEqual((f['A'], f['feas']), (0, 1)); self.assertLessEqual(f['GD'], 3)
        check_same_function(self, text, (d / 'out.bfx').read_text())

    def test_nl_root_modes(self):
        # nl_root: sampled two-gate candidates with AND-like roots only (1) or all divisors (2)
        text = aes('aes-sbox-a29-ad5-g182-gd16-xx153-29.circ.txt')
        for mode in (1, 2):
            s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A)
            s.update({'cap.a': 29, 'cap.ad': 5, 'cap.gd': 20, 'iters': 300, 'nl_root': mode})
            rc, out, err, d = run(text, s)
            self.assertEqual(rc, 0, err)
            f = final(out)
            self.assertEqual(f['feas'], 1); self.assertLess(f['G'], 182)
            check_same_function(self, text, (d / 'out.bfx').read_text())
        # an XOR-only library has no AND-like root: the sampled block is skipped, the run still works
        s = dict(BASE); s.update({'cost.6': 1, 'cost.9': 1, 'cost.3': 1, 'lex': 'cost,gd', 'w.cost': 1, 'linear': 1, 'iters': 300, 'nl_root': 2})
        lin = '\n'.join(['n 4', 'm 2', 'g 5', '6 0 1', '6 4 2', '6 5 3', '6 2 3', '6 7 0', 'o 6 8']) + '\n'
        rc, out, err, d = run(lin, s)
        self.assertEqual(rc, 0, err)
        check_same_function(self, lin, (d / 'out.bfx').read_text())

    def test_repair_keep_never_raises_a_cap_excess(self):
        text = aes('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt')
        worst = {}
        for keep in (0, 1):
            d = Path(tempfile.mkdtemp(prefix='bft-k-'))
            s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A)
            s.update({'cap.a': 32, 'cap.ad': 5, 'cap.gd': 24, 'iters': 400, 'repair_keep': keep, 'trace': d / 'tr.txt'})
            rc, out, err, _ = run(text, s, d=d)
            self.assertEqual(rc, 0, err)
            rows = [x.split() for x in (d / 'tr.txt').read_text().splitlines()]
            worst[keep] = (max(int(r[5]) for r in rows), max(int(r[7]) for r in rows))     # A, AD
            gd = [int(r[6]) for r in rows]
            if keep: self.assertEqual(gd, sorted(gd, reverse=True))                        # GD excess never rises
            check_same_function(self, text, (d / 'out.bfx').read_text())
        self.assertEqual(worst[1], (32, 5))            # A and AD stay inside their caps during the repair
        self.assertGreater(worst[0][0], 32)            # default: the repair buys depth with an AND above cap.a


def stats_lines(log):
    """final metrics + per-move counters + no-op count, without wall-clock fields."""
    keep = [re.sub(r' (t|seconds|time) [0-9.]+', '', x) for x in log.splitlines()
            if x.startswith(('final ', 'move ', 'noop_'))]
    return ' | '.join(keep)


def golden_cases():
    a = dict(BASE); a.update(NIST_LIB); a.update(LEX_A); a.update({'cap.a': 29, 'cap.ad': 5, 'iters': 400})
    b = dict(BASE); b.update(NIST_LIB); b.update(LEX_COST); b.update({'iters': 400, 'seed': 2})
    c = dict(BASE); c.update(NIST_LIB); c.update(LEX_A); c.update({'cap.a': 32, 'cap.ad': 5, 'cap.gd': 24, 'iters': 400})
    e = dict(BASE); e.update(BGC_LIB); e.update(LEX_COST); e.update({'iters': 6000, 'seed': 3})
    return {'aes_a29_lexA': (aes('aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt'), a),
            'aes_a32_cost': (aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt'), b),
            'aes_repair_gd24': (aes('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'), c),
            'present_bgc': (present_start(), e)}


# Recorded with the kernel of commit 695a90b; the kernel of commit f9fe6f7 (before the performance
# changes of 2026-11-14) gives the same lines.  Regenerate (stats_lines() of each golden case) ONLY for
# a change that is meant to alter the default search.
GOLDEN = {
    'aes_a29_lexA': 'final cost 137 G 137 A 29 GD 32 AD 5 obj 29.000501370031998 feas 1 iters 400 restarts 0 | move resub1 prop 79 acc 11 imp 0 cands 80 | move resub2 prop 213 acc 87 imp 0 cands 4469 | move resub3 prop 108 acc 41 imp 0 cands 2875 | noop_candidates_skipped 801',
    'aes_a32_cost': 'final cost 103 G 103 A 32 GD 32 AD 7 obj 103.00320000000001 feas 1 iters 400 restarts 0 | move resub1 prop 92 acc 9 imp 0 cands 92 | move resub2 prop 202 acc 58 imp 0 cands 3449 | move resub3 prop 106 acc 28 imp 0 cands 2827 | noop_candidates_skipped 1013',
    'aes_repair_gd24': 'final cost 117 G 117 A 33 GD 24 AD 5 obj 1000033.0005011701 feas 0 iters 400 restarts 0 | move resub1 prop 103 acc 19 imp 2 cands 109 | move resub2 prop 193 acc 58 imp 15 cands 1580 | move resub3 prop 104 acc 38 imp 11 cands 1406 | noop_candidates_skipped 783',
    'present_bgc': 'final cost 14 G 14 A 4 GD 7 AD 2 obj 14.0007 feas 1 iters 6000 restarts 0 | move resub1 prop 1557 acc 219 imp 2 cands 1918 | move resub2 prop 3006 acc 1164 imp 10 cands 37625 | move resub3 prop 1437 acc 485 imp 10 cands 30488 | noop_candidates_skipped 28007',
}


class TestTrajectory(unittest.TestCase):
    """The performance changes (linear-digest pair table, cached structure hashes, lazy
    levels in fraig) and every later default-off option must leave the default search bit-identical
    for a fixed seed and iteration count."""

    def test_default_trajectories_unchanged(self):
        for name, (text, settings) in golden_cases().items():
            rc, out, err, d = run(text, settings)
            self.assertEqual(rc, 0, err)
            self.assertEqual(stats_lines(out), GOLDEN[name], name)
            check_same_function(self, text, (d / 'out.bfx').read_text())


if __name__ == '__main__':
    unittest.main()
