"""Regression tests for the review-5 findings on the Python package (nonlinear/boolflux/review5/PYTHON.md).

    python3 -m unittest nonlinear/boolflux/tests/test_review5_py.py     (from the repository root; ~1 min)

P1 independence of the two verifiers      P9  kernel / Python twins with an A cap
P2 BUF lines in aes_check                 P10 published() cache
P3 write_ncff wire names                  P11 best_table: one row per tuple, nothing dropped, speed
P4 read_ncff structure errors             P12 curate_aes with hub archives
P5 from_kernel structure errors           P13 the same circuit under two tracks
P6 NIST conventions (NOT, XNOR 0, BUF)    P14 manifest nist-format name collisions
P7 cli help texts, defaults, messages     P15 collect.py ranking
P8 model not_as                           P16 tool help / usage errors
P17 skeleton size, P18 core speed, P19 cli verify with NOT, P20 manifest start kind,
P21-P24 manifest reproducibility records and --check-repro, P25 atomic kernel builds,
P26 kernel seeds (collision-free, one formula for cli and workflow, legacy reachable)
"""
import ast
import contextlib
import io
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
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))
sys.path.insert(0, str(PKG / 'campaigns')); sys.path.insert(0, str(PKG / 'independent'))

from boolflux import core, objective, targets, workflow   # noqa: E402
import cli                                                # noqa: E402
import verify as V                                        # noqa: E402
import aes_check as AC                                    # noqa: E402
import best_table as BT                                   # noqa: E402

NIST = REPO / 'nonlinear' / 'nist'
NIST_MODEL = core.Model.load('nist')
CLI = [sys.executable, str(PKG / 'cli.py')]


def tmpdir(prefix='r5p-'):
    return Path(tempfile.mkdtemp(prefix=prefix))


def run_cli(*args):
    return subprocess.run(CLI + list(args), capture_output=True, text=True, cwd=str(REPO))


def an_aes_circuit():
    """A pinned NIST forward AES S-box circuit (the first one by name)."""
    return sorted((NIST / 'aes-sbox').glob('*.circ.txt'))[0]


def result_circuits(k):
    """k AES results of ours with pairwise different tuples that are new on the pinned set."""
    out = {}
    for f in sorted((PKG / 'results' / 'aes').glob('*.circ.txt')):
        m = core.read_ncff(str(f)).metrics()
        out.setdefault((m['A'], m['AD'], m['G'], m['GD']), f)
    new, front = BT.pareto(out, [u for u, _ in AC.published()])
    return [out[t] for t in front[:k]]


def swapped(c):
    """The same function and metrics with another gate list: operands of the first symmetric gate swapped."""
    gates = list(c.gates)
    for j, (op, a, b) in enumerate(gates):
        if op in core.SYMMETRIC and a != b:
            gates[j] = (op, b, a); break
    return core.Circuit(c.n, c.m, gates, list(c.outputs), c.name)


