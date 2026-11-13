"""Write the benchmark plan (predetermined seeds 1-5; budgets fixed before running).

    python3 nonlinear/boolflux/bench/make_plan.py PLAN.json [--only L,N,A,X,F] [--tag v1]

L  linear maps, XORFlux v8 vs XOR-only BoolFlux (gate level, linear mode), same start, same CPU
N  small nonlinear targets from naive ANF starts: full (skeleton + seeded rebuild + gate) vs gate
A  AES S-box: naive ANF start, and NIST warm starts (own caps; depth repair; the 104 record)
X  gate-kernel ablations (one mechanism off at a time) on PRESENT, RECTANGLE, GF(2^4) mult, AES
F  skeleton-level ablations (no merge move; rebuild without parent seeding)
"""
import json
import sys
from pathlib import Path

NIST = 'nonlinear/nist/aes-sbox/'
SEEDS = [1, 2, 3, 4, 5]


def main():
    out = Path(sys.argv[1])
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else ['L', 'N', 'A', 'X', 'F']
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'v1'
    tasks = []
    if 'L' in only:
        for mp in ('joltik', 'small-scale-aes', 'klsw17-m-4x4-gf16'):
            seed_json = sorted(Path('search/seeds', mp).glob('nist-*.json'))[0]
            for cap in (4, None):
                for st_name, st in (('naive', 'anf'), ('nist', str(seed_json))):
                    for s in SEEDS:
                        base = {'target': 'map:' + mp, 'model': 'xor', 'objective': 'cost,gd', 'caps': {'GD': cap},
                                'start': st, 'seconds': 120, 'seed': s}
                        lab = 'L-%s-c%s-%s-s%d' % (mp, cap or 'none', st_name, s)
                        pair = [dict(base, tool='xorflux', label=lab + '-xorflux')]   # rerun every round: paired CPU
                        tasks.append(pair + [dict(base, tool='boolflux', config='gate', label=lab + '-boolflux-' + tag)])
    small = [('present', 'bgc', 'cost'), ('rectangle', 'bgc', 'cost'), ('ascon', 'bgc', 'cost'),
             ('prince', 'bgc', 'cost'), ('gf16-mul', 'xag', 'a,cost')]
    if 'N' in only:
        for t, m, o in small:
            for s in SEEDS:
                base = {'tool': 'boolflux', 'target': t, 'model': m, 'objective': o, 'start': 'anf', 'seconds': 60,
                        'seed': s, 'round_s': 10}
                tasks.append([dict(base, config='full', label='N-%s-full-s%d-%s' % (t, s, tag)),
                              dict(base, config='gate', label='N-%s-gate-s%d-%s' % (t, s, tag))]
                             + ([dict(base, config='full', skel_set={'iters': 0}, label='N-%s-rebuild-s%d-%s' % (t, s, tag))]
                                if tag != 'v1' else []))
    aes = [('aes-anf', 'anf', {}, 300, [1, 2, 3], 60),
           ('aes-a36g142', NIST + 'aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt', {'A': 36, 'AD': 4, 'GD': 13}, 120, SEEDS, 30),
           ('aes-gd14repair', NIST + 'aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt', {'GD': 14}, 120, SEEDS, 30),
           ('aes-g104', NIST + 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt', {}, 120, SEEDS, 30)]
    if 'A' in only:
        for name, st, caps, secs, seeds, rs in aes:
            for s in seeds:
                base = {'tool': 'boolflux', 'target': 'aes', 'model': 'nist', 'objective': 'cost,gd', 'caps': caps,
                        'start': st, 'seconds': secs, 'seed': s, 'round_s': rs}
                tasks.append([dict(base, config='full', label='A-%s-full-s%d-%s' % (name, s, tag)),
                              dict(base, config='gate', label='A-%s-gate-s%d-%s' % (name, s, tag))]
                             + ([dict(base, config='full', skel_set={'iters': 0}, label='A-%s-rebuild-s%d-%s' % (name, s, tag))]
                                if tag != 'v1' else []))
    abl = {'no-resub3': {'mv.resub3': 0}, 'no-resub2+3': {'mv.resub2': 0, 'mv.resub3': 0}, 'no-anneal': {'T0': 0},
           'no-neutral': {'neutral': 0}, 'no-odc': {'odc': 0}, 'no-restart': {'stall_it': 10 ** 15}, 'no-fraig': {'fraig': 0}}
    xt = [('present', 'bgc', 'cost', 'anf', {}, 60), ('rectangle', 'bgc', 'cost', 'anf', {}, 60),
          ('gf16-mul', 'xag', 'a,cost', 'anf', {}, 60),
          ('aes', 'nist', 'cost,gd', NIST + 'aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt', {'A': 36, 'AD': 4, 'GD': 13}, 120)]
    if 'X' in only:
        for t, m, o, st, caps, secs in xt:
            for a, setting in abl.items():
                for s in SEEDS:
                    tasks.append([{'tool': 'boolflux', 'config': 'gate', 'target': t, 'model': m, 'objective': o,
                                   'caps': caps, 'start': st, 'seconds': secs, 'seed': s, 'set': setting,
                                   'label': 'X-%s-%s-s%d-%s' % (t, a, s, tag)}])
    if 'F' in only:
        for t, m, o, st, caps, secs in [xt[1], xt[2], xt[3]]:
            for a, extra in (('no-merge', {'skel_set': {'mv.merge': 0}}), ('unseeded', {'seeded': False}),
                             ('seeded-only', {'unseeded': False})):
                for s in SEEDS:
                    tasks.append([dict({'tool': 'boolflux', 'config': 'full', 'target': t, 'model': m, 'objective': o,
                                        'caps': caps, 'start': st, 'seconds': secs, 'seed': s,
                                        'round_s': 10 if secs <= 60 else 30,
                                        'label': 'F-%s-%s-s%d-%s' % (t, a, s, tag)}, **extra)])
    # kernel version: v1 = as committed in 3a71f0f (no-op candidates allowed), v2 = no-op filter
    noop = {'v1': 0}.get(tag, 1)
    for t in tasks:
        for r in t:
            if r['tool'] == 'boolflux':
                r['set'] = dict(r.get('set', {}), skip_noop=noop)
    out.write_text(json.dumps({'tasks': tasks}, indent=0) + '\n')
    print(len(tasks), 'tasks,', sum(len(t) for t in tasks), 'runs,',
          round(sum(r['seconds'] for t in tasks for r in t) / 3600, 2), 'CPU-hours of search budget')


if __name__ == '__main__':
    main()
