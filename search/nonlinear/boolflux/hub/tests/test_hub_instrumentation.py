"""Hub instrumentation (2026-11-16):  python3 -m unittest boolflux.hub.tests.test_hub_instrumentation   (from search/nonlinear/)

Decision records of the scheduler (operator and target choice, idle CPUs, admission reasons, summaries, process
timing), archive.explain / gain_reason, operator counters (trb, join), Recorder counts per `how`.  The recording
must not change a choice: the instrumented choose_op / choose_target are compared with the 50ce001 versions
(copied below) on the same random stream.
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core, runlog                                    # noqa: E402
from boolflux.hub import ops as HO, scheduler as SCH                  # noqa: E402
from boolflux.hub.common import NIST, load, metrics, cid               # noqa: E402
from boolflux.hub.tests.test_hub_invariants import sched, fake_job, OPEN, P104, P107, P117   # noqa: E402

SCH.kernel_bin = lambda d: None


def tearDownModule():
    for f in OPEN:
        try: f.close()
        except Exception: pass


# ---- the choice functions of commit 50ce001 (before the instrumentation), for the equivalence test ----
def old_choose_op(self):
    ops = self.active_ops()
    if not ops: return None, 'none'
    if self.rng.random() < self.args.eps: return self.rng.choice(ops), 'explore'
    return max(ops, key=lambda o: (self.score(o), self.rng.random())), 'exploit'


def old_choose_target(self, op, busy, ignore_caps=False):
    pool = self.ar.front_ids()
    if op in ('polish', 'pull', 'trb') and self.args.nursery > 0 and self.rng.random() < self.args.nursery:
        nu = [i for i in self.nursery_ids(op) if self.target_key(i) not in busy]
        if nu: return nu[0]
    ad3 = self.ad3_share > 0 and self.rng.random() < self.ad3_share
    if op in ('polish', 'pull', 'trb') and self.args.near > 0 and self.rng.random() < self.args.near:
        pool = self.near_ids() or pool
    if ad3:
        p3 = [i for i in pool if self.ar.rec[i]['AD'] <= 3]
        if p3: pool = p3
    ids = [i for i in pool if self.target_key(i) not in busy]
    if not ignore_caps: ids = [i for i in ids if not self.capped(op, self.target_key(i))]
    if op == 'join' and self.args.join_mode == 'incremental':
        ids = [i for i in ids if self.join_mark.get(i, 0.0) < self.last_admit]
    if not ids: return None
    self.rng.shuffle(ids)
    if self.args.target_mode == 'id':
        return min(ids, key=lambda i: self.attempts.get((op, i), 0))
    return min(ids, key=lambda i: (self.eff_attempts(op, self.target_key(i)), 0 if self.ar.rec[i]['A'] <= 31 else 1))


class FakePopen:
    def __init__(self, cmd, **kw): self.pid = 0; self.returncode = None


class TestDecisions(unittest.TestCase):
    def test_choices_equal_the_uninstrumented_ones(self):
        """same random stream -> same operator, same target, same final random state, in every mode"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull,join,trb', '--eps', '0.3', '--near', '0.5', '--nursery', '0.3', '--tuple-caps', 'polish=1')
            s.seed([str(P104), str(P107), str(P117)]); s.ad3_share = 0.4
            s.hist['trb'] = [(30.0, 2.0)]; s.hist['pull'] = [(30.0, 2.0)]       # a tie at the top
            busy = {s.target_key(next(iter(s.ar.rec)))}
            for n in range(200):
                st = s.rng.getstate()
                new = s.choose_op(); st_new = s.rng.getstate()
                s.rng.setstate(st); old = old_choose_op(s)
                self.assertEqual(new, old); self.assertEqual(s.rng.getstate(), st_new)
                for op in ('polish', 'join', 'trb'):
                    st = s.rng.getstate()
                    t_new = s.choose_target(op, busy if n % 2 else set(), ignore_caps=bool(n % 3 == 0)); st_new = s.rng.getstate()
                    s.rng.setstate(st); t_old = old_choose_target(s, op, busy if n % 2 else set(), ignore_caps=bool(n % 3 == 0))
                    self.assertEqual(t_new, t_old); self.assertEqual(s.rng.getstate(), st_new)
                    if t_new: s.attempts[(op, s.target_key(t_new))] = s.attempts.get((op, s.target_key(t_new)), 0) + 1

    def test_launch_records_the_decision(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'join,trb', '--eps', '0', '--policy', 'bandit'); s.seed([str(P104), str(P107)])
            for i in s.ar.rec: s.join_mark[i] = s.last_admit             # join has nothing to do
            s.hist['join'] = [(1.0, 100.0)]                              # the bandit prefers it
            real = SCH.subprocess.Popen; SCH.subprocess.Popen = FakePopen
            try:
                s.end = time.time() + 100
                j = s.launch(3, set())
                dec = j['decision']
                self.assertEqual((j['op'], dec['why'], dec['mode']), ('trb', 'exploit-fallback', 'exploit'))
                self.assertGreater(dec['bandit']['join']['score'], dec['bandit']['trb']['score'])
                self.assertEqual(dec['bandit']['join']['n'], 1)
                self.assertEqual(dec['targets_tried'][0]['op'], 'join'); self.assertEqual(dec['targets_tried'][0]['n_unjoined'], 0)
                self.assertEqual(dec['target_choice']['op'], 'trb'); self.assertIn('attempts', dec['target_choice'])
                s.join_mark.clear(); s.hist['trb'] = []
                j2 = s.launch(3, set())
                self.assertEqual(j2['op'], 'join'); self.assertEqual(j2['decision']['join_partners'], 1)
                # nothing launchable: the reason is kept for the idle event
                s.suspended = {'join': time.time() + 99, 'trb': time.time() + 99}
                self.assertIsNone(s.launch(3, set())); self.assertIn('no active operator', s._idle_why)
                s.suspended = {}; s.end = time.time() + 1
                self.assertIsNone(s.launch(3, set())); self.assertIn('left', s._idle_why)
                ev = runlog.read_events(s.runlog.events_path)
                jobs = [e for e in ev if e['ev'] == 'job']
                self.assertEqual(len(jobs), 2); self.assertEqual(jobs[0]['decision']['why'], 'exploit-fallback')
                self.assertEqual(jobs[0]['target_metrics'], list(metrics(s.ar.circuit(j['target']))))
                j['lf'].close(); j2['lf'].close()
            finally:
                SCH.subprocess.Popen = real

    def test_admission_reasons_summary_and_timing(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d); s.seed([str(P104), str(P117)])
            tid = next(iter(s.ar.rec)); c104 = load(P104); c107 = load(P107)
            n0 = c104.n + len(c104.gates); o = list(c104.outputs); g = list(c104.gates); x = o[0]
            for k in range(8): g.append((3, x, x)); x = n0 + k                # 8 NOTs on output 0: 112 gates, GD 38
            o[0] = x; worse = core.Circuit(c104.n, c104.m, g, o)
            j = fake_job(s, 'trb', tid, [c107, c104, worse])
            j.update({'m0': time.monotonic() - 1.0, 'mono_exit': time.monotonic(), 'proc_cpu_s': 0.9, 't_exit': time.time()})
            (j['jd'] / 'record.json').write_text(json.dumps(dict(json.loads((j['jd'] / 'record.json').read_text()),
                                                               timing={'mono_main': time.monotonic() - 0.8, 'mono_end': time.monotonic() - 0.1,
                                                                       'setup_s': 0.2, 'op_s': 0.5})))
            s.finish(j)
            run = json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())
            st = {o['cand']: o for o in run['outcome']}
            self.assertEqual(st['cand-000.bfx']['status'], 'admitted'); self.assertTrue(st['cand-000.bfx']['reason'])
            self.assertEqual(st['cand-001.bfx']['status'], 'duplicate'); self.assertIn('same circuit text', st['cand-001.bfx']['reason'])
            nb = st['cand-002.bfx']; self.assertEqual(nb['status'], 'not-better')
            self.assertEqual(nb['reason']['dominating_front_min_G'], 104); self.assertIn('slack 6', nb['reason']['reason'])
            self.assertEqual(run['admission']['counts'], {'admitted': 1, 'duplicate': 1, 'not-better': 1})
            self.assertGreaterEqual(run['admission']['finish_s'], run['admission']['admit_s'])
            tm = run['timing']
            self.assertAlmostEqual(tm['mono_wall_s'], 1.0, delta=0.05); self.assertAlmostEqual(tm['start_to_main_s'], 0.2, delta=0.05)
            self.assertAlmostEqual(tm['end_to_exit_seen_s'], 0.1, delta=0.05); self.assertEqual(tm['proc_cpu_s'], 0.9)
            line = json.loads(Path(d, 'stats.jsonl').read_text().splitlines()[-1])
            self.assertEqual(line['proc_cpu_s'], 0.9); self.assertIn('finish_s', line)
            ev = [e for e in runlog.read_events(s.runlog.events_path) if e['ev'] == 'admission']
            self.assertEqual(ev[-1]['counts']['admitted'], 1)
            s.summary()
            sm = [json.loads(l) for l in Path(d, 'events.jsonl').read_text().splitlines() if '"summary"' in l][-1]
            self.assertEqual(sm['per_op']['trb']['jobs'], 1); self.assertEqual(sm['per_op']['trb']['admitted'], 1)
            self.assertIn('trb', sm['bandit']); self.assertEqual(s.win, {})
            adm = [json.loads(l) for l in Path(d, 'events.jsonl').read_text().splitlines() if '"admit"' in l][-1]
            self.assertIn('gain_reason', adm)

    def test_lineage_file(self):
        """$BOOLFLUX_LINEAGE: a seed is its own root; an admitted child inherits the roots, one step more"""
        with tempfile.TemporaryDirectory() as d:
            lf = Path(d) / 'lineage.jsonl'; os.environ[runlog.LINEAGE_ENV] = str(lf)
            try:
                s = sched(Path(d) / 'hub'); s.seed([str(P104)])
                tid = next(iter(s.ar.rec))
                s.finish(fake_job(s, 'trb', tid, [load(P107)]))
                L = [json.loads(x) for x in lf.read_text().splitlines()]
                self.assertEqual([(x['op'], x['roots'], x['steps']) for x in L], [('seed', [P104.name], 0), ('trb', [P104.name], 1)])
                self.assertEqual(L[1]['parents'], [tid]); self.assertEqual(runlog.lineage_lookup(L[1]['id'])['id'], L[1]['id'])
            finally:
                os.environ.pop(runlog.LINEAGE_ENV, None)

    def test_host_sampler_and_interpreter_record(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d); s.cpus = [0]
            s.host_sample(); time.sleep(0.2); s.host_sample()
            if Path('/proc/stat').exists():
                h = json.loads(Path(d, 'host.jsonl').read_text().splitlines()[-1])
                self.assertIn('busy', h); self.assertTrue(all(0 <= v <= 1 for v in h['busy'].values()))
            ip = json.loads(Path(s.runlog.path).read_text())['interpreter']
            self.assertEqual(ip['sys_path'][:1], sys.path[:1]); self.assertIn('customize', ip)

    def test_reap_keeps_rusage_and_return_code(self):
        p = subprocess.Popen([sys.executable, '-c', 'import sys; sum(range(10**6)); sys.exit(3)'])
        job = {'p': p}
        t0 = time.time()
        while SCH.Scheduler.reap(job) is None and time.time() - t0 < 30: time.sleep(0.02)
        self.assertEqual(p.returncode, 3); self.assertEqual(p.poll(), 3)
        self.assertGreater(job['proc_cpu_s'], 0); self.assertGreater(job['proc_maxrss_kb'], 0); self.assertIn('mono_exit', job)
        p2 = subprocess.Popen(['sh', '-c', 'kill -9 $$']); job2 = {'p': p2}
        while SCH.Scheduler.reap(job2) is None: time.sleep(0.02)
        self.assertEqual(p2.returncode, -9)


