"""Tests of boolcirc: python3 -m unittest discover -s circuits/boolcirc/tests -t circuits"""
import pathlib
import unittest

from boolcirc import gf2, metrics as M, ncff, skeleton as S, truth

ROOT = pathlib.Path(__file__).resolve().parents[2]      # circuits/
NIST = ROOT.parent / 'search' / 'nonlinear' / 'seeds'

SMALL = """
% a comment
begin circuit small
Inputs: x0:x2
Outputs: y0 y1 y2
GateSyntax: GateName Output Inputs
begin SLP
XOR t1 x0 x1      % trailing comment
AND a1 t1 x2
XNOR y0 a1 x0
NOT y1 t1
OR t2 x1 x2
NAND t3 t2 x0
NOR y2 t3 a1
AND dead x0 x1
end SLP
end circuit
"""


def small():
    return ncff.parse(SMALL, 'small')[0]


class ParseTests(unittest.TestCase):
    def test_expand_names(self):
        self.assertEqual(ncff.expand_names('U0:U3 S7 t1:t2'),
                         ['U0', 'U1', 'U2', 'U3', 'S7', 't1', 't2'])
        with self.assertRaises(ncff.FormatError):
            ncff.expand_names('U3:U1')

    def test_parse_and_round_trip(self):
        c = small()
        self.assertEqual(c.inputs, ['x0', 'x1', 'x2'])
        self.assertEqual([g.op for g in c.gates],
                         ['XOR', 'AND', 'XNOR', 'NOT', 'OR', 'NAND', 'NOR', 'AND'])
        self.assertEqual(c.gates[3].args, ('t1',))
        self.assertEqual(c.comments, ['a comment'])
        again = ncff.parse(ncff.format_circuit(c, c.comments), 'again')[0]
        self.assertEqual(again.gates, c.gates)
        self.assertEqual((again.inputs, again.outputs), (c.inputs, c.outputs))
        self.assertEqual(again.comments, c.comments)
        legacy = ncff.parse(ncff.format_circuit(c, style='2020'), 'legacy')[0]
        self.assertEqual(legacy.gates, c.gates)

    def test_comments_and_markers(self):
        text = ('% file note\nbegin circuit c\n  % Tally of gates (1): 1 XOR\nInputs: x0 x1\n'
                'Outputs: y\nbegin SLP\nXOR y x0 x1 # 50% done\nend SLP\nend circuit\n'
                'begin circuit d\n% second\nInputs: x0\nOutputs: x0\nbegin SLP\nend SLP\nend circuit')
        c, d = ncff.parse(text)
        self.assertEqual(c.comments, ['file note', 'Tally of gates (1): 1 XOR'])
        self.assertEqual(d.comments, ['second'])
        self.assertEqual(c.gates[0].args, ('x0', 'x1'))
        self.assertEqual(ncff._strip('XOR a b c # 50% done'), ('XOR a b c', '50% done'))
        odd = ncff.Circuit('n', ['x-1', 'x-2', 'u1', 'u2'], ['u2'], [])
        back = ncff.parse(ncff.format_circuit(odd))[0]
        self.assertEqual(back.inputs, odd.inputs)

    def test_validation(self):
        bad = ['begin circuit b', 'Inputs: x0 x1', 'Outputs: y', 'begin SLP', '%s',
               'end SLP', 'end circuit']
        for line, msg in [('XOR y x0 x9', 'before it is defined'),
                          ('XOR x0 x0 x1', 'twice'),
                          ('MUX y x0 x1', 'unknown gate'),
                          ('NOT y x0 x1', 'operand'),
                          ('XOR y x0', 'operand')]:
            with self.assertRaisesRegex(ncff.FormatError, msg):
                ncff.parse('\n'.join(bad) % line)
        with self.assertRaisesRegex(ncff.FormatError, 'never assigned'):
            ncff.parse('\n'.join(bad) % 'XOR t x0 x1')
        with self.assertRaisesRegex(ncff.FormatError, 'constant name'):
            ncff.parse('\n'.join(bad) % 'XOR 2 x0 x1\nXOR y 2 x0')
        with self.assertRaisesRegex(ncff.FormatError, 'missing end SLP'):
            ncff.parse('begin circuit b\nInputs: x0\nOutputs: x0\nbegin SLP\nend circuit')


