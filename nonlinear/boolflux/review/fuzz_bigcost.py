"""Randomized differential test of the gate kernel bfx (review harness, not part of BoolFlux).

    python3 nonlinear/boolflux/review/fuzz_bfx.py [CASES] [SEED] [BIN]

For each case: a random library (subset of the 9 ops, random costs), a random correct start
circuit over that library (n = 3..8), random caps (sometimes below the start's metrics, so the
start is infeasible), random objective weights; runs the kernel for a short iteration budget
and checks, with this file's own evaluator and metric code:
  * the output computes the same function as the start on all 2^n inputs;
  * every gate op is in the library, operands are earlier signals, NOT has b == a;
  * the kernel's reported metrics (file comment + 'final' line) equal recomputed ones;
  * 'feas 1' iff the caps hold; if the start was feasible the result is feasible;
  * the result's objective is <= the start's objective (when the start is feasible);
  * a second run with the same config gives a byte-identical output file;
  * round trip: core.from_kernel -> core.write_ncff -> independent/verify.py (--fn, --model)
    passes, and core / independent / own metrics agree.
"""
import json
import os
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BF = HERE.parent
sys.path.insert(0, str(BF.parent))
from boolflux import core  # noqa: E402

TMP = HERE / 'tmp'
TMP.mkdir(exist_ok=True)
NAMES = {8: 'AND', 14: 'OR', 6: 'XOR', 9: 'XNOR', 7: 'NAND', 1: 'NOR', 4: 'ANDN', 13: 'ORN', 3: 'NOT'}


def f2(op, a, b):
    return (op >> ((a << 1) | b)) & 1


def evaluate(n, gates, outs):
    """value table: per input integer x, msb-first inputs; returns list of output tuples."""
    res = []
    for x in range(1 << n):
        v = [(x >> (n - 1 - i)) & 1 for i in range(n)]
        for op, a, b in gates:
            v.append(f2(op, v[a], v[b]))   # NOT: b == a, f2(3, a, a) = ~a
        res.append(tuple(v[s] for s in outs))
    return res


def my_metrics(n, gates, outs, cost):
    lg = [0] * n; la = [0] * n; A = 0; c = 0.0
    for op, a, b in gates:
        nl = bin(op).count('1') & 1
        A += nl; c += cost[op]
        x = (a, b) if op != 3 else (a,)
        lg.append(1 + max(lg[t] for t in x)); la.append(nl + max(la[t] for t in x))
    return {'G': len(gates), 'A': A, 'GD': max(lg[s] for s in outs), 'AD': max(la[s] for s in outs),
            'cost': round(c, 6)}


def rand_circuit(rng, n, lib):
    binops = [o for o in lib if o != 3]
    ng = rng.randint(4, int(os.environ.get("NGMAX", "30")))
    gates = []
    for j in range(ng):
        hi = n + j
        op = rng.choice(lib)
        a = rng.randrange(hi)
        if op == 3:
            b = a
        else:
            b = rng.randrange(hi)
            while b == a and hi > 1:
                b = rng.randrange(hi)
        gates.append((op, a, b))
    m = rng.randint(1, 4)
    tot = n + ng
    outs = [rng.randrange(max(n, tot - 8), tot) for _ in range(m)]
    if rng.random() < 0.15: outs[rng.randrange(m)] = rng.randrange(n)
    if m > 1 and rng.random() < 0.15: outs[0] = outs[-1]
    return gates, outs


def nonconst(n, gates, outs):
    vt = evaluate(n, gates, outs)
    for k in range(len(outs)):
        col = {r[k] for r in vt}
        if len(col) < 2: return False
    return True


def run(binp, cfgp):
    r = subprocess.run([binp, cfgp], capture_output=True, text=True, timeout=300)
    return r


def parse_final(text):
    for ln in text.splitlines():
        t = ln.split()
        if t and t[0] == 'final':
            return {t[i]: float(t[i + 1]) for i in range(1, len(t) - 1, 2)}
    return None


