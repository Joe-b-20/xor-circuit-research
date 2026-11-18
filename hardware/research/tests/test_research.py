"""Tests of the research code: python3 -m unittest discover -s hardware/research/tests -t hardware/research"""
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))

import inventory as I  # noqa: E402


def h(gates, outs, n=2):
    return I.structure_hash(n, gates, outs)


class TestStructureHash(unittest.TestCase):
    def test_renaming_and_order(self):
        a = [('XOR', 'p', ('i0', 'i1')), ('AND', 'q', ('p', 'i0'))]
        b = [('XOR', 'zz', ('i1', 'i0')), ('AND', 'yy', ('i0', 'zz'))]
        self.assertEqual(h(a, ['q', 'p']), h(b, ['yy', 'zz']))

    def test_constant_forms_fold(self):
        base = [('XOR', 'p', ('i0', 'i1'))]
        forms = [('XNOR', 'n', ('p', '0')), ('XOR', 'n', ('p', '1')), ('NOT', 'n', ('p',)),
                 ('XNOR', 'n', ('0', 'p'))]
        hs = {h(base + [f], ['n', 'p']) for f in forms}
        self.assertEqual(len(hs), 1)
        copy = [('XOR', 'p', ('i0', 'i1')), ('XOR', 'c', ('p', '0')), ('AND', 'q', ('c', 'i0'))]
        direct = [('XOR', 'p', ('i0', 'i1')), ('AND', 'q', ('p', 'i0'))]
        self.assertEqual(h(copy, ['q', 'p']), h(direct, ['q', 'p']))

    def test_different_structures_differ(self):
        a = [('XOR', 'p', ('i0', 'i1')), ('AND', 'q', ('p', 'i0'))]
        b = [('XOR', 'p', ('i0', 'i1')), ('AND', 'q', ('p', 'i1'))]
        c = [('XNOR', 'p', ('i0', 'i1')), ('AND', 'q', ('p', 'i0'))]
        self.assertEqual(len({h(a, ['q']), h(b, ['q']), h(c, ['q'])}), 3)

    def test_duplicate_gate_dead_or_used(self):
        used = [('XOR', 'g1', ('i0', 'i1')), ('XOR', 'g2', ('i0', 'i1')),
                ('AND', 'a', ('g1', 'i0')), ('AND', 'b', ('g2', 'i1'))]
        dead = [('XOR', 'g1', ('i0', 'i1')), ('XOR', 'g2', ('i0', 'i1')),
                ('AND', 'a', ('g1', 'i0')), ('AND', 'b', ('g1', 'i1'))]
        self.assertNotEqual(h(used, ['a', 'b']), h(dead, ['a', 'b']))


if __name__ == '__main__':
    unittest.main()
