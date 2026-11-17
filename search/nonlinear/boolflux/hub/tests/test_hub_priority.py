"""Hub scheduling and operator changes of 2026-11-16:
    python3 -m unittest boolflux.hub.tests.test_hub_priority   (from search/nonlinear/)

--policy priority (levels join, fresh, variant, near, other, repeat), batched join jobs and their marks, the join
cap at a partner boundary, placeable() (cleaned, archived copies skipped), intermediate kernel bests, pull and
trb defaults, ingest period, cap renewals across a restart, the SIGCHLD wake-up, archive load / structure check
before the verifiers, the inverse interface spaces, nursery slack for one generation.
No test starts a kernel.
"""
import json
import random
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import aesfn, core                                       # noqa: E402
from boolflux.hub import archive as AR, common as C, ops as HO, scheduler as SCH   # noqa: E402
from boolflux.hub.archive import Archive                               # noqa: E402
from boolflux.hub.common import load, metrics, cid                     # noqa: E402
from boolflux.hub.tests.test_hub_invariants import sched, fake_job, OPEN, P104, P107, P117, rewritten   # noqa: E402

SCH.kernel_bin = lambda d: None


def tearDownModule():
    for f in OPEN:
        try: f.close()
        except Exception: pass


def bloat(c, k):
    """2k NOT gates chained on the deepest output: G + 2k, GD + 2k, same function, survives clean()"""
    la = [0] * c.n
    for op, a, b in c.gates: la.append(max(la[a], la[b]) + 1)
    j = max(range(len(c.outputs)), key=lambda q: la[c.outputs[q]])
    g = list(c.gates); outs = list(c.outputs); x = outs[j]
    for _ in range(2 * k):
        g.append((3, x, x)); x = c.n + len(g) - 1
    outs[j] = x
    return core.Circuit(c.n, c.m, g, outs)


class FakePopen:
    def __init__(self, cmd, **kw): self.pid = 0; self.returncode = None; self.cmd = cmd


