"""ops/conjpull.py and conj_lib (2026-11-17 changes):

    python3 -m unittest search/nonlinear/boolflux/tests/test_conjpull.py   (from the repository root; ~1.5 min)

the vectorised BP run gives the same gates and RNG state as the reference (so the conj3 screen rows and the
built conjugates are unchanged); stage caps (absolute, input-relative, start-relative d+N, lineage clamps);
is_conjugated by content, not path (identity pulls of conjpull are not conjugates); conjugates of a conjugate
are refused with an explicit status; --overrun refuse; the registry skips a repeated (start, conjugate,
schedule); a short successive-halving run (stage 1 on K conjugates incl. 188:0 / 189:0, the best 2 continued).
"""
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
OPS = PKG / 'ops'
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))

from boolflux import core, runlog       # noqa: E402

NIST = PKG.parent / 'seeds'
FWD117 = NIST / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'
INV117 = NIST / 'aes-invsbox' / 'aes-invsbox-a32-ad4-g117-gd21-xx85-10.circ.txt'


def has(m):
    return importlib.util.find_spec(m) is not None


def tmpdir(prefix='bft-cp-'):
    return Path(tempfile.mkdtemp(prefix=prefix))


def load_cp():
    sys.path.insert(0, str(OPS)); sys.path.insert(0, str(OPS / 'conj_lib'))
    import conjpull
    return conjpull


def run_cp(args, out, cache, timeout=300):
    env = dict(os.environ, BOOLFLUX_CACHE=str(cache)); env.pop('BOOLFLUX_CONJ_REGISTRY', None)
    p = subprocess.run([sys.executable, str(OPS / 'conjpull.py')] + [str(x) for x in args] + ['--out', str(out)],
                       capture_output=True, text=True, env=env, timeout=timeout)
    return p, json.loads((out / 'result.json').read_text())