class TruthTests(unittest.TestCase):
    def test_input_tables_and_anf(self):
        t = truth.input_tables(3)
        self.assertEqual(t, [0b10101010, 0b11001100, 0b11110000])
        self.assertEqual(truth.degree(t[0] & t[1], 3), 2)
        self.assertEqual(truth.degree(t[0] ^ t[2], 3), 1)
        self.assertEqual(truth.degree(truth.all_ones(3), 3), 0)
        self.assertEqual(truth.anf(t[0] & t[1] ^ t[2], 3), (1 << 0b011) | (1 << 0b100))

    def test_aes_sbox(self):
        s = truth.aes_sbox()
        self.assertEqual([s.value(x) for x in (0, 1, 0x53, 0xFF)], [0x63, 0x7C, 0xED, 0x16])
        inv = truth.aes_inv_sbox()
        self.assertTrue(all(inv.value(s.value(x)) == x for x in range(256)))
        self.assertTrue(all(truth.degree(t, 8) == 7 for t in s.outputs))

    def test_aes_sbox_sel(self):
        sel = truth.aes_sbox_sel()
        s, inv = truth.aes_sbox(), truth.aes_inv_sbox()
        self.assertEqual((sel.n_inputs, sel.n_outputs), (9, 8))
        self.assertTrue(all(sel.value(x) == s.value(x) and sel.value(256 + x) == inv.value(x) for x in range(256)))
        fj = NIST / 'aes-sbox-sel' / 'aes-sbox-sel.fn.json'
        if fj.exists():                      # NIST's own table of the function
            import json
            self.assertEqual(sel.table(), json.loads(fj.read_text())['table'])

    def test_alt_rank(self):
        n = 4
        x = truth.input_tables(n)
        self.assertEqual(truth.alt_rank(x[0] & x[1], n), 2)
        self.assertEqual(truth.alt_rank((x[0] & x[1]) ^ (x[2] & x[3]), n), 4)
        self.assertEqual(truth.alt_rank((x[0] & x[1]) ^ (x[0] & x[2]), n), 2)   # x0(x1+x2)
        self.assertEqual(truth.alt_rank(x[0] ^ x[3], n), 0)
        inv = truth.gf_inverse(4, 0x13)
        self.assertTrue(all(truth.degree(t, n) == 3 for t in inv.outputs))

    def test_gf16_inverse(self):
        f = truth.gf_inverse(4, 0x13)
        for x in range(1, 16):
            self.assertEqual(truth.gf_mul(x, f.value(x), 4, 0x13), 1)
        self.assertEqual(f.value(0), 0)
        self.assertEqual(max(truth.degree(t, 4) for t in f.outputs), 3)

    def test_evaluate_small(self):
        c = small()
        v = truth.evaluate(c)
        x0, x1, x2 = truth.input_tables(3)
        ones = truth.all_ones(3)
        self.assertEqual(v['y0'], ((x0 ^ x1) & x2) ^ x0 ^ ones)
        self.assertEqual(v['y1'], x0 ^ x1 ^ ones)
        self.assertEqual(v['y2'], (((x1 | x2) & x0 ^ ones) | ((x0 ^ x1) & x2)) ^ ones)

    def test_match_orders(self):
        # y = x reversed: equivalent to identity under msb/lsb mixing only
        text = ('begin circuit rev\nInputs: x0:x1\nOutputs: x1 x0\nbegin SLP\nend SLP\n'
                'end circuit')
        c = ncff.parse(text)[0]
        ident = truth.Function.from_callable('id', 2, 2, lambda x: x)
        self.assertEqual(sorted(truth.match(c, ident)), [('lsb', 'msb'), ('msb', 'lsb')])