class TestCoreFormats(unittest.TestCase):
    def test_p3_wire_names_cannot_collide(self):
        """Inputs or outputs named t1, t2, ... used to collide with the internal wire names: the
        written file read back as a different circuit (or failed), with no error."""
        gates = [(8, 0, 1), (6, 2, 0), (6, 3, 1), (9, 4, 2)]
        c = core.Circuit(2, 2, gates, [5, 3], 'clash', in_names=['t1', 't2'], out_names=['t3', 'y'])
        for model in (None, NIST_MODEL):
            text = core.write_ncff(c, model)
            c2 = core.read_ncff(text)
            self.assertEqual((c2.gates, c2.outputs, c2.in_names, c2.out_names), (c.gates, c.outputs, c.in_names, c.out_names))
            self.assertEqual(c2.value_table(), c.value_table())
            vc = V.parse_circuit(text)                       # the independent reader accepts it too
            self.assertEqual([V.evaluate_int(vc, x) for x in range(4)], c.value_table())
        ok = core.Circuit(2, 1, [(8, 0, 1)], [2], 'plain')
        self.assertIn('AND y0 x0 x1', core.write_ncff(ok))       # unchanged naming when nothing collides
        self.assertIn('Internal: t1:t2', core.write_ncff(core.Circuit(2, 1, [(8, 0, 1), (6, 2, 0), (6, 3, 1)], [4])))
        with self.assertRaises(ValueError):
            core.write_ncff(core.Circuit(2, 1, [(8, 0, 1)], [2], in_names=['a', 'a'], out_names=['y']))

    def test_p4_read_ncff_rejects_malformed(self):
        head = 'begin circuit c\nInputs: a b\nOutputs: y\nbegin SLP\n'
        tail = 'end SLP\nend circuit\n'
        bad = {'assigned twice': 'XOR t a b\nAND t a b\nXOR y t a\n',
               'input assigned': 'XOR a a b\nXOR y a b\n',
               'not defined': 'XOR y a zz\n',
               'defined later': 'XOR y a t\nAND t a b\n',
               'unknown gate': 'MUX y a b\n',
               'operands': 'XOR y a\n',
               'constant output': 'BUF y 1\n'}
        for what, body in bad.items():
            with self.assertRaises(ValueError, msg=what):
                core.read_ncff(head + body + tail)
        with self.assertRaises(ValueError):
            core.read_ncff('begin circuit c\nOutputs: y\nbegin SLP\nXOR y a b\n' + tail)
        # every one of these is also a failure for the independent reader
        for what, body in bad.items():
            if what == 'constant output': continue          # BUF y 1 is legal NCFF there; core has no constants
            with self.assertRaises(V.CircuitError, msg=what):
                V.parse_circuit(head + body + tail)
        # the first circuit of a file only, as the independent verifier
        two = head + 'XOR y a b\n' + tail + '\nbegin circuit d\nInputs: a b\nOutputs: y\nbegin SLP\nAND y a b\n' + tail
        c = core.read_ncff(two)
        self.assertEqual((c.name, c.gates), ('c', [(6, 0, 1)]))
        self.assertEqual([V.evaluate_int(V.parse_circuit(two), x) for x in range(4)], c.value_table())

    def test_p5_from_kernel_rejects_malformed(self):
        good = 'n 2\nm 1\ng 2\n8 0 1\n6 2 0\no 3\n'
        self.assertEqual(core.to_kernel(core.from_kernel(good)), good)
        for what, text in {'negative operand': 'n 2\nm 1\ng 2\n8 0 1\n6 2 -1\no 3\n',
                           'forward operand': 'n 2\nm 1\ng 2\n8 0 3\n6 2 0\no 3\n',
                           'truncated': 'n 2\nm 1\ng 3\n8 0 1\n6 2 0\no 3\n',
                           'no output line': 'n 2\nm 1\ng 2\n8 0 1\n6 2 0\n',
                           'output count': 'n 2\nm 2\ng 2\n8 0 1\n6 2 0\no 3\n',
                           'output range': 'n 2\nm 1\ng 2\n8 0 1\n6 2 0\no 4\n',
                           'bad op': 'n 2\nm 1\ng 1\n16 0 1\no 2\n',
                           'empty': ''}.items():
            with self.assertRaises(ValueError, msg=what):
                core.from_kernel(text)

    def test_roundtrip_of_the_pinned_set(self):
        """NCFF -> Circuit -> NCFF -> Circuit and Circuit -> .bfx -> Circuit are exact for every pinned
        forward AES circuit, with the file's own wire names, and core's metrics equal the
        independent verifier's on the original file."""
        files = AC.published_files()
        self.assertGreater(len(files), 90)
        for f in files:
            c = core.read_ncff(str(f))
            for model in (NIST_MODEL, None):
                c2 = core.read_ncff(core.write_ncff(c, model))
                self.assertEqual((c2.gates, c2.outputs, c2.in_names, c2.out_names),
                                 (c.gates, c.outputs, c.in_names, c.out_names), f.name)
            k = core.from_kernel(core.to_kernel(c))
            self.assertEqual((k.gates, k.outputs), (c.gates, c.outputs), f.name)
            im = V.compute_metrics(V.parse_file(str(f))); cm = c.metrics()
            self.assertEqual([cm[x] for x in ('G', 'A', 'GD', 'AD')], [im[x] for x in ('G', 'A', 'GD', 'AD')], f.name)

    def test_p6_nist_conventions(self):
        """NOT is a gate (G and gate depth) and is written XNOR t a 0 under the NIST model; BUF is not
        a gate and has no depth; A counts ANDs; input 0 / output 0 are the most significant bits."""
        # y0 = NOT(a AND b), y1 = a, y2 = y0 again
        c = core.Circuit(2, 3, [(8, 0, 1), (3, 2, 2)], [3, 0, 3], 'conv', ['a', 'b'], ['y0', 'y1', 'y2'])
        m = c.metrics(NIST_MODEL)
        self.assertEqual((m['G'], m['A'], m['GD'], m['AD'], m['cost'], m['counts']), (2, 1, 2, 1, 2.0, {'AND': 1, 'NOT': 1}))
        text = core.write_ncff(c, NIST_MODEL)
        self.assertIn('XNOR y0 t1 0', text)
        self.assertIn('BUF y1 a', text); self.assertIn('BUF y2 y0', text)
        self.assertIn('G=2 A=1 GD=2 AD=1 AND=1 XNOR=1', text)
        self.assertIn('NOT y0 t1', core.write_ncff(c, None))
        vm = V.compute_metrics(V.parse_circuit(text))
        self.assertEqual((vm['G'], vm['A'], vm['GD'], vm['AD'], vm['counts']), (2, 1, 2, 1, {'AND': 1, 'BUF': 2, 'XNOR': 1}))
        back = core.read_ncff(text)
        self.assertEqual((back.gates, back.outputs), (c.gates, c.outputs))
        # msb/msb: x = a<<1 | b, value = y0<<2 | y1<<1 | y2
        want = [(1 - ((x >> 1) & x & 1)) * 5 + ((x >> 1) & 1) * 2 for x in range(4)]
        self.assertEqual(c.value_table(), want)
        self.assertEqual([V.evaluate_int(V.parse_circuit(text), x) for x in range(4)], want)
        # the other constant folds: XOR t a 1 = NOT a, XOR t a 0 and XNOR t a 1 = wire
        t2 = 'begin circuit k\nInputs: a b\nOutputs: y\nbegin SLP\nXOR p a 1\nXNOR q p 1\nXOR r q 0\nAND y r b\nend SLP\nend circuit\n'
        k = core.read_ncff(t2)
        self.assertEqual(k.gates, [(3, 0, 0), (8, 2, 1)])
        self.assertEqual(k.value_table(), [V.evaluate_int(V.parse_circuit(t2), x) for x in range(4)])

    def test_p8_model_not_as_checked(self):
        d = tmpdir()
        (d / 'm.json').write_text(json.dumps({'name': 'm', 'gates': {'AND': 1, 'XOR': 1, 'XNOR': 1, 'NOT': 1}, 'not_as': 'xnor0'}))
        with self.assertRaises(SystemExit):
            core.Model.load(str(d / 'm.json'))
        for f in core.MODELS.glob('*.json'):
            core.Model.load(f.stem)

    def test_p4_declarations_read_as_the_independent_reader_does(self):
        """Commas, zero-padded ranges and a declaration spread over two lines: both readers agree."""
        text = ('begin circuit d\nInputs: x00:x02,\nInputs: k\nOutputs: y1:y0\nbegin SLP\n'
                'AND t x00 x01\nXOR y1 t x02\nXNOR y0 y1 k\nend SLP\nend circuit\n')
        c = core.read_ncff(text)
        vc = V.parse_circuit(text)
        self.assertEqual((c.in_names, c.out_names), (['x00', 'x01', 'x02', 'k'], ['y1', 'y0']))
        self.assertEqual((vc.inputs, vc.outputs), (c.in_names, c.out_names))
        self.assertEqual(c.value_table(), [V.evaluate_int(vc, x) for x in range(16)])
        self.assertEqual(core._expand('x8:x11 a b7:b5'), ['x8', 'x9', 'x10', 'x11', 'a', 'b7', 'b6', 'b5'])

    def test_p17_skeleton_too_large_for_the_kernel_is_an_error(self):
        from boolflux import skeleton
        ok = {'n': 8, 'm': 1, 'ands': [(2, 4)] * 480, 'outputs': [2]}
        skeleton.write_skel(ok, [0])
        with self.assertRaises(ValueError):
            skeleton.write_skel(dict(ok, ands=[(2, 4)] * 481), [0])
        with self.assertRaises(ValueError):                  # 1 + n + k positions must fit in 64 * MW bits
            skeleton.write_skel({'n': 40, 'm': 1, 'ands': [(2, 4)] * 475, 'outputs': [2]}, [0])

    def test_p18_cached_input_tables_and_cost_table(self):
        a = core.input_tables(3); a.append('x'); a[0] = 0     # callers own the list they get
        self.assertEqual(core.input_tables(3), [0b11110000, 0b11001100, 0b10101010])
        c = core.Circuit(2, 1, [(8, 0, 1), (14, 2, 0), (3, 3, 3)], [4])
        d = tmpdir(); (d / 'w.json').write_text(json.dumps({'name': 'w', 'gates': {'AND': 2.5, 'OR': 0.25, 'NOT': 1}}))
        self.assertEqual(c.metrics(core.Model.load(str(d / 'w.json')))['cost'], 3.75)
        self.assertIsNone(c.metrics()['cost'])
        self.assertNotEqual(c.metrics(core.Model.load('nist'))['cost'], c.metrics(core.Model.load('nist'))['cost'])   # NaN: OR is outside nist


class TestKernelTwin(unittest.TestCase):
    def test_p9_metrics_and_path_excess_with_every_cap(self):
        """The kernel's metrics, cap excess and summed path excess equal objective.measure on random
        circuits under GD, AD and A caps (the review-4 twin script had no A cap and is not a test)."""
        cli.build_kernel()
        rng = random.Random(5); wd = tmpdir()
        model = core.Model.load('gc')
        ops = [8, 14, 6, 9, 7, 1, 4, 13, 3]
        checked = viol = 0
        for t in range(40):
            n, ng = 6, rng.randrange(15, 50)
            gates = []
            for j in range(ng):
                op = rng.choice(ops); a = rng.randrange(n + j)
                b = a if op == 3 else (a + 1 + rng.randrange(n + j - 1)) % (n + j)
                gates.append((op, a, b))
            c = core.Circuit(n, 3, gates, [n + ng - 1 - k for k in range(3)]).live()
            m0 = c.metrics(model)
            caps = [{'GD': max(1, m0['GD'] - 2)}, {'AD': max(0, m0['AD'] - 1)}, {'A': max(0, m0['A'] - 3)},
                    {'GD': max(1, m0['GD'] - 1), 'AD': max(0, m0['AD'] - 1), 'A': max(0, m0['A'] - 1)}, {}][t % 5]
            (wd / 'in.bfx').write_text(core.to_kernel(c))
            workflow.kernel_cfg(wd / 'k.cfg', wd / 'in.bfx', wd / 'out.bfx', model, {'objective': 'cost', 'caps': caps}, 60, 1, {}, iters=0)
            r = subprocess.run([str(cli.KBIN), str(wd / 'k.cfg')], capture_output=True, text=True)
            if r.returncode != 0:
                continue                                   # a structurally constant gate: the kernel refuses the start
            st = next(dict(zip(ln.split()[1::2], ln.split()[2::2])) for ln in r.stdout.splitlines() if ln.startswith('start '))
            out = core.from_kernel((wd / 'out.bfx').read_text())
            pm = objective.measure(out, model, caps)
            checked += 1
            self.assertEqual([int(st[k]) for k in ('G', 'A', 'GD', 'AD')], [pm[k] for k in ('G', 'A', 'GD', 'AD')])
            self.assertAlmostEqual(float(st['cost']), pm['cost'], places=6)
            e = objective.excess(pm, caps)
            self.assertEqual(int(st['feas']), int(e == 0))
            self.assertAlmostEqual(float(st['obj']), pm['cost'] + 1e6 * e + 1e4 * pm.get('VSUM', 0), places=4)
            self.assertEqual(objective.rank(pm, caps, 'cost,gd'),
                             (0 if e == 0 else 1, e, pm.get('VSUM', 0) if e else 0, pm['cost'], pm['GD']))
            viol += bool(e)
        self.assertGreater(checked, 25); self.assertGreater(viol, 10)


