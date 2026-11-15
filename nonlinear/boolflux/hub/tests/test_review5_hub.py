"""Review 5 (hub) regression tests:  python3 -m unittest boolflux.hub.tests.test_review5_hub   (from nonlinear/)

One test (at least) per finding of review5/HUB.md; the finding number is in each test's docstring.
No test starts a kernel or compiles one: scheduler jobs are faked on disk and finished in-process.
"""
import importlib.util
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
from boolflux import core                                           # noqa: E402
from boolflux.hub import archive as AR, common as C, ops as HO, scheduler as SCH   # noqa: E402
from boolflux.hub.archive import Archive, pareto                    # noqa: E402
from boolflux.hub.common import NIST, load, metrics, cid, structure_key, verify   # noqa: E402

P104 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'
P107 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt'
P117 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'
HUB = Path(__file__).resolve().parents[1]
SCH.kernel_bin = lambda d: None          # no test here runs the gate kernel


def rewritten(c):
    """the same DAG written differently: operands of symmetric gates swapped, and two independent
    neighbouring gates exchanged (metrics, function and structure unchanged; the text is not)"""
    g = [(op, b, a) if op in core.SYMMETRIC else (op, a, b) for op, a, b in c.gates]
    n = c.n
    for j in range(len(g) - 1):
        if n + j not in g[j + 1][1:]:
            x, y = n + j, n + j + 1
            sw = lambda s: y if s == x else (x if s == y else s)
            g[j], g[j + 1] = g[j + 1], g[j]
            g = g[:j + 2] + [(op, sw(a), sw(b)) for op, a, b in g[j + 2:]]
            return core.Circuit(c.n, c.m, g, [sw(o) for o in c.outputs])
    raise AssertionError('no independent neighbours')


OPEN = []


def sched(d, *extra):
    cpu = str(min(os.sched_getaffinity(0)))
    s = SCH.Scheduler(SCH.parser().parse_args(['--dir', str(d), '--cpus', cpu] + list(extra)))
    OPEN.append(s._lockf)
    return s


def tearDownModule():
    for f in OPEN: f.close()


def fake_job(s, op, tid, cands=(), rc=0, record=True, cand_ids=None, info=None, error=None):
    s.nrun += 1
    run_id = '%s.r%05d-%s' % (s.uid, s.nrun, op); jd = s.dir / 'jobs' / run_id; jd.mkdir()
    for k, c in enumerate(cands):
        (jd / ('cand-%03d.bfx' % k)).write_text(c if isinstance(c, str) else core.to_kernel(c))
    if record:
        rec = {'operator': op, 'caps': None, 'objective': 'a,ad,cost,gd', 'seed': 5, 'seconds': 3.0, 'wall_s': 1.0,
               'cpu_s': 1.0, 'code_version': 'opversion', 'info': info or {},
               'cand_ids': cand_ids if cand_ids is not None else [cid(c) for c in cands if not isinstance(c, str)]}
        if error: rec['error'] = error
        (jd / 'record.json').write_text(json.dumps(rec))
    return {'p': types.SimpleNamespace(returncode=rc, pid=0), 'lf': open(s.dir / 'jobs' / (run_id + '.log'), 'w'), 'op': op,
            'why': 'test', 'target': tid, 'run_id': run_id, 'jd': jd, 'seed': 5, 'cpu': 0, 't0': time.time() - 1, 'cmd': ['x'],
            'secs': 3.0, 'script': str(s.scripts[op]), 'script_sha': 'sha', 'limit': 100.0, 'since': None, 'key': s.target_key(tid)}


