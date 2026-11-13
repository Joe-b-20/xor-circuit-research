"""Shared helpers for the review2 test scripts (nothing here modifies files outside review2/)."""
import os
import subprocess
import sys
from pathlib import Path

R2 = Path(__file__).resolve().parent
PKG = R2.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))
from boolflux import core, starts, targets, skeleton   # noqa: E402,F401
import cli                                              # noqa: E402

BIN = R2 / 'bin'
TMP = R2 / 'tmp'; TMP.mkdir(exist_ok=True)
CPUS = [17, 18, 19]   # parent python on 16: at most 4 processes


def run_pinned(cmd, cpu, **kw):
    return subprocess.run(['taskset', '-c', str(cpu)] + [str(c) for c in cmd], capture_output=True, text=True, **kw)


def write_cfg(path, d):
    Path(path).write_text(''.join('%s %s\n' % kv for kv in d.items()))


def base_cfg(model, objective, caps=None):
    cfg = dict(cli.DEFAULTS); cfg.update(cli.objective_weights(objective))
    for op, c in model.cost.items(): cfg['cost.%d' % op] = c
    for k, key in (('GD', 'cap.gd'), ('AD', 'cap.ad'), ('A', 'cap.a')):
        if caps and caps.get(k) is not None: cfg[key] = caps[k]
    return cfg


def eval_circuit(n, gates, outs):
    """Independent evaluator: list of output integers (msb/msb) for x in 0..2^n-1."""
    m = len(outs); res = []
    for x in range(1 << n):
        v = [(x >> (n - 1 - i)) & 1 for i in range(n)]
        for op, a, b in gates:
            v.append((op >> ((v[a] << 1) | v[b])) & 1)
        res.append(sum(v[o] << (m - 1 - j) for j, o in enumerate(outs)))
    return res


def strip_times(log):
    """Kernel stdout without wall-clock fields (t ..., seconds ..., move time ...)."""
    out = []
    for ln in log.splitlines():
        t = ln.split()
        if not t: continue
        if t[0] == 'best': t = t[:1] + t[3:]                       # drop 't <x>'
        elif t[0] == 'final': t = t[:t.index('seconds')]
        elif t[0] == 'move': t = t[:t.index('time')]
        out.append(' '.join(t))
    return '\n'.join(out)
