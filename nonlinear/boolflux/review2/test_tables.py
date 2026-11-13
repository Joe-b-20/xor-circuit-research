"""Old vs new: core.value_table, core.tables_from_values, starts.anf_coeffs; targets.load('map:...').

    taskset -c 16 python3 test_tables.py
"""
import importlib.util
import random
import sys

from common import R2, REPO, core, starts, targets

sys.path.insert(0, str(R2 / 'old'))


def load_old(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    src = path.read_text().replace('from .core import', 'from boolflux.core import')
    exec(compile(src, str(path), 'exec'), mod.__dict__)
    return mod


core_old = load_old('core_old', R2 / 'old' / 'core_old.py')
starts_old = load_old('starts_old', R2 / 'old' / 'starts_old.py')


def old_value_table(c):
    outs = c.output_tables(); m = c.m
    return [sum(((t >> x) & 1) << (m - 1 - j) for j, t in enumerate(outs)) for x in range(1 << c.n)]


def main():
    rng = random.Random(7); bad = 0; cnt = 0
    for trial in range(3000):
        n = rng.randint(1, 10); m = rng.randint(1, 12)
        table = [rng.getrandbits(m) for _ in range(1 << n)]
        a = core.tables_from_values(n, m, table); b = core_old.tables_from_values(n, m, table)
        cnt += 1
        if a != b: bad += 1; print('tables_from_values differs', n, m)
        # value_table via a circuit whose outputs are inputs / random gates
        gates = []
        for j in range(rng.randint(0, 30)):
            s = n + j; op = rng.choice([8, 6, 9, 14, 7, 1, 4, 13, 3])
            x = rng.randrange(s); y = x if op == 3 else rng.randrange(s)
            gates.append((op, x, y))
        outs = [rng.randrange(n + len(gates)) for _ in range(m)]
        c = core.Circuit(n, m, gates, outs, 't')
        if c.value_table() != old_value_table(c): bad += 1; print('value_table differs', n, m)
        # round trip
        if core.tables_from_values(n, m, c.value_table()) != c.output_tables(): bad += 1; print('round trip differs')
        t = rng.getrandbits(1 << n)
        new = starts.anf_coeffs(t, n); old = starts_old.anf_coeffs(t, n)
        if [(new >> u) & 1 for u in range(1 << n)] != old: bad += 1; print('anf_coeffs differs', n)
    # anf start circuits identical to the old construction
    for name, model in (('present', 'bgc'), ('gf16-mul', 'xag'), ('aes', 'nist'), ('ascon', 'gc'), ('maj3', 'xag')):
        n, m, table, _ = targets.load(name); ops = core.Model.load(model).ops()
        a = starts.anf(n, m, table, ops); b = starts_old.anf(n, m, table, ops)
        same = core.to_kernel(a) == core.to_kernel(b)
        print('anf start', name, model, 'identical' if same else 'DIFFERENT'); bad += (not same)
    # linear maps: targets.load('map:X') against a direct row evaluation
    import glob
    maps = sorted(p.split('/')[-2] for p in glob.glob(str(REPO / 'circuits' / '*' / '*.mat.txt')))
    nm = 0; extra = []
    for mp in maps:
        toks = (REPO / 'circuits' / mp / (mp + '.mat.txt')).read_text().split()
        mm, nn = int(toks[1]), int(toks[2])
        if len(toks) != 3 + mm * nn: extra.append((mp, len(toks) - 3 - mm * nn))
        if nn > 16: continue
        n, m, table, _ = targets.load('map:' + mp)
        rows = [[int(t) for t in toks[3 + j * nn: 3 + (j + 1) * nn]] for j in range(mm)]
        for x in rng.sample(range(1 << n), min(1 << n, 300)):
            xb = [(x >> (n - 1 - i)) & 1 for i in range(n)]
            want = sum((sum(r[i] & xb[i] for i in range(n)) & 1) << (m - 1 - j) for j, r in enumerate(rows))
            if table[x] != want: bad += 1; print('map differs', mp, x); break
        nm += 1
        if mp in ('joltik', 'small-scale-aes', 'klsw17-m-4x4-gf16'):
            # the repository's own circuits for this map must verify against the BoolFlux target
            for f in glob.glob(str(REPO / 'circuits' / mp / '*.circ.txt')):
                c = core.read_ncff(f)
                ok = c.value_table() == table
                print('repo circuit', f.split('/')[-1], 'computes BoolFlux target:', ok); bad += (not ok)
    print('maps checked', nm, 'maps with extra tokens after the matrix (affine line ignored by targets.load):', extra)
    print('random trials', cnt, 'mismatches', bad)


if __name__ == '__main__':
    main()
