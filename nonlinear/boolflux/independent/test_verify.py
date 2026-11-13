"""Tests for the independent circuit verifier (verify.py in this directory).

Run from the repository root:
    python3 -m unittest discover -s nonlinear/boolflux/independent -v
"""

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify as V  # noqa: E402

REPO = HERE.parents[2]
NIST = REPO / "nonlinear" / "nist"
SCRIPT = HERE / "verify.py"

NCFF_NAME = re.compile(r"^aes-(sbox|invsbox)-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-xx(n?)(\d+)-(\d+)(?:-(\d+))?(?:-\d+)?\.circ\.txt$")
# 2026 names: -xxX-Y (X = XOR+XNOR, Y = XNOR); from NIST commit e6ac0d0 also -xxnX-Y-Z
# (X = XOR+XNOR+NOT, Y = XNOR, Z = NOT), sometimes with a trailing -k variant number
OLD_NAME = re.compile(r"^aes-sbox-(fwd|rev)-g(\d+)-a(\d+)-d(\d+)-ad(\d+)\.slp$")

AES = (8, 8, V.aes_sbox())
AES_INV = (8, 8, V.aes_inv_sbox())
REF_CIRCUIT = NIST / "aes-sbox" / "aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt"


def circ(inputs, outputs, gates, name="t"):
    return (f"begin circuit {name}\nInputs: {inputs}\nOutputs: {outputs}\n"
            f"begin SLP\n{gates}\nend SLP\nend circuit\n")


def run(text, table, n, m, **kw):
    return V.verify_text(text, (n, m, table), **kw)


def gate_line_indices(lines):
    """Indices of gate lines inside the SLP block of a source text."""
    idx, inside = [], False
    for i, raw in enumerate(lines):
        s = V.strip_comment(raw).lower()
        if s == "begin slp":
            inside = True
        elif s == "end slp":
            inside = False
        elif inside and s:
            idx.append(i)
    return idx


class TestAES(unittest.TestCase):
    def test_known_values(self):
        s, si = AES[2], AES_INV[2]
        self.assertEqual(s[0x00], 0x63)
        self.assertEqual(s[0x01], 0x7C)
        self.assertEqual(s[0x53], 0xED)
        self.assertEqual(s[:16], [0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5,
                                  0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76])
        self.assertEqual(si[:16], [0x52, 0x09, 0x6A, 0xD5, 0x30, 0x36, 0xA5, 0x38,
                                   0xBF, 0x40, 0xA3, 0x9E, 0x81, 0xF3, 0xD7, 0xFB])
        self.assertEqual(s[0xFF], 0x16)
        for x in range(256):
            self.assertEqual(si[s[x]], x)
            self.assertEqual(s[si[x]], x)

    def test_gf_mul(self):
        self.assertEqual(V.gf256_mul(0x57, 0x83), 0xC1)  # FIPS-197 example
        self.assertEqual(V.gf256_mul(0x57, 0x13), 0xFE)