class MetricsTests(unittest.TestCase):
    def test_small_metrics(self):
        m = M.metrics(small())
        # depths: t1 1, a1 2, y0 3, y1 2, t2 1, t3 2, y2 3, dead 1; AND depths: a1 1, t2 1,
        # t3 2, y2 3, dead 1
        self.assertEqual((m.and_count, m.and_depth, m.gates, m.gate_depth), (5, 3, 8, 3))
        self.assertEqual((m.xor, m.xnor, m.not_count, m.other), (1, 1, 1, {'OR': 1, 'NAND': 1, 'NOR': 1}))
        self.assertEqual(m.dead, ['dead'])
        self.assertEqual(m.gate_levels, [3, 3, 2])
        self.assertEqual(m.and_levels, [3, 1, 1])
        self.assertEqual(m.live_gate_depth, 3)

    def test_names(self):
        self.assertEqual(M.name_metrics('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt'),
                         {'A': 32, 'AD': 5, 'G': 104, 'GD': 30, 'XX': 72, 'XNOR': 5, 'style': '2026'})
        self.assertEqual(M.name_metrics('aes-sbox-fwd-g113-a32-d27-ad6.slp'),
                         {'A': 32, 'AD': 6, 'G': 113, 'GD': 27, 'style': '2020'})
        self.assertIsNone(M.name_metrics('aes-mixcols-xor97-depth3.circ.txt'))
        m = M.metrics(small())
        self.assertEqual(M.check_name('x' + m.name_suffix() + '.circ.txt', m), [])
        self.assertEqual(len(M.check_name('x-a4-ad3-g8-gd3-xx2-1.circ.txt', m)), 1)

    def test_header_tallies(self):
        c = small()
        c.comments = ['Tally of gates (8): 2 AND; 1 XOR; 1 XNOR; 1 NOT; 1 OR; 1 NAND; 1 NOR',
                      'Gate depth 3; AND depth 3',
                      'Gates per gate level: 3 3 2', 'AND gates per AND level: 3 1 1']
        m = M.metrics(c)
        self.assertEqual(M.check_tallies(c, m), [])
        c.comments[1] = 'Gate depth 4; AND depth 3'
        self.assertEqual(len(M.check_tallies(c, m)), 1)
        c.comments[0] = 'Tally of gates (8): 2 AND gates; junk'
        self.assertEqual(M.header_tallies(c)['by_op'], {'AND': 2})
        c.comments[0] = 'Tally of gates (8): 2 AND gates; junk'
        self.assertEqual(M.header_tallies(c)['by_op'], {'AND': 2})


class GF2Tests(unittest.TestCase):
    def test_rank_solve_kernel(self):
        vs = [0b0011, 0b0110, 0b0101, 0b1000]
        self.assertEqual(gf2.rank(vs), 3)
        self.assertTrue(gf2.in_span(vs, 0b0101))
        self.assertFalse(gf2.in_span(vs, 0b0001))
        self.assertIsNone(gf2.solve(vs, 0b1111))
        m = gf2.solve(vs, 0b1101)
        self.assertIsNotNone(m)
        acc = 0
        for k, v in enumerate(vs):
            if m >> k & 1:
                acc ^= v
        self.assertEqual(acc, 0b1101)
        rel = gf2.kernel(vs)
        self.assertEqual(len(rel), 1)
        acc = 0
        for k, v in enumerate(vs):
            if rel[0] >> k & 1:
                acc ^= v
        self.assertEqual(acc, 0)

    def test_reduce_is_canonical_and_linear(self):
        # rows 0b1100 and 0b0110: an echelon basis where the lower pivot bit (bit 2) is set in
        # the upper row, the case where a stop-at-first-gap reduction is not canonical.
        b = gf2.Basis([0b1100, 0b0110])
        u, v = 0b1011, 0b1011 ^ 0b0110          # same coset
        self.assertEqual(b.reduce(u), b.reduce(v))
        self.assertEqual(b.reduce(u ^ 0b0001), b.reduce(u) ^ b.reduce(0b0001))
        for p in b.rows:
            self.assertFalse(b.reduce(u) >> p & 1)
        self.assertEqual(b.rank_modulo([0b1100, 0b0001, 0b1101]), 1)
        self.assertTrue(b.contains(0b1010))

    def test_nullspace(self):
        rows = [0b0111, 0b0101]                  # x0+x1+x2 = 0, x0+x2 = 0 over 4 columns
        ns = gf2.nullspace(rows, 4)
        self.assertEqual(len(ns), 2)
        for x in ns:
            for r in rows:
                self.assertEqual(bin(r & x).count('1') % 2, 0)
        self.assertEqual(gf2.rank(ns), 2)


