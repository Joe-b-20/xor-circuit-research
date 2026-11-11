"""Print a recorded MixColumns circuit in the sheet language: python3 sheets.py FILE.circ.txt

Block j = the four inputs "bit j of byte c", c = 0..3. On a block, the even vectors are
  s0=1100 s1=0110 s2=0011 s3=1001 (adjacent pairs), d0=1010 d1=0101 (opposite pairs), t=1111,
and the odd vectors are e_c (one input) and E_c = t + e_c (the other three inputs).
An even signal is printed as the list of its nonzero block components, e.g. [2:s1 7:t].
An odd signal (odd on exactly one block when the partition is the canonical one) is printed as
  sheet j: e_c or E_c, followed by its even components on the other blocks.
Each gate line shows: name = operand + operand, kind (PRODUCER odd+odd, SUM even+even, OUTPUT, HELPER),
fan-out, and the value. Standard library only; examines an existing circuit.
"""
import pathlib
import re
import sys
from collections import Counter

GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")

EVEN = {(1, 1, 0, 0): "s0", (0, 1, 1, 0): "s1", (0, 0, 1, 1): "s2", (1, 0, 0, 1): "s3",
        (1, 0, 1, 0): "d0", (0, 1, 0, 1): "d1", (1, 1, 1, 1): "t"}
ODD = {(1, 0, 0, 0): "e0", (0, 1, 0, 0): "e1", (0, 0, 1, 0): "e2", (0, 0, 0, 1): "e3",
       (0, 1, 1, 1): "E0", (1, 0, 1, 1): "E1", (1, 1, 0, 1): "E2", (1, 1, 1, 0): "E3"}


def blocks(mu):
    return [tuple((mu >> (8 * c + r)) & 1 for c in range(4)) for r in range(8)]


def describe(mu):
    odd, even = [], []
    for j, b in enumerate(blocks(mu)):
        if b in ODD:
            odd.append(f"{j}:{ODD[b]}")
        elif b in EVEN:
            even.append(f"{j}:{EVEN[b]}")
    if len(odd) == 1:
        return f"POINT sheet {odd[0]}" + (f"  + [{' '.join(even)}]" if even else "")
    if not odd:
        return f"VECTOR [{' '.join(even)}]"
    return f"MIXED odd on {' '.join(odd)}  + [{' '.join(even)}]"


def main(circ):
    vals, order = {}, []
    for line in pathlib.Path(circ).read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = RANGE.match(line)
        if m and m.group(1) == "Inputs":
            base = int(m.group(3))
            for j in range(int(m.group(4)) - base + 1):
                vals[f"x{j + base}"] = 1 << j
            continue
        m = GATE.match(line)
        if m:
            _, out, a, b = m.groups()
            vals[out] = vals[a] ^ vals[b]
            order.append((out, a, b))
    fan = Counter()
    for out, a, b in order:
        fan[a] += 1
        fan[b] += 1
    par = lambda v: bin(v).count("1") & 1
    name = {}
    for k in vals:
        if k.startswith("x"):
            i = int(k[1:])
            name[k] = f"in(c{i // 8},j{i % 8})"
        elif k.startswith("y"):
            i = int(k[1:])
            name[k] = f"OUT(c{i // 8},j{i % 8})"
        else:
            name[k] = k
    for out, a, b in order:
        pa, pb = par(vals[a]), par(vals[b])
        if pa and pb:
            kind = "PRODUCER"
        elif not pa and not pb:
            kind = "SUM"
        else:
            kind = "OUTPUT" if out.startswith("y") else "HELPER"
        print(f"{name[out]:>12} = {name[a]:>12} + {name[b]:<12} {kind:<8} fan-out {fan[out]}  {describe(vals[out])}")


if __name__ == "__main__":
    main(sys.argv[1])