class TestArchive(unittest.TestCase):
    def test_structural_duplicate_not_admitted(self):
        """H2: a cell keeps K distinct structures; the same DAG in another gate order is a duplicate"""
        c = load(P104); r = rewritten(c)
        self.assertNotEqual(cid(c), cid(r))
        self.assertEqual(structure_key(c), structure_key(r))
        self.assertEqual(metrics(c), metrics(r))
        self.assertNotEqual(structure_key(c), structure_key(load(P107)))
        dead = core.Circuit(c.n, c.m, list(c.gates) + [(6, 0, 1)], list(c.outputs))
        self.assertNotEqual(structure_key(c), structure_key(dead))       # a dead gate counts in G: not the same circuit
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d)
            self.assertEqual(ar.admit(c)[0], 'admitted')
            st, rec, g = ar.admit(r)
            self.assertEqual(st, 'duplicate-structure')
            self.assertEqual(rec['id'], cid(c))
            self.assertEqual(ar.admit(r, force_keep=True)[0], 'duplicate-structure')
            self.assertEqual(len(ar.cells[Archive.key(metrics(c))]), 1)
            ar2 = Archive(d)                                             # records admitted before review 5 carry no skey
            for rr in ar2.rec.values(): rr.pop('skey')
            self.assertEqual(ar2.admit(r)[0], 'duplicate-structure')
        with tempfile.TemporaryDirectory() as d:                         # an archive filled by the old code: both in one cell
            ar = Archive(d); ar.admit(c); ar._skeys = {}; self.assertEqual(ar.admit(r)[0], 'admitted')
            k = Archive.key(metrics(c))
            ix = Path(d, 'archive', 'index.jsonl'); rows = [json.loads(l) for l in ix.read_text().splitlines()]
            for row in rows:
                row.pop('skey'); Path(d, 'archive', row['id'] + '.json').write_text(json.dumps(row))
            ix.unlink()
            old = Archive(d); self.assertEqual(len(old.cells[k]), 2)
            self.assertEqual(old.dedupe_legacy(), 1); self.assertEqual(old.cells[k], [cid(c)])
            self.assertEqual(Archive(d).cells, old.cells)                # readers (operators) see the same cells
            self.assertEqual(len(Archive(d).rec), 2)                     # nothing is deleted
            self.assertEqual(Archive(d).dedupe_legacy(), 0)

    def test_cells_rebuilt_from_records(self):
        """H1: cells.json is a cache; a stale or damaged one cannot corrupt the cells or crash the load"""
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d)
            for p in (P104, P107): self.assertEqual(ar.admit(load(p))[0], 'admitted')
            good = dict(ar.cells)
            cf = Path(d, 'archive', 'cells.json')
            cf.write_text(json.dumps({'32,5,30': ['feedfeedfeed'], '1,1,1': ['000000000000']}))   # ids without records
            ar2 = Archive(d)
            self.assertEqual(ar2.cells, good); self.assertTrue(ar2.cells_repaired)
            self.assertEqual(ar2.cell_min((32, 5, 30)), 104)
            cf.write_text('{"32,5,')                                      # cut off in the middle of a write
            self.assertEqual(Archive(d).cells, good)
            cf.unlink()
            ar3 = Archive(d); self.assertEqual(ar3.cells, good); self.assertFalse(ar3.cells_repaired)
            Path(d, 'archive', 'zzzz.json').write_text('{"id": "zz')     # damaged record: reported, not fatal
            ar4 = Archive(d); self.assertEqual(ar4.cells, good); self.assertEqual(len(ar4.load_errors), 1)

    def test_index_is_a_cache_of_the_records(self):
        """H10: operators load index.jsonl (one read); records missing from it are read from their files"""
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d)
            for p in (P104, P107, P117): ar.admit(load(p), force_keep=True)
            ix = Path(d, 'archive', 'index.jsonl')
            self.assertEqual(len(ix.read_text().splitlines()), 3)
            a2 = Archive(d); self.assertEqual(a2.rec, ar.rec); self.assertEqual(a2.index_missing, 0)
            lines = ix.read_text().splitlines()
            ix.write_text(lines[0] + '\n' + lines[1][:40])               # second line cut, third missing
            a3 = Archive(d)
            self.assertEqual(set(a3.rec), set(ar.rec)); self.assertEqual(a3.index_missing, 2); self.assertEqual(a3.cells, ar.cells)
            a3.write_index(); self.assertEqual(Archive(d).index_missing, 0)

    def test_incremental_front_equals_recomputation(self):
        """H11: the front is updated in O(front) per admission and stays equal to the full recomputation"""
        rng = random.Random(5)
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d); ar.front()
            for n in range(600):
                r = {'id': 'x%04d' % n, 'A': rng.randint(27, 36), 'AD': rng.randint(3, 6), 'G': rng.randint(100, 150), 'GD': rng.randint(11, 30)}
                ar.rec[r['id']] = r; ar._place(r)
                if n % 20 == 0 or n > 580:
                    self.assertEqual(sorted(ar.front()), pareto(ar.points()))
            pts = ar.points()
            self.assertEqual(pareto(pts), sorted(p for p in set(pts) if not any(q != p and C.leq(q, p) for q in pts)))
            self.assertEqual(sorted(set(ar.front_ids())), sorted(i for k, ids in ar.cells.items() for i in ids
                                                                 if (k[0], k[1], ar.rec[i]['G'], k[2]) in set(pareto(pts))))

    def test_malformed_circuit_is_rejected_not_raised(self):
        """H12: a candidate that is not a well-formed circuit is a rejection, never an exception"""
        c = load(P104)
        fwd = core.Circuit(8, 8, [(6, 0, 9), (6, 1, 2)], [8] * 8)
        self.assertFalse(verify(fwd)[0])
        self.assertFalse(verify(core.Circuit(4, 8, [(6, 0, 1)], [4] * 8))[0])
        self.assertFalse(verify(core.Circuit(8, 8, list(c.gates), list(c.outputs[:7]) + [10 ** 6]))[0])
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d)
            for bad in (fwd, core.Circuit(8, 8, list(c.gates), list(c.outputs[:7]) + [10 ** 6])):
                st, r, g = ar.admit(bad, force_keep=True)
                self.assertTrue(st.startswith('rejected'), st)
            self.assertEqual(ar.rec, {})

    def test_circuit_cache_is_bounded(self):
        """H13: the scheduler does not keep every admitted circuit in memory"""
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d, cache=2)
            for p in (P104, P107, P117): ar.admit(load(p), force_keep=True)
            self.assertLessEqual(len(ar.circ), 2)
            for i in ar.rec: self.assertEqual(cid(ar.circuit(i)), i)
            self.assertLessEqual(len(ar.circ), 2)

    def test_value_gain(self):
        """H5: credit only for A / AD / GD reach or fewer gates inside the cap box; the legacy rule is kept as a mode"""
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d); ar._front = [(32, 5, 104, 29), (28, 5, 127, 22), (35, 3, 140, 25)]
            self.assertEqual(ar.gain((27, 5, 150, 30)), 8.0)        # fewer ANDs than anything at AD <= 5
            self.assertEqual(ar.gain((34, 3, 150, 25)), 8.0)        # fewer ANDs than anything at AD <= 3
            self.assertEqual(ar.gain((30, 4, 140, 25)), 8.0)        # AD <= 4 existed (35/3): its AND count drops to 30
            self.assertEqual(ar.gain((60, 2, 200, 12)), 4.0)        # nothing at AD <= 2 before: a new AND depth
            self.assertEqual(ar.gain((28, 5, 127, 21)), 1.0)        # only the gate depth is new
            self.assertEqual(ar.gain((32, 5, 103, 29)), 0.5)        # one gate fewer under the same caps
            self.assertEqual(ar.gain((32, 5, 100, 29)), 2.0)
            self.assertEqual(ar.gain((32, 5, 80, 29)), 3.0)         # the gate credit is capped below an AD reach
            self.assertEqual(ar.gain((32, 5, 110, 29)), 0.0)        # dominated
            self.assertEqual(ar.gain((32, 5, 104, 29)), 0.0)        # equal to a front point
            old = Archive(d, gain_mode='legacy'); old._front = ar._front + [(40, 5, 90, 29)]
            self.assertEqual(old.gain((32, 5, 103, 29)), 8.0)       # 2026-11-14: "lowers A", because a 40-AND circuit has fewer gates
            ar._front = list(old._front)
            self.assertEqual(ar.gain((32, 5, 103, 29)), 0.5)        # what it is: one gate fewer at A <= 32
            self.assertRaises(ValueError, Archive, d, True, 8, 'other')

    def test_pub_new_matches_aes_check(self):
        """pub_new is the aes_check 'new_point' rule on the pinned set: published circuits are not new"""
        with tempfile.TemporaryDirectory() as d:
            st, r, g = Archive(d).admit(load(P104))
            self.assertIs(r['pub_new'], False)
            self.assertIn((32, 5, 104, 30), C.published())


class TestCommon(unittest.TestCase):
    def test_code_version_covers_operators_and_package(self):
        """H9: the recorded code version changes with hub/ops, core.py, objective.py and the verifier"""
        names = {str(f.relative_to(C.PKG)) for f in C.source_files()}
        for n in ('hub/ops/f_ops.py', 'hub/ops/e_lib/skel_e.c', 'hub/scheduler.py', 'kernel/bfx.c', 'core.py', 'objective.py',
                  'independent/verify.py'):
            self.assertIn(n, names)
        v = C.code_version()
        self.assertRegex(v, r'^(\?|[0-9a-f]{7,}(-dirty)?)\+[0-9a-f]{10}$')