class TestAesCheck(unittest.TestCase):
    def test_p1_independent_verifier_imports_nothing_of_ours(self):
        tree = ast.parse((PKG / 'independent' / 'verify.py').read_text())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): mods |= {a.name.split('.')[0] for a in node.names}
            if isinstance(node, ast.ImportFrom): mods.add((node.module or '').split('.')[0])
        self.assertLessEqual(mods, {'__future__', 'argparse', 'json', 'math', 're', 'sys', 'dataclasses'})

    def test_p1_each_side_fails_on_its_own(self):
        """A wrong circuit is rejected by both sides separately; the metrics of the two sides are
        compared; a .bfx input writes nothing to disk."""
        src = an_aes_circuit()
        good = AC.check(src)
        self.assertTrue(good['ok'] and good['core_ok'] and good['independent_ok'] and good['metrics_agree'])
        c = core.read_ncff(str(src))
        d = tmpdir()
        j = next(j for j, g in enumerate(c.gates) if g[0] == 6)
        wrong = core.Circuit(8, 8, c.gates[:j] + [(9,) + c.gates[j][1:]] + c.gates[j + 1:], list(c.outputs))
        (d / 'wrong.circ.txt').write_text(core.write_ncff(wrong, NIST_MODEL))
        (d / 'wrong.bfx').write_text(core.to_kernel(wrong))
        (d / 'good.bfx').write_text(core.to_kernel(c))
        before = sorted(p.name for p in d.iterdir())
        for name in ('wrong.circ.txt', 'wrong.bfx'):
            r = AC.check(d / name)
            self.assertEqual((r['ok'], r['core_ok'], r['independent_ok']), (False, False, False), name)
        r = AC.check(d / 'good.bfx')
        self.assertTrue(r['ok']); self.assertEqual(tuple(r['tuple']), tuple(good['tuple']))
        self.assertEqual(sorted(p.name for p in d.iterdir()), before)
        # an OR gate: right function is not enough, the library is checked on both sides
        (d / 'or.bfx').write_text(core.to_kernel(core.Circuit(8, 8, c.gates + [(14, 0, 1)], list(c.outputs))))
        r = AC.check(d / 'or.bfx')
        self.assertEqual((r['ok'], r['core_ok'], r['library_ok']), (False, True, False))

    def test_p2_buf_is_not_a_gate(self):
        """A file whose outputs are BUF lines used to FAIL the library check (BUF not in the NIST set)."""
        c = core.read_ncff(str(an_aes_circuit()))
        lines = ['begin circuit bufs', 'Inputs: ' + ' '.join('x%d' % i for i in range(8)),
                 'Outputs: ' + ' '.join('y%d' % i for i in range(8)), 'begin SLP']
        nm = lambda s: 'x%d' % s if s < 8 else 'w%d' % (s - 8)
        for j, (op, a, b) in enumerate(c.gates):
            lines.append('XNOR w%d %s 0' % (j, nm(a)) if op == 3 else '%s w%d %s %s' % (core.OPNAME[op], j, nm(a), nm(b)))
        lines += ['BUF y%d %s' % (k, nm(s)) for k, s in enumerate(c.outputs)] + ['end SLP', 'end circuit']
        d = tmpdir(); (d / 'bufs.circ.txt').write_text('\n'.join(lines) + '\n')
        r = AC.check(d / 'bufs.circ.txt')
        self.assertTrue(r['ok'], r.get('errors'))
        m = c.metrics()
        self.assertEqual(tuple(r['tuple']), (m['A'], m['AD'], m['G'], m['GD']))
        self.assertEqual(r['counts'].get('BUF'), 8)

    def test_p16_bad_file_fails_alone(self):
        d = tmpdir()
        (d / 'garbage.circ.txt').write_text('not a circuit\n')
        (d / 'garbage.bfx').write_text('n 8\nm 8\ng 1\n')
        (d / 'small.bfx').write_text('n 2\nm 1\ng 1\n8 0 1\no 2\n')
        for f in ('garbage.circ.txt', 'garbage.bfx', 'small.bfx', 'missing.circ.txt'):
            r = AC.check(d / f)
            self.assertFalse(r['ok'], f); self.assertTrue(r['errors'], f)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = AC.main([str(d / 'garbage.circ.txt'), str(an_aes_circuit()), '--json', str(d / 'o.json')])
        self.assertEqual(rc, 1)
        self.assertIn('FAIL', buf.getvalue()); self.assertIn('OK  ', buf.getvalue())
        self.assertEqual([r['ok'] for r in json.loads((d / 'o.json').read_text())], [False, True])
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)                   # no file: usage error, not silent success
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), '-h'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0); self.assertIn('A AD G GD', r.stdout)

    def test_p10_published_cache_is_the_same_result(self):
        """The cached published set equals a fresh computation, is keyed by the files' bytes and the
        verifier's source, and can be turned off."""
        old = {k: os.environ.get(k) for k in ('XDG_CACHE_HOME', 'BOOLFLUX_NO_CACHE')}
        d = tmpdir()
        try:
            os.environ['XDG_CACHE_HOME'] = str(d); os.environ.pop('BOOLFLUX_NO_CACHE', None)
            fresh = AC.published.__wrapped__()                 # computed, written to the cache
            cf = AC._cache_file(AC.published_files())
            self.assertTrue(cf.exists())
            self.assertEqual(AC.published.__wrapped__(), fresh)  # read back
            self.assertEqual(len(fresh), len(AC.published_files()))
            self.assertTrue(all(len(u) == 4 for u, _ in fresh))
            other = AC._cache_file(AC.published_files()[:-1])   # another set of files: another cache entry
            self.assertNotEqual(other, cf)
            cf.write_text('garbage')                            # a damaged cache file is recomputed, not trusted
            self.assertEqual(AC.published.__wrapped__(), fresh)
            os.environ['BOOLFLUX_NO_CACHE'] = '1'
            self.assertIsNone(AC._cache_file(AC.published_files()))
        finally:
            for k, v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        self.assertEqual(AC.published(), fresh)


