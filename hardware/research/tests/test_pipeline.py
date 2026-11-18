"""Regression tests of the study's pipeline (no EDA tools needed):

  - run.py exits with status 1 when a preparation or a job fails;
  - manifest.py / collect.py stop on missing results and write nothing;
  - research fingerprints change with the harness and with the variant's settings;
  - stale repeat results (old fingerprints, other settings) are rejected.

    python3 -m unittest discover -s hardware/research/tests -t hardware/research
"""
import contextlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))

import harness as H  # noqa: E402
import manifest as M  # noqa: E402
import run as RUN  # noqa: E402
import collect as C  # noqa: E402
import revalidate as RV  # noqa: E402
from hwbench import design as D, flow as F, verilog as V  # noqa: E402

REPO = HERE.parents[2]
CIRC = 'hardware/research/candidates/aes-mixcolumns/aes-mixcolumns-xor97-depth3-h9e2cc4c35f6e50b0.circ.txt'


class Sandbox(unittest.TestCase):
    """Research build folder, library hash and job functions replaced for the test."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.saved = (H.RBUILD, H.lib_sha, H.run_job, H.prepare_design, M.jobs, C.OUT,
                      H.HARNESS_SHA256, dict(H.GP_DEFAULTS), RV.TMP)
        H.RBUILD = self.tmp / 'build'
        H.lib_sha = lambda platform: 'lib-' + platform      # no Liberty file needed
        RV.TMP = self.tmp / 'reval'
        self.circ = str(REPO / CIRC)
        self.d = D.load(self.circ)

    def tearDown(self):
        (H.RBUILD, H.lib_sha, H.run_job, H.prepare_design, M.jobs, C.OUT,
         H.HARNESS_SHA256, gp, RV.TMP) = self.saved
        H.GP_DEFAULTS.clear()
        H.GP_DEFAULTS.update(gp)
        H.set_variant('base')
        F.BUILD = F.ROOT / 'build'
        F.fingerprint = H._fingerprint
        shutil.rmtree(self.tmp)

    def write_metrics(self, variant, platform='nangate45', flow='preserve', fp=None, settings=None):
        mf = H.RBUILD / variant / self.d.id / platform / flow / 'metrics.json'
        mf.parent.mkdir(parents=True, exist_ok=True)
        parts = (self.d.sha256, platform, flow, H.lib_sha(platform))
        r = {'fingerprint': fp or H.job_fingerprint(variant, *parts), 'design': self.d.id,
             'platform': platform, 'flow': flow,
             'research': {'settings': settings or H.settings(variant)}}
        mf.write_text(json.dumps(r))
        return mf


class TestRunExitStatus(Sandbox):
    def setUp(self):
        super().setUp()
        os.environ['HWRESEARCH_CHECK_LIBRARIES'] = '0'      # no Liberty files in CI

    def tearDown(self):
        os.environ.pop('HWRESEARCH_CHECK_LIBRARIES', None)
        super().tearDown()

    def run_main(self):
        lst = self.tmp / 'list.txt'
        lst.write_text(CIRC + '\n')
        with contextlib.redirect_stdout(io.StringIO()):
            return RUN.main(['--list', str(lst), '--variant', 'pnr1', '-p', 'nangate45',
                             '-f', 'preserve,free', '-j', '1'])

    def test_success_is_zero(self):
        H.prepare_design = lambda path, variant: None
        H.run_job = lambda path, plat, flow, variant: {'seconds': 0}
        self.assertEqual(self.run_main(), 0)

    def test_failed_job_is_nonzero(self):
        H.prepare_design = lambda path, variant: None

        def job(path, plat, flow, variant):
            if flow == 'free':
                raise RuntimeError('synthesis failed')
            return {'seconds': 0}
        H.run_job = job
        self.assertEqual(self.run_main(), 1)
        fails = (H.RBUILD / 'pnr1' / 'failures.jsonl').read_text().splitlines()
        self.assertEqual(len(fails), 1)
        self.assertEqual(json.loads(fails[0])['flow'], 'free')

    def test_failed_preparation_is_nonzero(self):
        def prep(path, variant):
            raise RuntimeError('RTL check failed')
        H.prepare_design = prep
        H.run_job = lambda *a: self.fail('a job ran after its preparation failed')
        self.assertEqual(self.run_main(), 1)


class TestFingerprints(Sandbox):
    def fp(self, variant):
        return H.job_fingerprint(variant, self.d.sha256, 'nangate45', 'free', 'lib')

    def test_variants_differ_and_names_are_canonical(self):
        fps = {v: self.fp(v) for v in ('base', 'pnr1', 'pnr2', 'synth1', 'o1p2', 'o2p1')}
        self.assertEqual(len(set(fps.values())), len(fps))
        self.assertEqual(self.fp('o0p1'), fps['pnr1'])
        self.assertEqual(self.fp('o1p1'), fps['synth1'])
        self.assertEqual(self.fp('o0p0'), fps['base'])
        self.assertEqual(H.canonical('o2p2'), 'synth2')
        self.assertEqual(H.canonical('synth0'), 'base')

    def test_research_differs_from_benchmark(self):
        self.assertNotEqual(self.fp('base'),
                            H.bench_fingerprint(self.d.sha256, 'nangate45', 'free', 'lib'))

    def test_harness_change_invalidates(self):
        before = self.fp('pnr1')
        H.HARNESS_SHA256 = '0' * 64
        self.assertNotEqual(self.fp('pnr1'), before)

    def test_setting_change_invalidates(self):
        before, base = self.fp('pnr1'), self.fp('base')
        H.GP_DEFAULTS['overflow'] = 0.2
        self.assertNotEqual(self.fp('pnr1'), before)
        self.assertEqual(self.fp('base'), base)          # base runs the benchmark's script

    def test_set_variant_salts_job_and_rtl_fingerprints(self):
        H.set_variant('synth2')
        self.assertEqual(F.fingerprint(self.d.sha256), H.job_fingerprint('synth2', self.d.sha256))
        self.assertEqual(F.BUILD, H.RBUILD / 'synth2')
        self.assertIn('seeded random order (seed 2)', V.rtl(self.d))
        H.set_variant('pnr2')
        self.assertNotIn('seeded random order', V.rtl(self.d))
        self.assertIn('-random_seed 2', F.PNR_TCL)
        H.set_variant('base')
        self.assertEqual(F.PNR_TCL, H._PNR)
        self.assertIs(V.rtl, H._rtl)


class TestManifestAndCollect(Sandbox):
    def jobs(self, variants=('pnr1',)):
        return [M.Job('repeats', v, self.circ, 'nangate45', 'preserve', 'test') for v in variants]

    def test_missing_result_stops(self):
        js = self.jobs()
        res = M.check(js=js)
        self.assertEqual(len(res['missing']), 1)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            M.require(js=js)

    def test_current_result_is_ok(self):
        self.write_metrics('pnr1')
        res = M.check(js=self.jobs())
        self.assertEqual((len(res['ok']), len(res['missing']), len(res['stale'])), (1, 0, 0))

    def test_stale_repeat_rejected(self):
        parts = (self.d.sha256, 'nangate45', 'preserve', H.lib_sha('nangate45'))
        # a result of the benchmark's fingerprint (no harness in it)
        self.write_metrics('pnr1', fp=H.bench_fingerprint(*parts))
        self.assertEqual(len(M.check(js=self.jobs())['stale']), 1)
        # the right fingerprint but another variant's settings record
        self.write_metrics('pnr1', settings=H.settings('pnr2'))
        self.assertEqual(len(M.check(js=self.jobs())['stale']), 1)
        # made by an older harness
        self.write_metrics('pnr1')
        H.HARNESS_SHA256 = 'f' * 64
        self.assertEqual(len(M.check(js=self.jobs())['stale']), 1)

    def test_unlisted_results_reported_not_collected(self):
        self.write_metrics('pnr1')
        self.write_metrics('pnr1', flow='free')
        res = M.check(js=self.jobs())
        self.assertEqual(len(res['ok']), 1)
        self.assertEqual(len(res['unlisted']), 1)

    def test_collect_writes_nothing_when_incomplete(self):
        out = self.tmp / 'results'
        out.mkdir()
        (out / 'table.csv').write_text('published\n')
        C.OUT = out
        M.jobs = lambda stages=M.STAGES: self.jobs(('pnr1', 'pnr2'))
        self.write_metrics('pnr1')                       # pnr2 missing
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            C.main([])
        self.assertEqual((out / 'table.csv').read_text(), 'published\n')
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['table.csv'])

    def test_collect_writes_nothing_when_stale(self):
        out = self.tmp / 'results'
        out.mkdir()
        (out / 'seeds.csv').write_text('published\n')
        C.OUT = out
        M.jobs = lambda stages=M.STAGES: self.jobs(('pnr1', 'pnr2'))
        self.write_metrics('pnr1')
        self.write_metrics('pnr2', settings=H.settings('pnr1'))      # another variant's record
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            C.main([])
        self.assertEqual((out / 'seeds.csv').read_text(), 'published\n')
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['seeds.csv'])

    def test_collect_refuses_partial_results(self):
        with self.assertRaises(SystemExit):
            C.main(['--stage', 'baseline,base'])            # default --out is results/

    def test_extra_jobs_file(self):
        js = M.read_jobs_file('extra.txt')
        self.assertTrue(js and all(pathlib.Path(j.file).exists() for j in js))
        self.assertEqual({j.stage for j in js}, {'base', 'repeats'})


class TestRevalidateRTL(Sandbox):
    def rtl_dir(self, variant, rtl_text, fp):
        H.set_variant(variant)
        dd = F.design_dir(self.d)
        dd.mkdir(parents=True, exist_ok=True)
        (dd / 'rtl.v').write_text(rtl_text)
        (dd / 'rtl_check.json').write_text(json.dumps({'formal': 'proved', 'fingerprint': fp}))

    def test_matching_rtl_restamped(self):
        rtl = H.shuffled_rtl(1)(self.d)
        self.rtl_dir('synth1', rtl, H.bench_fingerprint(self.d.sha256))
        self.assertEqual(RV._design(('synth1', self.circ, False)), 'restamp')
        self.assertEqual(RV._design(('synth1', self.circ, False)), 'ok')

    def test_other_statement_order_rejected(self):
        rtl = H.shuffled_rtl(7)(self.d)
        self.rtl_dir('synth1', rtl, H.bench_fingerprint(self.d.sha256))
        self.assertEqual(RV._design(('synth1', self.circ, False)), 'rtl.v differs')

    def test_unknown_fingerprint_rejected(self):
        self.rtl_dir('base', V.rtl(self.d), 'deadbeef')
        self.assertIn('not the benchmark', RV._design(('base', self.circ, False)))


if __name__ == '__main__':
    unittest.main()
