#!/usr/bin/env python3
"""Where do real MixColumns circuits live in the 75 proof's space?

Reconstructs a gate list from each sampled value list, then runs the proof package's own
stress.py machinery (Circuit, analyse, canonical_transpose, check_rows) along the transpose orbit.
Writes bridge/profiles.json.  Standard library + the package copy only.

usage: python3 profile_real.py [N_SAMPLES] [N_KSTE]
"""
import sys, json, random, re, time
from collections import Counter, defaultdict
from math import comb

HOME = '/home/joebachir20'
SPRINT = HOME + '/xs-campaigns/2026-11-07-sprint'
OUT = SPRINT + '/bridge'
PKG = SPRINT + '/lb76/pkg_copy/source/lower_bounds/checks'
sys.path.insert(0, PKG)
import stress
from stress import Circuit, check_rows, ROWS, parity

ROWSET = set(ROWS)
INPUTS = [1 << i for i in range(32)]


def rot(v, s):
    return ((v << s) | (v >> (32 - s))) & 0xFFFFFFFF


def rotkey(helpers):
    return min(tuple(sorted(rot(v, s) for v in helpers)) for s in (0, 8, 16, 24))


# ----------------------------------------------------------------------------- reconstruction
def min_levels(values):
    """min-level of every value (inputs 0) by rounds; raises if some value is not a XOR of two others."""
    lev = {m: 0 for m in INPUTS}
    pending = set(values) - set(INPUTS)
    L = 0
    while pending:
        placed = list(lev)
        new = [v for v in pending if any((a ^ v) in lev and (a ^ v) != a for a in placed)]
        if not new:
            raise ValueError('unbuildable: %d values' % len(pending))
        L += 1
        for v in new:
            lev[v] = L
        pending -= set(new)
    return lev


def candidates(v, lev, strict):
    """all (a,b) with a<b, a^b=v, both present; strict: both of lower min-level than v."""
    out = []
    for a in lev:
        b = a ^ v
        if b in lev and a < b:
            if strict and not (lev[a] < lev[v] and lev[b] < lev[v]):
                continue
            out.append((a, b))
    return out


def kind(a, b):
    pa, pb = parity(a), parity(b)
    return 'ee' if not pa and not pb else ('oo' if pa and pb else 'mix')


def reconstruct(values, policy='ymax', seed=0, strict=True, max_repair=500):
    """Choose a parent pair per value. policy in ymax | xmax | rand | lex.
    Returns (gates as list of (a,b) indices, order of masks, info dict) or raises."""
    rng = random.Random(seed)
    lev = min_levels(values)
    vals = [v for v in values]
    cands = {v: candidates(v, lev, strict) for v in vals}
    for v in vals:
        if not cands[v]:
            cands[v] = candidates(v, lev, False)  # should not happen with strict levels

    def pick(v, cs):
        cs = list(cs)
        if policy == 'lex':
            return min(cs)
        rng.shuffle(cs)
        if policy == 'ymax' and not parity(v):
            pref = [c for c in cs if kind(*c) == 'ee']
            if pref:
                return pref[0]
        if policy == 'xmax' and not parity(v):
            pref = [c for c in cs if kind(*c) == 'oo']
            if pref:
                return pref[0]
        return cs[0]

    choice = {v: pick(v, cands[v]) for v in vals}
    # dead-signal repair: every non-output value must be used by some gate
    for it in range(max_repair):
        use = Counter()
        for v, (a, b) in choice.items():
            use[a] += 1
            use[b] += 1
        dead = [v for v in vals if v not in ROWSET and use[v] == 0]
        if not dead:
            break
        d = dead[0]
        users = [(v, c) for v in vals for c in cands[v] if d in c and v != d]
        if not users:
            raise ValueError('helper %x can never be used' % d)
        # prefer a switch whose current parents stay alive
        rng.shuffle(users)
        users.sort(key=lambda vc: -min(use[choice[vc[0]][0]], use[choice[vc[0]][1]]))
        v, c = users[0]
        choice[v] = c
    else:
        raise ValueError('dead-signal repair did not converge')
    # topological order (cycle check for loose mode)
    idx = {m: i for i, m in enumerate(INPUTS)}
    order = []
    remaining = set(vals)
    while remaining:
        ready = [v for v in remaining if choice[v][0] in idx and choice[v][1] in idx]
        if not ready:
            raise ValueError('cyclic choice')
        ready.sort(key=lambda v: (lev[v], v))
        for v in ready:
            idx[v] = len(idx)
            order.append(v)
        remaining -= set(ready)
    gates = [(idx[choice[v][0]], idx[choice[v][1]]) for v in order]
    nchoice = {v: len(cands[v]) for v in vals}
    info = dict(n_multi=sum(1 for v in vals if nchoice[v] > 1), max_cands=max(nchoice.values()),
                even_with_ee=sum(1 for v in vals if not parity(v) and any(kind(*c) == 'ee' for c in cands[v])),
                even_with_oo=sum(1 for v in vals if not parity(v) and any(kind(*c) == 'oo' for c in cands[v])),
                even_both=sum(1 for v in vals if not parity(v) and any(kind(*c) == 'ee' for c in cands[v]) and any(kind(*c) == 'oo' for c in cands[v])),
                repairs=it)
    return gates, order, info


