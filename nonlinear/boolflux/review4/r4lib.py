"""Helpers for the review-4 reproductions: run the gate kernel directly on a circuit."""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))          # nonlinear/
from boolflux import core, objective, workflow     # noqa: E402

TMP = HERE / 'tmp'
BIN = TMP / 'bin'


def build():
    BIN.mkdir(parents=True, exist_ok=True)
    for b in ('bfx', 'skel'):
        src = HERE.parent / 'kernel' / (b + '.c')
        out = BIN / b
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            subprocess.run(['gcc', '-O2', '-o', str(out), str(src), '-lm'], check=True)
    return BIN / 'bfx'


def write_model(name, gates, not_as='NOT'):
    p = TMP / ('%s.json' % name)
    p.write_text(json.dumps({'name': name, 'gates': gates, 'not_as': not_as}) + '\n', encoding='utf-8')
    return p


def kernel(c, model, wd, objective_spec='cost', caps=None, extra=None, iters=0, seed=1, seconds=60):
    """Run bfx with the same config as cli/workflow (workflow.kernel_cfg); returns (log, out circuit)."""
    wd = Path(wd); wd.mkdir(parents=True, exist_ok=True)
    (wd / 'in.bfx').write_text(core.to_kernel(c))
    run = {'objective': objective_spec, 'caps': caps or {}}
    workflow.kernel_cfg(wd / 'k.cfg', wd / 'in.bfx', wd / 'out.bfx', model, run, seconds, seed,
                        extra or {}, iters=iters)
    r = subprocess.run([str(build()), str(wd / 'k.cfg')], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stdout + r.stderr)
    return r.stdout, core.from_kernel((wd / 'out.bfx').read_text())


def line(log, tag):
    for ln in log.splitlines():
        t = ln.split()
        if t and t[0] == tag:
            return {t[i]: t[i + 1] for i in range(1, len(t) - 1, 2)}
    return None


def random_circuit(n, m, ng, ops, rng):
    gates = []
    for j in range(ng):
        op = rng.choice(ops)
        a = rng.randrange(n + j)
        b = a if op == 3 else rng.randrange(n + j)
        if op != 3 and a == b:
            b = (a + 1) % (n + j) if n + j > 1 else a
        gates.append((op, a, b))
    outs = [n + ng - 1 - k for k in range(m)]
    return core.Circuit(n, m, gates, outs).live()
