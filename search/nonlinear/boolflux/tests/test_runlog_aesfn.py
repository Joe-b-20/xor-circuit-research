"""Run records (runlog.py), the fallbacks for GNU time and taskset, and the inverse S-box in the AES tools:

    python3 -m unittest search/nonlinear/boolflux/tests/test_runlog_aesfn.py   (from the repository root; ~2 min)

run.json / events.jsonl.gz of cli run and flow and of a method script; the git diff of a dirty tree
replays; measurement and pinning without GNU time and taskset (shutil.which patched); aes_check and
both verifiers on every NIST inverse S-box circuit; the conjugate maps of the inverse; a short
conjpull run on a NIST inverse circuit.
"""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))
sys.path.insert(0, str(PKG / 'independent'))

from boolflux import aesfn, core, runlog, workflow       # noqa: E402
import cli                                                # noqa: E402
import aes_check as AC                                    # noqa: E402

NIST = PKG.parent / 'seeds'
INV117 = NIST / 'aes-invsbox' / 'aes-invsbox-a32-ad4-g117-gd21-xx85-10.circ.txt'
FWD117 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'
CLI = [sys.executable, str(PKG / 'cli.py')]
RUN_KEYS = ('schema', 'kind', 'status', 'argv', 'cwd', 'command', 'git', 'sources_sha256', 'function', 'seeds',
            'config', 'starts', 'budget_s', 'kernels', 'host', 'tools', 'env', 't_start_utc', 't_end_utc', 'wall_s',
            'cpu_s', 'max_rss_kb', 'result')


def tmpdir(prefix='bft-rl-'):
    return Path(tempfile.mkdtemp(prefix=prefix))


@contextmanager
def without(*progs):
    """shutil.which finds none of `progs` (as on a machine without GNU time / taskset)"""
    real = shutil.which
    shutil.which = lambda cmd, *a, **k: None if cmd in progs else real(cmd, *a, **k)
    runlog.gnu_time.cache_clear(); runlog.taskset.cache_clear(); runlog._WARNED.clear()
    try:
        yield
    finally:
        shutil.which = real
        runlog.gnu_time.cache_clear(); runlog.taskset.cache_clear()


@contextmanager
def function(f):
    old = os.environ.get(aesfn.ENV)
    aesfn.use(f)
    try:
        yield
    finally:
        if old is None: os.environ.pop(aesfn.ENV, None)
        else: os.environ[aesfn.ENV] = old


def has(mod):
    try:
        __import__(mod); return True
    except ImportError:
        return False