def reconstruct_loose(values, seed):
    """Random valid reconstruction: random build order, random parent pair among already-built signals.
    Every acyclic reconstruction of the value set arises from some sequence of these choices."""
    rng = random.Random(seed)
    built = {m: i for i, m in enumerate(INPUTS)}
    pending = set(values)
    gates = []
    order = []
    while pending:
        opts = []
        for v in pending:
            ps = [(a, a ^ v) for a in built if (a ^ v) in built and a < (a ^ v)]
            if ps:
                opts.append((v, ps))
        if not opts:
            raise ValueError('unbuildable')
        v, ps = rng.choice(sorted(opts))
        a, b = rng.choice(ps)
        built[v] = len(built)
        gates.append((built[a], built[b]))
        order.append(v)
        pending.discard(v)
    return gates, order, {}


# ----------------------------------------------------------------------------- repo circuits
GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")


def read_ncff(path):
    names = {f'x{j}': j for j in range(32)}
    gates = []
    for line in open(path):
        line = line.split('%')[0].strip()
        m = GATE.match(line)
        if not m:
            continue
        _, out, a, b = m.groups()
        gates.append((names[a], names[b]))
        names[out] = 32 + len(gates) - 1
    return gates


# ----------------------------------------------------------------------------- orbit analysis
def orbit(gates, steps=6):
    """profiles of C, T(C), T(T(C)), ... with the package's functions."""
    C = Circuit(gates, 'M')
    recs = []
    for step in range(steps):
        I = C.analyse()
        rows = check_rows(I, C.ori)
        # weight-2 labels: even signals of mask weight 2; represented ones
        evens = [v for v in range(32, C.n) if not C.odd[v]]
        w2 = [v for v in evens if bin(C.mask[v]).count('1') == 2]
        # a label is represented iff some B-B edge carries it; recompute the B-B labels as analyse does
        B = I['B']
        bb = set()
        for k, (a, b) in enumerate(C.gates):
            s = 32 + k
            if C.odd[a] and C.odd[b] and a in B and b in B:
                bb.add(s)
            elif C.odd[a] != C.odd[b]:
                o, e = (a, b) if C.odd[a] else (b, a)
                if o in B and s in B:
                    bb.add(e)
        w2_rep = sum(1 for v in w2 if v in bb)
        bb_edges = sum(1 for k, (a, b) in enumerate(C.gates)
                       if (C.odd[a] and C.odd[b] and a in B and b in B)
                       or (C.odd[a] != C.odd[b] and ((a if C.odd[a] else b) in B) and (32 + k) in B))
        rec = dict(step=step, ori=C.ori, G=C.G, x=I['x'], y=I['y'], h=I['h'], q=I['q'], z=I['z'], s=I['s'],
                   F=I['F'], F_H=I['F_H'], F_B=I['F_B'], e1=I['e1'], xp=I['xprime'], E_B=I['E_B'], L_H=I['L_H'],
                   types={'%d,%d,%d' % t: c for t, c in I['types'].items()},
                   n_r=[sum(c for (r, u, v), c in I['types'].items() if r == rr) for rr in range(4)],
                   rows=rows, n_even=len(evens), w2=len(w2), w2_rep=w2_rep, bb_edges=bb_edges,
                   helper_fanout=Counter(C.d[v] for v in I['H']),
                   input_pairs_as_values=sum(1 for v in evens if bin(C.mask[v]).count('1') == 2),
                   depth=None)
        recs.append(rec)
        if step + 1 < steps:
            T, origin = C.canonical_transpose(I)
            C = T
    return recs


def summarize_orbit(recs):
    """two-phase quantities as the proof uses them, from steps 0 and 1 (C and T(C))."""
    I, J = recs[0], recs[1]
    G = I['G']
    a, b = I['x'], J['x']
    budget = a + b + 2 * G - 192
    return dict(a=a, b=b, Y=I['y'], V=J['y'], he=I['h'], ho=J['h'], F0=I['F'], F1=J['F'],
                q0=I['q'], z0=I['z'], s0=I['s'], q1=J['q'], z1=J['z'], s1=J['s'],
                budget=budget, s_sum=I['s'] + J['s'], margin=I['s'] + J['s'] - budget,
                drift_lb=I['s'] + J['s'] + 192 - 2 * G - a - b,
                drift_actual=recs[2]['e1'] - recs[0]['e1'],
                ys=[r['y'] for r in recs], xs=[r['x'] for r in recs], hs=[r['h'] for r in recs],
                ss=[r['s'] for r in recs], e1s=[r['e1'] for r in recs])