class TestNIST(unittest.TestCase):
    def check_dir(self, files, fn, parse_name):
        self.assertTrue(files, "no circuit files found")
        for f in files:
            with self.subTest(file=f.name):
                r = V.verify_file(str(f), fn)
                self.assertTrue(r["ok"], r["errors"])
                self.assertEqual(r["order"], "msb/msb")
                met = r["metrics"]
                for k, v in parse_name(f.name).items():
                    if k == "XNOR":
                        self.assertEqual(met["counts"].get("XNOR", 0), v, k)
                    else:
                        self.assertEqual(met[k], v, k)
                self.assertEqual(met["dead"], 0)

    @staticmethod
    def ncff_metrics(name):
        m = NCFF_NAME.match(name)
        a, ad, g, gd = map(int, m.groups()[1:5])
        n_flag, xx, xn, nots = m.group(6), int(m.group(7)), int(m.group(8)), m.group(9)
        if n_flag:
            return {"A": a, "AD": ad, "G": g, "GD": gd, "XX": xx - int(nots), "XNOR": xn}
        return {"A": a, "AD": ad, "G": g, "GD": gd, "XX": xx, "XNOR": xn}

    @staticmethod
    def old_metrics(name):
        m = OLD_NAME.match(name)
        g, a, d, ad = map(int, m.groups()[1:])
        return {"G": g, "A": a, "GD": d, "AD": ad}

    def test_aes_sbox_ncff(self):
        files = sorted((NIST / "aes-sbox").glob("*.circ.txt"))
        for f in files:
            self.assertRegex(f.name, NCFF_NAME)
        self.check_dir(files, AES, self.ncff_metrics)

    def test_aes_invsbox_ncff(self):
        files = sorted((NIST / "aes-invsbox").glob("*.circ.txt"))
        self.check_dir(files, AES_INV, self.ncff_metrics)

    def test_old_2020_fwd(self):
        files = sorted((NIST / "old-2020").glob("aes-sbox-fwd-*.slp"))
        self.check_dir(files, AES, self.old_metrics)

    def test_old_2020_rev(self):
        files = sorted((NIST / "old-2020").glob("aes-sbox-rev-*.slp"))
        self.check_dir(files, AES_INV, self.old_metrics)

    def test_wrong_function_fails(self):
        r = V.verify_file(str(REF_CIRCUIT), AES_INV)
        self.assertFalse(r["ok"])
        self.assertEqual(r["mismatch"]["x"], 0)
        self.assertEqual(r["mismatch"]["expected"], 0x52)
        self.assertEqual(r["mismatch"]["got"], 0x63)

    def test_other_orders_fail(self):
        # AES is not invariant under bit reversal, so only msb/msb matches.
        r = V.verify_file(str(REF_CIRCUIT), AES, any_order=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["orders_matched"], ["msb/msb"])
        for io_, oo in (("lsb", "lsb"), ("msb", "lsb"), ("lsb", "msb")):
            self.assertFalse(V.verify_file(str(REF_CIRCUIT), AES, in_order=io_, out_order=oo)["ok"])


class TestMutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = REF_CIRCUIT.read_text().splitlines()
        cls.gidx = gate_line_indices(cls.lines)
        assert len(cls.gidx) == 104

    def mutated(self, i, new_line):
        lines = list(self.lines)
        lines[i] = new_line
        return "\n".join(lines) + "\n"

    def test_baseline_ok(self):
        self.assertTrue(run("\n".join(self.lines), AES[2], 8, 8)["ok"])

    def test_gate_type_changes_fail(self):
        swap = {"XOR": "XNOR", "XNOR": "XOR", "AND": "OR"}
        for i in self.gidx[::5] + [self.gidx[-1]]:
            op, rest = self.lines[i].split(None, 1)
            for new in (swap[op], "AND" if op != "AND" else "XOR"):
                with self.subTest(line=self.lines[i], new=new):
                    r = run(self.mutated(i, f"{new} {rest}"), AES[2], 8, 8)
                    self.assertFalse(r["ok"])
                    self.assertIsNotNone(r["mismatch"])

    def test_operand_change_fails(self):
        for i in self.gidx[::9]:
            op, out, a, b = self.lines[i].split()
            repl = next(x for x in ("x0", "x1", "x2") if x not in (a, b))
            with self.subTest(line=self.lines[i]):
                r = run(self.mutated(i, f"{op} {out} {repl} {b}"), AES[2], 8, 8)
                self.assertFalse(r["ok"])
                self.assertIsNotNone(r["mismatch"])

    def test_later_wire_fails_structurally(self):
        i = self.gidx[3]
        last_out = self.lines[self.gidx[-1]].split()[1]
        op, out, a, b = self.lines[i].split()
        r = run(self.mutated(i, f"{op} {out} {a} {last_out}"), AES[2], 8, 8)
        self.assertFalse(r["ok"])
        self.assertIsNone(r["metrics"])
        self.assertTrue(any("later line" in e for e in r["errors"]), r["errors"])

    def test_self_reference_fails(self):
        i = self.gidx[3]
        op, out, a, b = self.lines[i].split()
        r = run(self.mutated(i, f"{op} {out} {a} {out}"), AES[2], 8, 8)
        self.assertFalse(r["ok"])
        self.assertTrue(any("own output" in e for e in r["errors"]), r["errors"])

    def test_duplicate_assignment_fails(self):
        i = self.gidx[10]
        r = run(self.mutated(i, self.lines[i] + "\n" + self.lines[i]), AES[2], 8, 8)
        self.assertFalse(r["ok"])
        self.assertTrue(any("assigned more than once" in e for e in r["errors"]), r["errors"])

    def test_library_violation(self):
        model = V.validate_model({"name": "and-xor", "gates": {"AND": 1, "XOR": 1}})
        r = V.verify_file(str(REF_CIRCUIT), AES, model=model)
        self.assertFalse(r["ok"])
        self.assertEqual(r["metrics"]["library_violations"], ["XNOR"])
        self.assertIsNone(r["metrics"]["cost"])
        self.assertTrue(any("XNOR x5" in e and "and-xor" in e for e in r["errors"]), r["errors"])

    def test_model_cost(self):
        model = V.validate_model({"name": "w", "gates": {"AND": 2.33, "XOR": 1, "XNOR": 1.5}})
        r = V.verify_file(str(REF_CIRCUIT), AES, model=model)
        self.assertTrue(r["ok"], r["errors"])
        self.assertAlmostEqual(r["metrics"]["cost"], 32 * 2.33 + 67 + 5 * 1.5)
        self.assertNotIn("WD", r["metrics"])
        unit = V.validate_model({"gates": {"AND": 1, "XOR": 1, "XNOR": 1, "NOT": 1}})
        self.assertEqual(V.verify_file(str(REF_CIRCUIT), AES, model=unit)["metrics"]["cost"], 104)

    def test_assertions(self):
        ok = {"expect_G": 104, "expect_A": 32, "expect_GD": 30, "expect_AD": 5,
              "max_GD": 30, "max_AD": 5, "max_G": 104}
        self.assertTrue(V.verify_file(str(REF_CIRCUIT), AES, expect=ok)["ok"])
        for bad in ({"expect_G": 103}, {"max_GD": 29}, {"max_AD": 4}, {"expect_A": 31}):
            with self.subTest(bad=bad):
                r = V.verify_file(str(REF_CIRCUIT), AES, expect=bad)
                self.assertFalse(r["ok"])
        r = V.verify_file(str(REF_CIRCUIT), AES, expect={"max_cost": 200})
        self.assertFalse(r["ok"])  # cost requires a model


TRUTH_2 = {  # x = a<<1 | b (msb), entries for x = 0,1,2,3
    "XOR": [0, 1, 1, 0], "XNOR": [1, 0, 0, 1],
    "AND": [0, 0, 0, 1], "NAND": [1, 1, 1, 0],
    "OR": [0, 1, 1, 1], "NOR": [1, 0, 0, 0],
    "ANDN": [0, 0, 1, 0],   # a AND NOT b
    "ORN": [1, 0, 1, 1],    # a OR NOT b
}


