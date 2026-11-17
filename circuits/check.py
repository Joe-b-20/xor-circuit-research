"""Check every circuit: python3 circuits/check.py [FILE_OR_DIR ...]

Linear maps (a folder with one *.mat.txt): every *.circ.txt is checked against that matrix: each
output must equal its matrix row, and the gate count and depth must match the file name
(...-xor<G>-depth<D>.circ.txt).

Boolean circuits (S-boxes; every other folder): every *.circ.txt, *.ncff.txt and *.slp file is read
with each gate's own semantics (XOR, XNOR, AND, NOT; also OR, NAND, NOR); NIST's metrics (#AND, AND
depth, #gates, gate depth, #XOR, #XNOR) must match the file name and the tallies in its header, if
any; and it is verified twice by complete truth table, from the gate list and from its AND skeleton,
against the function its folder or name designates: the AES S-box, its inverse, or the S-box with a
direction bit by FIPS-197's definition (names aes-sbox..., aes-invsbox..., aes-sbox-sel...), or the
*.fn.json table in its folder.

Default: circuits/ and NIST's circuits in search/nonlinear/seeds/.  Files in logs/ folders are
records of how a circuit was found and are not checked.  Exit status 1 if any circuit fails.
Standard library only; no search code is used (boolcirc/ is this checker's own library).
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from boolcirc import metrics as M, ncff, skeleton as S, truth  # noqa: E402

DEFAULT_DIRS = [ROOT, REPO / "search" / "nonlinear" / "seeds"]
SUFFIXES = (".circ.txt", ".ncff.txt", ".slp")
GATE = re.compile(r"^(XOR|XNOR)\s+(\S+)\s+(\S+)\s+(\S+)")
NAME = re.compile(r"-xor(\d+)-depth(\d+)\.circ\.txt$")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


# ---- linear maps ---------------------------------------------------------------------------

def read_matrix(path):
    """Rows as int masks (bit j = input x_j) and the output constants (0 when absent)."""
    tokens = " ".join(l.split("#")[0].split("%")[0] for l in path.read_text().splitlines()).split()
    rows_n, cols_n = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:]))
    assert len(bits) in (rows_n * cols_n, rows_n * cols_n + rows_n), f"{path}: not {rows_n}x{cols_n}"
    rows = [sum(bits[i * cols_n + j] << j for j in range(cols_n)) for i in range(rows_n)]
    consts = bits[rows_n * cols_n:] or [0] * rows_n
    return rows, consts, cols_n


def check(circ, rows, consts, n_in):
    vals, depth, gates = {}, {}, 0
    for line in circ.read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = RANGE.match(line)
        if m and m.group(1) == "Inputs":
            base = int(m.group(3))
            if int(m.group(4)) - base + 1 != n_in:
                return f"{n_in} inputs expected"
            for j in range(n_in):
                vals[f"x{j + base}"], depth[f"x{j + base}"] = (1 << j, 0), 0
            continue
        m = GATE.match(line)
        if not m:
            continue
        op, out, a, b = m.groups()
        if a not in vals or b not in vals:
            return f"gate {gates + 1} reads an undefined variable"
        if out in vals:
            return f"{out} is assigned twice"
        (ma, ca), (mb, cb) = vals[a], vals[b]
        vals[out] = (ma ^ mb, ca ^ cb ^ (op == "XNOR"))
        depth[out] = 1 + max(depth[a], depth[b])
        gates += 1
    ys = sorted((int(k[1:]), k) for k in vals if k.startswith("y"))
    if len(ys) != len(rows):
        return f"{len(ys)} outputs, map has {len(rows)}"
    base = ys[0][0]
    for i, (idx, k) in enumerate(ys):
        if idx != i + base or vals[k] != (rows[i], consts[i]):
            return f"y{idx} is wrong"
    d = max(depth[k] for _, k in ys)
    m = NAME.search(circ.name)
    if not m or (int(m.group(1)), int(m.group(2))) != (gates, d):
        return f"file name says {m.groups() if m else '?'}, circuit has {gates} gates, depth {d}"
    return (gates, d)


def check_linear(circ, mat):
    rows, consts, n_in = read_matrix(mat)
    return check(circ, rows, consts, n_in)


# ---- Boolean circuits ----------------------------------------------------------------------

def function_for(path):
    """The Function a circuit file must compute, from a ``*.fn.json`` in its folder or from
    its name (``aes-sbox``, ``aes-invsbox``, ``aes-sbox-fwd/-inv/-rev``, ``aes-sbox-sel``)."""
    tables = sorted(path.parent.glob("*.fn.json"))
    if len(tables) > 1:          # several targets in one folder: the file name starts with the target's
        tables = [t for t in tables if path.name.startswith(t.name[:-len(".fn.json")])]
    if len(tables) == 1:
        d = json.loads(tables[0].read_text())
        return truth.Function.from_table(d["name"], d["n_inputs"], d["n_outputs"], d["table"],
                                         **{k: v for k, v in d.items()
                                            if k not in ("name", "n_inputs", "n_outputs", "table")})
    if tables:
        raise ValueError("%s: several *.fn.json match" % path)
    name = path.name.lower()
    if name.startswith("aes-sbox-sel"):
        return truth.aes_sbox_sel()
    if name.startswith(("aes-invsbox", "aes-sbox-inv", "aes-sbox-rev")):
        return truth.aes_inv_sbox()
    if name.startswith("aes-sbox"):
        return truth.aes_sbox()
    return None


def check_file(path):
    """``[(circuit name, metrics, orders, problems)]`` for every circuit in a Boolean circuit file."""
    out = []
    try:
        circuits = ncff.parse_file(path)
    except (ncff.FormatError, UnicodeDecodeError) as e:
        return [(path.name, None, [], ["cannot parse: %s" % e])]
    fn = function_for(path)
    for c in circuits:
        problems = []
        m = M.metrics(c)
        if m.dead:
            problems.append("dead gates: %s" % " ".join(m.dead[:8]))
        if m.not_count:
            problems.append("note: %d NOT gates counted as gates and depth levels" % m.not_count)
        problems += M.check_name(path.name, m)
        problems += M.check_tallies(c, m)
        orders = []
        if fn is None:
            problems.append("no function known for this file (name or *.fn.json)")
        else:
            orders = truth.match(c, fn)
            if not orders:
                problems.append("not equivalent to %s under any bit order" % fn.name)
            sk = S.skeleton(c)
            sk_orders = truth.match_evaluator(sk.tables, c.n_inputs, fn)
            if sorted(sk_orders) != sorted(orders):
                problems.append("skeleton evaluation disagrees with the gate list")
            degenerate = sk.degenerate()
            if degenerate:
                problems.append("degenerate AND gates: %s" % degenerate)
        out.append((c.name, m, orders, problems))
    return out


# ---- driver --------------------------------------------------------------------------------

def collect(args):
    files = []
    for a in args:
        p = pathlib.Path(a)
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.name.endswith(SUFFIXES)
                            and "logs" not in f.relative_to(p).parts[:-1])
        elif p.exists():
            files.append(p)
        else:
            print(f"FAIL {a}: no such file or folder")
            files.append(None)
    return files


def shown(path):
    path = path.resolve()
    for base in (ROOT, REPO):
        if path.is_relative_to(base):
            return path.relative_to(base)
    return path


def main(args):
    paths = args or [d for d in DEFAULT_DIRS if d.is_dir()]
    files = collect(paths)
    counts = {"linear": [0, 0], "Boolean": [0, 0]}      # [checked, failing]
    for f in files:
        if f is None:
            counts["linear"][0] += 1; counts["linear"][1] += 1
            continue
        mats = list(f.parent.glob("*.mat.txt"))
        if mats:
            res = check_linear(f, mats[0]) if len(mats) == 1 and f.name.endswith(".circ.txt") \
                else "no single *.mat.txt in the folder"
            ok = isinstance(res, tuple)
            counts["linear"][0] += 1; counts["linear"][1] += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {shown(f)}" + ("" if ok else f": {res}"))
            continue
        for name, m, orders, problems in check_file(f):
            hard = [p for p in problems if not p.startswith("note:")]
            counts["Boolean"][0] += 1; counts["Boolean"][1] += bool(hard)
            label = shown(f) if name in (f.name, None) or f.name.startswith(name) else f"{shown(f)} [{name}]"
            print(f"{'ok  ' if not hard else 'FAIL'} {label}  {m.summary() if m else ''}  orders="
                  + (",".join("%s/%s" % o for o in orders) or "-"))
            for p in problems:
                print("      " + p)
    total = sum(c[0] for c in counts.values()); bad = sum(c[1] for c in counts.values())
    print(f"{total - bad}/{total} circuits ok ("
          + ", ".join(f"{k} {c[0] - c[1]}/{c[0]}" for k, c in counts.items()) + ")")
    return 1 if bad or not total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
