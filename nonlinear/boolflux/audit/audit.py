#!/usr/bin/env python3
"""Independent audit of BoolFlux circuit claims.

Standard library only. Imports nothing from nonlinear/ (no optimizer, no
boolcirc, no independent/verify.py code). Targets are computed here from
their definitions; small S-box tables are read as data from
nonlinear/boolflux/benchmarks/sboxes.json.

Usage (from the repo root):
    python3 nonlinear/boolflux/audit/audit.py [--second-opinion]

Writes nonlinear/boolflux/audit/audit.json (machine-readable) and
nonlinear/boolflux/audit/AUDIT-tables.md (generated tables, included by AUDIT.md).
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

BIN = {"XOR", "XNOR", "AND", "NAND", "OR", "NOR", "ANDN", "ORN"}
UN = {"NOT", "BUF"}
NONLIN = {"AND", "NAND", "OR", "NOR", "ANDN", "ORN"}
MODELS = {
    "bgc": {"AND", "OR", "XOR", "NOT"},
    "gc6": {"AND", "OR", "XOR", "XNOR", "NAND", "NOR", "NOT"},
    "nist": {"AND", "XOR", "XNOR", "NOT"},
    "xag": {"AND", "XOR", "NOT"},
    "gc": {"AND", "OR", "XOR", "XNOR", "NAND", "NOR", "ANDN", "ORN", "NOT"},
}

# ----------------------------------------------------------------- targets


def gf_mul(a, b, poly, deg):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> deg & 1:
            a ^= poly
    return r


def gf_inv_table(poly, deg):
    size = 1 << deg
    inv = [0] * size
    for x in range(1, size):
        ys = [y for y in range(1, size) if gf_mul(x, y, poly, deg) == 1]
        assert len(ys) == 1
        inv[x] = ys[0]
    return inv


def aes_sbox():
    inv = gf_inv_table(0x11B, 8)
    s = []
    for x in range(256):
        b = inv[x]
        o = 0
        for i in range(8):
            bit = (b >> i ^ b >> ((i + 4) % 8) ^ b >> ((i + 5) % 8)
                   ^ b >> ((i + 6) % 8) ^ b >> ((i + 7) % 8) ^ 0x63 >> i) & 1
            o |= bit << i
        s.append(o)
    # self-checks: FIPS-197 examples and bijectivity
    assert s[0x00] == 0x63 and s[0x01] == 0x7C and s[0x53] == 0xED
    assert s[0xFF] == 0x16 and s[0x10] == 0xCA and sorted(s) == list(range(256))
    return s


def small_targets():
    t = {}
    t["maj3"] = (3, 1, [1 if bin(x).count("1") >= 2 else 0 for x in range(8)])
    t["fulladd"] = (3, 2, [bin(x).count("1") for x in range(8)])  # carry MSB, sum LSB
    t["gf16-mul"] = (8, 4, [gf_mul(x >> 4, x & 15, 0x13, 4) for x in range(256)])
    t["gf16-inv"] = (4, 4, gf_inv_table(0x13, 4))
    assert t["gf16-inv"][2][2] == 9 and t["gf16-mul"][2][0x23] == 6
    assert all(gf_mul(x, t["gf16-inv"][2][x], 0x13, 4) == 1 for x in range(1, 16))
    with open(os.path.join(ROOT, "nonlinear/boolflux/benchmarks/sboxes.json"), encoding="utf-8") as f:
        d = json.load(f)
    for e in d["sboxes"]:
        tab = e["table"]
        assert len(tab) == 1 << e["n"] and all(0 <= v < (1 << e["m"]) for v in tab)
        t[e["name"]] = (e["n"], e["m"], tab)
    return t


# ------------------------------------------------------------------ parser


RANGE = re.compile(r"^([A-Za-z_][A-Za-z_]*?)(\d+):([A-Za-z_][A-Za-z_]*?)(\d+)$")


def expand(tokens):
    out = []
    for tok in tokens:
        m = RANGE.match(tok)
        if m and m.group(1) == m.group(3):
            a, b = int(m.group(2)), int(m.group(4))
            step = 1 if b >= a else -1
            out += [m.group(1) + str(i) for i in range(a, b + step, step)]
        else:
            out.append(tok)
    return out


def parse(path):
    """Return a list of circuits found in the file."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    has_begin = any(re.match(r"^\s*begin\s+circuit\b", ln, re.I) for ln in lines)
    circuits = []
    cur = None
    comments = []
    in_slp = False

    def new(name):
        return {"name": name, "inputs": [], "outputs": [], "internal": [], "gates": [],
                "header": list(comments), "issues": [], "slp_seen": False, "slp_closed": False}

    if not has_begin:
        cur = new(os.path.basename(path))
    for no, raw in enumerate(lines, 1):
        cpos = [p for p in (raw.find("%"), raw.find("#")) if p >= 0]
        code = raw[:min(cpos)] if cpos else raw
        if cpos and not in_slp:
            comments.append(raw[min(cpos):].lstrip("%# ").rstrip())
            if cur is not None:
                cur["header"].append(comments[-1])
        s = code.strip()
        if not s:
            continue
        m = re.match(r"^begin\s+circuit\s*(.*)$", s, re.I)
        if m:
            cur = new(m.group(1).strip())
            continue
        if re.match(r"^end\s+circuit\b", s, re.I):
            if cur is not None:
                circuits.append(cur)
            cur = None
            comments = []
            continue
        if cur is None:
            continue
        if re.match(r"^begin\s+SLP\b", s, re.I):
            in_slp = True
            cur["slp_seen"] = True
            continue
        if re.match(r"^end\s+SLP\b", s, re.I):
            in_slp = False
            cur["slp_closed"] = True
            continue
        if in_slp:
            toks = s.split()
            cur["gates"].append((toks[0].upper(), toks[1] if len(toks) > 1 else None, toks[2:], no))
            continue
        m = re.match(r"^(Inputs|Outputs|Internal|GateSyntax)\s*:\s*(.*)$", s, re.I)
        if m:
            key = m.group(1).lower()
            if key == "gatesyntax":
                if m.group(2).split() != ["GateName", "Output", "Inputs"]:
                    cur["issues"].append("unexpected GateSyntax: " + m.group(2))
            else:
                cur[key] += expand(m.group(2).split())
            continue
        cur["issues"].append("unparsed header line %d: %s" % (no, s))
    if cur is not None:
        if has_begin:
            cur["issues"].append("missing 'end circuit'")
        circuits.append(cur)
    return circuits