class TestSemantics(unittest.TestCase):
    def test_two_input_gates(self):
        for op, table in TRUTH_2.items():
            with self.subTest(op=op):
                text = circ("a b", "y", f"{op} y a b")
                self.assertTrue(run(text, table, 2, 1)["ok"])
                # the operand-swapped table must be rejected for ANDN / ORN
                swapped = [table[0], table[2], table[1], table[3]]
                if swapped != table:
                    self.assertFalse(run(text, swapped, 2, 1)["ok"])

    def test_one_input_gates(self):
        self.assertTrue(run(circ("a", "y", "NOT y a"), [1, 0], 1, 1)["ok"])
        self.assertFalse(run(circ("a", "y", "NOT y a"), [0, 1], 1, 1)["ok"])
        r = run(circ("a", "y", "BUF y a"), [0, 1], 1, 1)
        self.assertTrue(r["ok"])
        self.assertEqual((r["metrics"]["G"], r["metrics"]["GD"]), (0, 0))

    def test_constants(self):
        text = circ("a", "y0:y3", "XOR y0 a 1\nAND y1 a 0\nOR y2 0 1\nXNOR y3 a 0")
        # y0 = NOT a, y1 = 0, y2 = 1, y3 = NOT a ; y0 is the msb
        r = run(text, [0b1011, 0b0010], 1, 4)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["metrics"]["GD"], 1)
        self.assertEqual(r["metrics"]["AD"], 1)

    def test_majority_nand(self):
        text = circ("a b c", "y", "NAND t1 a b\nNAND t2 a c\nNAND t3 b c\n"
                                  "AND t4 t1 t2\nNAND y t4 t3")
        maj = [0, 0, 0, 1, 0, 1, 1, 1]
        r = run(text, maj, 3, 1)
        self.assertTrue(r["ok"], r["errors"])
        met = r["metrics"]
        self.assertEqual((met["G"], met["A"], met["GD"], met["AD"]), (5, 5, 3, 3))
        model = V.validate_model({"gates": {"NAND": 2, "AND": 1},
                                  "depth_weights": {"NAND": 2}})
        r = run(text, maj, 3, 1, model=model)
        self.assertEqual(r["metrics"]["WD"], 5)   # NAND(2) -> AND(1) -> NAND(2)
        self.assertEqual(r["metrics"]["cost"], 9)
        self.assertTrue(run(text, maj, 3, 1, expect={"expect_WD": 5, "max_cost": 9},
                            model=model)["ok"])

    def test_majority_nor(self):
        text = circ("a b c", "y", "NOR u1 a b\nNOR u2 a c\nNOR u3 b c\n"
                                  "OR u4 u1 u2\nNOR y u4 u3")
        self.assertTrue(run(text, [0, 0, 0, 1, 0, 1, 1, 1], 3, 1)["ok"])

    def test_full_adder(self):
        text = circ("a b c", "s cout",
                    "XNOR p a b\nXNOR s p c\nANDN q c p\nAND r a b\nOR cout r q")
        table = []
        for x in range(8):
            a, b, c = (x >> 2) & 1, (x >> 1) & 1, x & 1
            table.append(((a ^ b ^ c) << 1) | (a + b + c >= 2))
        r = run(text, table, 3, 2)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["metrics"]["XX"], 2)
        bad = text.replace("ANDN q c p", "ANDN q p c")
        self.assertFalse(run(bad, table, 3, 2)["ok"])

    def test_orn_adder_variant(self):
        # qn = ORN(p, c) = p OR NOT c = NOT(c AND (a XOR b)); cout = NOT(NOT r AND qn)
        text = circ("a b c", "s cout",
                    "XNOR p a b\nXNOR s p c\nORN qn p c\nAND r a b\nNOT rn r\n"
                    "AND w rn qn\nNOT cout w")
        table = [(((x >> 2) ^ (x >> 1) ^ x) & 1) << 1 |
                 (((x >> 2) & 1) + ((x >> 1) & 1) + (x & 1) >= 2) for x in range(8)]
        self.assertTrue(run(text, table, 3, 2)["ok"])

    def test_outputs_used_as_operands_and_buf_depth(self):
        text = circ("a b", "y z", "AND t a b\nBUF y t\nXOR z y a")
        r = run(text, [0b00, 0b00, 0b01, 0b10], 2, 2)
        self.assertTrue(r["ok"], r["errors"])
        met = r["metrics"]
        self.assertEqual(met["counts"], {"AND": 1, "BUF": 1, "XOR": 1})
        self.assertEqual((met["G"], met["GD"], met["AD"]), (2, 2, 1))

    def test_bit_orders(self):
        # y = a AND NOT b, z = a OR b; table written for in=lsb (a = bit 0), out=msb.
        text = circ("a b", "y z", "ANDN y a b\nOR z a b")
        table = [0, 3, 1, 1]
        self.assertFalse(run(text, table, 2, 2)["ok"])
        self.assertTrue(run(text, table, 2, 2, in_order="lsb", out_order="msb")["ok"])
        r = run(text, table, 2, 2, any_order=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["orders_matched"], ["lsb/msb"])
        self.assertEqual(r["order"], "lsb/msb")

    def test_sixteen_inputs(self):
        lines, layer, k = [], [f"x{i}" for i in range(16)], 0
        while len(layer) > 1:
            nxt = []
            for i in range(0, len(layer), 2):
                k += 1
                o = "p" if len(layer) == 2 else f"t{k}"
                lines.append(f"XOR {o} {layer[i]} {layer[i + 1]}")
                nxt.append(o)
            layer = nxt
        text = circ("x0:x15", "p", "\n".join(lines))
        parity = [bin(x).count("1") & 1 for x in range(1 << 16)]
        r = run(text, parity, 16, 1)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual((r["metrics"]["G"], r["metrics"]["GD"], r["metrics"]["AD"]), (15, 4, 0))
        parity[12345] ^= 1
        r = run(text, parity, 16, 1)
        self.assertFalse(r["ok"])
        self.assertEqual(r["mismatch"]["x"], 12345)