class TestScheduler(unittest.TestCase):
    def test_cpu_list_parsing_and_limits(self):
        """H4: one job per CPU; --cpus outside the process affinity is refused; control.json cannot leave the allow list"""
        self.assertEqual(SCH.parse_cpus('3,1,1,5-7'), [1, 3, 5, 6, 7])
        self.assertEqual(SCH.parse_cpus([2, 2, '0-1']), [0, 1, 2])
        self.assertRaises(ValueError, SCH.parse_cpus, 'a')
        mask = sorted(os.sched_getaffinity(0)); outside = [c for c in range(os.cpu_count()) if c not in mask]
        with tempfile.TemporaryDirectory() as d:
            s = sched(d)
            s.init_cpus()
            self.assertEqual(s.cpus, [mask[0]]); self.assertEqual(s.free, [mask[0]]); self.assertEqual(s.allow, {mask[0]})
            s.set_cpus([mask[0], 9999])                                   # not allowed: ignored and logged
            self.assertEqual(s.cpus, [mask[0]])
            ev = [json.loads(l) for l in Path(d, 'events.jsonl').read_text().splitlines()]
            self.assertTrue(any(e['ev'] == 'control-error' and '9999' in e['error'] for e in ev))
            self.assertEqual(json.loads(Path(d, 'cpus.json').read_text())['active'], [mask[0]])
            s.args.cpus = 'auto'; s.args.cpu_allow = None; s.init_cpus()
            self.assertEqual(s.cpus, mask)                                 # default: the launch pinning is the list
            if outside:
                s.args.cpus = str(outside[0])
                self.assertRaises(SystemExit, s.init_cpus)                 # stale list on the command line
                s.args.cpu_allow = str(outside[0]); s.init_cpus()          # explicit confirmation
                self.assertEqual(s.cpus, [outside[0]])
            s.args.cpus = '99999'; s.args.cpu_allow = '99999'
            self.assertRaises(SystemExit, s.init_cpus)                     # not online

    def test_control_cpus_is_the_exact_set(self):
        """H4: control.json "cpus" shrinks as well as grows; a dropped CPU is not reused after its job ends"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d)
            s.allow = {0, 1, 2, 3}; s.cpus = [0, 1, 2, 3]; s.free = [2, 3]
            s.running.extend([{'cpu': 0}, {'cpu': 1}])
            s.set_cpus([1, 2])
            self.assertEqual(s.cpus, [1, 2]); self.assertEqual(s.free, [2])
            s.set_cpus('0-2')                                              # 0 is still busy: not handed out twice
            self.assertEqual(s.cpus, [0, 1, 2]); self.assertEqual(s.free, [2])
            s.set_cpus([])                                                 # would leave nothing: ignored
            self.assertEqual(s.cpus, [0, 1, 2])
            self.assertIsNone(s.apply_control({'cpus': [0, 1]})); self.assertEqual(s.cpus, [0, 1]); self.assertEqual(s.free, [])

    def test_control_is_validated_as_a_whole(self):
        """H6: an invalid control.json changes nothing; scripts / generators register per scheduler"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d)
            before = (list(s.ops), dict(s.secs), s.args.eps)
            self.assertIn('unknown ops', s.apply_control({'ops': ['polish', 'nosuch'], 'seconds': {'polish': 5}, 'eps': 0.9}))
            self.assertIn('script missing', s.apply_control({'scripts': {'x': str(Path(d) / 'nope.py')}, 'eps': 0.9}))
            self.assertIsNotNone(s.apply_control({'eps': 7}))
            self.assertIsNotNone(s.apply_control({'seconds': {'polish': 'fast'}}))
            self.assertIsNotNone(s.apply_control({'generators': ['nosuch']}))
            self.assertEqual((s.ops, s.secs, s.args.eps), before)
            sp = Path(d) / 'op_new.py'; sp.write_text('')
            self.assertIsNone(s.apply_control({'scripts': {'new': str(sp)}, 'generators': ['new'], 'ops': ['polish', 'new'],
                                               'near_gap': 5, 'tuple_caps': {'polish': 1}, 'ad3_share': 0.5}))
            self.assertEqual(s.ops, ['polish', 'new']); self.assertEqual(s.secs['new'], 60.0); self.assertIn('new', s.generators)
            self.assertEqual((s.args.near_gap, s.tuple_caps, s.ad3_share), (5, {'polish': 1}, 0.5))
            self.assertNotIn('new', SCH.SCRIPTS); self.assertNotIn('new', SCH.GENERATORS)
            # a file read while half written is retried; the scheduler loop never dies in control()
            cf = Path(d) / 'control.json'; cf.write_text('{"eps": 0.')
            s.control(); self.assertIsNone(s.ctl_mtime)
            cf.write_text('{"eps": 0.5, "ingest": ["%s/missing/*.bfx"]}' % d); os.utime(cf, (1, 1))
            s.control(); self.assertEqual(s.args.eps, 0.5)

    def test_run_ids_unique_and_one_scheduler_per_campaign(self):
        """H3: run numbers continue after the highest used (also by jobs without a run file), carry the campaign uid, and
        a second scheduler on the same directory is refused"""
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'runs').mkdir(); Path(d, 'jobs').mkdir()
            for n in (1, 2, 3): Path(d, 'runs', 'r%05d-join.json' % n).write_text('{}')
            Path(d, 'jobs', 'r00009-polish.log').write_text('')          # killed job: no run file
            Path(d, 'jobs', 'other-abc123.r00012-trb').mkdir()
            s = sched(d)
            self.assertEqual(s.nrun, 12)
            self.assertRaises(SystemExit, sched, d)
            uid = json.loads(Path(d, 'campaign.json').read_text())['uid']
            self.assertEqual(s.uid, uid)
            s._lockf.close()
            s2 = sched(d); self.assertEqual(s2.uid, uid)                  # the uid belongs to the directory
            s2._lockf.close()
        with tempfile.TemporaryDirectory() as d2:
            s3 = sched(d2); self.assertNotEqual(s3.uid, uid); s3._lockf.close()

    def test_finish_lineage_and_failures(self):
        """H3, H14: every admitted circuit carries operator, parents, run id, seed, settings, script hash and code
        versions; failed jobs get a run record, their candidates are checked, the operator is suspended after repeats"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d); s.seed([str(P104)])
            tid = next(iter(s.ar.rec)); c107 = load(P107); c117 = load(P117)
            seedrec = s.ar.rec[tid]['operator_settings']
            self.assertEqual(seedrec['file_sha'], C.file_sha(P104))
            # 1. a normal job
            j = fake_job(s, 'trb', tid, [c107]); s.finish(j)
            r = s.ar.rec[cid(c107)]
            self.assertEqual((r['operator'], r['parents'], r['seed'], r['run_id'], r['code_version']), ('trb', [tid], 5, j['run_id'], 'opversion'))
            self.assertTrue(r['run_id'].startswith(s.uid + '.r'))
            for k in ('script', 'script_sha', 'scheduler_version', 'seconds', 'objective'): self.assertIn(k, r['operator_settings'])
            self.assertNotIn('job_status', r['operator_settings'])
            run = json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())
            self.assertEqual((run['status'], run['admitted'], run['campaign']), ('ok', 1, s.uid))
            st = json.loads(Path(d, 'stats.jsonl').read_text().splitlines()[-1])
            self.assertEqual((st['target'], st['tm'], st['status']), (tid, [32, 5, 104, 30], 'ok'))
            # 2. candidate files that record.json does not list, or that are not circuits, are not admitted
            j = fake_job(s, 'trb', tid, [c117, 'n 8\nm 8\ng garbage\n'], cand_ids=['000000000000']); s.finish(j)
            run = json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())
            self.assertEqual(len(run['outcome']), 2)
            self.assertTrue(all(o['status'].startswith('rejected') for o in run['outcome']), run['outcome'])
            self.assertNotIn(cid(c117), s.ar.rec)
            # 3. the operator died (no record.json): run record with status failed; the verified candidate is kept, flagged
            j = fake_job(s, 'trb', tid, [c117], rc=1, record=False); s.finish(j)
            r = s.ar.rec[cid(c117)]
            self.assertEqual(r['operator_settings']['job_status'], 'failed')
            self.assertEqual(r['code_version'], s.version); self.assertEqual(r['operator_settings']['seconds'], 3.0)
            run = json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())
            self.assertEqual((run['status'], run['returncode'], run['record_error']), ('failed', 1, 'no record.json'))
            # 4. repeated failures suspend the operator, a success resets the count
            for n in range(SCH.FAIL_LIMIT - 2): s.finish(fake_job(s, 'trb', tid, rc=1, error='boom'))
            self.assertIn('trb', s.active_ops())
            s.finish(fake_job(s, 'trb', tid, rc=1, error='boom'))
            self.assertNotIn('trb', s.active_ops())
            s.suspended['trb'] = 0; self.assertIn('trb', s.active_ops())
            self.assertEqual(len(list(Path(d, 'runs').glob('*.json'))), s.nrun)   # every job has its run file
            # 5. unreadable record.json
            j = fake_job(s, 'join', tid); (j['jd'] / 'record.json').write_text('{"operator": '); s.finish(j)
            self.assertEqual(json.loads(Path(d, 'runs', j['run_id'] + '.json').read_text())['status'], 'failed')
            s._lockf.close()
            # 6. state survives a restart: attempts per tuple, bandit history
            s2 = sched(d)
            self.assertEqual(s2.attempts[('trb', (32, 5, 104, 30))], s.nrun - 1)
            self.assertEqual(len(s2.hist['trb']), s.nrun - 1)
            self.assertNotEqual(s2.rng.random(), sched_rng_first(d, s2.args.seed, 0))

    def test_targets_by_tuple_with_caps_and_fresh_first(self):
        """H7: attempts are counted per (A, AD, G, GD) tuple, capped per operator, and new tuples get their first
        polish / pull at once"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull,trb', '--tuple-caps', 'polish=2,pull=3'); s.seed([str(P104), str(P107), str(P117)])
            ids = {metrics(s.ar.circuit(i)): i for i in s.ar.rec}
            self.assertEqual(s.target_key(ids[(32, 5, 104, 30)]), (32, 5, 104, 30))
            got = []
            for n in range(6):                              # 3 tuples x (polish, pull): all first jobs before anything else
                op, tid = s.fresh_target(set()); got.append((op, s.target_key(tid)))
                s.attempts[(op, s.target_key(tid))] = 1
            self.assertEqual(len(set(got)), 6); self.assertIsNone(s.fresh_target(set()))
            self.assertEqual({g[0] for g in got}, {'polish', 'pull'})
            # busy tuples are skipped
            s.attempts.clear(); self.assertNotIn((32, 5, 104, 30), [s.target_key(s.fresh_target({(32, 5, 104, 30)})[1]) for n in range(3)])
            # caps: a tuple with 2 polish jobs is not chosen for polish again, the others are
            s.attempts[('polish', (32, 5, 104, 30))] = 2; s.attempts[('polish', (32, 5, 107, 22))] = 1
            seen = {s.target_key(s.choose_target('polish', set())) for n in range(20)}
            self.assertEqual(seen, {(32, 4, 117, 19)})        # fewest attempts first, never the capped one
            for k in ids: s.attempts[('polish', k)] = 2
            self.assertIsNone(s.choose_target('polish', set()))
            self.assertIsNotNone(s.choose_target('polish', set(), ignore_caps=True))
            self.assertIsNotNone(s.choose_target('trb', set()))             # no cap set for trb
            s._lockf.close()
        with tempfile.TemporaryDirectory() as d:        # old mode
            s = sched(d, '--target-mode', 'id'); s.seed([str(P104)])
            tid = next(iter(s.ar.rec)); self.assertEqual(s.target_key(tid), tid); self.assertIsNone(s.fresh_target(set()))
            s._lockf.close()

    def test_cap_renewal_by_front_change_in_the_cap_box(self):
        """H7b: --cap-renew box gives a capped tuple its jobs again when a new front tuple appears under its caps"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,pull', '--tuple-caps', 'polish=2', '--cap-renew', 'box', '--cap-renew-max', '1')
            s.seed([str(P104), str(P107), str(P117)])
            t104, t107, t117 = (32, 5, 104, 30), (32, 5, 107, 22), (32, 4, 117, 19)
            for t in (t104, t107, t117): s.attempts[('polish', t)] = 2
            self.assertIsNone(s.choose_target('polish', set()))
            # 32/4/117/19 is inside the boxes of 104@30 and 107@22 (A, AD, GD all <=), not the other way round
            self.assertEqual(s.renew_caps(t117), 2)
            self.assertEqual({s.target_key(s.choose_target('polish', set())) for n in range(20)}, {t104, t107})
            self.assertTrue(s.capped('polish', t117))
            s.attempts[('polish', t104)] = 4; s.attempts[('polish', t107)] = 4
            self.assertEqual(s.renew_caps(t117), 0)                         # --cap-renew-max 1: no second renewal
            self.assertIsNone(s.choose_target('polish', set()))
            self.assertEqual(s.renew_caps((32, 5, 120, 31)), 0)             # outside every box
        with tempfile.TemporaryDirectory() as d:                            # default: never
            s = sched(d); s.seed([str(P104), str(P117)]); s.attempts[('polish', (32, 5, 104, 30))] = 2
            self.assertEqual(s.renew_caps((32, 4, 117, 19)), 0); self.assertTrue(s.capped('polish', (32, 5, 104, 30)))

    def test_subclass_with_its_own_parser_and_job_dict(self):
        """X2 compatibility: a subclass may pass an argparse namespace without the review 5 options, and a job started
        without its own process group is still killed"""
        import argparse
        with tempfile.TemporaryDirectory() as d:
            ns = argparse.Namespace(dir=d, cpus=str(min(os.sched_getaffinity(0))), hours=0.1, seed_list=None, ops='polish,pull',
                                    seconds=None, eps=0.25, seed=1, seed_only=False, near=0.0, near_gap=3, nursery=0.0)
            s = SCH.Scheduler(ns); OPEN.append(s._lockf)
            self.assertEqual((s.args.gain, s.args.target_mode, s.args.join_mode, s.args.cap_renew), ('value', 'tuple', 'incremental', 'never'))
            self.assertEqual(s.tuple_caps, {'polish': 2, 'pull': 3})
        p = subprocess.Popen(['sleep', '60'])                               # same process group as this test
        job = {'p': p}; SCH.Scheduler.kill(job, 'timeout')
        self.assertEqual(p.wait(timeout=10), -9)

    def test_one_join_pass_per_target_and_archive_state(self):
        """H8: join is offered a target only when the archive has members it has not been joined with; the pool is every
        cell member (front or not); the legacy pool is kept behind a flag"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'join', '--tuple-caps', ''); s.seed([str(P104), str(P107), str(P117)])
            by = {metrics(s.ar.circuit(i)): i for i in s.ar.rec}
            x = by[(32, 5, 104, 30)]; rng = random.Random(1)
            # non-front cell member: a bloated copy of 107 in a new, dominated cell
            c = load(P107); worse = core.Circuit(c.n, c.m, list(c.gates) + [(3, c.outputs[0], c.outputs[0])], list(c.outputs))
            g = list(worse.gates); o = list(worse.outputs); g.append((3, len(g) + 7, len(g) + 7)); o[0] = len(g) + 7
            worse = core.Circuit(c.n, c.m, g, o)
            st, r, gn = s.ar.admit(worse, force_keep=True); self.assertEqual(st, 'admitted'); s.last_admit = r['t_admit']
            self.assertNotIn(r['id'], s.ar.front_ids())
            self.assertIn(r['id'], HO.join_partners(s.ar, x, 0.0, rng))
            self.assertNotIn(r['id'], HO.join_partners(s.ar, x, None, rng, 2))       # legacy: front first, cut at the limit
            t = [s.ar.rec[i]['t_admit'] for i in HO.join_partners(s.ar, x, 0.0, rng)]
            self.assertEqual(t, sorted(t)); self.assertEqual(len(t), 3)
            self.assertEqual(HO.join_partners(s.ar, x, s.ar.rec[by[(32, 4, 117, 19)]]['t_admit'], rng), [r['id']])
            # op_join reports how far it got; the scheduler stores it and stops offering the target
            args = types.SimpleNamespace(inp=x, since=0.0, partners=300, seconds=30.0, max_cands=40)
            cands, info = HO.op_join(s.ar, args, rng, None)
            self.assertEqual(info['partners_done'], 3); self.assertEqual(info['joined_through'], s.last_admit)
            self.assertEqual(len(info['joins']), len(cands))
            args.seconds = -1.0                                             # out of time before the first partner
            self.assertEqual(HO.op_join(s.ar, args, rng, None)[1]['joined_through'], 0.0)
            j = fake_job(s, 'join', x, info={'joined_through': info['joined_through'], 'joins': []}); s.finish(j)
            self.assertEqual(s.join_mark[x], s.last_admit)
            for n in range(10): self.assertNotEqual(s.choose_target('join', set()), x)
            for i in list(s.ar.rec): s.join_mark[i] = s.last_admit
            self.assertIsNone(s.choose_target('join', set()))               # nothing new anywhere: no join job at all
            s.last_admit += 1.0                                             # an admission reopens every target
            self.assertIsNotNone(s.choose_target('join', set()))
            s._lockf.close()
            s2 = sched(d, '--ops', 'join')
            self.assertIn(x, s2.join_mark)                                   # marks survive a restart (stats.jsonl)
            s2.args.join_mode = 'legacy'; s2.last_admit = 0.0
            self.assertIsNotNone(s2.choose_target('join', set()))

    def test_stuck_job_is_killed_with_its_children(self):
        """H15: a job past its limit is killed as a process group (operator and kernel child)"""
        p = subprocess.Popen(['sh', '-c', 'sleep 60 & wait'], start_new_session=True)
        job = {'p': p}
        time.sleep(0.2); SCH.Scheduler.kill(job, 'timeout')
        self.assertEqual(p.wait(timeout=10), -9); self.assertEqual(job['killed'], 'timeout')
        self.assertNotEqual(subprocess.run(['pgrep', '-g', str(p.pid)], capture_output=True).returncode, 0)

    def test_launch_falls_back_cuts_to_the_end_and_never_reuses_a_job_dir(self):
        """H15, H20, H3: an operator without a target does not idle the CPU; a job is cut to the time left; job
        directories are new"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'join,trb', '--eps', '0'); s.seed([str(P104), str(P107)])
            for i in s.ar.rec: s.join_mark[i] = s.last_admit           # join has nothing new to do
            s.hist['join'] = [(1.0, 100.0)]                             # ... although the bandit prefers it
            started = []
            real = SCH.subprocess.Popen
            SCH.subprocess.Popen = lambda cmd, **kw: (started.append((cmd, kw)) or types.SimpleNamespace(pid=0, returncode=None))
            try:
                s.end = time.time() + 12.0
                j = s.launch(3, set())
                self.assertEqual((j['op'], j['why']), ('trb', 'exploit-fallback'))
                cmd = j['cmd']; self.assertEqual(cmd[:3], ['taskset', '-c', '3'])
                self.assertLessEqual(float(cmd[cmd.index('--seconds') + 1]), 12.0)       # trb default is 30
                self.assertTrue(started[0][1]['start_new_session'])
                (s.dir / 'jobs' / ('%s.r%05d-trb' % (s.uid, s.nrun + 1))).mkdir()        # left over by something else
                j2 = s.launch(3, set()); self.assertEqual(s.nrun, 3); self.assertNotEqual(j2['jd'], j['jd'])
                self.assertFalse(j2['jd'].exists())
                s.end = time.time() + 2.0
                self.assertIsNone(s.launch(3, set()))                   # too little time left for any job
                s.end = time.time() + 100.0; s.suspended = {'join': time.time() + 99, 'trb': time.time() + 99}
                self.assertIsNone(s.launch(3, set()))                   # every operator suspended
                j['lf'].close(); j2['lf'].close()
            finally:
                SCH.subprocess.Popen = real

    def test_sigterm_ends_the_campaign_cleanly(self):
        """H15: a stop (systemctl stop sends SIGTERM) kills the jobs, writes their run files, the front and the end event"""
        import signal
        with tempfile.TemporaryDirectory() as d:
            op = Path(d) / 'op_sleep.py'
            op.write_text('import time\ntime.sleep(300)\n')
            Path(d, 'control.json').write_text(json.dumps({'scripts': {'sleeper': str(op)}, 'ops': ['sleeper'], 'seconds': {'sleeper': 200}}))
            lst = Path(d) / 'seed.list'; lst.write_text('%s\n' % P104)
            code = ('import sys; sys.path.insert(0, %r); from boolflux.hub import scheduler as S; S.kernel_bin = lambda d: None; '
                    'S.main(sys.argv[1:])' % str(Path(__file__).resolve().parents[3]))
            cpu = str(min(os.sched_getaffinity(0)))
            p = subprocess.Popen([sys.executable, '-c', code, '--dir', d, '--cpus', cpu, '--hours', '0.2', '--seed-list', str(lst)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            t0 = time.time()
            while time.time() - t0 < 60 and not list(Path(d, 'jobs').glob('*.log')): time.sleep(0.2)
            self.assertTrue(list(Path(d, 'jobs').glob('*.log')), 'no job started')
            p.send_signal(signal.SIGTERM)
            out, err = p.communicate(timeout=60)
            self.assertEqual(p.returncode, 0, err[-2000:])
            ev = [json.loads(l) for l in Path(d, 'events.jsonl').read_text().splitlines()]
            self.assertEqual((ev[-1]['ev'], ev[-1]['reason']), ('end', 'SIGTERM'))
            runs = [json.loads(f.read_text()) for f in Path(d, 'runs').glob('*.json')]
            self.assertEqual([r['status'] for r in runs], ['stopped'])
            self.assertEqual(runs[0]['operator'], 'sleeper'); self.assertEqual(runs[0]['script_sha'], C.file_sha(op))
            self.assertTrue(Path(d, 'front.json').exists())

    def test_ingest_never_fatal_and_keeps_the_sidecar(self):
        """H16: ingest records the file hash and its JSON sidecar; unreadable files are logged, not fatal"""
        with tempfile.TemporaryDirectory() as d:
            s = sched(d)
            f = Path(d) / 'found' / 'a.bfx'; f.parent.mkdir(); f.write_text(core.to_kernel(load(P104)))
            f.with_suffix('.json').write_text(json.dumps({'how': 'test', 'seed': 3}))
            (f.parent / 'b.bfx').write_text('not a circuit')
            wrong = load(P104); g = list(wrong.gates); g[-1] = (9 if g[-1][0] == 6 else 6,) + tuple(g[-1][1:])
            (f.parent / 'c.bfx').write_text(core.to_kernel(core.Circuit(8, 8, g, list(wrong.outputs))))
            s.ingest_globs = [str(f.parent / '*.bfx')]; s.ingest()
            self.assertEqual(len(s.ar.rec), 1)
            r = next(iter(s.ar.rec.values()))
            self.assertEqual(r['operator_settings']['sidecar'], {'how': 'test', 'seed': 3})
            self.assertEqual(r['operator_settings']['file_sha'], C.file_sha(f))
            ev = [json.loads(l)['ev'] for l in Path(d, 'events.jsonl').read_text().splitlines()]
            self.assertIn('ingest-error', ev); self.assertIn('ingest-reject', ev)


class TestLineage(unittest.TestCase):
    def test_lineage_audit(self):
        """H3: hub/lineage.py finds every record whose origin cannot be reconstructed"""
        from boolflux.hub import lineage as LN
        with tempfile.TemporaryDirectory() as d:
            s = sched(d); s.seed([str(P104)]); tid = next(iter(s.ar.rec))
            j = fake_job(s, "trb", tid, [load(P107)]); s.finish(j)
            rows, gaps = LN.audit(d)
            self.assertEqual(len(rows), 2); self.assertEqual(gaps, {})
            self.assertEqual(LN.main([d]), 0)
            new = cid(load(P107))
            rows, gaps = LN.audit(d, ids=[new]); self.assertEqual(set(rows), {new, tid})     # ancestors are followed
            run = Path(d, "runs", j["run_id"] + ".json"); keep = run.read_text()
            other = json.loads(keep); other["outcome"] = []                   # a run of the same name that did not make it
            run.write_text(json.dumps(other))
            self.assertIn("run", LN.audit(d)[1][new][0])
            run.unlink()
            with tempfile.TemporaryDirectory() as d2:                       # the run file lives in another campaign
                Path(d2, "runs").mkdir(); Path(d2, "runs", run.name).write_text(keep)
                self.assertEqual(LN.audit(d, also=[d2])[1], {})
            rf = Path(d, "archive", new + ".json"); r = json.loads(rf.read_text())
            r["seed"] = None; r["parents"] = ["ffffffffffff"]; rf.write_text(json.dumps(r)); Path(d, "archive", "index.jsonl").unlink()
            g = LN.audit(d)[1][new]
            self.assertIn("seed", g); self.assertTrue(any(x.startswith("parent ffffffffffff") for x in g))
            Path(d, "archive", tid + ".bfx").write_text(core.to_kernel(load(P117)))
            self.assertTrue(any(x.startswith("file") for x in LN.audit(d)[1][tid]))
            self.assertEqual(LN.main([d]), 1)


def sched_rng_first(d, seed, nrun):
    return random.Random('%s/%d' % (seed, nrun)).random()


class TestOperators(unittest.TestCase):
    def test_cli_contract(self):
        """H14, H17: bad caps / objective are command-line errors; an operator failure writes record.json with the
        error and exits 1; a job directory is used once; the kernel settings come from boolflux.objective"""
        self.assertEqual(HO.parse_caps('-,4,14'), {'A': None, 'AD': 4, 'GD': 14})
        for bad in ('1,2', 'a,b,c', '0,1,2', '1,2,3,4'):
            self.assertRaises(SystemExit, HO.parse_caps, bad)
        with tempfile.TemporaryDirectory() as d:
            ar = Archive(d); st, r, g = ar.admit(load(P104))
            out = Path(d) / 'job1'
            with open(os.devnull, 'w') as dn:
                err, sys.stderr = sys.stderr, dn
                try:
                    self.assertRaises(SystemExit, HO.main, 'trb', ['--archive', d, '--in', r['id'], '--out', str(out), '--objective', 'a,zz'])
                    rc = HO.main('trb', ['--archive', d, '--in', 'nosuchid0000', '--out', str(out), '--seconds', '1'])
                finally:
                    sys.stderr = err
            self.assertEqual(rc, 1)
            rec = json.loads((out / 'record.json').read_text())
            self.assertIn('not in the archive', rec['error']); self.assertEqual(rec['cand_ids'], [])
            (out / 'cand-000.bfx').write_text('x')
            self.assertRaises(SystemExit, HO.main, 'trb', ['--archive', d, '--in', r['id'], '--out', str(out)])
            # kernel config: same weights / lex as the package (objective.weights), caps passed through
            seen = {}

            def fake_run(cmd, **kw):
                seen['cfg'] = dict(l.split(None, 1) for l in Path(cmd[1]).read_text().splitlines())
                return types.SimpleNamespace(returncode=seen.get('rc', 0))
            real, HO.subprocess.run = HO.subprocess.run, fake_run
            kb, HO.kernel_bin = HO.kernel_bin, lambda a: Path('bfx-test')
            try:
                jd = Path(d) / 'job2'; jd.mkdir()
                cands, info = HO._kernel(load(P104), {'A': 32, 'AD': None, 'GD': 20}, 'a,ad,cost,gd', 1, 5, jd, d)
                from boolflux import objective
                for k, v in objective.weights('a,ad,cost,gd').items(): self.assertEqual(seen['cfg'][k], str(v))
                self.assertEqual((seen['cfg']['cap.a'], seen['cfg']['cap.gd']), ('32', '20')); self.assertNotIn('cap.ad', seen['cfg'])
                self.assertEqual({k: seen['cfg'][k] for k in ('cost.8', 'cost.6', 'cost.9', 'cost.3')}, {k: '1' for k in ('cost.8', 'cost.6', 'cost.9', 'cost.3')})
                self.assertRaises(SystemExit, HO._kernel, load(P104), {}, 'a,nokey', 1, 5, jd, d)
                seen['rc'] = 2                                              # the kernel died: a failure, not "no candidate"
                self.assertRaises(HO.OpError, HO._kernel, load(P104), {}, 'a,cost', 1, 5, jd, d)
            finally:
                HO.subprocess.run = real; HO.kernel_bin = kb

    def test_pull_caps_stay_positive_and_osc_keeps_the_and_cap(self):
        """H8b: osc runs under the input's A cap (it used to run without one)"""
        spec = importlib.util.spec_from_file_location('f_ops_r5', HUB / 'ops' / 'f_ops.py')
        F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
        c = load(P104); calls = []
        ar = types.SimpleNamespace(circuit=lambda i: c)
        real = HO._kernel
        HO._kernel = lambda c_, caps, *a: (calls.append(dict(caps)) or ([c_], {}))
        try:
            with tempfile.TemporaryDirectory() as d:
                args = types.SimpleNamespace(inp='x', caps=None, objective='a,ad,cost,gd', seed=1, seconds=3, archive=d)
                cands, info = F.op_osc(ar, args, random.Random(1), Path(d))
                self.assertEqual(calls, [{'A': 32, 'AD': 5, 'GD': 31}, {'A': 32, 'AD': 5, 'GD': 30}, {'A': 32, 'AD': 5, 'GD': 30}])
                del calls[:]; args.caps = {'A': None, 'AD': 5, 'GD': 30}      # the old behaviour on request
                F.op_osc(ar, args, random.Random(1), Path(d))
                self.assertIsNone(calls[0]['A'])
                del calls[:]; args.caps = None
                for seed in range(30): HO.op_pull(ar, args, random.Random(seed), Path(d))
                self.assertTrue(all(v is None or v >= 1 for k in calls for v in k.values()))
        finally:
            HO._kernel = real

    def test_linres_scans_the_bank_once_per_layer(self):
        """H18: the function-bank scan of linres is cached per layer"""
        spec = importlib.util.spec_from_file_location('op_linres_r5', HUB / 'ops' / 'op_linres.py')
        L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
        c = load(P104); tabs = c.tables()
        bank = ['%064x' % (tabs[10] ^ tabs[11])]

        class Bank(list):
            scans = 0

            def __iter__(self):
                Bank.scans += 1
                return super().__iter__()
        b = Bank(bank); cache = {}; rng = random.Random(2)
        out = [L.rebuild_layer(c, 0, b, rng, cache) for n in range(4)]
        self.assertEqual(Bank.scans, 1); self.assertIn(0, cache)
        for nc in out:
            if nc is not None: self.assertTrue(verify(nc)[0])