class TestArchiveExplain(unittest.TestCase):
    def test_explain_and_gain_reason_match_the_decisions(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d); s.seed([str(P104), str(P107), str(P117)]); ar = s.ar
            rng = random.Random(3)
            for n in range(400):
                m = (rng.randint(30, 34), rng.randint(3, 6), rng.randint(95, 125), rng.randint(17, 32))
                for slack in (None, 40):
                    self.assertEqual(ar.explain(m, slack)['reason'] == 'would place', ar.would_place(m, slack), m)
                g = ar.gain(m); r = ar.gain_reason(m)
                want = {'dominated': 0.0, 'new (A, AD) at a known AD': 8.0, 'new AND depth': 4.0, 'GD reach': 0.5}
                if r in want: self.assertEqual(g, want[r], (m, r))
                else: self.assertEqual(g, 1.0 + 0.5 * (min(int(r.split()[-1]), 6) - 1), (m, r))


class TestOperatorCounters(unittest.TestCase):
    def test_trb_and_join_counters(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'join'); s.seed([str(P104), str(P107), str(P117)])
            x = next(i for i in s.ar.rec if metrics(s.ar.circuit(i)) == (32, 5, 104, 30))
            args = types.SimpleNamespace(inp=x, since=0.0, partners=300, seconds=30.0, max_cands=40, archive=d)
            j = fake_job(s, 'join', [i for i in s.ar.rec if i != x][0], info={'joined_through': s.last_admit, 'joins': []}); s.finish(j)
            cands, info = HO.op_join(s.ar, args, random.Random(1), None)
            pa = info['pair_accounting']
            self.assertEqual(len(pa['partner_hash']), 16); self.assertEqual(pa['repeated_pairs'], 1)
            self.assertEqual(info['stop'], 'partners done')
            self.assertEqual(info['tried'], info['not_placed'] + info['duplicate'] + info['archived'] + len(cands) + info['kept_over_limit'] + info['deferred'])
            args = types.SimpleNamespace(inp=x, seconds=1.0, max_cands=40)
            cands, info = HO.op_trb(s.ar, args, random.Random(2), None)
            tot = sum(sum(v.values()) for v in info['by_region'].values())
            self.assertEqual(tot, info['reps']); self.assertGreater(info['reps'], 0)
            self.assertEqual(sum(info['dG'].values()), sum(n for v in info['by_region'].values() for k, n in v.items() if k.startswith('built')))


class TestRecorderCounts(unittest.TestCase):
    def test_offers_by_how(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ops'))
        import common as CM
        with tempfile.TemporaryDirectory() as d:
            r = CM.Recorder(d, 'test', str(P104), str(P104), 1, 'cmd', 'method', {})
            c = load(P104)
            self.assertIsNone(r.offer(c, how='g30'))                         # the start's own tuple: dominated
            self.assertIsNone(r.offer(load(NIST / 'aes-sbox' / 'aes-sbox-a36-ad4-g148-gd14-xx112-24.circ.txt'), how='g30')
                              if (NIST / 'aes-sbox' / 'aes-sbox-a36-ad4-g148-gd14-xx112-24.circ.txt').exists() else None)
            self.assertEqual(r.by_how['g30']['offered'], 2 if (NIST / 'aes-sbox' / 'aes-sbox-a36-ad4-g148-gd14-xx112-24.circ.txt').exists() else 1)
            self.assertEqual(r.by_how['g30']['dominated'], 1)
            r.finish('ok')
            res = json.loads(Path(d, 'result.json').read_text())
            self.assertEqual(res['offers_by_how']['g30']['offered'], r.by_how['g30']['offered'])


if __name__ == '__main__':
    unittest.main()
