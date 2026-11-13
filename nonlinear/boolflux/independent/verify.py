#!/usr/bin/env python3
"""Independent verifier for Boolean circuit files (NCFF / NIST 2020 .slp subset).

Written from a specification only; it deliberately shares no code with the
other packages in this repository.  Python 3.12 standard library only.

What it does, per file:
  1. parse the first circuit (structural rules: single assignment, inputs never
     assigned, operands defined on an earlier line, declared outputs assigned,
     known gate names, correct arity);
  2. evaluate the circuit exhaustively, one input integer at a time, on plain
     Python ints 0/1, and compare with the target table;
  3. compute metrics G, per-type counts, A, GD, AD, and (with a cost model)
     the cost, library violations and optionally a weighted depth WD;
  4. check optional assertions (--expect-G, --max-AD, ...).

Bit order "msb/msb" (default): the i-th declared input is bit (n-1-i) of the
input integer and the j-th declared output is bit (m-1-j) of the output
integer.  "lsb" means the i-th declared wire is bit i.

Run "python3 verify.py --help" for the command line.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Gate library
# ---------------------------------------------------------------------------

ARITY = {
    "XOR": 2, "XNOR": 2,
    "AND": 2, "NAND": 2, "OR": 2, "NOR": 2,
    "ANDN": 2, "ORN": 2,
    "NOT": 1, "BUF": 1,
}
NONLINEAR = frozenset({"AND", "NAND", "OR", "NOR", "ANDN", "ORN"})
CONSTANTS = {"0": 0, "1": 1}

# Semantics on 0/1 ints.  ANDN/ORN complement the SECOND operand.
SEMANTICS = {
    "XOR":  lambda a, b: a ^ b,
    "XNOR": lambda a, b: 1 - (a ^ b),
    "AND":  lambda a, b: a & b,
    "NAND": lambda a, b: 1 - (a & b),
    "OR":   lambda a, b: a | b,
    "NOR":  lambda a, b: 1 - (a | b),
    "ANDN": lambda a, b: a & (1 - b),
    "ORN":  lambda a, b: a | (1 - b),
    "NOT":  lambda a: 1 - a,
    "BUF":  lambda a: a,
}

ORDERS = ("msb", "lsb")
ALL_ORDER_PAIRS = (("msb", "msb"), ("msb", "lsb"), ("lsb", "msb"), ("lsb", "lsb"))


class CircuitError(Exception):
    """Parse or structural failure; .errors holds every message found."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


class SpecError(Exception):
    """Bad function table or cost model (a usage problem, not a circuit failure)."""


@dataclass
class Gate:
    line: int          # 1-based line number in the source text
    op: str            # upper-case gate name
    out: str
    args: tuple


@dataclass
class Circuit:
    name: str
    inputs: list
    outputs: list
    internal: list
    gates: list
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_HEADER = re.compile(r"^(inputs|outputs|internal|gatesyntax)\s*:\s*(.*)$", re.IGNORECASE)
_RANGE = re.compile(r"^(\D(?:.*\D)?)(\d+):(\D(?:.*\D)?)(\d+)$")


def strip_comment(line: str) -> str:
    """Remove a '%' or '#' comment (whichever comes first) and surrounding blanks."""
    cut = len(line)
    for ch in "%#":
        k = line.find(ch)
        if 0 <= k < cut:
            cut = k
    return line[:cut].strip()


def expand_names(text: str, lineno: int, errors: list) -> list:
    """Expand a declaration list such as 'x0:x7 y z'.  Ranges keep the written
    direction (x7:x0 = x7 x6 ... x0); a leading zero fixes the digit width."""
    names = []
    for tok in text.replace(",", " ").split():
        if ":" not in tok:
            names.append(tok)
            continue
        m = _RANGE.match(tok)
        if not m or m.group(1) != m.group(3):
            errors.append(f"line {lineno}: bad name range '{tok}'")
            continue
        prefix, s, e = m.group(1), m.group(2), m.group(4)
        width = len(s) if (len(s) > 1 and s.startswith("0")) else 0
        a, b = int(s), int(e)
        step = 1 if b >= a else -1
        for k in range(a, b + step, step):
            names.append(f"{prefix}{str(k).zfill(width)}")
    return names


