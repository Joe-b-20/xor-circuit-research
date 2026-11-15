#!/usr/bin/env python3
"""X1 flip / split walk on the product program (see x1lib.py for the identities).

    python3 x1walk.py FILE OUT_DIR [--seconds S] [--seed N] [--plus K] [--psplit P] [--horizon H] [--redecomp 0|1]

State: product program.  Step: if two ANDs are read by exactly the same forms and share a factor, merge
them (-1 AND).  Otherwise a random flip between two ANDs sharing a factor; with probability psplit (and
while A <= A_start + plus) a split p_i = a*(b+c) + a*c with c taken from another AND's operand span, so
that the new AND shares a factor with it.  After `horizon` steps without a new best the walk returns to a
stored state of the best AND count.  Every new best is materialised and checked on all 256 inputs.
[H] search; flips stay inside span{1, x, products}, splits leave it.
"""
import json, random, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X
from boolflux.hub.common import load, metrics, sbox
from boolflux import core

TARGET = core.tables_from_values(8, 8, list(sbox()))


class Walker:
    def __init__(self, p, rng, plus=1, psplit=0.02, horizon=20000):
        self.rng = rng; self.plus = plus; self.psplit = psplit; self.horizon = horizon
        self.p = p.copy(); self.p.reduce()
        self.best = self.p.copy(); self.pool = [self.p.copy()]
        self.stats = {'flips': 0, 'splits': 0, 'merges': 0, 'restarts': 0, 'steps': 0}
        self.since = 0
        self.R = [rng.getrandbits(62) | 1 for _ in range(400)]

    def sigs(self):
        p = self.p; pm = p.pmask(); sig = dict.fromkeys(p.ands, 0); R = self.R
        idx = 0
        for k, (L, Rr) in p.ands.items():
            for f in (L, Rr):
                m = f & pm; r = R[idx]; idx += 1
                while m:
                    b = m & -m; sig[b.bit_length() - 1] ^= r; m ^= b
        for f in p.outs:
            m = f & pm; r = R[idx]; idx += 1
            while m:
                b = m & -m; sig[b.bit_length() - 1] ^= r; m ^= b
        return sig

    def share(self):
        d = {}
        for k, (L, R) in self.p.ands.items():
            L0 = L & ~1; R0 = R & ~1
            for a in (L0, R0, L0 ^ R0):
                d.setdefault(a, []).append(k)
        return {a: ks for a, ks in d.items() if len(ks) > 1}

    def step(self):
        p = self.p; rng = self.rng; self.stats['steps'] += 1
        sh = self.share()
        sig = self.sigs()
        # merge: equal usage + shared factor
        for a, ks in sh.items():
            for x in range(len(ks)):
                for y in range(x + 1, len(ks)):
                    i, j = ks[x], ks[y]
                    if sig[i] == sig[j]:
                        if p.flip(i, j, a):
                            n = p.remove_dead()
                            if n:
                                self.stats['merges'] += 1
                                return True
                            # hash collision or j still read: keep going as a normal flip
                            return False
        if (not sh or rng.random() < self.psplit) and p.A < self.best.A + self.plus:
            return self.split()
        if not sh: return False
        a = rng.choice(list(sh)); ks = sh[a]
        i, j = rng.sample(ks, 2)
        if p.depends(j, i):
            if p.depends(i, j): return False
            i, j = j, i
        if p.flip(i, j, a): self.stats['flips'] += 1
        return False

    def split(self):
        p = self.p; rng = self.rng
        ks = list(p.ands)
        i = rng.choice(ks)
        a = rng.choice(X.Prog.span3(*p.ands[i]))
        tf = p.tfo(i) | (1 << i)
        if rng.random() < 0.8:
            js = [j for j in ks if not (tf >> j) & 1]
            if not js: return False
            j = rng.choice(js)
            c = rng.choice(X.Prog.span3(*p.ands[j]))
        else:
            atoms = [b for b in list(range(1, p.n + 1)) + ks if not (tf >> b) & 1]
            c = 1 << rng.choice(atoms)
            if rng.random() < 0.5: c ^= 1 << rng.choice(atoms)
            if c == 0: return False
        if c & tf: return False
        k = p.split(i, a, c)
        if k is not None: self.stats['splits'] += 1
        return False

    def run(self, seconds, on_best=None):
        t0 = time.time()
        while time.time() - t0 < seconds:
            for _ in range(200):
                red = self.step(); self.since += 1
                if red:
                    if self.p.A < self.best.A:
                        self.p.reduce()
                        assert X.check(self.p, TARGET), 'walk broke the function'
                        self.best = self.p.copy(); self.pool = [self.p.copy()]; self.since = 0
                        if on_best: on_best(self)
                    elif self.p.A == self.best.A:
                        if len(self.pool) < 50: self.pool.append(self.p.copy())
                        else: self.pool[self.rng.randrange(50)] = self.p.copy()
                if self.since > self.horizon:
                    self.p = self.rng.choice(self.pool).copy(); self.since = 0; self.stats['restarts'] += 1
        return self.best


def main():
    args = sys.argv[1:]
    f = args[0]; out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
    def opt(name, d):
        return type(d)(args[args.index(name) + 1]) if name in args else d
    seconds = opt('--seconds', 60.0); seed = opt('--seed', 1); plus = opt('--plus', 1)
    psplit = opt('--psplit', 0.02); horizon = opt('--horizon', 20000)
    c = load(f); m0 = metrics(c); rng = random.Random(seed)
    p = X.extract(c)
    w = Walker(p, rng, plus, psplit, horizon)
    t0 = time.time()
    print('start %s %s A after static reduce %d' % (Path(f).name, m0, w.p.A), flush=True)

    def on_best(w):
        nc = X.materialise(w.best, rng)
        ok = tuple(nc.value_table()) == sbox(); m = metrics(nc)
        print('BEST A %d  t %.1f  circuit %s ok=%s  %s' % (w.best.A, time.time() - t0, m, ok, w.stats), flush=True)
        if ok:
            name = 'walk-%s-s%d-a%d' % (Path(f).name.split('.')[0][:40], seed, m[0])
            (out / (name + '.bfx')).write_text(core.to_kernel(nc))
            (out / (name + '.json')).write_text(json.dumps({'method': 'x1walk flip/split walk', 'source': f, 'seed': seed,
                'plus': plus, 'psplit': psplit, 'horizon': horizon, 'metrics': m, 't': round(time.time() - t0, 1), 'stats': w.stats}))
    w.run(seconds, on_best)
    print('end A %d (start %d) %s  %.0f steps/s' % (w.best.A, m0[0], w.stats, w.stats['steps'] / (time.time() - t0)), flush=True)


if __name__ == '__main__':
    main()
