"""Skeleton rebuild checks.

1. Incremental Paar: new skeleton.synthesize(parent=None) vs the old implementation (9f4c8df), for
   all three unseeded variants, byte for byte.  A second old copy gets only the new
   "complemented forms are not terms" line in build(), to separate that change from Paar.
2. Seeded rebuild: synthesize(parent=c) on skeletons after 0..300 skeleton-kernel iterations
   (emit_current 1), parents from results/, NIST AES circuits and equivalence-mutated parents
   (NOT pushing, AND -> NOR/ANDN forms, XOR -> XNOR(NOT a, b)); checks the truth table, the gate
   library, exceptions, and AND depth / gate depth against the parent's caps.
    taskset -c 16 python3 test_synth.py [--quick]
"""
import glob
import json
import random
import sys
import time
from pathlib import Path

from common import BIN, R2, REPO, TMP, core, skeleton, targets, write_cfg, run_pinned

NL = core.NONLINEAR_OPS


def load_old(path, patch_fm=False):
    src = path.read_text().replace('from .core import', 'from boolflux.core import')
    if patch_fm:
        a = "            for fm, s in have.items():\n"
        assert a in src
        src = src.replace(a, a + "                if fm & 1: continue\n", 1)
    mod = {}
    exec(compile(src, str(path), 'exec'), mod)
    return mod


OLD = load_old(R2 / 'old' / 'skeleton_old.py')
OLDFIX = load_old(R2 / 'old' / 'skeleton_old.py', patch_fm=True)


def parents():
    out = []
    for f in sorted(glob.glob(str(REPO / 'nonlinear' / 'boolflux' / 'results' / '*' / '*.summary.json'))):
        if '_superseded' in f: continue
        s = json.loads(Path(f).read_text())
        cf = Path(f.replace('.summary.json', '.circ.txt'))
        if not cf.exists(): continue
        try:
            out.append((cf.name, s['target'], s['model'], core.read_ncff(str(cf))))
        except Exception as e:
            print('skip', cf.name, repr(e))
    for f in sorted(glob.glob(str(REPO / 'nonlinear' / 'nist' / 'aes-sbox' / '*.circ.txt')))[::4]:
        out.append((Path(f).name, 'aes', 'nist', core.read_ncff(f)))
    return out


def mutate(c, ops, rng):
    """Equivalent circuit with more complemented structure (only ops in the library)."""
    n = c.n; gates = []; sig = list(range(n))
    def g(op, a, b): gates.append((op, a, b)); return n + len(gates) - 1
    has = lambda name: core.OPS[name] in ops
    for op, a, b in c.gates:
        a2, b2 = sig[a], sig[b]
        r = rng.random()
        if op == 8 and has('NOR') and has('NOT') and r < 0.4:
            s = g(core.OPS['NOR'], g(3, a2, a2), g(3, b2, b2))
        elif op == 8 and has('ANDN') and has('NOT') and r < 0.7:
            s = g(core.OPS['ANDN'], a2, g(3, b2, b2))
        elif op == 8 and has('NAND') and has('NOT') and r < 0.9:
            s = g(3, g(core.OPS['NAND'], a2, b2), 0); gates[-1] = (3, gates[-1][1], gates[-1][1])
        elif op == 6 and has('XNOR') and has('NOT') and r < 0.3:
            s = g(core.OPS['XNOR'], g(3, a2, a2), b2)
        elif op == 6 and has('NOT') and r < 0.4:
            s = g(3, g(3, g(6, a2, b2), 0), 0)
            gates[-2] = (3, gates[-2][1], gates[-2][1]); gates[-1] = (3, gates[-1][1], gates[-1][1])
        else:
            s = g(op, a2, b2)
        sig.append(s)
    return core.Circuit(n, c.m, gates, [sig[o] for o in c.outputs], c.name).live()


def skel_run(sk, outs, iters, seed, cap_ad, emit, cpu=16):
    d = TMP / 'synth'; d.mkdir(exist_ok=True)
    (d / 'in').write_text(skeleton.write_skel(sk, outs))
    cfg = {'in': d / 'in', 'out': d / 'out', 'seed': seed, 'iters': iters, 'seconds': 120, 'emit_current': emit,
           'T0': 0.3, 'Tperiod_it': 4000}
    if cap_ad is not None: cfg['cap.ad'] = cap_ad
    write_cfg(d / 'cfg', cfg)
    r = run_pinned([BIN / 'skel', d / 'cfg'], cpu)
    if r.returncode != 0: return None
    return skeleton.read_skel((d / 'out').read_text())