class TestRunRecord(unittest.TestCase):
    def test_cli_run_record(self):
        """cli.py run writes run.json (every field) and an event per kernel improvement; summary.json points to it"""
        out = tmpdir()
        r = subprocess.run(CLI + ['run', '--target', 'maj3', '--model', 'xag', '--objective', 'a,cost', '--iters', '3000',
                                  '--seeds', '1-2', '--jobs', '1', '--out', str(out)], capture_output=True, text=True, cwd=str(REPO))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('boolflux: python', r.stderr)                    # the startup line
        rec = json.loads((out / 'run.json').read_text())
        for k in RUN_KEYS: self.assertIn(k, rec)
        self.assertEqual((rec['schema'], rec['kind'], rec['status']), ('boolflux-run/1', 'cli.run', 'ok'))
        self.assertEqual(rec['argv'][1:], [str(PKG / 'cli.py'), 'run', '--target', 'maj3', '--model', 'xag',
                                           '--objective', 'a,cost', '--iters', '3000', '--seeds', '1-2', '--jobs', '1',
                                           '--out', str(out)])
        self.assertEqual(rec['seeds']['kernel_seeds'], {'r0-s1': 1, 'r0-s2': 2})
        self.assertEqual({k['path'] for k in rec['kernels']}, {str((out / 'bin' / b).resolve()) for b in ('bfx', 'skel')})
        for k in rec['kernels']:
            self.assertEqual(k['sha256'], runlog.sha256_file(k['path']))
            self.assertTrue(k['compiler'].startswith('gcc'))
            self.assertIn('-O2', k['command'])
        self.assertEqual(rec['starts'][0]['label'], 'anf (built from the target table)')
        if rec['git']['commit'] and rec['git']['dirty']:
            self.assertTrue(Path(rec['git']['diff']).exists())
        ev = runlog.read_events(out / 'events.jsonl.gz')
        self.assertTrue(any(e['ev'] == 'improvement' and e['operator'] == 'gate kernel' and 'A' in e['metrics'] for e in ev))
        self.assertEqual(sorted(e['kernel_seed'] for e in ev if e['ev'] == 'kernel'), [1, 2])
        s = json.loads((out / 'summary.json').read_text())
        self.assertEqual(s['run_record'], 'run.json')

    def test_flow_without_gnu_time_and_taskset(self):
        """flow measures with Python and pins with os.sched_setaffinity when GNU time and taskset are missing
        (with them missing, workflow.timed used to fail on /usr/bin/time)"""
        bindir = cli.build_kernel().parent
        cpu = min(os.sched_getaffinity(0))
        with without('time', 'taskset'):
            self.assertIsNone(runlog.gnu_time()); self.assertIsNone(runlog.taskset())
            so, se, rss, wall, rc = runlog.measured([sys.executable, '-c', 'import os; print(sorted(os.sched_getaffinity(0)))'], cpu)
            self.assertEqual((rc, so.strip()), (0, '[%d]' % cpu))            # pinned without taskset
            self.assertGreater(rss, 1000)                                    # kB, from os.wait4
            so, se, rss, wall, rc = runlog.measured([sys.executable, '-c', 'import sys; sys.exit(3)'])
            self.assertEqual(rc, 3)
            d = tmpdir()
            log = runlog.RunLog(d, 'test.flow')
            run = {'target': 'present', 'model': 'bgc', 'objective': 'cost', 'caps': {}, 'start': 'anf', 'seconds': 2.0,
                   'seed': 3, 'config': 'full', 'round_s': 0.5, 'skel_set': {'iters': 0}}
            r = workflow.search(run, bindir, d / 'wd', cpu, log=log)
            self.assertTrue(r['rss'] and all(x and x > 0 for x in r['rss']))
            self.assertTrue(r['rss_source'].startswith('python-resource'))
            self.assertEqual(r['pinning'], 'sched_setaffinity')
            self.assertEqual(log.rec['tools']['gnu_time'], None)
            ev = runlog.read_events(log.events_path)
            ks = [e['kernel_seed'] for e in ev if e['ev'] == 'kernel']
            self.assertEqual(ks[:2], [workflow.kernel_seed(3, 0), workflow.kernel_seed(3, 0)])   # skel and gate of round 0
            self.assertTrue(any(e['ev'] == 'improvement' and e['operator'] == 'start' for e in ev))
            out = tmpdir()
            r = subprocess.run(CLI + ['flow', '--target', 'present', '--model', 'bgc', '--config', 'gate', '--seconds', '1',
                                      '--seeds', '1', '--cpus', str(cpu), '--out', str(out)], capture_output=True, text=True,
                               cwd=str(REPO), env=dict(os.environ, PATH=str(_nobin())))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            rec = json.loads((out / 'run.json').read_text())
            self.assertEqual((rec['tools']['gnu_time'], rec['tools']['taskset']), (None, None))
            self.assertEqual(rec['status'], 'ok'); self.assertEqual(rec['budget_s'], 1.0)
            self.assertIn('GNU time: missing', r.stderr)

    def test_git_diff_replays(self):
        """a dirty tree: run.json names the commit and a saved diff (tracked changes and untracked files under
        search/) that `git apply` turns the commit back into the tree that ran"""
        if not shutil.which('git'): self.skipTest('git missing')
        d = tmpdir(); g = lambda *a: subprocess.run(['git', '-C', str(d)] + list(a), capture_output=True, check=True)
        g('init', '-q'); g('config', 'user.email', 't@example.invalid'); g('config', 'user.name', 't')
        (d / 'search').mkdir(); (d / 'search' / 'a.py').write_text('x = 1\n'); g('add', '.'); g('commit', '-qm', 'c')
        info, diff = runlog.git_state.__wrapped__(str(d))
        self.assertEqual((info['dirty'], diff), (False, None))
        (d / 'search' / 'a.py').write_text('x = 2\n'); (d / 'search' / 'new.py').write_text('y = 3\n')
        info, diff = runlog.git_state.__wrapped__(str(d))
        self.assertTrue(info['dirty']); self.assertEqual(info['untracked'], ['search/new.py'])
        self.assertEqual(info['diff_sha256'], hashlib.sha256(diff).hexdigest())
        e = tmpdir(); subprocess.run(['git', 'clone', '-q', str(d), str(e)], check=True)
        p = subprocess.run(['git', '-C', str(e), 'apply'], input=diff, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual((e / 'search' / 'a.py').read_text(), 'x = 2\n'); self.assertEqual((e / 'search' / 'new.py').read_text(), 'y = 3\n')

    def test_events_survive_a_kill(self):
        """each event is a complete gzip member: what was written before a SIGKILL is readable"""
        d = tmpdir()
        code = ('import os, sys; sys.path.insert(0, %r); from boolflux import runlog\n'
                'l = runlog.RunLog(%r, "test.kill")\n'
                'for i in range(5): l.improvement({"G": 10 - i}, "x")\n'
                'os.kill(os.getpid(), 9)\n') % (str(PKG.parent), str(d))
        subprocess.run([sys.executable, '-c', code])
        self.assertEqual([e['metrics']['G'] for e in runlog.read_events(d / 'events.jsonl.gz')], [10, 9, 8, 7, 6])
        self.assertEqual(json.loads((d / 'run.json').read_text())['status'], 'running')


def _nobin():
    """a PATH folder with links to python3 and gcc only (no GNU time, no taskset)"""
    d = tmpdir(prefix='bft-nobin-')
    for prog in ('gcc', 'cc', 'as', 'ld', 'git'):
        p = shutil.which(prog)
        if p: os.symlink(p, d / prog)
    return d


class TestInverse(unittest.TestCase):
    def test_both_verifiers_on_nist_inverse_files(self):
        """every pinned NIST inverse S-box circuit passes both verifiers as aes-invsbox, fails as aes-sbox, is
        detected as the inverse, and is placed against the inverse set (dominated by itself)"""
        files = aesfn.published_files('aes-invsbox')
        self.assertEqual(len(files), 91)
        self.assertTrue(set(files).isdisjoint(aesfn.published_files('aes-sbox')))
        pub = AC.published('aes-invsbox')
        self.assertEqual(len(pub), 91)
        for f in files:
            r = AC.check(f, 'aes-invsbox')
            self.assertTrue(r['ok'] and r['core_ok'] and r['independent_ok'] and r['metrics_agree'], (f, r.get('errors')))
            self.assertIn(f.name, r['dominated_by']); self.assertFalse(r['new_point'])
            self.assertEqual(aesfn.detect(core.read_ncff(str(f))), 'aes-invsbox')
        r = AC.check(files[0], 'aes-sbox'); self.assertFalse(r['ok']); self.assertFalse(r['core_ok'])
        self.assertFalse(AC.check(FWD117, 'aes-invsbox')['ok'])
        self.assertEqual(AC.check(FWD117, 'auto')['function'], 'aes-sbox')
        self.assertTrue(AC.check(FWD117)['ok'])                                   # the default stays the forward S-box
        p = subprocess.run([sys.executable, str(PKG / 'independent' / 'verify.py'), str(INV117), '--aes-inv',
                            '--model', str(PKG / 'models' / 'nist.json')], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        p = subprocess.run([sys.executable, str(PKG / 'aes_check.py'), str(INV117), '--function', 'aes-invsbox'],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0); self.assertIn('(aes-invsbox)', p.stdout)

    def test_hub_and_ops_follow_the_function(self):
        from boolflux.hub import common as HC
        sys.path.insert(0, str(PKG / 'ops'))
        import common as OC
        c = core.read_ncff(str(INV117))
        self.assertFalse(HC.verify(c)[0])                                         # default: forward
        with function('aes-invsbox'):
            ok, info = HC.verify(c); self.assertTrue(ok, info)
            self.assertEqual(len(HC.published()), 91)
            self.assertEqual(OC.AES, list(aesfn.table('aes-invsbox')))
            self.assertEqual(OC.target(INV117.name)['ref'], str(INV117.resolve()))
            self.assertEqual(OC.limits(INV117.name), {'A': 32, 'AD': 4, 'G': 117, 'GD': 21})
        self.assertEqual(OC.AES, list(aesfn.table('aes-sbox')))
        self.assertEqual(aesfn.resolve('auto', INV117), 'aes-invsbox')

    def test_conjugates(self):
        """forward conjugates are the gates of the code before 2026-11-16 (sha256 pins); every inverse conjugate
        computes the inverse S-box, with S^-1(y) = G'(S^-1(Lin y + cL)), Lin = A G A^-1"""
        sys.path.insert(0, str(PKG / 'ops' / 'conj_lib'))
        import conj as CJ
        f = core.read_ncff(str(FWD117)); i = core.read_ncff(str(INV117))
        pins = {(7, 3): '491afacc6d1e9df8aaf17d1453b703d907af9b40d94bf10cc8227a19f392baeb',
                (200, 5): '45d306a278ab8545719c534103fa65a48af43a4b8d86f916672eb66ab80a8417',
                (1, 0): 'c7bfa38a8dd5e52b0af884234bf4153b28331d7ff39764ca239a3146b2d7f591'}
        for (lam, k), h in pins.items():
            self.assertEqual(hashlib.sha256(core.to_kernel(CJ.conj_circuit(f, lam, k, 'aes-sbox')).encode()).hexdigest(), h)
        inv = list(aesfn.table('aes-invsbox'))
        for lam, k in ((1, 0), (7, 3), (200, 5), (255, 7), (2, 1)):
            cc = CJ.conj_circuit(i, lam, k, 'aes-invsbox')
            self.assertEqual(cc.value_table(), inv, (lam, k))
            self.assertEqual(cc.metrics()['A'], 32)
            Lin, cL, Gp, cout = CJ.maps(lam, k, 'aes-invsbox')
            self.assertEqual(cout, 0)
            for y in (0, 1, 0x53, 0xff):                                          # the identity itself
                ly = CJ.apply(Lin, y) ^ cL
                self.assertEqual(inv[y], CJ.apply(Gp, inv[ly]))
        self.assertEqual(len(CJ.conj_circuit(i, 1, 0, 'aes-invsbox').gates), len(i.live().gates))

    @unittest.skipUnless(has('numpy') and has('pysat'), 'ops/conjpull.py needs numpy and python-sat')
    def test_conjpull_on_an_inverse_seed(self):
        """conjpull on a NIST inverse circuit (function detected): one conjugate, one short stage; status ok,
        every circuit it wrote passes aes_check as the inverse, the run record names the function"""
        out = tmpdir()
        env = dict(os.environ, BOOLFLUX_CACHE=str(tmpdir(prefix='bft-cache-'))); env.pop(aesfn.ENV, None)
        p = subprocess.run([sys.executable, str(PKG / 'ops' / 'conjpull.py'), '--in', str(INV117), '--target', INV117.name,
                            '--conj', '7:3', '--schedule', 'g:+2:10', '--seed', '1', '--seconds', '45', '--out', str(out)],
                           capture_output=True, text=True, env=env, timeout=300)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        res = json.loads((out / 'result.json').read_text()); self.assertEqual(res['status'], 'ok')
        rec = json.loads((out / 'run.json').read_text())
        self.assertEqual((rec['function'], rec['kind'], rec['status']), ('aes-invsbox', 'ops.conjpull', 'ok'))
        self.assertEqual(rec['starts'][0]['sha256'], runlog.sha256_file(INV117))
        ev = runlog.read_events(out / 'events.jsonl.gz')
        conj = [e for e in ev if e['ev'] == 'conjugate']
        self.assertEqual([(e['lam'], e['k'], e['metrics'][0]) for e in conj], [(7, 3, 32)])
        kern = [e for e in ev if e['ev'] == 'kernel']
        self.assertTrue(kern and all(e['rc'] == 0 and e['seed'] == 1000 * 100000 + 1 for e in kern[:1]))
        for f in out.glob('conjpull-*.circ.txt'):
            self.assertTrue(AC.check(f, 'aes-invsbox')['ok'], f)
            side = json.loads(f.with_suffix('').with_suffix('.json').read_text())
            self.assertEqual(side['function'], 'aes-invsbox'); self.assertEqual(side['run']['kind'], 'ops.conjpull')


if __name__ == '__main__':
    unittest.main()