def parse_circuit(text: str) -> Circuit:
    """Parse the first circuit in `text` and check the structural rules.
    Raises CircuitError listing every problem found."""
    errors: list = []
    notes: list = []
    state = "pre"          # pre -> header -> slp -> slp_done -> post
    name = ""
    inputs: list = []
    outputs: list = []
    internal: list = []
    gates: list = []
    seen = {"inputs": 0, "outputs": 0}
    n_circuits = 0
    ignored_header = 0
    ignored_after = 0

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line:
            continue
        toks = line.split()
        key = " ".join(t.lower() for t in toks[:2])

        if key == "begin circuit":
            n_circuits += 1
            if state == "pre":
                state = "header"
                name = toks[2] if len(toks) > 2 else ""
            elif state != "post":
                errors.append(f"line {lineno}: 'begin circuit' inside an unfinished circuit")
            continue
        if state in ("pre", "post"):
            continue

        if state == "header":
            if key == "begin slp":
                state = "slp"
                continue
            if key == "end circuit":
                errors.append(f"line {lineno}: 'end circuit' before 'begin SLP'")
                state = "post"
                continue
            m = _HEADER.match(line)
            if not m:
                ignored_header += 1
                continue
            kw, rest = m.group(1).lower(), m.group(2)
            if kw == "inputs":
                seen["inputs"] += 1
                inputs.extend(expand_names(rest, lineno, errors))
            elif kw == "outputs":
                seen["outputs"] += 1
                outputs.extend(expand_names(rest, lineno, errors))
            elif kw == "internal":
                internal.extend(expand_names(rest, lineno, errors))
            else:  # gatesyntax
                if [t.lower() for t in rest.split()] != ["gatename", "output", "inputs"]:
                    errors.append(f"line {lineno}: unsupported GateSyntax '{rest.strip()}' "
                                  "(only 'GateName Output Inputs')")
            continue

        if state == "slp":
            if key == "end slp":
                state = "slp_done"
                continue
            op = toks[0].upper()
            if op not in ARITY:
                errors.append(f"line {lineno}: unknown gate type '{toks[0]}'")
                continue
            if len(toks) < 2:
                errors.append(f"line {lineno}: {op} has no output wire")
                continue
            args = tuple(toks[2:])
            if len(args) != ARITY[op]:
                errors.append(f"line {lineno}: {op} takes {ARITY[op]} operand(s), got {len(args)}")
                continue
            gates.append(Gate(lineno, op, toks[1], args))
            continue

        if state == "slp_done":
            if key == "end circuit":
                state = "post"
            else:
                ignored_after += 1
            continue

    if state == "pre":
        errors.append("no 'begin circuit' found")
    elif state == "header":
        errors.append("missing 'begin SLP'")
    elif state == "slp":
        errors.append("missing 'end SLP'")
    elif state == "slp_done":
        errors.append("missing 'end circuit'")

    if n_circuits > 1:
        notes.append(f"file holds {n_circuits} circuits; only the first ('{name}') was verified")
    if ignored_header:
        notes.append(f"{ignored_header} unrecognised header line(s) ignored")
    if ignored_after:
        notes.append(f"{ignored_after} line(s) between 'end SLP' and 'end circuit' ignored")

    if state != "pre":
        if not seen["inputs"]:
            errors.append("no 'Inputs:' declaration")
        if not seen["outputs"]:
            errors.append("no 'Outputs:' declaration")

    circ = Circuit(name, inputs, outputs, internal, gates, notes)
    errors.extend(structure_errors(circ))
    if errors:
        raise CircuitError(errors)
    return circ