def gates_key(c):
    return (tuple(c.gates), tuple(c.outputs))


def main():
    quick = '--quick' in sys.argv
    rng = random.Random(11)
    stats = {'paar_cases': 0, 'paar_diff_vs_old': 0, 'paar_diff_vs_oldfix': 0, 'old_exceptions': 0,
             'seeded_cases': 0, 'seeded_wrong': 0, 'seeded_exc': 0, 'unseeded_exc': 0, 'seeded_lib': 0,
             'seeded_ad_over_parent': 0, 'unseeded_ad_over_parent': 0, 'chosen_ad_over_parent': 0,
             'seeded_better': 0, 'seeded_worse': 0, 'tie': 0}
    examples = []
    ps = parents()
    print(len(ps), 'parent circuits'); sys.stdout.flush()
    t0 = time.time()
    for name, tgt, model_name, c0 in ps:
        model = core.Model.load(model_name); ops = model.ops()
        n, m, table, _ = targets.load(tgt)
        if c0.value_table() != table: print('parent wrong?!', name); continue
        outs = core.tables_from_values(n, m, table)
        variants = [('orig', c0)]
        mc = mutate(c0, ops, rng)
        assert mc.value_table() == table and {g[0] for g in mc.gates} <= ops
        variants.append(('mut', mc))
        for vname, c in variants:
            cap_ad = c.metrics(model)['AD']
            sk = skeleton.extract(c)
            iters_list = (0, 3, 30) if quick else (0, 1, 3, 10, 30, 100, 300)
            for iters in iters_list:
                seed = rng.randint(1, 10 ** 6)
                for emit in ((1,) if iters else (0,)):
                    sk2 = skel_run(sk, outs, iters, seed, cap_ad, emit)
                    if sk2 is None: continue
                    # 1. Paar identity
                    for up, po in ((False, False), (True, False), (True, True)):
                        stats['paar_cases'] += 1
                        new = skeleton.synthesize(sk2, ops, use_paar=up, paar_outputs=po)
                        try:
                            old = OLD['synthesize'](sk2, ops, use_paar=up, paar_outputs=po)
                            if gates_key(old) != gates_key(new): stats['paar_diff_vs_old'] += 1
                        except Exception:
                            stats['old_exceptions'] += 1
                        oldf = OLDFIX['synthesize'](sk2, ops, use_paar=up, paar_outputs=po)
                        if gates_key(oldf) != gates_key(new):
                            stats['paar_diff_vs_oldfix'] += 1
                            if len(examples) < 5: examples.append(('paar', name, vname, iters, up, po))
                        if new.value_table() != table: print('UNSEEDED WRONG', name)
                    # 2. seeded
                    stats['seeded_cases'] += 1
                    try:
                        se = skeleton.synthesize(sk2, ops, parent=c)
                    except Exception as e:
                        stats['seeded_exc'] += 1; examples.append(('seeded_exc', name, vname, iters, repr(e))); continue
                    if se.value_table() != table:
                        stats['seeded_wrong'] += 1; examples.append(('seeded_wrong', name, vname, iters))
                    if not {g[0] for g in se.gates} <= ops: stats['seeded_lib'] += 1
                    uns = [skeleton.synthesize(sk2, ops, use_paar=a, paar_outputs=b) for a, b in ((0, 0), (1, 0), (1, 1))]
                    ub = min(uns, key=lambda x: x.metrics(model)['cost'])
                    chosen = min([se] + uns, key=lambda x: x.metrics(model)['cost'])
                    ms, mu, mch = se.metrics(model), ub.metrics(model), chosen.metrics(model)
                    stats['seeded_ad_over_parent'] += ms['AD'] > cap_ad
                    stats['unseeded_ad_over_parent'] += mu['AD'] > cap_ad
                    stats['chosen_ad_over_parent'] += mch['AD'] > cap_ad
                    if ms['AD'] > cap_ad and len(examples) < 40:
                        examples.append(('seeded_AD', name, vname, iters, cap_ad, ms['AD'], mu['AD'], 'skelAD', ))
                    if ms['cost'] < mu['cost']: stats['seeded_better'] += 1
                    elif ms['cost'] > mu['cost']: stats['seeded_worse'] += 1
                    else: stats['tie'] += 1
        print(name, json.dumps(stats), round(time.time() - t0), 's'); sys.stdout.flush()
    print('FINAL', json.dumps(stats))
    for e in examples[:40]: print('example', e)
    (TMP / 'test_synth.json').write_text(json.dumps({'stats': stats, 'examples': examples}, indent=1))


if __name__ == '__main__':
    main()