def main():
    cases = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    binp = sys.argv[3] if len(sys.argv) > 3 else str(HERE / 'bfx')
    rng = random.Random(seed0)
    fails = []
    stats = {'cases': 0, 'start_infeasible': 0, 'repaired': 0, 'improved': 0}
    for case in range(cases):
        n = rng.randint(3, 8)
        allops = [8, 14, 6, 9, 7, 1, 4, 13, 3]
        lib = sorted(set(rng.sample(allops, rng.randint(2, 9))))
        if not any(bin(o).count('1') & 1 for o in lib): lib.append(8)
        cost = {o: 1e7 * rng.choice([1, 2]) for o in lib}
        for _ in range(20):
            gates, outs = rand_circuit(rng, n, lib)
            if nonconst(n, gates, outs): break
        else:
            continue
        sm = my_metrics(n, gates, outs, cost)
        caps = {}
        if rng.random() < 0.5: caps['cap.gd'] = max(1, sm['GD'] - rng.choice([0, 0, 1, 2, -1]))
        if rng.random() < 0.4: caps['cap.ad'] = max(1, sm['AD'] - rng.choice([0, 0, 1, -1]))
        caps["cap.a"] = sm["A"]
        tag = 'c%d_%d' % (seed0, case)
        sp = TMP / (tag + '.start'); op_ = TMP / (tag + '.out'); op2 = TMP / (tag + '.out2')
        sp.write_text('n %d\nm %d\ng %d\n' % (n, len(outs), len(gates)) +
                      ''.join('%d %d %d\n' % g for g in gates) + 'o ' + ' '.join(map(str, outs)) + '\n')
        objs = [['cost'], ['a', 'cost'], ['cost', 'gd'], ['gd', 'cost'], ['g', 'ad']][rng.randrange(5)]
        w = {'w.cost': 0, 'w.g': 0, 'w.a': 0, 'w.gd': 0, 'w.ad': 0}
        for i, k in enumerate(objs): w['w.' + k] += 10.0 ** (-4 * i)
        cfg = {'T0': rng.choice([0, 0.6, 1.5]), 'Tperiod_it': rng.choice([50, 500]), 'stall_it': rng.choice([30, 300]),
               'uphill': rng.choice([0, 1, 2]), 'max_excess': 8, 'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1,
               'dmax': rng.choice([10, 220]), 'pdiv': rng.choice([5, 90]), 'nl_samples': 12,
               'cand_cap': rng.choice([3, 40]), 'fraig': rng.choice([0, 1]),
               **w, **{'cost.%d' % o: c for o, c in cost.items()}, **caps,
               'seed': rng.randrange(1, 10 ** 6), 'seconds': 1000, 'iters': rng.choice([200, 1000, 3000])}
        def write_cfg(path, outp):
            Path(path).write_text(''.join('%s %s\n' % kv for kv in {**cfg, 'in': sp, 'out': outp}.items()))
        cp = TMP / (tag + '.cfg'); cp2 = TMP / (tag + '.cfg2')
        write_cfg(cp, op_); write_cfg(cp2, op2)
        r = run(binp, str(cp))
        stats['cases'] += 1
        err = []
        if r.returncode != 0:
            fails.append((tag, 'rc %d: %s' % (r.returncode, (r.stdout + r.stderr)[-400:]))); continue
        txt = op_.read_text()
        c = core.from_kernel(txt)
        # structure
        for j, (gop, a, b) in enumerate(c.gates):
            if gop not in lib: err.append('op %d not in library %s' % (gop, lib))
            if not (0 <= a < n + j and 0 <= b < n + j): err.append('bad operand at gate %d' % j)
            if gop == 3 and a != b: err.append('NOT with b != a')
        if evaluate(n, c.gates, c.outputs) != evaluate(n, gates, outs): err.append('FUNCTION DIFFERS')
        mm = my_metrics(n, c.gates, c.outputs, cost)
        # kernel's own report
        cm = [ln for ln in txt.splitlines() if ln.startswith('#')][-1].split()
        rep = {'cost': float(cm[2]), 'G': int(cm[4]), 'A': int(cm[6]), 'GD': int(cm[8]), 'AD': int(cm[10])}
        for k in rep:
            if abs(rep[k] - mm[k]) > 1e-6: err.append('reported %s %s != recomputed %s' % (k, rep[k], mm[k]))
        fin = parse_final(r.stdout)
        feas = all(mm[{'cap.gd': 'GD', 'cap.ad': 'AD', 'cap.a': 'A'}[k]] <= v for k, v in caps.items())
        sfeas = all(sm[{'cap.gd': 'GD', 'cap.ad': 'AD', 'cap.a': 'A'}[k]] <= v for k, v in caps.items())
        if not sfeas: stats['start_infeasible'] += 1
        if not sfeas and feas: stats['repaired'] += 1
        if fin is not None and 'feas' in fin and int(fin['feas']) != int(feas):
            err.append('kernel feas %s but caps say %s' % (fin['feas'], feas))
        if sfeas and not feas: err.append('START FEASIBLE BUT RESULT INFEASIBLE')
        def obj(m_):
            return sum(w['w.' + k.lower()] * m_[{'cost': 'cost', 'g': 'G', 'a': 'A', 'gd': 'GD', 'ad': 'AD'}[k]]
                       for k in ('cost', 'g', 'a', 'gd', 'ad'))
        if sfeas and obj(mm) > obj(sm) + 1e-9: err.append('result obj %g > start obj %g' % (obj(mm), obj(sm)))
        if sfeas and obj(mm) < obj(sm) - 1e-9: stats['improved'] += 1
        # reproducibility
        r2 = run(binp, str(cp2))
        if r2.returncode != 0 or op2.read_text() != txt: err.append('NOT REPRODUCIBLE')
        # round trip through NCFF + independent verifier
        c.in_names = ['x%d' % i for i in range(n)]; c.out_names = ['y%d' % j for j in range(c.m)]
        model = core.Model('m' + tag, {NAMES[o]: cost[o] for o in lib})
        ncf = TMP / (tag + '.circ.txt'); ncf.write_text(core.write_ncff(c, model))
        mj = TMP / (tag + '.model.json'); mj.write_text(json.dumps({'name': model.name, 'gates': model.gates}))
        vt = evaluate(n, gates, outs)
        table = [sum(b << (len(outs) - 1 - j) for j, b in enumerate(row)) for row in vt]
        fj = TMP / (tag + '.fn.json'); fj.write_text(json.dumps({'n': n, 'm': len(outs), 'table': table}))
        vr = subprocess.run([sys.executable, str(BF / 'independent' / 'verify.py'), str(ncf), '--fn', str(fj),
                             '--model', str(mj), '--json'], capture_output=True, text=True)
        try:
            ind = json.loads(vr.stdout)[0]
        except Exception:
            ind = {'ok': False, 'errors': [vr.stdout + vr.stderr]}
        if not ind['ok'] or vr.returncode != 0: err.append('independent FAIL: %s' % ind.get('errors'))
        c2 = core.read_ncff(str(ncf))
        if c2.value_table() != table: err.append('core read_ncff value table differs')
        cmet = c2.metrics(model)
        im = ind.get('metrics') or {}
        for k in ('G', 'A', 'GD', 'AD'):
            if cmet[k] != mm[k] or im.get(k) != mm[k]:
                err.append('metric %s: own %s core %s indep %s' % (k, mm[k], cmet[k], im.get(k)))
        if im.get('cost') is None or abs(im['cost'] - mm['cost']) > 1e-6 or abs(cmet['cost'] - mm['cost']) > 1e-6:
            err.append('cost: own %s core %s indep %s' % (mm['cost'], cmet['cost'], im.get('cost')))
        if err:
            fails.append((tag, '; '.join(err)))
        else:
            for p in (sp, op_, op2, cp, cp2, ncf, mj, fj):
                try: p.unlink()
                except OSError: pass
    print(json.dumps(stats))
    print('%d failures' % len(fails))
    for t, e in fails[:40]:
        print(t, e)


if __name__ == '__main__':
    main()