# --------------------------------------------------------------- evaluator


def apply(op, a, b, mask):
    if op == "XOR":
        return a ^ b
    if op == "XNOR":
        return ~(a ^ b) & mask
    if op == "AND":
        return a & b
    if op == "NAND":
        return ~(a & b) & mask
    if op == "OR":
        return a | b
    if op == "NOR":
        return ~(a | b) & mask
    if op == "ANDN":
        return a & ~b & mask
    if op == "ORN":
        return (a | ~b) & mask
    if op == "NOT":
        return ~a & mask
    if op == "BUF":
        return a
    raise ValueError(op)


def analyse(c, n, m, table):
    """Structural checks, exhaustive functional check, metrics."""
    errors, flags = list(c["issues"]), []
    ins, outs = c["inputs"], c["outputs"]
    if len(ins) != n:
        errors.append("expected %d inputs, file declares %d" % (n, len(ins)))
    if len(outs) != m:
        errors.append("expected %d outputs, file declares %d" % (m, len(outs)))
    if len(set(ins)) != len(ins):
        errors.append("duplicate input names")
    if len(set(outs)) != len(outs):
        errors.append("duplicate output names")
    if not c["slp_seen"] or not c["slp_closed"]:
        errors.append("missing begin/end SLP")
    for tok in ins + outs:
        if re.search(r"[~!']", tok) or tok in ("0", "1"):
            errors.append("suspicious IO token %r" % tok)
    for o in outs:
        if o in ins:
            errors.append("output %s is an input (no gate)" % o)
    N = 1 << n
    mask = (1 << N) - 1
    val = {"0": 0, "1": mask}
    lev = {"0": 0, "1": 0}
    alev = {"0": 0, "1": 0}
    for i, name in enumerate(ins):
        v = 0
        for x in range(N):
            if x >> (n - 1 - i) & 1:
                v |= 1 << x
        val[name] = v
        lev[name] = 0
        alev[name] = 0
    counts = {}
    const_ops = []
    same_ops = []
    level_hist = {}
    and_hist = {}
    fanin = {}
    order = []
    for op, out, args, no in c["gates"]:
        if op not in BIN | UN:
            errors.append("line %d: unknown gate %s" % (no, op))
            continue
        arity = 2 if op in BIN else 1
        if out is None or len(args) != arity:
            errors.append("line %d: wrong arity for %s" % (no, op))
            continue
        if out in ("0", "1") or re.search(r"[~!']", out) or any(re.search(r"[~!']", a) for a in args):
            errors.append("line %d: suspicious token" % no)
        if out in ins:
            errors.append("line %d: assigns input %s" % (no, out))
            continue
        if out in val:
            errors.append("line %d: %s assigned twice" % (no, out))
            continue
        bad = [a for a in args if a not in val]
        if bad:
            errors.append("line %d: operand(s) %s not defined earlier" % (no, bad))
            continue
        counts[op] = counts.get(op, 0) + 1
        if any(a in ("0", "1") for a in args):
            const_ops.append((op, tuple(args), no))
        if arity == 2 and args[0] == args[1]:
            same_ops.append((op, tuple(args), no))
        a = val[args[0]]
        b = val[args[1]] if arity == 2 else 0
        val[out] = apply(op, a, b, mask)
        step = 0 if op == "BUF" else 1
        lev[out] = step + max(lev[x] for x in args)
        alev[out] = (1 if op in NONLIN else 0) + max(alev[x] for x in args)
        if op != "BUF":
            level_hist[lev[out]] = level_hist.get(lev[out], 0) + 1
        if op in NONLIN:
            and_hist[alev[out]] = and_hist.get(alev[out], 0) + 1
        fanin[out] = [x for x in args if x not in ("0", "1")]
        order.append((op, out, args))
    missing = [o for o in outs if o not in val or o in ins]
    for o in missing:
        if o not in ins:
            errors.append("output %s never assigned" % o)
    declared = set(ins) | set(outs) | set(c["internal"])
    undeclared = [g[1] for g in order if g[1] not in declared]
    if c["internal"] and undeclared:
        flags.append("%d gate outputs not declared in Internal/Outputs" % len(undeclared))
    # functional check (bitsliced) and an independent scalar re-evaluation
    func_ok = not missing and len(outs) == m and len(ins) == n and not errors
    mism = None
    if func_ok:
        for j, o in enumerate(outs):
            exp = 0
            for x in range(N):
                if table[x] >> (m - 1 - j) & 1:
                    exp |= 1 << x
            if val[o] != exp:
                diff = val[o] ^ exp
                x = (diff & -diff).bit_length() - 1
                mism = {"output": o, "x": x}
                func_ok = False
                break
        if func_ok:  # scalar cross-check
            for x in range(N):
                w = {"0": 0, "1": 1}
                for i, name in enumerate(ins):
                    w[name] = x >> (n - 1 - i) & 1
                for op, out, args in order:
                    w[out] = apply(op, w[args[0]], w[args[1]] if len(args) == 2 else 0, 1)
                y = 0
                for o in outs:
                    y = y << 1 | w[o]
                if y != table[x]:
                    func_ok = False
                    mism = {"scalar_x": x, "got": y, "expected": table[x]}
                    break
    # dead gates
    live = set()
    stack = [o for o in outs if o in fanin]
    while stack:
        g = stack.pop()
        if g in live:
            continue
        live.add(g)
        stack += [x for x in fanin.get(g, []) if x in fanin]
    dead = [g[1] for g in order if g[1] not in live]
    # functionally constant or duplicate gates (information only)
    seen = {}
    dup_fn = 0
    const_fn = []
    for op, out, args in order:
        v = val[out]
        if v in (0, mask):
            const_fn.append(out)
        key = min(v, ~v & mask)
        if key in seen:
            dup_fn += 1
        seen[key] = out
    for x in ins:
        seen.setdefault(min(val[x], ~val[x] & mask), x)
    outs_const = [o for o in outs if o in val and val[o] in (0, mask)]
    if outs_const:
        errors.append("constant outputs: %s" % outs_const)
    if "BUF" in counts:
        flags.append("BUF present (%d)" % counts["BUF"])
    if dead:
        flags.append("%d dead gates" % len(dead))
    xnor_c0 = sum(1 for op, a, _ in const_ops if op == "XNOR" and sorted(a)[0] == "0" and "1" not in a)
    odd_const = [(op, a, no) for op, a, no in const_ops if not (op == "XNOR" and a.count("0") == 1 and "1" not in a)]
    if odd_const:
        flags.append("constant-operand gates other than XNOR-with-0: %s" % odd_const)
    if same_ops:
        flags.append("gates with identical operands: %s" % same_ops)
    if const_fn:
        flags.append("gates computing a constant: %s" % const_fn)
    G = sum(v for k, v in counts.items() if k != "BUF")
    met = {
        "G": G, "G_lines": len(c["gates"]),
        "A": sum(counts.get(k, 0) for k in NONLIN),
        "GD": max([lev[o] for o in outs if o in lev] or [0]),
        "AD": max([alev[o] for o in outs if o in alev] or [0]),
        "XOR": counts.get("XOR", 0), "XNOR": counts.get("XNOR", 0), "NOT": counts.get("NOT", 0),
        "XX": counts.get("XOR", 0) + counts.get("XNOR", 0),
        "XNOR_const": sum(1 for op, a, _ in const_ops if op == "XNOR"),
        "XNOR_with_0": xnor_c0,
        "counts": dict(sorted(counts.items())),
        "dead": len(dead),
        "dup_functions": dup_fn,
        "gates_per_level": [level_hist.get(i, 0) for i in range(1, max(level_hist or [0]) + 1)],
        "and_per_level": [and_hist.get(i, 0) for i in range(1, max(and_hist or [0]) + 1)],
    }
    return {"ok": func_ok and not errors, "functional": func_ok, "mismatch": mism,
            "errors": errors, "flags": flags, "metrics": met}


