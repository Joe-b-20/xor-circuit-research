"""Instrumentation of the gate kernel (kstat lines, 2026-11-16) and their reader in runlog.py.

    python3 -m unittest boolflux.tests.test_instrumentation      (from search/nonlinear/)

The kstat counters must leave the search unchanged: the golden trajectories of test_kernel hold with every
option on, and the counters agree with the kernel's older lines and with each other.
"""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG.parent))

from boolflux import runlog                       # noqa: E402
from boolflux.tests import test_kernel as TK      # noqa: E402  (builds the kernel once)

KOPTS = {'stats_every_it': 97, 'stats_every_s': 0.05, 'kstat_time': 1}


def kv(line, start):
    t = line.split()
    return {t[i]: t[i + 1] for i in range(start, len(t) - 1, 2)}


def vec(x):
    return [int(v) for v in x.split(',')]


class TestKstat(unittest.TestCase):
    def test_golden_trajectories_with_every_option_on(self):
        """periodic lines, phase timers and all counters on: the default search is bit-identical"""
        for name, (text, settings) in TK.golden_cases().items():
            s = dict(settings); s.update(KOPTS)
            rc, out, err, d = TK.run(text, s)
            self.assertEqual(rc, 0, err)
            self.assertEqual(TK.stats_lines(out), TK.GOLDEN[name], name)
            self.assertIn('kstat periodic', out); self.assertIn('kstat time resub2', out)
            rc0, out0, err0, d0 = TK.run(text, settings)
            strip = lambda o: [re.sub(r' (t|seconds|time) [0-9.]+', '', x) for x in o.splitlines() if not x.startswith('kstat ')]
            self.assertEqual(strip(out), strip(out0), name)                  # every older line, best lines included
            self.assertEqual((d / 'out.bfx').read_text().split('#')[0], (d0 / 'out.bfx').read_text().split('#')[0])

    def test_counters_agree(self):
        """kstat counters against the old move lines and against each other (repair case: every branch occurs)"""
        text, s = TK.golden_cases()['aes_repair_gd24']
        s = dict(s); s.update({'iters': 600, 'stall_it': 150})
        rc, out, err, d = TK.run(text, s)
        self.assertEqual(rc, 0, err)
        L = out.splitlines()
        move = {x.split()[1]: {k: int(float(v)) for k, v in kv(x, 2).items()} for x in L if x.startswith('move ')}
        mx = {x.split()[2]: kv(x, 3) for x in L if x.startswith('kstat movex ')}
        stop = kv(next(x for x in L if x.startswith('kstat stop')), 3)
        acc = {k: int(v) for k, v in kv(next(x for x in L if x.startswith('kstat accept')), 2).items()}
        cands = {k: int(v) for k, v in kv(next(x for x in L if x.startswith('kstat cands')), 2).items()}
        self.assertEqual(next(x for x in L if x.startswith('kstat stop')).split()[2], 'iters')
        self.assertEqual(int(stop['it']), 600)
        self.assertEqual(int(stop['repair_it']), 600)                         # the best never meets GD 24 here
        self.assertEqual(int(stop['first_feasible_it']), -1)
        self.assertGreater(int(stop['restarts']), 0)
        tot_acc = sum(m['acc'] for m in move.values())
        self.assertEqual(acc['improve'] + acc['neutral'] + acc['uphill'], tot_acc)
        self.assertEqual(cands['noop'], int(next(x for x in L if x.startswith('noop_')).split()[1]))
        ev_total = 0
        for mv, m in move.items():
            x = mx[mv]; n = {k: int(v) for k, v in x.items() if ',' not in v}
            self.assertEqual(n['acc_imp'] + n['acc_neu'] + n['acc_up'], m['acc'], mv)
            self.assertEqual(sum(vec(x['kept'])), m['cands'], mv)            # the reservoir is what the move evaluates
            self.assertGreaterEqual(sum(vec(x['seen'])), m['cands'])
            self.assertEqual(n['eval'], m['cands'], mv)                       # every kept candidate is evaluated
            self.assertEqual(n['rbfail'] + n['noop'] + n['rkeep'] + n['infeas'] + n['better'] + n['equal'] + n['up_ok'] + n['up_far'],
                             n['eval'], mv)
            self.assertEqual(sum(vec(x['accform'])), m['acc']); self.assertEqual(sum(vec(x['bestform'])), m['imp'])
            self.assertEqual(sum(vec(x['impform'])), n['acc_imp'])
            self.assertEqual(n['fraig0'] + n['fraig1'] + n['fraig2p'], n['eval'] - n['rbfail'])
            self.assertLessEqual(n['acc_up'], n['up_tried'])
            ev_total += n['eval'] - n['rbfail']
        self.assertEqual(ev_total, cands['evaluated'])
        props = sum(m['prop'] for m in move.values()) - cands['no_divisor_moves']
        tgt = {}
        for x in L:
            if x.startswith('kstat tgt '):
                t = x.split(); tgt.setdefault(t[2], []).append({k: int(v) for k, v in kv(x, 4).items()})
        for st, rows in tgt.items():
            want = props if st != 'on_violating_path' else props          # repair throughout: every proposal is counted
            self.assertEqual(sum(r['prop'] for r in rows), want, st)
            self.assertEqual(sum(r['acc'] for r in rows), tot_acc, st)
            self.assertEqual(sum(r['best'] for r in rows), sum(m['imp'] for m in move.values()), st)
        walk = kv(next(x for x in L if x.startswith('kstat walk')), 2)
        self.assertEqual(int(walk['acc']), tot_acc)
        self.assertLessEqual(int(walk['distinct_struct']), tot_acc + 1)
        self.assertEqual(len(walk['restarts_at'].split(',')), int(stop['restarts']))
        dc = {x.split()[2]: sum(int(v) for v in kv(x, 3).values()) for x in L if x.startswith('kstat dcost ')}
        self.assertEqual(dc['evaluated'], cands['evaluated']); self.assertEqual(dc['accepted'], tot_acc)
        self.assertEqual(dc['improving'], acc['improve'])
        per = [x for x in L if x.startswith('kstat periodic')]
        self.assertEqual(per, [])                                            # off unless asked

    def test_keep_bests_and_clocks(self):
        """keep_bests DIR: one file per best line, the last equal to the final best; clocks and best times"""
        import tempfile
        text, s = TK.golden_cases()['aes_repair_gd24']
        kd = Path(tempfile.mkdtemp(prefix='bft-kb-'))
        s = dict(s); s.update({'keep_bests': kd})
        rc, out, err, d = TK.run(text, s)
        self.assertEqual(rc, 0, err)
        nb = sum(1 for x in out.splitlines() if x.startswith('best '))
        files = sorted(kd.glob('best-*.bfx'), key=lambda p: int(p.stem.split('-')[1]))
        self.assertEqual(len(files), nb); self.assertGreater(nb, 0)
        body = lambda p: p.read_text().split('#')[0]
        self.assertEqual(body(files[-1]), body(d / 'out.bfx'))
        st = runlog.kernel_stats(out)
        self.assertEqual(st['keep_bests']['files'], nb)
        self.assertEqual(len(st['bests']), nb); self.assertEqual(len(st['bests'][0]), 9)      # + treal, cpu
        self.assertGreater(st['clock']['real_s'], 0); self.assertGreater(st['clock']['cpu_s'], 0)

    def test_stop_reason_time_and_parser(self):
        text, s = TK.golden_cases()['present_bgc']
        s = dict(s); s.pop('iters'); s.update({'seconds': 0.3, 'stats_every_s': 0.1})
        rc, out, err, d = TK.run(text, s)
        self.assertEqual(rc, 0, err)
        st = runlog.kernel_stats(out, periodic=True)
        self.assertEqual(st['stop']['reason'], 'time')
        self.assertGreaterEqual(st['periodic_rows'], 1); self.assertEqual(len(st['periodic']), st['periodic_rows'])
        self.assertEqual(set(st['moves']), {'resub1', 'resub2', 'resub3'})
        self.assertIn('prop', st['moves']['resub2']); self.assertIn('nocand', st['moves']['resub2'])
        self.assertEqual(len(st['movex']['resub3']['seen']), 6)
        self.assertIn('on_violating_path', st['tgt']); self.assertIn('evaluated', st['dcost'])
        self.assertIsInstance(st['walk']['restarts_at'], list)
        sm = runlog.kernel_summary(out)
        self.assertEqual(sm['stop'], 'time'); self.assertEqual(sm['final']['G'], int(st['final']['G']))
        self.assertIn('accept', sm); self.assertIn('walk', sm)
        # a log of a kernel built before the kstat lines: the old fields only
        old = '\n'.join(x for x in out.splitlines() if not x.startswith('kstat '))
        so = runlog.kernel_summary(old)
        self.assertNotIn('stop', so); self.assertEqual(so['iters'], st['final']['iters'])
        self.assertIsNone(runlog.kernel_summary(''))


if __name__ == '__main__':
    unittest.main()
