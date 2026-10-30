"""Check circuits against their map: python3 circuits/check.py [FILE_OR_DIR ...]

Every *.circ.txt is checked against the one *.mat.txt in its folder: each output must equal its
matrix row, and the gate count and depth must match the file name (...-xor<G>-depth<D>.circ.txt).
Standard library only; no search code is used.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
GATE = re.compile(r"^(XOR|XNOR)\s+(\S+)\s+(\S+)\s+(\S+)")
NAME = re.compile(r"-xor(\d+)-depth(\d+)\.circ\.txt$")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


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


def main(args):
    files = []
    for a in args or [ROOT]:
        p = pathlib.Path(a)
        files += sorted(p.rglob("*.circ.txt")) if p.is_dir() else [p]
    bad = 0
    for circ in files:
        mats = list(circ.parent.glob("*.mat.txt"))
        if len(mats) != 1:
            res = "no single *.mat.txt in the folder"
        else:
            rows, consts, n_in = read_matrix(mats[0])
            res = check(circ, rows, consts, n_in)
        ok = isinstance(res, tuple)
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {circ.relative_to(ROOT) if circ.is_relative_to(ROOT) else circ}"
              + ("" if ok else f": {res}"))
    print(f"{len(files) - bad}/{len(files)} circuits ok")
    return 1 if bad or not files else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
