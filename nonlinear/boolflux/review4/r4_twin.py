"""review4: kernel vs Python twins on random circuits.

(1) cost/G/A/GD/AD of the kernel (`start` line after its clean-up) == core.metrics == verify.py
    compute_metrics, for unit, fractional, large and zero gate costs;
(2) kernel VSUM (recovered from obj = cost + 1e6*viol + 1e4*vsum, objective `cost`) ==
    objective.path_excess, with GD caps, AD caps and both, on circuits that violate them;
(3) the same with `--set gdw.3=0` (kernel gate-depth weight of NOT = 0): the kernel's GD, feasibility
    and VSUM are no longer the Python ones.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r4lib as L                                   # noqa: E402
from r4lib import core, objective                   # noqa: E402

sys.path.insert(0, str(L.HERE.parent / 'independent'))
import verify as V                                  # noqa: E402

MODELS = {
    'unit': {'AND': 1, 'OR': 1, 'XOR': 1, 'XNOR': 1, 'NAND': 1, 'NOR': 1, 'ANDN': 1, 'ORN': 1, 'NOT': 1},
    'frac': {'AND': 1.37, 'OR': 2.5, 'XOR': 0.333, 'XNOR': 0.71, 'NAND': 1.0, 'NOR': 3.25, 'ANDN': 0.05, 'ORN': 7.5, 'NOT': 0},
    'big': {'AND': 1234.5, 'OR': 999, 'XOR': 3, 'XNOR': 7, 'NAND': 10000, 'NOR': 1, 'ANDN': 250, 'ORN': 0.125, 'NOT': 42},
}


def main():
    rng = random.Random(4)
    ops = [8, 14, 6, 9, 7, 1, 4, 13, 3]
    bad = {'metrics': 0, 'vsum': 0, 'cases': 0, 'viol_cases': 0}
    for mname, gates in MODELS.items():
        mp = L.write_model('r4-' + mname, gates)
        model = core.Model.load(str(mp))
        for t in range(60):
            c = L.random_circuit(6, 3, rng.randrange(15, 60), ops, rng)
            m0 = c.metrics(model)
            caps = [{'GD': max(1, m0['GD'] - 2)}, {'AD': max(0, m0['AD'] - 1)},
                    {'GD': max(1, m0['GD'] - 1), 'AD': max(0, m0['AD'] - 1)}, {}][t % 4]
            try:
                log, out = L.kernel(c, model, L.TMP / 'twin' / mname, 'cost', caps, iters=0)
            except RuntimeError:
                continue          # random circuit with a structurally constant gate
            st = L.line(log, 'start')
            pm = objective.measure(out, model, caps)
            # verify.py on the NCFF the CLI would write
            out.in_names = ['x%d' % i for i in range(6)]; out.out_names = ['y%d' % j for j in range(3)]
            vm = V.compute_metrics(V.parse_circuit(core.write_ncff(out, model)), {'name': mname, 'gates': gates})
            bad['cases'] += 1
            ok = (abs(float(st['cost']) - pm['cost']) < 1e-4 and abs(vm['cost'] - pm['cost']) < 1e-6
                  and all(int(st[k]) == pm[k] == vm[k] for k in ('G', 'A', 'GD', 'AD')))
            if not ok:
                bad['metrics'] += 1
                print('METRICS MISMATCH', mname, st, {k: pm[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}, vm.get('cost'))
            e = objective.excess(pm, caps)
            if e:
                bad['viol_cases'] += 1
                k_vsum = (float(st['obj']) - pm['cost'] - 1e6 * e) / 1e4
                if abs(k_vsum - pm['VSUM']) > 1e-6:
                    bad['vsum'] += 1
                    print('VSUM MISMATCH', mname, caps, 'kernel', k_vsum, 'python', pm['VSUM'])
    print('(1)+(2) %d circuits (%d violating a cap): metric mismatches %d, VSUM mismatches %d'
          % (bad['cases'], bad['viol_cases'], bad['metrics'], bad['vsum']))

    # (3) gdw override
    model = core.Model.load(str(L.write_model('r4-unit', MODELS['unit'])))
    n_gd = n_feas = 0; ex = None
    for t in range(40):
        c = L.random_circuit(6, 3, rng.randrange(20, 50), [8, 6, 3, 3, 3], rng)
        m0 = c.metrics(model); caps = {'GD': m0['GD'] - 1}
        try:
            log, out = L.kernel(c, model, L.TMP / 'twin' / 'gdw', 'cost', caps, extra={'gdw.3': 0}, iters=0)
        except RuntimeError:
            continue
        st = L.line(log, 'start'); pm = objective.measure(out, model, caps)
        if int(st['GD']) != pm['GD']: n_gd += 1
        kfeas = int(st['feas']); pfeas = int(objective.feasible(pm, caps))
        if kfeas != pfeas:
            n_feas += 1; ex = ex or (caps, st['GD'], pm['GD'], kfeas, pfeas)
    print('(3) gdw.3=0: kernel GD != Python GD in %d/40 circuits; kernel feasible != Python feasible in %d/40; e.g. caps %s kernel GD %s python GD %s kernel feas %s python feas %s'
          % ((n_gd, n_feas) + (ex or (None,) * 5)))


if __name__ == '__main__':
    main()
