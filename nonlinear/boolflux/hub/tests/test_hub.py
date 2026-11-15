"""Hub regression tests:  python3 -m unittest boolflux.hub.tests.test_hub   (from nonlinear/)"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core                                  # noqa: E402
from boolflux.hub.archive import Archive                   # noqa: E402
from boolflux.hub.common import NIST, load, metrics        # noqa: E402
from boolflux.hub import join as J                         # noqa: E402

P104 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'
P107 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt'
P117 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'


def bloated(c):
    """same function and depths, two extra (unused) gates: a worse member of the same (A, AD, GD) cell"""
    g = list(c.gates) + [(6, 0, 1), (6, 1, 2)]
    return core.Circuit(c.n, c.m, g, list(c.outputs))


class TestArchive(unittest.TestCase):
    def test_rejects_wrong_circuit(self):
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d)
            c = load(P104)
            g = list(c.gates)
            op, a, b = g[-1]
            g[-1] = (9 if op == 6 else 6, a, b)            # flip one XOR/XNOR: wrong function
            bad = core.Circuit(c.n, c.m, g, list(c.outputs))
            st, r, gain = ar.admit(bad, force_keep=True)
            self.assertTrue(st.startswith('rejected'), st)
            self.assertEqual(len(ar.rec), 0)
            self.assertEqual(list(Path(d, 'archive').glob('*.bfx')), [])

    def test_cell_keeps_min_g(self):
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d)
            c = load(P104); worse = bloated(c)
            self.assertEqual(metrics(worse)[0:2], metrics(c)[0:2])
            st, r, g = ar.admit(worse, force_keep=True, clean_first=False)   # review 5: admission cleans dead gates away
            self.assertEqual(st, 'admitted')                                 # by default; an old record can hold them
            st2, r2, g2 = ar.admit(c)
            self.assertEqual(st2, 'admitted')
            k = Archive.key(metrics(c))
            self.assertEqual(Archive.key(metrics(worse)), k)
            self.assertEqual(metrics(worse)[2], metrics(c)[2] + 2)
            self.assertEqual(ar.cells[k], [r2['id']])           # the 104 replaced the bloated one
            self.assertIn(r['id'], ar.rec)                       # the superseded circuit stays archived
            st3, r3, g3 = ar.admit(bloated(c))                    # worse again: refused (not force_keep); cleaned it is c
            self.assertIn(st3, ('not-better', 'duplicate', 'duplicate-structure'))
            ar2 = Archive(d)                                      # persisted cells
            self.assertEqual(ar2.cells, ar.cells)

    def test_join_reproduces_a31(self):
        X = J.Prepared(load(P107)); Y = J.Prepared(load(P117))
        c, nint = J.join(X.front(4), Y, 3)
        self.assertIsNotNone(c)
        self.assertEqual(c.value_table(), list(__import__('boolflux').targets.aes_sbox()))
        self.assertEqual(metrics(c), (31, 5, 119, 20))


class TestScheduler(unittest.TestCase):
    def test_run_record_fields(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            lst = Path(d) / 'seed.list'; lst.write_text('%s\n%s\n%s\n' % (P104, P107, P117))
            hub = Path(__file__).resolve().parents[1] / 'scheduler.py'
            import os
            cpu = str(min(os.sched_getaffinity(0)))            # a CPU this process may use (the scheduler refuses others)
            r = subprocess.run([sys.executable, str(hub), '--dir', d, '--cpus', cpu, '--hours', '0.004',
                                '--seed-list', str(lst), '--ops', 'join,trb', '--seconds', 'join=5,trb=3'],
                               capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            runs = list(Path(d, 'runs').glob('*.json'))
            self.assertTrue(runs)
            rec = json.loads(runs[0].read_text())
            for k in ('run_id', 'operator', 'target', 'target_metrics', 'seed', 'code_version', 'settings',
                      'parents', 'wall_s', 'cpu_s', 'outcome', 'gain'):
                self.assertIn(k, rec)
            ar = Archive(d)
            self.assertGreaterEqual(len(ar.rec), 3)
            for i, rr in ar.rec.items():
                for k in ('id', 'A', 'AD', 'G', 'GD', 'counts', 'parents', 'operator', 'operator_settings', 'seed',
                          'run_id', 'code_version', 'cpu_s', 'wall_s', 't_admit', 'verified'):
                    self.assertIn(k, rr)


if __name__ == '__main__':
    unittest.main()