class TestBestTable(unittest.TestCase):
    def test_p11_scan_keeps_every_distinct_circuit(self):
        src = result_circuits(2)
        c = core.read_ncff(str(src[0])); alt = swapped(c)
        self.assertNotEqual(core.to_kernel(alt), core.to_kernel(c))
        d = tmpdir()
        (d / 'a.circ.txt').write_bytes(src[0].read_bytes())
        (d / 'a-copy.circ.txt').write_bytes(src[0].read_bytes())          # byte-identical: one circuit, two files
        (d / 'a-renamed.bfx').write_text(core.to_kernel(c))                # same gate list in the other format
        (d / 'alt.bfx').write_text(core.to_kernel(alt))                    # a different circuit, same tuple
        (d / 'b.circ.txt').write_bytes(src[1].read_bytes())
        (d / 'junk.bfx').write_text('n 8\nm 8\ng 5\n')
        by_tuple, skipped = BT.scan(sorted(d.iterdir()), NIST_MODEL)
        m = c.metrics(); t = (m['A'], m['AD'], m['G'], m['GD'])
        self.assertEqual(len(by_tuple), 2)
        self.assertEqual([(e['file'].name, e['files']) for e in by_tuple[t]], [('a-copy.circ.txt', 3), ('alt.bfx', 1)])
        self.assertEqual([f.name for f, _ in skipped], ['junk.bfx'])

    def test_p11_pareto_equals_all_pairs(self):
        rng = random.Random(1)
        pub = [tuple(rng.randrange(3, 9) for _ in range(4)) for _ in range(6)]
        ts = {tuple(rng.randrange(0, 9) for _ in range(4)) for _ in range(400)}
        new, front = BT.pareto(ts, pub)
        want_new = {t for t in ts if not any(BT.le(u, t) for u in pub)}
        want = {t for t in want_new if not any(u != t and BT.le(u, t) for u in want_new)}
        self.assertEqual((set(new), set(front)), (want_new, want))

    def test_p11_one_row_per_tuple_and_the_rest_is_listed(self):
        src = result_circuits(2)
        c = core.read_ncff(str(src[0]))
        d = tmpdir(); out = d / 'best'
        (d / 'alt.bfx').write_text(core.to_kernel(swapped(c)))
        (d / 'junk.bfx').write_text('n 8\nm 8\ng 5\n')
        cands = [src[0], d / 'alt.bfx', src[1], d / 'junk.bfx']
        out.mkdir()
        stale = out / 'aes-sbox-a99-ad9-g999-gd99-xx900-1.circ.txt'; stale.write_text('old run\n')
        keepme = out / 'notes.txt'; keepme.write_text('not ours\n')
        orig = BT.candidates
        BT.candidates = lambda: cands
        try:
            buf, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = BT.main(['--out', str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(stale.exists()); self.assertIn('--clean', err.getvalue())
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                BT.main(['--out', str(out), '--clean'])
            self.assertFalse(stale.exists()); self.assertTrue(keepme.exists())
        finally:
            BT.candidates = orig
        md = (out / 'BEST.md').read_text()
        rows = [ln for ln in md.splitlines() if ln.startswith('| aes-sbox-')]
        self.assertEqual(len(rows), 2)
        m = c.metrics()
        mine = [ln for ln in rows if '-a%d-ad%d-g%d-gd%d-' % (m['A'], m['AD'], m['G'], m['GD']) in ln]
        self.assertEqual(len(mine), 1); self.assertTrue(mine[0].rstrip().endswith('| 1 |'))
        rec = json.loads((out / 'BEST.json').read_text())
        self.assertEqual(sorted(len(r['distinct_circuits']) for r in rec['rows']), [1, 2])
        self.assertEqual([Path(u['file']).name for u in rec['unreadable_files']], ['junk.bfx'])
        self.assertIn('4 files, 3 distinct circuits, 2 distinct tuples', md)
        for r in rec['rows']:                                # every table file is a verified circuit
            self.assertTrue(AC.check(out / r['file'])['ok'])
        self.assertNotIn('29 <= #AND <= 31 (published circuits here have G >= 124)', md)


class TestCli(unittest.TestCase):
    def test_p7_every_command_and_option_has_help(self):
        ap = cli.build_parser()
        sub = next(a for a in ap._actions if a.__class__.__name__ == '_SubParsersAction')
        self.assertEqual(set(sub.choices), {'run', 'pipe', 'flow', 'verify', 'start', 'list'})
        self.assertEqual({a.dest for a in sub._choices_actions}, set(sub.choices))      # one-line help for each
        for name, p in sub.choices.items():
            if name != 'list': self.assertTrue(p.description, name)
            for a in p._actions:
                if a.dest == 'files': continue
                self.assertTrue(a.help, '%s %s has no help text' % (name, a.option_strings or a.dest))
            with contextlib.redirect_stdout(io.StringIO()) as buf, self.assertRaises(SystemExit) as cm:
                ap.parse_args([name, '-h'])
            self.assertEqual(cm.exception.code, 0)
            self.assertNotIn('%(', buf.getvalue())

    def test_p7_defaults_are_the_measured_ones(self):
        ap = cli.build_parser()
        r = ap.parse_args(['run', '--target', 'present', '--model', 'bgc', '--out', 'X'])
        self.assertEqual((r.start, r.objective, r.cap_gd, r.cap_ad, r.cap_a, r.iters, r.seconds, r.seeds, r.rounds, r.pool, r.jobs, r.set),
                         ('anf', 'cost', None, None, None, 200000, 3600, '1-8', 1, 4, 0, None))
        p = ap.parse_args(['pipe', '--target', 'present', '--model', 'bgc', '--out', 'X'])
        self.assertEqual((p.start, p.objective, p.iters, p.skel_iters, p.seconds, p.seeds, p.rounds, p.pool, p.skel_share, p.jobs, p.set),
                         ('anf', 'cost', 100000, 20000, 3600, '1-8', 3, 4, 0.5, 0, None))
        f = ap.parse_args(['flow', '--target', 'present', '--model', 'bgc', '--out', 'X', '--seconds', '5'])
        self.assertEqual((f.start, f.objective, f.config, f.round_s, f.adaptive, f.no_seeded, f.no_unseeded, f.skel_set, f.set, f.seeds, f.jobs, f.cpus),
                         ('anf', 'cost', 'gate', 10.0, False, False, False, None, None, '1-4', 0, ''))
        self.assertEqual(workflow.DEFAULTS['T0'], 0.6); self.assertEqual(workflow.DEFAULTS['max_excess'], 8)

    def test_p7_clear_messages_for_bad_input(self):
        d = tmpdir()

        def fails(argv, text):
            with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as cm:
                cli.main(argv)
            self.assertIn(text, str(cm.exception.code) + err.getvalue(), argv)
        fails(['run', '--target', 'nosuch', '--model', 'bgc', '--out', str(d / 'a')], 'unknown or unreadable target')
        fails(['start', '--target', 'nosuch', '--model', 'bgc', '--out', str(d / 'a.txt')], 'present')     # names the targets
        fails(['run', '--target', 'present', '--model', 'bgc', '--objective', 'cost,zz', '--out', str(d / 'b')], 'unknown objective key')
        fails(['run', '--target', 'present', '--model', 'bgc', '--rounds', '0', '--out', str(d / 'c')], 'at least 1')
        fails(['flow', '--target', 'present', '--model', 'bgc', '--seconds', '1', '--set', 'skel.iters=0', '--out', str(d / 'e')], '--skel-set')
        self.assertFalse(any(d.iterdir()))                  # refused before a run folder is made
        for bad in ('', 'a-b', '8-1', '1,,2', '1-2-3'):
            with self.assertRaises(SystemExit, msg=bad):
                cli.parse_seeds(bad)
        self.assertEqual(cli.parse_seeds('1,3,5-7'), [1, 3, 5, 6, 7])
        for bad in (['novalue'], ['=3']):
            with self.assertRaises(SystemExit):
                cli.parse_sets(bad)
        self.assertEqual(cli.parse_sets(['mv.resub3=0', 'skel.iters=0']), {'mv.resub3': '0', 'skel.iters': '0'})

    def test_p7_verify_checks_caps_reads_bfx_and_explains(self):
        f = sorted((PKG / 'results' / 'present').glob('present-bgc-*.circ.txt'))[0]
        c = core.read_ncff(str(f)); m = c.metrics()
        d = tmpdir(); (d / 'p.bfx').write_text(core.to_kernel(c))
        r = run_cli('verify', str(f), str(d / 'p.bfx'), '--target', 'present', '--model', 'bgc', '--cap-gd', str(m['GD']))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count('caps=met'), 2)
        r = run_cli('verify', str(f), '--target', 'present', '--model', 'bgc', '--cap-gd', str(m['GD'] - 1))
        self.assertEqual(r.returncode, 1); self.assertIn('caps=NOT MET', r.stdout); self.assertIn('exceeds max', r.stdout)
        r = run_cli('verify', str(f), '--target', 'present', '--model', 'bgc')
        self.assertEqual(r.returncode, 0); self.assertNotIn('caps=', r.stdout)      # output as before without caps
        r = run_cli('verify', str(f), '--target', 'present', '--model', 'xag')        # OR is not in xag
        self.assertEqual(r.returncode, 1); self.assertIn('outside model', r.stdout)
        (d / 'bad.circ.txt').write_text('junk\n')
        r = run_cli('verify', str(d / 'bad.circ.txt'), str(f), '--target', 'present', '--model', 'bgc')
        self.assertEqual(r.returncode, 1); self.assertIn('cannot be read', r.stdout); self.assertIn('ok  ', r.stdout)
        self.assertEqual(sorted(p.name for p in d.iterdir()), ['bad.circ.txt', 'p.bfx'])

    def test_p19_explicit_not_under_the_nist_model(self):
        """`NOT t a` and `XNOR t a 0` are the same gate under the NIST model: a file with either
        verifies, with the same metrics (the NIST-format copies of our results used to FAIL here
        with 'metrics differ' although every number agreed)."""
        d = tmpdir()
        # a small circuit with a NOT, in both spellings, against its own function
        k = core.Circuit(3, 1, [(8, 0, 1), (3, 3, 3), (6, 4, 2)], [5], 'k')
        (d / 'k.fn.json').write_text(json.dumps({'n': 3, 'm': 1, 'table': k.value_table()}))
        (d / 'not.circ.txt').write_text(core.write_ncff(k, None))
        (d / 'xnor0.circ.txt').write_text(core.write_ncff(k, NIST_MODEL))
        self.assertIn('NOT t2 t1', (d / 'not.circ.txt').read_text()); self.assertIn('XNOR t2 t1 0', (d / 'xnor0.circ.txt').read_text())
        orig = cli.verify_independent
        cli.verify_independent = lambda path, target, model_path, caps=None: V.verify_file(
            str(path), (3, 1, k.value_table()), model=V.load_model(str(model_path)))
        tl = targets.load
        targets.load = lambda name: (3, 1, k.value_table(), 'k') if name == 'k' else tl(name)
        try:
            for f in ('not.circ.txt', 'xnor0.circ.txt'):
                v = cli.verify_file(d / f, 'k', 'nist')
                self.assertTrue(v['core_ok'] and v['library_ok'] and v['metrics_agree'] and v['independent_ok'], f)
                self.assertEqual((v['metrics']['G'], v['metrics']['cost']), (3, 3.0))
            v = cli.verify_file(d / 'not.circ.txt', 'k', 'xag')        # no folding without XNOR0
            self.assertTrue(v['metrics_agree'] and v['independent_ok'])
        finally:
            cli.verify_independent = orig; targets.load = tl
        nf = sorted((PKG / 'results' / 'nist-format').glob('*xxn*.circ.txt'))
        if nf:                                               # the real case, through the command line
            small = min(nf, key=lambda p: p.stat().st_size)
            r = run_cli('verify', str(small), '--target', 'aes', '--model', 'nist')
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_p7_list(self):
        r = run_cli('list')
        self.assertEqual(r.returncode, 0, r.stderr)
        for word in ('aes', 'present', 'nist', 'bgc', 'map:<name>', 'cost, g, a, gd, ad'):
            self.assertIn(word, r.stdout)


class TestCuration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import curate_aes, manifest
        cls.CU, cls.MF = curate_aes, manifest

    def test_p12_tracks_of_every_candidate_source(self):
        CU = self.CU
        self.assertEqual(CU.track_of(CU.HUB / 'long' / 'archive' / '000ceb576971.bfx'), 'hub')     # used to raise ValueError
        self.assertEqual(CU.track_of(CU.C / 'D' / 'found' / 'x.circ.txt'), 'D')
        self.assertEqual(CU.track_of(CU.C / 'E' / 'long1' / 'splice' / 'admitted' / 'ab.bfx'), 'E')
        self.assertEqual(CU.track_of(CU.RES / 'x.circ.txt'), 'results')
        self.assertEqual(CU.track_of(Path('/somewhere/else/x.circ.txt')), 'other')
        for base, g in BT.EXTRA:                             # every source best_table lists has a track
            tr = CU.track_of(base / g.replace('*', 'x'))
            self.assertTrue(tr in ('hub', 'other') or tr.startswith('study-'), tr)
        # 2026-11-15 study agents: the track is the agent id of the found/ folder
        self.assertEqual(CU.track_of(CU.STUDY / 'T1' / 'found' / 'front' / 'x.bfx'), 'study-T1')
        self.assertEqual(CU.track_of(CU.STRAT / 'H2' / 'found' / 'x.circ.txt'), 'study-H2')

    def test_p12_hub_provenance_and_lineage(self):
        CU = self.CU
        camp = tmpdir() / 'camp'; ar = camp / 'archive'; ar.mkdir(parents=True); (camp / 'runs').mkdir()

        def side(i, op, parents, t, **st):
            (ar / (i + '.json')).write_text(json.dumps({
                'id': i, 'A': t[0], 'AD': t[1], 'G': t[2], 'GD': t[3], 'parents': parents, 'operator': op,
                'operator_settings': st, 'seed': 7 if parents else None, 'run_id': 'r1-' + op if parents else None,
                'code_version': 'abc+def', 'cpu_s': 9.5, 'wall_s': 9.0, 't_admit': 100.0}))
        side('aaaa', 'seed', [], (32, 6, 113, 27), file='/x/nist/a.circ.txt')
        side('bbbb', 'ingest', [], (33, 4, 108, 20), file='/x/found/b.circ.txt')
        side('cccc', 'join', ['aaaa', 'bbbb'], (32, 5, 110, 22), objective='a,ad,cost,gd', seconds=60.0, front='aaaa', back='bbbb', LX=2, LY=3)
        side('dddd', 'pull', ['cccc'], (31, 5, 112, 22), objective='a,ad,cost,gd', seconds=90.0, caps={'A': 31, 'AD': 5, 'GD': 22},
             lowered='A', t_last_improvement=12.5)
        (camp / 'runs' / 'r1-pull.json').write_text(json.dumps({'command': ['python3', 'op_pull.py', '--in', 'cccc', '--seed', '7']}))
        (ar / 'dddd.bfx').write_text('n 8\nm 8\ng 0\no 0 1 2 3 4 5 6 7\n')
        s = CU.describe_hub(ar / 'dddd.bfx', {'A': 31, 'AD': 5, 'G': 112, 'GD': 22})
        self.assertEqual(s['mech_short'], 'pull'); self.assertIn('hub operator pull', s['mechanism'])
        self.assertEqual(s['command'], 'python3 op_pull.py --in cccc --seed 7')
        self.assertEqual((s['caps'], s['seeds'], s['objective']), ({'GD': 22, 'AD': 5, 'A': 31}, [7], 'a,ad,cost,gd'))
        self.assertTrue(s['start'].endswith('archive/cccc.bfx'))
        self.assertEqual(s['time_to_result_s']['within_job_s'], 12.5)
        self.assertEqual(s['campaign_sidecar_src'], ar / 'dddd.json')
        join = s['parents'][0]
        self.assertEqual((join['id'], join['operator'], join['metrics_A_AD_G_GD']), ('cccc', 'join', [32, 5, 110, 22]))
        self.assertEqual([(p['id'], p['file']) for p in join['parents']], [('aaaa', '/x/nist/a.circ.txt'), ('bbbb', '/x/found/b.circ.txt')])
        # the fields manifest.py reads from a curated summary are all there
        for k in ('command', 'seeds', 'iters', 'rounds', 'objective', 'caps', 'start', 'mechanism', 'reproduction', 'run_record', 'code_version'):
            self.assertIn(k, s)
        # a long ancestry is cut, and says where
        prev = 'dddd'
        for k in range(8):
            side('e%03d' % k, 'polish', [prev], (31, 5, 112 - k, 22)); prev = 'e%03d' % k
        lin = CU.hub_lineage(ar, prev); depth = 0
        while 'parents' in lin: lin = lin['parents'][0]; depth += 1
        self.assertEqual(depth, 4); self.assertIn('parents_not_expanded', lin)
        self.assertEqual(CU.hub_lineage(ar, 'zzzz'), {'id': 'zzzz', 'unresolved': True})

    def test_p13_one_circuit_one_track(self):
        """The selection is by distinct gate list: a track's circuit that the hub ingested (same gates,
        other file) is one entry whose file is the first in candidate order."""
        src = result_circuits(1)[0]
        c = core.read_ncff(str(src)); d = tmpdir()
        (d / 'F-found.circ.txt').write_bytes(src.read_bytes())
        (d / 'hub-archive.bfx').write_text(core.to_kernel(c))
        by_tuple, _ = BT.scan([d / 'F-found.circ.txt', d / 'hub-archive.bfx'], NIST_MODEL)
        (ents,) = by_tuple.values()
        self.assertEqual([(e['file'].name, e['files']) for e in ents], [('F-found.circ.txt', 2)])
        self.assertIn("for ent in by_tuple[t]", (PKG / 'campaigns' / 'curate_aes.py').read_text())

    def test_p14_nist_format_names_do_not_overwrite(self):
        MF = self.MF; d = tmpdir(); w = {}
        self.assertEqual(MF.nist_format_name(d, 'aes-sbox-a32-ad4-g116-gd20-xx84-30', 'one\n', w), 'aes-sbox-a32-ad4-g116-gd20-xx84-30')
        self.assertEqual(MF.nist_format_name(d, 'aes-sbox-a32-ad4-g116-gd20-xx84-30', 'one\n', w), 'aes-sbox-a32-ad4-g116-gd20-xx84-30')
        self.assertEqual(MF.nist_format_name(d, 'aes-sbox-a32-ad4-g116-gd20-xx84-30', 'two\n', w), 'aes-sbox-a32-ad4-g116-gd20-xx84-30-v2')
        self.assertEqual(MF.nist_format_name(d, 'aes-sbox-a32-ad4-g116-gd20-xx84-30', 'three\n', w), 'aes-sbox-a32-ad4-g116-gd20-xx84-30-v3')
        self.assertEqual(sorted((p.name, p.read_text()) for p in d.iterdir()),
                         [('aes-sbox-a32-ad4-g116-gd20-xx84-30-v2.circ.txt', 'two\n'),
                          ('aes-sbox-a32-ad4-g116-gd20-xx84-30-v3.circ.txt', 'three\n'),
                          ('aes-sbox-a32-ad4-g116-gd20-xx84-30.circ.txt', 'one\n')])
        sys.path.insert(0, str(REPO / 'nonlinear'))
        from boolcirc import metrics as BM                   # the third counter still reads the suffixed name
        self.assertEqual(BM.name_metrics('aes-sbox-a32-ad4-g116-gd20-xx84-30-v2.circ.txt')['G'], 116)

    def test_p20_start_kind_of_a_file_outside_the_repository(self):
        MF = self.MF; d = tmpdir(); (d / 'pool.bfx').write_text('n 2\nm 1\ng 1\n8 0 1\no 2\n')
        info = MF.start_info(str(d / 'pool.bfx'))
        self.assertEqual(info['kind'], 'campaign circuit (outside the repository)')      # was 'BoolFlux result'
        self.assertEqual(info['sha256'], MF.sha((d / 'pool.bfx').read_bytes()))
        res = sorted((PKG / 'results' / 'present').glob('*.circ.txt'))[0]
        for spelled in (str(res.relative_to(REPO)), str(res)):
            self.assertEqual(MF.start_info(spelled)['kind'], 'BoolFlux result')
        self.assertEqual(MF.start_info('anf')['kind'][:9], 'naive ANF')
        self.assertNotIn('kind', MF.start_info('pool hash 0123 (splice)'))

    def test_p21_reproduction_wording_follows_the_evidence(self):
        """'Deterministic' is stated for the run's own snapshot; the current code only when the source
        is unchanged or a check says so (L2: 28/4/133/20 replays with its binary, ends at 134 today)."""
        MF = self.MF
        base = {'class': 'deterministic', 'code_at_run': {'code_sha256_12': 'b0e5', 'snapshot': '~/run', 'head_same_source': False,
                                                         'source_files_changed_since': ['bfx.c', 'cli.py']}}
        t = MF.reproduction_text(base)
        self.assertIn("with the run's own snapshot (~/run/src and bin, code b0e5)", t)
        self.assertIn('NOT known to give this circuit', t); self.assertIn('bfx.c, cli.py', t)
        self.assertNotIn('so the command gives the same circuit', t)
        same = dict(base, code_at_run=dict(base['code_at_run'], head_same_source=True))
        self.assertIn('unchanged since, so the command gives the same circuit at the current code', MF.reproduction_text(same))
        chk = dict(base, checked={'snapshot': {'utc': '2026-11-15T03:00:00Z', 'identical': True},
                                  'head': {'utc': '2026-11-15T03:00:00Z', 'identical': False, 'code': '9124', 'result_A_AD_G_GD': [28, 4, 134, 20]}})
        t = MF.reproduction_text(chk)
        self.assertIn('Checked 2026-11-15, snapshot replay: identical circuit', t)
        self.assertIn('Checked 2026-11-15, current code (9124): DIFFERENT result [28, 4, 134, 20]', t)
        gone = {'class': 'deterministic', 'code_at_run': {'code_sha256_12': 'b0e5', 'snapshot': None, 'head_same_source': None}}
        self.assertIn('cannot be replayed', MF.reproduction_text(gone))
        self.assertEqual(MF.reproduction_text({'class': 'one-off', 'text': 'one-off: x'}), 'one-off: x')
        # code_at_run compares the snapshot with the current source, file by file
        run = tmpdir(); (run / 'src').mkdir(); (run / 'bin').mkdir(); (run / 'bin' / 'bfx').write_bytes(b'binary')
        for n in MF.SNAP_FILES:
            (run / 'src' / n).write_bytes((PKG / ('kernel/' + n if n.endswith('.c') else n)).read_bytes())
        car = MF.code_at_run(run, 'abc')
        self.assertEqual((car['head_same_source'], car['source_files_changed_since'], car['code_sha256_12']), (True, [], 'abc'))
        self.assertEqual(car['binary_sha256'], MF.sha(b'binary'))
        (run / 'src' / 'bfx.c').write_text('/* older kernel */\n'); (run / 'src' / 'workflow.py').unlink()
        car = MF.code_at_run(run, 'abc')
        self.assertEqual((car['head_same_source'], car['source_files_changed_since']), (False, ['bfx.c', 'workflow.py']))
        self.assertEqual(MF.code_at_run(None, 'abc')['head_same_source'], None)
        # the committed manifest no longer promises more than that
        man = json.loads((PKG / 'results' / 'MANIFEST.json').read_text())
        for e in man['entries']:
            self.assertNotIn('so the command gives the same circuit"', json.dumps(e.get('reproduction')))
            self.assertIn(e['reproducibility']['class'], ('deterministic', 'one-off', 'construction', 'unknown'), e['file'])
            if e['reproducibility']['class'] == 'deterministic':
                self.assertIn('code_at_run', e['reproducibility'], e['file'])
                if e['reproducibility']['code_at_run']['head_same_source'] is not True and 'head' not in (e['reproducibility'].get('checked') or {}):
                    self.assertIn('NOT known', e['reproduction'], e['file'])

    def test_p22_caps_not_met_is_said(self):
        MF = self.MF
        e = {'metrics': {'A': 32, 'AD': 5, 'G': 104, 'GD': 29}, 'caps': {'GD': None, 'AD': None, 'A': None},
             'job_caps': {'GD': None, 'AD': None, 'A': 31}, 'mechanism': "polish: gate kernel under caps {'A': 31}"}
        MF.caps_status(e)
        self.assertFalse(e['caps_met']); self.assertIn('CAPS NOT MET by this job (cap A 31, circuit A 32)', e['mechanism'])
        m1 = e['mechanism']; MF.caps_status(e); self.assertEqual(e['mechanism'], m1)       # said once
        ok = {'metrics': {'A': 28, 'AD': 4, 'G': 133, 'GD': 20}, 'caps': {'GD': 20, 'AD': 4, 'A': 28}, 'mechanism': 'gate kernel'}
        MF.caps_status(ok)
        self.assertTrue(ok['caps_met']); self.assertEqual(ok['mechanism'], 'gate kernel')
        man = json.loads((PKG / 'results' / 'MANIFEST.json').read_text())
        for x in man['entries']:
            self.assertEqual('CAPS NOT MET' in x['mechanism'], not x['caps_met'], x['file'])
        # the two cap misses of the 11-14 push stay flagged; later curations may add more (e.g. the
        # hub's depth pulls that ended above their GD cap, L1's "infeasible-end" circuits)
        missed = {Path(x['file']).name for x in man['entries'] if not x['caps_met']}
        self.assertLessEqual({'aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt',
                              'aes-nist-E-pull-g135-a29-gd17-ad5.circ.txt'}, missed)

    def test_p23_code_version_of_curated_results_says_when_it_was_taken(self):
        MF = self.MF
        import hashlib
        blob = MF.git_show(MF.SCRIPTS_COMMIT, 'nonlinear/boolflux/strategies/E/splice2.py')
        self.assertIsNotNone(blob)
        e = {'curated_utc': '2026-11-14T17:54:30Z', 'reproduction': 'deterministic construction from its two parents; not re-run',
             'code_version': {'kernel': 'kernel/bfx.c at git 0659eb9',
                              'strategies/E (uncommitted, sha256 now)': {'splice2.py': hashlib.sha256(blob).hexdigest()[:12],
                                                                         'common.py': '000000000000', 'nosuch.py': 'abc'}}}
        MF.curated_code_record(e)
        self.assertIn('taken at curation time (2026-11-14T17:54:30Z), not at run time', e['code_version_recorded'])
        self.assertEqual(e['code_version_commit_check'], {
            'strategies/E/splice2.py': 'identical to commit 377b03f', 'strategies/E/common.py': 'differs from commit 377b03f',
            'strategies/E/nosuch.py': 'not in commit 377b03f'})
        self.assertEqual(e['reproducibility'], {'class': 'construction', 'text': e['reproduction'], 'code_recorded_at_run': False})
        hub = {'reproduction': 'one-off: hub job', 'code_version': {'hub (git commit + hash of uncommitted changes)': '97abda7+d317'}}
        MF.curated_code_record(hub)
        self.assertTrue(hub['code_version_recorded'].startswith('at run time')); self.assertTrue(hub['reproducibility']['code_recorded_at_run'])

    def test_p24_check_repro_replays_a_run(self):
        """--check-repro on a real (small) run: the snapshot replay and the current-code replay both
        give the recorded circuit; a different recorded circuit is reported as DIFFERENT."""
        MF = self.MF
        out = tmpdir(prefix='r5rep-')
        r = run_cli('run', '--target', 'present', '--model', 'bgc', '--iters', '3000', '--seeds', '1-2', '--jobs', '1', '--out', str(out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = json.loads((out / 'summary.json').read_text())
        origin = s['best']['origin'].split()                 # 'seed S round R'
        self.assertEqual(origin[0], 'seed', s['best']['origin'])
        entry = {'file': str(out / 'best.circ.txt'), 'sha256': 'x', 'run_record': str(out), 'model': 'bgc', 'objective': 'cost',
                 'caps': s['caps'], 'iters': 3000, 'command': s['command'], 'code_sha256_12': s['code_sha256_12'],
                 'time_to_result_s': {'job': 'r%s-s%s' % (origin[3], origin[1])}, 'metrics': s['best']['metrics']}
        tmp = tmpdir()
        for mode in ('snapshot', 'head'):
            res = MF.replay(entry, mode, tmp)
            self.assertIs(res['identical'], True, res); self.assertTrue(res['identical_to_job_file'], res)
        other = sorted((PKG / 'results' / 'present').glob('present-gc6-*.circ.txt'))[0]
        res = MF.replay(dict(entry, file=str(other)), 'snapshot', tmp)
        self.assertIs(res['identical'], False)
        res = MF.replay(dict(entry, run_record=str(tmp / 'nowhere')), 'snapshot', tmp)
        self.assertIsNone(res['identical']); self.assertIn('missing', res['error'])
        car = MF.code_at_run(out, s['code_sha256_12'])
        self.assertTrue(car['head_same_source'])              # the run was just made from this source
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'manifest.py'), '--check-repro'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_p15_collect_ranks_like_everything_else(self):
        """'gd,cost': a result with a worse first key is no gain, however much the second improves
        (the weighted sum 1*GD + 1e-4*cost called it an improvement)."""
        f = sorted((PKG / 'results' / 'present').glob('present-bgc-*.circ.txt'))[0]
        m = core.read_ncff(str(f)).metrics(core.Model.load('bgc'))
        d = tmpdir()

        def collect(start_metrics, objective_spec):
            run = tmpdir(prefix='r5run-')
            (run / 'summary.json').write_text(json.dumps({
                'target': 'present', 'model': 'bgc', 'objective': objective_spec, 'caps': {'GD': None, 'AD': None, 'A': None},
                'start': 'anf', 'start_metrics': start_metrics, 'seeds': [1], 'iters': 1, 'runs': [],
                'command': 'test', 'best': {'file': str(f)}}))
            r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'collect.py'), str(run)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.splitlines()[-1]
        base = {'G': m['G'], 'A': m['A'], 'AD': m['AD']}
        self.assertIn('no gain', collect(dict(base, GD=m['GD'] - 1, cost=m['cost'] + 30000), 'gd,cost'))
        self.assertNotIn('no gain', collect(dict(base, GD=m['GD'], cost=m['cost'] + 1), 'gd,cost'))
        self.assertNotIn('no gain', collect(dict(base, GD=m['GD'] + 1, cost=m['cost']), 'cost,gd'))
        self.assertIn('no gain', collect(dict(base, GD=m['GD'], cost=m['cost']), 'cost,gd'))

    def test_p16_tools_answer_help_without_running(self):
        for tool in ('verify_all.py', 'manifest.py', 'curate_aes.py', 'collect.py', 'best_table.py'):
            r = subprocess.run([sys.executable, str(PKG / 'campaigns' / tool), '-h'], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, tool); self.assertIn(tool, r.stdout)
            self.assertGreater(len(r.stdout), 200, tool)
        for tool in ('verify_all.py', 'manifest.py', 'curate_aes.py', 'collect.py'):
            r = subprocess.run([sys.executable, str(PKG / 'campaigns' / tool), '--no-such-option'], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 2, tool)
        for tool in ('bench.py', 'analyze.py', 'make_plan.py', 'pooled.py', 'rebuild_penalty.py', 'show_trace.py'):
            r = subprocess.run([sys.executable, str(PKG / 'bench' / tool), '-h'], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, tool); self.assertIn(tool, r.stdout)
            r = subprocess.run([sys.executable, str(PKG / 'bench' / tool)], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 2, tool)          # used to be an IndexError traceback

    def test_targets_without_a_table_are_unknown(self):
        self.assertEqual(len(set(targets.names())), len(targets.names()))
        for nm in targets.names():
            n, m, table, _ = targets.load(nm)
            self.assertEqual(len(table), 1 << n, nm)
        with self.assertRaises(KeyError):
            targets.load('no-such-target')



class TestBuildAndSeeds(unittest.TestCase):
    def test_p25_kernel_build_is_atomic_with_its_own_temporary_name(self):
        """cli.build_kernel / cli.snapshot: gcc writes a temporary file of its own in the target's folder,
        which is renamed into place; concurrent builders never share a name or expose a partial file."""
        import threading
        import time as _t
        from unittest import mock
        d = tmpdir(prefix='r5bk-'); seen = []; lock = threading.Lock()

        def fake_gcc(cmd, check=True):
            out = cmd[cmd.index('-o') + 1]
            with lock: seen.append(out)
            Path(out).write_text('partial')
            _t.sleep(0.2)
            Path(out).write_text('complete %s' % Path(cmd[-2]).name)
            return subprocess.CompletedProcess(cmd, 0)
        old = cli.KBIN, cli.SBIN
        try:
            cli.KBIN, cli.SBIN = d / 'bfx', d / 'skel'
            with mock.patch.object(cli.subprocess, 'run', fake_gcc):
                th = [threading.Thread(target=cli.build_kernel) for _ in range(3)]
                for x in th: x.start()
                for x in th: x.join()
        finally:
            cli.KBIN, cli.SBIN = old
        self.assertEqual(len(seen), len(set(seen)))                       # one temporary name per build
        for out in seen:
            self.assertEqual(Path(out).parent, d)
            self.assertNotIn(Path(out).name, ('bfx', 'skel', 'bfx.tmp', 'skel.tmp'))
        self.assertEqual((d / 'bfx').read_text(), 'complete bfx.c')
        self.assertEqual((d / 'skel').read_text(), 'complete skel.c')
        self.assertEqual(sorted(x.name for x in d.iterdir()), ['bfx', 'skel'])   # nothing left behind

        def failing(cmd, check=True):
            Path(cmd[cmd.index('-o') + 1]).write_text('partial')
            raise subprocess.CalledProcessError(1, cmd)
        with mock.patch.object(cli.subprocess, 'run', failing):
            self.assertRaises(subprocess.CalledProcessError, cli.compile_kernel, cli.KDIR / 'bfx.c', d / 'other')
        self.assertEqual(sorted(x.name for x in d.iterdir()), ['bfx', 'skel'])
        cli.compile_kernel(cli.KDIR / 'skel.c', d / 'real')                # the real compiler, once
        self.assertTrue(os.access(d / 'real', os.X_OK))
        self.assertEqual(sorted(x.name for x in d.iterdir()), ['bfx', 'real', 'skel'])

    def test_p26_kernel_seeds_are_collision_free_and_shared(self):
        """v2 = seed + round x 2^32 in cli run/pipe/flow and workflow (bench); the old formulas collided
        ((1, 1) = (1001, 0) in run, (1, 1000) = (2, 0) in flow) and stay reachable."""
        ks = workflow.kernel_seed
        self.assertNotEqual(ks(1, 1), ks(1001, 0))
        self.assertNotEqual(ks(1, 1000), ks(2, 0))
        pairs = [(s, r) for s in range(1200) for r in (0, 1, 2, 3, 999, 1000, 1001)]
        self.assertEqual(len({ks(s, r) for s, r in pairs}), len(pairs))
        top = (1 << 32) - 1
        self.assertEqual(len({ks(s, r) for s in (0, 1, top) for r in (0, 1, top)}), 9)
        self.assertLess(ks(top, top), 1 << 64)                              # the kernel seed is a u64
        for s in range(50): self.assertEqual(ks(s, 0), s)                   # round 0: the seed, as before in run
        self.assertRaises(ValueError, ks, 1 << 32, 0); self.assertRaises(ValueError, ks, 0, 1 << 32)
        self.assertRaises(ValueError, ks, -1, 0); self.assertRaises(ValueError, ks, 1, 1, 'nope')
        self.assertEqual(ks(1, 1, 'legacy-run'), ks(1001, 0, 'legacy-run'))        # the old collision, documented
        self.assertEqual(ks(1, 1000, 'legacy-flow'), ks(2, 0, 'legacy-flow'))
        self.assertEqual((ks(7, 2, 'legacy-run'), ks(7, 2, 'legacy-flow')), (2007, 7002))
        # cli.py run writes and records the same seeds; --seed-scheme legacy gives the old ones
        for scheme, want in (('v2', lambda s, r: s + r * (1 << 32)), ('legacy', lambda s, r: s + 1000 * r)):
            out = tmpdir(prefix='r5seed-')
            r = run_cli('run', '--target', 'present', '--model', 'bgc', '--iters', '300', '--seeds', '1-2', '--rounds', '2',
                        '--jobs', '1', '--seed-scheme', scheme, '--out', str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            s = json.loads((out / 'summary.json').read_text())
            self.assertEqual(s['seed_scheme'], 'v2' if scheme == 'v2' else 'legacy-run')
            self.assertEqual(len(s['runs']), 4)
            for job in s['runs']:
                self.assertEqual(job['kernel_seed'], want(job['seed'], job['round']), job)
                cfg = dict(ln.split(None, 1) for ln in (out / ('%s.cfg' % job['tag'])).read_text().splitlines() if ln.strip())
                self.assertEqual(int(cfg['seed']), job['kernel_seed'])
        # workflow.search (cli flow, bench) asks the same function for every round
        bindir = cli.build_kernel().parent
        got = []; real = workflow.kernel_cfg
        def spy(path, start_path, out_path, model, run, seconds, seed, extra, iters=None):
            got.append(seed); return real(path, start_path, out_path, model, run, seconds, seed, extra, iters)
        workflow.kernel_cfg = spy
        try:
            for scheme in ('v2', 'legacy-flow'):
                got.clear()
                run = {'target': 'present', 'model': 'bgc', 'objective': 'cost', 'caps': {}, 'start': 'anf', 'seconds': 2.5,
                       'seed': 3, 'config': 'full', 'round_s': 0.4, 'skel_set': {'iters': 0}, 'seed_scheme': scheme}
                workflow.search(run, bindir, tmpdir(prefix='r5wf-'))
                self.assertGreaterEqual(len(got), 2, got)
                self.assertEqual(got, [ks(3, r, scheme) for r in range(len(got))])
        finally:
            workflow.kernel_cfg = real
        # no second copy of a formula is left in the two modules
        for f in ('cli.py', 'workflow.py'):
            src = (PKG / f).read_text()
            body = src.split('def kernel_seed', 1)[0] + src.split('def kernel_seed', 1)[-1].split('\ndef ', 1)[-1] if 'def kernel_seed' in src else src
            self.assertNotIn('1000 * rnd', body, f); self.assertNotIn("* 1000 + rnd", body, f)
        r = run_cli('run', '-h'); self.assertIn('--seed-scheme', r.stdout)
        r = run_cli('flow', '-h'); self.assertIn('--seed-scheme', r.stdout)


if __name__ == '__main__':
    unittest.main()