LONG = Path.home() / 'xs-campaigns' / '2026-11-14-hub' / 'long' / 'archive'


def with_duplicate_and(c):
    """c with its first AND written twice, the copy used by the first later reader of the original
    (same function; A and G one higher), plus one dead XOR at the end"""
    n = c.n; g = list(c.gates)
    j = next(k for k, (op, a, b) in enumerate(g) if op == 8); s = n + j
    sh = lambda x: x + 1 if x > s else x
    new = g[:j + 1] + [g[j]] + [(op, sh(a), sh(b)) for op, a, b in g[j + 1:]]
    outs = [sh(o) for o in c.outputs]
    for k in range(j + 2, len(new)):
        op, a, b = new[k]
        if s in (a, b):
            new[k] = (op, s + 1 if a == s else a, s + 1 if b == s else b); break
    new.append((6, 0, 1))
    return core.Circuit(c.n, c.m, new, outs, c.name)


class TestCleanup(unittest.TestCase):
    def test_clean_merges_identical_gates_and_drops_dead_ones(self):
        """C (review 5): structural-hash cleanup keeps the function, removes the duplicate AND and the dead gate"""
        c = load(P104); d = with_duplicate_and(c)
        m, md = metrics(c), metrics(d)
        self.assertEqual((md[0], md[2]), (m[0] + 1, m[2] + 2))
        self.assertTrue(verify(d)[0])
        cc = C.clean(d)
        self.assertEqual(metrics(cc), m)
        self.assertTrue(verify(cc)[0])
        self.assertEqual(structure_key(cc), structure_key(C.clean(c)))
        self.assertIs(C.clean(cc), cc)                                     # idempotent, and c itself when clean
        self.assertIs(C.clean(c), c)
        # merges propagate: a gate whose operands are two copies of one gate equals a gate on the original
        x = core.Circuit(2, 2, [(8, 0, 1), (8, 1, 0), (6, 0, 2), (6, 3, 0)], [4, 5])
        y = C.clean(x)
        self.assertEqual(len(y.gates), 2); self.assertEqual(y.outputs[0], y.outputs[1])

    def test_candidates_are_cleaned_before_admission(self):
        """C: the archive stores, measures and places the cleaned circuit and records where it came from"""
        c = load(P104); d = with_duplicate_and(c)
        with tempfile.TemporaryDirectory() as tmp:
            ar = Archive(tmp)
            st, r, g = ar.admit(d)
            self.assertEqual(st, 'admitted')
            self.assertEqual((r['A'], r['AD'], r['G'], r['GD']), metrics(c))
            self.assertEqual(r['operator_settings']['cleaned_from'], cid(d))
            self.assertEqual(r['operator_settings']['raw_metrics'], list(metrics(d)))
            self.assertEqual(metrics(ar.circuit(r['id'])), metrics(c))
            self.assertEqual(metrics(core.from_kernel(Path(tmp, 'archive', r['id'] + '.bfx').read_text())), metrics(c))
            self.assertIn(ar.admit(c)[0], ('duplicate', 'duplicate-structure'))
            self.assertEqual(Archive(tmp).rec[r['id']]['A'], metrics(c)[0])
            st, r2, _ = ar.admit(load(P107))                               # a clean circuit: no cleanup fields
            self.assertNotIn('cleaned_from', r2['operator_settings'])

    def test_finish_admits_the_cleaned_candidate(self):
        """C: an operator's candidate with a duplicate AND is admitted with the lower A; the run file shows both"""
        with tempfile.TemporaryDirectory() as tmp:
            s = sched(tmp); s.seed([str(P104)]); tid = next(iter(s.ar.rec))
            c107 = load(P107); d = with_duplicate_and(c107)
            j = fake_job(s, 'trb', tid, [d]); s.finish(j)
            run = json.loads(Path(tmp, 'runs', j['run_id'] + '.json').read_text())
            o = run['outcome'][0]
            self.assertEqual(o['status'], 'admitted')
            self.assertEqual(o['metrics'], list(metrics(d))); self.assertEqual(o['cleaned_metrics'], list(metrics(c107)))
            r = s.ar.rec[o['id']]
            self.assertEqual((r['A'], r['G']), metrics(c107)[0:3:2])
            self.assertEqual((r['operator'], r['parents']), ('trb', [tid]))
            ev = [json.loads(l) for l in Path(tmp, 'events.jsonl').read_text().splitlines()]
            self.assertEqual([e['m'] for e in ev if e['ev'] == 'admit'], [list(metrics(c107))])

    def test_legacy_records_are_cleaned_once_with_lineage(self):
        """C: on the first start, old records whose cleaned metrics differ are logged and their cleaned versions
        admitted as new records (operator clean, parent = old record); no file is rewritten; done once"""
        c = load(P104); d = with_duplicate_and(c)
        with tempfile.TemporaryDirectory() as tmp:
            ar = Archive(tmp)
            st, old, _ = ar.admit(d, operator='trb', clean_first=False, force_keep=True)    # as the old code did
            self.assertEqual(st, 'admitted'); self.assertEqual(old['A'], metrics(d)[0])
            ar.admit(load(P107), operator='trb', clean_first=False)                         # nothing to clean
            files = {f.name: f.read_bytes() for i in ar.rec for f in Path(tmp, 'archive').glob(i + '.*')}   # the records (cells.json is a cache)
            s = sched(tmp)
            ev = [json.loads(l) for l in Path(tmp, 'events.jsonl').read_text().splitlines()]
            lc = [e for e in ev if e['ev'] == 'legacy-clean']
            self.assertEqual(len(lc), 1)
            self.assertEqual((lc[0]['id'], lc[0]['recorded'], lc[0]['cleaned'], lc[0]['status']),
                             (old['id'], list(metrics(d)), list(metrics(c)), 'admitted'))
            self.assertTrue(any(e['ev'] == 'legacy-cleaned' and e['records'] == 1 for e in ev))
            new = s.ar.rec[lc[0]['new_id']]
            self.assertEqual((new['operator'], new['parents'], new['A']), ('clean', [old['id']], metrics(c)[0]))
            self.assertEqual(new['operator_settings']['raw_metrics'], list(metrics(d)))
            self.assertEqual(new['code_version'], s.version)
            for name, b in files.items():
                self.assertEqual(Path(tmp, 'archive', name).read_bytes(), b, name)      # old files untouched
            self.assertIn(old['id'], s.ar.rec)                                           # and still a record
            s._lockf.close()
            n0 = len(s.ar.rec)
            s2 = sched(tmp)                                                              # second start: nothing again
            ev = [json.loads(l) for l in Path(tmp, 'events.jsonl').read_text().splitlines()]
            self.assertEqual(len([e for e in ev if e['ev'] == 'legacy-clean']), 1)
            self.assertEqual(len(s2.ar.rec), n0)

    @unittest.skipUnless((LONG / '1b706c348e80.bfx').exists(), 'the 2026-11-14 hub archive is not on this machine')
    def test_the_reported_example_of_the_long_campaign(self):
        """C, on the record named in the finding: recorded 30/4/144/17, cleaned 29/4/143/17"""
        r = json.loads((LONG / '1b706c348e80.json').read_text())
        self.assertEqual((r['A'], r['AD'], r['G'], r['GD']), (30, 4, 144, 17))
        cc = C.clean(core.from_kernel((LONG / '1b706c348e80.bfx').read_text()))
        self.assertEqual(metrics(cc), (29, 4, 143, 17))
        self.assertTrue(verify(cc)[0])