class TestStructure(unittest.TestCase):
    def errors(self, text):
        with self.assertRaises(V.CircuitError) as cm:
            V.parse_circuit(text)
        return " | ".join(cm.exception.errors)

    def test_rules(self):
        cases = {
            "input 'a' is assigned": circ("a b", "y", "XOR a a b\nXOR y a b"),
            "never assigned": circ("a b", "y z", "XOR y a b"),
            "operand 'q' is never assigned": circ("a b", "y", "XOR y a q"),
            "takes 2 operand": circ("a b", "y", "XOR y a"),
            "takes 1 operand": circ("a b", "y", "NOT y a b"),
            "unknown gate type 'MUX'": circ("a b", "y", "MUX y a b"),
            "constant '1' used as gate output": circ("a b", "y", "XOR 1 a b\nXOR y a b"),
            "input 'a' declared more than once": circ("a a", "y", "XOR y a a"),
            "declared both as input and as output": circ("a b", "a", "XOR c a b"),
            "unsupported GateSyntax": circ("a b", "y", "XOR y a b").replace(
                "begin SLP", "GateSyntax: GateName Inputs Output\nbegin SLP"),
            "missing 'end SLP'": "begin circuit t\nInputs: a\nOutputs: y\nbegin SLP\nNOT y a\n",
            "no 'Outputs:'": "begin circuit t\nInputs: a\nbegin SLP\nNOT y a\nend SLP\nend circuit\n",
            "no 'begin circuit'": "Inputs: a\nOutputs: y\n",
            "bad name range": circ("x0:y3", "y", "NOT y x0"),
        }
        for frag, text in cases.items():
            with self.subTest(frag=frag):
                self.assertIn(frag, self.errors(text))

    def test_comments_ranges_and_headers(self):
        text = ("% preamble\nsome junk line\n## heading\n"
                "begin circuit demo   # trailing\n"
                "Inputs: x2:x0 c   % descending range plus a separate name\n"
                "Outputs: y0\nInternal: t1:t2\nGateSyntax: GateName Output Inputs\n"
                "begin SLP\n"
                "XOR t1 x2 x1 % comment\n"
                "and t2 t1 x0 # lower-case gate name, 2020-style comment\n\n"
                "XNOR y0 t2 c\nend SLP\nend circuit\n")
        c = V.parse_circuit(text)
        self.assertEqual(c.name, "demo")
        self.assertEqual(c.inputs, ["x2", "x1", "x0", "c"])
        self.assertEqual([g.op for g in c.gates], ["XOR", "AND", "XNOR"])
        self.assertEqual(V.expand_names("v08:v10", 1, []), ["v08", "v09", "v10"])

    def test_multiple_circuits(self):
        one = circ("a b", "y", "AND y a b", name="first")
        two = circ("a b", "y", "OR y a b", name="second")
        r = run(one + "\n" + two, TRUTH_2["AND"], 2, 1)
        self.assertTrue(r["ok"])
        self.assertEqual(r["circuit"], "first")
        self.assertTrue(any("2 circuits" in n for n in r["notes"]))

    def test_shape_mismatch(self):
        r = run(circ("a b", "y", "AND y a b"), [0] * 8, 3, 1)
        self.assertFalse(r["ok"])
        self.assertTrue(any("shape mismatch" in e for e in r["errors"]))

    def test_bad_specs(self):
        with self.assertRaises(V.SpecError):
            V.validate_model({"gates": {"MUX": 1}})
        with self.assertRaises(V.SpecError):
            V.validate_model({"gates": {"AND": -1}})
        with self.assertRaises(V.SpecError):
            V.validate_fn(2, 1, [0, 1, 2, 0])
        with self.assertRaises(V.SpecError):
            V.validate_fn(2, 1, [0, 1, 1])


