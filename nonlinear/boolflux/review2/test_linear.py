"""Exact linear mode: for affine circuits, linear 1 (n+1 patterns) must make exactly the same
decisions as linear 0 (all 2^n patterns), since every equality test and care set is then exact in
both.  Same seed, iteration budget -> identical timing-free stdout and identical output circuit.
Also: guards (nonlinear op in the library; start with an op outside the library), and every
final circuit re-verified on all 2^n inputs by an independent evaluator.
    taskset -c 16 python3 test_linear.py
"""
import json
import random
from concurrent.futures import ThreadPoolExecutor

from common import BIN, TMP, core, starts, targets, write_cfg, run_pinned, strip_times, eval_circuit, base_cfg

CPUS = [18, 19]
D = TMP / 'linear'; D.mkdir(exist_ok=True)


def rand_affine(rng, n, m, affine):
    rows = [rng.getrandbits(n) or 1 for _ in range(m)]
    consts = [rng.getrandbits(1) if affine else 0 for _ in range(m)]
    table = []
    for x in range(1 << n):
        v = 0
        for j, r in enumerate(rows):
            bit = (bin(x & r).count('1') + consts[j]) & 1      # row bit k <-> x bit k
            v |= bit << (m - 1 - j)
        table.append(v)
    return table


def affine_start(rng, n, m, table, lib):
    """Naive affine start: per output an XOR chain of its inputs, complements via XNOR/NOT,
    randomly sprinkled NOT pairs and XNOR(NOT a, b) when the library has them."""
    outs_t = core.tables_from_values(n, m, table)
    ins = core.input_tables(n); ones = (1 << (1 << n)) - 1
    gates = []; outs = []
    def g(op, a, b): gates.append((op, a, b)); return n + len(gates) - 1
    for t in outs_t:
        const = t & 1                                     # value at x = 0
        lin = t ^ (ones if const else 0)
        # coefficient of x_i: value at the unit vector of input i
        terms = [i for i in range(n) if (lin >> (1 << (n - 1 - i))) & 1]
        s = terms[0]
        for i in terms[1:]:
            if 9 in lib and 3 in lib and rng.random() < 0.3: s = g(9, g(3, s, s), i)
            else: s = g(6, s, i)
        if 3 in lib and rng.random() < 0.3: s = g(3, g(3, s, s), 0); gates[-1] = (3, gates[-1][1], gates[-1][1])
        if const:
            if 3 in lib: s = g(3, s, s)
            else:                                         # ~s = XNOR(XOR(s, j), j)
                j = 0 if s != 0 else 1; s = g(9, g(6, s, j), j)
        outs.append(s)
    c = core.Circuit(n, m, gates, outs, 'aff')
    assert c.value_table() == table, 'start construction'
    return c


def run_case(job):
    idx, n, m, lib, affine, iters, seed, cpu = job
    rng = random.Random(idx)
    table = rand_affine(rng, n, m, affine)
    if lib == (6,):
        c = starts.anf(n, m, table, {6})
    else:
        c = affine_start(rng, n, m, table, lib)
    d = D / ('c%d' % idx); d.mkdir(exist_ok=True)
    (d / 'start').write_text(core.to_kernel(c))
    res = {}
    for lin in (0, 1):
        cfg = dict(base_cfg(core.Model('x', {core.OPNAME[o]: 1 for o in lib}, 'NOT', ''), 'cost,gd'))
        cfg.update({'linear': lin, 'in': d / 'start', 'out': d / ('out%d' % lin), 'seed': seed, 'iters': iters, 'seconds': 1e9})
        write_cfg(d / ('cfg%d' % lin), cfg)
        r = run_pinned([BIN / 'bfx_new', d / ('cfg%d' % lin)], cpu)
        circ = core.from_kernel((d / ('out%d' % lin)).read_text()) if r.returncode == 0 else None
        ok = circ is not None and eval_circuit(n, circ.gates, circ.outputs) == table
        res[lin] = (r.returncode, strip_times(r.stdout), (d / ('out%d' % lin)).read_text() if r.returncode == 0 else None, ok,
                    r.stdout.splitlines()[-5] if r.returncode == 0 else r.stderr[-300:])
    return {'idx': idx, 'n': n, 'm': m, 'lib': lib, 'affine': affine, 'start_G': len(c.gates),
            'identical': res[0][1] == res[1][1] and res[0][2] == res[1][2], 'verified0': res[0][3], 'verified1': res[1][3],
            'final1': res[1][4]}


def guards():
    out = {}
    c = core.Circuit(2, 1, [(8, 0, 1)], [2], 'and')
    (D / 'g_start').write_text(core.to_kernel(c))
    for name, lib in (('and_in_library', {8: 1, 6: 1}), ('start_op_outside_library', {6: 1})):
        cfg = {'in': D / 'g_start', 'out': D / 'g_out', 'iters': 10, 'seed': 1, 'linear': 1}
        cfg.update({'cost.%d' % k: v for k, v in lib.items()})
        write_cfg(D / 'g_cfg', cfg)
        r = run_pinned([BIN / 'bfx_new', D / 'g_cfg'], 16)
        out[name] = (r.returncode, r.stderr.strip())
    return out


def main():
    rng = random.Random(5); jobs = []; idx = 0
    for n in (3, 4, 5, 6, 7, 8, 10, 12, 14, 16):
        for lib in ((6,), (6, 9, 3), (6, 9), (6, 3)):
            if lib != (6,) and n > 13: continue          # PCAP differs at W >= 256 with 2 binary ops
            for affine in ((False,) if lib == (6,) else (False, True)):
                for rep in range(2):
                    m = rng.randint(2, min(16, 2 * n))
                    iters = 3000 if n <= 12 else 1500
                    jobs.append((idx, n, m, lib, affine, iters, rng.randint(1, 1000), CPUS[idx % len(CPUS)])); idx += 1
    with ThreadPoolExecutor(max_workers=len(CPUS)) as ex:
        res = list(ex.map(run_case, jobs))
    for r in res: print(json.dumps(r))
    print('cases', len(res), 'identical', sum(r['identical'] for r in res),
          'verified (linear 1)', sum(r['verified1'] for r in res), 'verified (linear 0)', sum(r['verified0'] for r in res))
    print('guards', guards())
    (TMP / 'test_linear.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
