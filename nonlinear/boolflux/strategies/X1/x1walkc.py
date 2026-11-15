#!/usr/bin/env python3
"""Driver for the C walk (bfw.c): circuit -> product program -> bfw -> programs with fewer ANDs ->
circuits (x1lib.materialise), each checked on all 256 inputs.

    python3 x1walkc.py FILE OUT_DIR [--seconds S] [--seed N] [--plus K] [--psplit P] [--horizon H] [--redec P]
"""
import json, subprocess, sys, time, random, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import x1lib as X
from boolflux.hub.common import load, metrics, sbox
from boolflux import core

TARGET = core.tables_from_values(8, 8, list(sbox()))


def binary(out):
    src = HERE / "bfw.c"; h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
    b = Path(out) / ("bfw-" + h)
    if not b.exists():
        import os
        Path(out).mkdir(parents=True, exist_ok=True)
        tmp = str(b) + ".tmp%d" % os.getpid()
        subprocess.run(["gcc", "-O3", "-march=native", "-o", tmp, str(src)], check=True)
        os.replace(tmp, b)            # atomic: several shards may start at once
    return b


def write_prog(p, path):
    # compact the product bits into 9..63
    ks = sorted(p.ands)
    assert len(ks) <= 54, "too many ANDs for bfw"
    mp = {k: p.n + 1 + x for x, k in enumerate(ks)}
    def tr(f):
        g = f & ((1 << (p.n + 1)) - 1)
        for b in X.bits(f >> (p.n + 1) << (p.n + 1)): g |= 1 << mp[b]
        return g
    lines = ["and %d %x %x" % (mp[k], tr(p.ands[k][0]), tr(p.ands[k][1])) for k in ks]
    lines += ["out %x" % tr(o) for o in p.outs]
    Path(path).write_text("\n".join(lines) + "\n")


def read_prog(path, n=8, m=8):
    p = X.Prog(n, m)
    for ln in Path(path).read_text().split("\n"):
        t = ln.split()
        if not t: continue
        if t[0] == "and": p.ands[int(t[1])] = [int(t[2], 16), int(t[3], 16)]
        else: p.outs.append(int(t[1], 16))
    return p


def run(c, out, seconds, seed, plus=1, psplit=0.02, horizon=20000, redec=0.2, tag="w", adcap=0, dump=0, tabu=0, shift=0.0, pmerge=1.0):
    """returns [(circuit, A)] for every new best AND count (all verified)"""
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    p = X.extract(c); p.reduce()
    pf = out / ("%s-s%d.in.prog" % (tag, seed)); write_prog(p, pf)
    pre = out / ("%s-s%d" % (tag, seed))
    r = subprocess.run([str(binary(out)), str(pf), str(pre), str(seconds), str(seed), str(plus), str(psplit), str(horizon), str(redec), str(adcap), str(dump), str(tabu), str(shift), str(pmerge)],
                       capture_output=True, text=True)
    log = r.stdout + r.stderr
    (out / ("%s-s%d.log" % (tag, seed))).write_text(log)
    res = []
    for f in sorted(out.glob("%s-s%d.*.prog" % (tag, seed))):
        if f.name.endswith(".in.prog") or ".span" in f.name: continue
        q = read_prog(f, c.n, c.m)
        if not X.check(q, TARGET): print("WRONG PROGRAM", f); continue
        q.reduce()
        nc = X.materialise(q, random.Random(seed))
        if tuple(nc.value_table()) != sbox(): print("WRONG CIRCUIT", f); continue
        res.append((nc, q.A))
    return res, log


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(name, d): return type(d)(a[a.index(name) + 1]) if name in a else d
    c = load(a[0]); out = Path(a[1]); seed = opt("--seed", 1)
    tag = Path(a[0]).name.split(".")[0][:44]
    res, log = run(c, out, opt("--seconds", 60.0), seed, opt("--plus", 1), opt("--psplit", 0.02), opt("--horizon", 20000), opt("--redec", 0.2), tag, opt("--adcap", 0), opt("--dump", 0), opt("--tabu", 0), opt("--shift", 0.0), opt("--pmerge", 1.0))
    print(Path(a[0]).name, metrics(c)); print(log.strip())
    for nc, A in res:
        m = metrics(nc); name = "walk-%s-s%d-a%d" % (tag, seed, m[0])
        (out / (name + ".bfx")).write_text(core.to_kernel(nc))
        (out / (name + ".json")).write_text(json.dumps({"method": "x1walkc (bfw.c) flip/split walk + x1lib.materialise", "source": a[0],
            "seed": seed, "args": a[2:], "metrics": m, "time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}))
        print("VERIFIED", name, m)
