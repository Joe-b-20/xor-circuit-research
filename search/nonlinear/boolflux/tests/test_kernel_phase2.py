"""Gate kernel and skeleton kernel changes of 2026-11-16 (phase 2, W1): the same-trajectory speedups keep the
default search bit-identical (golden trajectories in test_kernel.py, plus the no-op pre-check counted here),
the budget clock, the default-off options (target weights, per-move slack, repair uphill, stall stop,
XOR-only pair table) and the line-based config reader of skel.c.

    python3 -m unittest search/nonlinear/boolflux/tests/test_kernel_phase2.py     (from the repository root)
"""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from boolflux.tests.test_kernel import (BASE, LEX_A, LEX_COST, NIST_LIB, BGC_LIB, PKG, aes, check_same_function,
                                         final, present_start, run)


class TestSameTrajectory(unittest.TestCase):
    def test_noop_precheck_counts_inside_the_old_noop_count(self):
        # the pre-check only takes over no-ops the full evaluation would have found: the old counter is unchanged
        # (golden lines) and the new one is a part of it
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s.update({'iters': 400, 'seed': 2})
        rc, out, err, d = run(aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt'), s)
        self.assertEqual(rc, 0, err)
        total = int(re.search(r'noop_candidates_skipped (\d+)', out).group(1))
        pre = int(re.search(r'kstat cands .* noop_pre (\d+)', out).group(1))
        self.assertEqual(total, 1013)
        self.assertGreater(pre, 0); self.assertLessEqual(pre, total)
        # skip_noop 0: no-ops are ordinary neutral candidates, the pre-check must not run
        s['skip_noop'] = 0
        rc, out, err, d = run(aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt'), s)
        self.assertEqual(rc, 0, err)
        self.assertEqual(int(re.search(r'noop_pre (\d+)', out).group(1)), 0)

    def test_resub1_direct_equals_scan(self):
        # l1_direct 0 = the old resub1 pair scan; both must give the same run (NIST library and a library with
        # every AND-like op, asymmetric ones included, fractional costs)
        full = {'cost.8': 1, 'cost.14': 1, 'cost.6': 1, 'cost.9': 1.5, 'cost.7': 1.25, 'cost.1': 1.25, 'cost.4': 1,
                'cost.13': 1, 'cost.3': 0.5}
        for lib, text in ((NIST_LIB, aes('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt')), (full, aes('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt')),
                          (BGC_LIB, present_start())):
            res = []
            for fast in (0, 1):
                s = dict(BASE); s.update(lib); s.update(LEX_COST); s.update({'iters': 500, 'seed': 5, 'l1_direct': fast})
                rc, out, err, d = run(text, s)
                self.assertEqual(rc, 0, err)
                keep = [re.sub(r' (t|seconds|time|np_sum|np_max|probe_sum|probe_max) [0-9.]+', '', x) for x in out.splitlines()
                        if not x.startswith(('kstat time', 'kstat clock', 'kstat best', 'kstat stop', 'kstat l1', 'kstat r3_'))]
                res.append((keep, (d / 'out.bfx').read_text().split('#')[0]))
                if fast: self.assertRegex(out, r'kstat l1 direct [1-9]\d* scan 0')
            self.assertEqual(res[0], res[1])

    def test_clock_option(self):
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s.update({'iters': 200})
        text = aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt')
        lines = set()
        for clk in ('real', 'cpu', 'mono'):
            s['clock'] = clk
            rc, out, err, d = run(text, s)
            self.assertEqual(rc, 0, err)
            lines.add(re.sub(r' seconds [0-9.]+', '', [x for x in out.splitlines() if x.startswith('final ')][0]))
        self.assertEqual(len(lines), 1)              # an iteration budget does not depend on the clock
        s['clock'] = 'wall'
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 2); self.assertIn('clock must be', err)
        # a CPU-time budget ends the run
        s.update({'clock': 'cpu', 'seconds': 0.3}); s.pop('iters')
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        self.assertIn('kstat stop time', out)


class TestPhase2Options(unittest.TestCase):
    def check(self, text, s):
        rc, out, err, d = run(text, s)
        self.assertEqual(rc, 0, err)
        check_same_function(self, text, (d / 'out.bfx').read_text())
        return out

    def test_options_run_and_keep_the_function(self):
        text = aes('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt')
        for extra in ({'tgt_w.mffc1': 0.3}, {'tgt_w.and': 0.25, 'tgt_w.viol': 4}, {'tgt_w.mffc1': 0, 'tgt_w.and': 0},
                      {'uphill.resub3': 2}, {'uphill.resub2': 2, 'uphill.resub3': 3}, {'repair_uphill': 2},
                      {'pair_xor': 1}, {'pair_xor': 1, 'mv.xspan': 1, 'nl_root': 1}):
            s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A); s.update({'cap.a': 32, 'cap.ad': 5, 'cap.gd': 24, 'iters': 400})
            s.update(extra)
            out = self.check(text, s)
            self.assertNotIn('pair_xor off', out)
        # PRESENT (bgc library: no XNOR): pair_xor cannot apply and says so
        s = dict(BASE); s.update(BGC_LIB); s.update(LEX_COST); s.update({'iters': 2000, 'pair_xor': 1})
        out = self.check(present_start(), s)
        self.assertIn('pair_xor off', out)

    def test_pair_xor_builds_fewer_entries(self):
        text = aes('aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt')
        nps = {}
        for px in (0, 1):
            s = dict(BASE); s.update(NIST_LIB); s.update(LEX_A); s.update({'cap.a': 29, 'cap.ad': 5, 'iters': 1, 'seed': 3,
                                                                            'mv.resub1': 0, 'mv.resub2': 1, 'mv.resub3': 0, 'pair_xor': px})
            out = self.check(text, s)
            nps[px] = int(re.search(r'kstat movex resub2 .* np_sum (\d+)', out).group(1))
            nps[(px, 'seen')] = [int(x) for x in re.search(r'kstat movex resub2 seen (\S+)', out).group(1).split(',')]
        self.assertLess(nps[1], nps[0])
        # first move from the same start: the same level-0/1 candidates; at level 2 (XOR root) at least as many
        # (the 4-hit limit applies to each of the two lookups)
        self.assertEqual(nps[(0, 'seen')][:2], nps[(1, 'seen')][:2])
        self.assertGreaterEqual(nps[(1, 'seen')][2], nps[(0, 'seen')][2])

    def test_stop_stall_it(self):
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s.update({'iters': 100000, 'stop_stall_it': 300})
        out = self.check(aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt'), s)
        m = re.search(r'kstat stop (\S+) it (\d+) t \S+ last_improve_it (\d+)', out)
        self.assertEqual(m.group(1), 'stall')
        self.assertEqual(int(m.group(2)) - int(m.group(3)), 300)

    def test_target_weight_zero_excludes_and_targets(self):
        # tgt_w.and 0: an AND-like gate is never the target
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s.update({'iters': 300, 'tgt_w.and': 0})
        out = self.check(aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt'), s)
        self.assertEqual(int(re.search(r'kstat tgt s_andlike yes prop (\d+)', out).group(1)), 0)
        self.assertGreater(int(re.search(r'kstat tgt s_andlike no prop (\d+)', out).group(1)), 0)

    def test_bad_target_weight(self):
        s = dict(BASE); s.update(NIST_LIB); s.update(LEX_COST); s.update({'iters': 10, 'tgt_w.and': -1})
        rc, out, err, d = run(aes('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt'), s)
        self.assertEqual(rc, 2); self.assertIn('tgt_w', err)


def build_skel():
    d = Path(tempfile.mkdtemp(prefix='bft-skel-'))
    subprocess.run(['gcc', '-O2', '-o', str(d / 'skel'), str(PKG / 'kernel' / 'skel.c'), '-lm'], check=True)
    return d / 'skel'


class TestSkelConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from boolflux import core, skeleton, targets
        cls.bin = build_skel()
        c = core.read_ncff(str(PKG.parent / 'seeds' / 'aes-sbox' / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'))
        cls.text = skeleton.write_skel(skeleton.extract(c), core.tables_from_values(8, 8, targets.aes_sbox()))

    def run_cfg(self, lines, d=None):
        d = Path(d or tempfile.mkdtemp(prefix='bft-sk-'))
        (d / 'in.sk').write_text(self.text)
        cfg = (d / 'k.cfg'); cfg.write_text(lines.format(d=d))
        return subprocess.run([str(self.bin), str(cfg)], capture_output=True, text=True), d

    def test_line_reader_comments_blank_lines_and_paths(self):
        d = Path(tempfile.mkdtemp(prefix='bft-sk dir-'))           # a path with a space
        r, _ = self.run_cfg('# skeleton config\n\nin {d}/in.sk\nout {d}/out.sk\niters 50\nseed 3\n   \nmv.split 0\nclock cpu\n', d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((d / 'out.sk').exists())
        self.assertIn('final K', r.stdout)

    def test_unknown_keys_rejected(self):
        for bad in ('mv.swapp 1', 'itres 5', 'clock wall', 'seed'):
            r, _ = self.run_cfg('in {d}/in.sk\nout {d}/out.sk\niters 5\n' + bad + '\n')
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn('skel:', r.stderr)


if __name__ == '__main__':
    unittest.main()