# ------------------------------------------------------------ claim parsing


def name_claims(stem):
    """Metrics written in a file/circuit name (last occurrence of each key)."""
    toks = stem.split("-")
    cl = {}
    i = 0
    while i < len(toks):
        t = toks[i]
        mm = re.fullmatch(r"(xxn|xx|ad|gd|a|g|d|n)(\d+)", t)
        if mm:
            k, v = mm.group(1), int(mm.group(2))
            if k == "xxn":
                cl["XXN"] = v
                if i + 2 < len(toks) and toks[i + 1].isdigit() and toks[i + 2].isdigit():
                    cl["XNOR"], cl["NOT"] = int(toks[i + 1]), int(toks[i + 2])
                    i += 2
            elif k == "xx":
                cl["XX"] = v
                if i + 1 < len(toks) and toks[i + 1].isdigit():
                    cl["XNOR"] = int(toks[i + 1])
                    i += 1
            else:
                cl[{"ad": "AD", "gd": "GD", "a": "A", "g": "G", "d": "GD", "n": "NOT"}[k]] = v
        i += 1
    return cl


def header_claims(lines):
    txt = "\n".join(lines)
    cl = {}

    def cnt(piece):
        for v, k in re.findall(r"(\d+)\s+(AND|XOR|XNOR|NOT|OR|NAND|NOR|ANDN|ORN)\b", piece):
            cl["#" + k] = int(v)
        for k, v in re.findall(r"\b(AND|XOR|XNOR|NOT|OR|NAND|NOR|ANDN|ORN)=(\d+)", piece):
            cl["#" + k] = int(v)
    m = re.search(r"Tally: G=(\d+) A=(\d+) GD=(\d+) AD=(\d+)([^;\n]*)", txt)
    if m:
        cl.update(G=int(m.group(1)), A=int(m.group(2)), GD=int(m.group(3)), AD=int(m.group(4)))
        cnt(m.group(5))
    m = re.search(r"Tally of gates \((\d+)\):([^\n]*)", txt)
    if m:
        cl["G"] = int(m.group(1))
        cnt(m.group(2))
    m = re.search(r"Tally:\s*\d+ inputs, \d+ outputs, (\d+) gates,([^\n]*)", txt)
    if m:
        cl["G"] = int(m.group(1))
        cnt(m.group(2))
    for pat in (r"Depth\(Gate\):\s*(\d+);\s*Depth\(AND\):\s*(\d+)",
                r"Gate[- ]depth (\d+);\s*AND[- ]depth (\d+)"):
        m = re.search(pat, txt)
        if m:
            cl["GD"], cl["AD"] = int(m.group(1)), int(m.group(2))
    m = re.search(r"Gates per gate level:\s*([\d ]+)", txt)
    if m:
        cl["gates_per_level"] = [int(v) for v in m.group(1).split()]
    m = re.search(r"AND gates per AND[- ](?:level|depth):\s*([\d ]+)", txt)
    if m:
        cl["and_per_level"] = [int(v) for v in m.group(1).split()]
    return cl


def compare(claims, met):
    bad = {}
    for k, v in claims.items():
        if k.startswith("#"):
            mine = met["counts"].get(k[1:], 0)
        elif k == "XXN":
            mine = met["XX"] + met["NOT"]
        else:
            mine = met.get(k)
        if mine != v:
            bad[k] = {"claimed": v, "recomputed": mine}
    return bad


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