def structure_errors(c: Circuit) -> list:
    """All violations of the structural rules (empty list = structurally fine)."""
    errs = []
    if not c.inputs:
        errs.append("no inputs declared")
    if not c.outputs:
        errs.append("no outputs declared")

    def dups(names):
        seen, d = set(), []
        for x in names:
            if x in seen and x not in d:
                d.append(x)
            seen.add(x)
        return d

    for x in dups(c.inputs):
        errs.append(f"input '{x}' declared more than once")
    for x in dups(c.outputs):
        errs.append(f"output '{x}' declared more than once")
    for x in c.inputs + c.outputs:
        if x in CONSTANTS:
            errs.append(f"constant '{x}' used as a declared wire name")
    inset = set(c.inputs)
    for x in c.outputs:
        if x in inset:
            errs.append(f"'{x}' is declared both as input and as output")

    first_line = {}
    for g in c.gates:
        first_line.setdefault(g.out, g.line)

    assigned = {}
    for g in c.gates:
        if g.out in CONSTANTS:
            errs.append(f"line {g.line}: constant '{g.out}' used as gate output")
        elif g.out in inset:
            errs.append(f"line {g.line}: input '{g.out}' is assigned")
        elif g.out in assigned:
            errs.append(f"line {g.line}: wire '{g.out}' assigned more than once "
                        f"(first at line {assigned[g.out]})")
        for a in g.args:
            if a in CONSTANTS or a in inset or a in assigned:
                continue
            if first_line.get(a) == g.line:
                errs.append(f"line {g.line}: operand '{a}' is the gate's own output")
            elif a in first_line:
                errs.append(f"line {g.line}: operand '{a}' is assigned on a later line "
                            f"({first_line[a]})")
            else:
                errs.append(f"line {g.line}: operand '{a}' is never assigned")
        if g.out not in CONSTANTS and g.out not in inset and g.out not in assigned:
            assigned[g.out] = g.line

    for x in c.outputs:
        if x not in assigned and x not in inset:
            errs.append(f"output '{x}' is never assigned")

    if c.internal and not errs:
        declared = set(c.outputs) | set(c.internal)
        undeclared = [g.out for g in c.gates if g.out not in declared]
        if undeclared:
            c.notes.append(f"{len(undeclared)} gate output(s) not listed in Internal/Outputs "
                           f"(e.g. '{undeclared[0]}')")
    return errs


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def parse_file(path: str) -> Circuit:
    return parse_circuit(read_text(path))


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_bits(c: Circuit, bits) -> list:
    """Evaluate on input bits given in declaration order; return output bits
    in declaration order."""
    env = dict(CONSTANTS)
    for name, b in zip(c.inputs, bits, strict=True):
        env[name] = b
    for g in c.gates:
        env[g.out] = SEMANTICS[g.op](*[env[a] for a in g.args])
    return [env[o] for o in c.outputs]


def evaluate_int(c: Circuit, x: int, in_order: str = "msb", out_order: str = "msb") -> int:
    n, m = len(c.inputs), len(c.outputs)
    if in_order == "msb":
        bits = [(x >> (n - 1 - i)) & 1 for i in range(n)]
    else:
        bits = [(x >> i) & 1 for i in range(n)]
    out = evaluate_bits(c, bits)
    y = 0
    for j, b in enumerate(out):
        y |= b << ((m - 1 - j) if out_order == "msb" else j)
    return y


def check_function(c: Circuit, n: int, m: int, table, in_order="msb", out_order="msb"):
    """Exhaustive check.  Returns None on success or the first mismatch as a
    dict {x, expected, got}.  Raises ValueError on an n/m shape mismatch."""
    if in_order not in ORDERS or out_order not in ORDERS:
        raise ValueError(f"bad order {in_order}/{out_order}")
    if len(c.inputs) != n or len(c.outputs) != m:
        raise ValueError(f"circuit has {len(c.inputs)} inputs / {len(c.outputs)} outputs, "
                         f"function has n={n} / m={m}")
    for x in range(1 << n):
        got = evaluate_int(c, x, in_order, out_order)
        if got != table[x]:
            return {"x": x, "expected": table[x], "got": got}
    return None


# ---------------------------------------------------------------------------
# Target functions
# ---------------------------------------------------------------------------

