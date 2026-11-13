#!/usr/bin/env python3
"""Netlist conversion for the ABC comparator.

  netconv.py blif2ncff MAPPED.blif OUT.circ.txt   # ABC mapped BLIF (.gate) -> NCFF
  netconv.py ncff2blif IN.circ.txt OUT.blif       # NCFF -> logic BLIF (.names)

blif2ncff accepts ABC's write_blif output after `map`/`amap`: `.gate CELL pin=net ... O=net`
lines for the cells of our genlibs, plus single-input `.names` buffers/inverters and
constant `.names` that ABC may emit for primary outputs. Buffers are removed by
renaming when that is free (the buffered net is an internal wire used by nothing else as
an output name); otherwise a BUF line is written and reported. Constants are reported.
The ordering of gates is a fresh topological sort.
"""
import re
import sys

CELL = {  # genlib cell -> (NCFF op, pin order)
    "AND2": ("AND", ("a", "b")), "OR2": ("OR", ("a", "b")),
    "XOR2": ("XOR", ("a", "b")), "XNOR2": ("XNOR", ("a", "b")),
    "NAND2": ("NAND", ("a", "b")), "NOR2": ("NOR", ("a", "b")),
    "INV": ("NOT", ("a",)), "BUF": ("BUF", ("a",)),
    "ZERO": ("CONST0", ()), "ONE": ("CONST1", ()),
}


def read_blif_lines(path):
    out, cur = [], ""
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#", 1)[0].rstrip()
        if line.endswith("\\"):
            cur += line[:-1] + " "
            continue
        cur += line
        if cur.strip():
            out.append(cur.strip())
        cur = ""
    return out


def blif2ncff(src, dst):
    lines = read_blif_lines(src)
    ins, outs, gates, notes = [], [], [], []  # gates: (op, out, [operands])
    i = 0
    while i < len(lines):
        t = lines[i].split()
        if t[0] == ".inputs":
            ins += t[1:]
        elif t[0] == ".outputs":
            outs += t[1:]
        elif t[0] == ".gate":
            cell = t[1]
            pins = dict(p.split("=", 1) for p in t[2:])
            op, order = CELL[cell]
            o = pins["O"]
            if op.startswith("CONST"):
                gates.append((op, o, []))
            else:
                gates.append((op, o, [pins[p] for p in order]))
        elif t[0] == ".names":
            sig = t[1:]
            cover = []
            while i + 1 < len(lines) and not lines[i + 1].startswith("."):
                i += 1
                cover.append(lines[i].split())
            if len(sig) == 1:
                val = 1 if cover and cover[0] == ["1"] else 0
                gates.append((f"CONST{val}", sig[0], []))
            elif len(sig) == 2 and cover in ([["1", "1"]], [["0", "0"]]):
                gates.append(("BUF", sig[1], [sig[0]]))
            elif len(sig) == 2 and cover in ([["0", "1"]], [["1", "0"]]):
                gates.append(("NOT", sig[1], [sig[0]]))
            else:
                raise SystemExit(f"unsupported .names in mapped netlist: {lines[i]}")
        elif t[0] in (".model", ".end", ".default_input_arrival", ".default_output_required",
                      ".default_input_drive", ".default_output_load", ".default_max_input_load"):
            pass
        else:
            raise SystemExit(f"unexpected BLIF line: {lines[i]}")
        i += 1

    # remove free buffers: BUF out <- src where src is an internal net and not a PO,
    # and src feeds exactly this one buffer as a PO alias -> rename src to out.
    outset = set(outs)
    changed = True
    while changed:
        changed = False
        for g in list(gates):
            if g[0] != "BUF":
                continue
            _, o, (s,) = g
            if s in ins or s in outset:
                continue
            aliases = [h for h in gates if h[0] == "BUF" and h[2][0] == s]
            if len(aliases) != 1:
                continue
            gates.remove(g)
            gates = [(op, (o if oo == s else oo), [o if a == s else a for a in args])
                     for op, oo, args in gates]
            changed = True
            break

    # constants: express as explicit gates on input x0 (honest count), reported
    final = []
    for op, o, args in gates:
        if op == "CONST0":
            notes.append(f"constant-0 net {o}: written as XOR {o} {ins[0]} {ins[0]} (1 gate)")
            final.append(("XOR", o, [ins[0], ins[0]]))
        elif op == "CONST1":
            notes.append(f"constant-1 net {o}: written as XNOR {o} {ins[0]} {ins[0]} (1 gate)")
            final.append(("XNOR", o, [ins[0], ins[0]]))
        else:
            if op == "BUF":
                notes.append(f"BUF kept: {o} <- {args[0]}")
            final.append((op, o, args))

    # topological sort
    driver = {o: k for k, (_, o, _) in enumerate(final)}
    assert len(driver) == len(final), "net driven twice"
    done, order = set(ins), []
    state = {}

    def visit(k):
        if state.get(k) == 2:
            return
        if state.get(k) == 1:
            raise SystemExit("combinational loop")
        state[k] = 1
        for a in final[k][2]:
            if a not in done:
                visit(driver[a])
        state[k] = 2
        order.append(k)
        done.add(final[k][1])

    for o in outs:
        if o not in ins:
            visit(driver[o])
    dead = len(final) - len(order)
    if dead:
        notes.append(f"{dead} dead gates dropped")

    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("%NCFF-0.1-2026\n% converted from ABC mapped BLIF " + src.split("/")[-1] + "\n")
        for n_ in notes:
            f.write(f"% note: {n_}\n")
        f.write("begin circuit abc\n")
        f.write("Inputs: " + " ".join(ins) + "\n")
        f.write("Outputs: " + " ".join(outs) + "\n")
        f.write("begin SLP\n")
        for k in order:
            op, o, args = final[k]
            f.write(" ".join([op, o] + args) + "\n")
        f.write("end SLP\nend circuit\n")
    for n_ in notes:
        print("note:", n_)
    print(f"wrote {dst}: {len(order)} gate lines")