@unittest.skipUnless(has('numpy') and has('pysat'), 'ops/conjpull.py needs numpy and python-sat')
class TestConjLib(unittest.TestCase):
    def test_bp_run_same_as_reference(self):
        """bp_run (incremental distances, vectorised pair scan, one getrandbits) = bp_run_ref: same gates, same RNG
        state after, on random target sets and on conjugated top layers of a NIST circuit"""
        sys.path.insert(0, str(OPS / 'conj_lib'))
        import bp
        import conj3 as C3
        r = random.Random(3); cases = []
        for _ in range(60):
            m = r.choice([5, 6, 8, 8])
            cases.append((m, [r.randrange(1, 1 << m) for _ in range(r.randrange(2, 24))], r.randrange(1 << 30),
                          r.choice([0.0, 0.5, 1.0])))
        cp = load_cp()
        top, outs, nl = C3.layers(cp.CM.load(FWD117))
        for lam, k in ((2, 0), (9, 4), (188, 0), (77, 6)):
            G = C3.CJ.maps(lam, k)[0]
            urow = [sum(1 << (7 - j) for j in range(8) if G[j] >> (7 - i) & 1) for i in range(8)]
            nt = []
            for t in top:
                v = 0
                for i in range(8):
                    if t >> i & 1: v ^= urow[i]
                nt.append(v)
            cases.append((8, [t for t in set(nt) if bin(t).count('1') >= 2], lam * 8 + k, 0.5))
        for m, tl, seed, p in cases:
            a, b = random.Random(seed), random.Random(seed)
            self.assertEqual(bp.bp_run_ref(m, tl, a, p), bp.bp_run(m, tl, b, p), (m, tl, seed, p))
            self.assertEqual(a.getstate(), b.getstate())

    def test_paar_wide_rows(self):
        """paar reads every bit (before: bits 0-63); rows within 64 bits unchanged"""
        sys.path.insert(0, str(OPS / 'conj_lib'))
        import conj3 as C3
        self.assertEqual(C3.paar([0b0111, 0b0110, 0b1011]), 4)
        self.assertEqual(C3.paar([(1 << 70) | 1, (1 << 70) | 1 | 2]), 2)

    def test_stage_caps(self):
        cp = load_cp()
        sc = cp.stage_cap
        self.assertEqual(sc('31', 26, 19, 0, True), (31, 31))           # first stage: as planned (loose recovery)
        self.assertEqual(sc('27', 22, 19, 1, True), (21, 27))           # loose later stage -> a pull of 1
        self.assertEqual(sc('19', 25, 19, 1, True), (23, 19))           # at most 2 levels below the input
        self.assertEqual(sc('19', 25, 19, 1, False), (19, 19))          # --caps plan
        self.assertEqual(sc('19', 25, 19, 1, True, 4), (21, 19))        # --max-pull 4
        self.assertEqual(sc('19', 25, 19, 1, True, 0), (19, 19))        # no floor
        self.assertEqual(sc('27', 22, 19, 1, True, 0), (21, 27))        # still no loose later stage
        self.assertEqual(sc('d+6', 30, 19, 0, True), (25, 25))
        self.assertEqual(sc('d-1', 19, 19, 2, True), (18, 18))
        self.assertEqual(sc('d', 21, 19, 2, True), (19, 19))
        self.assertEqual(sc('+2', 20, 19, 3, True), (22, 22))           # input-relative: unchanged
        self.assertEqual(sc('-1', 20, 19, 3, True), (19, 19))
        self.assertEqual([x[1] for x in cp.parse_schedule('g:d+6:10,m:d:5,m:-1:5,k:23:4')], ['d+6', 'd', '-1', '23'])
        with self.assertRaises(AssertionError):
            cp.parse_schedule('g:x3:10')

    def test_is_conjugated_by_content(self):
        """not by path; a conjpull identity pull (lineage 'start', method text naming conjugation) is not a
        conjugate; a 'conj lam' lineage, a conj.py header, or a conjugate parent is"""
        cp = load_cp()
        d = tmpdir(); text = FWD117.read_text()
        def mk(name, side=None, header=None):
            p = d / name; p.write_text((header + '\n' if header else '') + text)
            if side is not None: (d / (name[:-len('.circ.txt')] + '.json')).write_text(json.dumps(side))
            return p
        meth = 'ops/conjpull.py: GF(2^8) conjugate (conj3 screen + build_conj) then staged kernel pulls'
        self.assertFalse(cp.is_conjugated(mk('cj-3-conj-x.circ.txt')))
        self.assertFalse(cp.is_conjugated(mk('conjpull-a.circ.txt', {'op': 'conjpull', 'method': meth,
                                                                      'lineage': ['start', 'stage 1 g:31:200']})))
        c1 = mk('conjpull-b.circ.txt', {'op': 'conjpull', 'method': meth, 'lineage': ['conj lam 3 k 1 (rank:1, score 50)']})
        self.assertTrue(cp.is_conjugated(c1))
        self.assertTrue(cp.is_conjugated(mk('x.circ.txt', header='% conj.py of y.circ.txt, lam 2 k 0, trb')))
        self.assertTrue(cp.is_conjugated(mk('polish-c.circ.txt', {'op': 'polish', 'parent': {'path': str(c1)}})))
        self.assertFalse(cp.is_conjugated(FWD117))