# ------------------------------------------------------------------- main


def canonical(c):
    """Gate list with wires renamed positionally (inputs, outputs, then internals by definition order)."""
    ren = {"0": "0", "1": "1"}
    for i, x in enumerate(c["inputs"]):
        ren[x] = "I%d" % i
    for j, y in enumerate(c["outputs"]):
        ren[y] = "O%d" % j
    k = 0
    out = []
    for op, o, args, _ in c["gates"]:
        if o not in ren:
            ren[o] = "W%d" % k
            k += 1
        if op == "XNOR" and len(args) == 2 and args.count("0") == 1 and "1" not in args:
            op, args = "NOT", [a for a in args if a != "0"]  # XNOR a 0 is written NOT a in NIST style
        out.append((op, ren[o]) + tuple(ren.get(a, "?" + a) for a in args))
    return out


def order_diag(c, n, m, table):
    """Which (input order, output order) pairs make the circuit match the table."""
    hits = []
    for io in ("msb", "lsb"):
        for oo in ("msb", "lsb"):
            cc = dict(c)
            cc["inputs"] = c["inputs"][::-1] if io == "lsb" else c["inputs"]
            cc["outputs"] = c["outputs"][::-1] if oo == "lsb" else c["outputs"]
            cc["issues"] = []
            if analyse(cc, n, m, table)["functional"]:
                hits.append(io + "/" + oo)
    return hits