class TestKernelBin(unittest.TestCase):
    def test_kernel_bin_unique_temporary_and_atomic_rename(self):
        """C (review 5): every builder used ARCHIVE/bin/bfx-<hash>.tmp; now each has its own name and renames"""
        import threading
        from unittest import mock
        seen = []; lock = threading.Lock()

        def fake_gcc(cmd, check=True):
            out = cmd[cmd.index('-o') + 1]
            with lock: seen.append(out)
            Path(out).write_text('partial'); time.sleep(0.2); Path(out).write_text('complete')
            return subprocess.CompletedProcess(cmd, 0)
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(HO.subprocess, 'run', fake_gcc):
                th = [threading.Thread(target=HO.kernel_bin, args=(tmp,)) for _ in range(4)]
                for x in th: x.start()
                for x in th: x.join()
                b = HO.kernel_bin(tmp)                                 # built: no further compile
            self.assertEqual(len(seen), len(set(seen)))
            self.assertTrue(b.name.startswith('bfx-'))
            self.assertNotIn(str(b) + '.tmp', seen)
            self.assertEqual(b.read_text(), 'complete')
            self.assertEqual([f.name for f in b.parent.iterdir()], [b.name])

            def failing(cmd, check=True):
                Path(cmd[cmd.index('-o') + 1]).write_text('partial'); raise subprocess.CalledProcessError(1, cmd)
            b.unlink()
            with mock.patch.object(HO.subprocess, 'run', failing):
                self.assertRaises(subprocess.CalledProcessError, HO.kernel_bin, tmp)
            self.assertEqual(list(b.parent.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