@unittest.skipUnless(has('numpy') and has('pysat'), 'ops/conjpull.py needs numpy and python-sat')
class TestConjpullRuns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = tmpdir(prefix='bft-cp-cache-')

    def test_refusals(self):
        """conjugates of a conjugate: status refused (not an identity pull); --overrun refuse"""
        d = tmpdir(); p = d / 'conjpull-z.circ.txt'; p.write_text(FWD117.read_text())
        (d / 'conjpull-z.json').write_text(json.dumps({'op': 'conjpull', 'lineage': ['conj lam 7 k 3 (7:3, score None)']}))
        out = tmpdir()
        pr, res = run_cp(['--in', p, '--target', FWD117.name, '--conj', '7:3', '--schedule', 'g:+2:5', '--seconds', 30],
                         out, self.cache)
        self.assertEqual(pr.returncode, 0, pr.stderr)
        self.assertEqual(res['status'], 'refused'); self.assertEqual(res['conj_refused'][0]['label'], '7:3')
        out = tmpdir()
        pr, res = run_cp(['--in', FWD117, '--target', FWD117.name, '--conj', 'id,7:3', '--schedule', 'g:+2:40',
                          '--seconds', 30, '--overrun', 'refuse'], out, self.cache)
        self.assertEqual(res['status'], 'refused'); self.assertGreater(res['plan']['need_s'], res['plan']['avail_s'])
        p = res['params']                       # defaults = the behaviour before 2026-11-17 (the A/B did not decide)
        self.assertEqual((p['stage_caps'], p['identity_first'], p['missed_pulls'], p['stage_choice'], p['bp_cap'],
                          p['repair_keep']), ('plan', 'no', 0, 'old', 'none', 1))

    def test_registry_and_halving(self):
        """sh:3 = 188:0, 189:0 (+ span keepers, then screen order): stage 1 on each, the best 2 continue; a second
        job with the same registry skips the identity pull and the explicit conjugate it already ran"""
        reg = tmpdir() / 'reg.jsonl'
        out = tmpdir()
        pr, res = run_cp(['--in', FWD117, '--target', FWD117.name, '--conj', 'sh:3', '--schedule', 'g:d+6:4,m:d:4',
                          '--seconds', 75, '--registry', reg, '--sh-span', 0, '--identity-first', 'no'], out, self.cache)
        self.assertEqual(pr.returncode, 0, pr.stderr); self.assertEqual(res['status'], 'ok')
        h = res['halving']
        self.assertEqual(h['K'], 3); self.assertEqual(h['candidates'][:2], ['188:0=188:0', '189:0=189:0'])
        self.assertEqual(len(h['ranking']), 3)
        cont = [x for x in res['conj_run'] if x['stages_done'] == 2]
        self.assertEqual(sorted(x['halving_rank'] for x in cont), [1, 2])
        ev = runlog.read_events(out / 'events.jsonl.gz')
        self.assertTrue(any(e['ev'] == 'halving-rank' for e in ev))
        st = [e for e in ev if e['ev'] == 'stage']
        self.assertTrue(all(e['cap_planned'] == 25 for e in st if e['stage'] == 1))
        lines = [json.loads(l) for l in reg.read_text().splitlines()]
        self.assertEqual(len(lines), 5)                                 # 3 stage-1 entries + 2 continuations
        cont1 = [x['label'] for x in cont]
        out2 = tmpdir()
        pr, res2 = run_cp(['--in', FWD117, '--target', FWD117.name, '--conj', '%s,sh:2' % cont1[0], '--schedule',
                           'g:d+6:4,m:d:4', '--seconds', 60, '--registry', reg, '--sh-span', 0, '--identity-first', 'no'],
                          out2, self.cache)
        self.assertEqual(res2['status'], 'ok'); self.assertTrue(res2['fates'][cont1[0]].startswith('skipped: registry'))
        self.assertEqual(res2['halving']['registry_skipped'], 3)       # the three stage-1 runs of the first job
        self.assertFalse({'188:0=188:0', '189:0=189:0'} & set(res2['halving']['candidates']))
        for f in out.glob('conjpull-*.circ.txt'):
            side = json.loads(f.with_name(f.name[:-len('.circ.txt')] + '.json').read_text())
            self.assertLessEqual(side['A'], 32); self.assertLessEqual(side['AD'], 4)

    def test_halving_probe(self):
        """sh:3 --sh-probe 3: one probe stage (stage 1's cap, gate mode) per candidate, the best --sh-keep 1 runs the
        WHOLE schedule (stages 1 and 2) from its probe best; the probe is logged as a probe stage, not a schedule stage"""
        out = tmpdir()
        pr, res = run_cp(['--in', FWD117, '--target', FWD117.name, '--conj', 'sh:3', '--sh-probe', 3, '--sh-keep', 1,
                          '--schedule', 'g:d+6:4,m:d:4', '--seconds', 90, '--sh-span', 0, '--identity-first', 'no'],
                         out, self.cache)
        self.assertEqual(pr.returncode, 0, pr.stderr); self.assertEqual(res['status'], 'ok')
        h = res['halving']
        self.assertEqual(h['K'], 3); self.assertEqual(h['probe_s'], 3); self.assertEqual(len(h['ranking']), 3)
        cont = [x for x in res['conj_run'] if x['stages_done'] == 2]
        self.assertEqual([x['halving_rank'] for x in cont], [1])
        self.assertEqual(sum(1 for x in res['conj_run'] if x['stages_done'] == 0), 2)
        ev = runlog.read_events(out / 'events.jsonl.gz')
        st = [e for e in ev if e['ev'] == 'stage']
        self.assertEqual(sum(1 for e in st if e['probe']), 3)
        self.assertTrue(all(e['cap_planned'] == 25 and e['mode'] == 'g' for e in st if e['probe']))
        self.assertEqual(sorted(e['stage'] for e in st if not e['probe']), [1, 2])
        self.assertTrue(any(v.startswith('halving: probe only') for v in res['fates'].values()))


if __name__ == '__main__':
    unittest.main()