class TestPriority(unittest.TestCase):
    def test_levels_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull,join,trb', '--variants-first'); s.seed([str(P104), str(P107), str(P117)])
            by = {metrics(s.ar.circuit(i)): i for i in s.ar.rec}
            i104, i107, i117 = by[(32, 5, 104, 30)], by[(32, 5, 107, 22)], by[(32, 4, 117, 19)]
            t104, t107, t117 = (32, 5, 104, 30), (32, 5, 107, 22), (32, 4, 117, 19)
            # 1 join: every target unjoined, batched, AD 4 first
            op, tid, lvl, batch = s.priority_choice(set())
            self.assertEqual((op, tid, lvl), ('join', i117, 'join')); self.assertEqual(set(batch), {i104, i107})
            self.assertEqual(s._dec['levels']['join'], 3)
            # one join job at a time (--join-cpus 1): the next CPU gets the first polish of the lowest (A, AD) tuple
            s.running = [{'op': 'join', 'target': i117, 'batch': [i104, i107]}]
            self.assertEqual(s.priority_choice(set())[:3], ('polish', i117, 'fresh'))
            s.running = []; s.cpus = [0, 1]; s._recent = [(time.monotonic(), 'join', 30.0)]    # 30 CPU-s in >= 2 x 120: 12.5%
            self.assertEqual(s.priority_choice(set())[:3], ('polish', i117, 'fresh')); self.assertGreater(s._dec['join_share'], 0.1)
            s.args.join_share = 0.2; self.assertEqual(s.priority_choice(set())[0], 'join')
            s.running = [{'op': 'join', 'target': i117, 'batch': [i104, i107]}]
            self.assertEqual(s.priority_choice({t117, i117})[:3], ('polish', i107, 'fresh'))      # busy tuple skipped
            for t in (t104, t107, t117): s.attempts[('polish', t)] = 1
            self.assertEqual(s.priority_choice(set())[:3], ('pull', i117, 'fresh'))
            for t in (t104, t107, t117): s.attempts[('pull', t)] = 1
            s.args.variants_first = False                                   # default: repeats under the caps first
            self.assertEqual(s.priority_choice(set())[:3], ('polish', i117, 'repeat'))
            s.args.variants_first = True
            # 3 variant: a structure of a front tuple without its own first pull
            for i in (i104, i107, i117): s.sattempts[('polish', s.skey(i))] = 1
            for i in (i104, i117): s.sattempts[('pull', s.skey(i))] = 1
            self.assertEqual(s.priority_choice(set())[:3], ('pull', i107, 'variant'))
            s.sattempts[('pull', s.skey(i107))] = 1
            # 4 near: a cell 2 gates above a dominating front point
            st, r, g = s.ar.admit(bloat(load(P107), 1), force_keep=True); self.assertEqual(st, 'admitted'); s.last_admit = r['t_admit']
            self.assertNotIn(r['id'], s.ar.front_ids())
            self.assertEqual(s.priority_choice(set())[:3], ('polish', r['id'], 'near'))
            s.sattempts[('polish', s.skey(r['id']))] = 1; s.sattempts[('pull', s.skey(r['id']))] = 1
            # 5 other: trb once per front tuple
            self.assertEqual(s.priority_choice(set())[:3], ('trb', i117, 'other'))
            for t in (t104, t107, t117): s.attempts[('trb', t)] = 1
            # 6 repeat: under the caps first (polish=2, pull=3), fewest jobs first, never trb or join
            self.assertEqual(s.priority_choice(set())[:3], ('polish', i117, 'repeat'))
            for t in (t104, t107, t117): s.attempts[('polish', t)] = 2
            self.assertEqual(s.priority_choice(set())[:3], ('pull', i117, 'repeat'))
            for t in (t104, t107, t117): s.attempts[('pull', t)] = 3
            self.assertEqual(s.priority_choice(set())[:3], ('polish', i117, 'repeat-over-cap'))
            s.args.repeat_max = 3                                           # pull has had 3 jobs per tuple: only polish left
            self.assertEqual(s.priority_choice(set())[:3], ('polish', i117, 'repeat-over-cap'))
            for t in (t104, t107, t117): s.attempts[('polish', t)] = 3
            self.assertIsNone(s.priority_choice(set())); self.assertEqual(s._dec['mode'], 'empty')
            s.suspended = {o: time.time() + 99 for o in s.ops}
            self.assertIsNone(s.priority_choice(set())); self.assertEqual(s._dec['mode'], 'none')
            s._lockf.close()

    def test_launch_batches_join_and_marks_survive_a_restart(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'join,polish'); s.seed([str(P104), str(P107), str(P117)])
            real = SCH.subprocess.Popen; SCH.subprocess.Popen = FakePopen
            try:
                s.end = time.time() + 100
                j = s.launch(3, set())
                self.assertEqual((j['op'], j['why']), ('join', 'join')); self.assertEqual(len(j['batch']), 2)
                cmd = j['cmd']; b = cmd[cmd.index('--batch') + 1].split(',')
                self.assertEqual(sorted(x.split(':')[0] for x in b), sorted(j['batch']))
                self.assertEqual(j['decision']['level'], 'join'); self.assertEqual(j['decision']['batch'], 2)
                self.assertTrue(all(s.attempts[('join', s.target_key(i))] == 1 for i in s.ar.rec))
                s.running.append(j)
                self.assertEqual(s.busy_set(), set())                   # a join job does not block kernel jobs on its targets
                j2 = s.launch(3, s.busy_set())
                self.assertEqual(j2['op'], 'polish')                    # the join CPU is taken
                s.running.append(j2); self.assertIn(j2['target'], s.busy_set()); self.assertIn(j2['key'], s.busy_set())
                j['lf'].close(); j2['lf'].close(); s.running = []
            finally:
                SCH.subprocess.Popen = real
            t = s.last_admit
            fj = fake_job(s, 'join', j['target'], info={'joined_through': t, 'joined_through_by': {i: t for i in s.ar.rec}, 'joins': []})
            s.finish(fj)
            self.assertEqual({s.join_mark[i] for i in s.ar.rec}, {t})
            line = json.loads(Path(d, 'stats.jsonl').read_text().splitlines()[-1])
            self.assertEqual(len(line['join_marks']), 3); self.assertEqual(line['gain_rule'], AR.GAIN_RULE['value'])
            self.assertEqual(HO.join_marks(d), {i: t for i in s.ar.rec})            # the operators' reader
            self.assertIsNone(s.priority_choice(set())[0] == 'join' or None)
            s._lockf.close()
            s2 = sched(d, '--ops', 'join,polish')
            self.assertEqual({s2.join_mark[i] for i in s2.ar.rec}, {t})
            self.assertEqual(s2.hist['join'][-1], (1.0, 0.0))                     # tagged lines feed the bandit history

    def test_op_join_batch_partner_boundary_and_archived_copies(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'join'); s.seed([str(P104), str(P107), str(P117)])
            by = {metrics(s.ar.circuit(i)): i for i in s.ar.rec}
            x, y = by[(32, 5, 104, 30)], by[(32, 4, 117, 19)]
            args = types.SimpleNamespace(inp=x, since=0.0, batch='%s:0.0' % y, partners=300, seconds=30.0, max_cands=40, archive=d)
            cands, info = HO.op_join(s.ar, args, random.Random(1), None)
            self.assertEqual([b['target'] for b in info['batch']], [x, y])
            self.assertEqual(set(info['joined_through_by']), {x, y})
            self.assertEqual(info['joined_through_by'][y], s.last_admit)
            self.assertEqual(info['tried'], info['not_placed'] + info['duplicate'] + info['archived'] + len(cands) + info['kept_over_limit'] + info['deferred'])
            for c in cands:                                   # cleaned, placeable, not archived
                self.assertIs(C.clean(c), c); self.assertTrue(s.ar.would_place(metrics(c))); self.assertNotIn(cid(c), s.ar.rec)
            n_all = len(cands)
            args.max_cands = 1
            c1, i1 = HO.op_join(s.ar, args, random.Random(1), None)
            self.assertLessEqual(len(c1), 1)
            if n_all > 1:
                self.assertEqual(i1['stop'], 'max_cands'); self.assertGreater(i1['deferred'] + i1['kept_over_limit'], 0)
            if i1['deferred']:                                # the mark stops before the partner that did not fit
                self.assertLess(min(v for v in i1['joined_through_by'].values()), s.last_admit)
            s._lockf.close()

    def test_placeable_and_intermediate_bests(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish'); s.seed([str(P104), str(P107), str(P117)])
            c = load(P104)
            self.assertEqual(HO.placeable(s.ar, c)[2], 'archived')
            self.assertEqual(HO.placeable(s.ar, rewritten(c))[2], 'archived structure')
            g = list(c.gates) + [c.gates[-1]]                 # a duplicate gate: archived after cleaning
            self.assertIn(HO.placeable(s.ar, core.Circuit(c.n, c.m, g, list(c.outputs)))[2], ('archived', 'archived structure'))
            near = bloat(load(P107), 1); far = bloat(load(P107), 5)
            self.assertEqual(HO.placeable(s.ar, near)[2], 'ok'); self.assertEqual(HO.placeable(s.ar, far)[2], 'not placed')
            bd = Path(d) / 'bests'; bd.mkdir()
            for k, x in enumerate([c, near, far, rewritten(near)], 1): (bd / ('best-%d.bfx' % k)).write_text(core.to_kernel(x))
            info = {'bests_dir': str(bd)}
            out = HO.with_bests(s.ar, [c], info, 8)
            self.assertEqual(len(out), 2); self.assertEqual(metrics(out[1]), metrics(near))
            self.assertEqual((info['bests']['files'], info['bests']['returned'], info['bests']['archived'], info['bests']['not placed']), (4, 1, 1, 1))
            self.assertEqual(HO.with_bests(s.ar, [c], {'bests_dir': str(bd)}, 0), [c])
            s._lockf.close()

    def test_pull_lowers_gd_and_trb_keeps_the_input_gd(self):
        calls = []
        real = HO._kernel
        HO._kernel = lambda c_, caps, *a: (calls.append(dict(caps)) or ([], {}))
        try:
            with tempfile.TemporaryDirectory() as d:
                s = sched(d, '--ops', 'pull'); s.seed([str(P117)]); x = next(iter(s.ar.rec))
                for seed in range(20):
                    args = types.SimpleNamespace(inp=x, caps=None, objective='a,ad,cost,gd', seed=seed, seconds=1, archive=d, bests=8)
                    cands, info = HO.op_pull(s.ar, args, random.Random(seed), None)
                    self.assertEqual(info['lowered'], 'GD')
                self.assertTrue(all(cp['GD'] < 19 and cp['A'] == 32 for cp in calls))
                args.lower = 'A'; HO.op_pull(s.ar, args, random.Random(1), None); self.assertEqual(calls[-1]['A'], 31)
                args.lower = 'X'; self.assertRaises(HO.OpError, HO.op_pull, s.ar, args, random.Random(1), None)
                args = types.SimpleNamespace(inp=x, seconds=1.0, max_cands=40)
                cands, info = HO.op_trb(s.ar, args, random.Random(2), None)
                self.assertTrue(all(k.endswith('/-0') for k in info['by_region']))
                gains = [s.ar.gain(metrics(c)) for c in cands]
                self.assertEqual(gains, sorted(gains, reverse=True))
                s._lockf.close()
        finally:
            HO._kernel = real

    def test_ingest_period_and_cap_renewals_after_restart(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull', '--tuple-caps', 'polish=2', '--cap-renew', 'box')
            s.seed([str(P104), str(P107), str(P117)])
            f = Path(d) / 'found' / 'a.bfx'; f.parent.mkdir(); f.write_text(core.to_kernel(bloat(load(P104), 1)))
            s.ingest_globs = [str(f.parent / '*.bfx')]; s.last_ingest = time.time() - 30
            s.maybe_ingest(); self.assertNotIn('ingested', Path(d, 'events.jsonl').read_text())
            s.last_ingest = time.time() - 61; s.maybe_ingest()
            self.assertIn('"ingested"', Path(d, 'events.jsonl').read_text())
            self.assertIsNotNone(s.apply_control({'ingest_every': 0}))
            self.assertIsNone(s.apply_control({'ingest_every': 5})); self.assertEqual(s.args.ingest_every, 5.0)
            for t in ((32, 5, 104, 30), (32, 5, 107, 22), (32, 4, 117, 19)): s.attempts[('polish', t)] = 2
            self.assertEqual(s.renew_caps((32, 4, 117, 19)), 2)
            want = (dict(s.cap_base), dict(s.renewals)); s._lockf.close()
            s2 = sched(d, '--ops', 'polish,pull', '--tuple-caps', 'polish=2', '--cap-renew', 'box')
            self.assertEqual((s2.cap_base, s2.renewals), want)
            s2._lockf.close()

    def test_wait_wakes_when_a_child_exits(self):
        wake = SCH._wake_setup_fn()
        self.assertIsNotNone(wake)
        try:
            t0 = time.monotonic(); p = subprocess.Popen(['sleep', '0.3'])
            SCH._wait_fn(wake, 20.0); el = time.monotonic() - t0
            p.wait(); self.assertLess(el, 10.0)
            t0 = time.monotonic(); SCH._wait_fn(wake, 0.2); self.assertGreaterEqual(time.monotonic() - t0, 0.15)   # drained
        finally:
            SCH._wake_close_fn(wake)

    def test_archive_load_and_structure_check_before_verify(self):
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d); c = load(P104); ar.admit(c, force_keep=True)
            (Path(d) / 'archive' / 'cleaned.json').write_text('[]')
            self.assertEqual(Archive(d).load_errors, [])
            n = [0]; real = AR.verify
            AR.verify = lambda x: (n.__setitem__(0, n[0] + 1) or real(x))
            try:
                st, r, g = ar.admit(rewritten(c), force_keep=True)
                self.assertEqual((st, n[0]), ('duplicate-structure', 0))
                st, r, g = ar.admit(bloat(c, 1), force_keep=True)
                self.assertEqual((st, n[0]), ('admitted', 1))
            finally:
                AR.verify = real

    def test_interface_spaces_of_the_inverse(self):
        try:
            for f in aesfn.NAMES:
                aesfn.use(f); t = aesfn.table(f)
                pre = [C._gpow(t[x], 254) for x in range(256)] if f == 'aes-invsbox' else list(range(256))
                N = C._bit_tables(lambda x: C._gpow(pre[x], 17))
                sp = C.interface_spaces()
                self.assertTrue(all(b in sp['N'] for b in N), f)
                self.assertTrue(all(b in sp['out'] for b in C._bit_tables(lambda x: t[x])), f)
            aesfn.use('aes-invsbox')
            fwdN = C._bit_tables(lambda x: C._gpow(x, 17))
            self.assertFalse(all(b in C.interface_spaces()['N'] for b in fwdN))
        finally:
            aesfn.use('aes-sbox')

    def test_nursery_slack_for_one_generation(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish'); s.seed([str(P104), str(P107), str(P117)])
            st, g0, gn = s.ar.admit(bloat(load(P107), 4), operator='gen_skel', force_keep=True); self.assertEqual(st, 'admitted')
            c1 = bloat(load(P104), 5); c2 = bloat(load(P117), 5)
            self.assertFalse(s.ar.would_place(metrics(c1))); self.assertFalse(s.ar.would_place(metrics(c2)))
            j = fake_job(s, 'polish', g0['id'], cands=[c1]); s.finish(j)
            out = json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())['outcome']
            self.assertEqual(out[0]['status'], 'admitted')                      # a job on a generator's output: slack
            i1 = out[0]['id']
            j = fake_job(s, 'polish', i1, cands=[c2]); s.finish(j)
            out = json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())['outcome']
            self.assertEqual(out[0]['status'], 'not-better')                    # its descendants: no slack
            s._lockf.close()


if __name__ == '__main__':
    unittest.main()