def sha256(path):
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def audit_file(path, n, m, table, kind):
    circs = parse(path)
    rec = {"file": rel(path), "kind": kind, "n_circuits": len(circs), "sha256": sha256(path),
           "mtime_utc": __import__("datetime").datetime.utcfromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if not circs:
        rec.update(ok=False, errors=["no circuit found"])
        return rec
    c = circs[0]
    r = analyse(c, n, m, table)
    rec.update(circuit=c["name"], **r)
    rec["canonical"] = canonical(c)  # NOT-normalised gate list, for twin matching
    if not r["functional"]:
        rec["orders_that_match"] = order_diag(c, n, m, table)
    if len(circs) > 1:
        rec["flags"].append("file holds %d circuits; first audited" % len(circs))
    stem = os.path.basename(path).split(".")[0]
    rec["name_claims"] = name_claims(stem)
    rec["name_mismatch"] = compare(rec["name_claims"], r["metrics"])
    cn = name_claims(c["name"]) if c["name"] else {}
    rec["circuit_name_mismatch"] = compare(cn, r["metrics"]) if cn else {}
    rec["header_claims"] = header_claims(c["header"])
    rec["header_mismatch"] = compare(rec["header_claims"], r["metrics"])
    return rec


def basis_check(rec, allowed):
    used = set(rec["metrics"]["counts"])
    bad = sorted(used - allowed)
    return bad


def dominates_le(p, r):
    return all(p[k] <= r[k] for k in ("A", "AD", "G", "GD"))


def tup(rec):
    mt = rec["metrics"]
    return {k: mt[k] for k in ("A", "AD", "G", "GD")}


def tstr(t):
    return "(%d,%d,%d,%d)" % (t["A"], t["AD"], t["G"], t["GD"])


def main():
    second = "--second-opinion" in sys.argv
    aes = aes_sbox()
    small = small_targets()
    import datetime
    report = {"run_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "targets": {"aes_sbox_self_check": "ok",
                          "aes_matches_sboxes_json": small["aes"][2] == aes}}

    # ---- published AES forward circuits
    pub_files = sorted(glob.glob(os.path.join(ROOT, "nonlinear/nist/aes-sbox/*.circ.txt")))
    pub_files += sorted(glob.glob(os.path.join(ROOT, "nonlinear/nist/old-2020/aes-sbox-fwd-*.slp")))
    pub_files += sorted(glob.glob(os.path.join(ROOT, "nonlinear/nist/sbox/aes-sbox-fwd-*")))
    with open(os.path.join(ROOT, "nonlinear/nist/MANIFEST.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    man = {}
    for e in manifest.get("files", []):
        man[e["folder"] + "/" + e["file"]] = e
    pubs = []
    for p in pub_files:
        rec = audit_file(p, 8, 8, aes, "published")
        rec["basis_violations"] = basis_check(rec, MODELS["nist"])
        key = rel(p)[len("nonlinear/nist/"):]
        if key in man:
            e = man[key]
            mc = {k: e[k] for k in ("A", "AD", "G", "GD", "XOR", "XNOR") if k in e}
            rec["manifest_mismatch"] = compare(mc, rec["metrics"])
        else:
            rec["manifest_mismatch"] = "not in MANIFEST"
        pubs.append(rec)
    report["published"] = pubs

    # ---- our AES results
    res = []
    for p in sorted(glob.glob(os.path.join(ROOT, "nonlinear/boolflux/results/aes/*.circ.txt"))):
        rec = audit_file(p, 8, 8, aes, "result")
        rec["basis_violations"] = basis_check(rec, MODELS["nist"])
        if any(k in NONLIN and k != "AND" for k in rec["metrics"]["counts"]):
            rec["flags"].append("non-AND nonlinear gate in AES result")
        sp = p[:-len(".circ.txt")] + ".summary.json"
        rec["summary"] = None
        if os.path.exists(sp):
            with open(sp, encoding="utf-8") as f:
                s = json.load(f)
            bm = (s.get("best") or {}).get("metrics", {})
            claims = {k: bm[k] for k in ("G", "A", "GD", "AD") if k in bm}
            for k, v in (bm.get("counts") or {}).items():
                claims["#" + k] = v
            caps = s.get("caps") or {}
            capviol = {k: v for k, v in caps.items() if v is not None and rec["metrics"][k] > v}
            rec["summary"] = {"start": s.get("start"), "caps": caps, "model": s.get("model"),
                              "mismatch": compare(claims, rec["metrics"]), "cap_violations": capviol,
                              "start_metrics": {k: (s.get("start_metrics") or {}).get(k) for k in ("A", "AD", "G", "GD")}}
        rec["valid"] = rec["ok"] and not rec["basis_violations"] and not any(
            f.startswith("BUF") for f in rec["flags"])
        res.append(rec)
    report["results_aes"] = res

    # ---- NIST-named copies of results (results/nist-format/): verify, recount, find twin in results/aes
    nf = []
    for p in sorted(glob.glob(os.path.join(ROOT, "nonlinear/boolflux/results/nist-format/*.circ.txt"))):
        rec = audit_file(p, 8, 8, aes, "nist-format")
        rec["basis_violations"] = basis_check(rec, MODELS["nist"])
        rec["twin_identical_gates"] = [r["file"] for r in res if r.get("canonical") == rec.get("canonical")]
        rec["twin_same_metrics"] = [r["file"] for r in res if r.get("metrics") == rec.get("metrics")]
        nf.append(rec)
    report["results_nist_format"] = nf
    twinned = {t for x in nf for t in x["twin_identical_gates"]}
    report["aes_results_without_nist_format_twin"] = [r["file"] for r in res if r["file"] not in twinned]
    # a nist-format file with no gate-identical twin in results/aes is an extra claim: include it
    for x in nf:
        if not x["twin_identical_gates"]:
            x["valid"] = x["ok"] and not x["basis_violations"]
            res.append(x)
    for x in pubs + res + nf:
        x.pop("canonical", None)

    P = [p for p in pubs if p["ok"]]
    R = [r for r in res if r["valid"]]
    for r in res:
        if not r["valid"]:
            r["status"] = "invalid"
            continue
        t = tup(r)
        le = [p for p in P if dominates_le(tup(p), t)]
        r["published_le"] = [{"file": p["file"], "tuple": tstr(tup(p)), "equal": tup(p) == t} for p in le]
        r["own_strict"] = [x["file"] for x in R if x is not r and dominates_le(tup(x), t) and tup(x) != t]
        r["own_equal"] = [x["file"] for x in R if x is not r and tup(x) == t]
        r["beats_published"] = [p["file"] for p in P if dominates_le(t, tup(p)) and tup(p) != t]
        strict_pub = [x for x in r["published_le"] if not x["equal"]]
        eq_pub = [x for x in r["published_le"] if x["equal"]]
        if strict_pub:
            r["status"] = "dominated-by-published"
        elif r["own_strict"]:
            r["status"] = "dominated-by-own"
        elif eq_pub:
            r["status"] = "equals-published"
        else:
            r["status"] = "survives"
    # collapse identical surviving tuples
    reps = {}
    for r in res:
        if r.get("status") == "survives":
            reps.setdefault(tstr(tup(r)), []).append(r["file"])
    report["survivors"] = [{"tuple": k, "files": v} for k, v in sorted(reps.items())]

    # published Pareto front (for context)
    front = []
    for p in P:
        t = tup(p)
        if not any(dominates_le(tup(q), t) and tup(q) != t for q in P):
            front.append(tstr(t))
    report["published_front"] = sorted(set(front))

    # ---- depth-cap table
    caps = []
    for d in range(9, 41):
        pg = [p for p in P if p["metrics"]["GD"] <= d]
        rg = [r for r in R if r["metrics"]["GD"] <= d]
        bp = min(pg, key=lambda x: (x["metrics"]["G"], x["metrics"]["GD"])) if pg else None
        br = min(rg, key=lambda x: (x["metrics"]["G"], x["metrics"]["GD"])) if rg else None
        row = {"cap": d,
               "pub_G": bp["metrics"]["G"] if bp else None, "pub_file": bp["file"] if bp else None,
               "pub_tuple": tstr(tup(bp)) if bp else None,
               "res_G": br["metrics"]["G"] if br else None, "res_file": br["file"] if br else None,
               "res_tuple": tstr(tup(br)) if br else None}
        row["strict"] = bool(br and (not bp or br["metrics"]["G"] < bp["metrics"]["G"]))
        caps.append(row)
    report["depth_caps"] = caps

    # ---- small S-boxes / functions
    smalls = []
    for d in sorted(glob.glob(os.path.join(ROOT, "nonlinear/boolflux/results/*/"))):
        dname = os.path.basename(os.path.dirname(d))
        if dname in ("aes", "reports", "nist-format"):
            continue
        for p in sorted(glob.glob(os.path.join(d, "*.circ.txt"))):
            base = os.path.basename(p)
            tname = dname
            if dname == "_superseded":
                cands = [k for k in small if base.startswith(k + "-")]
                tname = max(cands, key=len) if cands else "?"
            mm = re.search(r"-(bgc|gc6|nist|xag|gc)-", base[len(tname):])
            model = mm.group(1) if mm else None
            if tname not in small:
                smalls.append({"file": rel(p), "ok": False, "errors": ["unknown target " + tname]})
                continue
            n, m, tab = small[tname]
            rec = audit_file(p, n, m, tab, "small")
            rec["target"] = tname
            rec["model"] = model
            rec["superseded"] = dname == "_superseded"
            rec.pop("canonical", None)
            rec["basis_violations"] = basis_check(rec, MODELS[model]) if model else ["no model in name"]
            if model and rec["metrics"]["XNOR_const"] and "XNOR" not in MODELS[model]:
                rec["flags"].append("XNOR-with-constant used as NOT in a model without XNOR")
            sp = p[:-len(".circ.txt")] + ".summary.json"
            if os.path.exists(sp):
                with open(sp, encoding="utf-8") as f:
                    s = json.load(f)
                bm = (s.get("best") or {}).get("metrics", {})
                claims = {k: bm[k] for k in ("G", "A", "GD", "AD") if k in bm}
                for k, v in (bm.get("counts") or {}).items():
                    claims["#" + k] = v
                rec["summary"] = {"model": s.get("model"), "mismatch": compare(claims, rec["metrics"]),
                                  "model_matches_name": s.get("model") == model}
            smalls.append(rec)
    report["results_small"] = smalls

    # ---- ledger-rows.jsonl (bookkeeping comparison only)
    lr = []
    lp = os.path.join(ROOT, "nonlinear/boolflux/results/ledger-rows.jsonl")
    if os.path.exists(lp):
        byfile = {r["file"]: r for r in res + smalls}
        with open(lp, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                fl = row.get("file")
                ent = {"file": fl, "verified_claim": row.get("verified"), "G_claim": row.get("G")}
                if fl and fl in byfile:
                    ent["G_mine"] = byfile[fl]["metrics"]["G"]
                    ent["ok_mine"] = byfile[fl]["ok"]
                    ent["match"] = (ent["G_mine"] == row.get("G")) and (bool(row.get("verified")) == byfile[fl]["ok"])
                elif fl:
                    ent["match"] = False
                    ent["note"] = "file listed but not found"
                lr.append(ent)
        listed = {e["file"] for e in lr if e.get("file")}
        report["ledger_rows_unlisted_files"] = [r["file"] for r in res + smalls if r["file"] not in listed]
    report["ledger_rows"] = lr

    # ---- results/MANIFEST.json (bookkeeping comparison only)
    mp = os.path.join(ROOT, "nonlinear/boolflux/results/MANIFEST.json")
    rm = []
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as f:
            rmj = json.load(f)
        byfile = {r["file"]: r for r in res + smalls + nf}
        for e in rmj.get("entries", []):
            fl = e.get("file")
            ent = {"file": fl}
            if fl not in byfile:
                ent["problem"] = "file not found"
            else:
                mine = byfile[fl]
                em = e.get("metrics") or {}
                claims = {k: em[k] for k in ("G", "A", "GD", "AD") if k in em}
                for k, v in (em.get("counts") or {}).items():
                    claims["#" + k] = v
                ent["metric_mismatch"] = compare(claims, mine["metrics"])
                ent["sha_match"] = e.get("sha256") == mine["sha256"]
                ver = e.get("verified")
                vclaim = all(ver.values()) if isinstance(ver, dict) else bool(ver)
                ent["verified_claim"] = vclaim
                ent["verified_mine"] = mine["ok"] and not mine.get("basis_violations")
                nff = e.get("nist_format_file")
                if nff:
                    tw = [x for x in nf if x["file"] == nff]
                    ent["nist_format_twin_ok"] = bool(tw) and fl in tw[0]["twin_identical_gates"]
            rm.append(ent)
        listed = {e.get("file") for e in rmj.get("entries", [])}
        report["results_manifest_unlisted"] = [r["file"] for r in res + smalls if r["file"] not in listed]
    report["results_manifest"] = rm

    # ---- second opinion
    if second:
        vp = os.path.join(ROOT, "nonlinear/boolflux/independent/verify.py")
        fndir = os.path.join(HERE, "fn")
        os.makedirs(fndir, exist_ok=True)
        so = []
        for rec in pubs + [r for r in res if r["kind"] == "result"] + nf + smalls:
            if "metrics" not in rec:
                continue
            tgt = rec.get("target", "aes")
            if tgt == "aes":
                targ = ["--aes"]
            else:
                n, m, tab = small[tgt]
                fp = os.path.join(fndir, tgt + ".json")
                with open(fp, "w", encoding="utf-8", newline="\n") as f:
                    json.dump({"n": n, "m": m, "table": tab}, f)
                targ = ["--fn", fp]
            out = subprocess.run([sys.executable, vp] + targ + ["--json", os.path.join(ROOT, rec["file"])],
                                 capture_output=True, text=True)
            try:
                v = json.loads(out.stdout)[0]
                vm = v.get("metrics") or {}
                agree = (v.get("ok") == rec["ok"] and all(vm.get(k) == rec["metrics"][k] for k in ("G", "A", "GD", "AD"))
                         and vm.get("dead") == rec["metrics"]["dead"])
                so.append({"file": rec["file"], "ok": v.get("ok"), "G": vm.get("G"), "A": vm.get("A"),
                           "GD": vm.get("GD"), "AD": vm.get("AD"), "dead": vm.get("dead"),
                           "errors": v.get("errors"), "agrees": agree})
            except Exception as e:  # noqa
                so.append({"file": rec["file"], "agrees": False, "error": str(e), "stderr": out.stderr[-500:]})
        report["second_opinion"] = so

    with open(os.path.join(HERE, "audit.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1)
    write_tables(report)
    print_summary(report)


def mm_str(d):
    if not d:
        return ""
    if isinstance(d, str):
        return d
    return "; ".join("%s %s->%s" % (k, v["claimed"], v["recomputed"]) for k, v in d.items())


def write_tables(rep):
    L = []
    L.append("<!-- generated by audit.py at %s; do not edit by hand -->" % rep["run_utc"])
    L.append("## Published forward AES circuits (recomputed)\n")
    L.append("| file | ok | A | AD | G | GD | XX | XNOR | NOT | XNOR-const | dead | name/header/manifest disagreement | flags |")
    L.append("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|---|")
    for p in rep["published"]:
        mt = p["metrics"]
        dis = "; ".join(x for x in (mm_str(p["name_mismatch"]) and "name: " + mm_str(p["name_mismatch"]),
                                    mm_str(p["circuit_name_mismatch"]) and "circuit name: " + mm_str(p["circuit_name_mismatch"]),
                                    mm_str(p["header_mismatch"]) and "header: " + mm_str(p["header_mismatch"]),
                                    mm_str(p["manifest_mismatch"]) and "manifest: " + mm_str(p["manifest_mismatch"])) if x)
        fl = "; ".join(p["flags"] + p["errors"] + (["basis " + str(p["basis_violations"])] if p["basis_violations"] else []))
        L.append("| %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %s | %s |" % (
            p["file"][len("nonlinear/nist/"):], "yes" if p["ok"] else "**NO**", mt["A"], mt["AD"], mt["G"], mt["GD"],
            mt["XX"], mt["XNOR"], mt["NOT"], mt["XNOR_const"], mt["dead"], dis, fl))
    L.append("\nPublished Pareto front on (A,AD,G,GD), verified circuits only: " + ", ".join(rep["published_front"]) + "\n")

    L.append("## AES results: recount and Pareto status\n")
    L.append("Tuple = (A, AD, G, GD). `pub<=`: verified published circuits with all four <= (= marks an identical tuple).\n")
    L.append("| result (file stem after `aes-nist-cost_gd-`) | verified | basis | A | AD | G | GD | XX | XNOR | NOT | XNOR w/ 0 | dead | pub<= | own strictly better | own identical | status |")
    L.append("|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|---|---|---|")
    for r in rep["results_aes"]:
        mt = r["metrics"]
        stem = os.path.basename(r["file"]).replace("aes-nist-cost_gd-", "").replace(".circ.txt", "")

        def short(f):
            return os.path.basename(f).replace(".circ.txt", "").replace(".ncff.txt", "").replace(".slp", "").replace("aes-nist-cost_gd-", "")
        pl = ", ".join(("=" if x["equal"] else "") + short(x["file"]) for x in r.get("published_le", []))
        L.append("| %s | %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %s | %s | %s | **%s** |" % (
            stem, "yes" if r["ok"] else "**NO**", "ok" if not r["basis_violations"] else "**" + ",".join(r["basis_violations"]) + "**",
            mt["A"], mt["AD"], mt["G"], mt["GD"], mt["XX"], mt["XNOR"], mt["NOT"], mt["XNOR_with_0"], mt["dead"],
            pl or "-", ", ".join(short(x) for x in r.get("own_strict", [])) or "-",
            ", ".join(short(x) for x in r.get("own_equal", [])) or "-", r["status"]))
    L.append("\n### Surviving tuples (duplicates collapsed)\n")
    byf = {r["file"]: r for r in rep["results_aes"]}
    for s in rep["survivors"]:
        L.append("- %s: %s" % (s["tuple"], ", ".join(os.path.basename(f) for f in s["files"])))
        bp = sorted(set(os.path.basename(x) for f in s["files"] for x in byf[f].get("beats_published", [])))
        L.append("  - strictly dominates published: %s" % (", ".join(bp) or "none (new trade-off point only)"))
    eq = [r for r in rep["results_aes"] if r.get("status") == "equals-published"]
    L.append("\n### Results equal to a published tuple (not new)\n")
    for r in eq:
        L.append("- %s %s = %s" % (os.path.basename(r["file"]), tstr(tup(r)),
                                   ", ".join(os.path.basename(x["file"]) for x in r["published_le"] if x["equal"])))
    if not eq:
        L.append("- none")
    L.append("\n### Header / file-name / summary.json disagreements for AES results\n")
    anyd = False
    for r in rep["results_aes"]:
        parts = []
        if r["name_mismatch"]:
            parts.append("name: " + mm_str(r["name_mismatch"]))
        if r["header_mismatch"]:
            parts.append("header: " + mm_str(r["header_mismatch"]))
        if r.get("summary") and r["summary"]["mismatch"]:
            parts.append("summary: " + mm_str(r["summary"]["mismatch"]))
        if r.get("summary") and r["summary"]["cap_violations"]:
            parts.append("cap violated: %s" % r["summary"]["cap_violations"])
        if r["flags"] or r["errors"]:
            parts.append("flags: " + "; ".join(r["flags"] + r["errors"]))
        if parts:
            anyd = True
            L.append("- %s: %s" % (os.path.basename(r["file"]), " | ".join(parts)))
    if not anyd:
        L.append("- none")

    L.append("\n## Smallest G under a gate-depth cap\n")
    L.append("| GD cap | best published G (A,AD,G,GD) | file | best result G (A,AD,G,GD) | file | strict improvement |")
    L.append("|--:|---|---|---|---|---|")
    for c in rep["depth_caps"]:
        L.append("| %d | %s %s | %s | %s %s | %s | %s |" % (
            c["cap"], c["pub_G"], c["pub_tuple"] or "", os.path.basename(c["pub_file"] or "-"),
            c["res_G"], c["res_tuple"] or "", os.path.basename(c["res_file"] or "-"), "**yes**" if c["strict"] else "no"))

    L.append("\n## Small S-boxes and functions\n")
    L.append("| target | model | file | verified | model gates ok | G | A | GD | AD | counts | dead | name/header/summary disagreement | flags |")
    L.append("|---|---|---|---|---|--:|--:|--:|--:|---|--:|---|---|")
    for r in rep["results_small"]:
        if "metrics" not in r:
            L.append("| ? | ? | %s | **NO** | | | | | | | | | %s |" % (r["file"], r.get("errors")))
            continue
        mt = r["metrics"]
        dis = "; ".join(x for x in (mm_str(r["name_mismatch"]) and "name: " + mm_str(r["name_mismatch"]),
                                    mm_str(r["header_mismatch"]) and "header: " + mm_str(r["header_mismatch"]),
                                    r.get("summary") and mm_str(r["summary"]["mismatch"]) and "summary: " + mm_str(r["summary"]["mismatch"])) if x)
        extra = list(r["flags"] + r["errors"])
        if r.get("mismatch"):
            extra.append("first mismatch %s" % r["mismatch"])
        if "orders_that_match" in r:
            extra.append("bit orders (in/out) that match table: %s" % (r["orders_that_match"] or "none"))
        if r.get("superseded"):
            extra.append("in _superseded/ (not claimed)")
        L.append("| %s | %s | %s | %s | %s | %d | %d | %d | %d | %s | %d | %s | %s |" % (
            r["target"], r["model"], os.path.basename(r["file"]), "yes" if r["ok"] else "**NO**",
            "yes" if not r["basis_violations"] else "**NO: %s**" % ",".join(r["basis_violations"]),
            mt["G"], mt["A"], mt["GD"], mt["AD"], " ".join("%s=%d" % kv for kv in mt["counts"].items()), mt["dead"],
            dis, "; ".join(extra)))

    nf = rep.get("results_nist_format") or []
    L.append("\n## results/nist-format/ (NIST-named copies of AES results)\n")
    L.append("| file | verified | basis | (A,AD,G,GD) | XX | XNOR | NOT | name disagreement | gate-identical twin in results/aes |")
    L.append("|---|---|---|---|--:|--:|--:|---|---|")
    for x in nf:
        mt = x["metrics"]
        L.append("| %s | %s | %s | %s | %d | %d | %d | %s | %s |" % (
            os.path.basename(x["file"]), "yes" if x["ok"] else "**NO**", "ok" if not x["basis_violations"] else "**%s**" % x["basis_violations"],
            tstr(tup(x)), mt["XX"], mt["XNOR"], mt["NOT"], mm_str(x["name_mismatch"]) or "-",
            ", ".join(os.path.basename(t) for t in x["twin_identical_gates"]) or "**none**"))
    un = rep.get("aes_results_without_nist_format_twin") or []
    L.append("\nresults/aes files without a gate-identical nist-format copy: %s" % (", ".join(os.path.basename(u) for u in un) or "none"))

    rm = rep.get("results_manifest") or []
    if rm:
        bad = [e for e in rm if e.get("problem") or e.get("metric_mismatch") or not e.get("sha_match")
               or e.get("verified_claim") != e.get("verified_mine") or e.get("nist_format_twin_ok") is False]
        L.append("\n## results/MANIFEST.json vs recount\n")
        L.append("%d entries; %d disagree (metrics, sha256, verified flag, or nist-format twin)." % (len(rm), len(bad)))
        for e in bad:
            L.append("- %s: %s" % (e["file"], {k: v for k, v in e.items() if k != "file"}))
        un = rep.get("results_manifest_unlisted") or []
        L.append("\nResult files not listed in results/MANIFEST.json: %s" % (", ".join(os.path.basename(u) for u in un) or "none"))

    if rep.get("ledger_rows"):
        bad = [e for e in rep["ledger_rows"] if e.get("file") and not e.get("match")]
        L.append("\n## results/ledger-rows.jsonl vs recount\n")
        L.append("%d rows, %d with a file; %d disagree with the recount (G or verified flag)." % (
            len(rep["ledger_rows"]), sum(1 for e in rep["ledger_rows"] if e.get("file")), len(bad)))
        for e in bad:
            L.append("- %s: %s" % (e["file"], e))
        un = rep.get("ledger_rows_unlisted_files") or []
        L.append("\nResult files with no ledger row: %d%s" % (len(un), (" (" + ", ".join(os.path.basename(x) for x in un) + ")") if un else ""))

    if rep.get("second_opinion") is not None:
        so = rep["second_opinion"]
        dis = [s for s in so if not s.get("agrees")]
        L.append("\n## Second opinion (independent/verify.py)\n")
        L.append("%d files checked; %d disagree with this audit on ok/G/A/GD/AD/dead." % (len(so), len(dis)))
        for s in dis:
            L.append("- %s: %s" % (s["file"], s))
    with open(os.path.join(HERE, "AUDIT-tables.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


def print_summary(rep):
    print("AES self-check ok; matches sboxes.json:", rep["targets"]["aes_matches_sboxes_json"])
    pubs = rep["published"]
    print("published: %d files, %d verified" % (len(pubs), sum(p["ok"] for p in pubs)))
    for p in pubs:
        if not p["ok"] or p["flags"] or p["name_mismatch"] or p["header_mismatch"] or p["manifest_mismatch"] or p["circuit_name_mismatch"] or p["basis_violations"]:
            print("  PUB", p["file"], p["ok"], p["errors"], p["flags"], p["basis_violations"], "name", mm_str(p["name_mismatch"]),
                  "cname", mm_str(p["circuit_name_mismatch"]), "hdr", mm_str(p["header_mismatch"]), "man", mm_str(p["manifest_mismatch"]))
    for r in rep["results_aes"]:
        mt = r["metrics"]
        print("RES %-60s ok=%s basis=%s %s XX=%d XNOR=%d NOT=%d xn0=%d dead=%d %s name=%s hdr=%s sum=%s flags=%s" % (
            os.path.basename(r["file"]), r["ok"], r["basis_violations"], tstr(tup(r)), mt["XX"], mt["XNOR"], mt["NOT"],
            mt["XNOR_with_0"], mt["dead"], r["status"], mm_str(r["name_mismatch"]), mm_str(r["header_mismatch"]),
            r.get("summary") and (mm_str(r["summary"]["mismatch"]), r["summary"]["cap_violations"]), r["flags"] + r["errors"]))
    print("survivors:", json.dumps(rep["survivors"], indent=0))
    print("strict depth caps:", [(c["cap"], c["pub_G"], c["res_G"]) for c in rep["depth_caps"] if c["strict"]])
    for r in rep["results_small"]:
        if "metrics" in r:
            print("SMALL %-55s ok=%s basis=%s G=%d A=%d GD=%d AD=%d name=%s hdr=%s sum=%s flags=%s" % (
                os.path.basename(r["file"]), r["ok"], r["basis_violations"], r["metrics"]["G"], r["metrics"]["A"],
                r["metrics"]["GD"], r["metrics"]["AD"], mm_str(r["name_mismatch"]), mm_str(r["header_mismatch"]),
                r.get("summary") and mm_str(r["summary"]["mismatch"]), r["flags"] + r["errors"]))
        else:
            print("SMALL", r)
    if rep.get("second_opinion") is not None:
        print("second opinion disagreements:", [s for s in rep["second_opinion"] if not s.get("agrees")])
    print("ledger-row disagreements:", [e for e in rep["ledger_rows"] if e.get("file") and not e.get("match")])
    print("unlisted:", rep.get("ledger_rows_unlisted_files"))


if __name__ == "__main__":
    main()
