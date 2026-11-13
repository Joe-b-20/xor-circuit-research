"""Randomized test of the skeleton kernel skel and skeleton.synthesize (review harness).

    python3 nonlinear/boolflux/review/fuzz_skel.py [CASES] [SEED] [BIN]

Random start circuit (n = 3..8, full library) -> skeleton.extract -> skel kernel (short run,
random move weights, optional cap.ad) -> checks with this file's own skeleton evaluator:
  * every AND operand form only uses positions < its own position, no constant-only forms;
  * the output forms Y written by the kernel reproduce the target tables exactly;
  * the kernel's reported K equals the number of AND lines; with cap.ad, every AND's depth <= cap;
  * same config twice -> byte-identical output;
  * skeleton.synthesize(sk, ops) for several libraries computes the target, uses only the
    library's ops, and its AND depth respects cap.ad; reports A vs K.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BF = HERE.parent
sys.path.insert(0, str(BF.parent))
from boolflux import core, skeleton  # noqa: E402

sys.path.insert(0, str(HERE))
from fuzz_bfx import rand_circuit, nonconst, evaluate  # noqa: E402

TMP = HERE / 'tmp'
LIBS = {'xag': {8, 6, 3}, 'nist': {8, 6, 9, 3}, 'gc': {8, 14, 6, 9, 7, 1, 4, 13, 3}, 'bgc': {8, 14, 6, 3},
        'xag_nonot': {8, 6, 9}}


def form_table(f, tabs, ones):
    t = 0; p = 0
    while f:
        if f & 1: t ^= tabs[p]
        f >>= 1; p += 1
    return t & ones


def skel_check(sk, target_tables, cap_ad):
    n = sk['n']; ones = (1 << (1 << n)) - 1
    tabs = [ones] + core.input_tables(n)
    ad = []
    err = []
    for k, (L, R) in enumerate(sk['ands']):
        P = 1 + n + k
        if L >> P or R >> P: err.append('AND %d uses a later position' % k)
        if (L & ~1) == 0 or (R & ~1) == 0: err.append('AND %d has a constant operand' % k)
        tabs.append(form_table(L, tabs, ones) & form_table(R, tabs, ones))
        d = 0
        for p in range(1 + n, P):
            if ((L | R) >> p) & 1: d = max(d, ad[p - 1 - n])
        ad.append(d + 1)
    for j, (y, t) in enumerate(zip(sk['outputs'], target_tables)):
        if form_table(y, tabs, ones) != t: err.append('output %d form wrong' % j)
    if cap_ad is not None and ad and max(ad) > cap_ad: err.append('AD %d > cap %d' % (max(ad), cap_ad))
    return err, (max(ad) if ad else 0)


def main():
    cases = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    binp = sys.argv[3] if len(sys.argv) > 3 else str(HERE / 'skel')
    rng = random.Random(seed0)
    fails = []; st = {'cases': 0, 'K_drop': 0, 'synth_A_gt_K': 0, 'synth_AD_gt_skel': 0, 'synth_err': 0}
    for case in range(cases):
        n = rng.randint(3, 8)
        lib = [8, 14, 6, 9, 7, 1, 4, 13, 3]
        for _ in range(20):
            gates, outs = rand_circuit(rng, n, lib)
            if nonconst(n, gates, outs): break
        else:
            continue
        c = core.Circuit(n, len(outs), gates, outs).live()
        sk = skeleton.extract(c)
        tt = c.output_tables()
        tag = 's%d_%d' % (seed0, case)
        sp = TMP / (tag + '.skin'); so = TMP / (tag + '.skout'); so2 = TMP / (tag + '.skout2')
        sp.write_text(skeleton.write_skel(sk, tt))
        k0 = len(sk['ands'])
        # start AND depth (all ANDs) to choose a cap
        _, ad0 = skel_check(sk, tt, None)
        cap = None if rng.random() < 0.5 else max(1, ad0 - rng.choice([0, 0, 1]))
        cfg = {'w.a': 1, 'w.lin': rng.choice([0.001, 0.02, 0.5]), 'T0': rng.choice([0, 0.3, 1]),
               'Tperiod_it': rng.choice([100, 4000]), 'mv.swap': rng.choice([0, 4]), 'mv.merge': rng.choice([0, 3]),
               'mv.split': rng.choice([0, 1, 3]), 'mv.perturb': rng.choice([0, 1, 3]),
               'pairs': rng.choice([200, 60000]), 'fext': rng.choice([0, 400]),
               'seed': rng.randrange(1, 10 ** 6), 'iters': rng.choice([100, 500, 2000]), 'seconds': 1000}
        if sum(cfg[k] for k in ('mv.swap', 'mv.merge', 'mv.split', 'mv.perturb')) == 0: cfg['mv.swap'] = 1
        if cap is not None: cfg['cap.ad'] = cap
        def wc(p, o):
            p.write_text(''.join('%s %s\n' % kv for kv in {**cfg, 'in': sp, 'out': o}.items()))
        cp = TMP / (tag + '.skcfg'); cp2 = TMP / (tag + '.skcfg2'); wc(cp, so); wc(cp2, so2)
        r = subprocess.run([binp, str(cp)], capture_output=True, text=True, timeout=300)
        st['cases'] += 1
        err = []
        if r.returncode != 0:
            # rc 3 = start infeasible under cap.ad: legit when cap < start AD
            if not (r.returncode == 3 and cap is not None and cap < ad0):
                fails.append((tag, 'rc %d %s' % (r.returncode, (r.stdout + r.stderr)[-300:])))
            continue
        txt = so.read_text()
        sk2 = skeleton.read_skel(txt)
        e, ad2 = skel_check(sk2, tt, cap)
        err += e
        kk = int([ln for ln in txt.splitlines() if ln.startswith('#')][-1].split()[2])
        if kk != len(sk2['ands']): err.append('reported K %d != %d' % (kk, len(sk2['ands'])))
        if len(sk2['ands']) < k0: st['K_drop'] += 1
        r2 = subprocess.run([binp, str(cp2)], capture_output=True, text=True, timeout=300)
        if so2.read_text() != txt: err.append('NOT REPRODUCIBLE')
        for ln, ops in LIBS.items():
            try:
                c2 = skeleton.synthesize(sk2, ops)
            except Exception as ex:   # noqa: BLE001
                st['synth_err'] += 1
                if ln != 'xag_nonot': err.append('synthesize(%s) raised %r' % (ln, ex))
                continue
            if c2.output_tables() != tt: err.append('SYNTH %s WRONG FUNCTION' % ln)
            bad = {g[0] for g in c2.gates} - ops
            if bad: err.append('synth %s uses ops %s outside library' % (ln, sorted(bad)))
            mt = c2.metrics()
            if mt['A'] > len(sk2['ands']): st['synth_A_gt_K'] += 1
            if mt['AD'] > ad2: st['synth_AD_gt_skel'] += 1
            if cap is not None and mt['AD'] > cap: err.append('synth %s AD %d > cap %d' % (ln, mt['AD'], cap))
        if err: fails.append((tag, '; '.join(err)))
        else:
            for p in (sp, so, so2, cp, cp2):
                try: p.unlink()
                except OSError: pass
    print(json.dumps(st)); print('%d failures' % len(fails))
    for t, e in fails[:40]: print(t, e)


if __name__ == '__main__':
    main()