def expand(tokens):
    res = []
    for t in tokens:
        m = re.fullmatch(r"([A-Za-z_]+)(\d+):\1?(\d+)", t) or re.fullmatch(r"([A-Za-z_]+)(\d+):[A-Za-z_]+(\d+)", t)
        if m:
            p, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            step = 1 if b >= a else -1
            res += [f"{p}{k}" for k in range(a, b + step, step)]
        else:
            res.append(t)
    return res


COVER = {
    "AND": ["11 1"], "OR": ["1- 1", "-1 1"], "XOR": ["10 1", "01 1"], "XNOR": ["11 1", "00 1"],
    "NAND": ["0- 1", "-0 1"], "NOR": ["00 1"], "NOT": ["0 1"], "BUF": ["1 1"],
}


def ncff2blif(src, dst):
    ins, outs, gates, in_slp = [], [], [], False
    for raw in open(src, encoding="utf-8"):
        line = re.split(r"[%#]", raw, 1)[0].strip()
        if not line:
            continue
        t = line.split()
        if t[0] == "Inputs:":
            ins = expand(t[1:])
        elif t[0] == "Outputs:":
            outs = expand(t[1:])
        elif line == "begin SLP":
            in_slp = True
        elif line == "end SLP":
            in_slp = False
        elif in_slp:
            gates.append((t[0].upper(), t[1], t[2:]))
    lines = [".model warm", ".inputs " + " ".join(ins), ".outputs " + " ".join(outs)]
    for op, o, args in gates:
        if any(a in ("0", "1") for a in args):
            raise SystemExit("constant operands not supported")
        lines.append(".names " + " ".join(args) + " " + o)
        lines += COVER[op]
    lines.append(".end")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {dst}: {len(gates)} gates")


if __name__ == "__main__":
    {"blif2ncff": blif2ncff, "ncff2blif": ncff2blif}[sys.argv[1]](sys.argv[2], sys.argv[3])
