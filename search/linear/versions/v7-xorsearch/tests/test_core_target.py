"""``core.target``: map catalog, loaders, generators, the canonical matrix hash and ``map new``."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from xorsearch.cli import main
from xorsearch.core.circuit import verify
from xorsearch.core.target import (CIRCUITS_DIR, Target, catalog, circulant, format_matrix_text,
                                   generate, gf_mul, invmixcolumns, load_matrix_text, load_target,
                                   map_path, matrix_over_field, min_depth, mixcolumns,
                                   parse_matrix_text, random_target, sparse_target)

#: The maps' matrix hashes as defined by earlier versions (target JSON files and generators).
MAP_HASHES = {
    'aes-mixcolumns': '2a16955dfe321e1bc8ef1a1eb9e4be319670eb21554c552f8938f7e4987c6eba',
    'aes-invmixcolumns': '7a3774b642e7c92bfaea20e6c1b379c3f4f0f389592f0ab26d089745e40f94a3',
    'aes-sbox-bottom': '6a2a15b9921418f0f3aa5affdd14254d505c49e57856b10fc4a064f83e64b569',
    'joltik': '9190373ebe4882ad07b68892119babb183524d88f5b9ae2095adcb0f91a32415',
    'fox-mu4': 'd48d0571690c03a28305fcbec547b9f6eab0f3a29c12bf9b20c695f0b371524f',
    'fox-mu8': 'ac1e3d1f408c638f757abfa6667514ded6435f97c80985ba5d4ac682ef562028',
}
AES_MC = '02 03 01 01; 01 02 03 01; 01 01 02 03; 03 01 01 02'


def run_cli(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(list(argv))
    return code, out.getvalue()


@unittest.skipUnless(CIRCUITS_DIR.is_dir(), 'no circuits/ next to search/')
class CatalogTest(unittest.TestCase):
    def test_catalog_names(self):
        names = catalog()
        for name in MAP_HASHES:
            self.assertIn(name, names)

    def test_maps_match_earlier_definitions(self):
        for name, digest in MAP_HASHES.items():
            t = load_target(name)
            self.assertEqual(t.name, name)
            self.assertEqual(t.matrix_sha256, digest, name)
            for seed in t.seeds:
                v = verify(seed.load(t.n_inputs), t)
                self.assertTrue(v.ok, (name, seed.path, v.reason))
                self.assertEqual((v.gate_count, v.depth), (seed.gates, seed.depth))
            # the file is exactly what format_matrix_text writes (one canonical text per map)
            self.assertEqual(map_path(name).read_text(),
                             format_matrix_text(t.n_inputs, t.rows,
                                                t.meta.get('affine_output_constants')))
        self.assertEqual(load_target('aes-mixcolumns').rows, mixcolumns().rows)
        self.assertEqual(load_target('aes-invmixcolumns').rows, invmixcolumns().rows)
        self.assertEqual(load_target('aes-sbox-bottom').meta['affine_output_constants'],
                         [0, 1, 1, 0, 0, 0, 1, 1])
        self.assertNotIn('affine_output_constants', load_target('joltik').meta)

    def test_paths_and_dicts(self):
        path = str(map_path('joltik'))
        self.assertEqual(load_target(path), load_target('joltik'))
        self.assertEqual(len(load_target(path).seeds), len(load_target('joltik').seeds))
        with tempfile.TemporaryDirectory() as tmp:
            copy = os.path.join(tmp, 'joltik.mat.txt')      # same name, not the catalog file:
            Path(copy).write_text(Path(path).read_text())    # no seeds attached
            self.assertEqual(load_target(copy).rows, load_target('joltik').rows)
            self.assertEqual(load_target(copy).seeds, ())
        data = load_target('fox-mu4').to_json()
        self.assertEqual(load_target(data).rows, load_target('fox-mu4').rows)
        bad = dict(data, matrix_sha256='0' * 64)
        with self.assertRaises(ValueError):
            load_target(bad)
        with self.assertRaises(ValueError):
            load_target('no_such_target')


@unittest.skipUnless(CIRCUITS_DIR.is_dir(), 'no circuits/ next to search/')
class MapNewTest(unittest.TestCase):
    def test_aes_mixcolumns_reproduced_exactly(self):
        want = map_path('aes-mixcolumns').read_text()
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli('map', 'new', 'aes-mixcolumns', '--gf', '0x11b', '--bytes', AES_MC,
                                '--circuits', tmp)
            self.assertEqual(code, 0, out)
            self.assertEqual(map_path('aes-mixcolumns', tmp).read_text(), want)
            code, out = run_cli('map', 'new', 'mc2', '--gf', '0x11b', '--circulant', '02 03 01 01',
                                '--circuits', tmp)
            self.assertEqual(code, 0, out)
            self.assertEqual(map_path('mc2', tmp).read_text(), want)
            self.assertIn(MAP_HASHES['aes-mixcolumns'], out)
            # same text again is fine; a different matrix needs --force
            self.assertEqual(run_cli('map', 'new', 'mc2', '--gf', '0x11b', '--circulant',
                                     '02 03 01 01', '--circuits', tmp)[0], 0)
            code, out = run_cli('map', 'new', 'mc2', '--gf', '0x11b', '--circulant',
                                '0e 0b 0d 09', '--circuits', tmp)
            self.assertEqual(code, 1)
            self.assertIn('--force', out)

    def test_rows_file_and_constants(self):
        bottom = map_path('aes-sbox-bottom')
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli('map', 'new', 'bottom', '--rows', str(bottom), '--circuits', tmp)
            self.assertEqual(code, 0, out)
            self.assertEqual(map_path('bottom', tmp).read_text(), bottom.read_text())
            plain = os.path.join(tmp, 'plain.txt')
            Path(plain).write_text('110\n011\n')
            code, out = run_cli('map', 'new', 'tiny', '--rows', plain, '--constants', '0 1',
                                '--circuits', tmp)
            self.assertEqual(code, 0, out)
            self.assertEqual(map_path('tiny', tmp).read_text(), '1\n2 3\n1 1 0\n0 1 1\n0 1\n')
            t = load_target(str(map_path('tiny', tmp)))
            self.assertEqual((t.rows, t.meta['affine_output_constants']), ((0b011, 0b110), [0, 1]))
            for bad in (['--gf', '0x11b', '--bytes', '02 1ff'],     # entry outside GF(2^8)
                        ['--bytes', '02 03'],                        # no field
                        ['--gf', '0x11b'],                           # no matrix
                        ['--rows', plain, '--constants', '0 1 1']):  # wrong constant count
                self.assertEqual(run_cli('map', 'new', 'x', '--circuits', tmp, *bad)[0], 1, bad)
            self.assertEqual(run_cli('map', 'new', 'a/b', '--rows', plain, '--circuits', tmp)[0], 1)

    def test_other_fields(self):
        # GF(2^4) mod x^4 + x + 1: matrix_over_field derives m from the modulus.
        n, rows = matrix_over_field([[1, 2], [2, 1]], 0x13)
        self.assertEqual((n, rows), (8, list(circulant((1, 2), m=4, poly=0x13).rows)))
        with self.assertRaises(ValueError):
            matrix_over_field([[1, 2], [3]], 0x13)


class GeneratorTest(unittest.TestCase):
    def test_gf_mul(self):
        self.assertEqual(gf_mul(0x57, 0x83), 0xC1)          # FIPS-197 worked example
        self.assertEqual(gf_mul(0x57, 0x13), 0xFE)
        for a in range(256):
            self.assertEqual(gf_mul(a, 1), a)

    def test_mixcolumns_weights(self):
        w = sorted(r.bit_count() for r in mixcolumns().rows)
        self.assertEqual((w.count(5), w.count(7), len(w)), (20, 12, 32))
        t = mixcolumns()
        self.assertEqual((t.n_inputs, t.n_outputs, t.min_depth), (32, 32, 3))

    def test_invmixcolumns_matches_json(self):
        gen = invmixcolumns()
        ref = load_target('invmixcolumns')
        self.assertEqual(gen.rows, ref.rows)
        self.assertEqual(gen.matrix_sha256, ref.matrix_sha256)

    def test_inverse_pair(self):
        # MixColumns o InvMixColumns = identity over GF(2).
        mc, imc = mixcolumns(), invmixcolumns()
        for bit in range(32):
            x = 1 << bit
            y = 0
            for i, row in enumerate(imc.rows):
                y |= ((row & x).bit_count() & 1) << i
            z = 0
            for i, row in enumerate(mc.rows):
                z |= ((row & y).bit_count() & 1) << i
            self.assertEqual(z, x)

    def test_circulant_general(self):
        # GF(2^4) with x^4 + x + 1, circulant (1, 2, 4): the GF(2) rows must reproduce the
        # field arithmetic y_i = sum_j c[(j - i) mod 3] * x_j on every input.
        import random
        coeffs = (1, 2, 4)
        t = circulant(coeffs, m=4, poly=0x13)
        self.assertEqual((t.n_inputs, t.n_outputs), (12, 12))
        rng = random.Random(0)
        for _ in range(50):
            xs = [rng.randrange(16) for _ in range(3)]
            word = sum(x << (4 * j) for j, x in enumerate(xs))
            got = sum((((row & word).bit_count() & 1) << i) for i, row in enumerate(t.rows))
            want = 0
            for i in range(3):
                y = 0
                for j in range(3):
                    y ^= gf_mul(coeffs[(j - i) % 3], xs[j], 4, 0x13)
                want |= y << (4 * i)
            self.assertEqual(got, want)
        t = circulant((1, 2), m=4, poly=0x13)
        self.assertEqual(t.rows[:2], (0b10000001, 0b10010010))   # y0 bits 0, 1 of x0 + 2*x1
        same = generate('circulant:m=4,poly=0x13,coeffs=1/2')
        self.assertEqual(same.rows, t.rows)
        self.assertEqual(generate({'generator': 'circulant', 'm': 4, 'poly': 0x13,
                                   'coeffs': [1, 2]}).rows, t.rows)
        self.assertEqual(generate('mixcolumns').rows, mixcolumns().rows)

    def test_random_generators(self):
        a = random_target(10, 6, density=0.3, seed=4)
        self.assertEqual(a, random_target(10, 6, density=0.3, seed=4))
        self.assertTrue(all(r.bit_count() >= 2 for r in a.rows))
        self.assertEqual(generate('random:n=10,m=6,density=0.3,seed=4').rows, a.rows)
        s = sparse_target(12, 5, weight=3, seed=1)
        self.assertEqual([r.bit_count() for r in s.rows], [3] * 5)
        self.assertEqual(load_target('sparse:n=12,m=5,weight=3,seed=1').rows, s.rows)
        with self.assertRaises(ValueError):
            generate('nope:n=3')

    def test_random_target_zero_density_is_rejected(self):
        # Regression: density 0 with min_weight >= 1 redrew rows forever.
        with self.assertRaises(ValueError):
            random_target(6, 3, density=0.0)
        self.assertEqual(random_target(6, 3, density=0.0, min_weight=0).rows, (0, 0, 0))


class TextMatrixTest(unittest.TestCase):
    def test_nist_format_and_constants_line(self):
        t = parse_matrix_text('1\n2 3\n1 1 0\n0 1 1\n', 'n')
        self.assertEqual((t.n_inputs, t.rows, t.meta['source_format']), (3, (0b011, 0b110), 'nist-mat'))
        self.assertNotIn('affine_output_constants', t.meta)
        t = parse_matrix_text('1\n2 3\n1 1 0\n0 1 1\n1 0\n', 'n')
        self.assertEqual((t.rows, t.meta['affine_output_constants']), ((0b011, 0b110), [1, 0]))
        self.assertEqual(parse_matrix_text('1\n2 3\n1 1 0\n0 1 1\n0 0\n').meta.get(
            'affine_output_constants'), None)                       # all-zero constants: linear
        self.assertEqual(format_matrix_text(3, (0b011, 0b110), [1, 0]), '1\n2 3\n1 1 0\n0 1 1\n1 0\n')
        self.assertEqual(format_matrix_text(3, (0b011, 0b110), [0, 0]), '1\n2 3\n1 1 0\n0 1 1\n')
        with self.assertRaises(ValueError):
            format_matrix_text(3, (0b011, 0b110), [1])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'm.mat.txt')
            Path(path).write_text('1\n1 2\n1 1\n')
            self.assertEqual(load_matrix_text(path).name, 'm')

    def test_plain_rows(self):
        t = parse_matrix_text('# comment\n0110\n1 0 0 1\n', 'm')
        self.assertEqual((t.n_inputs, t.rows), (4, (0b0110, 0b1001)))
        with self.assertRaises(ValueError):
            parse_matrix_text('011\n10\n')
        with self.assertRaises(ValueError):
            parse_matrix_text('012\n')
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'small.txt')
            with open(path, 'w') as fh:
                fh.write('110\n011\n')
            t = load_target(path)
            self.assertEqual((t.name, t.rows), ('small', (0b011, 0b110)))

    def test_one_input_plain_rows(self):
        # Regression: "1 / 0 / 1" matched the NIST header test as a 0 x 1 matrix and failed.
        t = parse_matrix_text('1\n0\n1\n', 'one')
        self.assertEqual((t.n_inputs, t.rows), (1, (1, 0, 1)))
        t = parse_matrix_text('1\n2 2\n1 0\n0 1\n', 'nist')      # a real 2 x 2 NIST file
        self.assertEqual((t.n_inputs, t.rows), (2, (0b01, 0b10)))


class TargetModelTest(unittest.TestCase):
    def test_properties(self):
        t = Target.make('x', 5, [0, 1, 0b11, 0b11, 0b11111])
        self.assertEqual(t.n_outputs, 5)
        self.assertEqual(t.min_depth, 3)
        self.assertEqual(min_depth([0, 1]), 0)                         # zero and unit rows
        self.assertEqual(hash(t), hash(Target.make('x', 5, [0, 1, 0b11, 0b11, 0b11111])))
        with self.assertRaises(ValueError):
            Target.make('bad', 3, [8])
        with self.assertRaises(ValueError):
            Target('bad', 3, (1,), '0' * 64)
        js = load_target('joltik').to_json()
        self.assertEqual(load_target(js).rows, load_target('joltik').rows)


if __name__ == '__main__':
    unittest.main()