def gf256_mul(a: int, b: int) -> int:
    """Multiply in GF(2^8) modulo x^8+x^4+x^3+x+1 (0x11B)."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
    return r


def aes_sbox() -> list:
    """Forward AES S-box from FIPS-197 (inverse in GF(2^8), then the affine map)."""
    inv = [0] * 256
    for a in range(1, 256):
        for b in range(1, 256):
            if gf256_mul(a, b) == 1:
                inv[a] = b
                break
    c = 0x63
    s = []
    for x in range(256):
        b = inv[x]
        y = 0
        for i in range(8):
            bit = ((b >> i) ^ (b >> ((i + 4) % 8)) ^ (b >> ((i + 5) % 8))
                   ^ (b >> ((i + 6) % 8)) ^ (b >> ((i + 7) % 8)) ^ (c >> i)) & 1
            y |= bit << i
        s.append(y)
    _self_check(s)
    return s


def aes_inv_sbox() -> list:
    s = aes_sbox()
    inv = [0] * 256
    for x, y in enumerate(s):
        inv[y] = x
    for x in range(256):
        assert inv[s[x]] == x and s[inv[x]] == x, "inverse S-box does not compose to identity"
    return inv


def _self_check(s):
    assert s[0x00] == 0x63, "S(0x00) != 0x63"
    assert s[0x01] == 0x7C, "S(0x01) != 0x7c"
    assert s[0x53] == 0xED, "S(0x53) != 0xed"
    assert sorted(s) == list(range(256)), "S-box is not a permutation"


def validate_fn(n, m, table, where="function"):
    for k, v in (("n", n), ("m", m)):
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            raise SpecError(f"{where}: '{k}' must be a positive integer, got {v!r}")
    if not isinstance(table, list) or len(table) != (1 << n):
        raise SpecError(f"{where}: table must be a list of 2^n = {1 << n} entries")
    for x, v in enumerate(table):
        if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v < (1 << m):
            raise SpecError(f"{where}: table[{x}] = {v!r} is not an integer in [0, 2^m)")
    return n, m, table


def load_table(path: str, name: str):
    """Load entry `name` from {"sboxes": [{"name","n","m","table"}, ...]}."""
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("sboxes"), list):
        raise SpecError(f"{path}: expected an object with an 'sboxes' list")
    hits = [e for e in data["sboxes"] if isinstance(e, dict) and e.get("name") == name]
    if not hits:
        names = [e.get("name") for e in data["sboxes"] if isinstance(e, dict)]
        raise SpecError(f"{path}: no entry named {name!r} (have {names})")
    if len(hits) > 1:
        raise SpecError(f"{path}: {len(hits)} entries named {name!r}")
    e = hits[0]
    return validate_fn(e.get("n"), e.get("m"), e.get("table"), f"{path}:{name}")


def load_fn(path: str):
    """Load a single {"n","m","table"} object."""
    with open(path, "r", encoding="utf-8-sig") as f:
        e = json.load(f)
    if not isinstance(e, dict):
        raise SpecError(f"{path}: expected a JSON object")
    return validate_fn(e.get("n"), e.get("m"), e.get("table"), path)


# ---------------------------------------------------------------------------
# Cost models and metrics
# ---------------------------------------------------------------------------

def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate_model(model: dict, where="model") -> dict:
    if not isinstance(model, dict) or not isinstance(model.get("gates"), dict):
        raise SpecError(f"{where}: expected an object with a 'gates' mapping")
    for key in ("gates", "depth_weights"):
        table = model.get(key)
        if table is None:
            continue
        if not isinstance(table, dict):
            raise SpecError(f"{where}: '{key}' must be a mapping")
        for g, v in table.items():
            if g not in ARITY:
                raise SpecError(f"{where}: unknown gate type {g!r} in '{key}'")
            if not _number(v) or v < 0:
                raise SpecError(f"{where}: {key}[{g}] = {v!r} is not a non-negative number")
            if g == "BUF" and v != 0:
                raise SpecError(f"{where}: BUF is always free and depth-transparent; "
                                f"{key}[BUF] must be 0 or absent")
    return model


def load_model(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return validate_model(json.load(f), path)


def compute_metrics(c: Circuit, model: dict | None = None) -> dict:
    counts = {}
    for g in c.gates:
        counts[g.op] = counts.get(g.op, 0) + 1
    G = sum(v for k, v in counts.items() if k != "BUF")
    A = sum(counts.get(k, 0) for k in NONLINEAR)
    XX = counts.get("XOR", 0) + counts.get("XNOR", 0)

    weights = None
    if model is not None and model.get("depth_weights") is not None:
        weights = {k: 1 for k in ARITY}
        weights.update(model["depth_weights"])
        weights["BUF"] = 0

    gd = {w: 0 for w in list(CONSTANTS) + c.inputs}
    ad = dict(gd)
    wd = dict(gd)
    for g in c.gates:
        mg = max(gd[a] for a in g.args)
        ma = max(ad[a] for a in g.args)
        mw = max(wd[a] for a in g.args)
        if g.op == "BUF":
            gd[g.out], ad[g.out], wd[g.out] = mg, ma, mw
        else:
            gd[g.out] = mg + 1
            ad[g.out] = ma + (1 if g.op in NONLINEAR else 0)
            wd[g.out] = mw + (weights[g.op] if weights else 1)

    live = set(c.outputs)
    for g in reversed(c.gates):
        if g.out in live:
            live.update(g.args)
    dead = sum(1 for g in c.gates if g.out not in live and g.op != "BUF")

    met = {
        "G": G,
        "counts": dict(sorted(counts.items())),
        "A": A,
        "XX": XX,
        "GD": max(gd[o] for o in c.outputs),
        "AD": max(ad[o] for o in c.outputs),
        "dead": dead,
        "n": len(c.inputs),
        "m": len(c.outputs),
    }
    if model is not None:
        allowed = model["gates"]
        violations = sorted(k for k in counts if k != "BUF" and k not in allowed)
        met["model"] = model.get("name")
        met["library_violations"] = violations
        if violations:
            met["cost"] = None
        else:
            met["cost"] = math.fsum(allowed[k] * v for k, v in counts.items() if k != "BUF")
        if weights is not None:
            met["WD"] = max(wd[o] for o in c.outputs)
    return met


# ---------------------------------------------------------------------------
# Verification driver
# ---------------------------------------------------------------------------

ASSERT_KEYS = ("G", "A", "GD", "AD", "WD", "cost")


def _close(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def check_assertions(met: dict, expect: dict | None) -> list:
    """expect maps 'expect_G' / 'max_AD' / ... to numbers."""
    errs = []
    for key, want in (expect or {}).items():
        if want is None:
            continue
        kind, metric = key.split("_", 1)
        have = met.get(metric)
        if have is None:
            errs.append(f"{key}: metric {metric} not available (needs --model"
                        f"{' with depth_weights' if metric == 'WD' else ''})")
        elif kind == "expect" and not _close(have, want):
            errs.append(f"{metric} = {fmt_num(have)}, expected {fmt_num(want)}")
        elif kind == "max" and have > want and not _close(have, want):
            errs.append(f"{metric} = {fmt_num(have)} exceeds max {fmt_num(want)}")
    return errs


def verify_circuit(c: Circuit, fn, model=None, in_order="msb", out_order="msb",
                   any_order=False, expect=None) -> dict:
    """fn = (n, m, table).  Returns a result dict (see verify_file)."""
    n, m, table = fn
    res = {"circuit": c.name, "ok": False, "errors": [], "notes": list(c.notes),
           "order": None, "orders_matched": [], "mismatch": None, "metrics": None}
    met = compute_metrics(c, model)
    res["metrics"] = met
    if model is not None and met["library_violations"]:
        res["errors"].append("gate type(s) outside model '%s': %s" % (
            model.get("name"), ", ".join(f"{k} x{met['counts'][k]}"
                                         for k in met["library_violations"])))

    pairs = ALL_ORDER_PAIRS if any_order else ((in_order, out_order),)
    try:
        first_mismatch = None
        for io, oo in pairs:
            mm = check_function(c, n, m, table, io, oo)
            if mm is None:
                res["orders_matched"].append(f"{io}/{oo}")
            elif first_mismatch is None:
                first_mismatch = dict(mm, order=f"{io}/{oo}")
        if res["orders_matched"]:
            res["order"] = res["orders_matched"][0]
        else:
            res["mismatch"] = first_mismatch
            mm = first_mismatch
            res["errors"].append(
                "function mismatch (%s%s): x=0x%x expected 0x%x got 0x%x" % (
                    mm["order"], ", no order matched" if any_order else "",
                    mm["x"], mm["expected"], mm["got"]))
    except ValueError as e:
        res["errors"].append(f"shape mismatch: {e}")

    res["errors"].extend(check_assertions(met, expect))
    res["ok"] = not res["errors"]
    return res


def verify_text(text: str, fn, **kw) -> dict:
    try:
        c = parse_circuit(text)
    except CircuitError as e:
        return {"circuit": None, "ok": False, "errors": e.errors, "notes": [],
                "order": None, "orders_matched": [], "mismatch": None, "metrics": None}
    return verify_circuit(c, fn, **kw)


def verify_file(path: str, fn, **kw) -> dict:
    """Verify one file.  Keyword args as verify_circuit (model, in_order,
    out_order, any_order, expect).  Result keys: file, circuit, ok, errors,
    notes, order, orders_matched, mismatch, metrics."""
    try:
        text = read_text(path)
    except OSError as e:
        res = {"circuit": None, "ok": False, "errors": [f"cannot read: {e}"], "notes": [],
               "order": None, "orders_matched": [], "mismatch": None, "metrics": None}
    else:
        res = verify_text(text, fn, **kw)
    return {"file": path, **res}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def fmt_num(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return format(v, ".10g")
    return str(v)


def format_line(r: dict) -> str:
    parts = ["ok  " if r["ok"] else "FAIL", r["file"]]
    met = r.get("metrics")
    if met:
        parts.append(f"G={met['G']}")
        parts.append("[" + " ".join(f"{k}={v}" for k, v in met["counts"].items()) + "]")
        parts.append(f"A={met['A']} AD={met['AD']} GD={met['GD']}")
        if "cost" in met:
            parts.append(f"cost={fmt_num(met['cost'])}")
        if "WD" in met:
            parts.append(f"WD={fmt_num(met['WD'])}")
    if r.get("order"):
        parts.append(f"order={r['order']}")
    line = " ".join(parts)
    if r["errors"]:
        line += " -- " + "; ".join(r["errors"])
    if r.get("notes"):
        line += " (note: " + "; ".join(r["notes"]) + ")"
    return line


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Independent exhaustive verifier for Boolean circuit files.")
    p.add_argument("files", nargs="+", metavar="FILE")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--aes", action="store_true", help="forward AES S-box")
    g.add_argument("--aes-inv", action="store_true", help="inverse AES S-box")
    g.add_argument("--table", metavar="T.json", help='{"sboxes": [...]} file (needs --name)')
    g.add_argument("--fn", metavar="F.json", help='single {"n","m","table"} file')
    p.add_argument("--name", help="entry name inside --table")
    p.add_argument("--model", metavar="M.json", help="cost model / gate library")
    p.add_argument("--order", choices=ORDERS, help="set both input and output bit order")
    p.add_argument("--in-order", choices=ORDERS, help="input bit order (default msb)")
    p.add_argument("--out-order", choices=ORDERS, help="output bit order (default msb)")
    p.add_argument("--any-order", action="store_true", help="accept any of the four order pairs")
    p.add_argument("--json", action="store_true", help="print a JSON list of results")
    for k in ASSERT_KEYS:
        typ = float if k in ("cost", "WD") else int
        p.add_argument(f"--expect-{k}", dest=f"expect_{k}", type=typ, metavar="N")
        p.add_argument(f"--max-{k}", dest=f"max_{k}", type=typ, metavar="N")
    return p


def main(argv=None) -> int:
    p = build_parser()
    a = p.parse_args(argv)
    try:
        if a.aes:
            fn = (8, 8, aes_sbox())
        elif a.aes_inv:
            fn = (8, 8, aes_inv_sbox())
        elif a.table:
            if not a.name:
                p.error("--table needs --name")
            fn = load_table(a.table, a.name)
        else:
            fn = load_fn(a.fn)
        model = load_model(a.model) if a.model else None
    except (SpecError, OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.name and not a.table:
        p.error("--name only applies to --table")

    in_order = a.in_order or a.order or "msb"
    out_order = a.out_order or a.order or "msb"
    expect = {f"{kind}_{k}": getattr(a, f"{kind}_{k}")
              for k in ASSERT_KEYS for kind in ("expect", "max")}

    results = [verify_file(f, fn, model=model, in_order=in_order, out_order=out_order,
                           any_order=a.any_order, expect=expect) for f in a.files]
    if a.json:
        print(json.dumps(results, indent=1))
    else:
        for r in results:
            print(format_line(r))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
