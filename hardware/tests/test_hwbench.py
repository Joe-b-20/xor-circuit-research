"""hwbench without the EDA tools: python3 -m unittest discover -s hardware/tests -t hardware"""
import itertools
import pathlib
import unittest

from hwbench import design as D, liberty as L, netlist as N, pairs as PR, verilog as V

REPO = D.REPO
OURS = REPO / 'circuits/aes-invsbox/aes-invsbox-a40-ad4-g134-gd12-xx94-41.circ.txt'
NIST = REPO / 'search/nonlinear/seeds/aes-invsbox/aes-invsbox-a45-ad4-g141-gd12-xx96-25.circ.txt'

LIB = r'''
library (tiny) {
  time_unit : "1ns" ;
  capacitive_load_unit (1,ff) ;
  /* a comment */
  cell (AND2) { area : 1.0 ;
    pin (A) { direction : input ; capacitance : 1.5 ; }
    pin (B) { direction : input ; capacitance : 1.5 ; }
    pin (Y) { direction : output ; function : "(A & B)" ; } }
  cell (XOR2) { area : 2.0 ;
    pin (A) { direction : input ; capacitance : 2.0 ; }
    pin (B) { direction : input ; capacitance : 2.0 ; }
    pin (Y) { direction : output ; function : "(A&!B) | (!A&B)" ; } }
  cell (INV) { area : 0.5 ;
    pin (A) { direction : input ; capacitance : 1.0 ; }
    pin (Y) { direction : output ; function : "A'" ; } }
  cell (DFF) { area : 4.0 ; ff (IQ, IQN) { next_state : "D" ; clocked_on : "CK" ; }
    pin (D) { direction : input ; }
    pin (CK) { direction : input ; }
    pin (Q) { direction : output ; function : "IQ" ; } }
}
'''


def truth(expr, names):
    """Truth table (int) of a Python boolean expression over ``names``."""
    t = 0
    for i, vals in enumerate(itertools.product((0, 1), repeat=len(names))):
        env = dict(zip(names, vals))
        if eval(expr, {}, env):
            t |= 1 << i
    return t


def tables(names):
    n = len(names)
    out = {}
    for k, name in enumerate(names):
        t = 0
        for i in range(1 << n):
            if (i >> (n - 1 - k)) & 1:
                t |= 1 << i
        out[name] = t
    return out, (1 << (1 << n)) - 1


class TestLiberty(unittest.TestCase):
    CASES = [
        ('(A1 & A2)', '(A1 and A2)', ['A1', 'A2']),
        ('!(A ^ B)', 'not (A != B)', ['A', 'B']),
        ('(A&!B) | (!A&B)', 'A != B', ['A', 'B']),
        ('!(A | (B1 & B2))', 'not (A or (B1 and B2))', ['A', 'B1', 'B2']),
        ('A B + C', '(A and B) or C', ['A', 'B', 'C']),
        ("A' B", '(not A) and B', ['A', 'B']),
        ('A ^ B & C', '(A != B) and C', ['A', 'B', 'C']),       # XOR binds tighter than AND
        ('A | B ^ C', 'A or (B != C)', ['A', 'B', 'C']),
        ('(A&B) | (A&CIN) | (B&CIN)', '(A and B) or (A and CIN) or (B and CIN)', ['A', 'B', 'CIN']),
        ('!((A1 | A2) & B1)', 'not ((A1 or A2) and B1)', ['A1', 'A2', 'B1']),
        ('1', 'True', ['A']),
    ]

    def test_functions(self):
        for expr, py, names in self.CASES:
            fn, used = L.compile_function(expr)
            vals, ones = tables(names)
            self.assertEqual(fn(vals, ones), truth(py, names), expr)
            self.assertLessEqual(set(used), set(names))

    def test_parse(self):
        lib = L.parse(LIB)
        self.assertEqual(lib.name, 'tiny')
        self.assertEqual(lib.cap_unit, 'ff')
        self.assertEqual(set(lib.cells), {'AND2', 'XOR2', 'INV', 'DFF'})
        self.assertEqual(lib.cells['XOR2'].area, 2.0)
        self.assertEqual([p.name for p in lib.cells['AND2'].inputs], ['A', 'B'])
        self.assertEqual(lib.cells['INV'].outputs[0].function, "A'")
        self.assertTrue(lib.cells['DFF'].sequential)
        self.assertFalse(lib.cells['AND2'].sequential)


