"""--policy learned (idea 07, 2026-11-17):
    python3 -m unittest boolflux.hub.tests.test_hub_learned   (from search/nonlinear/)

The feature state (learned.State: front, front-add flags, attempts), the model score, the learned choice (join
kept first, scored launches, attempt limits, calibration from finished jobs), and the decision record.
No test starts a kernel.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import learned as L, scheduler as SCH                     # noqa: E402
from boolflux.hub.common import metrics                                      # noqa: E402
from boolflux.hub.tests.test_hub_invariants import sched, OPEN, P104, P107, P117   # noqa: E402

SCH.kernel_bin = lambda d: None


def tearDownModule():
    for f in OPEN:
        try: f.close()
        except Exception: pass


class TestState(unittest.TestCase):
    def test_front_adds_and_attempts(self):
        st = L.State('aes-invsbox', [(28, 4, 130, 20)])
        st.add_record({'id': 'a', 'A': 30, 'AD': 4, 'G': 140, 'GD': 20, 'operator': 'seed', 't_admit': 0.0})
        st.add_launch('polish', 'a', 1.0)
        self.assertIsNone(st.add_record({'id': 'b', 'A': 30, 'AD': 4, 'G': 141, 'GD': 20, 'operator': 'polish', 't_admit': 2.0}))
        self.assertEqual(st.add_record({'id': 'c', 'A': 30, 'AD': 4, 'G': 138, 'GD': 20, 'operator': 'polish', 't_admit': 3.0}), 'G')
        x = dict(zip(L.FEATS, st.features('polish', 'a', 4.0)))
        self.assertEqual(x['att1'], 1.0); self.assertEqual(x['on_front'], 0.0); self.assertEqual(x['o_seed'], 1.0)
        self.assertAlmostEqual(x['refdef'], 1.0)          # 140 - 130 = 10 -> 1.0
        y = dict(zip(L.FEATS, st.features('pull', 'c', 4.0)))
        self.assertEqual(y['on_front'], 1.0); self.assertEqual(y['is_add'], 1.0); self.assertEqual(y['att1'], 0.0)
        self.assertEqual(len(st.features('pull', 'c', 4.0)), len(L.FEATS))

    def test_model_score(self):
        m = L.Model({'polish': {'w': [0.0] * len(L.FEATS), 'adds_per_hit': 2.0, 'cpu_s': 100.0}})
        x = [1.0] * len(L.FEATS)
        self.assertAlmostEqual(m.prob('polish', x), 0.5); self.assertAlmostEqual(m.score('polish', x), 0.01)
        self.assertAlmostEqual(m.score('polish', x, cpu_s=50), 0.02); self.assertEqual(m.score('pull', x), 0.0)


class TestLearnedChoice(unittest.TestCase):
    def test_choice(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull,join,trb', '--policy', 'learned', '--learned-noise', '0')
            s.seed([str(P104), str(P107), str(P117)])
            by = {metrics(s.ar.circuit(i)): i for i in s.ar.rec}
            i117 = by[(32, 4, 117, 19)]
            # join first (priority level 1)
            op, tid, lvl, batch = s.learned_choice(set())
            self.assertEqual((op, lvl), ('join', 'join')); self.assertEqual(s._dec['policy'], 'learned')
            s.args.join_share = -1.0                     # join off: scored launches
            op, tid, lvl, batch = s.learned_choice(set())
            self.assertIn(op, ('polish', 'pull', 'trb')); self.assertTrue(lvl.startswith('learned-'))
            dec = s._dec
            self.assertEqual(dec['mode'], 'learned'); self.assertGreater(dec['n_cands'], 0)
            self.assertEqual(dec['top'][0][:2], [op, tid])
            json.dumps(dec)                               # the decision record is JSON
            # a tuple at --learned-max-att for an operator is not offered to it; trb once per tuple
            s.args.learned_max_att = 1
            for o in ('polish', 'pull', 'trb'):
                s.attempts[(o, (32, 4, 117, 19))] = 1
            s.sattempts.clear(); s.sattempts.update({(o, s.skey(i)): 1 for o in ('polish', 'pull') for i in s.ar.rec})
            s.learned_choice(set())
            self.assertFalse(any(t[1] == i117 for t in s._dec['top']))
            # calibration: a finished job with 0 adds against its prediction lowers its operator's factor
            s._ls_pred['x1'] = ('polish', 0.5); s._ls_done.add('x1')
            cal, obs, pred = s.learned_calib()
            self.assertAlmostEqual(cal['polish'], 2.0 / 2.5)


if __name__ == '__main__':
    unittest.main()