# ----------------------------------------------------------------------------- main
def load_samples(n_want):
    files = [SPRINT + '/hunt/samples.jsonl', SPRINT + '/hunt/samplesC/samples.jsonl',
             SPRINT + '/hunt/samplesD/samples.jsonl']
    pools = []
    for f in files:
        pool = []
        for line in open(f):
            d = json.loads(line)
            if d['gates'] == 88 and len(d['values']) == 88:
                pool.append(d)
        pools.append(pool)
    seen = set()
    chosen = []
    i = 0
    while len(chosen) < n_want and any(pools):
        pool = pools[i % 3]
        i += 1
        while pool:
            d = pool.pop(0)
            helpers = [v for v in d['values'] if v not in ROWSET]
            k = rotkey(helpers)
            if k in seen:
                continue
            seen.add(k)
            d['src'] = ['A', 'C', 'D'][(i - 1) % 3]
            chosen.append(d)
            break
    return chosen


def main():
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    n_kste = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    t0 = time.time()
    jobs = []
    for d in load_samples(n_samples):
        jobs.append(('sample:%s:%s' % (d['src'], d['hash']), d['values'], None))
    for name in ('xor88-depth5', 'xor89-depth4', 'xor97-depth3'):
        p = HOME + '/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns-%s.circ.txt' % name
        g = read_ncff(p)
        C = Circuit(g, 'M')
        vals = C.mask[32:]
        jobs.append(('repo:%s' % name, vals, g))
    if n_kste:
        ks = json.load(open(SPRINT + '/kste/data/kste_valuesets.json'))
        rng = random.Random(1)
        seen = set()
        pick = []
        for vs in rng.sample(ks, min(len(ks), 20 * n_kste)):
            if len(vs) != 88:
                continue
            k = rotkey([v for v in vs if v not in ROWSET])
            if k in seen:
                continue
            seen.add(k)
            pick.append(vs)
            if len(pick) >= n_kste:
                break
        for i, vs in enumerate(pick):
            jobs.append(('kste:%d' % i, vs, None))
    print('jobs', len(jobs), flush=True)
    results = []
    failures = []
    for tag, values, true_gates in jobs:
        rec = dict(tag=tag, G=len(values), values=list(values))
        try:
            gates, order, info = reconstruct(values, 'ymax', 0, True)
            rec['recon'] = info
            recs = orbit(gates)
            rec['orbit'] = recs
            rec['two'] = summarize_orbit(recs)
            # dependence on the choice: 8 random ymax tie-breaks, 8 random any-pair, xmax, loose ymax
            var = []
            for pol, strict, seeds in (('ymax', True, range(1, 9)), ('rand', True, range(1, 9)),
                                       ('xmax', True, [1]), ('loose', False, range(1, 4)), ('lex', True, [0])):
                for sd in seeds:
                    try:
                        if pol == 'loose':
                            g2, _, _ = reconstruct_loose(values, sd)
                        else:
                            g2, _, _ = reconstruct(values, pol, sd, strict)
                        r2 = orbit(g2, steps=3)
                        var.append(dict(pol=pol, strict=strict, seed=sd,
                                        x=r2[0]['x'], y=r2[0]['y'], h=r2[0]['h'], q=r2[0]['q'], z=r2[0]['z'],
                                        F=r2[0]['F'], xT=r2[1]['x'], yT=r2[1]['y'], hT=r2[1]['h'],
                                        qT=r2[1]['q'], zT=r2[1]['z'], e1=r2[0]['e1'],
                                        margin=r2[0]['s'] + r2[1]['s'] - (r2[0]['x'] + r2[1]['x'] + 2 * len(values) - 192)))
                    except (ValueError, AssertionError) as ex:
                        var.append(dict(pol=pol, strict=strict, seed=sd, error=str(ex)))
            rec['variants'] = var
            if true_gates is not None:
                r3 = orbit(true_gates)
                rec['true_orbit'] = r3
                rec['true_two'] = summarize_orbit(r3)
        except (ValueError, AssertionError) as ex:
            rec['error'] = str(ex) or repr(ex)
            failures.append((tag, rec['error']))
            print('FAIL', tag, rec['error'], flush=True)
        results.append(rec)
        if len(results) % 25 == 0:
            print(len(results), 'done', '%.0fs' % (time.time() - t0), flush=True)
    json.dump(dict(results=results, failures=failures, seconds=time.time() - t0),
              open(OUT + '/profiles.json', 'w'), default=str)
    print('written', len(results), 'failures', len(failures), '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