class TestDesign(unittest.TestCase):
    def test_first_pair(self):
        o, n = D.load(OURS), D.load(NIST)
        self.assertEqual(o.label, '40/4/134/12')
        self.assertEqual(n.label, '45/4/141/12')
        self.assertEqual((o.origin, n.origin), ('ours', 'nist'))
        self.assertEqual(o.function, 'aes-invsbox')
        # FIPS-197: InvSbox(0x00) = 0x52, InvSbox(0x63) = 0x00, InvSbox(0xED) = 0x53
        self.assertEqual((o.value(0x00), o.value(0x63), o.value(0xED)), (0x52, 0x00, 0x53))
        for d in (o, n):
            for x in range(256):
                self.assertEqual(D.simulate_int(d, x), d.value(x))

    def test_linear(self):
        d = D.load(REPO / 'circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt')
        self.assertEqual((d.kind, d.label, d.n_in), ('linear', '89@4', 32))
        self.assertEqual(D.check_linear(d), '')
        n = D.load(REPO / 'hardware/nist/linear/aes-mixcols-xor90-depth4.circ.txt')
        self.assertEqual((n.origin, n.function, n.label), ('nist', 'aes-mixcolumns', '90@4'))

    def test_wrong_circuit_is_refused(self):
        text = OURS.read_text().replace('XOR t1 x4 x5', 'XNOR t1 x4 x5', 1)
        self.assertNotEqual(text, OURS.read_text())
        bad = pathlib.Path(__file__).parent / 'data' / 'aes-invsbox-mutant.circ.txt'
        bad.parent.mkdir(exist_ok=True)
        try:
            bad.write_text(text)
            with self.assertRaises(ValueError):
                D.load(bad)
        finally:
            bad.unlink()


class TestVerilog(unittest.TestCase):
    def test_constant_operands(self):
        d = D.load(OURS)
        from boolcirc import ncff
        g = ncff.Gate
        d.circuit.gates = [g('XNOR', 'n1', ('x0', '0')), g('XOR', 'n2', ('x1', '1')),
                           g('XOR', 'n3', ('x1', '0')), g('AND', 'n4', ('0', 'x2')),
                           g('XNOR', 'n5', ('1', 'x3')), g('NOT', 'n6', ('1',))]
        self.assertEqual(V.simplified_gates(d), [
            ('NOT', 'n1', ['x0']), ('NOT', 'n2', ['x1']), ('BUF', 'n3', ['x1']),
            ('CONST0', 'n4', []), ('BUF', 'n5', ['x3']), ('CONST0', 'n6', [])])

    def test_rtl_one_operator_per_gate(self):
        d = D.load(NIST)
        rtl = V.rtl(d)
        ops = sum(rtl.count(s) for s in (' ^ ', ' ~^ ', ' & '))
        m = d.metrics
        self.assertEqual(ops, m['A'] + m['XOR'] + m['XNOR'])
        self.assertEqual(sum(V.expected_cells(d).values()), m['G'])
        for b in range(8):
            self.assertEqual(rtl.count('assign y[%d] ' % b), 1)

    def test_vectors(self):
        self.assertEqual(V.vectors(D.load(OURS)), list(range(256)))
        lin = V.vectors(D.load(REPO / 'circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt'))
        self.assertIn(0, lin)
        self.assertTrue(all((1 << j) in lin for j in range(32)))


class TestNetlist(unittest.TestCase):
    NETLIST = '''
module dut(x, y);
  input [1:0] x;
  output [0:0] y;
  wire w1, w2;
  XOR2 g1 (.A(x[0]), .B(x[1]), .Y(w1));
  INV g2 (.A(w1), .Y(w2));
  AND2 \\g3  (
    .A(w2),
    .B(x[0]),
    .Y(y[0])
  );
endmodule
'''

    class Stub:
        """What netlist.simulate needs of a design: port widths and the reference function."""
        n_in, n_out = 2, 1

        def __init__(self, f):
            self.value = f

    def design(self, f):
        return self.Stub(f)

    def test_simulate(self):
        lib = L.parse(LIB)
        nl = N.parse(self.NETLIST)
        self.assertEqual([i.name for i in nl.instances], ['g1', 'g2', 'g3'])
        good = self.design(lambda x: int((x & 1) and not ((x & 1) ^ (x >> 1))))
        sim = N.simulate(nl, lib, good, [0, 1, 2, 3])
        self.assertEqual(sim.mismatches, 0)
        self.assertEqual(sim.area_logic, 3.5)
        self.assertEqual(sim.cells, {'XOR2': 1, 'INV': 1, 'AND2': 1})
        act = N.activity(sim)
        self.assertAlmostEqual(act['y[0]'][1], 0.25)         # 1 for one input in four
        self.assertAlmostEqual(act['y[0]'][0], 2 * 0.25 * 0.75)
        bad = self.design(lambda x: x & 1)
        self.assertGreater(N.simulate(nl, lib, bad, [0, 1, 2, 3]).mismatches, 0)

    def test_loop_and_undriven(self):
        lib = L.parse(LIB)
        loop = N.parse('module dut(x, y); input [1:0] x; output [0:0] y;'
                       ' INV a (.A(y[0]), .Y(y[0])); endmodule')
        with self.assertRaises(ValueError):
            N.simulate(loop, lib, self.design(lambda x: 0), [0, 1])


class TestPairs(unittest.TestCase):
    def test_first_pair_is_paired(self):
        o, n = D.load(OURS), D.load(NIST)
        self.assertTrue(PR.dominates(o.metrics, n.metrics))
        self.assertEqual(PR.pair([o], [n]), [(n, o)])


if __name__ == '__main__':
    unittest.main()