class TestCLI(unittest.TestCase):
    def cli(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                           capture_output=True, text=True,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        return p.returncode, p.stdout, p.stderr

    def test_cli_aes(self):
        code, out, _ = self.cli(REF_CIRCUIT, "--aes", "--expect-G", 104, "--max-AD", 5)
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("ok"))
        self.assertIn("G=104 [AND=32 XNOR=5 XOR=67] A=32 AD=5 GD=30", out)

    def test_cli_fail_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.circ.txt"
            bad.write_text(REF_CIRCUIT.read_text().replace("XNOR y1 y0 t59", "XOR y1 y0 t59"))
            model = Path(d) / "m.json"
            model.write_text(json.dumps({"name": "unit", "gates": {"AND": 1, "XOR": 1, "XNOR": 1}}))
            code, out, _ = self.cli(REF_CIRCUIT, bad, "--aes", "--model", model, "--json")
            self.assertEqual(code, 1)
            res = json.loads(out)
            self.assertEqual([r["ok"] for r in res], [True, False])
            self.assertEqual(res[0]["metrics"]["cost"], 104)
            self.assertEqual(res[1]["mismatch"]["x"] >= 0, True)
            code, out, _ = self.cli(REF_CIRCUIT, "--aes", "--expect-GD", 29)
            self.assertEqual(code, 1)
            self.assertIn("GD = 30, expected 29", out)

    def test_cli_tables(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.json"
            t.write_text(json.dumps({"sboxes": [
                {"name": "aes", "n": 8, "m": 8, "table": AES[2]},
                {"name": "inv", "n": 8, "m": 8, "table": AES_INV[2]}]}))
            f = Path(d) / "f.json"
            f.write_text(json.dumps({"n": 8, "m": 8, "table": AES[2]}))
            self.assertEqual(self.cli(REF_CIRCUIT, "--table", t, "--name", "aes")[0], 0)
            self.assertEqual(self.cli(REF_CIRCUIT, "--table", t, "--name", "inv")[0], 1)
            self.assertEqual(self.cli(REF_CIRCUIT, "--table", t, "--name", "nope")[0], 2)
            self.assertEqual(self.cli(REF_CIRCUIT, "--fn", f)[0], 0)
            inv_file = NIST / "aes-invsbox" / "aes-invsbox-a32-ad5-g106-gd25-xx74-9.circ.txt"
            self.assertEqual(self.cli(inv_file, "--aes-inv")[0], 0)

    def test_cli_main_in_process(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = V.main([str(REF_CIRCUIT), "--aes", "--any-order"])
        self.assertEqual(code, 0)
        self.assertIn("order=msb/msb", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