class SkeletonTests(unittest.TestCase):
    def test_skeleton_matches_gates(self):
        c = small()
        sk = S.skeleton(c)
        self.assertEqual(sk.n_ands, 5)
        self.assertEqual(sk.and_names, ['a1', 't2', 't3', 'y2', 'dead'])
        self.assertEqual(sk.tables(), truth.truth_tables(c))
        self.assertEqual(sk.describe(sk.forms['y0']), 'x0 + a1 + 1')
        self.assertEqual(sk.and_depth[0], 2)
        self.assertEqual(sk.and_level, [1, 1, 2, 3, 1])
        rebuilt = S.circuit_from_skeleton(sk)
        self.assertEqual(truth.truth_tables(rebuilt), truth.truth_tables(c))
        self.assertEqual(sk.degenerate(), [])
        self.assertEqual(M.metrics(rebuilt).not_count, 0)   # complements are XNOR-with-0
        self.assertEqual(M.metrics(S.circuit_from_skeleton(sk, not_style='not')).not_count, 1)
        # a single-AND edit: swapping the operands of AND 0 keeps the function
        swapped = sk.with_and(0, sk.ands[0][1], sk.ands[0][0])
        self.assertEqual(swapped.tables(), sk.tables())
        self.assertEqual(swapped.and_level, sk.and_level)
        with self.assertRaises(ValueError):
            sk.with_and(0, S.Form(1 << sk.n_inputs, 0), sk.ands[0][0])
        lp = sk.linear_problem()
        self.assertEqual(lp['arrival'][:3], [0, 0, 0])
        self.assertEqual(lp['deadline'][0], 1)         # L of the first AND, which fires at depth 2
        text = sk.matrix_text().splitlines()
        self.assertEqual(text[1], '%d %d' % (2 * 5 + 3, 3 + 5))

    def test_helpers(self):
        sk = S.skeleton(small())
        self.assertEqual(sk.and_levels_from_masks(), sk.and_level)
        self.assertEqual(sk.degrees()[0], 2)              # a1 = (x0+x1).x2
        n = sk.n_inputs
        basis = sk.basis_tables()
        for i in sk.redundant():                          # the claim redundant() makes, checked
            self.assertTrue(gf2.in_span([truth.all_ones(n)] + basis[:n + i], basis[n + i]))
        text = ('begin circuit r\nInputs: x0 x1\nOutputs: y\nbegin SLP\nAND a x0 x1\nNOT m x1\n'
                'AND b x0 m\nXOR y a b\nend SLP\nend circuit')     # b = x0(x1+1) = a + x0
        self.assertEqual(S.skeleton(ncff.parse(text)[0]).redundant(), [1])

    def test_degenerate(self):
        text = ('begin circuit d\nInputs: x0 x1\nOutputs: y\nbegin SLP\nNOT n x0\nAND y x0 n\n'
                'end SLP\nend circuit')
        sk = S.skeleton(ncff.parse(text)[0])
        self.assertEqual(sk.degenerate(), [(0, 'complementary operands')])

    def test_constants_in_rebuild(self):
        text = ('begin circuit k\nInputs: x0 x1\nOutputs: y z\nbegin SLP\nAND a x0 1\n'
                'XNOR n 0 x1\nAND b a n\nXOR y b x1\nXOR z x0 x0\nend SLP\nend circuit')
        c = ncff.parse(text)[0]
        sk = S.skeleton(c)
        self.assertEqual(sk.degenerate(), [(0, 'constant operand')])
        rebuilt = S.circuit_from_skeleton(sk)
        self.assertEqual(truth.truth_tables(rebuilt), truth.truth_tables(c))


@unittest.skipUnless(NIST.exists(), 'NIST circuits not imported')
class NistTests(unittest.TestCase):
    def test_every_imported_file(self):
        import check
        files = sorted(f for f in NIST.rglob('*') if f.name.endswith(check.SUFFIXES))
        self.assertGreater(len(files), 100)
        with_tallies = 0
        for f in files:
            for name, m, orders, problems in check.check_file(f):
                hard = [p for p in problems if not p.startswith('note:')]
                self.assertEqual(hard, [], '%s: %s' % (f.name, hard))
                self.assertIn(('msb', 'msb'), orders, f.name)
            with_tallies += 'gates' in M.header_tallies(ncff.load(f))
        self.assertEqual(with_tallies, len(files), 'every NIST file states its tallies')

    def test_sel_by_name(self):
        """an aes-sbox-sel file in a folder without a *.fn.json is checked against FIPS-197's definition"""
        import check
        import shutil
        import tempfile
        src = sorted((NIST / 'aes-sbox-sel').glob('aes-sbox-sel-*.circ.txt'))[0]
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / src.name
            shutil.copy(src, f)
            self.assertEqual(check.function_for(f).name, 'aes-sbox-sel')
            [(name, m, orders, problems)] = check.check_file(f)
            self.assertEqual([p for p in problems if not p.startswith('note:')], [])
            self.assertIn(('msb', 'msb'), orders)


if __name__ == '__main__':
    unittest.main()
