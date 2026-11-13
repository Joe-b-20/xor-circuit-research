#!/usr/bin/env python3
"""Write target function files for the ABC comparator.

For each target: targets/<name>.fn.json  ({"n","m","table"}, for verify.py)
                 targets/<name>.blif     (full minterm table, naive start)
Bit order: input x0 = MSB of x, output y0 = MSB of table[x] (msb/msb).
Usage: make_targets.py SBOXES_JSON OUTDIR
"""
import json
import os
import sys

SBOXES = ["present", "rectangle", "ascon", "prince", "aes"]


def gf16_mul_table():
    def mul(a, b):
        r = 0
        for i in range(4):
            if (b >> i) & 1:
                r ^= a << i
        for i in (6, 5, 4):  # reduce mod x^4 + x + 1 (0x13)
            if (r >> i) & 1:
                r ^= 0x13 << (i - 4)
        return r
    return [mul(x >> 4, x & 15) for x in range(256)]


def write_blif(path, name, n, m, table):
    ins = [f"x{i}" for i in range(n)]
    outs = [f"y{j}" for j in range(m)]
    lines = [f".model {name}", ".inputs " + " ".join(ins), ".outputs " + " ".join(outs)]
    for j in range(m):
        bit = m - 1 - j
        rows = [x for x in range(2 ** n) if (table[x] >> bit) & 1]
        lines.append(".names " + " ".join(ins) + " " + outs[j])
        if not rows:  # constant 0: empty cover
            continue
        for x in rows:
            lines.append(format(x, f"0{n}b") + " 1")  # first char = x0 = MSB
    lines.append(".end")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(src, encoding="utf-8"))
    by = {s["name"]: s for s in d["sboxes"]}
    targets = {k: (by[k]["n"], by[k]["m"], by[k]["table"]) for k in SBOXES}
    targets["gf16-mul"] = (8, 4, gf16_mul_table())
    for name, (n, m, t) in targets.items():
        assert len(t) == 2 ** n and all(0 <= v < 2 ** m for v in t)
        with open(os.path.join(out, f"{name}.fn.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"n": n, "m": m, "table": t}, f)
        write_blif(os.path.join(out, f"{name}.blif"), name.replace("-", "_"), n, m, t)
        print(name, n, m)


if __name__ == "__main__":
    main()
