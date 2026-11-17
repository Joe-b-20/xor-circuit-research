"""Per-operator kernel options (2026-11-17, idea 10): ops --kopt, scheduler --kopt / --kopt-first.
    python3 -m unittest boolflux.hub.tests.test_hub_kopt   (from search/nonlinear/)

No test starts a kernel.
"""
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import ops as HO, scheduler as SCH                   # noqa: E402
from boolflux.hub.common import load                                   # noqa: E402
from boolflux.hub.tests.test_hub_invariants import sched, OPEN, P104, P107, P117   # noqa: E402

SCH.kernel_bin = lambda d: None


def tearDownModule():
    for f in OPEN:
        try: f.close()
        except Exception: pass


class FakePopen:
    def __init__(self, cmd, **kw): self.pid = 0; self.returncode = None; self.cmd = cmd


class TestKopt(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(HO.parse_kopt(''), {})
        self.assertEqual(HO.parse_kopt('pair_xor=1, tgt_w.and=0.3,stop_stall_it=40000'),
                         {'pair_xor': 1, 'tgt_w.and': 0.3, 'stop_stall_it': 40000})
        for bad in ('pair_xor', 'nosuch=1', 'pair_xor=x', 'stop_stall_it=1.5', 'tgt_w.and=-1', 'seed=3', 'cap.a=3'):
            self.assertRaises(ValueError, HO.parse_kopt, bad)
        self.assertEqual(SCH.parse_kopt_arg(['polish,pull:pair_xor=1', 'polish:tgt_w.mffc1=0.5,pair_xor=0']),
                         {'polish': {'pair_xor': 0, 'tgt_w.mffc1': 0.5}, 'pull': {'pair_xor': 1}})
        for bad in (['pair_xor=1'], ['join:pair_xor=1'], ['polish:nosuch=1']):
            self.assertRaises(SystemExit, SCH.parse_kopt_arg, bad)

    def test_kernel_cfg(self):
        """--kopt reaches kernel.cfg; caps, seed, objective weights cannot be overridden through it"""
        seen = {}

        def fake_run(cmd, **kw):
            seen['cfg'] = dict(l.split(None, 1) for l in Path(cmd[1]).read_text().splitlines())
            return types.SimpleNamespace(returncode=0)
        real, HO.subprocess.run = HO.subprocess.run, fake_run
        kb, HO.kernel_bin = HO.kernel_bin, lambda a: Path('bfx-test')
        try:
            with tempfile.TemporaryDirectory() as d:
                jd = Path(d) / 'j'; jd.mkdir()
                HO._kernel(load(P104), {'A': 32, 'AD': None, 'GD': 20}, 'a,ad,cost,gd', 7, 5, jd, d,
                           HO.parse_kopt('pair_xor=1,stop_stall_it=30000,T0=0'))
                self.assertEqual((seen['cfg']['pair_xor'], seen['cfg']['stop_stall_it'], seen['cfg']['seed']), ('1', '30000', '7'))
                self.assertEqual(seen['cfg']['T0'], '0.0')          # over KDEFAULTS T0 0.6
                jd2 = Path(d) / 'j2'; jd2.mkdir()
                HO._kernel(load(P104), {}, 'a,ad,cost,gd', 7, 5, jd2, d)
                self.assertNotIn('pair_xor', seen['cfg']); self.assertNotIn('tgt_w.and', seen['cfg'])
        finally:
            HO.subprocess.run = real; HO.kernel_bin = kb

    def test_scheduler_passes_options_per_level(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull', '--kopt', 'polish,pull:pair_xor=1',
                      '--kopt-first', 'polish:tgt_w.mffc1=0.5,tgt_w.and=0.3')
            s.seed([str(P104), str(P107), str(P117)])
            self.assertEqual(s.job_kopt('polish', 'fresh'), {'pair_xor': 1, 'tgt_w.mffc1': 0.5, 'tgt_w.and': 0.3})
            self.assertEqual(s.job_kopt('polish', 'repeat'), {'pair_xor': 1})
            self.assertEqual(s.job_kopt('pull', 'fresh'), {'pair_xor': 1})
            self.assertEqual(s.job_kopt('join', 'join'), {})
            real = SCH.subprocess.Popen; SCH.subprocess.Popen = FakePopen
            try:
                s.end = time.time() + 100
                j = s.launch(3, set())
                self.assertEqual((j['op'], j['why']), ('polish', 'fresh'))
                cmd = j['cmd']; self.assertEqual(cmd[cmd.index('--kopt') + 1], 'pair_xor=1,tgt_w.and=0.3,tgt_w.mffc1=0.5')
                j['lf'].close()
            finally:
                SCH.subprocess.Popen = real
            s._lockf.close()
        with tempfile.TemporaryDirectory() as d:           # default: no --kopt on the command line (08012e1 behaviour)
            s = sched(d, '--ops', 'polish,pull'); s.seed([str(P104)])
            real = SCH.subprocess.Popen; SCH.subprocess.Popen = FakePopen
            try:
                s.end = time.time() + 100
                j = s.launch(3, set()); self.assertNotIn('--kopt', j['cmd']); j['lf'].close()
            finally:
                SCH.subprocess.Popen = real
            s._lockf.close()


if __name__ == '__main__':
    unittest.main()
